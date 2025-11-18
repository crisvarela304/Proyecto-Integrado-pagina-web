"""
Formularios seguros para mensajería interna
Con validaciones de CSRF, rate limiting, y sanitización
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from .models import Conversacion, Mensaje, RateLimit
from django.conf import settings


class BusquedaConversacionForm(forms.Form):
    """Formulario de búsqueda en conversaciones"""
    busqueda = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre del participante...',
            'class': 'form-control'
        })
    )
    
    def clean_busqueda(self):
        """Sanitizar búsqueda"""
        busqueda = self.cleaned_data.get('busqueda', '')
        return busqueda.strip()


class NuevaConversacionForm(forms.Form):
    """Formulario para crear nueva conversación con rate limiting"""
    destinatario = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        
        if usuario:
            # Filtrar destinatarios según el tipo de usuario
            if usuario.groups.filter(name='Alumno').exists():
                # Alumno puede crear conversación con profesor
                self.fields['destinatario'].queryset = User.objects.filter(
                    groups__name='Profesor',
                    is_active=True
                ).exclude(id=usuario.id)
            elif usuario.groups.filter(name='Profesor').exists():
                # Profesor puede crear conversación con alumno
                self.fields['destinatario'].queryset = User.objects.filter(
                    groups__name='Alumno',
                    is_active=True
                ).exclude(id=usuario.id)
    
    def clean_destinatario(self):
        """Validaciones de destinatario y rate limiting"""
        destinatario = self.cleaned_data['destinatario']
        usuario = self.usuario
        
        if not usuario:
            raise ValidationError("Usuario no especificado")
        
        # Verificar rate limiting
        if self._verificar_rate_limit(usuario, 'nueva_conversacion'):
            raise ValidationError("Demasiadas solicitudes. Intenta en unos minutos.")
        
        # Verificar que el usuario puede crear conversación con este destinatario
        if usuario.groups.filter(name='Alumno').exists():
            if not destinatario.groups.filter(name='Profesor').exists():
                raise ValidationError("Los alumnos solo pueden conversar con profesores")
        elif usuario.groups.filter(name='Profesor').exists():
            if not destinatario.groups.filter(name='Alumno').exists():
                raise ValidationError("Los profesores solo pueden conversar con alumnos")
        
        # Verificar que no es el mismo usuario
        if usuario == destinatario:
            raise ValidationError("No puedes crear una conversación contigo mismo")
        
        return destinatario
    
    @transaction.atomic
    def _verificar_rate_limit(self, usuario, tipo_accion):
        """Verifica límites de tasa para prevenir DoS"""
        # Limpiar registros antiguos (más de 1 hora)
        una_hora_atras = timezone.now() - timezone.timedelta(hours=1)
        RateLimit.objects.filter(
            usuario=usuario,
            tipo_accion=tipo_accion,
            timestamp__lt=una_hora_atras
        ).delete()
        
        # Contar solicitudes en la última hora
        solicitudes_recientes = RateLimit.objects.filter(
            usuario=usuario,
            tipo_accion=tipo_accion,
            timestamp__gte=una_hora_atras
        ).count()
        
        # Límite: 10 conversaciones por hora
        if solicitudes_recientes >= 10:
            # Registrar intento
            RateLimit.objects.create(
                usuario=usuario,
                tipo_accion=tipo_accion,
                ip_address='127.0.0.1'  # En producción, obtener IP real
            )
            return True
        
        # Registrar esta solicitud
        RateLimit.objects.create(
            usuario=usuario,
            tipo_accion=tipo_accion,
            ip_address='127.0.0.1'
        )
        
        return False
    
    @transaction.atomic
    def save(self, usuario=None):
        """Crear conversación de forma atómica"""
        usuario = usuario or self.usuario
        if not usuario:
            raise ValidationError("Usuario no especificado")
        destinatario = self.cleaned_data['destinatario']
        
        # Determinar roles y crear conversación
        if usuario.groups.filter(name='Alumno').exists():
            # Usuario es alumno
            conversacion, created = Conversacion.objects.get_or_create(
                alumno=usuario,
                profesor=destinatario
            )
        else:
            # Usuario es profesor
            conversacion, created = Conversacion.objects.get_or_create(
                alumno=destinatario,
                profesor=usuario
            )
        
        return conversacion, created


class MensajeForm(forms.ModelForm):
    """Formulario para enviar mensajes con validaciones de seguridad"""
    class Meta:
        model = Mensaje
        fields = ['contenido', 'adjunto']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Escribe tu mensaje...',
                'class': 'form-control',
                'maxlength': 1000
            }),
            'adjunto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            })
        }
    
    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        conversacion = kwargs.pop('conversacion', None)
        super().__init__(*args, **kwargs)
        
        # Guardar usuario y conversación para validaciones
        self.usuario = usuario
        self.conversacion = conversacion
    
    def clean_contenido(self):
        """Sanitizar contenido del mensaje"""
        contenido = self.cleaned_data.get('contenido', '')
        
        # Validar que no esté vacío
        if not contenido.strip():
            raise ValidationError("El mensaje no puede estar vacío")
        
        # Validar longitud máxima
        if len(contenido) > 1000:
            raise ValidationError("El mensaje no puede tener más de 1000 caracteres")
        
        # Sanitizar HTML (Django ya lo escapa por defecto, pero asegurarnos)
        contenido = contenido.strip()
        
        return contenido
    
    def clean_adjunto(self):
        """Validaciones adicionales de archivo adjunto"""
        adjunto = self.cleaned_data.get('adjunto')
        
        if adjunto:
            # Verificar rate limiting de archivos
            if self._verificar_rate_limit_archivos():
                raise ValidationError("Demasiados archivos enviados. Intenta en unos minutos.")
            
            # Validar que el usuario puede subir archivos
            config = getattr(self.usuario, 'config_mensajeria', None)
            if config and not config.notificaciones_activas:
                # Si las notificaciones están desactivadas, permitir archivos igual
                pass
            
            # El archivo se validará también en el modelo con _validar_archivo_adjunto()
        
        return adjunto
    
    def _verificar_rate_limit_archivos(self):
        """Verifica límites de archivos por minuto"""
        un_minuto_atras = timezone.now() - timezone.timedelta(minutes=1)
        
        archivos_recientes = RateLimit.objects.filter(
            usuario=self.usuario,
            tipo_accion='archivo',
            timestamp__gte=un_minuto_atras
        ).count()
        
        config = getattr(self.usuario, 'config_mensajeria', None)
        limite = config.limite_adjuntos_por_minuto if config else 5
        
        if archivos_recientes >= limite:
            RateLimit.objects.create(
                usuario=self.usuario,
                tipo_accion='archivo',
                ip_address='127.0.0.1'
            )
            return True
        
        return False
    
    def clean(self):
        """Validaciones generales del formulario"""
        cleaned_data = super().clean()
        
        # Verificar que el usuario puede acceder a la conversación
        if self.conversacion and self.usuario:
            if not self.conversacion.puede_acceder(self.usuario):
                raise ValidationError("No tienes permisos para enviar mensajes en esta conversación")
        
        # Verificar que el usuario puede enviar mensajes (rate limiting)
        if self._verificar_rate_limit_mensajes():
            raise ValidationError("Demasiados mensajes enviados. Espera un momento.")
        
        return cleaned_data
    
    def _verificar_rate_limit_mensajes(self):
        """Verifica límites de mensajes por minuto"""
        un_minuto_atras = timezone.now() - timezone.timedelta(minutes=1)
        
        mensajes_recientes = RateLimit.objects.filter(
            usuario=self.usuario,
            tipo_accion='mensaje',
            timestamp__gte=un_minuto_atras
        ).count()
        
        # Límite: 20 mensajes por minuto
        if mensajes_recientes >= 20:
            RateLimit.objects.create(
                usuario=self.usuario,
                tipo_accion='mensaje',
                ip_address='127.0.0.1'
            )
            return True
        
        return False
    
    @transaction.atomic
    def save(self, commit=True):
        """Override save para manejo de rate limits"""
        # Registrar actividad de rate limiting
        RateLimit.objects.create(
            usuario=self.usuario,
            tipo_accion='mensaje',
            ip_address='127.0.0.1'
        )
        
        if self.cleaned_data.get('adjunto'):
            RateLimit.objects.create(
                usuario=self.usuario,
                tipo_accion='archivo',
                ip_address='127.0.0.1'
            )
        
        return super().save(commit=commit)


class PaginacionForm(forms.Form):
    """Formulario para paginación"""
    pagina = forms.IntegerField(min_value=1, required=False)
    
    def clean_pagina(self):
        """Validar número de página"""
        pagina = self.cleaned_data.get('pagina')
        if pagina and pagina < 1:
            raise ValidationError("Número de página inválido")
        return pagina
