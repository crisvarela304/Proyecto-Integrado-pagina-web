import uuid
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


class ColegioConfig(models.Model):
    """
    Configuración única del colegio (Singleton).
    Usado por el Phone Home Protocol para auto-registro con el Directorio Central.
    """
    codigo = models.CharField(
        max_length=8, 
        unique=True, 
        help_text='Código único del colegio (ej: COLE-A1B2)'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Colegio')
    url = models.URLField(
        blank=True, 
        help_text='URL pública del colegio (ej: https://colegio.schoolar.cl)'
    )
    
    # Branding para la App
    logo = models.ImageField(upload_to='colegio/', blank=True, null=True)
    color_primario = models.CharField(max_length=7, default='#1976D2', help_text='Color HEX')
    color_secundario = models.CharField(max_length=7, default='#424242', help_text='Color HEX')
    
    # Estado de registro
    registrado_en_directorio = models.BooleanField(
        default=False, 
        help_text='True si el colegio ya se registró con el Directorio Central'
    )
    fecha_registro = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración del Colegio'
        verbose_name_plural = 'Configuración del Colegio'
    
    def save(self, *args, **kwargs):
        # Singleton: siempre PK=1
        self.pk = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @classmethod
    def get_config(cls):
        """Retorna la configuración del colegio, creándola si no existe"""
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'codigo': cls._generate_code(),
                'nombre': 'Mi Colegio'
            }
        )
        return obj
    
    @staticmethod
    def _generate_code():
        """Genera un código único de 8 caracteres"""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        return 'COLE-' + ''.join(random.choices(chars, k=4))

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
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
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
