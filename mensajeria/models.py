"""
Sistema de mensajería interna seguro para alumno-profesor
Cumple con todos los requisitos de seguridad, concurrencia y validaciones
"""
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings


class Conversacion(models.Model):
    """
    Conversaciones 1:1 entre alumno y profesor
    Constraint único para evitar duplicados
    """
    alumno = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversaciones_como_alumno',
        limit_choices_to={'perfil__tipo_usuario': 'estudiante'}
    )
    profesor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversaciones_como_profesor',
        limit_choices_to={'perfil__tipo_usuario': 'profesor'}
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    ultimo_mensaje_en = models.DateTimeField(null=True, blank=True)
    no_leidos_alumno = models.PositiveIntegerField(default=0)
    no_leidos_profesor = models.PositiveIntegerField(default=0)
    
    class Meta:
        # PREVIENE duplicados de conversación alumno-profesor
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'profesor'], 
                name='unique_alumno_profesor_conversacion'
            )
        ]
        ordering = ['-ultimo_mensaje_en', '-creado_en']
        verbose_name = "Conversación"
        verbose_name_plural = "Conversaciones"
    
    def __str__(self):
        return (
            f"Conversacion {self.alumno.get_full_name() or self.alumno.username} "
            f"<-> {self.profesor.get_full_name() or self.profesor.username}"
        )
    
    def get_otro_participante(self, usuario):
        """Retorna el otro participante de la conversación"""
        if usuario == self.alumno:
            return self.profesor
        elif usuario == self.profesor:
            return self.alumno
        else:
            raise ValueError("Usuario no participa en esta conversación")
    
    def puede_acceder(self, usuario):
        """Verifica si el usuario puede acceder a esta conversación (previene IDOR)"""
        return usuario in [self.alumno, self.profesor]
    
    def get_contador_no_leidos(self, usuario):
        """Retorna contador de no leídos para el usuario"""
        if usuario == self.alumno:
            return self.no_leidos_alumno
        elif usuario == self.profesor:
            return self.no_leidos_profesor
        return 0
    
    @transaction.atomic
    def marcar_como_leido(self, usuario):
        """Marca conversación como leída de forma atómica"""
        if usuario == self.alumno:
            self.no_leidos_alumno = 0
        elif usuario == self.profesor:
            self.no_leidos_profesor = 0
        else:
            raise ValueError("Usuario no participa en esta conversación")
        self.save()


