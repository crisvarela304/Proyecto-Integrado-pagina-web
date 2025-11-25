from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from comunicacion.models import Noticia

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

def error_404(request, exception):
    """
    Manejador personalizado para errores 404.
    """
    return render(request, 'core/404.html', status=404)
