from django.contrib import admin
from .models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha_inicio', 'fecha_fin', 'curso', 'activo')
    list_filter = ('tipo', 'activo', 'curso')
    search_fields = ('titulo', 'descripcion')
    date_hierarchy = 'fecha_inicio'
    list_per_page = 25
    
    fieldsets = (
        ('Información del Evento', {
            'fields': ('titulo', 'descripcion', 'tipo', 'color')
        }),
        ('Fechas y Horarios', {
            'fields': ('fecha_inicio', 'fecha_fin', 'todo_el_dia', 'hora_inicio', 'hora_fin')
        }),
        ('Visibilidad', {
            'fields': ('curso', 'visible_para_todos', 'activo')
        }),
    )
