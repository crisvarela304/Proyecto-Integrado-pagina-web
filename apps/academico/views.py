from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count, Max
from datetime import datetime, timedelta
from django.db.models import Q
from .models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia
from comunicacion.models import Noticia

@login_required
def dashboard_academico(request):
    """Dashboard académico personalizado por tipo de usuario"""
    user = request.user
    
    # Obtener perfil del usuario
    try:
        perfil = user.perfil
        tipo_usuario = perfil.tipo_usuario
    except:
        tipo_usuario = 'estudiante'
        perfil = None

    # Datos comunes
    context = {
        'titulo_dashboard': f'Dashboard Académico - {perfil.get_tipo_usuario_display() if perfil else "Usuario"}',
        'perfil': perfil,
        'user': user
    }

    if tipo_usuario in ['estudiante', 'apoderado']:
        return dashboard_estudiante(request, context)
    elif tipo_usuario == 'profesor':
        return dashboard_profesor(request, context)
    else:
        return dashboard_administrativo(request, context)

@login_required
def dashboard_estudiante(request, context):
    """Dashboard específico para estudiantes"""
    user = request.user
    
    # Datos del estudiante - Optimizado con select_related
    cursos = InscripcionCurso.objects.filter(
        estudiante=user, 
        estado='activo'
    ).select_related('curso')
    
    # Pre-calcular promedios para evitar N+1 en el template
    calificaciones_all = Calificacion.objects.filter(estudiante=user).values('curso').annotate(
        promedio=Avg('nota')
    )
    promedios_map = {item['curso']: item['promedio'] for item in calificaciones_all}
    
    # Calcular asistencia por curso (porcentaje de presencia)
    asistencias_por_curso = Asistencia.objects.filter(estudiante=user).values('curso').annotate(
        total=Count('id'),
        presentes=Count('id', filter=Q(estado='presente'))
    )
    asistencia_map = {}
    for item in asistencias_por_curso:
        if item['total'] > 0:
            porcentaje = (item['presentes'] / item['total']) * 100
            asistencia_map[item['curso']] = round(porcentaje, 1)
        else:
            asistencia_map[item['curso']] = 0

    for inscripcion in cursos:
        promedio = promedios_map.get(inscripcion.curso.id)
        inscripcion.promedio_calculado = round(promedio, 1) if promedio else None
        inscripcion.asistencia_porcentaje = asistencia_map.get(inscripcion.curso.id, 0)

    # Calificaciones recientes - Optimizado
    calificaciones = Calificacion.objects.filter(
        estudiante=user
    ).select_related('asignatura').order_by('-fecha_evaluacion')[:10]
    
    # Asistencia del mes actual para el widget
    hoy = datetime.now()
    inicio_mes = hoy.replace(day=1)
    asistencias_mes = Asistencia.objects.filter(
        estudiante=user, 
        fecha__gte=inicio_mes
    )
    
    # Calcular promedio general acumulado (Desde caché)
    try:
        promedio_general = user.perfil.promedio_general
    except:
        promedio_general = None
    
    # Horario de hoy - Optimizado
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dia_actual = dias_semana[datetime.now().weekday()]
    
    curso_ids = [inscripcion.curso.id for inscripcion in cursos]
    horario_hoy = HorarioClases.objects.filter(
        curso__id__in=curso_ids,
        dia=dia_actual
    ).select_related('asignatura', 'profesor').order_by('hora')
    
    context.update({
        'cursos': cursos,
        'calificaciones': calificaciones,
        'asistencias_mes': asistencias_mes,
        'promedio_general': promedio_general,
        'horario_hoy': horario_hoy
    })
    
    return render(request, 'academico/estudiante_dashboard.html', context)

