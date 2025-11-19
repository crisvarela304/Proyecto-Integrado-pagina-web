from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from .models import PerfilUsuario

def limpiar_rut(rut):
    """Limpia y formatea un RUT chileno"""
    if not rut:
        return ""
    rut = rut.strip().replace('.', '').replace('-', '').upper()
    return rut

def validar_rut_completo(rut):
    """Valida un RUT chileno completo"""
    if not rut:
        return False
    
    # Limpiar RUT
    rut = rut.strip().replace('.', '').replace('-', '').upper()
    
    if len(rut) < 2:
        return False
    
    # Separar cuerpo y dígito verificador
    cuerpo = rut[:-1]
    dv = rut[-1]
    
    try:
        # Calcular dígito verificador
        suma = 0
        multiplicador = 2
        
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplicador
            multiplicador += 1
            if multiplicador == 8:
                multiplicador = 2
        
        resto = suma % 11
        dv_calculado = 11 - resto
        
        if dv_calculado == 11:
            dv_calculado = '0'
        elif dv_calculado == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(dv_calculado)
        
        return dv == dv_calculado
    except:
        return False

def autenticar_con_rut(request, rut, password):
    """Autentica un usuario usando su RUT"""
    try:
        # Buscar perfil por RUT
        perfil = PerfilUsuario.objects.get(rut=rut, activo=True)
        user = perfil.user
        
        # Verificar que la contraseña sea correcta
        if user.check_password(password):
            return user
        return None
    except PerfilUsuario.DoesNotExist:
        return None

from .forms import UserRegistrationForm, PerfilUsuarioRegistrationForm

# Registrar usuario
def registrar_usuario(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        perfil_form = PerfilUsuarioRegistrationForm(request.POST)
        if user_form.is_valid() and perfil_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    user.set_password(user_form.cleaned_data['password'])
                    user.save()
                    perfil = perfil_form.save(commit=False)
                    perfil.user = user
                    perfil.save()
                    messages.success(request, 'Usuario registrado exitosamente. Ya puedes iniciar sesión.')
                    return redirect('usuarios:login')
            except Exception as e:
                messages.error(request, f'Error al registrar usuario: {str(e)}')
        else:
            # Combine form errors for display
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{user_form.fields[field].label}: {error}")
            for field, errors in perfil_form.errors.items():
                for error in errors:
                    messages.error(request, f"{perfil_form.fields[field].label}: {error}")
    else:
        user_form = UserRegistrationForm()
        perfil_form = PerfilUsuarioRegistrationForm()
    
    return render(request, 'usuarios/registrar.html', {
        'user_form': user_form,
        'perfil_form': perfil_form
    })

from .forms import UserRegistrationForm, PerfilUsuarioRegistrationForm, LoginForm

# Iniciar sesión
def login_usuario(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            rut_o_username = form.cleaned_data['rut_o_username']
            password = form.cleaned_data['password']
            
            user = autenticar_con_rut(request, rut_o_username, password)
            
            if not user:
                user = authenticate(request, username=rut_o_username, password=password)
            
            if user is not None:
                try:
                    perfil = user.perfil
                    if not perfil.activo:
                        messages.error(request, 'Su cuenta ha sido desactivada. Contacte al administrador.')
                        return render(request, 'usuarios/login.html', {'form': form})
                except PerfilUsuario.DoesNotExist:
                    pass
                
                login(request, user)
                return redirect('usuarios:panel')
            else:
                messages.error(request, 'RUT/Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

# Cerrar sesión
def logout_usuario(request):
    logout(request)
    return redirect('usuarios:login')

# Página de inicio -> redirige al login
def index(request):
    return redirect('login')

# Panel tipo intranet (con accesos rápidos)
@login_required
def panel(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    # Obtener información del usuario
    if perfil:
        rut = perfil.rut
        tipo_usuario = perfil.get_tipo_usuario_display()
        nombre_completo = perfil.nombre_completo
    else:
        rut = user.username
        tipo_usuario = "Usuario"
        nombre_completo = user.get_full_name() or user.username
    
    # Enlaces rápidos según tipo de usuario
    quick_links = [
        {"icon": "bi-journal-text",   "title": "Noticias",     "desc": "Comunicados y avisos del liceo",
         "url": reverse("noticias"),  "color": "primary"},
        {"icon": "bi-calendar-date",  "title": "Mi horario",    "desc": "Horarios y asignaturas",
         "url": reverse("academico:mi_horario"),                  "color": "info"},
        {"icon": "bi-file-earmark-text", "title": "Certificados", "desc": "Descargar certificados",
         "url": reverse("documentos:documentos_list"),                  "color": "success"},
        {"icon": "bi-envelope-paper", "title": "Mensajería",    "desc": "Comunicaciones internas",
         "url": reverse("mensajeria:bandeja_entrada"),                  "color": "warning"},
    ]
    
    # Enlaces adicionales según tipo de usuario
    if perfil and perfil.tipo_usuario in ['profesor', 'administrativo', 'directivo']:
        quick_links.extend([
            {"icon": "bi-people", "title": "Gestionar alumnos", "desc": "Administrar estudiantes",
             "url": reverse("academico:panel_profesor"), "color": "secondary"},
            {"icon": "bi-clipboard-data", "title": "Reportes", "desc": "Informes y estadísticas",
             "url": reverse("academico:estadisticas_profesor"), "color": "dark"},
        ])
    
    # Enlaces administrativos
    admin_links = []
    if user.is_staff:
        admin_links = [
            {"title": "Administración Django", "url": reverse("admin:index")},
            {"title": "Gestionar Noticias", "url": reverse("admin:comunicacion_noticia_changelist")},
            {"title": "Gestionar Usuarios", "url": reverse("admin:usuarios_perfilusuario_changelist")},
            {"title": "Estadísticas", "url": reverse("estadisticas_noticias")},
        ]

    ctx = {
        "user_profile": perfil,
        "tipo_usuario": tipo_usuario,
        "rut": rut,
        "quick_links": quick_links,
        "admin_links": admin_links,
        "is_admin": user.is_staff,
    }
    return render(request, "usuarios/panel.html", ctx)

from .forms import UserRegistrationForm, PerfilUsuarioRegistrationForm, LoginForm, UserEditForm, PerfilUsuarioEditForm

# Vista de perfil del usuario
@login_required
def mi_perfil(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        perfil_form = PerfilUsuarioEditForm(request.POST, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    perfil_form.save()
                    messages.success(request, 'Perfil actualizado exitosamente.')
                    return redirect('usuarios:mi_perfil')
            except Exception as e:
                messages.error(request, f'Error al actualizar perfil: {str(e)}')
        else:
            # Combine form errors for display
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{user_form.fields[field].label}: {error}")
            for field, errors in perfil_form.errors.items():
                for error in errors:
                    messages.error(request, f"{perfil_form.fields[field].label}: {error}")
    else:
        user_form = UserEditForm(instance=user)
        perfil_form = PerfilUsuarioEditForm(instance=perfil)
    
    return render(request, "usuarios/perfil.html", {
        "user_form": user_form,
        "perfil_form": perfil_form
    })

from .forms import UserRegistrationForm, PerfilUsuarioRegistrationForm, LoginForm, UserEditForm, PerfilUsuarioEditForm, PasswordChangeForm

# Vista de cambio de contraseña
@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('usuarios:panel')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, "usuarios/cambiar_password.html", {'form': form})
