from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from django.http import JsonResponse, FileResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.storage import default_storage
import datetime
import os

from usuarios.models import PerfilUsuario
from academico.models import (
    Asignatura, Curso, InscripcionCurso, Calificacion, 
    Asistencia, HorarioClases, RecursoAcademico
)
from .forms import SeleccionCursoAsignaturaForm, CalificacionForm
from documentos.models import ComunicadoPadres

@login_required
def panel_profesor(request):
    """Redirecciona al panel principal consolidado"""
    return redirect('usuarios:panel')

@login_required
def mis_estudiantes_profesor(request):
    """Lista todos los estudiantes del profesor"""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('usuarios:panel')
    
    cursos_profesor = Curso.objects.filter(
        Q(profesor_jefe=user) | Q(horario__profesor=user)
    ).distinct()
    
    curso_seleccionado = request.GET.get('curso', '')
    busqueda = request.GET.get('busqueda', '').strip()
    
    estudiantes_query = InscripcionCurso.objects.filter(
        curso__in=cursos_profesor
    ).select_related('estudiante', 'estudiante__perfil', 'curso')
    
    if curso_seleccionado:
        estudiantes_query = estudiantes_query.filter(curso_id=curso_seleccionado)
    
    if busqueda:
        estudiantes_query = estudiantes_query.filter(
            Q(estudiante__first_name__icontains=busqueda) |
            Q(estudiante__last_name__icontains=busqueda) |
            Q(estudiante__perfil__rut__icontains=busqueda) |
            Q(estudiante__username__icontains=busqueda)
        )
    
    paginator = Paginator(estudiantes_query, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    estudiantes_ids = [inscripcion.estudiante_id for inscripcion in page_obj.object_list]
    perfiles_estudiantes = PerfilUsuario.objects.filter(user_id__in=estudiantes_ids).in_bulk(field_name='user_id')
    
    # Logic for curso is_selected and Subject Annotation
    cursos_list = []
    target_curso_id = int(curso_seleccionado) if curso_seleccionado.isdigit() else None
    
    # Importar HorarioClases localmente para evitar dependencias circulares si es necesario, O asegúrate que está importado arriba.
    # Check imports later. For now assume it is available or use apps.get_model if unsure, but better to check imports.
    # Actually, let's just assume simple access first.
    from .models import HorarioClases 

    for c in cursos_profesor:
        c.is_selected = (c.id == target_curso_id)
        
        # Obtener asignaturas que el profesor dicta en este curso
        asignaturas = HorarioClases.objects.filter(
            curso=c, 
            profesor=user
        ).values_list('asignatura__nombre', flat=True).distinct()
        
        subjects_str = ", ".join(asignaturas)
        
        # Agregar etiqueta si es Profesor Jefe
        if c.profesor_jefe == user:
            if subjects_str:
                subjects_str += ", Jefatura"
            else:
                subjects_str = "Jefatura"
                
        c.asignaturas_display = subjects_str
        cursos_list.append(c)

    context = {
        'page_obj': page_obj,
        'cursos_profesor': cursos_list,
        'curso_seleccionado': curso_seleccionado,
        'busqueda': busqueda,
        'perfiles_estudiantes': perfiles_estudiantes,
    }
    
    return render(request, 'academico/profesor_mis_estudiantes.html', context)

@login_required
def lista_calificaciones_profesor(request):
    """Lista estudiantes para calificar"""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('usuarios:panel')
    
    cursos_profesor = Curso.objects.filter(
        Q(profesor_jefe=user) | Q(horario__profesor=user)
    ).distinct()
    
    curso_seleccionado = request.GET.get('curso', '')
    busqueda = request.GET.get('busqueda', '').strip()
    
    estudiantes_query = InscripcionCurso.objects.filter(
        curso__in=cursos_profesor
    ).select_related('estudiante', 'estudiante__perfil', 'curso')
    
    if curso_seleccionado:
        estudiantes_query = estudiantes_query.filter(curso_id=curso_seleccionado)
    
    if busqueda:
        estudiantes_query = estudiantes_query.filter(
            Q(estudiante__first_name__icontains=busqueda) |
            Q(estudiante__last_name__icontains=busqueda) |
            Q(estudiante__perfil__rut__icontains=busqueda) |
            Q(estudiante__username__icontains=busqueda)
        )
    
    paginator = Paginator(estudiantes_query, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    estudiantes_ids = [inscripcion.estudiante_id for inscripcion in page_obj.object_list]
    perfiles_estudiantes = PerfilUsuario.objects.filter(user_id__in=estudiantes_ids).in_bulk(field_name='user_id')
    
    # Logic for curso is_selected (reuse var name for template compatibility or new one)
    # The view shares the template, so we must use the same structure
    cursos_list = []
    target_curso_id = int(curso_seleccionado) if curso_seleccionado.isdigit() else None
    
    for c in cursos_profesor:
        c.is_selected = (c.id == target_curso_id)
        cursos_list.append(c)
    
    context = {
        'page_obj': page_obj,
        'cursos_profesor': cursos_list,
        'curso_seleccionado': curso_seleccionado,
        'busqueda': busqueda,
        'perfiles_estudiantes': perfiles_estudiantes,
        'modo_calificaciones': True,
    }
    
    return render(request, 'academico/profesor_mis_estudiantes.html', context)

import logging

logger = logging.getLogger(__name__)

# Configuración de evaluaciones
NUMERO_EVALUACIONES = 10  # Aumentado de 4 a 10

@login_required
def gestionar_calificaciones(request, estudiante_id):
    """Gestionar calificaciones de un estudiante específico"""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('usuarios:panel')
    
    estudiante = get_object_or_404(
        User.objects.select_related('perfil'),
        id=estudiante_id
    )
    
    cursos_profesor = Curso.objects.filter(
        Q(profesor_jefe=user) | Q(horario__profesor=user)
    ).distinct()
    inscripcion = InscripcionCurso.objects.filter(
        estudiante=estudiante,
        curso__in=cursos_profesor
    ).select_related('curso').first()
    
    if not inscripcion:
        messages.error(request, 'Este estudiante no está en ninguno de tus cursos.')
        return redirect('academico:mis_estudiantes_profesor')
    
    asignaturas_profesor = Asignatura.objects.filter(
        horarioclases__profesor=user,
        horarioclases__curso=inscripcion.curso
    ).distinct()
    
    if request.method == 'POST':
        try:
            for asignatura in asignaturas_profesor:
                for i in range(1, NUMERO_EVALUACIONES + 1):
                    campo_nota = f'nota_{asignatura.id}_{i}'
                    campo_desc = f'desc_{asignatura.id}_{i}'
                    
                    if campo_nota in request.POST:
                        nota_str = request.POST.get(campo_nota, '').strip()
                        descripcion = request.POST.get(campo_desc, f'Evaluación {i}')
                        
                        if nota_str:
                            try:
                                # Reemplazar coma por punto para soportar formato local
                                nota_str = nota_str.replace(',', '.')
                                nota = float(nota_str)
                                if 1.0 <= nota <= 7.0:
                                    Calificacion.objects.update_or_create(
                                        estudiante=estudiante,
                                        asignatura=asignatura,
                                        curso=inscripcion.curso,
                                        numero_evaluacion=i,
                                        defaults={
                                            'nota': nota,
                                            'descripcion': descripcion,
                                            'fecha_evaluacion': datetime.date.today(),
                                            'profesor': user,
                                            'tipo_evaluacion': 'nota',
                                            'semestre': '1',
                                        }
                                    )
                                else:
                                    messages.error(request, f'⚠️ Nota fuera de rango en {asignatura.nombre} - Evaluación {i}: {nota}. Las notas deben estar entre 1.0 y 7.0')
                            except ValueError:
                                messages.warning(request, f'Nota inválida para {asignatura.nombre} - Evaluación {i}. Solo se permiten números.')
            
            # --- LOGGING ---
            try:
                from administrativo.services import LiceoOSService
                LiceoOSService.registrar_evento(
                    usuario=request.user,
                    tipo_accion='nota',
                    descripcion=f"Actualizó calificaciones de {estudiante}",
                    detalles=f"Curso: {inscripcion.curso}, Asignaturas: {[a.nombre for a in asignaturas_profesor]}",
                    request=request
                )
            except Exception:
                pass
            # ----------------

            messages.success(request, 'Calificaciones actualizadas exitosamente.')
            return redirect('academico:gestionar_calificaciones', estudiante_id=estudiante_id)
            
        except Exception as e:
            logger.error(f"Error al actualizar calificaciones: {str(e)}")
            messages.error(request, f'Error al actualizar calificaciones: {str(e)}')
    
    calificaciones = Calificacion.objects.filter(
        estudiante=estudiante,
        asignatura__in=asignaturas_profesor,
        curso=inscripcion.curso
    ).select_related('asignatura').order_by('asignatura__nombre', 'numero_evaluacion')
    
    calificaciones_dict = {}
    for cal in calificaciones:
        calificaciones_dict.setdefault(cal.asignatura.id, []).append(cal)
    
    perfil_estudiante = PerfilUsuario.objects.filter(user=estudiante).first()
    
    context = {
        'estudiante': estudiante,
        'inscripcion': inscripcion,
        'asignaturas_profesor': asignaturas_profesor,
        'calificaciones_dict': calificaciones_dict,
        'perfil_estudiante': perfil_estudiante,
        'rango_evaluaciones': range(1, NUMERO_EVALUACIONES + 1),
        'numero_evaluaciones': NUMERO_EVALUACIONES,
    }
    
    return render(request, 'academico/profesor_gestionar_calificaciones.html', context)

@login_required
def enviar_correos(request):
    """Enviar correos a estudiantes o apoderados"""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('usuarios:panel')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            destinatarios = request.POST.getlist('destinatarios')
            asunto = request.POST.get('asunto', '').strip()
            mensaje = request.POST.get('mensaje', '').strip()
            incluir_apoderados = request.POST.get('incluir_apoderados') == 'on'
            
            if not asunto or not mensaje:
                messages.error(request, 'Asunto y mensaje son obligatorios.')
                return redirect('academico:enviar_correos')
            
            # Obtener estudiantes seleccionados
            estudiantes_seleccionados = User.objects.filter(
                id__in=destinatarios,
                perfil__tipo_usuario='estudiante'
            )
            
            correos_enviados = 0
            correos_fallidos = 0
            
            for estudiante in estudiantes_seleccionados:
                try:
                    # Enviar correo al estudiante
                    send_mail(
                        asunto,
                        mensaje,
                        settings.EMAIL_HOST_USER or 'liceo@liceo.cl',
                        [estudiante.email],
                        fail_silently=False,
                    )
                    
                    # Si se incluyen apoderados, buscar información
                    if incluir_apoderados:
                        # Aquí podrías buscar el apoderado del estudiante
                        # Por simplicidad, usamos un correo genérico
                        pass
                    
                    correos_enviados += 1
                    
                except Exception as e:
                    correos_fallidos += 1
                    logger.error(f"Error enviando correo a {estudiante.email}: {e}")
            
            # Mensaje de resultado
            if correos_enviados > 0:
                # --- LOGGING ---
                try:
                    from administrativo.services import LiceoOSService
                    LiceoOSService.registrar_evento(
                        usuario=request.user,
                        tipo_accion='otro',
                        descripcion=f"Envió {correos_enviados} correos a estudiantes",
                        detalles=f"Asunto: {asunto}",
                        request=request
                    )
                except Exception:
                    pass
                # ----------------
                messages.success(request, f'Correos enviados exitosamente: {correos_enviados}')
            if correos_fallidos > 0:
                messages.warning(request, f'Correos fallidos: {correos_fallidos}')
            
            return redirect('academico:enviar_correos')
            
        except Exception as e:
            messages.error(request, f'Error al enviar correos: {str(e)}')
    
    # Obtener cursos del profesor para filtrar estudiantes
    cursos_profesor = Curso.objects.filter(
        Q(profesor_jefe=user) | Q(horario__profesor=user)
    ).distinct()
    
    # Obtener estudiantes de los cursos del profesor
    estudiantes = User.objects.filter(
        perfil__tipo_usuario='estudiante',
        cursos_inscrito__curso__in=cursos_profesor
    ).select_related('perfil').distinct().order_by('first_name', 'last_name')
    estudiantes_ids = list(estudiantes.values_list('id', flat=True))
    perfiles_estudiantes = PerfilUsuario.objects.filter(user_id__in=estudiantes_ids).in_bulk(field_name='user_id')
    
    context = {
        'estudiantes': estudiantes,
        'cursos_profesor': cursos_profesor,
        'perfiles_estudiantes': perfiles_estudiantes,
    }
    
    return render(request, 'academico/profesor_enviar_correos.html', context)

@login_required
def registro_asistencias(request, curso_id):
    """Registrar asistencias para un curso"""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('usuarios:panel')
    
    # Obtener curso (Profesor Jefe O Profesor de Asignatura)
    curso = Curso.objects.filter(
        Q(pk=curso_id) & (Q(profesor_jefe=user) | Q(horario__profesor=user))
    ).distinct().first()
    
    if not curso:
        messages.error(request, 'No tienes permisos para pasar asistencia en este curso.')
        return redirect('usuarios:panel')
    
    if request.method == 'POST':
        try:
            fecha_asistencia = request.POST.get('fecha_asistencia')
            observacion_general = request.POST.get('observaciones', '')
            
            # Obtener estudiantes del curso
            estudiantes = User.objects.filter(
                perfil__tipo_usuario='estudiante',
                cursos_inscrito__curso=curso
            )
            
            estudiantes_procesados = 0
            
            for estudiante in estudiantes:
                campo_estado = f'estado_{estudiante.id}'
                campo_obs = f'observaciones_{estudiante.id}'
                
                if campo_estado in request.POST:
                    estado = request.POST.get(campo_estado)
                    obs_individual = request.POST.get(campo_obs, '')
                    
                    # Crear o actualizar asistencia
                    Asistencia.objects.update_or_create(
                        estudiante=estudiante,
                        curso=curso,
                        fecha=fecha_asistencia,
                        defaults={
                            'estado': estado,
                            'observacion': obs_individual or observacion_general,
                            'registrado_por': user
                        }
                    )
                    estudiantes_procesados += 1
            
            messages.success(request, f'Asistencia registrada para {estudiantes_procesados} estudiantes.')
            return redirect('academico:registro_asistencias', curso_id=curso_id)
            
        except Exception as e:
            messages.error(request, f'Error al registrar asistencia: {str(e)}')
    
    # Obtener estudiantes del curso
    estudiantes = User.objects.filter(
        perfil__tipo_usuario='estudiante',
        cursos_inscrito__curso=curso
    ).select_related('perfil').order_by('first_name', 'last_name')
    
    # Obtener últimas asistencias (opcional)
    fecha_hoy = datetime.date.today()
    asistencias_hoy = Asistencia.objects.filter(
        curso=curso,
        fecha=fecha_hoy
    )
    
    context = {
        'curso': curso,
        'estudiantes': estudiantes,
        'asistencias_hoy': asistencias_hoy,
        'fecha_hoy': fecha_hoy,
    }
    
    return render(request, 'academico/profesor_registro_asistencias.html', context)

@login_required
def estadisticas_profesor(request):
    """Ver estadísticas como profesor"""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('usuarios:panel')
    
    # Cursos donde el profesor enseña o es jefe
    cursos_profesor = Curso.objects.filter(
        Q(profesor_jefe=user) | Q(horario__profesor=user)
    ).distinct()
    
    # Total de estudiantes únicos en esos cursos
    total_estudiantes = InscripcionCurso.objects.filter(
        curso__in=cursos_profesor
    ).values('estudiante').distinct().count()
    
    # Asignaturas que dicta el profesor
    asignaturas_profesor = Asignatura.objects.filter(
        horarioclases__profesor=user
    ).distinct()
    
    # Todas las calificaciones puestas por este profesor
    calificaciones = Calificacion.objects.filter(
        profesor=user
    )
    
    # Promedio general de las notas puestas por el profesor
    promedio_general = calificaciones.aggregate(
        promedio=Avg('nota')
    )['promedio'] or 0
    
    # Estudiantes con bajo rendimiento (promedio < 4.0) SOLO en asignaturas de este profesor
    # Optimizacion: Calcular promedios en la DB y filtrar
    estudiantes_bajo_rendimiento = Calificacion.objects.filter(
        profesor=user
    ).values(
        'estudiante__id', 
        'estudiante__first_name', 
        'estudiante__last_name', 
        'estudiante__username'
    ).annotate(
        promedio=Avg('nota')
    ).filter(
        promedio__lt=4.0
    ).order_by('promedio')[:10]
    
    # Formatear lista para el template (manteniendo compatibilidad)
    lista_bajo_rendimiento = []
    for item in estudiantes_bajo_rendimiento:
        # Creamos un objeto dummy o diccionario que el template pueda leer
        # El template espera (estudiante_obj, promedio)
        estudiante_dummy = type('User', (), {
            'first_name': item['estudiante__first_name'],
            'last_name': item['estudiante__last_name'],
            'username': item['estudiante__username'],
            'id': item['estudiante__id'],
            'get_full_name': lambda self: f"{self.first_name} {self.last_name}".strip() or self.username
        })()

        lista_bajo_rendimiento.append((estudiante_dummy, item['promedio']))
    
    context = {
        'total_estudiantes': total_estudiantes,
        'total_cursos': cursos_profesor.count(),
        'total_asignaturas': asignaturas_profesor.count(),
        'promedio_general': round(promedio_general, 2),
        'total_calificaciones': calificaciones.count(),
        'estudiantes_bajo_rendimiento': lista_bajo_rendimiento,
    }
    
    return render(request, 'academico/profesor_estadisticas.html', context)

# --- RECURSOS ACADÉMICOS ---

@login_required
def gestionar_recursos(request):
    """Lista y gestiona recursos académicos"""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    if not perfil or perfil.tipo_usuario != 'profesor':
        messages.error(request, 'No tienes permisos.')
        return redirect('usuarios:panel')

    # Cursos del profesor
    cursos_profesor = Curso.objects.filter(
        Q(profesor_jefe=user) | Q(horario__profesor=user)
    ).distinct()
    
    recursos = RecursoAcademico.objects.filter(profesor=user).select_related('curso', 'asignatura')
    
    context = {
        'cursos': cursos_profesor,
        'recursos': recursos
    }
    return render(request, 'academico/recursos/gestionar_recursos.html', context)

@login_required
def subir_recurso(request):
    """Procesa la subida de recursos"""
    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo')
            curso_id = request.POST.get('curso')
            archivo = request.FILES.get('archivo')
            
            # Crear recurso
            RecursoAcademico.objects.create(
                titulo=titulo,
                curso_id=curso_id,
                archivo=archivo,
                profesor=request.user
            )
            # --- LOGGING ---
            try:
                from administrativo.services import LiceoOSService
                LiceoOSService.registrar_evento(
                    usuario=request.user,
                    tipo_accion='recurso',
                    descripcion=f"Subió material: {titulo}",
                    detalles=f"Curso ID: {curso_id}",
                    request=request
                )
            except Exception:
                pass
            # ----------------
            messages.success(request, 'Recurso subido exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al subir: {str(e)}')
            
    return redirect('academico:gestionar_recursos')

@login_required
def eliminar_recurso(request, pk):
    """Elimina un recurso propio"""
    recurso = get_object_or_404(RecursoAcademico, pk=pk, profesor=request.user)
    recurso.delete()
    messages.success(request, 'Recurso eliminado.')
    return redirect('academico:gestionar_recursos')

@login_required
def descargar_recurso(request, pk):
    """Descarga segura de recursos"""
    recurso = get_object_or_404(RecursoAcademico, pk=pk)
    
    # Validar permisos: es el profe dueño O el estudiante del curso
    user = request.user
    es_profe_dueno = (recurso.profesor == user)
    es_estudiante_curso = InscripcionCurso.objects.filter(estudiante=user, curso=recurso.curso).exists()
    
    if not (es_profe_dueno or es_estudiante_curso or user.is_staff):
         messages.error(request, 'No tienes permiso para descargar este recurso.')
         return redirect('usuarios:panel')

    try:
        return FileResponse(open(recurso.archivo.path, 'rb'), as_attachment=True)
    except FileNotFoundError:
         messages.error(request, 'El archivo no se encuentra en el servidor.')
         return redirect('usuarios:panel')


