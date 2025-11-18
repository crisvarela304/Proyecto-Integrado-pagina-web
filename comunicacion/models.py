from django.db import models
from django.contrib.auth.models import User

class CategoriaNoticia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#007bff')  # Color hex para badges
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Noticia(models.Model):
    CATEGORIAS = [
        ('académico', 'Académico'),
        ('actividades', 'Actividades'),
        ('convivencia', 'Convivencia Escolar'),
        ('eventos', 'Eventos'),
        ('deportes', 'Deportes'),
        ('cultura', 'Cultura'),
        ('administrativo', 'Administrativo'),
        ('comunicado', 'Comunicado'),
    ]
    
    titulo = models.CharField(max_length=150)
    bajada = models.CharField("Resumen", max_length=200, blank=True)
    cuerpo = models.TextField()
    portada = models.ImageField(upload_to="noticias/", blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='académico')
    es_publica = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    urgente = models.BooleanField(default=False)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    visitas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-destacado", "-urgente", "-creado"]

    def __str__(self):
        return f"{self.titulo} - {self.get_categoria_display()}"

    def increment_visits(self):
        """Incrementa el contador de visitas"""
        self.visitas += 1
        self.save(update_fields=['visitas'])
