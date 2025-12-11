from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count, Max
from datetime import datetime, timedelta
from django.contrib import messages
from django.http import HttpResponse

from .models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia
from comunicacion.models import Noticia
from core.models import ConfiguracionAcademica
from .utils import render_to_pdf, generar_certificado_alumno_regular, generar_certificado_notas
from django.utils import timezone
from .services import AcademicoService
import secrets
import mimetypes
from django.http import FileResponse

@login_required
def dashboard_academico(request):
    """Dashboard académico personalizado por tipo de usuario"""
    user = request.user
    
    # Obtener perfil del usuario
    try:
        perfil = user.perfil
        tipo_usuario = perfil.tipo_usuario
    except Exception:
        tipo_usuario = 'estudiante'
        perfil = None

    # Datos comunes
    context = {
        'titulo_dashboard': f'Dashboard Académico - {perfil.get_tipo_usuario_display() if perfil else "Usuario"}',
        'perfil': perfil,
        'user': user
    }

    if tipo_usuario in ['estudiante', 'apoderado']:
        return dashboard_estudiante(request, context)
    elif tipo_usuario == 'profesor':
        return dashboard_profesor(request, context)
    else:
        return dashboard_administrativo(request, context)

@login_required
def dashboard_estudiante(request, context):
    """Dashboard específico para estudiantes"""
    user = request.user
    
    # Delegar lógica al servicio
    dashboard_data = AcademicoService.get_estudiante_dashboard_data(user)
    
    if not dashboard_data:
        messages.warning(request, "No estás inscrito en ningún curso activo este año.")
        return render(request, 'academico/estudiante_dashboard.html', context)
    
    context.update(dashboard_data)
    
    return render(request, 'academico/estudiante_dashboard.html', context)

