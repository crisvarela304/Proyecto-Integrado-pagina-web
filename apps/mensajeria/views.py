from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db import transaction
from django.contrib.auth.models import User

from django.utils import timezone
from academico.models import HorarioClases, InscripcionCurso
from .models import Conversacion, Mensaje, ConfiguracionMensajeria
from .forms import (
    MensajeForm,
    PaginacionForm,
    ProfesorMensajeForm,
    ContactoColegioForm,
    BusquedaConversacionForm,
    NuevaConversacionForm,
)

def verificar_rol_mensajeria(user):
    """Decorator interno para verificar roles permitidos"""
    if not user.is_authenticated:
        return False
    perfil = getattr(user, 'perfil', None)
    return perfil and perfil.tipo_usuario in ['estudiante', 'profesor']


def _estudiantes_de_profesor(profesor):
    """Obtiene estudiantes asociados a los cursos impartidos por el profesor"""
    cursos_ids = HorarioClases.objects.filter(
        profesor=profesor
    ).values_list('curso_id', flat=True).distinct()
    return User.objects.filter(
        cursos_inscrito__curso_id__in=cursos_ids,
        cursos_inscrito__estado='activo',
        perfil__tipo_usuario='estudiante'
    ).distinct()


def _profesores_de_estudiante(estudiante):
    """Obtiene profesores vinculados a los cursos del estudiante"""
    cursos_ids = InscripcionCurso.objects.filter(
        estudiante=estudiante,
        estado='activo'
    ).values_list('curso_id', flat=True)
    return User.objects.filter(
        horarioclases__curso_id__in=cursos_ids,
        perfil__tipo_usuario='profesor'
    ).distinct()


@login_required
def conversaciones_list(request):
    """
    Lista de conversaciones del usuario
    Con prevención de N+1 queries y paginación estable
    """
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')

    usuario_actual = request.user
    
    # Crear configuración si no existe
    config, created = ConfiguracionMensajeria.objects.get_or_create(
        usuario=usuario_actual
    )

    es_alumno = usuario_actual.groups.filter(name="Alumno").exists()
    es_profesor = usuario_actual.groups.filter(name="Profesor").exists()
    
    # Query optimizado con select_related para evitar N+1
    conversaciones = Conversacion.objects.filter(
        Q(alumno=usuario_actual) | Q(profesor=usuario_actual)
    ).select_related(
        'alumno', 'profesor'
    ).annotate(
        total_mensajes=Count('mensajes')
    ).order_by(
        '-ultimo_mensaje_en', '-creado_en'
    )
    
    # Búsqueda por nombre del otro participante
    form_busqueda = BusquedaConversacionForm(request.GET)
    if form_busqueda.is_valid():
        busqueda = form_busqueda.cleaned_data.get('busqueda', '').strip()
        if busqueda:
            conversaciones = conversaciones.filter(
                Q(alumno__first_name__icontains=busqueda) |
                Q(alumno__last_name__icontains=busqueda) |
                Q(alumno__username__icontains=busqueda) |
                Q(profesor__first_name__icontains=busqueda) |
                Q(profesor__last_name__icontains=busqueda) |
                Q(profesor__username__icontains=busqueda)
            )
    
    # Estadísticas para la vista
    total_conversaciones = conversaciones.count()
    no_leidos = sum([
        c.no_leidos_alumno if c.alumno == request.user else c.no_leidos_profesor
        for c in conversaciones
    ])
    
    # Paginación estable
    paginator = Paginator(conversaciones, 20)  # 20 conversaciones por página
    try:
        page_number = int(request.GET.get('page', 1))
        page_obj = paginator.get_page(page_number)
    except (ValueError, TypeError, EmptyPage, InvalidPage):
        page_number = 1
        page_obj = paginator.get_page(1)
    
    contexto = {
        'conversaciones': page_obj,
        'form_busqueda': form_busqueda,
        'no_leidos_total': no_leidos,
        'total_conversaciones': total_conversaciones,
        'usuario_actual': usuario_actual,
        'config': config,
        'es_alumno': es_alumno,
        'es_profesor': es_profesor,
    }
    
    return render(request, 'mensajeria/conversaciones_list.html', contexto)


