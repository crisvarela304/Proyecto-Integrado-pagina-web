from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from comunicacion.models import Noticia
from .models import ConfiguracionAcademica, ConfiguracionSistema

def home(request):
    noticias_destacadas = Noticia.objects.filter(es_publica=True, destacado=True).order_by('-creado')[:3]
    context = {
        'noticias_destacadas': noticias_destacadas
    }
    return render(request, 'core/home.html', context)

def contacto(request):
    """Página de contacto"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        email = request.POST.get('email', '')
        asunto = request.POST.get('asunto', '')
        mensaje = request.POST.get('mensaje', '')
        
        # Simular envío de correo (en desarrollo)
        messages.success(request, '¡Mensaje enviado! Te contactaremos pronto.')
        return render(request, 'core/contacto.html')
    
    return render(request, 'core/contacto.html')

@login_required
def configuracion_sistema(request):
    """Vista para gestión de configuraciones globales (Core)"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    if not es_admin:
        messages.error(request, "Acceso denegado.")
        return redirect('home')

    config_academica = ConfiguracionAcademica.get_actual()
    settings_globales = ConfiguracionSistema.objects.all()

    if request.method == 'POST':
        # Guardar Config Académica
        anio = request.POST.get('anio')
        semestre = request.POST.get('semestre')
        
        if anio and semestre:
            config_academica.año_actual = anio
            config_academica.semestre_actual = semestre
            config_academica.save()
            messages.success(request, "Configuración académica actualizada.")
            return redirect('configuracion_sistema')

    return render(request, 'core/configuracion_sistema.html', {
        'config_academica': config_academica,
        'semestres': ConfiguracionAcademica.SEMESTRE_CHOICES,
        'settings': settings_globales
    })


def error_404(request, exception):
    """
    Manejador personalizado para errores 404.
    """
    return render(request, 'core/404.html', status=404)
