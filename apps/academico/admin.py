from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from .models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia, TipoExamen, Examen, PreguntaExamen

# --- Inlines para facilitar asignaciones ---

# Acciones personalizadas para el admin
@admin.action(description='Marcar como presentes seleccionados')
def marcar_presentes(modeladmin, request, queryset):
    queryset.update(estado='presente')

@admin.action(description='Marcar como ausentes seleccionados')
def marcar_ausentes(modeladmin, request, queryset):
    queryset.update(estado='ausente')

@admin.action(description='Enviar correo a alumnos del curso')
def enviar_correo_curso(modeladmin, request, queryset):
    """Acción para enviar correo a los alumnos de los cursos seleccionados"""
    from django.core.mail import send_mail
    from django.conf import settings
    from django.contrib import messages
    
    cursos_enviados = 0
    alumnos_total = 0
    
    for curso in queryset:
        # Obtener emails de estudiantes activos en el curso
        emails = curso.estudiantes.filter(estado='activo').values_list('estudiante__email', flat=True)
        emails = [e for e in emails if e] # Filtrar vacíos
        
        if emails:
            asunto = f"Comunicado del Curso {curso}"
            mensaje = f"Estimados estudiantes de {curso},\n\nSu profesor {request.user.get_full_name()} les envía el siguiente comunicado:\n\n[ESCRIBIR MENSAJE AQUÍ]\n\nAtte,\nLiceo"
            
            try:
                # Enviar correo (BCC para privacidad)
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email], # To: Profesor
                    bcc=emails, # BCC: Alumnos
                    fail_silently=False,
                )
                cursos_enviados += 1
                alumnos_total += len(emails)
            except Exception as e:
                modeladmin.message_user(request, f"Error enviando a {curso}: {str(e)}", level=messages.ERROR)
    
    if cursos_enviados > 0:
        modeladmin.message_user(request, f"Se enviaron correos a {alumnos_total} alumnos de {cursos_enviados} cursos.", level=messages.SUCCESS)

@admin.action(description='Ingresar Notas al Curso (Masivo)')
def ingresar_notas_curso(modeladmin, request, queryset):
    """Redirige a la vista de ingreso masivo de notas para el primer curso seleccionado"""
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.contrib import messages
    
    if queryset.count() != 1:
        modeladmin.message_user(request, "Por favor seleccione solo un curso para ingresar notas.", level=messages.WARNING)
        return
        
    curso = queryset.first()
    return redirect(reverse('academico:registrar_notas_curso', args=[curso.id]))

@admin.action(description='Duplicar bloque al siguiente horario (Bloque Doble)')
def duplicar_bloque_siguiente(modeladmin, request, queryset):
    """Duplica el bloque seleccionado al horario inmediatamente siguiente"""
    from django.contrib import messages
    
    creados = 0
    errores = 0
    
    for horario in queryset:
        # Calcular siguiente bloque
        try:
            hora_actual = int(horario.hora)
            siguiente_hora = str(hora_actual + 1)
            
            # Verificar si existe el bloque siguiente en las opciones
            opciones_hora = [h[0] for h in HorarioClases.HORA_CHOICES]
            
            if siguiente_hora in opciones_hora:
                # Verificar si ya está ocupado
                existe = HorarioClases.objects.filter(
                    curso=horario.curso,
                    dia=horario.dia,
                    hora=siguiente_hora
                ).exists()
                
                if not existe:
                    HorarioClases.objects.create(
                        curso=horario.curso,
                        asignatura=horario.asignatura,
                        profesor=horario.profesor,
                        dia=horario.dia,
                        hora=siguiente_hora,
                        sala=horario.sala,
                        activo=horario.activo
                    )
                    creados += 1
                else:
                    errores += 1
            else:
                errores += 1
        except ValueError:
            errores += 1
            
    if creados > 0:
        modeladmin.message_user(request, f"Se crearon {creados} bloques dobles exitosamente.", level=messages.SUCCESS)
    if errores > 0:
        modeladmin.message_user(request, f"No se pudieron crear {errores} bloques (horario ocupado o inválido).", level=messages.WARNING)

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

class InscripcionCursoInline(admin.TabularInline):
    model = InscripcionCurso
    extra = 1
    autocomplete_fields = ['estudiante']
    verbose_name = "Alumno inscrito"
    verbose_name_plural = "Alumnos inscritos en este curso"

class HorarioClasesInline(admin.TabularInline):
    model = HorarioClases
    extra = 1
    autocomplete_fields = ['asignatura', 'profesor']
    verbose_name = "Asignación Horaria"
    verbose_name_plural = "Asignaturas y Profesores (Horario)"

