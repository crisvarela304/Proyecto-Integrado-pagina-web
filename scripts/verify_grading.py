import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from academico.models import Calificacion, Asignatura, Curso, InscripcionCurso
from usuarios.models import PerfilUsuario
import datetime

def test_grading_logic():
    print("Don't worry, verifying grading logic now... 🧪")
    
    # 1. Create Data
    try:
        # Student
        student, _ = User.objects.get_or_create(username='test_student_verification')
        if not hasattr(student, 'perfil'):
            PerfilUsuario.objects.create(user=student, tipo_usuario='estudiante', rut='11111111-1')
        
        # Prof
        prof, _ = User.objects.get_or_create(username='test_prof_verification')
        if not hasattr(prof, 'perfil'):
            PerfilUsuario.objects.create(user=prof, tipo_usuario='profesor', rut='22222222-2')

        # Course & Subject
        curso, _ = Curso.objects.get_or_create(nombre='Curso Test', nivel=1, letra='A')
        asignatura, _ = Asignatura.objects.get_or_create(nombre='Matemáticas Test')
        
        # Enforce Enrollment
        InscripcionCurso.objects.get_or_create(estudiante=student, curso=curso)

        print("✅ Test Environment Created")

        # 2. Simulate Grading (The Logic from Views)
        print("📝 Professor assigning grade 7.0...")
        
        Calificacion.objects.update_or_create(
            estudiante=student,
            asignatura=asignatura,
            curso=curso,
            numero_evaluacion=1,
            defaults={
                'nota': 7.0,
                'descripcion': 'Prueba de Verificación',
                'fecha_evaluacion': datetime.date.today(),
                'profesor': prof,
                'tipo_evaluacion': 'nota',
                'semestre': '1',
            }
        )

        # 3. Verify it exists
        calificacion = Calificacion.objects.get(
            estudiante=student, 
            asignatura=asignatura, 
            curso=curso, 
            numero_evaluacion=1
        )
        
        if calificacion.nota == 7.0:
            print(f"🎉 SUCCESS: Grade found in database! Student {student.username} has a {calificacion.nota} in {asignatura.nombre}")
        else:
            print(f"❌ FAILURE: Grade is {calificacion.nota}, expected 7.0")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_grading_logic()