@login_required
def descargar_informe_notas(request):
    """Genera un informe detallado de notas por asignatura"""
    if not hasattr(request.user, 'perfil') or request.user.perfil.tipo_usuario != 'estudiante':
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('home')
        
    estudiante = request.user
    anio_actual = ConfiguracionAcademica.get_actual().año_actual
    
    # 1. Obtener cursos activos
    inscripciones = InscripcionCurso.objects.filter(
        estudiante=estudiante,
        año=anio_actual,
        estado='activo'
    ).select_related('curso')

    datos_informe = []
    promedio_global_acumulado = 0
    cantidad_asignaturas_global = 0

    for inscripcion in inscripciones:
        curso = inscripcion.curso
        # Obtener asignaturas del curso (base horarios)
        ids_asignaturas = HorarioClases.objects.filter(curso=curso).values_list('asignatura_id', flat=True).distinct()
        asignaturas = Asignatura.objects.filter(id__in=ids_asignaturas).order_by('nombre')
        
        lista_asignaturas = []
        promedio_curso_acumulado = 0
        cantidad_asignaturas_curso = 0
        
        for asignatura in asignaturas:
            # Calcular promedio asignatura
            notas = Calificacion.objects.filter(
                estudiante=estudiante,
                asignatura=asignatura,
                curso=curso,
                fecha_evaluacion__year=anio_actual
            )
            
            promedio_asignatura = notas.aggregate(Avg('nota'))['nota__avg']
            
            if promedio_asignatura:
                promedio_final = round(promedio_asignatura, 1)
                promedio_curso_acumulado += promedio_final
                cantidad_asignaturas_curso += 1
            else:
                promedio_final = None
                
            lista_asignaturas.append({
                'nombre': asignatura.nombre,
                'promedio': promedio_final,
                'cantidad_notas': notas.count()
            })
            
        promedio_curso = round(promedio_curso_acumulado / cantidad_asignaturas_curso, 1) if cantidad_asignaturas_curso > 0 else None
        
        if promedio_curso:
            promedio_global_acumulado += promedio_curso
            cantidad_asignaturas_global += 1
            
        datos_informe.append({
            'curso': curso,
            'asignaturas': lista_asignaturas,
            'promedio_curso': promedio_curso
        })
        
    promedio_general = round(promedio_global_acumulado / cantidad_asignaturas_global, 1) if cantidad_asignaturas_global > 0 else None

    context = {
        'estudiante': estudiante,
        'datos_informe': datos_informe,
        'promedio_general': promedio_general,
        'fecha': timezone.now(),
        'anio': anio_actual
    }
    
    pdf = render_to_pdf('academico/pdf/informe_notas.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Informe_Notas_{estudiante.username}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
        
    return HttpResponse("Error generando PDF", status=400)

@login_required
def descargar_certificado_alumno_regular(request):
    """Genera un certificado de alumno regular en PDF"""
    if not hasattr(request.user, 'perfil') or request.user.perfil.tipo_usuario != 'estudiante':
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('home')
        
    estudiante = request.user
    anio_actual = ConfiguracionAcademica.get_actual().año_actual
    
    # Obtener inscripción vigente
    inscripcion = InscripcionCurso.objects.filter(
        estudiante=estudiante,
        año=anio_actual,
        estado='activo'
    ).first()
    
    if not inscripcion:
        messages.error(request, "No estás matriculado como alumno regular para el año en curso.")
        return redirect('academico:dashboard_academico')
        
    context = {
        'estudiante': estudiante,
        'curso': inscripcion.curso,
        'anio': anio_actual,
        'fecha': timezone.now(),
        'numero_matricula': f"{anio_actual}-{estudiante.id}", # Simulación de nro matrícula
    }
    
    pdf = render_to_pdf('academico/pdf/certificado_regular.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Certificado_Regular_{estudiante.username}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
        
    return HttpResponse("Error generando Certificado", status=400)

@login_required
def dashboard_profesor(request, context):
    """Dashboard específico para profesores"""
    user = request.user
    
    # Obtener cursos donde el profesor dicta clases
    horarios = HorarioClases.objects.filter(profesor=user).select_related('curso', 'asignatura')
    cursos_ids = horarios.values_list('curso_id', flat=True).distinct()
    
    # Obtener cursos con conteo de alumnos activos
    cursos_unicos = Curso.objects.filter(id__in=cursos_ids).annotate(
        cantidad_alumnos_real=Count('estudiantes', filter=Q(estudiantes__estado='activo'))
    )
    
    # Calcular total de alumnos
    total_alumnos_real = sum(c.cantidad_alumnos_real for c in cursos_unicos)

    # Optimización N+1: Obtener la última evaluación de CADA curso en una sola query (o pocas)
    # Estrategia: Obtener todas las evaluaciones recientes del profesor agrupadas por curso
    # Como Django no soporta 'distinct on' en todas las DBs, traemos las últimas por fecha
    
    evaluaciones_recientes = Calificacion.objects.filter(
        profesor=user
    ).select_related('asignatura', 'curso').order_by('-fecha_evaluacion')[:50] # Limitamos para no traer todo el historial
    
    # Mapear curso_id -> ultima_evaluacion
    mapa_ultima_eval = {}
    for eval in evaluaciones_recientes:
        if eval.curso_id not in mapa_ultima_eval:
            mapa_ultima_eval[eval.curso_id] = eval
            
    # Asignar datos a los cursos
    for curso in cursos_unicos:
        ultima_eval = mapa_ultima_eval.get(curso.id)
        
        if ultima_eval:
            # Calcular promedio de esa evaluación específica (esto sigue siendo una query por curso, pero es ligera)
            # Podríamos optimizarlo más pre-calculando, pero es aceptable para <10 cursos
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

    # Asignaturas asignadas
    asignaturas_ids = horarios.values_list('asignatura_id', flat=True).distinct()
    asignaturas_unicas = Asignatura.objects.filter(id__in=asignaturas_ids)
    
    # Horario de hoy
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dia_actual = dias_semana[datetime.now().weekday()]
    horario_hoy = HorarioClases.objects.filter(profesor=user, dia=dia_actual).select_related('curso', 'asignatura')
    
    # Calificaciones recientes (para la tabla)
    calificaciones_recientes = evaluaciones_recientes[:10]
    
    # Consejo de Profesores
    consejos = Noticia.objects.filter(categoria='consejo', es_publica=True).order_by('-creado')[:5]

    context.update({
        'cursos_unicos': cursos_unicos,
        'asignaturas_unicas': asignaturas_unicas,
        'horario_hoy': horario_hoy,
        'calificaciones_recientes': calificaciones_recientes,
        'total_alumnos_real': total_alumnos_real,
        'consejos': consejos
    })
    
    return render(request, 'academico/profesor_dashboard.html', context)

@login_required
def tomar_asistencia(request, curso_id):
    """Vista rápida para tomar asistencia"""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    # Verificar permisos
    if not (request.user.is_staff or request.user.perfil.tipo_usuario == 'profesor'):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('academico:dashboard_academico')
        
    curso = get_object_or_404(Curso, id=curso_id)
    estudiantes = User.objects.filter(
        cursos_inscrito__curso=curso,
        cursos_inscrito__estado='activo'
    ).order_by('last_name', 'first_name')
    
    if request.method == 'POST':
        fecha_hoy = datetime.now().date()
        
        # Verificar si ya se tomó asistencia hoy
        if Asistencia.objects.filter(curso=curso, fecha=fecha_hoy).exists():
            messages.warning(request, f"Ya existe un registro de asistencia para el curso {curso} con fecha de hoy.")
            # Opcional: Redirigir o permitir sobrescribir. Por seguridad, permitimos sobrescribir/actualizar.
        
        registros_creados = 0
        for estudiante in estudiantes:
            estado = request.POST.get(f'estado_{estudiante.id}')
            observacion = request.POST.get(f'obs_{estudiante.id}', '')
            
            if estado:
                Asistencia.objects.update_or_create(
                    estudiante=estudiante,
                    curso=curso,
                    fecha=fecha_hoy,
                    defaults={
                        'estado': estado,
                        'observacion': observacion,
                        'registrado_por': request.user
                    }
                )
                registros_creados += 1
        
                registros_creados += 1
        
        # --- LOGGING ---
        try:
            from administrativo.services import LiceoOSService
            LiceoOSService.registrar_evento(
                usuario=request.user,
                tipo_accion='asistencia',
                descripcion=f"Pasó asistencia en {curso}",
                detalles=f"Registros procesados: {registros_creados}",
                request=request
            )
        except Exception:
            pass
        # ----------------
        
        messages.success(request, f"Se registró la asistencia de {registros_creados} estudiantes correctamente.")
        return redirect('academico:dashboard_academico')
        
    return render(request, 'academico/tomar_asistencia.html', {
        'curso': curso,
        'estudiantes': estudiantes,
        'fecha_hoy': datetime.now()
    })

@login_required
def dashboard_administrativo(request, context):
    """Dashboard específico para administrativos"""
    user = request.user
    
    # Estadísticas generales
    total_estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante').count()
    total_profesores = User.objects.filter(perfil__tipo_usuario='profesor').count()
    total_cursos = Curso.objects.filter(activo=True).count()
    total_asignaturas = Asignatura.objects.filter(activa=True).count()
    
    # Calificaciones por nivel
    calificaciones_por_curso = Calificacion.objects.values('curso__nivel').annotate(
        promedio=Avg('nota')
    ).order_by('curso__nivel')
    
    context.update({
        'total_estudiantes': total_estudiantes,
        'total_profesores': total_profesores,
        'total_cursos': total_cursos,
        'total_asignaturas': total_asignaturas,
        'calificaciones_por_curso': calificaciones_por_curso
    })
    
    return render(request, 'administrativo/dashboard.html', context)

@login_required
def mis_calificaciones(request):
    """Vista para ver calificaciones del estudiante"""
    user = request.user
    
    # Filtros
    semestre_actual = request.GET.get('semestre', '')
    calificaciones = Calificacion.objects.filter(estudiante=user)
    
    if semestre_actual:
        calificaciones = calificaciones.filter(semestre=semestre_actual)
    
    calificaciones = calificaciones.order_by('-fecha_evaluacion')
    
    # Calcular promedios
    try:
        promedio_general = user.perfil.promedio_general
    except Exception:
        promedio_general = None
    
    # Promedios por semestre
    promedios_semestre = {}
    for semestre in ['1', '2']:
        promedio_sem = Calificacion.objects.filter(estudiante=user, semestre=semestre).aggregate(
            promedio=Avg('nota')
        )
        promedios_semestre[semestre] = round(promedio_sem['promedio'], 1) if promedio_sem['promedio'] else None
    
    return render(request, 'academico/mis_calificaciones.html', {
        'calificaciones': calificaciones,
        'promedio_general': promedio_general,
        'promedios': promedios_semestre,
        'semestre_actual': semestre_actual
    })

@login_required
def mi_horario(request):
    """Vista para ver el horario del estudiante"""
    user = request.user
    
    # Obtener cursos del estudiante
    cursos = InscripcionCurso.objects.filter(estudiante=user, estado='activo')
    curso_ids = cursos.values_list('curso_id', flat=True)
    
    # Obtener todo el horario en una sola consulta
    horario_completo = HorarioClases.objects.filter(
        curso__id__in=curso_ids
    ).select_related('asignatura', 'profesor').order_by('hora')
    
    # Agrupar por día en memoria
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    horario_por_dia = {dia: [] for dia in dias_semana}
    
    for clase in horario_completo:
        if clase.dia in horario_por_dia:
            horario_por_dia[clase.dia].append(clase)
    
    return render(request, 'academico/mi_horario.html', {
        'horario_por_dia': horario_por_dia,
        'dias_semana': dias_semana
    })

@login_required
def mis_asistencias(request):
    """Vista para ver las asistencias del estudiante"""
    user = request.user
    
    
    # Filtros
    mes_seleccionado = request.GET.get('mes', '')
    estado_seleccionado = request.GET.get('estado', '')
    
    asistencias = Asistencia.objects.filter(estudiante=user)
    
    if mes_seleccionado:
        try:
            fecha_mes = datetime.strptime(mes_seleccionado + '-01', '%Y-%m-%d')
            asistencias = asistencias.filter(
                fecha__year=fecha_mes.year,
                fecha__month=fecha_mes.month
            )
        except ValueError:
            pass
            
    if estado_seleccionado:
        asistencias = asistencias.filter(estado=estado_seleccionado)
    
    asistencias = asistencias.order_by('-fecha')
    
    # Estados para filtro
    estados_filtro = []
    estados_choices = [
        ('presente', 'Presente'), 
        ('ausente', 'Ausente'), 
        ('tardanza', 'Tardanza'), 
        ('justificado', 'Justificado')
    ]
    
    for valor, texto in estados_choices:
        estados_filtro.append({
            'valor': valor,
            'texto': texto,
            'is_selected': (valor == estado_seleccionado)
        })

    # Estadísticas (Calculadas sobre el total del estudiante, no sobre el filtro, para dar contexto)
    total_asistencias = Asistencia.objects.filter(estudiante=user)
    estadisticas = {
        'presentes': total_asistencias.filter(estado='presente').count(),
        'ausentes': total_asistencias.filter(estado='ausente').count(),
        'tardanzas': total_asistencias.filter(estado='tardanza').count(),
        'justificadas': total_asistencias.filter(estado='justificado').count()
    }
    
    return render(request, 'academico/mis_asistencias.html', {
        'asistencias': asistencias,
        'estadisticas': estadisticas,
        'mes_seleccionado': mes_seleccionado,
        'estados_filtro': estados_filtro
    })

@login_required
def mis_cursos(request):
    """Vista para ver cursos del estudiante"""
    user = request.user
    cursos = InscripcionCurso.objects.filter(estudiante=user, estado='activo')
    return render(request, 'academico/mis_cursos.html', {'cursos': cursos})

@login_required
def mis_asignaturas(request):
    """Vista para ver asignaturas del estudiante"""
    user = request.user
    cursos = InscripcionCurso.objects.filter(estudiante=user, estado='activo')
    asignaturas = Asignatura.objects.filter(
        horario__curso__in=cursos.values('curso')
    ).distinct()
    
    asignaturas_activas_count = asignaturas.filter(activa=True).count()
    
    return render(request, 'academico/mis_asignaturas.html', {
        'asignaturas': asignaturas,
        'asignaturas_activas_count': asignaturas_activas_count
    })

@login_required
def registrar_notas_curso(request, curso_id):
    """Vista para ingreso masivo de notas"""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    # Verificar permisos (solo staff/profesores)
    if not (request.user.is_staff or request.user.perfil.tipo_usuario == 'profesor'):
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('academico:dashboard_academico')
        
    curso = get_object_or_404(Curso, id=curso_id)
    
    # Validación estricta: Si es profesor, DEBE tener clases en este curso
    if not request.user.is_staff:
        tiene_clases = HorarioClases.objects.filter(curso=curso, profesor=request.user).exists()
        if not tiene_clases:
            messages.error(request, "No tienes asignaturas en este curso.")
            return redirect('academico:dashboard_academico')
    
    # Obtener estudiantes activos
    estudiantes = User.objects.filter(
        cursos_inscrito__curso=curso,
        cursos_inscrito__estado='activo'
    ).order_by('last_name', 'first_name')
    
    # Obtener asignaturas del curso (basado en horario)
    asignaturas_ids = HorarioClases.objects.filter(curso=curso).values_list('asignatura', flat=True).distinct()
    asignaturas = Asignatura.objects.filter(id__in=asignaturas_ids)
    
    # Si es profesor, filtrar solo sus asignaturas
    if not request.user.is_staff:
        mis_asignaturas_ids = HorarioClases.objects.filter(
            curso=curso, 
            profesor=request.user
        ).values_list('asignatura', flat=True).distinct()
        asignaturas = asignaturas.filter(id__in=mis_asignaturas_ids)

    if request.method == 'POST':
        asignatura_id = request.POST.get('asignatura')
        tipo_evaluacion = request.POST.get('tipo_evaluacion')
        numero_evaluacion = request.POST.get('numero_evaluacion')
        fecha_evaluacion = request.POST.get('fecha_evaluacion')
        descripcion_general = request.POST.get('descripcion', '')
        
        if not all([asignatura_id, tipo_evaluacion, numero_evaluacion, fecha_evaluacion]):
            messages.error(request, "Todos los campos de configuración son obligatorios.")
        else:
            asignatura = get_object_or_404(Asignatura, id=asignatura_id)
            notas_guardadas = 0
            
            for estudiante in estudiantes:
                nota_valor = request.POST.get(f'nota_{estudiante.id}')
                obs_individual = request.POST.get(f'obs_{estudiante.id}', '')
                
                if nota_valor:
                    try:
                        # Crear o actualizar calificación
                        Calificacion.objects.update_or_create(
                            estudiante=estudiante,
                            asignatura=asignatura,
                            curso=curso,
                            numero_evaluacion=numero_evaluacion,
                            defaults={
                                'profesor': request.user,
                                'tipo_evaluacion': tipo_evaluacion,
                                'semestre': ConfiguracionAcademica.get_actual().semestre_actual,
                                'fecha_evaluacion': fecha_evaluacion,
                                'nota': nota_valor,
                                'descripcion': obs_individual or descripcion_general
                            }
                        )
                        notas_guardadas += 1
                    except Exception as e:
                        messages.warning(request, f"Error guardando nota para {estudiante}: {e}")
            
            if notas_guardadas > 0:
                # --- LOGGING ---
                try:
                    from administrativo.services import LiceoOSService
                    LiceoOSService.registrar_evento(
                        usuario=request.user,
                        tipo_accion='nota',
                        descripcion=f"Ingresó {notas_guardadas} notas en {asignatura.nombre} ({curso})",
                        detalles=f"Evaluación {numero_evaluacion}, Tipo: {tipo_evaluacion}",
                        request=request
                    )
                except Exception:
                    pass
                # ----------------
                
                messages.success(request, f"Se guardaron exitosamente {notas_guardadas} notas.")
                return redirect('academico:dashboard_academico')
            else:
                messages.warning(request, "No se ingresó ninguna nota.")

    return render(request, 'academico/registrar_notas_curso.html', {
        'curso': curso,
        'estudiantes': estudiantes,
        'asignaturas': asignaturas
    })

@login_required
def detalle_estudiante(request, pk):
    """
    Vista para que profesores vean el perfil de sus estudiantes.
    Restricción: Solo pueden ver estudiantes que estén inscritos en sus cursos.
    """
    estudiante = get_object_or_404(User, pk=pk)
    perfil = getattr(estudiante, 'perfil', None)
    
    # Verificar que el usuario consultado sea estudiante
    if not perfil or perfil.tipo_usuario != 'estudiante':
        messages.error(request, "El usuario consultado no es un estudiante.")
        return redirect('academico:dashboard_academico')

    # Verificar permisos del solicitante
    es_profesor = request.user.perfil.tipo_usuario == 'profesor' if hasattr(request.user, 'perfil') else False
    
    if not (request.user.is_staff or es_profesor):
        messages.error(request, "No tienes permisos para ver perfiles de estudiantes.")
        return redirect('academico:dashboard_academico')
        
    # Si es profesor, verificar que le hace clases al alumno
    if es_profesor and not request.user.is_staff:
        # Obtener cursos del profesor
        cursos_profesor = HorarioClases.objects.filter(profesor=request.user).values_list('curso_id', flat=True)
        
        # Verificar si el estudiante está en alguno de esos cursos
        es_alumno_suyo = InscripcionCurso.objects.filter(
            estudiante=estudiante,
            curso_id__in=cursos_profesor,
            estado='activo'
        ).exists()
        
        if not es_alumno_suyo:
            messages.error(request, "No tienes permiso para ver el perfil de este estudiante (no pertenece a tus cursos).")
            return redirect('academico:dashboard_academico')

    # Si pasa las validaciones, mostrar datos
    # Obtener información académica del estudiante para mostrarla en el perfil
    inscripciones = InscripcionCurso.objects.filter(estudiante=estudiante, estado='activo').select_related('curso')
    
    # Calcular asistencia y notas (resumido)
    resumen_academico = []
    anio_actual = ConfiguracionAcademica.get_actual().año_actual
    
    for inscripcion in inscripciones:
        # Promedio
        promedio = Calificacion.objects.filter(
            estudiante=estudiante, 
            curso=inscripcion.curso,
            fecha_evaluacion__year=anio_actual
        ).aggregate(Avg('nota'))['nota__avg']
        
        # Asistencia
        total_asist = Asistencia.objects.filter(
            estudiante=estudiante,
            curso=inscripcion.curso,
            fecha__year=anio_actual
        ).count()
        presentes = Asistencia.objects.filter(
            estudiante=estudiante,
            curso=inscripcion.curso,
            fecha__year=anio_actual,
            estado='presente'
        ).count()
        
        porcentaje_asistencia = (presentes / total_asist * 100) if total_asist > 0 else 0
        
        resumen_academico.append({
            'curso': inscripcion.curso,
            'promedio': round(promedio, 1) if promedio else None,
            'asistencia': round(porcentaje_asistencia, 1)
        })

    return render(request, 'academico/detalle_estudiante.html', {
        'estudiante': estudiante,
        'perfil_estudiante': perfil,
        'resumen_academico': resumen_academico
    })

@login_required
def importar_estudiantes(request):
    """Vista para importar estudiantes desde CSV/Excel"""
    if not request.user.is_staff:
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('academico:dashboard_academico')

    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        try:
            import csv
            import io
            from usuarios.models import PerfilUsuario
            
            # Detectar tipo de archivo
            if archivo.name.endswith('.csv'):
                decoded_file = archivo.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file)
            else:
                # Para Excel necesitaríamos pandas o openpyxl, por ahora solo CSV básico
                # Si el usuario sube excel, le pedimos CSV
                messages.error(request, "Por favor guarda tu Excel como CSV (delimitado por comas) e intenta nuevamente.")
                return render(request, 'academico/importar_estudiantes.html')

            count_creados = 0
            count_errores = 0
            
            for row in reader:
                try:
                    # Normalizar claves (minusculas)
                    row = {k.lower(): v for k, v in row.items()}
                    
                    rut = row.get('rut', '').strip()
                    nombres = row.get('nombres', '').strip()
                    apellidos = row.get('apellidos', '').strip()
                    email = row.get('email', '').strip()
                    curso_nombre = row.get('curso', '').strip()
                    
                    if not rut or not email:
                        continue
                        
                    # Crear usuario base
                    username = email.split('@')[0]
                    # Evitar duplicados de username
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                        
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'first_name': nombres,
                            'last_name': apellidos
                        }
                    )
                    
                    if created:
                        user.set_password(secrets.token_urlsafe(8)) # Contraseña segura
                        user.save()
                        
                        # Crear perfil
                        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
                        perfil.rut = rut
                        perfil.tipo_usuario = 'estudiante'
                        perfil.save()
                        
                        # Inscribir en curso si existe
                        if curso_nombre:
                            curso = Curso.objects.filter(nombre__iexact=curso_nombre).first()
                            if curso:
                                InscripcionCurso.objects.create(
                                    estudiante=user,
                                    curso=curso,
                                    año=ConfiguracionAcademica.get_actual().año_actual,
                                    estado='activo'
                                )
                        
                        count_creados += 1
                        
                except Exception as e:
                    # Logging error instead of print
                    count_errores += 1
            
            if count_creados > 0:
                messages.success(request, f"Se importaron {count_creados} estudiantes correctamente.")
            if count_errores > 0:
                messages.warning(request, f"Hubo {count_errores} errores al procesar algunas filas.")
                
            return redirect('usuarios:panel')

        except Exception as e:
            messages.error(request, f"Error procesando el archivo: {str(e)}")
            
    return render(request, 'academico/importar_estudiantes.html')

