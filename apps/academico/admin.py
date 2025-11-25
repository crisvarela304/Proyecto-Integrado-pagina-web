from django.contrib import admin
from .models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia, TipoExamen, Examen, PreguntaExamen

# --- Inlines para facilitar asignaciones ---

class InscripcionCursoInline(admin.TabularInline):
    model = InscripcionCurso
    extra = 1
    autocomplete_fields = ['estudiante']
    verbose_name = "Alumno inscrito"
    verbose_name_plural = "Alumnos inscritos en este curso"

class HorarioClasesInline(admin.TabularInline):
    model = HorarioClases
    extra = 1
    autocomplete_fields = ['profesor', 'asignatura']
    verbose_name = "Asignación Horaria"
    verbose_name_plural = "Asignaturas y Profesores (Horario)"

class AsignaturaHorarioInline(admin.TabularInline):
    """Permite asignar profesores a esta asignatura en diferentes cursos"""
    model = HorarioClases
    extra = 1
    autocomplete_fields = ['profesor', 'curso']
    verbose_name = "Profesor asignado"
    verbose_name_plural = "Profesores que dictan esta asignatura"
    fields = ('curso', 'profesor', 'dia', 'hora', 'sala', 'activo')

# --- Admins Principales ---

@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'horas_semanales', 'activa')
    list_filter = ('activa', 'horas_semanales')
    search_fields = ('codigo', 'nombre', 'descripcion')
    list_per_page = 20
    inlines = [AsignaturaHorarioInline] # Aquí asignas profesores a la asignatura

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel', 'letra', 'año', 'profesor_jefe_display', 'total_alumnos', 'activo')
    list_filter = ('nivel', 'año', 'activo')
    search_fields = ('nombre', 'letra')
    autocomplete_fields = ['profesor_jefe']
    list_per_page = 15
    inlines = [InscripcionCursoInline, HorarioClasesInline] # Aquí asignas alumnos y horario
    
    def profesor_jefe_display(self, obj):
        if obj.profesor_jefe:
            return f"{obj.profesor_jefe.get_full_name() or obj.profesor_jefe.username}"
        return "Sin asignar"
    profesor_jefe_display.short_description = 'Profesor Jefe'

@admin.register(InscripcionCurso)
class InscripcionCursoAdmin(admin.ModelAdmin):
    list_display = ('estudiante_display', 'curso_display', 'año', 'estado', 'fecha_inscripcion')
    list_filter = ('estado', 'año', 'curso__nivel')
    search_fields = ('estudiante__first_name', 'estudiante__last_name', 'estudiante__username', 'curso__nombre')
    autocomplete_fields = ['estudiante', 'curso']
    list_per_page = 25
    date_hierarchy = 'fecha_inscripcion'
    
    def estudiante_display(self, obj):
        return f"{obj.estudiante.get_full_name() or obj.estudiante.username}"
    estudiante_display.short_description = 'Estudiante'
    
    def curso_display(self, obj):
        return obj.curso
    curso_display.short_description = 'Curso'

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante_display', 'asignatura', 'curso_display', 'tipo_evaluacion', 'nota', 'semestre', 'fecha_evaluacion')
    list_filter = ('tipo_evaluacion', 'semestre', 'fecha_evaluacion', 'asignatura')
    search_fields = ('estudiante__first_name', 'estudiante__last_name', 'asignatura__nombre', 'descripcion')
    autocomplete_fields = ['estudiante', 'asignatura', 'curso', 'profesor']
    list_per_page = 30
    date_hierarchy = 'fecha_evaluacion'
    ordering = ('-fecha_evaluacion',)
    
    def estudiante_display(self, obj):
        return f"{obj.estudiante.get_full_name() or obj.estudiante.username}"
    estudiante_display.short_description = 'Estudiante'
    
    def curso_display(self, obj):
        return obj.curso
    curso_display.short_description = 'Curso'

@admin.register(HorarioClases)
class HorarioClasesAdmin(admin.ModelAdmin):
    list_display = ('curso', 'asignatura', 'profesor_display', 'dia', 'hora_display', 'sala', 'activo')
    list_filter = ('dia', 'activo', 'asignatura')
    search_fields = ('curso__nombre', 'asignatura__nombre', 'profesor__first_name', 'sala')
    autocomplete_fields = ['curso', 'asignatura', 'profesor']
    list_per_page = 20
    
    def profesor_display(self, obj):
        return f"{obj.profesor.get_full_name() or obj.profesor.username}"
    profesor_display.short_description = 'Profesor'
    
    def hora_display(self, obj):
        return obj.get_hora_display()
    hora_display.short_description = 'Hora'

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('estudiante_display', 'curso_display', 'fecha', 'estado', 'registrado_por_display', 'creado')
    list_filter = ('estado', 'fecha', 'curso__nivel')
    search_fields = ('estudiante__first_name', 'estudiante__last_name', 'observacion')
    autocomplete_fields = ['estudiante', 'curso', 'registrado_por']
    list_per_page = 30
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    
    def estudiante_display(self, obj):
        return f"{obj.estudiante.get_full_name() or obj.estudiante.username}"
    estudiante_display.short_description = 'Estudiante'
    
    def curso_display(self, obj):
        return obj.curso
    curso_display.short_description = 'Curso'
    
    def registrado_por_display(self, obj):
        return f"{obj.registrado_por.get_full_name() or obj.registrado_por.username}"
    registrado_por_display.short_description = 'Registrado por'

# Acciones personalizadas para el admin
@admin.action(description='Marcar como presentes seleccionados')
def marcar_presentes(modeladmin, request, queryset):
    queryset.update(estado='presente')

@admin.action(description='Marcar como ausentes seleccionados')
def marcar_ausentes(modeladmin, request, queryset):
    queryset.update(estado='ausente')

@admin.action(description='Exportar calificaciones a CSV')
def exportar_calificaciones_csv(modeladmin, request, queryset):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="calificaciones.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Estudiante', 'Asignatura', 'Curso', 'Tipo', 'Nota', 'Semestre', 'Fecha'])
    
    for calificacion in queryset:
        writer.writerow([
            calificacion.estudiante.get_full_name() or calificacion.estudiante.username,
            calificacion.asignatura.nombre,
            str(calificacion.curso),
            calificacion.get_tipo_evaluacion_display(),
            str(calificacion.nota),
            calificacion.get_semestre_display(),
            calificacion.fecha_evaluacion.strftime('%d/%m/%Y')
        ])
    
    return response

# Agregar acciones
AsistenciaAdmin.actions = [marcar_presentes, marcar_ausentes]
CalificacionAdmin.actions = [exportar_calificaciones_csv]

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
    autocomplete_fields = ['curso', 'asignatura', 'profesor', 'tipo_examen']
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
    autocomplete_fields = ['examen']
    ordering = ('examen', 'orden', 'numero')