import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from comunicacion.models import CategoriaNoticia
from core.models import ConfiguracionAcademica

def obtener_año_actual():
    """Retorna el año académico actual configurado"""
    try:
        return ConfiguracionAcademica.get_actual().año_actual
    except Exception:
        return 2024

class Asignatura(models.Model):
    """Asignaturas/materias del liceo"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField(blank=True)
    horas_semanales = models.IntegerField(default=2)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Curso(models.Model):
    """Cursos del liceo (1° Medio A, 2° Medio B, etc.)"""
    NIVEL_CHOICES = [
        ('1', '1° Medio'),
        ('2', '2° Medio'),
        ('3', '3° Medio'),
        ('4', '4° Medio'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    nombre = models.CharField(max_length=50)  # "1° Medio A"
    nivel = models.CharField(max_length=1, choices=NIVEL_CHOICES)
    letra = models.CharField(max_length=1)  # A, B, C, etc.
    año = models.IntegerField(default=obtener_año_actual)
    profesor_jefe = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'perfil__tipo_usuario__in': ['profesor', 'administrativo', 'directivo']})
    total_alumnos = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        unique_together = ('nivel', 'letra', 'año')
        ordering = ['nivel', 'letra']

    def __str__(self):
        return f"{self.get_nivel_display()} {self.letra}"

class InscripcionCurso(models.Model):
    """Inscripción de estudiantes a cursos"""
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('retirado', 'Retirado'),
        ('egresado', 'Egresado'),
    ]
    
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cursos_inscrito', limit_choices_to={'perfil__tipo_usuario': 'estudiante'})
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='estudiantes')
    año = models.IntegerField(default=obtener_año_actual)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
    promedio = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Promedio calculado automáticamente")
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscripción de Curso"
        verbose_name_plural = "Inscripciones de Cursos"
        unique_together = ('estudiante', 'curso', 'año')
        ordering = ['curso__nivel', 'curso__letra']

    def __str__(self):
        return f"{self.estudiante.username} - {self.curso}"

    @property
    def promedio_actual(self):
        """Calcula el promedio actual del estudiante en este curso"""
        from django.db.models import Avg
        promedio = self.estudiante.calificaciones.filter(
            curso=self.curso
        ).aggregate(Avg('nota'))['nota__avg']
        return round(promedio, 1) if promedio else None

class Calificacion(models.Model):
    """Calificaciones de estudiantes"""
    TIPO_EVALUACION = [
        ('nota', 'Nota'),
        ('examen', 'Examen'),
        ('tarea', 'Tarea'),
        ('proyecto', 'Proyecto'),
        ('participacion', 'Participación'),
    ]
    
    SEMESTRE_CHOICES = [
        ('1', 'Primer Semestre'),
        ('2', 'Segundo Semestre'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones', limit_choices_to={'perfil__tipo_usuario': 'estudiante'})
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='calificaciones')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='calificaciones')
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluaciones', limit_choices_to={'perfil__tipo_usuario__in': ['profesor', 'administrativo', 'directivo']})
    tipo_evaluacion = models.CharField(max_length=15, choices=TIPO_EVALUACION)
    semestre = models.CharField(max_length=1, choices=SEMESTRE_CHOICES)
    fecha_evaluacion = models.DateField()
    numero_evaluacion = models.PositiveIntegerField(default=1)
    nota = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        validators=[
            MinValueValidator(1.0, message="La nota mínima es 1.0"),
            MaxValueValidator(7.0, message="La nota máxima es 7.0")
        ],
        help_text="Nota del 1.0 al 7.0"
    )
    descripcion = models.CharField(max_length=200, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        ordering = ['-fecha_evaluacion']
        unique_together = ('estudiante', 'asignatura', 'curso', 'numero_evaluacion')

    def __str__(self):
        return f"{self.estudiante.username} - {self.asignatura} ({self.nota})"



class HorarioClases(models.Model):
    """Horarios de clases"""
    DIA_CHOICES = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
    ]
    
    HORA_CHOICES = [
        ('1', '08:00 - 08:45'),
        ('2', '08:50 - 09:35'),
        ('3', '09:40 - 10:25'),
        ('4', '10:40 - 11:25'),
        ('5', '11:30 - 12:15'),
        ('6', '13:00 - 13:45'),
        ('7', '13:50 - 14:35'),
        ('8', '14:40 - 15:25'),
    ]
    
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='horario')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'perfil__tipo_usuario__in': ['profesor', 'administrativo', 'directivo']})
    dia = models.CharField(max_length=10, choices=DIA_CHOICES)
    hora = models.CharField(max_length=1, choices=HORA_CHOICES)
    sala = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horario de Clases"
        verbose_name_plural = "Horarios de Clases"
        unique_together = ('curso', 'dia', 'hora')
        ordering = ['dia', 'hora']

    def __str__(self):
        return f"{self.curso} - {self.dia} {self.get_hora_display()}"

class Asistencia(models.Model):
    """Registro de asistencia"""
    ESTADO_CHOICES = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('tardanza', 'Tardanza'),
        ('justificado', 'Justificado'),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asistencias', limit_choices_to={'perfil__tipo_usuario': 'estudiante'})
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES)
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'perfil__tipo_usuario__in': ['profesor', 'administrativo', 'directivo']})
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ('estudiante', 'curso', 'fecha')
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.estudiante.username} - {self.fecha} ({self.estado})"

class TipoExamen(models.Model):
    """Tipos de exámenes y evaluaciones"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    ponderacion_por_defecto = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Examen"
        verbose_name_plural = "Tipos de Exámenes"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Examen(models.Model):
    """Exámenes programados"""
    TIPO_PERIODO = [
        ('semestral', 'Semestral'),
        ('trimestral', 'Trimestral'),
        ('mensual', 'Mensual'),
        ('prueba', 'Prueba'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo_examen = models.ForeignKey(TipoExamen, on_delete=models.CASCADE, related_name='examenes')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='examenes')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='examenes')
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='examenes_creados', limit_choices_to={'perfil__tipo_usuario__in': ['profesor', 'administrativo', 'directivo']})
    tipo_periodo = models.CharField(max_length=15, choices=TIPO_PERIODO, default='prueba')
    fecha_aplicacion = models.DateField()
    hora_inicio = models.TimeField()
    duracion_minutos = models.PositiveIntegerField(default=90)
    sala = models.CharField(max_length=50, blank=True)
    instrucciones = models.TextField(blank=True)
    material_permitido = models.TextField(blank=True)
    ponderacion = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Examen"
        verbose_name_plural = "Exámenes"
        ordering = ['fecha_aplicacion', 'hora_inicio']

    def __str__(self):
        return f"{self.titulo} - {self.curso} - {self.asignatura}"

