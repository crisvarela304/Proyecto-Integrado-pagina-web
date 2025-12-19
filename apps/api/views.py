"""
Views de la API REST para Schoolar OS
Endpoints que consumirá la App móvil
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Avg

from .serializers import (
    UserSerializer, CalificacionSerializer, AsistenciaSerializer,
    HorarioSerializer, NotificacionSerializer, AnotacionSerializer
)
from .utils import api_response, api_error
from academico.models import Calificacion, Asistencia, HorarioClases, Anotacion, InscripcionCurso
from core.models import Notificacion, ColegioConfig


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado que incluye datos del usuario en el login
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Agregar claims personalizados
        token['username'] = user.username
        token['email'] = user.email
        if hasattr(user, 'perfil'):
            token['tipo_usuario'] = user.perfil.tipo_usuario
            token['uuid'] = str(user.perfil.uuid)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Agregar datos del usuario a la respuesta
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Login con JWT que retorna tokens + datos del usuario
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Envolver en respuesta estándar
            return api_response(
                data=response.data,
                message='Login exitoso'
            )
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Renovar token de acceso usando refresh token
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return api_response(
                data=response.data,
                message='Token renovado'
            )
        return response


# =============================================================================
# ALUMNO - ENDPOINTS PARA ESTUDIANTES
# =============================================================================

class AlumnoProfileView(APIView):
    """
    GET /api/alumno/me/
    Retorna el perfil del alumno autenticado
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Verificar que es estudiante
        if not hasattr(user, 'perfil') or user.perfil.tipo_usuario != 'estudiante':
            return api_error('Solo estudiantes pueden acceder a este recurso', status=403)
        
        serializer = UserSerializer(user)
        
        # Agregar info adicional del alumno
        data = serializer.data
        
        # Obtener curso actual
        inscripcion = InscripcionCurso.objects.filter(
            estudiante=user,
            estado='activo'
        ).select_related('curso').first()
        
        if inscripcion:
            data['curso'] = {
                'uuid': str(inscripcion.curso.uuid),
                'nombre': str(inscripcion.curso),
                'promedio': inscripcion.promedio
            }
        
        return api_response(data=data)


class AlumnoNotasView(ListAPIView):
    """
    GET /api/alumno/me/notas/
    Retorna las notas del alumno autenticado
    """
    serializer_class = CalificacionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Calificacion.objects.filter(
            estudiante=user
        ).select_related('asignatura').order_by('-fecha_evaluacion')
    
    def list(self, request, *args, **kwargs):
        # Verificar que es estudiante
        if not hasattr(request.user, 'perfil') or request.user.perfil.tipo_usuario != 'estudiante':
            return api_error('Solo estudiantes pueden acceder a este recurso', status=403)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calcular promedio general
        promedio = queryset.aggregate(promedio=Avg('nota'))['promedio']
        
        return api_response(data={
            'notas': serializer.data,
            'promedio_general': round(promedio, 1) if promedio else None,
            'total': queryset.count()
        })


class AlumnoAsistenciaView(ListAPIView):
    """
    GET /api/alumno/me/asistencia/
    Retorna la asistencia del alumno autenticado
    """
    serializer_class = AsistenciaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Asistencia.objects.filter(
            estudiante=user
        ).order_by('-fecha')
    
    def list(self, request, *args, **kwargs):
        if not hasattr(request.user, 'perfil') or request.user.perfil.tipo_usuario != 'estudiante':
            return api_error('Solo estudiantes pueden acceder a este recurso', status=403)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calcular estadísticas
        total = queryset.count()
        presentes = queryset.filter(estado='presente').count()
        porcentaje = round((presentes / total * 100), 1) if total > 0 else 100
        
        return api_response(data={
            'asistencia': serializer.data,
            'estadisticas': {
                'total_dias': total,
                'dias_presente': presentes,
                'porcentaje_asistencia': porcentaje
            }
        })


