from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from django.db.models import Avg, Count, Q
from datetime import datetime
from .models import PerfilUsuario
from .forms import (
    UserRegistrationForm,
    PerfilUsuarioRegistrationForm,
    LoginForm,
    UserEditForm,
    PerfilUsuarioEditForm,
    PasswordChangeForm,
)
from mensajeria.forms import ContactoColegioForm
from core.utils import limpiar_rut, validar_rut

# Importaciones de modelos académicos y comunicación
from academico.models import Curso, InscripcionCurso, Calificacion, Asistencia, HorarioClases, Asignatura
from comunicacion.models import Noticia

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
    """Login genérico o redirección"""
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

def login_base(request, allowed_roles, template_context, success_url='usuarios:panel'):
    """Vista base para logins específicos"""
    if request.user.is_authenticated:
        return redirect(success_url)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            rut_o_username = form.cleaned_data['rut_o_username']
            password = form.cleaned_data['password']
            
            user = autenticar_con_rut(request, rut_o_username, password)
            if not user:
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
                
                login(request, user)
                return redirect(success_url)
            else:
                messages.error(request, 'Credenciales incorrectas.')
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
    es_estudiante = rol_codigo in ['estudiante', 'apoderado']
    
    # Contexto extendido
    ctx = {
        "user_profile": perfil,
        "perfil": perfil,
        "tipo_usuario": tipo_usuario,
        "rut": rut,
        "is_admin": user.is_staff,
        "es_profesor": es_profesor,
        "es_estudiante": es_estudiante,
    }

    # --- Lógica para Estudiantes ---
    if es_estudiante:
        # Promedio General
        promedio_data = Calificacion.objects.filter(estudiante=user).aggregate(promedio=Avg('nota'))
        promedio_general = round(promedio_data['promedio'], 1) if promedio_data['promedio'] else None
        
        # Asistencia Global (Total)
        total_asistencias = Asistencia.objects.filter(estudiante=user).count()
        asistencias_presente = Asistencia.objects.filter(estudiante=user, estado='presente').count()
        asistencia_porcentaje = round((asistencias_presente / total_asistencias * 100), 0) if total_asistencias > 0 else 0
        
        # Cursos inscritos y cálculo de promedios por curso
        cursos_inscritos = InscripcionCurso.objects.filter(estudiante=user, estado='activo').select_related('curso')
        
        # Pre-calcular promedios por curso
        calificaciones_all = Calificacion.objects.filter(estudiante=user).values('curso').annotate(promedio=Avg('nota'))
        promedios_map = {item['curso']: item['promedio'] for item in calificaciones_all}
        
        # Asistencia por curso
        asistencias_por_curso = Asistencia.objects.filter(estudiante=user).values('curso').annotate(
            total=Count('id'),
            presentes=Count('id', filter=Q(estado='presente'))
        )
        asistencia_map = {}
        for item in asistencias_por_curso:
            if item['total'] > 0:
                porcentaje = (item['presentes'] / item['total']) * 100
                asistencia_map[item['curso']] = round(porcentaje, 0)
            else:
                asistencia_map[item['curso']] = 0

        for inscripcion in cursos_inscritos:
            promedio = promedios_map.get(inscripcion.curso.id)
            inscripcion.promedio_calculado = round(promedio, 1) if promedio else None
            inscripcion.asistencia_porcentaje = asistencia_map.get(inscripcion.curso.id, 0)

        ctx.update({
            'promedio_general': promedio_general,
            'asistencia_porcentaje': asistencia_porcentaje,
            'cursos_inscritos': cursos_inscritos,
        })

    # --- Lógica para Profesores ---
    if es_profesor:
        # Cursos asignados
        horarios = HorarioClases.objects.filter(profesor=user).select_related('curso', 'asignatura')
        cursos_ids = horarios.values_list('curso_id', flat=True).distinct()
        cursos_unicos = Curso.objects.filter(id__in=cursos_ids)
        
        # Total alumnos reales y promedios por curso
        total_alumnos_real = 0
        for curso in cursos_unicos:
            cantidad = InscripcionCurso.objects.filter(curso=curso, estado='activo').count()
            curso.cantidad_alumnos_real = cantidad
            total_alumnos_real += cantidad
            
            # Promedio última nota
            ultima_eval = Calificacion.objects.filter(curso=curso, profesor=user).order_by('-fecha_evaluacion').first()
            if ultima_eval:
                promedio_eval = Calificacion.objects.filter(
                    curso=curso, 
                    asignatura=ultima_eval.asignatura, 
                    numero_evaluacion=ultima_eval.numero_evaluacion
                ).aggregate(Avg('nota'))['nota__avg']
                curso.promedio_ultima_nota = round(promedio_eval, 1) if promedio_eval else None
                curso.nombre_ultima_eval = f"{ultima_eval.asignatura.nombre} - Nota {ultima_eval.numero_evaluacion}"
            else:
                curso.promedio_ultima_nota = None
                curso.nombre_ultima_eval = "Sin evaluaciones"

        # Consejos de profesores
        consejos = Noticia.objects.filter(categoria='consejo', es_publica=True).order_by('-creado')[:5]
        
        ctx.update({
            'cursos_unicos': cursos_unicos,
            'total_alumnos_real': total_alumnos_real,
            'consejos': consejos,
        })
    
    # Enlaces rápidos comunes (se mantienen igual que antes)
    quick_links = [
        {"icon": "bi-journal-text",   "title": "Noticias",     "desc": "Comunicados y avisos del liceo",
         "url": reverse("noticias"),  "color": "primary"},
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
            {"title": "Estadísticas", "url": reverse("estadisticas_noticias")},
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
