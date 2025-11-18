"""
Tests para el módulo de mensajería interna
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.db import IntegrityError
from datetime import datetime
import os

from mensajeria.models import Conversacion, Mensaje
from usuarios.models import PerfilUsuario

class MensajeriaModelTests(TestCase):
    """Tests para los modelos de mensajería"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear grupos
        self.grupo_alumno = Group.objects.create(name='Alumno')
        self.grupo_profesor = Group.objects.create(name='Profesor')
        
        # Crear usuarios de prueba
        self.alumno = User.objects.create_user(
            username='test_alumno',
            email='alumno@test.com',
            first_name='Alumno',
            last_name='Test',
            password='testpass123'
        )
        self.alumno.groups.add(self.grupo_alumno)
        
        self.profesor = User.objects.create_user(
            username='test_profesor',
            email='profesor@test.com',
            first_name='Profesor',
            last_name='Test',
            password='testpass123'
        )
        self.profesor.groups.add(self.grupo_profesor)
        
        # Crear perfiles
        PerfilUsuario.objects.create(
            user=self.alumno,
            rut='12.345.678-9',
            tipo_usuario='estudiante'
        )
        PerfilUsuario.objects.create(
            user=self.profesor,
            rut='12.345.679-7',
            tipo_usuario='profesor'
        )
        
        # Crear conversación
        self.conversacion = Conversacion.objects.create(
            alumno=self.alumno,
            profesor=self.profesor
        )
        
        # Crear mensaje
        self.mensaje = Mensaje.objects.create(
            conversacion=self.conversacion,
            autor=self.alumno,
            contenido='Mensaje de prueba'
        )
    
    def test_conversacion_creation(self):
        """Test crear conversación"""
        conversacion = Conversacion.objects.get(
            alumno=self.alumno,
            profesor=self.profesor
        )
        self.assertEqual(conversacion.alumno, self.alumno)
        self.assertEqual(conversacion.profesor, self.profesor)
        self.assertEqual(conversacion.no_leidos_alumno, 0)
        self.assertEqual(conversacion.no_leidos_profesor, 0)
    
    def test_conversacion_unique_constraint(self):
        """Test que no se puedan crear conversaciones duplicadas"""
        with self.assertRaises(IntegrityError):
            Conversacion.objects.create(
                alumno=self.alumno,
                profesor=self.profesor
            )
    
    def test_mensaje_creation(self):
        """Test crear mensaje"""
        self.assertEqual(self.mensaje.conversacion, self.conversacion)
        self.assertEqual(self.mensaje.autor, self.alumno)
        self.assertEqual(self.mensaje.contenido, 'Mensaje de prueba')
        self.assertFalse(self.mensaje.leido_por_destinatario)
    
    def test_get_otro_participante(self):
        """Test obtener el otro participante"""
        self.assertEqual(
            self.conversacion.get_otro_participante(self.alumno),
            self.profesor
        )
        self.assertEqual(
            self.conversacion.get_otro_participante(self.profesor),
            self.alumno
        )
    
    def test_get_contador_no_leidos(self):
        """Test obtener contador de no leídos"""
        self.assertEqual(
            self.conversacion.get_contador_no_leidos(self.alumno),
            0
        )
        self.assertEqual(
            self.conversacion.get_contador_no_leidos(self.profesor),
            0
        )
    
    def test_marcar_como_leido(self):
        """Test marcar conversación como leída"""
        self.conversacion.no_leidos_alumno = 3
        self.conversacion.no_leidos_profesor = 2
        self.conversacion.save()
        
        self.conversacion.marcar_como_leido(self.alumno)
        self.assertEqual(self.conversacion.no_leidos_alumno, 0)
        self.assertEqual(self.conversacion.no_leidos_profesor, 2)
        
        self.conversacion.marcar_como_leido(self.profesor)
        self.assertEqual(self.conversacion.no_leidos_alumno, 0)
        self.assertEqual(self.conversacion.no_leidos_profesor, 0)
    
    def test_mensaje_actualiza_contador_no_leidos(self):
        """Test que crear mensaje actualice contadores"""
        conversacion = Conversacion.objects.create(
            alumno=self.alumno,
            profesor=self.profesor
        )
        self.assertEqual(conversacion.no_leidos_alumno, 0)
        self.assertEqual(conversacion.no_leidos_profesor, 0)
        
        # Mensaje del alumno debería incrementar contador del profesor
        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            autor=self.alumno,
            contenido='Mensaje del alumno'
        )
        conversacion.refresh_from_db()
        self.assertEqual(conversacion.no_leidos_alumno, 0)
        self.assertEqual(conversacion.no_leidos_profesor, 1)
        
        # Mensaje del profesor debería incrementar contador del alumno
        mensaje2 = Mensaje.objects.create(
            conversacion=conversacion,
            autor=self.profesor,
            contenido='Mensaje del profesor'
        )
        conversacion.refresh_from_db()
        self.assertEqual(conversacion.no_leidos_alumno, 1)
        self.assertEqual(conversacion.no_leidos_profesor, 1)