class AlumnoHorarioView(APIView):
    """
    GET /api/alumno/me/horario/
    Retorna el horario del alumno autenticado
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'perfil') or user.perfil.tipo_usuario != 'estudiante':
            return api_error('Solo estudiantes pueden acceder a este recurso', status=403)
        
        # Obtener curso del alumno
        inscripcion = InscripcionCurso.objects.filter(
            estudiante=user,
            estado='activo'
        ).first()
        
        if not inscripcion:
            return api_error('No tienes un curso asignado', status=404)
        
        horarios = HorarioClases.objects.filter(
            curso=inscripcion.curso,
            activo=True
        ).select_related('asignatura').order_by('dia', 'hora')
        
        serializer = HorarioSerializer(horarios, many=True)
        
        return api_response(data={
            'curso': str(inscripcion.curso),
            'horario': serializer.data
        })


class AlumnoAnotacionesView(ListAPIView):
    """
    GET /api/alumno/me/anotaciones/
    Retorna las anotaciones (hoja de vida) del alumno
    """
    serializer_class = AnotacionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Anotacion.objects.filter(
            estudiante=self.request.user
        ).order_by('-fecha')
    
    def list(self, request, *args, **kwargs):
        if not hasattr(request.user, 'perfil') or request.user.perfil.tipo_usuario != 'estudiante':
            return api_error('Solo estudiantes pueden acceder a este recurso', status=403)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        positivas = queryset.filter(tipo='positiva').count()
        negativas = queryset.filter(tipo='negativa').count()
        
        return api_response(data={
            'anotaciones': serializer.data,
            'resumen': {
                'positivas': positivas,
                'negativas': negativas
            }
        })


# =============================================================================
# NOTIFICACIONES
# =============================================================================

class NotificacionesListView(ListAPIView):
    """
    GET /api/notificaciones/
    Retorna las notificaciones del usuario
    """
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notificacion.objects.filter(
            usuario=self.request.user
        ).order_by('-created_at')[:50]  # Últimas 50
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        no_leidas = queryset.filter(leida=False).count()
        
        return api_response(data={
            'notificaciones': serializer.data,
            'no_leidas': no_leidas
        })


class NotificacionMarcarLeidaView(APIView):
    """
    POST /api/notificaciones/<uuid>/leer/
    Marca una notificación como leída
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, uuid):
        try:
            notificacion = Notificacion.objects.get(
                uuid=uuid,
                usuario=request.user
            )
            notificacion.leida = True
            notificacion.save(update_fields=['leida'])
            return api_response(message='Notificación marcada como leída')
        except Notificacion.DoesNotExist:
            return api_error('Notificación no encontrada', status=404)


# =============================================================================
# COLEGIO - PHONE HOME
# =============================================================================

class ColegioDiscoverView(APIView):
    """
    GET /api/colegio/discover/
    Retorna información del colegio para que la App sepa a dónde conectarse.
    Este endpoint es PÚBLICO (no requiere autenticación).
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        config = ColegioConfig.get_config()
        
        # Construir URL del logo si existe
        logo_url = None
        if config.logo:
            logo_url = request.build_absolute_uri(config.logo.url)
        
        return api_response(data={
            'codigo': config.codigo,
            'nombre': config.nombre,
            'url': config.url or request.build_absolute_uri('/'),
            'branding': {
                'logo': logo_url,
                'color_primario': config.color_primario,
                'color_secundario': config.color_secundario,
            }
        })


# =============================================================================
# TAREAS
# =============================================================================

class AlumnoTareasView(ListAPIView):
    """
    GET /api/alumno/me/tareas/
    Retorna las tareas pendientes del alumno
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from tareas.models import Tarea
        from academico.models import InscripcionCurso
        
        user = self.request.user
        # Obtener curso del alumno
        inscripcion = InscripcionCurso.objects.filter(
            estudiante=user,
            estado='activo'
        ).first()
        
        if not inscripcion:
            return Tarea.objects.none()
        
        return Tarea.objects.filter(
            curso=inscripcion.curso,
            estado='publicada'
        ).select_related('asignatura').order_by('fecha_entrega')
    
    def list(self, request, *args, **kwargs):
        from .serializers import TareaSerializer
        from tareas.models import Entrega
        
        if not hasattr(request.user, 'perfil') or request.user.perfil.tipo_usuario != 'estudiante':
            return api_error('Solo estudiantes pueden acceder', status=403)
        
        queryset = self.get_queryset()
        
        # Separar pendientes y entregadas
        entregadas_ids = Entrega.objects.filter(
            estudiante=request.user
        ).values_list('tarea_id', flat=True)
        
        pendientes = queryset.exclude(id__in=entregadas_ids)
        entregadas = queryset.filter(id__in=entregadas_ids)
        
        return api_response(data={
            'pendientes': TareaSerializer(pendientes, many=True).data,
            'entregadas': TareaSerializer(entregadas, many=True).data,
            'total_pendientes': pendientes.count()
        })


