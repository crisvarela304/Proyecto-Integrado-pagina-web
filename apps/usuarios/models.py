from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class PerfilUsuario(models.Model):
    """Perfil extendido del usuario para almacenar información adicional como RUT"""
    TIPO_USUARIO = [
        ('estudiante', 'Estudiante'),
        ('apoderado', 'Apoderado'),
        ('profesor', 'Profesor'),
        ('administrativo', 'Administrativo'),
        ('directivo', 'Directivo'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rut = models.CharField('RUT', max_length=12, unique=True, help_text='Ej: 12.345.678-9')
    tipo_usuario = models.CharField(max_length=15, choices=TIPO_USUARIO, default='estudiante')
    telefono = models.CharField(max_length=15, blank=True)
    telefono_estudiante = models.CharField(max_length=20, blank=True)
    telefono_apoderado = models.CharField(max_length=20, blank=True)
    foto_perfil = models.ImageField(upload_to="perfiles/", blank=True, null=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.rut}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return self.user.get_full_name() or self.user.username

    def clean(self):
        """Valida el RUT antes de guardar"""
        from core.utils import validar_rut
        super().clean()
        if self.rut and not validar_rut(self.rut):
            raise ValidationError({'rut': 'El RUT ingresado no es válido.'})


