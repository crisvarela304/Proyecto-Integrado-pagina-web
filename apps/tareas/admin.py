from django.contrib import admin
from .models import Tarea, Entrega


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'asignatura', 'profesor', 'fecha_entrega', 'estado', 'entregas_count')
    list_filter = ('estado', 'tipo', 'curso', 'asignatura')
    search_fields = ('titulo', 'descripcion', 'curso__nombre', 'profesor__first_name')
    date_hierarchy = 'fecha_entrega'
    raw_id_fields = ('profesor',)
    list_per_page = 25
    
    fieldsets = (
        ('Información', {
            'fields': ('titulo', 'descripcion', 'tipo')
        }),
        ('Asignación', {
            'fields': ('curso', 'asignatura', 'profesor')
        }),
        ('Fechas', {
            'fields': ('fecha_entrega', 'hora_limite')
        }),
        ('Configuración', {
            'fields': ('puntaje_maximo', 'archivo_adjunto', 'estado', 'permite_entrega_tardia')
        }),
    )
    
    def entregas_count(self, obj):
        return obj.entregas.count()
    entregas_count.short_description = 'Entregas'


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ('estudiante_nombre', 'tarea', 'fecha_entrega', 'entrega_tardia', 'puntaje', 'estado')
    list_filter = ('estado', 'entrega_tardia', 'tarea__curso')
    search_fields = ('estudiante__first_name', 'estudiante__last_name', 'tarea__titulo')
    raw_id_fields = ('estudiante', 'tarea')
    readonly_fields = ('fecha_entrega',)
    list_per_page = 25
    
    def estudiante_nombre(self, obj):
        return obj.estudiante.get_full_name()
    estudiante_nombre.short_description = 'Estudiante'
