"""
Vistas para el portal del Apoderado.
Permite a los apoderados ver información académica de sus pupilos.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import date, timedelta

from .models import PerfilUsuario, Pupilo
from .mixins import ApoderadoRequiredMixin
from academico.models import (
    Calificacion, Asistencia, InscripcionCurso, 
    Asignatura, Curso, Anotacion
)


def verificar_apoderado(view_func):
    """Decorador que verifica que el usuario sea apoderado"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('usuarios:login')
        
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.tipo_usuario != 'apoderado':
            messages.error(request, 'Esta sección es solo para apoderados.')
            return redirect('usuarios:panel')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def verificar_acceso_pupilo(view_func):
    """Decorador que verifica acceso al pupilo específico"""
    def wrapper(request, estudiante_id, *args, **kwargs):
        perfil = request.user.perfil
        if not Pupilo.objects.filter(apoderado=perfil, estudiante__id=estudiante_id).exists():
            messages.error(request, 'No tienes acceso a este estudiante.')
            return redirect('usuarios:panel_apoderado')
        return view_func(request, estudiante_id, *args, **kwargs)
    return wrapper


@login_required
@verificar_apoderado
def panel_apoderado(request):
    """
    Dashboard principal del apoderado.
    Si tiene un solo pupilo, muestra resumen directo.
    Si tiene varios, muestra selector.
    """
    perfil = request.user.perfil
    pupilos = Pupilo.objects.filter(apoderado=perfil).select_related(
        'estudiante', 'estudiante__user'
    )
    
    if not pupilos.exists():
        messages.info(request, 'No tienes pupilos asignados. Contacta con la administración.')
        return render(request, 'usuarios/apoderado/sin_pupilos.html')
    
    # Si solo tiene un pupilo, mostrar directamente su resumen
    if pupilos.count() == 1:
        pupilo = pupilos.first()
        return _render_resumen_pupilo(request, pupilo.estudiante, perfil)
    
    # Si tiene varios, mostrar selector
    return render(request, 'usuarios/apoderado/panel_apoderado.html', {
        'pupilos': pupilos
    })


@login_required
@verificar_apoderado
@verificar_acceso_pupilo
def resumen_pupilo(request, estudiante_id):
    """Resumen completo de un pupilo específico"""
    estudiante = get_object_or_404(PerfilUsuario, id=estudiante_id, tipo_usuario='estudiante')
    perfil = request.user.perfil
    return _render_resumen_pupilo(request, estudiante, perfil)


def _render_resumen_pupilo(request, estudiante, apoderado_perfil):
    """Renderiza el resumen de un pupilo"""
    user_estudiante = estudiante.user
    hoy = date.today()
    
    # Obtener inscripción actual
    inscripcion = InscripcionCurso.objects.filter(
        estudiante=user_estudiante,
        estado='activo'
    ).select_related('curso').first()
    
    # Últimas 5 calificaciones
    ultimas_notas = Calificacion.objects.filter(
        estudiante=user_estudiante
    ).select_related('asignatura').order_by('-fecha_evaluacion')[:5]
    
    # Porcentaje asistencia del mes
    inicio_mes = hoy.replace(day=1)
    asistencias_mes = Asistencia.objects.filter(
        estudiante=user_estudiante,
        fecha__gte=inicio_mes,
        fecha__lte=hoy
    )
    total_dias = asistencias_mes.count()
    dias_presente = asistencias_mes.filter(estado='presente').count()
    porcentaje_asistencia = round((dias_presente / total_dias * 100), 1) if total_dias > 0 else 100
    
    # Últimas anotaciones
    try:
        ultimas_anotaciones = Anotacion.objects.filter(
            estudiante=user_estudiante
        ).order_by('-fecha')[:3]
    except:
        ultimas_anotaciones = []
    
    # Promedios por asignatura
    promedios = Calificacion.objects.filter(
        estudiante=user_estudiante
    ).values('asignatura__nombre').annotate(
        promedio=Avg('nota')
    ).order_by('asignatura__nombre')
    
    context = {
        'estudiante': estudiante,
        'inscripcion': inscripcion,
        'ultimas_notas': ultimas_notas,
        'porcentaje_asistencia': porcentaje_asistencia,
        'ultimas_anotaciones': ultimas_anotaciones,
        'promedios': promedios,
        # Para navegación de pupilos
        'pupilos': Pupilo.objects.filter(apoderado=apoderado_perfil).select_related('estudiante')
    }
    
    return render(request, 'usuarios/apoderado/resumen_pupilo.html', context)


@login_required
@verificar_apoderado
@verificar_acceso_pupilo
def notas_pupilo(request, estudiante_id):
    """Vista detallada de notas del pupilo"""
    estudiante = get_object_or_404(PerfilUsuario, id=estudiante_id)
    user_estudiante = estudiante.user
    
    # Agrupar calificaciones por asignatura
    asignaturas_notas = {}
    calificaciones = Calificacion.objects.filter(
        estudiante=user_estudiante
    ).select_related('asignatura').order_by('asignatura__nombre', 'numero_evaluacion')
    
    for cal in calificaciones:
        nombre_asig = cal.asignatura.nombre
        if nombre_asig not in asignaturas_notas:
            asignaturas_notas[nombre_asig] = {
                'notas': [],
                'promedio': 0
            }
        asignaturas_notas[nombre_asig]['notas'].append(cal)
    
    # Calcular promedios
    for asig, data in asignaturas_notas.items():
        notas = [n.nota for n in data['notas'] if n.nota]
        data['promedio'] = round(sum(notas) / len(notas), 1) if notas else 0
    
    return render(request, 'usuarios/apoderado/notas_pupilo.html', {
        'estudiante': estudiante,
        'asignaturas_notas': asignaturas_notas
    })


@login_required
@verificar_apoderado
@verificar_acceso_pupilo
def asistencia_pupilo(request, estudiante_id):
    """Vista de historial de asistencia"""
    estudiante = get_object_or_404(PerfilUsuario, id=estudiante_id)
    user_estudiante = estudiante.user
    
    # Últimos 30 días
    hace_30_dias = date.today() - timedelta(days=30)
    
    asistencias = Asistencia.objects.filter(
        estudiante=user_estudiante,
        fecha__gte=hace_30_dias
    ).order_by('-fecha')
    
    # Estadísticas
    total = asistencias.count()
    presentes = asistencias.filter(estado='presente').count()
    ausentes = asistencias.filter(estado='ausente').count()
    tardanzas = asistencias.filter(estado='tardanza').count()
    
    return render(request, 'usuarios/apoderado/asistencia_pupilo.html', {
        'estudiante': estudiante,
        'asistencias': asistencias,
        'estadisticas': {
            'total': total,
            'presentes': presentes,
            'ausentes': ausentes,
            'tardanzas': tardanzas,
            'porcentaje': round((presentes / total * 100), 1) if total > 0 else 100
        }
    })
