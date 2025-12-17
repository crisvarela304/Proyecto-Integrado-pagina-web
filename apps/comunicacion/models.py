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
        ('consejo', 'Consejo de Profesores'),
    ]
    
    titulo = models.CharField(max_length=150)
    bajada = models.CharField("Resumen", max_length=200, blank=True)
    cuerpo = models.TextField()
    portada = models.ImageField(upload_to="noticias/", blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='académico')
    es_publica = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    urgente = models.BooleanField(default=False)
    requiere_confirmacion = models.BooleanField(
        default=False,
        help_text='Si está activo, los usuarios deben confirmar que leyeron este comunicado'
    )
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    visitas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-destacado", "-urgente", "-creado"]

    def __str__(self):
        return f"{self.titulo} - {self.get_categoria_display()}"

    def increment_visits(self):
        """Incrementa el contador de visitas de forma atómica"""
        from django.db.models import F
        self.visitas = F('visitas') + 1
        self.save(update_fields=['visitas'])
        self.refresh_from_db()
    
    def confirmaciones_count(self):
        """Retorna la cantidad de confirmaciones de lectura"""
        return self.confirmaciones.count()
    
    def usuario_confirmo(self, user):
        """Verifica si un usuario ya confirmó la lectura"""
        return self.confirmaciones.filter(usuario=user).exists()


class ConfirmacionLectura(models.Model):
    """Registro de confirmación de lectura de noticias/comunicados"""
    noticia = models.ForeignKey(
        Noticia, 
        on_delete=models.CASCADE, 
        related_name='confirmaciones'
    )
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='lecturas_confirmadas'
    )
    fecha_confirmacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Confirmación de Lectura'
        verbose_name_plural = 'Confirmaciones de Lectura'
        unique_together = ['noticia', 'usuario']
        ordering = ['-fecha_confirmacion']
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} leyó '{self.noticia.titulo}'"