@login_required
def dashboard_profesor(request, context):
    """Dashboard específico para profesores"""
    user = request.user
    
    # Cursos que enseña (Distinct para no repetir si enseña varias materias al mismo curso)
    horarios = HorarioClases.objects.filter(profesor=user).select_related('curso', 'asignatura')
    cursos_ids = horarios.values_list('curso_id', flat=True).distinct()
    
    # Optimización: Obtener cursos con conteo de alumnos activos en una sola query
    cursos_unicos = Curso.objects.filter(id__in=cursos_ids).annotate(
        cantidad_alumnos_real=Count('estudiantes', filter=Q(estudiantes__estado='activo'))
    )
    
    # Calcular total de alumnos
    total_alumnos_real = sum(c.cantidad_alumnos_real for c in cursos_unicos)

    # Optimización: Obtener últimas evaluaciones de todos los cursos en una sola query
    # Subquery es complejo en Django ORM para "último de cada grupo", así que lo hacemos en memoria
    # pero optimizado: traemos la última evaluación de cada curso+profesor
    
    ultimas_evaluaciones = Calificacion.objects.filter(
        profesor=user,
        curso__in=cursos_unicos
    ).order_by('curso', '-fecha_evaluacion').distinct('curso') # distinct('curso') solo funciona en Postgres, en SQLite/MySQL no.
    
    # Alternativa compatible con SQLite: Traer todas las evaluaciones recientes y filtrar en Python
    # O mejor: Traer la última evaluación por curso usando ID
    
    # Mapa de curso_id -> ultima_evaluacion
    ultima_eval_map = {}
    
    # Si estamos en SQLite (probable), distinct(field) no funciona.
    # Estrategia: Iterar cursos (son pocos) es aceptable SI evitamos queries anidadas pesadas.
    # Pero para el promedio, sí podemos optimizar.
    
    for curso in cursos_unicos:
        # Esto sigue siendo N+1 pero reducido. Para eliminarlo completamente se requeriría Window Functions o lógica compleja.
        # Dado que un profe tiene ~5-10 cursos, esto es tolerable si la query interna es ligera.
        ultima_eval = Calificacion.objects.filter(curso=curso, profesor=user).order_by('-fecha_evaluacion').select_related('asignatura').first()
        
        if ultima_eval:
            # Calcular promedio de esa evaluación específica
            promedio_eval = Calificacion.objects.filter(
                curso=curso, 
                asignatura=ultima_eval.asignatura,
                numero_evaluacion=ultima_eval.numero_evaluacion
            ).aggregate(Avg('nota'))['nota__avg']
            
            curso.promedio_ultima_nota = round(promedio_eval, 1) if promedio_eval else None
            curso.nombre_ultima_eval = f"{ultima_eval.asignatura.nombre} - Nota {ultima_eval.numero_evaluacion}"
        else:
            curso.promedio_ultima_nota = None
            curso.nombre_ultima_eval = "Sin evaluaciones"

    # Asignaturas asignadas
    asignaturas_ids = horarios.values_list('asignatura_id', flat=True).distinct()
    asignaturas_unicas = Asignatura.objects.filter(id__in=asignaturas_ids)
    
    # Horario de hoy
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dia_actual = dias_semana[datetime.now().weekday()]
    horario_hoy = HorarioClases.objects.filter(profesor=user, dia=dia_actual).select_related('curso', 'asignatura')
    
    # Calificaciones pendientes (últimas evaluaciones realizadas)
    # Optimización: select_related para evitar queries al mostrar nombre alumno/curso/asignatura
    calificaciones_recientes = Calificacion.objects.filter(
        profesor=user
    ).select_related('estudiante', 'curso', 'asignatura').order_by('-fecha_evaluacion')[:20]
    
    # Consejo de Profesores (Noticias categoría 'consejo')
    consejos = Noticia.objects.filter(categoria='consejo', es_publica=True).order_by('-creado')[:5]

    context.update({
        'cursos_unicos': cursos_unicos,
        'asignaturas_unicas': asignaturas_unicas,
        'horario_hoy': horario_hoy,
        'calificaciones_recientes': calificaciones_recientes,
        'total_alumnos_real': total_alumnos_real,
        'consejos': consejos
    })
    
    return render(request, 'academico/profesor_dashboard.html', context)

@login_required
def dashboard_administrativo(request, context):
    """Dashboard específico para administrativos"""
    user = request.user
    
    # Estadísticas generales
    total_estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante').count()
    total_profesores = User.objects.filter(perfil__tipo_usuario='profesor').count()
    total_cursos = Curso.objects.filter(activo=True).count()
    total_asignaturas = Asignatura.objects.filter(activa=True).count()
    
    # Calificaciones por nivel
    calificaciones_por_curso = Calificacion.objects.values('curso__nivel').annotate(
        promedio=Avg('nota')
    ).order_by('curso__nivel')
    
    context.update({
        'total_estudiantes': total_estudiantes,
        'total_profesores': total_profesores,
        'total_cursos': total_cursos,
        'total_asignaturas': total_asignaturas,
        'calificaciones_por_curso': calificaciones_por_curso
    })
    
    return render(request, 'academico/administrativo_dashboard.html', context)