class Mensaje(models.Model):
    """
    Mensajes con validación de archivos y contenido seguro
    """
    conversacion = models.ForeignKey(
        Conversacion,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    receptor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensajes_recibidos'
    )
    asunto = models.CharField(max_length=150, blank=True)
    contenido = models.TextField()
    # Archivos adjuntos seguros
    adjunto = models.FileField(
        upload_to='mensajeria/adjuntos/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                message="Solo se permiten archivos PDF, JPG, PNG, DOC, DOCX"
            )
        ]
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['fecha_creacion']
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        # Índices para performance
        indexes = [
            models.Index(fields=['conversacion', 'fecha_creacion'], name='mensaje_conversacion_fecha_idx'),
            models.Index(fields=['autor', 'fecha_creacion'], name='mensaje_autor_fecha_idx'),
            models.Index(fields=['receptor', 'fecha_creacion'], name='mensaje_receptor_fecha_idx'),
        ]
    
    def __str__(self):
        destino = self.receptor.get_full_name() or self.receptor.username
        return f"Mensaje de {self.autor} para {destino}"
    
    def clean(self):
        """Validaciones de seguridad a nivel de modelo"""
        super().clean()
        
        # Validar que el autor participa en la conversación
        if self.conversacion and self.autor:
            if not self.conversacion.puede_acceder(self.autor):
                raise ValidationError("El autor no participa en esta conversación")

        # Establecer receptor automático cuando no se proporciona
        if not self.receptor and self.conversacion and self.autor:
            self.receptor = self.conversacion.get_otro_participante(self.autor)

        if self.receptor and self.conversacion:
            if not self.conversacion.puede_acceder(self.receptor):
                raise ValidationError("El receptor no participa en esta conversación")
        
        # Validar archivo adjunto si existe
        if self.adjunto:
            self._validar_archivo_adjunto()
    
    def _validar_archivo_adjunto(self):
        """Validación segura de archivos adjuntos (sin dependencias externas)"""
        # Tamaño máximo: 5MB
        if self.adjunto.size > 5 * 1024 * 1024:
            raise ValidationError("El archivo no puede ser mayor a 5MB")
        
        # Validar extensión (el validador ya lo hace, pero lo reforzamos)
        nombre_archivo = self.adjunto.name.lower()
        extensiones_permitidas = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        
        if not any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
            raise ValidationError("Extensión de archivo no permitida")
        
        # Validar nombre de archivo seguro (prevenir path traversal)
        if '..' in self.adjunto.name or '/' in self.adjunto.name or '\\' in self.adjunto.name:
            raise ValidationError("Nombre de archivo no válido")
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        """Override save para manejo de contadores y validaciones"""
        es_nuevo = self.pk is None
        self.full_clean()
        
        super().save(*args, **kwargs)

        if es_nuevo:
            self._actualizar_contadores_no_leidos()
            self.conversacion.ultimo_mensaje_en = timezone.now()
            self.conversacion.save(update_fields=['ultimo_mensaje_en'])
    
    def _actualizar_contadores_no_leidos(self):
        """Actualiza contadores de no leídos de forma atómica"""
        # Determinar destinatario
        if self.autor == self.conversacion.alumno:
            campo_contador = 'no_leidos_profesor'
        else:
            campo_contador = 'no_leidos_alumno'
        
        # Incrementar contador de forma atómica
        Conversacion.objects.filter(
            id=self.conversacion.id
        ).update(
            **{campo_contador: models.F(campo_contador) + 1}
        )
    
    def marcar_como_leido(self, usuario):
        """Marca el mensaje como leído por el destinatario"""
        if usuario != self.receptor or self.leido:
            return
        self.leido = True
        super(Mensaje, self).save(update_fields=['leido'])
    
    def es_mio(self, usuario):
        """Verifica si el mensaje es del usuario"""
        return self.autor == usuario
    
    def es_del_otro_participante(self, usuario):
        """Verifica si el mensaje es del otro participante"""
        return self.autor == self.conversacion.get_otro_participante(usuario)


class ConfiguracionMensajeria(models.Model):
    """Configuraciones de mensajería por usuario"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config_mensajeria')
    notificaciones_activas = models.BooleanField(default=True)
    limite_adjuntos_por_minuto = models.PositiveIntegerField(default=5, help_text="Límite de archivos por minuto")
    ultima_actividad = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Mensajería"
        verbose_name_plural = "Configuraciones de Mensajería"
    
    def __str__(self):
        return f"Configuración de {self.usuario.get_full_name() or self.usuario.username}"


class RateLimit(models.Model):
    """Control de límites de envío para prevenir DoS"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rate_limits')
    timestamp = models.DateTimeField(auto_now_add=True)
    tipo_accion = models.CharField(max_length=50)  # 'mensaje', 'archivo', etc.
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        verbose_name = "Límite de Tasa"
        verbose_name_plural = "Límites de Tasa"
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Rate limit: {self.usuario} - {self.tipo_accion} - {self.timestamp}"


class ConfiguracionSistema(models.Model):
    """Configuraciones globales del sistema de mensajería"""
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


class ContactoColegio(models.Model):
    """Mensajes enviados desde el panel del estudiante al colegio."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    asunto = models.CharField(max_length=150)
    mensaje = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Contacto del Colegio"
        verbose_name_plural = "Contactos del Colegio"

    def __str__(self):
        return f"{self.asunto} - {self.correo}"