class MensajeriaViewTests(TestCase):
    """Tests para las vistas de mensajería"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        # Crear grupos
        self.grupo_alumno = Group.objects.create(name='Alumno')
        self.grupo_profesor = Group.objects.create(name='Profesor')
        
        # Crear usuarios
        self.alumno = User.objects.create_user(
            username='alumno_test',
            password='testpass123'
        )
        self.alumno.groups.add(self.grupo_alumno)
        
        self.profesor = User.objects.create_user(
            username='profesor_test',
            password='testpass123'
        )
        self.profesor.groups.add(self.grupo_profesor)
        
        # Crear perfiles
        PerfilUsuario.objects.create(
            user=self.alumno,
            rut='12.345.678-9',
            tipo_usuario='estudiante'
        )
        PerfilUsuario.objects.create(
            user=self.profesor,
            rut='12.345.679-7',
            tipo_usuario='profesor'
        )
        
        # Crear conversación
        self.conversacion = Conversacion.objects.create(
            alumno=self.alumno,
            profesor=self.profesor
        )
    
    def test_conversaciones_list_requires_login(self):
        """Test que la lista de conversaciones requiera login"""
        response = self.client.get('/mensajeria/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_conversaciones_list_alumno(self):
        """Test lista de conversaciones para alumno"""
        self.client.login(username='alumno_test', password='testpass123')
        response = self.client.get('/mensajeria/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Conversaciones')
    
    def test_conversaciones_list_profesor(self):
        """Test lista de conversaciones para profesor"""
        self.client.login(username='profesor_test', password='testpass123')
        response = self.client.get('/mensajeria/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Conversaciones')
    
    def test_conversacion_detail_requires_login(self):
        """Test que el detalle de conversación requiera login"""
        response = self.client.get(f'/mensajeria/{self.conversacion.id}/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_conversacion_detail_access(self):
        """Test acceso al detalle de conversación"""
        self.client.login(username='alumno_test', password='testpass123')
        response = self.client.get(f'/mensajeria/{self.conversacion.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Conversación con')
    
    def test_conversacion_detail_unauthorized(self):
        """Test que usuario no participante no pueda acceder"""
        # Crear otro alumno
        otro_alumno = User.objects.create_user(
            username='otro_alumno',
            password='testpass123'
        )
        otro_alumno.groups.add(self.grupo_alumno)
        
        self.client.login(username='otro_alumno', password='testpass123')
        response = self.client.get(f'/mensajeria/{self.conversacion.id}/')
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_nueva_conversacion_post_alumno(self):
        """Test crear nueva conversación desde alumno"""
        self.client.login(username='alumno_test', password='testpass123')
        response = self.client.post('/mensajeria/nueva/', {
            'destinatario': self.profesor.id
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verificar que se creó la conversación
        conversaciones = Conversacion.objects.filter(
            alumno=self.alumno,
            profesor=self.profesor
        )
        self.assertEqual(conversaciones.count(), 2)  # Una ya existía, más esta nueva
    
    def test_nueva_conversacion_post_profesor(self):
        """Test crear nueva conversación desde profesor"""
        self.client.login(username='profesor_test', password='testpass123')
        response = self.client.post('/mensajeria/nueva/', {
            'destinatario': self.alumno.id
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verificar que se creó la conversación
        conversaciones = Conversacion.objects.filter(
            alumno=self.alumno,
            profesor=self.profesor
        )
        self.assertEqual(conversaciones.count(), 2)
    
    def test_nuevo_mensaje_post(self):
        """Test enviar nuevo mensaje"""
        self.client.login(username='alumno_test', password='testpass123')
        response = self.client.post(
            f'/mensajeria/{self.conversacion.id}/enviar/',
            {'contenido': 'Mensaje de prueba'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verificar que se creó el mensaje
        mensaje = Mensaje.objects.get(
            conversacion=self.conversacion,
            contenido='Mensaje de prueba'
        )
        self.assertEqual(mensaje.autor, self.alumno)
    
    def test_eliminar_conversacion_post(self):
        """Test eliminar conversación (solo alumno puede)"""
        self.client.login(username='alumno_test', password='testpass123')
        response = self.client.post(f'/mensajeria/{self.conversacion.id}/eliminar/')
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verificar que se eliminó
        with self.assertRaises(Conversacion.DoesNotExist):
            Conversacion.objects.get(id=self.conversacion.id)
    
    def test_eliminar_conversacion_get(self):
        """Test formulario de confirmación para eliminar"""
        self.client.login(username='alumno_test', password='testpass123')
        response = self.client.get(f'/mensajeria/{self.conversacion.id}/eliminar/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Eliminar')
        self.assertContains(response, 'confirmar')

class MensajeriaFormTests(TestCase):
    """Tests para los formularios de mensajería"""
    
    def setUp(self):
        """Configuración inicial"""
        self.grupo_alumno = Group.objects.create(name='Alumno')
        self.grupo_profesor = Group.objects.create(name='Profesor')
        
        self.alumno = User.objects.create_user(
            username='alumno_form',
            password='testpass123'
        )
        self.alumno.groups.add(self.grupo_alumno)
        
        self.profesor = User.objects.create_user(
            username='profesor_form',
            password='testpass123'
        )
        self.profesor.groups.add(self.grupo_profesor)
        
        from mensajeria.forms import (
            MensajeForm, 
            NuevaConversacionForm,
            BusquedaConversacionForm
        )
        self.MensajeForm = MensajeForm
        self.NuevaConversacionForm = NuevaConversacionForm
        self.BusquedaConversacionForm = BusquedaConversacionForm
    
    def test_mensaje_form_valid(self):
        """Test formulario de mensaje válido"""
        form = self.MensajeForm(
            data={'contenido': 'Mensaje de prueba'},
            usuario=self.alumno
        )
        self.assertTrue(form.is_valid())
    
    def test_mensaje_form_empty_content(self):
        """Test formulario de mensaje con contenido vacío"""
        form = self.MensajeForm(
            data={'contenido': ''},
            usuario=self.alumno
        )
        self.assertFalse(form.is_valid())
        self.assertIn('contenido', form.errors)
    
    def test_nueva_conversacion_form_alumno(self):
        """Test formulario de nueva conversación para alumno"""
        form = self.NuevaConversacionForm(
            data={'destinatario': self.profesor.id},
            usuario=self.alumno
        )
        self.assertTrue(form.is_valid())
    
    def test_nueva_conversacion_form_profesor(self):
        """Test formulario de nueva conversación para profesor"""
        form = self.NuevaConversacionForm(
            data={'destinatario': self.alumno.id},
            usuario=self.profesor
        )
        self.assertTrue(form.is_valid())
    
    def test_nueva_conversacion_form_same_user(self):
        """Test formulario de nueva conversación con mismo usuario"""
        form = self.NuevaConversacionForm(
            data={'destinatario': self.alumno.id},
            usuario=self.alumno
        )
        self.assertFalse(form.is_valid())
        self.assertIn('destinatario', form.errors)
    
    def test_busqueda_conversacion_form(self):
        """Test formulario de búsqueda"""
        form = self.BusquedaConversacionForm(
            data={'busqueda': 'test'}
        )
        self.assertTrue(form.is_valid())
        
        form_empty = self.BusquedaConversacionForm(
            data={}
        )
        self.assertTrue(form_empty.is_valid())

class MensajeriaIntegrationTests(TestCase):
    """Tests de integración para el flujo completo de mensajería"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        # Crear grupos
        self.grupo_alumno = Group.objects.create(name='Alumno')
        self.grupo_profesor = Group.objects.create(name='Profesor')
        
        # Crear usuarios
        self.alumno = User.objects.create_user(
            username='integration_alumno',
            password='testpass123',
            first_name='Alumno',
            last_name='Integración'
        )
        self.alumno.groups.add(self.grupo_alumno)
        
        self.profesor = User.objects.create_user(
            username='integration_profesor',
            password='testpass123',
            first_name='Profesor',
            last_name='Integración'
        )
        self.profesor.groups.add(self.grupo_profesor)
        
        # Crear perfiles
        PerfilUsuario.objects.create(
            user=self.alumno,
            rut='12.345.678-9',
            tipo_usuario='estudiante'
        )
        PerfilUsuario.objects.create(
            user=self.profesor,
            rut='12.345.679-7',
            tipo_usuario='profesor'
        )
    
    def test_complete_conversation_flow(self):
        """Test flujo completo de conversación"""
        # 1. Alumno inicia sesión y crea conversación
        self.client.login(username='integration_alumno', password='testpass123')
        response = self.client.post('/mensajeria/nueva/', {
            'destinatario': self.profesor.id
        })
        self.assertEqual(response.status_code, 302)
        
        # Obtener la conversación creada
        conversacion = Conversacion.objects.get(
            alumno=self.alumno,
            profesor=self.profesor
        )
        
        # 2. Alumno envía primer mensaje
        response = self.client.post(
            f'/mensajeria/{conversacion.id}/enviar/',
            {'contenido': 'Hola profesor, tengo una consulta.'}
        )
        self.assertEqual(response.status_code, 302)
        
        # 3. Profesor inicia sesión y ve la conversación
        self.client.logout()
        self.client.login(username='integration_profesor', password='testpass123')
        
        response = self.client.get('/mensajeria/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alumno Integración')  # Nombre del alumno
        
        # 4. Profesor accede a la conversación
        response = self.client.get(f'/mensajeria/{conversacion.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hola profesor, tengo una consulta.')
        
        # 5. Profesor responde
        response = self.client.post(
            f'/mensajeria/{conversacion.id}/enviar/',
            {'contenido': '¡Hola! Claro, te ayudo con tu consulta.'}
        )
        self.assertEqual(response.status_code, 302)
        
        # 6. Verificar que ambos mensajes existen
        mensajes = Mensaje.objects.filter(conversacion=conversacion)
        self.assertEqual(mensajes.count(), 2)
        
        # 7. Alumno vuelve a iniciar sesión y ve la respuesta
        self.client.logout()
        self.client.login(username='integration_alumno', password='testpass123')
        
        response = self.client.get(f'/mensajeria/{conversacion.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¡Hola! Claro, te ayudo con tu consulta.')
    
    def test_file_attachment_flow(self):
        """Test flujo con archivo adjunto"""
        self.client.login(username='integration_alumno', password='testpass123')
        
        # Crear conversación
        response = self.client.post('/mensajeria/nueva/', {
            'destinatario': self.profesor.id
        })
        
        conversacion = Conversacion.objects.get(
            alumno=self.alumno,
            profesor=self.profesor
        )
        
        # Crear archivo de prueba
        archivo_test = SimpleUploadedFile(
            "test.pdf",
            b"contenido de prueba",
            content_type="application/pdf"
        )
        
        # Enviar mensaje con archivo
        response = self.client.post(
            f'/mensajeria/{conversacion.id}/enviar/',
            {
                'contenido': 'Te envío un archivo.',
                'adjunto': archivo_test
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el mensaje se creó con el archivo
        mensaje = Mensaje.objects.get(conversacion=conversacion, contenido='Te envío un archivo.')
        self.assertIsNotNone(mensaje.adjunto)
        self.assertTrue(mensaje.adjunto.name.endswith('.pdf'))
    
    def test_user_without_role_cannot_access(self):
        """Test que usuarios sin rol no puedan acceder"""
        # Crear usuario sin grupo
        usuario_sin_rol = User.objects.create_user(
            username='sin_rol',
            password='testpass123'
        )
        
        self.client.login(username='sin_rol', password='testpass123')
        response = self.client.get('/mensajeria/')
        self.assertEqual(response.status_code, 302)  # Redirigido
        
        # Verificar que fue redirigido al panel
        self.assertIn('/usuarios/panel/', response.url)
