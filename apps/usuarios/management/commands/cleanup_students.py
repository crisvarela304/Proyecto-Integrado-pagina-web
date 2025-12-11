from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count

class Command(BaseCommand):
    help = 'Elimina estudiantes que no tienen registros asociados (notas, asistencia, mensajes)'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando limpieza de estudiantes sin registros...")
        
        # Filtrar usuarios que son estudiantes
        estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
        
        # Anotar con conteos de registros relacionados
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
            self.stdout.write(self.style.WARNING("No se encontraron estudiantes sin actividad para eliminar."))
            return

        self.stdout.write(f"Se encontraron {count} estudiantes sin actividad.")
        self.stdout.write("Eliminando estudiantes...")
        
        # Eliminamos
        # user.delete() borrará en cascada el PerfilUsuario e InscripcionCurso
        # Iteramos para borrar uno a uno y asegurar que se ejecuten las señales si las hay, 
        # o usamos delete() masivo si queremos rapidez. delete() masivo es mejor para "demasiados".
        deleted_count, _ = estudiantes_sin_actividad.delete()
        
        self.stdout.write(self.style.SUCCESS(f"Eliminados {deleted_count} registros (incluyendo objetos relacionados)."))
