"""
Vistas para el Calendario Escolar.
Incluye vista JSON para FullCalendar y vista de página.
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime, date

from .models import Evento
from academico.models import InscripcionCurso
from core.models import ConfiguracionAcademica


def calendario_publico(request):
    """Vista del calendario público"""
    return render(request, 'calendario/calendario.html', {
        'titulo': 'Calendario Escolar'
    })


@login_required
def calendario_usuario(request):
    """Vista del calendario personalizado para usuario logueado"""
    return render(request, 'calendario/calendario.html', {
        'titulo': 'Mi Calendario',
        'personalizado': True
    })


def eventos_json(request):
    """
    API JSON para FullCalendar.
    Retorna eventos en formato compatible.
    Incluye: Eventos escolares + Tareas del estudiante
    """
    from tareas.models import Tarea
    
    # Parámetros de FullCalendar
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # Filtrar eventos activos y visibles
    eventos = Evento.objects.filter(activo=True, visible_para_todos=True)
    
    # Filtrar por rango de fechas si se proporciona
    if start:
        try:
            fecha_inicio = datetime.strptime(start[:10], '%Y-%m-%d').date()
            eventos = eventos.filter(fecha_inicio__gte=fecha_inicio)
        except ValueError:
            pass
    
    if end:
        try:
            fecha_fin = datetime.strptime(end[:10], '%Y-%m-%d').date()
            eventos = eventos.filter(fecha_inicio__lte=fecha_fin)
        except ValueError:
            pass
    
    # Lista para acumular todos los eventos
    eventos_data = []
    
    # Si el usuario está logueado, incluir eventos personalizados
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfil', None)
        
        if perfil and perfil.tipo_usuario == 'estudiante':
            try:
                anio = ConfiguracionAcademica.get_actual().año_actual
                inscripcion = InscripcionCurso.objects.filter(
                    estudiante=request.user,
                    año=anio,
                    estado='activo'
                ).first()
                
                if inscripcion:
                    # Agregar eventos del curso
                    eventos_curso = Evento.objects.filter(
                        activo=True,
                        curso=inscripcion.curso
                    )
                    eventos = eventos | eventos_curso
                    
                    # ========== INTEGRACIÓN DE TAREAS ==========
                    tareas = Tarea.objects.filter(
                        curso=inscripcion.curso,
                        estado='publicada'
                    )
                    
                    for tarea in tareas:
                        # Color según si está vencida o no
                        if tarea.esta_vencida:
                            color = '#dc3545'  # Rojo - vencida
                        else:
                            color = '#28a745'  # Verde - pendiente
                        
                        eventos_data.append({
                            'id': f'tarea_{tarea.id}',
                            'title': f'📝 {tarea.titulo}',
                            'start': str(tarea.fecha_entrega),
                            'color': color,
                            'allDay': True,
                            'url': f'/tareas/entregar/{tarea.id}/',
                            'extendedProps': {
                                'tipo': 'tarea',
                                'asignatura': tarea.asignatura.nombre,
                                'descripcion': tarea.descripcion[:200] + '...' if len(tarea.descripcion) > 200 else tarea.descripcion,
                                'puntaje': str(tarea.puntaje_maximo),
                            }
                        })
                    # ============================================
                    
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error cargando eventos del curso: {e}")
        
        elif perfil and perfil.tipo_usuario == 'profesor':
            # Profesores ven sus tareas asignadas
            try:
                tareas_profe = Tarea.objects.filter(
                    profesor=request.user,
                    estado='publicada'
                )
                
                for tarea in tareas_profe:
                    eventos_data.append({
                        'id': f'tarea_{tarea.id}',
                        'title': f'📋 {tarea.titulo} ({tarea.curso.nombre})',
                        'start': str(tarea.fecha_entrega),
                        'color': '#6f42c1',  # Morado para profesor
                        'allDay': True,
                        'url': f'/tareas/ver-entregas/{tarea.id}/',
                        'extendedProps': {
                            'tipo': 'tarea_profesor',
                            'asignatura': tarea.asignatura.nombre,
                            'descripcion': f'{tarea.curso.nombre} - {tarea.asignatura.nombre}',
                        }
                    })
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error cargando tareas del profesor: {e}")
    
    # Convertir eventos del modelo a formato FullCalendar
    eventos_data.extend([evento.to_fullcalendar() for evento in eventos.distinct()])
    
    return JsonResponse(eventos_data, safe=False)


@login_required
def crear_evento(request):
    """Vista para crear evento (solo staff)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    if request.method == 'POST':
        from django.views.decorators.csrf import csrf_exempt
        import json
        
        try:
            data = json.loads(request.body)
            evento = Evento.objects.create(
                titulo=data.get('titulo'),
                descripcion=data.get('descripcion', ''),
                tipo=data.get('tipo', 'academico'),
                fecha_inicio=data.get('fecha_inicio'),
                fecha_fin=data.get('fecha_fin'),
                color=data.get('color', '#3788d8'),
                creado_por=request.user
            )
            return JsonResponse({
                'success': True,
                'evento': evento.to_fullcalendar()
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
