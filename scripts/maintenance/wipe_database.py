import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model

User = get_user_model()

def wipe_database():
    print("⚠️  INICIANDO LIMPIEZA PROFUNDA DE LA BASE DE DATOS ⚠️")
    print("="*60)
    
    # Get models safely
    Calificacion = apps.get_model('academico', 'Calificacion')
    Asistencia = apps.get_model('academico', 'Asistencia')
    HorarioClases = apps.get_model('academico', 'HorarioClases')
    InscripcionCurso = apps.get_model('academico', 'InscripcionCurso')
    Asignatura = apps.get_model('academico', 'Asignatura')
    Curso = apps.get_model('academico', 'Curso')
    PerfilUsuario = apps.get_model('usuarios', 'PerfilUsuario')

    # 1. Eliminar datos académicos dependientes
    print("1. Eliminando Calificaciones...")
    Calificacion.objects.all().delete()
    
    print("2. Eliminando Asistencias...")
    Asistencia.objects.all().delete()
    
    print("3. Eliminando Horarios...")
    HorarioClases.objects.all().delete()
    
    print("4. Eliminando Inscripciones...")
    InscripcionCurso.objects.all().delete()
    
    # 2. Eliminar estructura académica
    print("5. Eliminando Asignaturas...")
    Asignatura.objects.all().delete()
    
    print("6. Eliminando Cursos...")
    Curso.objects.all().delete()
    
    # 3. Eliminar Usuarios (excepto superusuarios)
    print("7. Eliminando Usuarios (Estudiantes, Profesores, etc)...")
    # Guardamos los IDs de superusuarios para no borrarlos
    superusers_ids = User.objects.filter(is_superuser=True).values_list('id', flat=True)
    
    # Borramos perfiles primero
    PerfilUsuario.objects.exclude(user_id__in=superusers_ids).delete()
    
    # Borramos usuarios
    deleted_count, _ = User.objects.exclude(is_superuser=True).delete()
    print(f"   -> Se eliminaron {deleted_count} usuarios.")
    
    print("="*60)
    print("✅ LIMPIEZA COMPLETADA. Solo quedan los administradores.")

if __name__ == '__main__':
    wipe_database()