@login_required
def bandeja_entrada(request):
    """Listado simple de mensajes recibidos por el usuario."""
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')
    
    mensajes_qs = Mensaje.objects.filter(
        receptor=request.user
    ).select_related('autor', 'conversacion').order_by('-fecha_creacion')
    
    paginator = Paginator(mensajes_qs, 20)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, InvalidPage):
        page_obj = paginator.get_page(1)
    
    contexto = {
        'page_obj': page_obj,
        'mensajes': page_obj.object_list,
    }
    return render(request, 'mensajeria/bandeja_entrada.html', contexto)


@login_required
def mensajes_enviados(request):
    """Listado de mensajes enviados por el usuario."""
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')

    mensajes_qs = Mensaje.objects.filter(
        autor=request.user
    ).select_related('receptor', 'conversacion').order_by('-fecha_creacion')

    paginator = Paginator(mensajes_qs, 20)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, InvalidPage):
        page_obj = paginator.get_page(1)

    contexto = {
        'page_obj': page_obj,
        'mensajes': page_obj.object_list,
    }
    return render(request, 'mensajeria/bandeja_enviados.html', contexto)


@login_required
def mensaje_detalle(request, mensaje_id):
    """Detalle individual de un mensaje directo."""
    mensaje = get_object_or_404(
        Mensaje.objects.select_related('autor', 'receptor', 'conversacion'),
        id=mensaje_id
    )
    if request.user not in (mensaje.autor, mensaje.receptor):
        return HttpResponseForbidden("No puedes ver este mensaje")

    if request.user == mensaje.receptor:
        mensaje.marcar_como_leido(request.user)
        mensaje.conversacion.marcar_como_leido(request.user)

    contexto = {
        'mensaje': mensaje,
        'conversacion': mensaje.conversacion,
        'otro_participante': mensaje.conversacion.get_otro_participante(request.user),
    }
    return render(request, 'mensajeria/mensaje_detalle.html', contexto)


