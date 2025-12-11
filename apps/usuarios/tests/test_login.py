from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario

class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'password123'
        
        # Create Student User
        self.student_user = User.objects.create_user(
            username='11111111-1', 
            password=self.password
        )
        self.student_profile = PerfilUsuario.objects.create(
            user=self.student_user,
            rut='11111111-1',
            tipo_usuario='estudiante'
        )
        
        # Create Professor User
        self.profesor_user = User.objects.create_user(
            username='22222222-2', 
            password=self.password
        )
        self.profesor_profile = PerfilUsuario.objects.create(
            user=self.profesor_user,
            rut='22222222-2',
            tipo_usuario='profesor'
        )

    def test_login_success_student(self):
        """Test successful login for a student"""
        response = self.client.post(reverse('usuarios:login'), {
            'rut_o_username': '11111111-1',
            'password': self.password
        })
        self.assertEqual(response.status_code, 302) # Redirects generally mean success
        self.assertRedirects(response, reverse('usuarios:panel'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_success_professor(self):
        """Test successful login for a professor"""
        response = self.client.post(reverse('usuarios:login'), {
            'rut_o_username': '22222222-2',
            'password': self.password
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('usuarios:panel'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_failure_invalid_credentials(self):
        """Test login failure with wrong password"""
        response = self.client.post(reverse('usuarios:login'), {
            'rut_o_username': '11111111-1',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200) # Returns to login page with errors
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        # Check if form error is displayed (assuming standard auth form use)
        self.assertContains(response, "RUT/Usuario o contraseña incorrectos")

    def test_logout(self):
        """Test logout functionality"""
        self.client.login(username='11111111-1', password=self.password)
        response = self.client.post(reverse('usuarios:logout'))
        self.assertEqual(response.status_code, 302) # Redirect after logout
        self.assertFalse(response.wsgi_request.user.is_authenticated)
