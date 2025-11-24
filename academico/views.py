from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count
from datetime import datetime, timedelta
from django.db.models import Q
from .models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia

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
    
    for inscripcion in cursos:
        promedio = promedios_map.get(inscripcion.curso.id)
        inscripcion.promedio_calculado = round(promedio, 1) if promedio else None

    # Calificaciones recientes - Optimizado
    calificaciones = Calificacion.objects.filter(
        estudiante=user
    ).select_related('asignatura').order_by('-fecha_evaluacion')[:5]
    
    # Asistencia del mes actual
    hoy = datetime.now()
    inicio_mes = hoy.replace(day=1)
    asistencias_mes = Asistencia.objects.filter(
        estudiante=user, 
        fecha__gte=inicio_mes
    )
    
    # Calcular promedio general
    promedio_data = Calificacion.objects.filter(estudiante=user).aggregate(
        promedio=Avg('nota')
    )
    promedio_general = round(promedio_data['promedio'], 1) if promedio_data['promedio'] else None
    
    # Horario de hoy - Optimizado
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dia_actual = dias_semana[datetime.now().weekday()]
    
    curso_ids = [inscripcion.curso.id for inscripcion in cursos]
    horario_hoy = HorarioClases.objects.filter(
        curso__id__in=curso_ids,
        dia=dia_actual
    ).select_related('asignatura', 'profesor', 'sala').order_by('hora')
    
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
    
    # Cursos que enseña
    cursos = HorarioClases.objects.filter(profesor=user).values('curso').distinct()
    cursos_unicos = Curso.objects.filter(id__in=cursos)
    
    # Asignaturas asignadas
    asignaturas = HorarioClases.objects.filter(profesor=user).values('asignatura').distinct()
    asignaturas_unicas = Asignatura.objects.filter(id__in=asignaturas)
    
    # Horario de hoy
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dia_actual = dias_semana[datetime.now().weekday()]
    horario_hoy = HorarioClases.objects.filter(profesor=user, dia=dia_actual)
    
    # Calificaciones pendientes (últimas 30 calificaciones)
    calificaciones_pendientes = Calificacion.objects.filter(
        profesor=user
    ).order_by('-fecha_evaluacion')[:10]
    
    context.update({
        'cursos_unicos': cursos_unicos,
        'asignaturas_unicas': asignaturas_unicas,
        'horario_hoy': horario_hoy,
        'calificaciones_pendientes': calificaciones_pendientes
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
    promedio_data = calificaciones.aggregate(promedio=Avg('nota'))
    promedio_general = round(promedio_data['promedio'], 1) if promedio_data['promedio'] else None
    
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
    return render(request, 'academico/mis_asignaturas.html', {'asignaturas': asignaturas})