class PreguntaExamen(models.Model):
    """Preguntas para los exámenes"""
    TIPO_PREGUNTA = [
        ('opcion_multiple', 'Opción Múltiple'),
        ('verdadero_falso', 'Verdadero/Falso'),
        ('desarrollo', 'Desarrollo'),
        ('completar', 'Completar'),
    ]
    
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='preguntas')
    numero = models.PositiveIntegerField()
    tipo_pregunta = models.CharField(max_length=20, choices=TIPO_PREGUNTA)
    enunciado = models.TextField()
    opciones = models.TextField(blank=True, help_text="Para preguntas de opción múltiple (separadas por |)")
    respuesta_correcta = models.TextField(blank=True)
    puntos = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Pregunta de Examen"
        verbose_name_plural = "Preguntas de Exámenes"
        ordering = ['orden', 'numero']
        unique_together = ('examen', 'numero')


class Anotacion(models.Model):
    """Registro de hoja de vida del estudiante (Anotaciones)"""
    TIPO_CHOICES = [
        ('positiva', 'Positiva (Mérito)'),
        ('negativa', 'Negativa (Falta)'),
    ]
    
    CATEGORIA_CHOICES = [
        ('responsabilidad', 'Responsabilidad'),
        ('respeto', 'Respeto y Convivencia'),
        ('presentacion', 'Presentación Personal'),
        ('participacion', 'Participación en Clases'),
        ('honradez', 'Honradez'),
        ('otro', 'Otro'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='anotaciones_recibidas', limit_choices_to={'perfil__tipo_usuario': 'estudiante'})
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='anotaciones_creadas', limit_choices_to={'perfil__tipo_usuario__in': ['profesor', 'administrativo', 'directivo']})
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='otro')
    observacion = models.TextField("Observación")
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Anotación"
        verbose_name_plural = "Anotaciones"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.estudiante.get_full_name()}"

class RecursoAcademico(models.Model):
    """Recursos académicos subidos por profesores"""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to='recursos_academicos/%Y/%m/')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='recursos')
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'perfil__tipo_usuario__in': ['profesor', 'administrativo', 'directivo']})
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recurso Académico"
        verbose_name_plural = "Recursos Académicos"
        ordering = ['-creado']

    def __str__(self):
        return f"{self.titulo} ({self.curso})"
