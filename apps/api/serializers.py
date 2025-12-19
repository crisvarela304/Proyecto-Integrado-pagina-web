"""
Serializers para la API REST
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import (
    Curso, Asignatura, Calificacion, Asistencia, 
    HorarioClases, Anotacion
)
from core.models import Notificacion


# =============================================================================
# USUARIOS
# =============================================================================

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para el perfil del usuario"""
    nombre_completo = serializers.ReadOnlyField()
    
    class Meta:
        model = PerfilUsuario
        fields = [
            'uuid', 'rut', 'tipo_usuario', 'telefono', 
            'foto_perfil', 'fecha_nacimiento', 'nombre_completo'
        ]
        read_only_fields = ['uuid', 'rut', 'tipo_usuario']


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el usuario de Django"""
    perfil = PerfilUsuarioSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'perfil']
        read_only_fields = ['id', 'username', 'email']


# =============================================================================
# ACADÉMICO
# =============================================================================

class AsignaturaSerializer(serializers.ModelSerializer):
    """Serializer para asignaturas"""
    class Meta:
        model = Asignatura
        fields = ['uuid', 'nombre', 'codigo']


class CursoSerializer(serializers.ModelSerializer):
    """Serializer para cursos"""
    nivel_display = serializers.CharField(source='get_nivel_display', read_only=True)
    
    class Meta:
        model = Curso
        fields = ['uuid', 'nombre', 'nivel', 'nivel_display', 'letra', 'año']


class CalificacionSerializer(serializers.ModelSerializer):
    """Serializer para calificaciones (notas)"""
    asignatura = AsignaturaSerializer(read_only=True)
    tipo_evaluacion_display = serializers.CharField(source='get_tipo_evaluacion_display', read_only=True)
    
    class Meta:
        model = Calificacion
        fields = [
            'uuid', 'asignatura', 'nota', 'tipo_evaluacion', 
            'tipo_evaluacion_display', 'descripcion', 'fecha_evaluacion',
            'semestre', 'numero_evaluacion'
        ]


class AsistenciaSerializer(serializers.ModelSerializer):
    """Serializer para asistencia"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Asistencia
        fields = ['uuid', 'fecha', 'estado', 'estado_display', 'observacion']


class HorarioSerializer(serializers.ModelSerializer):
    """Serializer para horario de clases"""
    asignatura = AsignaturaSerializer(read_only=True)
    dia_display = serializers.CharField(source='get_dia_display', read_only=True)
    hora_display = serializers.CharField(source='get_hora_display', read_only=True)
    
    class Meta:
        model = HorarioClases
        fields = ['dia', 'dia_display', 'hora', 'hora_display', 'asignatura', 'sala']


class AnotacionSerializer(serializers.ModelSerializer):
    """Serializer para anotaciones (hoja de vida)"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    
    class Meta:
        model = Anotacion
        fields = [
            'uuid', 'tipo', 'tipo_display', 'categoria', 
            'categoria_display', 'observacion', 'fecha'
        ]


# =============================================================================
# NOTIFICACIONES
# =============================================================================

class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Notificacion
        fields = ['uuid', 'tipo', 'tipo_display', 'titulo', 'mensaje', 'url', 'leida', 'created_at']


# =============================================================================
# TAREAS
# =============================================================================

class TareaSerializer(serializers.ModelSerializer):
    """Serializer para tareas"""
    from tareas.models import Tarea
    
    asignatura = AsignaturaSerializer(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)
    
    class Meta:
        from tareas.models import Tarea
        model = Tarea
        fields = [
            'uuid', 'titulo', 'descripcion', 'tipo', 'tipo_display',
            'asignatura', 'fecha_asignacion', 'fecha_entrega', 'hora_limite',
            'puntaje_maximo', 'estado', 'estado_display', 'esta_vencida'
        ]


class EntregaSerializer(serializers.ModelSerializer):
    """Serializer para entregas de tareas"""
    from tareas.models import Entrega
    
    tarea = TareaSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        from tareas.models import Entrega
        model = Entrega
        fields = [
            'uuid', 'tarea', 'fecha_entrega', 'entrega_tardia',
            'puntaje', 'comentario_profesor', 'estado', 'estado_display'
        ]


# =============================================================================
# APODERADO
# =============================================================================

class PupiloResumenSerializer(serializers.Serializer):
    """Serializer para resumen de pupilo (vista de apoderado)"""
    uuid = serializers.UUIDField(source='estudiante.uuid')
    nombre_completo = serializers.CharField(source='estudiante.nombre_completo')
    rut = serializers.CharField(source='estudiante.rut')
    vinculo = serializers.CharField(source='get_vinculo_display')
    es_principal = serializers.BooleanField(source='es_apoderado_principal')