class AlumnoEntregasView(ListAPIView):
    """
    GET /api/alumno/me/entregas/
    Retorna las entregas del alumno con sus calificaciones
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        from .serializers import EntregaSerializer
        from tareas.models import Entrega
        
        if not hasattr(request.user, 'perfil') or request.user.perfil.tipo_usuario != 'estudiante':
            return api_error('Solo estudiantes pueden acceder', status=403)
        
        entregas = Entrega.objects.filter(
            estudiante=request.user
        ).select_related('tarea', 'tarea__asignatura').order_by('-fecha_entrega')
        
        return api_response(data={
            'entregas': EntregaSerializer(entregas, many=True).data,
            'total': entregas.count()
        })


# =============================================================================
# APODERADO
# =============================================================================

class ApoderadoPupilosView(APIView):
    """
    GET /api/apoderado/pupilos/
    Retorna los pupilos del apoderado con resumen de datos
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from usuarios.models import Pupilo
        from .serializers import PupiloResumenSerializer
        from academico.models import Calificacion, Asistencia, InscripcionCurso
        from django.db.models import Avg
        
        user = request.user
        
        if not hasattr(user, 'perfil') or user.perfil.tipo_usuario != 'apoderado':
            return api_error('Solo apoderados pueden acceder', status=403)
        
        pupilos = Pupilo.objects.filter(
            apoderado=user.perfil
        ).select_related('estudiante', 'estudiante__user')
        
        resultado = []
        for pupilo in pupilos:
            estudiante_user = pupilo.estudiante.user
            
            # Obtener curso
            inscripcion = InscripcionCurso.objects.filter(
                estudiante=estudiante_user,
                estado='activo'
            ).select_related('curso').first()
            
            # Calcular promedio
            promedio = Calificacion.objects.filter(
                estudiante=estudiante_user
            ).aggregate(prom=Avg('nota'))['prom']
            
            # Calcular asistencia
            total_dias = Asistencia.objects.filter(estudiante=estudiante_user).count()
            dias_presente = Asistencia.objects.filter(
                estudiante=estudiante_user, estado='presente'
            ).count()
            asistencia_pct = round((dias_presente / total_dias * 100), 1) if total_dias > 0 else 100
            
            resultado.append({
                'uuid': str(pupilo.estudiante.uuid),
                'nombre_completo': pupilo.estudiante.nombre_completo,
                'rut': pupilo.estudiante.rut,
                'vinculo': pupilo.get_vinculo_display(),
                'es_principal': pupilo.es_apoderado_principal,
                'curso': str(inscripcion.curso) if inscripcion else None,
                'promedio': round(promedio, 1) if promedio else None,
                'asistencia': asistencia_pct
            })
        
        return api_response(data={
            'pupilos': resultado,
            'total': len(resultado)
        })
