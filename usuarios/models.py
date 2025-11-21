from django.db import models
from django.contrib.auth.models import User

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
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.rut}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return self.user.get_full_name() or self.user.username

    def validar_rut(self, rut):
        """Valida un RUT chileno"""
        if not rut:
            return False
        
        # Limpiar RUT
        rut = rut.strip().replace('.', '').replace('-', '').upper()
        
        if len(rut) < 2:
            return False
        
        # Separar cuerpo y dígito verificador
        cuerpo = rut[:-1]
        dv = rut[-1]
        
        try:
            # Calcular dígito verificador
            suma = 0
            multiplicador = 2
            
            for digito in reversed(cuerpo):
                suma += int(digito) * multiplicador
                multiplicador += 1
                if multiplicador == 8:
                    multiplicador = 2
            
            resto = suma % 11
            dv_calculado = 11 - resto
            
            if dv_calculado == 11:
                dv_calculado = '0'
            elif dv_calculado == 10:
                dv_calculado = 'K'
            else:
                dv_calculado = str(dv_calculado)
            
            return dv == dv_calculado
        except:
            return False

class ConfiguracionSistema(models.Model):
    """Configuraciones generales del sistema"""
    clave = models.CharField(max_length=50, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"

    def __str__(self):
        return self.clave
