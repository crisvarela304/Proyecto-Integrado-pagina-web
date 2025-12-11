from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User
from .models import Calificacion, Asistencia, InscripcionCurso, HorarioClases, ConfiguracionAcademica, Asignatura

class AcademicoService:
    @staticmethod
    def get_anio_actual():
        return ConfiguracionAcademica.get_actual().año_actual

    @staticmethod
    def calcular_promedio_asignatura(estudiante, asignatura, curso, anio):
        """Calcula el promedio de un estudiante en una asignatura específica para el año dado."""
        return Calificacion.objects.filter(
            estudiante=estudiante,
            asignatura=asignatura,
            curso=curso,
            fecha_evaluacion__year=anio
        ).aggregate(Avg('nota'))['nota__avg']

    @staticmethod
    def obtener_asistencia_curso(estudiante, curso, anio):
        """Obtiene estadísticas de asistencia para un estudiante en un curso y año."""
        total = Asistencia.objects.filter(
            estudiante=estudiante, 
            curso=curso, 
            fecha__year=anio
        ).count()
        
        presentes = Asistencia.objects.filter(
            estudiante=estudiante, 
            curso=curso, 
            fecha__year=anio, 
            estado='presente'
        ).count()
        
        porcentaje = (presentes / total * 100) if total > 0 else 0
        return {
            'total': total,
            'presentes': presentes,
            'porcentaje': round(porcentaje, 1)
        }

    @staticmethod
    def get_estudiante_dashboard_data(user):
        """Genera los datos para el dashboard del estudiante."""
        anio_actual = AcademicoService.get_anio_actual()
        
        inscripcion = InscripcionCurso.objects.filter(
            estudiante=user, 
            estado='activo',
            año=anio_actual
        ).select_related('curso').first()
        
        if not inscripcion:
            return None

        curso = inscripcion.curso
        
        # Obtener asignaturas del curso (vía Horario)
        asignaturas_ids = HorarioClases.objects.filter(curso=curso).values_list('asignatura_id', flat=True).distinct()
        asignaturas = Asignatura.objects.filter(id__in=asignaturas_ids)
        
        resumen_asignaturas = []
        labels_grafico = []
        data_grafico = []
        
        # Optimización: Traer todas las calificaciones del año una sola vez
        calificaciones_anio = Calificacion.objects.filter(
            estudiante=user,
            fecha_evaluacion__year=anio_actual
        ).select_related('asignatura')
        
        # Agrupar en memoria
        notas_por_asignatura = {}
        for cal in calificaciones_anio:
            if cal.asignatura_id not in notas_por_asignatura:
                notas_por_asignatura[cal.asignatura_id] = []
            notas_por_asignatura[cal.asignatura_id].append(cal.nota)
            
        for asignatura in asignaturas:
            notas = notas_por_asignatura.get(asignatura.id, [])
            promedio = round(sum(notas) / len(notas), 1) if notas else None
            
            resumen_asignaturas.append({
                'asignatura': asignatura,
                'promedio': promedio,
                'cantidad_notas': len(notas)
            })
            
            if promedio:
                labels_grafico.append(asignatura.nombre)
                data_grafico.append(promedio)
                
        asistencia_stats = AcademicoService.obtener_asistencia_curso(user, curso, anio_actual)
        
        return {
            'curso': curso,
            'resumen_asignaturas': resumen_asignaturas,
            'asistencia_global': asistencia_stats['porcentaje'],
            'calificaciones_recientes': calificaciones_anio.order_by('-fecha_evaluacion')[:10],
            'labels_grafico': labels_grafico,
            'data_grafico': data_grafico
        }
