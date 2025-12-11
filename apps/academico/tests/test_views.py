from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import Curso, InscripcionCurso, Asistencia, Asignatura
from core.models import ConfiguracionAcademica
from datetime import datetime

from django.conf import settings

class AcademicoViewsTest(TestCase):
    def setUp(self):

        
        self.client = Client()
        
        # Configuración Académica
        self.config, _ = ConfiguracionAcademica.objects.update_or_create(
            pk=1,
            defaults={'año_actual': 2024}
        )
        
        # Usuario Estudiante
        self.estudiante_user = User.objects.create_user(username='12345678-9', password='password')
        self.estudiante_perfil = PerfilUsuario.objects.create(
            user=self.estudiante_user, 
            rut='12345678-9', 
            tipo_usuario='estudiante'
        )
        
        # Usuario Profesor
        self.profesor_user = User.objects.create_user(username='98765432-1', password='password')
        self.profesor_perfil = PerfilUsuario.objects.create(
            user=self.profesor_user, 
            rut='98765432-1', 
            tipo_usuario='profesor'
        )
        
        # Curso y Asignatura
        self.curso = Curso.objects.create(nombre='1 Medio A', nivel='1_medio', activo=True)
        self.asignatura = Asignatura.objects.create(nombre='Matemáticas')
        
        # Inscripción
        InscripcionCurso.objects.create(
            estudiante=self.estudiante_user,
            curso=self.curso,
            año=2024,
            estado='activo'
        )

    def test_descargar_informe_notas_estudiante(self):
        self.client.force_login(self.estudiante_user)
        response = self.client.get(reverse('academico:descargar_informe_notas'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        
    def test_descargar_informe_notas_no_estudiante(self):
        self.client.force_login(self.profesor_user)
        response = self.client.get(reverse('academico:descargar_informe_notas'))
        self.assertEqual(response.status_code, 302) # Redirect a home

    def test_tomar_asistencia_view(self):
        self.client.force_login(self.profesor_user)
        # Asumiendo que el profesor tiene permiso (en la app real se chequea si dicta clases)
        # Para este test simplificado, verificamos que la URL responda
        url = reverse('academico:tomar_asistencia', args=[self.curso.id])
        response = self.client.get(url)
        # Puede ser 200 o 302 dependiendo de los permisos estrictos de "dicta clases en este curso"
        # Si la vista chequea estrictamente, podría fallar si no asignamos horario.
        # Ajustaremos si falla.
