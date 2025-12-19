import uuid
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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    rut = models.CharField('RUT', max_length=12, unique=True, help_text='Ej: 12.345.678-9')
    tipo_usuario = models.CharField(max_length=15, choices=TIPO_USUARIO, default='estudiante')
    telefono = models.CharField(max_length=15, blank=True)
    telefono_estudiante = models.CharField(max_length=20, blank=True)
    telefono_apoderado = models.CharField(max_length=20, blank=True)
    foto_perfil = models.ImageField(upload_to="perfiles/", blank=True, null=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    promedio_general = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Promedio general calculado automáticamente")
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'usuarios'
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


class Pupilo(models.Model):
    """
    Relación entre Apoderado y Estudiante.
    Permite que un apoderado tenga múltiples pupilos y viceversa.
    """
    VINCULO_CHOICES = [
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('tutor', 'Tutor Legal'),
        ('abuelo', 'Abuelo/a'),
        ('otro', 'Otro Familiar'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    apoderado = models.ForeignKey(
        PerfilUsuario, 
        on_delete=models.CASCADE, 
        related_name='pupilos',
        limit_choices_to={'tipo_usuario': 'apoderado'},
        verbose_name='Apoderado'
    )
    estudiante = models.ForeignKey(
        PerfilUsuario, 
        on_delete=models.CASCADE, 
        related_name='apoderados',
        limit_choices_to={'tipo_usuario': 'estudiante'},
        verbose_name='Estudiante'
    )
    vinculo = models.CharField(
        'Vínculo Familiar',
        max_length=20, 
        choices=VINCULO_CHOICES, 
        default='tutor'
    )
    es_apoderado_principal = models.BooleanField(
        default=False,
        help_text='Marcar si es el apoderado principal del estudiante'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pupilo'
        verbose_name_plural = 'Pupilos'
        unique_together = ['apoderado', 'estudiante']
        ordering = ['estudiante__user__last_name']
    
    def __str__(self):
        return f"{self.apoderado.nombre_completo} → {self.estudiante.nombre_completo} ({self.get_vinculo_display()})"
    
    def clean(self):
        """Validaciones del modelo"""
        if hasattr(self, 'apoderado') and self.apoderado.tipo_usuario != 'apoderado':
            raise ValidationError({'apoderado': 'El usuario seleccionado debe ser de tipo apoderado.'})
        if hasattr(self, 'estudiante') and self.estudiante.tipo_usuario != 'estudiante':
            raise ValidationError({'estudiante': 'El usuario seleccionado debe ser de tipo estudiante.'})
