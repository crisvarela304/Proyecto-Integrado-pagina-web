"""
Vistas para el Sistema de Tareas.
Incluye CRUD para profesores y vista de entregas para estudiantes.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from datetime import date

from .models import Tarea, Entrega
from academico.models import Curso, Asignatura, HorarioClases, InscripcionCurso
from core.models import ConfiguracionAcademica


def es_profesor(user):
    """Verifica si el usuario es profesor"""
    perfil = getattr(user, 'perfil', None)
    return perfil and perfil.tipo_usuario in ['profesor', 'directivo', 'administrativo']


def es_estudiante(user):
    """Verifica si el usuario es estudiante"""
    perfil = getattr(user, 'perfil', None)
    return perfil and perfil.tipo_usuario == 'estudiante'


# =====================
# VISTAS DEL PROFESOR
# =====================

@login_required
def lista_tareas_profesor(request):
    """Lista de tareas creadas por el profesor"""
    if not es_profesor(request.user):
        messages.error(request, 'Acceso solo para profesores.')
        return redirect('usuarios:panel')
    
    tareas = Tarea.objects.filter(profesor=request.user).annotate(
        num_entregas=Count('entregas')
    ).order_by('-created_at')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        tareas = tareas.filter(estado=estado)
    
    paginator = Paginator(tareas, 10)
    page = request.GET.get('page', 1)
    tareas_page = paginator.get_page(page)
    
    return render(request, 'tareas/profesor/lista_tareas.html', {
        'tareas': tareas_page,
        'estado_filter': estado
    })


@login_required
def crear_tarea(request):
    """Crear nueva tarea"""
    if not es_profesor(request.user):
        messages.error(request, 'Acceso solo para profesores.')
        return redirect('usuarios:panel')
    
    # Obtener cursos donde el profesor dicta clases
    cursos_ids = HorarioClases.objects.filter(
        profesor=request.user
    ).values_list('curso_id', flat=True).distinct()
    cursos = Curso.objects.filter(id__in=cursos_ids, activo=True)
    
    asignaturas_ids = HorarioClases.objects.filter(
        profesor=request.user
    ).values_list('asignatura_id', flat=True).distinct()
    asignaturas = Asignatura.objects.filter(id__in=asignaturas_ids)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        tipo = request.POST.get('tipo')
        curso_id = request.POST.get('curso')
        asignatura_id = request.POST.get('asignatura')
        fecha_entrega = request.POST.get('fecha_entrega')
        puntaje_maximo = request.POST.get('puntaje_maximo', 100)
        
        if not all([titulo, descripcion, curso_id, asignatura_id, fecha_entrega]):
            messages.error(request, 'Todos los campos obligatorios deben ser completados.')
        else:
            tarea = Tarea.objects.create(
                titulo=titulo,
                descripcion=descripcion,
                tipo=tipo,
                curso_id=curso_id,
                asignatura_id=asignatura_id,
                profesor=request.user,
                fecha_entrega=fecha_entrega,
                puntaje_maximo=puntaje_maximo,
                estado='publicada'
            )
            
            # Guardar archivo si existe
            if 'archivo_adjunto' in request.FILES:
                tarea.archivo_adjunto = request.FILES['archivo_adjunto']
                tarea.save()
            
            messages.success(request, f'Tarea "{titulo}" creada exitosamente.')
            return redirect('tareas:lista_tareas_profesor')
    
    return render(request, 'tareas/profesor/crear_tarea.html', {
        'cursos': cursos,
        'asignaturas': asignaturas,
        'tipos': Tarea.TIPO_CHOICES
    })


@login_required
def ver_entregas(request, tarea_id):
    """Ver entregas de una tarea"""
    tarea = get_object_or_404(Tarea, id=tarea_id, profesor=request.user)
    entregas = tarea.entregas.select_related('estudiante').order_by('-fecha_entrega')
    
    # Estudiantes pendientes
    anio = ConfiguracionAcademica.get_actual().año_actual
    inscritos = InscripcionCurso.objects.filter(
        curso=tarea.curso, año=anio, estado='activo'
    ).select_related('estudiante')
    
    entregaron_ids = entregas.values_list('estudiante_id', flat=True)
    pendientes = [i for i in inscritos if i.estudiante_id not in entregaron_ids]
    
    return render(request, 'tareas/profesor/ver_entregas.html', {
        'tarea': tarea,
        'entregas': entregas,
        'pendientes': pendientes
    })


@login_required
def calificar_entrega(request, entrega_id):
    """Calificar una entrega"""
    entrega = get_object_or_404(Entrega, id=entrega_id, tarea__profesor=request.user)
    
    if request.method == 'POST':
        puntaje = request.POST.get('puntaje')
        comentario = request.POST.get('comentario', '')
        
        from django.utils import timezone
        entrega.puntaje = puntaje
        entrega.comentario_profesor = comentario
        entrega.fecha_revision = timezone.now()
        entrega.estado = 'revisada'
        entrega.save()
        
        messages.success(request, f'Calificación guardada para {entrega.estudiante.get_full_name()}.')
        return redirect('tareas:ver_entregas', tarea_id=entrega.tarea.id)
    
    return render(request, 'tareas/profesor/calificar_entrega.html', {
        'entrega': entrega
    })


# =====================
# VISTAS DEL ESTUDIANTE
# =====================

@login_required
def mis_tareas(request):
    """Lista de tareas para el estudiante"""
    if not es_estudiante(request.user):
        messages.error(request, 'Acceso solo para estudiantes.')
        return redirect('usuarios:panel')
    
    # Obtener curso actual del estudiante
    anio = ConfiguracionAcademica.get_actual().año_actual
    inscripcion = InscripcionCurso.objects.filter(
        estudiante=request.user, año=anio, estado='activo'
    ).first()
    
    if not inscripcion:
        messages.warning(request, 'No estás inscrito en ningún curso.')
        return render(request, 'tareas/estudiante/mis_tareas.html', {'tareas': []})
    
    # Tareas del curso
    tareas = Tarea.objects.filter(
        curso=inscripcion.curso,
        estado='publicada'
    ).order_by('-fecha_entrega')
    
    # Marcar cuáles ya entregó
    mis_entregas = Entrega.objects.filter(
        estudiante=request.user
    ).values_list('tarea_id', flat=True)
    
    for tarea in tareas:
        tarea.ya_entregue = tarea.id in mis_entregas
        tarea.esta_vencida_flag = tarea.esta_vencida
    
    return render(request, 'tareas/estudiante/mis_tareas.html', {
        'tareas': tareas,
        'curso': inscripcion.curso
    })


@login_required
def entregar_tarea(request, tarea_id):
    """Entregar una tarea"""
    # Verificar que es estudiante
    if not es_estudiante(request.user):
        messages.error(request, 'Solo los estudiantes pueden entregar tareas.')
        return redirect('usuarios:panel')
    
    tarea = get_object_or_404(Tarea, id=tarea_id, estado='publicada')
    
    # Verificar que el estudiante está en el curso
    anio = ConfiguracionAcademica.get_actual().año_actual
    inscrito = InscripcionCurso.objects.filter(
        estudiante=request.user,
        curso=tarea.curso,
        año=anio,
        estado='activo'
    ).exists()
    
    if not inscrito:
        messages.error(request, 'No puedes entregar esta tarea.')
        return redirect('tareas:mis_tareas')
    
    # Verificar si ya entregó
    entrega_existente = Entrega.objects.filter(
        tarea=tarea, estudiante=request.user
    ).first()
    
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        comentario = request.POST.get('comentario', '')
        
        if not archivo:
            messages.error(request, 'Debes adjuntar un archivo.')
        else:
            if entrega_existente:
                # Actualizar entrega
                entrega_existente.archivo = archivo
                entrega_existente.comentario_estudiante = comentario
                entrega_existente.estado = 'pendiente'
                entrega_existente.save()
                messages.success(request, 'Tu entrega ha sido actualizada.')
            else:
                # Nueva entrega
                Entrega.objects.create(
                    tarea=tarea,
                    estudiante=request.user,
                    archivo=archivo,
                    comentario_estudiante=comentario
                )
                messages.success(request, 'Tu tarea ha sido entregada exitosamente.')
            
            return redirect('tareas:mis_tareas')
    
    return render(request, 'tareas/estudiante/entregar_tarea.html', {
        'tarea': tarea,
        'entrega': entrega_existente
    })
