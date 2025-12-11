from django.db import models
from django.contrib.auth.models import User

class RegistroActividad(models.Model):
    """
    Registro de auditoría para todas las acciones importantes del sistema.
    """
    TIPO_ACCION_CHOICES = [
        ('login', 'Inicio de Sesión'),
        ('nota', 'Registro de Notas'),
        ('asistencia', 'Registro de Asistencia'),
        ('recurso', 'Recurso Académico'),
        ('anotacion', 'Anotación/Hoja de Vida'),
        ('usuario', 'Gestión de Usuarios'),
        ('curso', 'Gestión de Cursos'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actividades')
    tipo_accion = models.CharField(max_length=20, choices=TIPO_ACCION_CHOICES)
    descripcion = models.CharField(max_length=255, help_text="Descripción breve de la acción")
    detalles = models.TextField(blank=True, help_text="Detalles técnicos o JSON")
    fecha = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Registro de Actividad"
        verbose_name_plural = "Registros de Actividad"

    def __str__(self):
        user_str = self.usuario.username if self.usuario else "Sistema"
        return f"[{self.get_tipo_accion_display()}] {user_str}: {self.descripcion}"
