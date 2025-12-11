from django.test import TestCase, Client
from django.urls import reverse

class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_login_view_status_code(self):
        # Assuming 'usuarios:login' is the URL name for login
        response = self.client.get(reverse('usuarios:login'))
        self.assertEqual(response.status_code, 200)
