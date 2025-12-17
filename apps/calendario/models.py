"""
Modelos para el Calendario Escolar.
"""
from django.db import models
from django.contrib.auth.models import User
from academico.models import Curso


class Evento(models.Model):
    """Evento del calendario escolar"""
    TIPO_CHOICES = [
        ('academico', 'Académico'),
        ('festivo', 'Festivo'),
        ('reunion', 'Reunión'),
        ('evaluacion', 'Evaluación'),
        ('feriado', 'Feriado'),
        ('actividad', 'Actividad Extracurricular'),
        ('otro', 'Otro'),
    ]
    
    COLOR_CHOICES = [
        ('#3788d8', 'Azul'),
        ('#dc3545', 'Rojo'),
        ('#28a745', 'Verde'),
        ('#ffc107', 'Amarillo'),
        ('#6f42c1', 'Morado'),
        ('#17a2b8', 'Celeste'),
        ('#6c757d', 'Gris'),
    ]
    
    titulo = models.CharField('Título', max_length=200)
    descripcion = models.TextField('Descripción', blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='academico')
    
    fecha_inicio = models.DateField('Fecha de Inicio')
    fecha_fin = models.DateField('Fecha de Fin', null=True, blank=True)
    todo_el_dia = models.BooleanField('Todo el día', default=True)
    hora_inicio = models.TimeField('Hora de Inicio', null=True, blank=True)
    hora_fin = models.TimeField('Hora de Fin', null=True, blank=True)
    
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='#3788d8')
    
    # Opcional: evento para un curso específico
    curso = models.ForeignKey(
        Curso, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='eventos',
        help_text='Dejar vacío para evento general'
    )
    
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='eventos_creados'
    )
    
    visible_para_todos = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['fecha_inicio']
    
    def __str__(self):
        return f"{self.titulo} ({self.fecha_inicio})"
    
    def to_fullcalendar(self):
        """Retorna dict compatible con FullCalendar"""
        event = {
            'id': self.id,
            'title': self.titulo,
            'start': str(self.fecha_inicio),
            'color': self.color,
            'allDay': self.todo_el_dia,
            'extendedProps': {
                'tipo': self.tipo,
                'descripcion': self.descripcion,
            }
        }
        
        if self.fecha_fin:
            event['end'] = str(self.fecha_fin)
        
        if not self.todo_el_dia and self.hora_inicio:
            event['start'] = f"{self.fecha_inicio}T{self.hora_inicio}"
            if self.hora_fin:
                end_date = self.fecha_fin or self.fecha_inicio
                event['end'] = f"{end_date}T{self.hora_fin}"
        
        return event
