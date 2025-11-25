from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class CategoriaDocumento(models.Model):
    """Categorías de documentos institucionales"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Color para la UI
    icono = models.CharField(max_length=50, default='bi-file-earmark')  # Bootstrap icon
    orden = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoría de Documento"
        verbose_name_plural = "Categorías de Documentos"
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

class Documento(models.Model):
    """Documentos institucionales del liceo"""
    VISIBILIDAD_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
        ('solo_estudiantes', 'Solo Estudiantes'),
        ('solo_profesores', 'Solo Profesores'),
        ('solo_administrativos', 'Solo Administrativos'),
    ]
    
    TIPO_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'Word'),
        ('xls', 'Excel'),
        ('ppt', 'PowerPoint'),
        ('img', 'Imagen'),
        ('zip', 'Archivo comprimido'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to='documentos/', null=True, blank=True)
    categoria = models.ForeignKey(CategoriaDocumento, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='pdf')
    visibilidad = models.CharField(max_length=20, choices=VISIBILIDAD_CHOICES, default='publico')
    tags = models.CharField(max_length=200, blank=True, help_text="Separados por comas")
    tamaño = models.PositiveIntegerField(default=0, help_text="Tamaño en bytes")
    descargar_count = models.PositiveIntegerField(default=0)
    version = models.CharField(max_length=10, default='1.0')
    es_oficial = models.BooleanField(default=False, help_text="Documento oficial del establecimiento")
    publicado = models.BooleanField(default=True)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('documentos:documento_detalle', kwargs={'pk': self.pk})

    @property
    def tamaño_formateado(self):
        """Retorna el tamaño en formato legible"""
        if self.tamaño < 1024:
            return f"{self.tamaño} B"
        elif self.tamaño < 1024 * 1024:
            return f"{self.tamaño / 1024:.1f} KB"
        else:
            return f"{self.tamaño / (1024 * 1024):.1f} MB"

class HistorialDescargas(models.Model):
    """Historial de descargas de documentos"""
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='descargas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='descargas_documentos')
    fecha_descarga = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = "Descarga"
        verbose_name_plural = "Descargas"
        ordering = ['-fecha_descarga']

    def __str__(self):
        return f"{self.usuario.username} - {self.documento.titulo}"

class ComunicadoPadres(models.Model):
    """Comunicados dirigidos a padres y apoderados"""
    URGENCIA_CHOICES = [
        ('normal', 'Normal'),
        ('importante', 'Importante'),
        ('urgente', 'Urgente'),
    ]
    
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    urgencia = models.CharField(max_length=15, choices=URGENCIA_CHOICES, default='normal')
    dirigido_a = models.CharField(max_length=50, default='todos', help_text="todos, padres, apoderados, estudiantes")
    cursos_objetivo = models.ManyToManyField('academico.Curso', blank=True, related_name='comunicados')
    publicado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comunicados_publicados')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    leido_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Comunicado a Padres"
        verbose_name_plural = "Comunicados a Padres"
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return self.titulo