@login_required
def gestion_cursos(request):
    """Vista para listar cursos (Administrativo)"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    
    if not es_admin:
        messages.error(request, "No tienes permisos para gestionar cursos.")
        return redirect('home')
        
    cursos = Curso.objects.all().order_by('nivel', 'letra')
    
    if request.method == 'POST':
        nivel = request.POST.get('nivel')
        letra = request.POST.get('letra')
        if nivel and letra:
            # Simple creación, validación básica
            Curso.objects.get_or_create(nivel=nivel, letra=letra.upper())
            messages.success(request, f"Curso {nivel}°{letra} gestionado correctamente.")
    
    return render(request, 'administrativo/gestion_cursos.html', {'cursos': cursos})

# --- CERTIFICADOS ---

@login_required
def mis_certificados(request):
    """Vista principal para la descarga de certificados del alumno"""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'estudiante':
        messages.error(request, "Esta sección es solo para estudiantes.")
        return redirect('home')

    # Aquí podríamos verificar si el alumno tiene deudas, sanciones, etc.
    # Por ahora simplemente mostramos la lista.
    
    certificados_disponibles = [
        {
            'tipo': 'alumno_regular',
            'nombre': 'Certificado de Alumno Regular',
            'descripcion': 'Acredita tu condición de estudiante activo para el año en curso.',
            'icono': 'bi-person-badge',
            'color': 'primary'
        },
        {
            'tipo': 'notas',
            'nombre': 'Informe de Notas Parcial',
            'descripcion': 'Resumen de calificaciones del año lectivo actual.',
            'icono': 'bi-journal-check',
            'color': 'success'
        },
        # Más certificados...
    ]

    return render(request, 'academico/mis_certificados.html', {
        'certificados': certificados_disponibles
    })

@login_required
def descargar_certificado_pdf(request, tipo):
    """Genera y descarga el certificado solicitado"""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'estudiante':
        return HttpResponse("No autorizado", status=403)

    buffer = None
    filename = ""

    try:
        if tipo == 'alumno_regular':
            buffer = generar_certificado_alumno_regular(request.user)
            filename = f"Certificado_Alumno_Regular_{request.user.username}.pdf"
        elif tipo == 'notas':
            buffer = generar_certificado_notas(request.user)
            filename = f"Informe_Notas_{request.user.username}.pdf"
        else:
            messages.error(request, "Tipo de certificado no válido.")
            return redirect('academico:mis_certificados')

        if buffer:
            response = FileResponse(buffer, as_attachment=True, filename=filename)
            return response
        else:
            messages.error(request, "Error generando el certificado.")
            return redirect('academico:mis_certificados')

    except Exception as e:
        messages.error(request, f"Error interno: {str(e)}")
        return redirect('academico:mis_certificados')


@login_required
def gestion_asignaturas(request):
    """Vista para listar asignaturas (Administrativo)"""
    es_admin = request.user.is_staff or (
        hasattr(request.user, 'perfil') and 
        request.user.perfil.tipo_usuario in ['administrativo', 'directivo']
    )
    
    if not es_admin:
        messages.error(request, "No tienes permisos.")
        return redirect('home')
        
    asignaturas = Asignatura.objects.all().order_by('nombre')
    
    # Opcional: Procesar creación simple si es POST 
    # (Para no hacer view separada por now)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            Asignatura.objects.create(nombre=nombre)
            messages.success(request, "Asignatura creada.")
            return redirect('academico:gestion_asignaturas')
            
    return render(request, 'academico/gestion_asignaturas.html', {'asignaturas': asignaturas})

@login_required
def editar_asignatura(request, asignatura_id):
    """Editar asignatura existente"""
    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            asignatura.nombre = nombre
            asignatura.save()
            messages.success(request, "Asignatura actualizada.")
            return redirect('academico:gestion_asignaturas')
            
    return render(request, 'academico/editar_asignatura.html', {'asignatura': asignatura})

@login_required
def eliminar_asignatura(request, asignatura_id):
    """Eliminar asignatura"""
    asignatura = get_object_or_404(Asignatura, id=asignatura_id)
    # Validar si tiene uso? Por ahora borrado simple o soft delete si el modelo lo soporta
    # Asumimos borrado directo con proteccion de DB
    try:
        asignatura.delete()
        messages.success(request, "Asignatura eliminada.")
    except Exception:
        messages.error(request, "No se puede eliminar la asignatura porque está en uso.")
    return redirect('academico:gestion_asignaturas')


# --- ANOTACIONES (HOJA DE VIDA) ---
from .forms import AnotacionForm
from .models import Anotacion

@login_required
def mis_anotaciones(request):
    """Vista para estudiantes: Ver su propia hoja de vida"""
    if request.user.perfil.tipo_usuario != 'estudiante':
        messages.error(request, "Acceso no autorizado.")
        return redirect('core:home')

    anotaciones = Anotacion.objects.filter(estudiante=request.user).select_related('profesor', 'curso').order_by('-fecha')
    positivas = anotaciones.filter(tipo='positiva').count()
    negativas = anotaciones.filter(tipo='negativa').count()

    context = {
        'anotaciones': anotaciones,
        'positivas': positivas,
        'negativas': negativas,
    }
    return render(request, 'academico/anotaciones/lista_anotaciones.html', context)

@login_required
def crear_anotacion(request, estudiante_id):
    """Vista para profesores: Crear una anotación"""
    # Permitir a administrativos y directivos también
    if request.user.perfil.tipo_usuario not in ['profesor', 'administrativo', 'directivo']:
        messages.error(request, "No tienes permisos para registrar anotaciones.")
        return redirect('core:home')

    estudiante = get_object_or_404(User, id=estudiante_id, perfil__tipo_usuario='estudiante')

    if request.method == 'POST':
        form = AnotacionForm(request.POST)
        if form.is_valid():
            anotacion = form.save(commit=False)
            anotacion.estudiante = estudiante
            anotacion.profesor = request.user
            # Intentar asignar curso actual si existe inscripción
            try:
                inscripcion = InscripcionCurso.objects.filter(alumno=estudiante, activo=True).first()
                if inscripcion:
                    anotacion.curso = inscripcion.curso
            except Exception:
                pass
            
            anotacion.save()
            messages.success(request, f"Anotación registrada para {estudiante.get_full_name()}")
            # Redirigir según quién sea (Profesor o Admin)
            return redirect('academico:historial_anotaciones', estudiante_id=estudiante.id)
    else:
        form = AnotacionForm()

    return render(request, 'academico/anotaciones/form_anotacion.html', {
        'form': form,
        'estudiante': estudiante
    })

@login_required
def historial_anotaciones_estudiante(request, estudiante_id):
    """Vista para profesores y admin: Ver historial de un alumno"""
    # Validar permisos: Staff o (tiene perfil Y es profesor/admin/directivo)
    es_admin = request.user.is_staff or request.user.is_superuser
    tiene_permiso = False
    
    if es_admin:
        tiene_permiso = True
    elif hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario in ['profesor', 'administrativo', 'directivo']:
        tiene_permiso = True
        
    if not tiene_permiso:
        messages.error(request, "No tienes permisos para ver este historial.")
        return redirect('core:home')

    estudiante = get_object_or_404(User, id=estudiante_id, perfil__tipo_usuario='estudiante')
    anotaciones = Anotacion.objects.filter(estudiante=estudiante).select_related('profesor', 'curso').order_by('-fecha')
    
    positivas = anotaciones.filter(tipo='positiva').count()
    negativas = anotaciones.filter(tipo='negativa').count()

    return render(request, 'academico/anotaciones/historial_anotaciones.html', {
        'estudiante': estudiante,
        'anotaciones': anotaciones,
        'positivas': positivas,
        'negativas': negativas
    })

@login_required
def editar_curso(request, curso_id):
    """Vista administrativa para editar un curso"""
    # Verificar permisos de admin/staff
    if not (request.user.is_staff or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario in ['administrativo', 'directivo'])):
        messages.error(request, 'No tienes permisos para editar cursos.')
        return redirect('academico:gestion_cursos')

    curso = get_object_or_404(Curso, id=curso_id)

    if request.method == 'POST':
        try:
            curso.nivel = request.POST.get('nivel')
            curso.letra = request.POST.get('letra', '').upper()
            curso.año = request.POST.get('anio')
            
            profe_id = request.POST.get('profesor_jefe')
            if profe_id:
                curso.profesor_jefe_id = profe_id
            else:
                curso.profesor_jefe = None
            
            curso.save()
            messages.success(request, f'Curso {curso.nombre} actualizado correctamente.')
            return redirect('academico:gestion_cursos')

        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')

    # Obtener profesores para el select
    # Buscamos en PerfilUsuario donde tipo_usuario='profesor'
    # Nota: Depende de cómo esté modelado, asumo User con PerfilUsuario
    from usuarios.models import PerfilUsuario
    profesores_perfiles = PerfilUsuario.objects.filter(tipo_usuario='profesor').select_related('user')
    profesores = [p.user for p in profesores_perfiles]

    return render(request, 'academico/editar_curso.html', {
        'curso': curso,
        'profesores': profesores
    })

@login_required
def curso_inscripciones(request, curso_id):
    """Vista administrativa para ver estudiantes inscritos en un curso"""
    if not (request.user.is_staff or (hasattr(request.user, 'perfil') and request.user.perfil.tipo_usuario in ['administrativo', 'directivo'])):
         messages.error(request, 'No tienes permisos para ver inscripciones.')
         return redirect('academico:gestion_cursos')

    curso = get_object_or_404(Curso, id=curso_id)
    inscripciones = InscripcionCurso.objects.filter(curso=curso, año=curso.año, estado='activo').select_related('estudiante', 'estudiante__perfil').order_by('estudiante__last_name')

    return render(request, 'academico/curso_inscripciones.html', {
        'curso': curso,
        'inscripciones': inscripciones
    })
