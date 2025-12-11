from django.utils import timezone
from academico.models import InscripcionCurso, Asistencia, Calificacion
from usuarios.models import PerfilUsuario
from django.db.models import Avg

class LiceoOSService:
    @staticmethod
    def get_kpis_globales():
        """Retorna indicadores clave para el dashboard"""
        from academico.models import Curso
        from comunicacion.models import Noticia
        from django.contrib.auth.models import User
        
        # Alumnos
        total_alumnos = PerfilUsuario.objects.filter(tipo_usuario='estudiante', activo=True).count()
        
        # Profesores
        total_profes = PerfilUsuario.objects.filter(tipo_usuario='profesor', activo=True).count()
        
        # Asistencia Hoy
        hoy = timezone.now().date()
        asistencias_hoy = Asistencia.objects.filter(fecha=hoy).count()
        presentes_hoy = Asistencia.objects.filter(fecha=hoy, estado='presente').count()
        porcentaje_asistencia_hoy = (presentes_hoy / asistencias_hoy * 100) if asistencias_hoy > 0 else 0
        
        pct_asistencia = round(porcentaje_asistencia_hoy, 1)
        
        return {
            'total_alumnos': total_alumnos,
            'total_profes': total_profes,
            'asistencia_hoy_pct': pct_asistencia,
            'asistencia_hoy_pct_js': str(pct_asistencia).replace(',', '.'), # Formato seguro para JS
            'ausentismo_hoy_pct_js': str(round(100 - pct_asistencia, 1)).replace(',', '.'), # Formato seguro para JS
            'noticias_mes': Noticia.objects.filter(creado__month=hoy.month).count()
        }

    @staticmethod
    def detectar_riesgo_academico():
        """
        Sistema de Alerta Temprana (SAT)
        Detecta alumnos con:
        1. Promedio general < 4.0
        2. Asistencia < 85%
        """
        año_actual = timezone.now().year
        # Obtener inscripciones activas
        inscripciones = InscripcionCurso.objects.filter(año=año_actual, estado='activo').select_related('estudiante', 'curso')
        
        alertas = []
        
        for inscripcion in inscripciones:
            estudiante = inscripcion.estudiante
            
            # Calcular Promedio
            promedio = Calificacion.objects.filter(
                estudiante=estudiante,
                fecha_evaluacion__year=año_actual
            ).aggregate(Avg('nota'))['nota__avg']
            
            # Calcular Asistencia
            total_asist = Asistencia.objects.filter(
                estudiante=estudiante,
                fecha__year=año_actual
            ).count()
            
            presentes = Asistencia.objects.filter(
                estudiante=estudiante,
                fecha__year=año_actual,
                estado='presente'
            ).count()
            
            pct_asistencia = (presentes / total_asist * 100) if total_asist > 0 else 100 # Asumimos 100 si no hay registros aun
            
            promedio = round(promedio, 1) if promedio else 0
            
            motivos = []
            if promedio > 0 and promedio < 4.0:
                motivos.append("Rendimiento Crítico")
            if pct_asistencia < 85:
                motivos.append("Inasistencia Grave")
                
            if motivos:
                alertas.append({
                    'estudiante': estudiante,
                    'curso': inscripcion.curso,
                    'promedio': promedio,
                    'asistencia': round(pct_asistencia, 1),
                    'motivos': motivos,
                    'nivel_riesgo': 'alto' if len(motivos) > 1 else 'medio'
                })
        
        # Ordenar por riesgo (doble motivo primero)
        return sorted(alertas, key=lambda x: x['nivel_riesgo'], reverse=False)

    @staticmethod
    def registrar_evento(usuario, tipo_accion, descripcion, detalles='', request=None):
        """
        Registra un evento en el Log de Auditoría.
        """
        try:
            from .models import RegistroActividad
            
            ip = None
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

            RegistroActividad.objects.create(
                usuario=usuario if usuario.is_authenticated else None,
                tipo_accion=tipo_accion,
                descripcion=descripcion,
                detalles=detalles,
                ip_address=ip
            )
        except Exception as e:
            # Fallback silencioso para no romper el flujo principal
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error registrando actividad: {e}")

    @staticmethod
    def get_historial_actividad(limite=20, tipo=None, usuario_id=None):
        """Retorna el historial filtrado"""
        from .models import RegistroActividad
        qs = RegistroActividad.objects.select_related('usuario__perfil').all()
        
        if tipo:
            qs = qs.filter(tipo_accion=tipo)
        
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
            
        return qs[:limite]