@login_required
def mis_calificaciones(request):
    """Vista para ver calificaciones del estudiante"""
    user = request.user
    
    # Filtros
    semestre_actual = request.GET.get('semestre', '')
    calificaciones = Calificacion.objects.filter(estudiante=user)
    
    if semestre_actual:
        calificaciones = calificaciones.filter(semestre=semestre_actual)
    
    calificaciones = calificaciones.order_by('-fecha_evaluacion')
    
    # Calcular promedios
    try:
        promedio_general = user.perfil.promedio_general
    except:
        promedio_general = None
    
    # Promedios por semestre
    promedios_semestre = {}
    for semestre in ['1', '2']:
        promedio_sem = Calificacion.objects.filter(estudiante=user, semestre=semestre).aggregate(
            promedio=Avg('nota')
        )
        promedios_semestre[semestre] = round(promedio_sem['promedio'], 1) if promedio_sem['promedio'] else None
    
    return render(request, 'academico/mis_calificaciones.html', {
        'calificaciones': calificaciones,
        'promedio_general': promedio_general,
        'promedios': promedios_semestre,
        'semestre_actual': semestre_actual
    })

@login_required
def mi_horario(request):
    """Vista para ver el horario del estudiante"""
    user = request.user
    
    # Obtener cursos del estudiante
    cursos = InscripcionCurso.objects.filter(estudiante=user, estado='activo')
    curso_ids = cursos.values_list('curso_id', flat=True)
    
    # Obtener todo el horario en una sola consulta
    horario_completo = HorarioClases.objects.filter(
        curso__id__in=curso_ids
    ).select_related('asignatura', 'profesor').order_by('hora')
    
    # Agrupar por día en memoria
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    horario_por_dia = {dia: [] for dia in dias_semana}
    
    for clase in horario_completo:
        if clase.dia in horario_por_dia:
            horario_por_dia[clase.dia].append(clase)
    
    return render(request, 'academico/mi_horario.html', {
        'horario_por_dia': horario_por_dia,
        'dias_semana': dias_semana
    })

@login_required
def mis_asistencias(request):
    """Vista para ver las asistencias del estudiante"""
    user = request.user
    
    # Filtros
    mes_seleccionado = request.GET.get('mes', '')
    asistencias = Asistencia.objects.filter(estudiante=user)
    
    if mes_seleccionado:
        try:
            fecha_mes = datetime.strptime(mes_seleccionado + '-01', '%Y-%m-%d')
            asistencias = asistencias.filter(
                fecha__year=fecha_mes.year,
                fecha__month=fecha_mes.month
            )
        except:
            pass
    
    asistencias = asistencias.order_by('-fecha')
    
    # Estadísticas
    estadisticas = {
        'presentes': asistencias.filter(estado='presente').count(),
        'ausentes': asistencias.filter(estado='ausente').count(),
        'tardanzas': asistencias.filter(estado='tardanza').count(),
        'justificadas': asistencias.filter(estado='justificado').count()
    }
    
    return render(request, 'academico/mis_asistencias.html', {
        'asistencias': asistencias,
        'estadisticas': estadisticas,
        'mes_seleccionado': mes_seleccionado
    })

@login_required
def mis_cursos(request):
    """Vista para ver cursos del estudiante"""
    user = request.user
    cursos = InscripcionCurso.objects.filter(estudiante=user, estado='activo')
    return render(request, 'academico/mis_cursos.html', {'cursos': cursos})

@login_required
def mis_asignaturas(request):
    """Vista para ver asignaturas del estudiante"""
    user = request.user
    cursos = InscripcionCurso.objects.filter(estudiante=user, estado='activo')
    asignaturas = Asignatura.objects.filter(
        horario__curso__in=cursos.values('curso')
    ).distinct()
    
    asignaturas_activas_count = asignaturas.filter(activa=True).count()
    
    return render(request, 'academico/mis_asignaturas.html', {
        'asignaturas': asignaturas,
        'asignaturas_activas_count': asignaturas_activas_count
    })
