import os
import sys
import django
from django.db.models import Count, Q

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.usuarios.models import PerfilUsuario

def cleanup_students():
    print("Iniciando limpieza de estudiantes sin registros...")
    
    # Filtrar usuarios que son estudiantes
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    
    # Anotar con conteos de registros relacionados
    # Usamos los related_names definidos en los modelos
    estudiantes_sin_actividad = estudiantes.annotate(
        num_calificaciones=Count('calificaciones', distinct=True),
        num_asistencias=Count('asistencias', distinct=True),
        num_conversaciones=Count('conversaciones_como_alumno', distinct=True),
        num_mensajes_enviados=Count('mensajes_enviados', distinct=True),
        num_mensajes_recibidos=Count('mensajes_recibidos', distinct=True),
        num_contactos=Count('contactocolegio', distinct=True)
    ).filter(
        num_calificaciones=0,
        num_asistencias=0,
        num_conversaciones=0,
        num_mensajes_enviados=0,
        num_mensajes_recibidos=0,
        num_contactos=0
    )
    
    count = estudiantes_sin_actividad.count()
    
    if count == 0:
        print("No se encontraron estudiantes sin actividad para eliminar.")
        return

    print(f"Se encontraron {count} estudiantes sin actividad.")
    
    # Confirmación (opcional en script, pero bueno para logs)
    print("Eliminando estudiantes...")
    
    # Eliminamos en lotes o directamente
    # user.delete() borrará en cascada el PerfilUsuario e InscripcionCurso
    deleted_count, _ = estudiantes_sin_actividad.delete()
    
    print(f"Eliminados {deleted_count} registros (incluyendo objetos relacionados).")
    print("Limpieza completada exitosamente.")

if __name__ == "__main__":
    cleanup_students()
