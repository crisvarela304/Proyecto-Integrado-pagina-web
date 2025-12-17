from django.db import models

class ConfiguracionSistema(models.Model):
    """Configuraciones generales del sistema"""
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        ordering = ['clave']

    def __str__(self):
        return f"{self.clave}: {self.valor[:50]}{'...' if len(self.valor) > 50 else ''}"

class ConfiguracionAcademica(models.Model):
    """Configuración global del año y semestre académico (Singleton)"""
    año_actual = models.PositiveIntegerField(default=2024, verbose_name="Año Escolar Actual")
    SEMESTRE_CHOICES = [
        ('1', 'Primer Semestre'),
        ('2', 'Segundo Semestre'),
    ]
    semestre_actual = models.CharField(max_length=1, choices=SEMESTRE_CHOICES, default='1')
    
    class Meta:
        verbose_name = "Configuración Académica"
        verbose_name_plural = "Configuración Académica"

    def save(self, *args, **kwargs):
        # Garantizar que solo exista una instancia (ID=1)
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Año {self.año_actual} - Semestre {self.semestre_actual}"

    @classmethod
    def get_actual(cls):
        """Retorna la configuración actual, creándola si no existe"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Notificacion(models.Model):
    """Sistema de notificaciones web para usuarios"""
    from django.contrib.auth.models import User
    
    TIPO_CHOICES = [
        ('info', 'Información'),
        ('tarea', 'Nueva Tarea'),
        ('nota', 'Nueva Calificación'),
        ('mensaje', 'Nuevo Mensaje'),
        ('evento', 'Evento'),
        ('alerta', 'Alerta'),
    ]
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notificaciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True, help_text='URL a la que redirige al hacer clic')
    
    leida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo}"
    
    @classmethod
    def crear_notificacion(cls, usuario, tipo, titulo, mensaje='', url=''):
        """Método helper para crear notificaciones fácilmente"""
        return cls.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            url=url
        )
    
    @classmethod
    def no_leidas_count(cls, usuario):
        """Retorna el número de notificaciones no leídas"""
        return cls.objects.filter(usuario=usuario, leida=False).count()
