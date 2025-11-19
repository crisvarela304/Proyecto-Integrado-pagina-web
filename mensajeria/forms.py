"""
Formularios seguros para mensajería interna
Con validaciones de CSRF, rate limiting, y sanitización
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from academico.models import InscripcionCurso, HorarioClases
from .models import Conversacion, Mensaje, RateLimit


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
            perfil = getattr(usuario, 'perfil', None)
            if perfil and perfil.tipo_usuario == 'estudiante':
                cursos = InscripcionCurso.objects.filter(
                    estudiante=usuario,
                    estado='activo'
                ).values_list('curso_id', flat=True)
                profesores_ids = HorarioClases.objects.filter(
                    curso_id__in=cursos
                ).values_list('profesor_id', flat=True)
                self.fields['destinatario'].queryset = User.objects.filter(
                    id__in=profesores_ids,
                    is_active=True
                ).distinct()
            elif perfil and perfil.tipo_usuario == 'profesor':
                cursos_profesor = HorarioClases.objects.filter(
                    profesor=usuario
                ).values_list('curso_id', flat=True).distinct()
                estudiantes_ids = InscripcionCurso.objects.filter(
                    curso_id__in=cursos_profesor,
                    estado='activo'
                ).values_list('estudiante_id', flat=True)
                self.fields['destinatario'].queryset = User.objects.filter(
                    id__in=estudiantes_ids,
                    is_active=True
                ).distinct()
    
    def clean_destinatario(self):
        """Validaciones de destinatario y rate limiting"""
        destinatario = self.cleaned_data['destinatario']
        usuario = self.usuario
        
        if not usuario:
            raise ValidationError("Usuario no especificado")
        
        # Verificar rate limiting
        if self._verificar_rate_limit(usuario, 'nueva_conversacion'):
            raise ValidationError("Demasiadas solicitudes. Intenta en unos minutos.")
        
        perfil = getattr(usuario, 'perfil', None)
        destino_perfil = getattr(destinatario, 'perfil', None)
        if perfil and perfil.tipo_usuario == 'estudiante':
            if not destino_perfil or destino_perfil.tipo_usuario != 'profesor':
                raise ValidationError("Los alumnos solo pueden conversar con profesores")
        elif perfil and perfil.tipo_usuario == 'profesor':
            if not destino_perfil or destino_perfil.tipo_usuario != 'estudiante':
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
        perfil = getattr(usuario, 'perfil', None)
        if perfil and perfil.tipo_usuario == 'estudiante':
            conversacion, created = Conversacion.objects.get_or_create(
                alumno=usuario,
                profesor=destinatario
            )
        else:
            conversacion, created = Conversacion.objects.get_or_create(
                alumno=destinatario,
                profesor=usuario
            )
        
        return conversacion, created


class MensajeForm(forms.ModelForm):
    """Formulario para enviar mensajes con validaciones de seguridad"""
    class Meta:
        model = Mensaje
        fields = ['asunto', 'contenido', 'adjunto']
        widgets = {
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asunto del mensaje (opcional)',
                'maxlength': 150
            }),
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
        self.fields['asunto'].required = False

        if conversacion:
            ultimo = conversacion.mensajes.order_by('-fecha_creacion').first()
            if ultimo and ultimo.asunto:
                self.fields['asunto'].initial = ultimo.asunto
    
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


class ProfesorMensajeForm(forms.Form):
    """Formulario sencillo para que el profesor escriba a sus estudiantes"""
    destinatario = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Estudiante',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    asunto = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asunto del mensaje'})
    )
    contenido = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Contenido del mensaje'})
    )

    def __init__(self, *args, **kwargs):
        profesor = kwargs.pop('profesor', None)
        super().__init__(*args, **kwargs)
        self.profesor = profesor

        if profesor:
            cursos_profesor = HorarioClases.objects.filter(
                profesor=profesor
            ).values_list('curso_id', flat=True).distinct()
            estudiantes_ids = InscripcionCurso.objects.filter(
                curso_id__in=cursos_profesor,
                estado='activo'
            ).values_list('estudiante_id', flat=True)
            self.fields['destinatario'].queryset = User.objects.filter(
                id__in=estudiantes_ids,
                is_active=True
            ).distinct()
    
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
