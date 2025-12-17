from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from django.db.models import Q
from django.core.cache import cache
from .models import PerfilUsuario
import secrets
from .forms import (
    UserRegistrationForm,
    PerfilUsuarioRegistrationForm,
    LoginForm,
    UserEditForm,
    PerfilUsuarioEditForm,
    PasswordChangeForm,
)
from mensajeria.forms import ContactoColegioForm
from core.utils import limpiar_rut, validar_rut, formatear_rut

# Importaciones de modelos académicos y comunicación
from comunicacion.models import Noticia
from academico.models import RecursoAcademico, InscripcionCurso

# ============================================
# RATE LIMITING PARA LOGIN (Seguridad)
# ============================================
INTENTOS_MAXIMOS = 5  # Máximo intentos fallidos
TIEMPO_BLOQUEO = 15 * 60  # 15 minutos en segundos

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_intentos_key(ip):
    """Genera la clave de caché para los intentos"""
    return f"login_intentos_{ip}"

def verificar_bloqueo(request):
    """Verifica si la IP está bloqueada. Retorna (bloqueado, minutos_restantes)"""
    ip = get_client_ip(request)
    key = get_intentos_key(ip)
    intentos = cache.get(key, 0)
    
    if intentos >= INTENTOS_MAXIMOS:
        ttl = cache.ttl(key) if hasattr(cache, 'ttl') else TIEMPO_BLOQUEO
        minutos = max(1, ttl // 60) if ttl else 15
        return True, minutos
    return False, 0

def registrar_intento_fallido(request):
    """Registra un intento fallido de login"""
    ip = get_client_ip(request)
    key = get_intentos_key(ip)
    intentos = cache.get(key, 0)
    cache.set(key, intentos + 1, TIEMPO_BLOQUEO)
    return INTENTOS_MAXIMOS - intentos - 1

def limpiar_intentos(request):
    """Limpia los intentos fallidos después de un login exitoso"""
    ip = get_client_ip(request)
    key = get_intentos_key(ip)
    cache.delete(key)

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

# Iniciar sesión
def login_usuario(request):
    """Login genérico con protección contra ataques de fuerza bruta"""
    
    # Verificar si la IP está bloqueada
    bloqueado, minutos = verificar_bloqueo(request)
    if bloqueado:
        messages.error(request, f'⚠️ Demasiados intentos fallidos. Intenta de nuevo en {minutos} minutos.')
        return render(request, 'usuarios/login.html', {'form': LoginForm(), 'bloqueado': True})
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            rut_o_username = form.cleaned_data['rut_o_username']
            password = form.cleaned_data['password']
            
            # Intentar autenticar con RUT formateado (quita puntos, agrega guion)
            rut_fmt = formatear_rut(rut_o_username)
            user = autenticar_con_rut(request, rut_fmt, password)
            
            # Si falla, intentar como usuario estándar (usando el RUT formateado como username)
            if not user:
                user = authenticate(request, username=rut_fmt, password=password)
            
            # Si falla y el input original es diferente (ej: 'admin'), intentar con el original
            if not user and rut_fmt != rut_o_username:
                user = authenticate(request, username=rut_o_username, password=password)
            
            if user is not None:
                try:
                    perfil = user.perfil
                    if not perfil.activo:
                        messages.error(request, 'Su cuenta ha sido desactivada. Contacte al administrador.')
                        return render(request, 'usuarios/login.html', {'form': form})
                except PerfilUsuario.DoesNotExist:
                    pass
                
                # Login exitoso: limpiar intentos fallidos
                limpiar_intentos(request)
                login(request, user)
                return redirect('usuarios:panel')
            else:
                # Login fallido: registrar intento
                intentos_restantes = registrar_intento_fallido(request)
                if intentos_restantes > 0:
                    messages.error(request, f'RUT/Usuario o contraseña incorrectos. Te quedan {intentos_restantes} intentos.')
                else:
                    messages.error(request, '⚠️ Cuenta bloqueada por 15 minutos debido a múltiples intentos fallidos.')
                    return render(request, 'usuarios/login.html', {'form': form, 'bloqueado': True})
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

def login_base(request, allowed_roles, template_context, success_url='usuarios:panel'):
    """Vista base para logins específicos con protección rate limiting"""
    if request.user.is_authenticated:
        return redirect(success_url)

    # Verificar bloqueo
    bloqueado, minutos = verificar_bloqueo(request)
    if bloqueado:
        messages.error(request, f'⚠️ Demasiados intentos fallidos. Intenta de nuevo en {minutos} minutos.')
        context = {**template_context, 'form': LoginForm(), 'bloqueado': True}
        return render(request, 'usuarios/login_role.html', context)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            rut_o_username = form.cleaned_data['rut_o_username']
            password = form.cleaned_data['password']
            
            # Intentar autenticar con RUT formateado
            rut_fmt = formatear_rut(rut_o_username)
            user = autenticar_con_rut(request, rut_fmt, password)
            
            if not user:
                user = authenticate(request, username=rut_fmt, password=password)
            
            if not user and rut_fmt != rut_o_username:
                user = authenticate(request, username=rut_o_username, password=password)
            
            if user is not None:
                # Verificar rol
                try:
                    perfil = user.perfil
                    if not perfil.activo:
                        messages.error(request, 'Su cuenta ha sido desactivada.')
                        return render(request, 'usuarios/login_role.html', {**template_context, 'form': form})
                    
                    if perfil.tipo_usuario not in allowed_roles and not user.is_staff:
                        messages.error(request, 'No tienes permisos para acceder a esta sección.')
                        return render(request, 'usuarios/login_role.html', {**template_context, 'form': form})
                        
                except PerfilUsuario.DoesNotExist:
                    if not user.is_staff: # Permitir staff sin perfil
                        messages.error(request, 'Perfil de usuario no encontrado.')
                        return render(request, 'usuarios/login_role.html', {**template_context, 'form': form})
                
                # Login exitoso: limpiar intentos
                limpiar_intentos(request)
                login(request, user)
                return redirect(success_url)
            else:
                # Login fallido: registrar intento
                intentos_restantes = registrar_intento_fallido(request)
                if intentos_restantes > 0:
                    messages.error(request, f'Credenciales incorrectas. Te quedan {intentos_restantes} intentos.')
                else:
                    messages.error(request, '⚠️ Bloqueado por 15 minutos debido a múltiples intentos fallidos.')
                    context = {**template_context, 'form': form, 'bloqueado': True}
                    return render(request, 'usuarios/login_role.html', context)
    else:
        form = LoginForm()
    
    context = {**template_context, 'form': form}
    return render(request, 'usuarios/login_role.html', context)

def login_profesor(request):
    return login_base(
        request, 
        allowed_roles=['profesor', 'administrativo', 'directivo'],
        template_context={
            'page_title': 'Acceso Docentes',
            'page_subtitle': 'Plataforma de Gestión Académica',
            'theme_color': 'primary',
            'icon_class': 'bi-briefcase'
        }
    )

def login_estudiante(request):
    return login_base(
        request, 
        allowed_roles=['estudiante', 'apoderado'],
        template_context={
            'page_title': 'Acceso Estudiantes',
            'page_subtitle': 'Portal del Alumno',
            'theme_color': 'info',
            'icon_class': 'bi-mortarboard'
        }
    )

# Cerrar sesión
def logout_usuario(request):
    logout(request)
    return redirect('home') # Redirigir al home público en lugar del login genérico

# Página de inicio -> redirige al login
def index(request):
    return redirect('usuarios:login_estudiante') # Por defecto al login de estudiantes

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
        rol_codigo = perfil.tipo_usuario
    else:
        rut = user.username
        tipo_usuario = "Usuario"
        nombre_completo = user.get_full_name() or user.username
        rol_codigo = 'admin' if user.is_staff else 'unknown'
    
    # Flags para la plantilla
    es_profesor = rol_codigo in ['profesor', 'administrativo', 'directivo'] or user.is_staff
    es_estudiante = rol_codigo == 'estudiante'
    es_apoderado = rol_codigo == 'apoderado'
    
    # Contexto base
    ctx = {
        "user_profile": perfil,
        "perfil": perfil,
        "tipo_usuario": tipo_usuario,
        "rut": rut,
        "is_admin": user.is_staff,
        "es_profesor": es_profesor,
        "es_estudiante": es_estudiante,
        "es_apoderado": es_apoderado,
    }

    # --- Lógica delegada al servicio ---
    from .services import PanelService

    if es_estudiante:
        student_stats = PanelService.get_student_stats(user)
        ctx.update(student_stats)
        
        # --- NUEVO: Obtener Recursos Académicos ---
        inscripciones = InscripcionCurso.objects.filter(estudiante=user)
        cursos_del_estudiante = [i.curso for i in inscripciones]
        
        recursos_recientes = RecursoAcademico.objects.filter(
            curso__in=cursos_del_estudiante
        ).select_related('asignatura', 'profesor').order_by('-creado')[:5]
        
        ctx['recursos_recientes'] = recursos_recientes
        # ------------------------------------------

    # Si es administrativo o staff, redirigir al Dashboard Visual (LiceoOS)
    if user.is_staff or (perfil and perfil.tipo_usuario in ['administrativo', 'directivo']):
        return redirect('administrativo:dashboard')

    if es_profesor:
        professor_stats = PanelService.get_professor_stats(user)
        ctx.update(professor_stats)
    
    # Enlaces rápidos comunes (se mantienen igual que antes)
    quick_links = [
        {"icon": "bi-journal-text",   "title": "Noticias",     "desc": "Comunicados y avisos del liceo",
         "url": reverse("comunicacion:noticias"),  "color": "primary"},
        {"icon": "bi-envelope-paper", "title": "Mensajería",    "desc": "Comunicaciones internas",
         "url": reverse("mensajeria:bandeja_entrada"),                  "color": "warning"},
    ]
    
    # Enlaces específicos
    if es_estudiante:
        quick_links.extend([
             {"icon": "bi-calendar-date",  "title": "Mi horario",    "desc": "Horarios y asignaturas",
              "url": reverse("academico:mi_horario"),                  "color": "info"},
            {"icon": "bi-file-earmark-text", "title": "Certificados", "desc": "Descargar certificados",
             "url": reverse("documentos:documentos_list"),                  "color": "success"},
        ])
    
    if es_profesor:
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
            {"title": "Estadísticas", "url": reverse("comunicacion:estadisticas_noticias")},
        ]

    initial_contacto = {
        "nombre": user.get_full_name() or user.username,
        "correo": user.email,
    }
    contacto_form = ContactoColegioForm(initial=initial_contacto)
    
    ctx.update({
        "quick_links": quick_links,
        "admin_links": admin_links,
        "contacto_form": contacto_form,
        "form": contacto_form,
    })
    
    ctx.update({
        "quick_links": quick_links,
        "admin_links": admin_links,
        "contacto_form": contacto_form,
        "form": contacto_form,
    })
    
    if es_profesor or user.is_staff or (perfil and perfil.tipo_usuario in ['administrativo', 'directivo']):
        return render(request, "usuarios/panel_profesor.html", ctx)
    elif es_estudiante:
        return render(request, "usuarios/panel_estudiante.html", ctx)
    elif es_apoderado:
        return render(request, "usuarios/panel.html", ctx)
    else:
        return render(request, "usuarios/panel.html", ctx)