class AsignaturaHorarioInline(admin.TabularInline):
    """Permite asignar profesores a esta asignatura en diferentes cursos"""
    model = HorarioClases
    extra = 1
    autocomplete_fields = ['curso', 'profesor']
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
    actions = [enviar_correo_curso, ingresar_notas_curso]
    list_display = ('nombre', 'nivel', 'letra', 'año', 'profesor_jefe_display', 'total_alumnos', 'activo')
    list_filter = ('nivel', 'año', 'activo')
    search_fields = ('nombre', 'letra')
    autocomplete_fields = ['profesor_jefe']
    list_per_page = 15
    inlines = [InscripcionCursoInline, HorarioClasesInline] # Aquí asignas alumnos y horario
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "profesor_jefe":
            kwargs["queryset"] = User.objects.filter(perfil__tipo_usuario__in=['profesor', 'administrativo', 'directivo'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
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
    autocomplete_fields = ['estudiante', 'asignatura', 'curso']
    list_per_page = 30
    date_hierarchy = 'fecha_evaluacion'
    ordering = ('-fecha_evaluacion',)
    list_editable = ('nota',)
    
    # Reordenar campos para mejor UX
    fields = (
        ('curso', 'asignatura'),
        'estudiante',
        ('tipo_evaluacion', 'numero_evaluacion'),
        ('semestre', 'fecha_evaluacion'),
        'nota',
        'descripcion',
        'profesor' # Necesario para validación, se oculta si no es superuser
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Si es profesor, solo ve sus calificaciones
        return qs.filter(profesor=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Si no es superusuario, ocultamos el campo profesor
        if not request.user.is_superuser:
            if 'profesor' in form.base_fields:
                form.base_fields['profesor'].disabled = True
                form.base_fields['profesor'].widget = forms.HiddenInput()
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.profesor = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        """Deshabilita el botón de agregar estándar para forzar el uso de la carga masiva, excepto para superusuarios"""
        return request.user.is_superuser
    
    def estudiante_display(self, obj):
        return f"{obj.estudiante.get_full_name() or obj.estudiante.username}"
    estudiante_display.short_description = 'Estudiante'
    
    def curso_display(self, obj):
        return obj.curso
    curso_display.short_description = 'Curso'

@admin.register(HorarioClases)
class HorarioClasesAdmin(admin.ModelAdmin):
    actions = [duplicar_bloque_siguiente]
    list_display = ('curso', 'asignatura', 'profesor_display', 'dia', 'hora_display', 'sala', 'activo')
    list_filter = ('dia', 'activo', 'asignatura')
    search_fields = ('curso__nombre', 'asignatura__nombre', 'profesor__first_name', 'sala')
    autocomplete_fields = ['curso', 'asignatura']
    list_per_page = 20
    list_editable = ('sala', 'activo')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "profesor":
            kwargs["queryset"] = User.objects.filter(perfil__tipo_usuario__in=['profesor', 'administrativo', 'directivo'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
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
    autocomplete_fields = ['estudiante', 'curso']
    list_per_page = 30
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    list_editable = ('estado',)

    
    # Reordenar campos
    fields = (
        ('curso', 'fecha'),
        'estudiante',
        'estado',
        'observacion',
        'registrado_por' # Se oculta automáticamente si no es superuser
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(registrado_por=request.user)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'registrado_por' in form.base_fields:
                form.base_fields['registrado_por'].disabled = True
                form.base_fields['registrado_por'].widget = forms.HiddenInput()
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)
    
    def estudiante_display(self, obj):
        return f"{obj.estudiante.get_full_name() or obj.estudiante.username}"
    estudiante_display.short_description = 'Estudiante'
    
    def curso_display(self, obj):
        return obj.curso
    curso_display.short_description = 'Curso'
    
    def registrado_por_display(self, obj):
        return f"{obj.registrado_por.get_full_name() or obj.registrado_por.username}"
    registrado_por_display.short_description = 'Registrado por'



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
    autocomplete_fields = ['curso', 'asignatura', 'tipo_examen']
    readonly_fields = ('creado',)
    ordering = ('-fecha_aplicacion',)
    list_editable = ('fecha_aplicacion', 'activo')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(profesor=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "profesor":
            kwargs["queryset"] = User.objects.filter(perfil__tipo_usuario__in=['profesor', 'administrativo', 'directivo'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'profesor' in form.base_fields:
                form.base_fields['profesor'].disabled = True
                form.base_fields['profesor'].widget = forms.HiddenInput()
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.profesor = request.user
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'descripcion', 'tipo_examen', 'curso', 'asignatura')
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