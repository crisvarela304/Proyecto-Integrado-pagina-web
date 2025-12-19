"""
Modelos para el Sistema de Tareas Escolares.
Permite a profesores asignar tareas y a estudiantes entregarlas.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from academico.models import Curso, Asignatura


class Tarea(models.Model):
    """Tarea asignada por un profesor a un curso"""
    TIPO_CHOICES = [
        ('tarea', 'Tarea'),
        ('trabajo', 'Trabajo de Investigación'),
        ('proyecto', 'Proyecto'),
        ('lectura', 'Lectura'),
        ('ejercicio', 'Ejercicios'),
    ]
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    titulo = models.CharField('Título', max_length=200)
    descripcion = models.TextField('Descripción')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='tarea')
    
    curso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE, 
        related_name='tareas'
    )
    asignatura = models.ForeignKey(
        Asignatura, 
        on_delete=models.CASCADE, 
        related_name='tareas'
    )
    profesor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='tareas_creadas'
    )
    
    fecha_asignacion = models.DateField('Fecha de Asignación', auto_now_add=True)
    fecha_entrega = models.DateField('Fecha de Entrega')
    hora_limite = models.TimeField('Hora Límite', null=True, blank=True)
    
    puntaje_maximo = models.DecimalField(
        'Puntaje Máximo', 
        max_digits=5, 
        decimal_places=1, 
        default=100
    )
    
    archivo_adjunto = models.FileField(
        'Archivo Adjunto', 
        upload_to='tareas/adjuntos/', 
        blank=True, 
        null=True
    )
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='publicada')
    permite_entrega_tardia = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
        ordering = ['-fecha_entrega']
    
    def __str__(self):
        return f"{self.titulo} - {self.curso.nombre}"
    
    @property
    def esta_vencida(self):
        from datetime import date
        return date.today() > self.fecha_entrega
    
    def entregas_count(self):
        return self.entregas.count()
    
    def entregas_pendientes(self, curso):
        """Retorna estudiantes sin entregar"""
        from academico.models import InscripcionCurso
        from core.models import ConfiguracionAcademica
        
        anio = ConfiguracionAcademica.get_actual().año_actual
        estudiantes_curso = InscripcionCurso.objects.filter(
            curso=curso, año=anio, estado='activo'
        ).values_list('estudiante_id', flat=True)
        
        entregaron = self.entregas.values_list('estudiante_id', flat=True)
        
        return User.objects.filter(id__in=estudiantes_curso).exclude(id__in=entregaron)


class Entrega(models.Model):
    """Entrega de tarea por un estudiante"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Revisión'),
        ('revisada', 'Revisada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada - Rehacer'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    tarea = models.ForeignKey(
        Tarea, 
        on_delete=models.CASCADE, 
        related_name='entregas'
    )
    estudiante = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='entregas_tareas'
    )
    
    archivo = models.FileField('Archivo Entregado', upload_to='tareas/entregas/')
    comentario_estudiante = models.TextField('Comentario del Estudiante', blank=True)
    
    fecha_entrega = models.DateTimeField('Fecha de Entrega', auto_now_add=True)
    entrega_tardia = models.BooleanField(default=False)
    
    # Calificación
    puntaje = models.DecimalField(
        'Puntaje Obtenido', 
        max_digits=5, 
        decimal_places=1, 
        null=True, 
        blank=True
    )
    comentario_profesor = models.TextField('Retroalimentación', blank=True)
    fecha_revision = models.DateTimeField('Fecha de Revisión', null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'
        unique_together = ['tarea', 'estudiante']
        ordering = ['-fecha_entrega']
    
    def __str__(self):
        return f"{self.estudiante.get_full_name()} - {self.tarea.titulo}"
    
    def save(self, *args, **kwargs):
        # Marcar si es entrega tardía
        if not self.pk:
            from datetime import date
            if date.today() > self.tarea.fecha_entrega:
                self.entrega_tardia = True
        super().save(*args, **kwargs)