# Vista de perfil del usuario
@login_required
def mi_perfil(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        perfil_form = PerfilUsuarioEditForm(request.POST, request.FILES, instance=perfil)
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


# --- Vistas Administrativas (Evaluación y Matrícula) ---
from .forms import MatriculaForm
from academico.models import Curso, InscripcionCurso
from core.models import ConfiguracionAcademica

@login_required
def matricular_alumno_administrativo(request):
    """Vista para que administrativos matriculen alumnos rápidamente"""
    # Verificar permisos
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    
    if not es_admin:
        messages.error(request, "No tienes permisos para matricular alumnos.")
        return redirect('home')
        
    if request.method == 'POST':
        form = MatriculaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    data = form.cleaned_data
                    
                    # 1. Crear Usuario Estudiante
                    rut_est = data['rut_estudiante']
                    # Generar contraseña segura
                    password_temp = secrets.token_urlsafe(8)
                    # password_temp = rut_est[:4] # 4 primeros dígitos del RUT (MOVIDO A SECURE)
                    
                    user_est = User.objects.create_user(
                        username=rut_est, # Usamos RUT como username
                        email=data['email'] or f"{rut_est}@liceo.cl",
                        password=password_temp,
                        first_name=data['nombres'],
                        last_name=data['apellidos']
                    )
                    
                    # 2. Crear Perfil Estudiante
                    PerfilUsuario.objects.create(
                        user=user_est,
                        rut=rut_est,
                        tipo_usuario='estudiante',
                        activo=True
                    )
                    
                    # 3. Gestionar Apoderado (si aplica)
                    apoderado_user = None
                    if data['tiene_apoderado']:
                        rut_apod = data['rut_apoderado']
                        # Buscar si ya existe
                        try:
                            perfil_apod = PerfilUsuario.objects.get(rut=rut_apod)
                            apoderado_user = perfil_apod.user
                        except PerfilUsuario.DoesNotExist:
                            # Crear nuevo apoderado
                            apoderado_user = User.objects.create_user(
                                username=rut_apod,
                                email=data['email_apoderado'] or f"{rut_apod}@apoderados.liceo.cl",
                                password=secrets.token_urlsafe(8),
                                first_name=data['nombre_apoderado'].split()[0], # Intento básico de nombre
                                last_name=" ".join(data['nombre_apoderado'].split()[1:]) or "Apoderado"
                            )
                            PerfilUsuario.objects.create(
                                user=apoderado_user,
                                rut=rut_apod,
                                tipo_usuario='apoderado',
                                activo=True
                            )

                    # 4. Inscribir en Curso
                    curso = data['curso']
                    if curso:
                        anio_actual = ConfiguracionAcademica.get_actual().año_actual
                        InscripcionCurso.objects.create(
                            estudiante=user_est,
                            curso=curso,
                            # apoderado=apoderado_user, # Link no soportado en modelo actual
                            año=anio_actual,
                            estado='activo'
                        )
                        messages.success(request, f"Alumno {data['nombres']} matriculado exitosamente en {curso}.")
                    else:
                        messages.success(request, f"Alumno {data['nombres']} registrado (sin matrícula de curso).")
                        
                    return redirect('administrativo:dashboard')
                    
            except Exception as e:
                messages.error(request, f"Error en el proceso de matrícula: {str(e)}")
    else:
        form = MatriculaForm()
    
    return render(request, 'usuarios/matricular_alumno.html', {'form': form})

# --- Gestión de Usuarios (CRUD) ---
from django.core.paginator import Paginator

@login_required
def gestion_usuarios(request):
    """Vista principal para listar y gestionar usuarios por rol"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    if not es_admin:
        messages.error(request, "Acceso denegado.")
        return redirect('home')
        
    tipo = request.GET.get('tipo', 'estudiante')
    query = request.GET.get('q', '')
    
    # Mapeo de labels para UI
    labels = {
        'estudiante': 'Estudiantes',
        'profesor': 'Profesores',
        'administrativo': 'Staff Administrativo',
        'apoderado': 'Apoderados'
    }
    titulo = labels.get(tipo, 'Usuarios')
    
    # Filtrado base
    usuarios = PerfilUsuario.objects.select_related('user').filter(tipo_usuario=tipo)
    
    if query:
        usuarios = usuarios.filter(
            Q(rut__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )
        
    paginator = Paginator(usuarios.order_by('user__last_name'), 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'usuarios/gestion_usuarios.html', {
        'page_obj': page_obj,
        'tipo_actual': tipo,
        'titulo': titulo,
        'q': query
    })


# --- Creación Rápida de Usuarios (Staff/Profesores) ---
from .forms import QuickStudentCreationForm

@login_required
@user_passes_test(lambda u: u.is_staff or (hasattr(u, 'perfil') and u.perfil.tipo_usuario in ['administrativo', 'directivo']), login_url='usuarios:login')
def crear_usuario_rapido(request):
    if request.method == 'POST':
        form = QuickStudentCreationForm(request.POST)
        tipo_actual = request.POST.get('tipo_usuario', 'estudiante')
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, f"Usuario creado exitosamente.")
                    return redirect(f"{reverse('usuarios:gestion_usuarios')}?tipo={tipo_actual}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error creando usuario: {str(e)}")
                return redirect(f"{reverse('usuarios:gestion_usuarios')}?tipo={tipo_actual}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect(f"{reverse('usuarios:gestion_usuarios')}?tipo={tipo_actual}")
    
    return redirect('usuarios:gestion_usuarios')

@login_required
def editar_usuario(request, usuario_id):
    """Vista administrativa para editar un usuario"""
    # Verificar permisos de admin/staff
    if not (request.user.is_staff or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario in ['administrativo', 'directivo'])):
        messages.error(request, 'No tienes permisos para editar usuarios.')
        return redirect('usuarios:panel')

    usuario_editar = get_object_or_404(User, id=usuario_id)
    perfil_editar = getattr(usuario_editar, 'perfil', None)

    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            usuario_editar.first_name = request.POST.get('first_name')
            usuario_editar.last_name = request.POST.get('last_name')
            usuario_editar.email = request.POST.get('email')
            
            # Actualizar perfil si existe
            if perfil_editar:
                perfil_editar.telefono = request.POST.get('telefono')
                perfil_editar.direccion = request.POST.get('direccion')
                perfil_editar.save()

            # Cambio de contraseña opcional
            pass1 = request.POST.get('new_password1')
            pass2 = request.POST.get('new_password2')
            
            if pass1 or pass2:
                if pass1 != pass2:
                    messages.error(request, 'Las contraseñas no coinciden.')
                    return render(request, 'usuarios/editar_usuario.html', {
                        'usuario_editar': usuario_editar,
                        'perfil_editar': perfil_editar
                    })
                usuario_editar.set_password(pass1)
                messages.info(request, f'Se ha actualizado la contraseña de {usuario_editar.get_full_name()}.')

            usuario_editar.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            
            # Redirigir según tipo
            tipo_filtro = perfil_editar.tipo_usuario if perfil_editar else 'estudiante'
            return redirect(f"{reverse('usuarios:gestion_usuarios')}?tipo={tipo_filtro}")

        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')

    return render(request, 'usuarios/editar_usuario.html', {
        'usuario_editar': usuario_editar,
        'perfil_editar': perfil_editar
    })

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_reset_password(request):
    """
    Vista AJAX/POST para que un administrador cambie la contraseña de cualquier usuario.
    """
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_password = request.POST.get('new_password')
        
        if not user_id or not new_password:
            messages.error(request, 'Faltan datos para el cambio de contraseña.')
            return redirect('usuarios:gestion_usuarios')
            
        try:
            target_user = User.objects.get(id=user_id)
            target_user.set_password(new_password)
            target_user.save()
            
            # Obtener tipo para redirigir correctamente
            tipo_redirect = 'todos'
            if hasattr(target_user, 'perfil'):
                 tipo_redirect = target_user.perfil.tipo_usuario
            if target_user.is_staff:
                 tipo_redirect = 'administrador'
                 
            messages.success(request, f'Contraseña actualizada exitosamente para {target_user.get_full_name()}.')
            
            # Recuperar parámetros de filtro anteriores si existen
            current_type = request.POST.get('current_type', tipo_redirect)
            return redirect(f"{reverse('usuarios:gestion_usuarios')}?tipo={current_type}")
            
        except User.DoesNotExist:
            messages.error(request, 'El usuario especificado no existe.')
        except Exception as e:
            messages.error(request, f'Error al cambiar contraseña: {str(e)}')
            
    return redirect('usuarios:gestion_usuarios')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def eliminar_usuario(request, usuario_id):
    """
    Vista para eliminar un usuario y todos sus datos asociados.
    Solo accesible para superusuarios.
    """
    try:
        target_user = User.objects.get(id=usuario_id)
        
        # No permitir eliminarse a sí mismo
        if target_user == request.user:
            messages.error(request, 'No puedes eliminar tu propia cuenta.')
            return redirect('usuarios:gestion_usuarios')
        
        # No permitir eliminar otros superusuarios
        if target_user.is_superuser:
            messages.error(request, 'No puedes eliminar a otro superusuario.')
            return redirect('usuarios:gestion_usuarios')
        
        # Guardar nombre para el mensaje
        nombre_usuario = target_user.get_full_name() or target_user.username
        
        # Obtener tipo para redirigir correctamente
        tipo_redirect = 'todos'
        if hasattr(target_user, 'perfil'):
            tipo_redirect = target_user.perfil.tipo_usuario
        
        # Eliminar el usuario (Django CASCADE eliminará el perfil y relaciones)
        target_user.delete()
        
        messages.success(request, f'Usuario "{nombre_usuario}" eliminado correctamente junto con todos sus datos.')
        return redirect(f"{reverse('usuarios:gestion_usuarios')}?tipo={tipo_redirect}")
        
    except User.DoesNotExist:
        messages.error(request, 'El usuario especificado no existe.')
    except Exception as e:
        messages.error(request, f'Error al eliminar usuario: {str(e)}')
    
    return redirect('usuarios:gestion_usuarios')
