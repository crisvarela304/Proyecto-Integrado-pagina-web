"""
Vistas seguras para mensajería interna
Con validaciones de autorización, concurrencia y prevención de IDOR
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db import transaction
from django.db.models import Q, Count, F
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import OuterRef
from .models import Conversacion, Mensaje, ConfiguracionMensajeria
from .forms import (
    BusquedaConversacionForm, 
    NuevaConversacionForm, 
    MensajeForm,
    PaginacionForm
)


def verificar_rol_mensajeria(user):
    """Decorator interno para verificar roles permitidos"""
    return user.is_authenticated and (
        user.groups.filter(name__in=['Alumno', 'Profesor']).exists()
    )


@login_required
def conversaciones_list(request):
    """
    Lista de conversaciones del usuario
    Con prevención de N+1 queries y paginación estable
    """
    if not verificar_rol_mensajeria(request.user):
        return redirect('usuarios:panel')
    
    # Crear configuración si no existe
    config, created = ConfiguracionMensajeria.objects.get_or_create(
        usuario=request.user
    )
    
    # Query optimizado con select_related para evitar N+1
    conversaciones = Conversacion.objects.filter(
        Q(alumno=request.user) | Q(profesor=request.user)
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
        'usuario_actual': request.user,
        'config': config,
    }
    
    return render(request, 'mensajeria/conversaciones_list.html', contexto)


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
    
    # Marcar como leído de forma atómica
    with transaction.atomic():
        conversacion.marcar_como_leido(request.user)
    
    # Obtener mensajes con select_related para optimizar
    mensajes = conversacion.mensajes.select_related('autor').order_by('-creado_en')
    
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
            mensaje.save()
            
            return JsonResponse({
                'status': 'success',
                'message_id': mensaje.id,
                'contenido': mensaje.contenido,
                'autor': mensaje.autor.get_full_name() or mensaje.autor.username,
                'creado_en': mensaje.creado_en.strftime('%d/%m/%Y %H:%M'),
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
    
    # Solo alumnos pueden eliminar conversaciones
    if not request.user.groups.filter(name='Alumno').exists():
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
    if not (request.user.is_staff or request.user.groups.filter(name='Profesor').exists()):
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
    ).order_by('-creado_en')
    
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


# Error handlers personalizados
def handler404(request, exception):
    """Manejador de errores 404 personalizado"""
    return render(request, 'core/error_404.html', status=404)


def handler500(request):
    """Manejador de errores 500 personalizado"""
    return render(request, 'core/error_500.html', status=500)
