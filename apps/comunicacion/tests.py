from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from comunicacion.models import Noticia, CategoriaNoticia

class ComunicacionTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Admin User
        self.admin_user = User.objects.create_superuser(
            username='admin', 
            email='admin@test.com', 
            password='password123'
        )
        
        # Create CategoriaNoticia (needed for context in list view)
        self.cat1 = CategoriaNoticia.objects.create(nombre='Académico', color='#000000')
        self.cat2 = CategoriaNoticia.objects.create(nombre='Eventos', color='#FFFFFF')
        
        # Create Noticias
        self.noticia1 = Noticia.objects.create(
            titulo='Noticia 1',
            bajada='Resumen 1',
            cuerpo='Cuerpo 1',
            categoria='académico', # Using choice value from model definition
            es_publica=True,
            autor=self.admin_user
        )
        self.noticia2 = Noticia.objects.create(
            titulo='Noticia 2',
            bajada='Resumen 2',
            cuerpo='Cuerpo 2',
            categoria='eventos',
            es_publica=True,
            autor=self.admin_user
        )
        self.noticia_privada = Noticia.objects.create(
            titulo='Noticia Privada',
            bajada='Resumen Privado',
            cuerpo='Cuerpo Privado',
            categoria='administrativo',
            es_publica=False,
            autor=self.admin_user
        )

    def test_noticias_list(self):
        """Test public news list view"""
        response = self.client.get(reverse('comunicacion:noticias'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Noticia 1')
        self.assertContains(response, 'Noticia 2')
        self.assertNotContains(response, 'Noticia Privada') # Should filter out private
        
    def test_noticia_detalle(self):
        """Test news detail view"""
        response = self.client.get(reverse('comunicacion:noticia_detalle', args=[self.noticia1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Noticia 1')
        self.assertContains(response, 'Cuerpo 1')
        
        # Check visit increment
        self.noticia1.refresh_from_db()
        self.assertEqual(self.noticia1.visitas, 1)

    def test_noticia_detalle_privada(self):
        """Test access to private news detail returns 404 for anonymous"""
        response = self.client.get(reverse('comunicacion:noticia_detalle', args=[self.noticia_privada.pk]))
        self.assertEqual(response.status_code, 404)

    def test_estadisticas_noticias_admin(self):
        """Test statistics view for admin"""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('comunicacion:estadisticas_noticias'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total de noticias')

    def test_estadisticas_noticias_unauthorized(self):
        """Test statistics view for non-staff"""
        user = User.objects.create_user('user', 'u@test.com', 'password')
        self.client.force_login(user)
        response = self.client.get(reverse('comunicacion:estadisticas_noticias'))
        self.assertEqual(response.status_code, 404) # View returns 404 for non-staff
