"""
Admin panel seguro para mensajería interna
Con validaciones de acceso y protección de datos
"""
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import (
    Conversacion, 
    Mensaje, 
    ConfiguracionMensajeria, 
    RateLimit
)

@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    """Panel de administración para conversaciones"""
    list_display = [
        'id', 
        'alumno', 
        'profesor', 
        'creado_en', 
        'get_total_mensajes',
        'no_leidos_alumno', 
        'no_leidos_profesor',
        'ultimo_mensaje_en'
    ]
    list_filter = ['creado_en', 'ultimo_mensaje_en']
    search_fields = [
        'alumno__username', 
        'alumno__first_name', 
        'alumno__last_name',
        'profesor__username', 
        'profesor__first_name', 
        'profesor__last_name'
    ]
    readonly_fields = [
        'id', 
        'creado_en', 
        'actualizado_en',
        'ultimo_mensaje_en', 
        'no_leidos_alumno', 
        'no_leidos_profesor'
    ]
    date_hierarchy = 'creado_en'
    
    def get_queryset(self, request):
        """Query optimizado con anotaciones"""
        qs = super().get_queryset(request)
        return qs.select_related('alumno', 'profesor')
    
    def get_total_mensajes(self, obj):
        """Cuenta total de mensajes en la conversación"""
        return obj.mensajes.count()
    get_total_mensajes.short_description = 'Total mensajes'
    get_total_mensajes.admin_order_field = 'mensajes__count'


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    """Panel de administración para mensajes"""
    list_display = [
        'id',
        'get_autor_display',
        'get_conversacion_display',
        'contenido_preview',
        'get_adjunto_info',
        'leido',
        'fecha_creacion'
    ]
    list_filter = [
        'fecha_creacion',
        'leido',
        'conversacion__alumno',
        'conversacion__profesor'
    ]
    search_fields = [
        'contenido',
        'autor__username',
        'autor__first_name',
        'autor__last_name'
    ]
    readonly_fields = [
        'id',
        'fecha_creacion',
        'leido'
    ]
    date_hierarchy = 'fecha_creacion'
    
    def get_queryset(self, request):
        """Query optimizado"""
        qs = super().get_queryset(request)
        return qs.select_related('autor', 'conversacion')
    
    def get_autor_display(self, obj):
        """Muestra información del autor"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.autor.get_full_name() or obj.autor.username,
            obj.autor.email or 'Sin email'
        )
    get_autor_display.short_description = 'Autor'
    
    def get_conversacion_display(self, obj):
        """Muestra información de la conversación"""
        return format_html(
            'Alumno: {}<br>Profesor: {}',
            obj.conversacion.alumno.get_full_name() or obj.conversacion.alumno.username,
            obj.conversacion.profesor.get_full_name() or obj.conversacion.profesor.username
        )
    get_conversacion_display.short_description = 'Conversación'
    
    def contenido_preview(self, obj):
        """Vista previa del contenido"""
        if len(obj.contenido) > 50:
            return obj.contenido[:50] + '...'
        return obj.contenido
    contenido_preview.short_description = 'Contenido'
    
    def get_adjunto_info(self, obj):
        """Información del archivo adjunto"""
        if obj.adjunto:
            return format_html(
                '<i class="bi bi-paperclip"></i> {} ({}MB)',
                obj.adjunto.name.split('/')[-1],
                round(obj.adjunto.size / (1024*1024), 2)
            )
        return '-'
    get_adjunto_info.short_description = 'Archivo adjunto'


@admin.register(ConfiguracionMensajeria)
class ConfiguracionMensajeriaAdmin(admin.ModelAdmin):
    """Panel de administración para configuraciones"""
    list_display = [
        'usuario',
        'notificaciones_activas',
        'limite_adjuntos_por_minuto',
        'ultima_actividad'
    ]
    list_filter = [
        'notificaciones_activas', 
        'ultima_actividad'
    ]
    search_fields = [
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name'
    ]
    readonly_fields = [
        'id', 
        'ultima_actividad'
    ]


@admin.register(RateLimit)
class RateLimitAdmin(admin.ModelAdmin):
    """Panel de administración para rate limiting"""
    list_display = (
        'usuario',
        'tipo_accion',
        'timestamp',
        'ip_address',
        'es_activo'
    )
    list_filter = [
        'tipo_accion', 
        'timestamp'
    ]
    search_fields = [
        'usuario__username',
        'ip_address'
    ]
    readonly_fields = [
        'id', 
        'timestamp'
    ]
    date_hierarchy = 'timestamp'
    
    def es_activo(self, obj):
        """Indica si el registro está activo (última hora)"""
        from django.utils import timezone
        import datetime
        return obj.timestamp >= timezone.now() - datetime.timedelta(hours=1)
    es_activo.boolean = True


@admin.action(description='Marcar todas como leídas')
def marcar_todas_leidas(modeladmin, request, queryset):
    """Acción para marcar conversaciones como leídas"""
    for conversacion in queryset:
        conversacion.no_leidos_alumno = 0
        conversacion.no_leidos_profesor = 0
        conversacion.save(update_fields=['no_leidos_alumno', 'no_leidos_profesor'])


@admin.action(description='Exportar estadísticas de mensajería')
def exportar_estadisticas(modeladmin, request, queryset):
    """Acción para exportar estadísticas"""
    # Implementar exportación de estadísticas
    pass


# Agregar acciones a los modelos
ConversacionAdmin.actions = [marcar_todas_leidas]
MensajeAdmin.actions = [exportar_estadisticas]
