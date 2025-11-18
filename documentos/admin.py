from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CategoriaDocumento, Documento, HistorialDescargas, 
    TipoExamen, Examen, PreguntaExamen, ComunicadoPadres
)

@admin.register(CategoriaDocumento)
class CategoriaDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color_display', 'icono', 'orden', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'tipo', 'visibilidad', 'es_oficial', 'publicado', 'creado_por', 'fecha_creacion')
    list_filter = ('categoria', 'tipo', 'visibilidad', 'es_oficial', 'publicado', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'tags')
    readonly_fields = ('tamaño', 'descargar_count', 'fecha_creacion', 'fecha_actualizacion')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'archivo', 'categoria')
        }),
        ('Configuración', {
            'fields': ('tipo', 'visibilidad', 'tags', 'version', 'es_oficial', 'publicado')
        }),
        ('Metadatos', {
            'fields': ('tamaño', 'descargar_count', 'creado_por', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo al crear
            obj.creado_por = request.user
            if obj.archivo:
                obj.tamaño = obj.archivo.size
        super().save_model(request, obj, form, change)

@admin.register(HistorialDescargas)
class HistorialDescargasAdmin(admin.ModelAdmin):
    list_display = ('documento', 'usuario', 'fecha_descarga', 'ip_address')
    list_filter = ('fecha_descarga',)
    search_fields = ('documento__titulo', 'usuario__username')
    readonly_fields = ('fecha_descarga',)
    ordering = ('-fecha_descarga',)

@admin.register(TipoExamen)
class TipoExamenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ponderacion_por_defecto', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')

@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'asignatura', 'tipo_periodo', 'fecha_aplicacion', 'profesor', 'activo')
    list_filter = ('tipo_periodo', 'fecha_aplicacion', 'activo', 'curso', 'asignatura')
    search_fields = ('titulo', 'descripcion', 'curso__nombre', 'asignatura__nombre')
    readonly_fields = ('creado',)
    ordering = ('-fecha_aplicacion',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'tipo_examen', 'curso', 'asignatura', 'profesor')
        }),
        ('Programación', {
            'fields': ('tipo_periodo', 'fecha_aplicacion', 'hora_inicio', 'duracion_minutos', 'sala')
        }),
        ('Detalles del Examen', {
            'fields': ('instrucciones', 'material_permitido', 'ponderacion', 'activo')
        }),
        ('Metadatos', {
            'fields': ('creado',),
            'classes': ('collapse',)
        }),
    )

@admin.register(PreguntaExamen)
class PreguntaExamenAdmin(admin.ModelAdmin):
    list_display = ('examen', 'numero', 'tipo_pregunta', 'puntos', 'orden')
    list_filter = ('tipo_pregunta',)
    search_fields = ('examen__titulo', 'enunciado')
    ordering = ('examen', 'orden', 'numero')

@admin.register(ComunicadoPadres)
class ComunicadoPadresAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'urgencia', 'dirigido_a', 'publicado_por', 'fecha_publicacion', 'activo')
    list_filter = ('urgencia', 'dirigido_a', 'fecha_publicacion', 'activo')
    search_fields = ('titulo', 'contenido')
    readonly_fields = ('fecha_publicacion', 'leido_count')
    ordering = ('-fecha_publicacion',)
    
    filter_horizontal = ('cursos_objetivo',)
    
    fieldsets = (
        ('Contenido', {
            'fields': ('titulo', 'contenido', 'urgencia', 'dirigido_a')
        }),
        ('Dirigido a', {
            'fields': ('cursos_objetivo',)
        }),
        ('Configuración', {
            'fields': ('publicado_por', 'fecha_publicacion', 'fecha_vencimiento', 'activo')
        }),
        ('Estadísticas', {
            'fields': ('leido_count',),
            'classes': ('collapse',)
        }),
    )