@login_required
def profesor_redactar(request):
    """Vista simplificada para que el profesor envíe mensajes a sus alumnos."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'Solo los profesores pueden acceder a esta sección.')
        return redirect('usuarios:panel')

    if request.method == 'POST':
        form = ProfesorMensajeForm(request.POST, profesor=request.user)
        if form.is_valid():
            destinatario = form.cleaned_data['destinatario']
            asunto = form.cleaned_data['asunto']
            contenido = form.cleaned_data['contenido']
            conversacion, _ = Conversacion.objects.get_or_create(
                alumno=destinatario,
                profesor=request.user
            )
            Mensaje.objects.create(
                conversacion=conversacion,
                autor=request.user,
                receptor=destinatario,
                asunto=asunto,
                contenido=contenido
            )
            messages.success(request, 'Mensaje enviado correctamente.')
            return redirect('mensajeria:mensajes_enviados')
    else:
        form = ProfesorMensajeForm(profesor=request.user)

    contexto = {
        'form': form,
        'estudiantes': _estudiantes_de_profesor(request.user),
    }
    return render(request, 'mensajeria/profesor_redactar.html', contexto)


@login_required
def conversacion_detail(request, conversacion_id):
    """
    Detalle de conversación con mensajes
    Con autorización estricta y paginación de mensajes
    """
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')
    
    # PREVENCIÓN DE IDOR: Verificar que el usuario puede acceder
    conversacion = get_object_or_404(
        Conversacion.objects.select_related('alumno', 'profesor'),
        id=conversacion_id
    )
    
    if not conversacion.puede_acceder(request.user):
        return HttpResponseForbidden("No tienes permisos para acceder a esta conversación")
    
    # Marcar como leído de forma atómica y actualizar mensajes del usuario
    with transaction.atomic():
        conversacion.marcar_como_leido(request.user)
        conversacion.mensajes.filter(
            receptor=request.user,
            leido=False
        ).update(leido=True)
    
    # Obtener mensajes con select_related para optimizar
    mensajes = conversacion.mensajes.select_related('autor').order_by('-fecha_creacion')
    
    # Paginación de mensajes (50 por página)
    paginator = Paginator(mensajes, 50)
    try:
        page_number = int(request.GET.get('page', 1))
        page_obj = paginator.get_page(page_number)
    except (ValueError, TypeError, EmptyPage, InvalidPage):
        page_number = 1
        page_obj = paginator.get_page(1)
    
    # Formulario para nuevo mensaje
    form_mensaje = None
    if request.method == 'POST':
        form_mensaje = MensajeForm(
            request.POST, 
            request.FILES,
            usuario=request.user,
            conversacion=conversacion
        )
        if form_mensaje.is_valid():
            try:
                mensaje = form_mensaje.save(commit=False)
                mensaje.conversacion = conversacion
                mensaje.autor = request.user
                mensaje.receptor = conversacion.get_otro_participante(request.user)
                mensaje.save()
                
                messages.success(request, 'Mensaje enviado correctamente')
                return redirect('mensajeria:conversacion_detail', conversacion_id=conversacion_id)
            except Exception as e:
                messages.error(request, f'Error al enviar mensaje: {str(e)}')
    else:
        form_mensaje = MensajeForm(
            usuario=request.user,
            conversacion=conversacion
        )
    
    # Obtener otros datos necesarios
    otro_participante = conversacion.get_otro_participante(request.user)
    contador_no_leidos = conversacion.get_contador_no_leidos(request.user)
    
    contexto = {
        'conversacion': conversacion,
        'mensajes': page_obj.object_list,
        'page_obj': page_obj,
        'form_mensaje': form_mensaje,
        'otro_participante': otro_participante,
        'contador_no_leidos': contador_no_leidos,
        'usuario_actual': request.user,
    }
    
    return render(request, 'mensajeria/conversacion_detail.html', contexto)


@login_required
def nueva_conversacion(request):
    """
    Crear nueva conversación
    Con validaciones de rol y rate limiting
    """
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')
    
    if request.method == 'POST':
        form = NuevaConversacionForm(
            request.POST,
            usuario=request.user
        )
        if form.is_valid():
            try:
                conversacion, created = form.save(request.user)
                
                if created:
                    messages.success(request, 'Conversación creada correctamente')
                else:
                    messages.info(request, 'Ya existía una conversación con este usuario')
                
                return redirect('mensajeria:conversacion_detail', conversacion_id=conversacion.id)
            except Exception as e:
                messages.error(request, f'Error al crear conversación: {str(e)}')
    else:
        form = NuevaConversacionForm(usuario=request.user)
    
    contexto = {
        'form': form,
        'usuario_actual': request.user,
    }
    
    return render(request, 'mensajeria/nueva_conversacion.html', contexto)


@login_required
def enviar_mensaje(request, conversacion_id):
    """
    Endpoint AJAX para enviar mensajes
    Con validaciones de CSRF y autorización
    """
    if not verificar_rol_mensajeria(request.user):
        return HttpResponseForbidden("No tienes permisos")
    
    if request.method != 'POST':
        return HttpResponseBadRequest("Método no permitido")
    
    # Verificar CSRF token automáticamente con Django
    conversacion = get_object_or_404(
        Conversacion.objects.select_related('alumno', 'profesor'),
        id=conversacion_id
    )
    
    # Prevenir IDOR
    if not conversacion.puede_acceder(request.user):
        return HttpResponseForbidden("No tienes permisos para esta conversación")
    
    form = MensajeForm(
        request.POST,
        request.FILES,
        usuario=request.user,
        conversacion=conversacion
    )
    
    if form.is_valid():
        try:
            mensaje = form.save(commit=False)
            mensaje.conversacion = conversacion
            mensaje.autor = request.user
            mensaje.receptor = conversacion.get_otro_participante(request.user)
            mensaje.save()
            
            return JsonResponse({
                'status': 'success',
                'message_id': mensaje.id,
                'asunto': mensaje.asunto,
                'contenido': mensaje.contenido,
                'autor': mensaje.autor.get_full_name() or mensaje.autor.username,
                'fecha_creacion': mensaje.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al enviar mensaje: {str(e)}'
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Datos inválidos',
            'errors': form.errors
        })


@login_required  
def marcar_leido(request, conversacion_id):
    """
    Marcar conversación como leída
    Con validaciones de autorización
    """
    if not verificar_rol_mensajeria(request.user):
        return HttpResponseForbidden("No tienes permisos")
    
    if request.method != 'POST':
        return HttpResponseBadRequest("Método no permitido")
    
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    
    if not conversacion.puede_acceder(request.user):
        return HttpResponseForbidden("No tienes permisos para esta conversación")
    
    with transaction.atomic():
        conversacion.marcar_como_leido(request.user)
    
    return JsonResponse({'status': 'success'})


@login_required
def eliminar_conversacion(request, conversacion_id):
    """
    Eliminar conversación (solo alumno puede)
    Con validaciones de autorización y confirmación
    """
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')
    
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'estudiante':
        messages.error(request, 'Solo los alumnos pueden eliminar conversaciones')
        return redirect('mensajeria:conversaciones_list')
    
    conversacion = get_object_or_404(Conversacion, id=conversacion_id)
    
    if not conversacion.puede_acceder(request.user):
        return HttpResponseForbidden("No tienes permisos para esta conversación")
    
    if conversacion.alumno != request.user:
        messages.error(request, 'Solo puedes eliminar tus propias conversaciones')
        return redirect('mensajeria:conversacion_detail', conversacion_id=conversacion_id)
    
    if request.method == 'POST':
        try:
            # Confirmar eliminación
            conversacion.delete()
            messages.success(request, 'Conversación eliminada correctamente')
            return redirect('mensajeria:conversaciones_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar conversación: {str(e)}')
    
    contexto = {
        'conversacion': conversacion,
        'otro_participante': conversacion.profesor,
    }
    
    return render(request, 'mensajeria/eliminar_conversacion.html', contexto)


@login_required
def mensajes_destacados(request):
    """
    Vista de mensajes destacados para profesores
    Solo para usuarios con permisos especiales
    """
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')
    
    # Solo mostrar si el usuario es staff o profesor
    perfil = getattr(request.user, 'perfil', None)
    if not (request.user.is_staff or (perfil and perfil.tipo_usuario == 'profesor')):
        messages.error(request, 'No tienes permisos para ver esta página')
        return redirect('mensajeria:conversaciones_list')
    
    # Query para mensajes destacados (ejemplo: con adjuntos o de alta importancia)
    mensajes_destacados = Mensaje.objects.filter(
        conversacion__in=Conversacion.objects.filter(
            Q(alumno=request.user) | Q(profesor=request.user)
        )
    ).filter(
        Q(adjunto__isnull=False) | 
        Q(contenido__icontains='importante') |
        Q(contenido__icontains='urgente')
    ).select_related(
        'conversacion', 'autor'
    ).order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(mensajes_destacados, 30)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, InvalidPage):
        page_obj = paginator.get_page(1)
    
    contexto = {
        'mensajes': page_obj.object_list,
        'page_obj': page_obj,
    }
    
    return render(request, 'mensajeria/mensajes_destacados.html', contexto)


def contacto_colegio(request):
    """Formulario embebido para contactar al colegio."""
    if request.method == "POST":
        form = ContactoColegioForm(request.POST)
        if form.is_valid():
            contacto = form.save(commit=False)
            if request.user.is_authenticated:
                contacto.user = request.user
            contacto.save()
            messages.success(request, "Tu mensaje fue enviado correctamente.")
            return redirect('usuarios:panel')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial["nombre"] = request.user.get_full_name() or request.user.username
            initial["correo"] = request.user.email
        form = ContactoColegioForm(initial=initial)
    return render(request, "mensajeria/contacto_colegio_embed.html", {"form": form})


# Error handlers personalizados
def handler404(request, exception):
    """Manejador de errores 404 personalizado"""
    return render(request, 'core/404.html', status=404)


def handler500(request):
    """Manejador de errores 500 personalizado"""
    return render(request, 'core/error_500.html', status=500)

@login_required
def gestion_mensajeria(request):
    """Vista administrativa para monitorear el sistema de mensajería"""
    if not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect('usuarios:panel')
        
    total_mensajes = Mensaje.objects.count()
    total_conversaciones = Conversacion.objects.count()
    mensajes_hoy = Mensaje.objects.filter(fecha_creacion__date=timezone.now().date()).count()
    
    context = {
        'total_mensajes': total_mensajes,
        'total_conversaciones': total_conversaciones,
        'mensajes_hoy': mensajes_hoy
    }
    return render(request, 'mensajeria/gestion_mensajeria.html', context)
