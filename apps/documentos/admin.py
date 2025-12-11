from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import (
    CategoriaDocumento, Documento, HistorialDescargas, ComunicadoPadres
)
from academico.models import Curso
from django.contrib.auth.models import User

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
    list_display = ('titulo', 'categoria', 'tipo', 'visibilidad', 'curso', 'es_oficial', 'publicado', 'creado_por', 'fecha_creacion')
    list_filter = ('categoria', 'tipo', 'visibilidad', 'curso', 'es_oficial', 'publicado', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'tags')
    readonly_fields = ('tamaño', 'descargar_count', 'fecha_creacion', 'fecha_actualizacion')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'archivo', 'categoria', 'curso')
        }),
        ('Configuración', {
            'fields': ('tipo', 'visibilidad', 'tags', 'version', 'es_oficial', 'publicado')
        }),
        ('Metadatos', {
            'fields': ('tamaño', 'descargar_count', 'creado_por', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creado_por=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'creado_por' in form.base_fields:
                form.base_fields['creado_por'].disabled = True
                form.base_fields['creado_por'].widget = forms.HiddenInput()
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "curso":
            # Si no es superusuario, filtrar cursos asignados al profesor
            if not request.user.is_superuser:
                # Filtrar cursos donde el usuario tiene clases asignadas (HorarioClases)
                # o es profesor jefe.
                from academico.models import HorarioClases
                cursos_ids = HorarioClases.objects.filter(profesor=request.user).values_list('curso', flat=True).distinct()
                kwargs["queryset"] = Curso.objects.filter(id__in=cursos_ids)
        
        if db_field.name == "creado_por":
            # Filtrar para mostrar solo usuarios tipo 'profesor' o 'administrativo'
            # Esto limpia la lista para el superusuario
            kwargs["queryset"] = User.objects.filter(perfil__tipo_usuario__in=['profesor', 'administrativo', 'directivo'])
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
