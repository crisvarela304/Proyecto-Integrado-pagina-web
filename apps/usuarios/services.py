from django.db.models import Avg, Count, Q
from academico.models import Curso, InscripcionCurso, Calificacion, Asistencia, HorarioClases
from comunicacion.models import Noticia

class PanelService:
    @staticmethod
    def get_student_stats(user):
        """Calcula estadísticas para el panel del estudiante (Optimizado)"""
        stats = {}
        
        # Promedio General (Leído desde caché DB)
        perfil = getattr(user, 'perfil', None)
        stats['promedio_general'] = perfil.promedio_general if perfil else None
        
        # Asistencia Global (Total)
        total_asistencias = Asistencia.objects.filter(estudiante=user).count()
        asistencias_presente = Asistencia.objects.filter(estudiante=user, estado='presente').count()
        stats['asistencia_porcentaje'] = round((asistencias_presente / total_asistencias * 100), 0) if total_asistencias > 0 else 0
        
        # Cursos inscritos (con promedio ya calculado)
        cursos_inscritos = InscripcionCurso.objects.filter(estudiante=user, estado='activo').select_related('curso')
        
        # Asistencia por curso (aún calculada al vuelo, pero es rápida)
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

        # Enriquecer objetos de inscripción
        for inscripcion in cursos_inscritos:
            # Usar el promedio guardado en la inscripción
            inscripcion.promedio_calculado = inscripcion.promedio
            inscripcion.asistencia_porcentaje = asistencia_map.get(inscripcion.curso.id, 0)
            
        stats['cursos_inscritos'] = cursos_inscritos
        return stats

    @staticmethod
    def get_professor_stats(user):
        """Calcula estadísticas para el panel del profesor"""
        stats = {}
        
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

        stats['cursos_unicos'] = cursos_unicos
        stats['total_alumnos_real'] = total_alumnos_real
        
        # Consejos de profesores
        stats['consejos'] = Noticia.objects.filter(categoria='consejo', es_publica=True).order_by('-creado')[:5]
        
        return stats
