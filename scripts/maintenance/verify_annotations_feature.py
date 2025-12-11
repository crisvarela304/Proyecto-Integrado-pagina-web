
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# Setup Django environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Django imports (MUST be after setup)
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from academico.models import Anotacion
from usuarios.models import PerfilUsuario

def run_verification():
    print("🚀 Iniciando Verificación Automática del Sistema de Anotaciones")
    print("==============================================================")

    # 1. Setup Temporary Users
    print("\n1. Creando usuarios de prueba...")
    try:
        # Pre-cleanup in case of previous failure
        User.objects.filter(username__in=['test_student_v', 'test_prof_v', 'test_admin_v']).delete()
        
        # Create Student
        student_user = User.objects.create_user(username='test_student_v', password='password123', email='test_s@mail.com', first_name='Test', last_name='Student')
        PerfilUsuario.objects.create(user=student_user, tipo_usuario='estudiante', rut='11111111-1')
        print(f"   ✅ Estudiante creado: {student_user.username}")

        # Create Professor
        prof_user = User.objects.create_user(username='test_prof_v', password='password123', email='test_p@mail.com', first_name='Test', last_name='Prof')
        PerfilUsuario.objects.create(user=prof_user, tipo_usuario='profesor', rut='22222222-2')
        print(f"   ✅ Profesor creado: {prof_user.username}")

        # Create Admin
        admin_user = User.objects.create_user(username='test_admin_v', password='password123', email='test_a@mail.com', is_staff=True, is_superuser=True)
        PerfilUsuario.objects.create(user=admin_user, tipo_usuario='administrativo', rut='33333333-3')
        print(f"   ✅ Administrativo creado: {admin_user.username}")

    except Exception as e:
        print(f"   ❌ Error creando usuarios: {e}")
        return

    client = Client()

    # 2. Test Professor Creating Annotation
    print("\n2. Probando creación de anotación (Profesor)...")
    try:
        client.login(username='test_prof_v', password='password123')
        url = reverse('academico:crear_anotacion', args=[student_user.id])
        data = {
            'tipo': 'positiva',
            'categoria': 'responsabilidad',
            'observacion': 'Esta es una anotación de prueba automática.'
        }
        response = client.post(url, data, follow=True)
        
        if response.status_code == 200 and 'Anotación registrada' in response.content.decode():
            print("   ✅ Profesor pudo crear la anotación correctamente.")
        else:
            print(f"   ⚠️ Respuesta inesperada: Status {response.status_code}")
            # Verificamos si se creó el objeto no obstante
            if Anotacion.objects.filter(observacion='Esta es una anotación de prueba automática.').exists():
                 print("   ✅ (Objeto creado en DB aunque la redirección/mensaje varió)")
            else:
                 print("   ❌ No se creó la anotación en la DB.")
    
    except Exception as e:
        print(f"   ❌ Error en prueba de profesor: {e}")

    # 3. Test Student Viewing Annotation
    print("\n3. Probando visualización (Estudiante)...")
    try:
        client.logout()
        client.login(username='test_student_v', password='password123')
        url = reverse('academico:mis_anotaciones')
        response = client.get(url)
        
        content = response.content.decode()
        if 'Esta es una anotación de prueba automática.' in content:
            print("   ✅ Estudiante puede ver su anotación en el dashboard.")
        else:
            print("   ❌ Estudiante NO ve la anotación.")
            
    except Exception as e:
        print(f"   ❌ Error en prueba de estudiante: {e}")

    # 4. Test Admin Viewing History
    print("\n4. Probando historial (Administrativo)...")
    try:
        client.logout()
        client.login(username='test_admin_v', password='password123')
        url = reverse('academico:historial_anotaciones', args=[student_user.id])
        response = client.get(url)
        
        if response.status_code == 200 and 'Esta es una anotación de prueba automática.' in response.content.decode():
             print("   ✅ Administrativo ve el historial correctamente.")
        else:
             print("   ❌ Administrativo no pudo ver el historial correctamente.")

    except Exception as e:
        print(f"   ❌ Error en prueba de administrativo: {e}")

    # 5. Teardown
    print("\n5. Limpieza de datos (Borrado)...")
    try:
        # Deleting users should cascade delete annotations
        cnt_before = Anotacion.objects.filter(estudiante=student_user).count()
        print(f"   Anotaciones antes de borrar usuario: {cnt_before}")
        
        student_user.delete()
        prof_user.delete()
        admin_user.delete()
        
        # Verify annotation is gone
        cnt_after = Anotacion.objects.filter(observacion='Esta es una anotación de prueba automática.').count()
        if cnt_after == 0:
            print("   ✅ Usuarios y datos eliminados correctamente (Cascade delete funcionó).")
        else:
            print(f"   ❌ ALERTA: Quedaron {cnt_after} anotaciones huérfanas.")

    except Exception as e:
        print(f"   ❌ Error durante la limpieza: {e}")

    print("\n==============================================================")
    print("🏁 Verificación Completada")

if __name__ == "__main__":
    run_verification()
