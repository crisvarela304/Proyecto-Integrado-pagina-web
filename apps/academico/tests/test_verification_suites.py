from django.test import TestCase, Client
from django.contrib.auth.models import User
from academico.models import Calificacion, Asignatura, Curso, InscripcionCurso
from usuarios.models import PerfilUsuario
from django.urls import reverse
import datetime

class SystemHealthTest(TestCase):
    def setUp(self):
        # Setup similar to verify_grading.py
        self.client = Client()
        self.student = User.objects.create_user(username='test_student_suite', password='password123')
        PerfilUsuario.objects.create(user=self.student, tipo_usuario='estudiante', rut='33333333-3')
        
        self.prof = User.objects.create_user(username='test_prof_suite', password='password123')
        PerfilUsuario.objects.create(user=self.prof, tipo_usuario='profesor', rut='44444444-4')
        
        self.curso = Curso.objects.create(nombre='Curso Suite', nivel=2, letra='B')
        self.asignatura = Asignatura.objects.create(nombre='Historia Suite')
        InscripcionCurso.objects.create(estudiante=self.student, curso=self.curso)

    def test_grading_persistence(self):
        """Verify that grades are correctly saved and retrieved (The Verify Grading Script Logic)"""
        Calificacion.objects.create(
            estudiante=self.student,
            asignatura=self.asignatura,
            curso=self.curso,
            numero_evaluacion=1,
            nota=6.5,
            profesor=self.prof,
            tipo_evaluacion='nota',
            fecha_evaluacion=datetime.date.today(),
            semestre='1'
        )
        
        exists = Calificacion.objects.filter(
            estudiante=self.student,
            asignatura=self.asignatura,
            nota=6.5
        ).exists()
        
        self.assertTrue(exists, "Grade was not saved to database!")

    def test_critical_routes(self):
        """Verify that critical pages load (The Verify Routes Script Logic)"""
        urls_to_check = [
            'home',
            'usuarios:login',
        ]
        
        for name in urls_to_check:
            url = reverse(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Route {name} failed with {response.status_code}")

    def test_panel_access_auth(self):
        """Verify panel is protected"""
        url = reverse('usuarios:panel')
        response = self.client.get(url)
        # Should redirect to login because we are not logged in
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_role_dashboards(self):
        """Verify that Admin, Professor, and Student dashboards load correctly"""
        # 1. ADMIN (Administrativo) Check
        # Should be able to access the admin dashboard
        admin_user = User.objects.create_user(username='admin_check', password='password123')
        PerfilUsuario.objects.create(user=admin_user, tipo_usuario='administrativo', rut='55555555-5')
        self.client.login(username='admin_check', password='password123')
        
        resp_admin = self.client.get(reverse('administrativo:dashboard'))
        self.assertEqual(resp_admin.status_code, 200, "Admin Dashboard failed to load")

        # 2. PROFESSOR Check
        # Should be able to access the professor specific panel logic on the main panel
        self.client.logout()
        self.client.login(username='test_prof_suite', password='password123')
        # panel_profesor is a redirect to usuarios:panel, so we check usuarios:panel directly
        # or we check that panel_profesor redirects correctly. Let's check the destination content.
        resp_prof = self.client.get(reverse('usuarios:panel')) 
        self.assertEqual(resp_prof.status_code, 200, "Professor Panel (usuarios:panel) failed to load")
        # Optional: Check for prof specific content if needed, but 200 is enough for now.

        # 3. STUDENT Check
        # Should receive 200 on the general user panel (landing)
        self.client.logout()
        self.client.login(username='test_student_suite', password='password123')
        resp_stud_panel = self.client.get(reverse('usuarios:panel'))
        self.assertEqual(resp_stud_panel.status_code, 200, "Student General Panel failed to load")
        
        # And also check specific student view (Grades)
        resp_stud_grades = self.client.get(reverse('academico:mis_calificaciones'))
        self.assertEqual(resp_stud_grades.status_code, 200, "Student Grades View failed to load")

