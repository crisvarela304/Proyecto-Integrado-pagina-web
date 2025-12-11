import os
import sys
import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def reset_users():
    print("Iniciando reseteo de usuarios...")
    
    # 1. Borrar usuarios no superusuarios
    count, _ = User.objects.filter(is_superuser=False).delete()
    print(f"Se eliminaron {count} usuarios no administrativos.")
    
    # 2. Crear Profesor de prueba
    profesor, created = User.objects.get_or_create(
        username='profesor1',
        defaults={
            'email': 'profesor1@liceo.cl',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'is_staff': False
        }
    )
    profesor.set_password('profe123')
    profesor.save()
    
    # Asignar grupo/perfil si existe
    try:
        from usuarios.models import PerfilUsuario
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=profesor)
        perfil.tipo_usuario = 'profesor'
        perfil.rut = '11111111-1'
        perfil.telefono = '+56911111111'
        perfil.direccion = 'Calle Falsa 123'
        perfil.save()
        print("Perfil de profesor creado/actualizado.")
    except ImportError:
        print("No se pudo importar PerfilUsuario, saltando creación de perfil.")
    except Exception as e:
        print(f"Error creando perfil profesor: {e}")

    print(f"Usuario 'profesor1' creado/reseteado con éxito.")

    # 3. Crear Alumno de prueba
    alumno, created = User.objects.get_or_create(
        username='alumno1',
        defaults={
            'email': 'alumno1@liceo.cl',
            'first_name': 'Pedro',
            'last_name': 'González',
            'is_staff': False
        }
    )
    alumno.set_password('alumno123')
    alumno.save()
    
    try:
        from usuarios.models import PerfilUsuario
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=alumno)
        perfil.tipo_usuario = 'estudiante'
        perfil.rut = '22222222-2'
        perfil.telefono = '+56922222222'
        perfil.direccion = 'Calle Real 456'
        perfil.save()
        print("Perfil de estudiante creado/actualizado.")
    except Exception as e:
        print(f"Error creando perfil estudiante: {e}")

    print(f"Usuario 'alumno1' creado/reseteado con éxito.")
    print("="*50)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("="*50)

if __name__ == '__main__':
    reset_users()
