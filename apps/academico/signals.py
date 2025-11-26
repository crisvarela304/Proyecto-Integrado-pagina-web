from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Calificacion, InscripcionCurso
from usuarios.models import PerfilUsuario

@receiver([post_save, post_delete], sender=Calificacion)
def actualizar_promedios(sender, instance, **kwargs):
    """
    Actualiza el promedio del curso y el promedio general del estudiante
    cada vez que se guarda o elimina una calificación.
    """
    estudiante = instance.estudiante
    curso = instance.curso
    
    # 1. Actualizar promedio del curso específico
    inscripcion = InscripcionCurso.objects.filter(estudiante=estudiante, curso=curso).first()
    if inscripcion:
        promedio_curso = Calificacion.objects.filter(
            estudiante=estudiante, 
            curso=curso
        ).aggregate(Avg('nota'))['nota__avg']
        
        inscripcion.promedio = round(promedio_curso, 1) if promedio_curso else None
        inscripcion.save()
        
    # 2. Actualizar promedio general del estudiante
    perfil = getattr(estudiante, 'perfil', None)
    if perfil:
        promedio_general = Calificacion.objects.filter(
            estudiante=estudiante
        ).aggregate(Avg('nota'))['nota__avg']
        
        perfil.promedio_general = round(promedio_general, 1) if promedio_general else None
        perfil.save()
