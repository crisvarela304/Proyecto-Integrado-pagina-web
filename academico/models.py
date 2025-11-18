from django.db import models
from django.contrib.auth.models import User
from comunicacion.models import CategoriaNoticia

class Asignatura(models.Model):
    """Asignaturas/materias del liceo"""
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField(blank=True)
    horas_semanales = models.IntegerField(default=2)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
    
    nombre = models.CharField(max_length=50)  # "1° Medio A"
    nivel = models.CharField(max_length=1, choices=NIVEL_CHOICES)
    letra = models.CharField(max_length=1)  # A, B, C, etc.
    año = models.IntegerField(default=2024)
    profesor_jefe = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    total_alumnos = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
    
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cursos_inscrito')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='estudiantes')
    año = models.IntegerField(default=2024)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('estudiante', 'curso', 'año')
        ordering = ['curso__nivel', 'curso__letra']

    def __str__(self):
        return f"{self.estudiante.username} - {self.curso}"

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
    
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='calificaciones')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='calificaciones')
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluaciones')
    tipo_evaluacion = models.CharField(max_length=15, choices=TIPO_EVALUACION)
    semestre = models.CharField(max_length=1, choices=SEMESTRE_CHOICES)
    fecha_evaluacion = models.DateField()
    numero_evaluacion = models.PositiveIntegerField(default=1)
    nota = models.DecimalField(max_digits=4, decimal_places=2, help_text="Nota del 1.0 al 7.0")
    descripcion = models.CharField(max_length=200, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
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
    profesor = models.ForeignKey(User, on_delete=models.CASCADE)
    dia = models.CharField(max_length=10, choices=DIA_CHOICES)
    hora = models.CharField(max_length=1, choices=HORA_CHOICES)
    sala = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
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
    
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asistencias')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES)
    observacion = models.TextField(blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('estudiante', 'curso', 'fecha')
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.estudiante.username} - {self.fecha} ({self.estado})"
