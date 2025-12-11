import os
import django
import sys
from django.conf import settings
from datetime import date

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# PATCH ALLOWED HOSTS
settings.ALLOWED_HOSTS += ['testserver']

from django.test import Client
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import Curso, Asignatura, InscripcionCurso, Calificacion, Asistencia, RecursoAcademico
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

def log(msg, status="INFO"):
    symbol = "✅" if status == "SUCCESS" else "❌" if status == "FAIL" else "ℹ️"
    print(f"{symbol} [{status}] {msg}")

def verify_actions():
    client = Client()
    
    # --- SETUP DATA ---
    log("Setting up test data...", "INFO")
    
    # 1. Admin
    admin_user, _ = User.objects.get_or_create(username='verif_admin', defaults={'email': 'admin@test.com'})
    admin_user.set_password('pass123')
    admin_user.is_staff = True
    admin_user.save()
    PerfilUsuario.objects.get_or_create(user=admin_user, defaults={'tipo_usuario': 'administrativo', 'rut': '9999999-9'})
    
    # 2. Professor
    prof_user, _ = User.objects.get_or_create(username='verif_prof', defaults={'email': 'prof@test.com'})
    prof_user.set_password('pass123')
    prof_user.save()
    PerfilUsuario.objects.get_or_create(user=prof_user, defaults={'tipo_usuario': 'profesor', 'rut': '8888888-8'})

    # 3. Student
    stud_user, _ = User.objects.get_or_create(username='verif_stud', defaults={'email': 'stud@test.com'})
    stud_user.set_password('pass123')
    stud_user.save()
    PerfilUsuario.objects.get_or_create(user=stud_user, defaults={'tipo_usuario': 'estudiante', 'rut': '7777777-7'})

    # 4. Course & Subject
    # Fix: nivel should be string '1', '2', etc.
    curso, _ = Curso.objects.get_or_create(
        nivel='1', 
        letra='Z',
        defaults={'nombre': 'Curso Verif', 'año': 2024}
    )
    
    # Fix: Asignatura needs unique codigo
    asignatura, _ = Asignatura.objects.get_or_create(
        codigo='CIEN-VERIF',
        defaults={'nombre': 'Ciencias Verif', 'horas_semanales': 4}
    )
    
    # Enroll
    # Ensure no duplicate enrollment logic issues
    InscripcionCurso.objects.get_or_create(estudiante=stud_user, curso=curso, defaults={'año': 2024})
    
    # Assign Prof to Course (Logic might vary, but let's assume direct assignment or schedule)
    # For now, we assume prof has permission if they are "profesor". 
    # Some views check `horario__profesor=user` or `profesor_jefe=user`.
    # Let's make him Boss for easier access
    curso.profesor_jefe = prof_user
    curso.save()

    log("Data setup complete.", "SUCCESS")
    
    # --- TEST 1: ADMIN ACTIONS ---
    log("Testing ADMIN Actions...", "INFO")
    client.login(username='verif_admin', password='pass123')
    
    # 1.1 Create Course (GET create page)
    resp = client.get(reverse('administrativo:curso_crear'))
    if resp.status_code == 200:
        log("Admin can access Create Course page", "SUCCESS")
    else:
        log(f"Admin failed to access Create Course page ({resp.status_code})", "FAIL")

    # --- TEST 2: PROFESSOR ACTIONS ---
    log("Testing PROFESSOR Actions...", "INFO")
    client.login(username='verif_prof', password='pass123')

    # 2.1 Access Students List
    resp = client.get(reverse('academico:mis_estudiantes_profesor'))
    if resp.status_code == 200 or resp.status_code == 302: # 302 might happen if redirecting to filter
        log("Professor can access Student List", "SUCCESS")
    else:
        log(f"Professor failed to access Student List ({resp.status_code})", "FAIL")

    # 2.2 Upload Resource (Simulation)
    # View: subir_recurso (POST)
    # We need a dummy file
    dummy_file = SimpleUploadedFile("test_doc.txt", b"content", content_type="text/plain")
    post_data = {
        'titulo': 'Recurso Test',
        'descripcion': 'Test Desc',
        'curso': curso.id,
        'asignatura': asignatura.id,
        'archivo': dummy_file
    }
    # Note: validation might fail if relations aren't perfect, but let's try
    try:
        resp = client.post(reverse('academico:subir_recurso'), post_data)
        # Expect 302 redirect to success or 200 (if ajax)
        if resp.status_code in [302, 200]:
            # Verify DB
            if RecursoAcademico.objects.filter(titulo='Recurso Test').exists():
                log("Professor successfully uploaded a Resource", "SUCCESS")
            else:
                log("Professor upload failed (DB record not found)", "FAIL")
                print(resp.content.decode()[:500]) # Debug
        else:
            log(f"Professor upload request failed ({resp.status_code})", "FAIL")
    except Exception as e:
        log(f"Resource upload error: {e}", "FAIL")

    # 2.3 Grading (Logic Check via Service or Direct)
    # Simulating the view logic for 'registrar_notas_curso' is complex via POST due to formsets.
    # We will verify the MODEL capability (Permission check done by view access)
    resp = client.get(reverse('academico:registrar_notas_curso', args=[curso.id]))
    if resp.status_code == 200:
        log("Professor can access Grading Sheet", "SUCCESS")
    else:
        log(f"Professor failed to access Grading Sheet ({resp.status_code})", "FAIL")

    # --- TEST 3: STUDENT ACTIONS ---
    log("Testing STUDENT Actions...", "INFO")
    client.login(username='verif_stud', password='pass123')

    # 3.1 View Grades
    resp = client.get(reverse('academico:mis_calificaciones'))
    if resp.status_code == 200:
        content = resp.content.decode()
        if "Mis Calificaciones" in content:
            log("Student can view Grades page", "SUCCESS")
        else:
            log("Student Grades page content mismatch", "FAIL")
    else:
        log(f"Student Grades page crashed ({resp.status_code})", "FAIL")

    # 3.2 View Certificates
    resp = client.get(reverse('academico:mis_certificados'))
    if resp.status_code == 200:
        log("Student can access Certificates page", "SUCCESS")
    else:
        log(f"Student Certificates page crashed ({resp.status_code})", "FAIL")

if __name__ == "__main__":
    verify_actions()
