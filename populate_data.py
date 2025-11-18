#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de ejemplo
para la intranet del Liceo Juan Bautista de Hualqui
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia
from comunicacion.models import Noticia

def crear_usuarios():
    """Crear usuarios de ejemplo"""
    print("Creando usuarios...")
    
    # Usuario administrador
    admin = User.objects.create_user(
        username='admin',
        email='admin@liceohualqui.cl',
        password='admin123',
        first_name='Admin',
        last_name='Sistema',
        is_staff=True,
        is_superuser=True
    )
    
    # Perfil administrador
    PerfilUsuario.objects.create(
        user=admin,
        rut='12345678-9',
        tipo_usuario='administrativo',
        telefono='+56 9 1234 5678'
    )
    
    # Crear profesores
    profesores_data = [
        ('prof.perez', 'María', 'Pérez', '23456789-0', '+56 9 2345 6789'),
        ('prof.martinez', 'Juan', 'Martínez', '34567890-1', '+56 9 3456 7890'),
        ('prof.gonzalez', 'Ana', 'González', '45678901-2', '+56 9 4567 8901'),
        ('prof.rodriguez', 'Carlos', 'Rodríguez', '56789012-3', '+56 9 5678 9012'),
        ('prof.lopez', 'Patricia', 'López', '67890123-4', '+56 9 6789 0123'),
    ]
    
    for username, nombre, apellido, rut, telefono in profesores_data:
        user = User.objects.create_user(
            username=username,
            email=f'{username}@liceohualqui.cl',
            password='profesor123',
            first_name=nombre,
            last_name=apellido
        )
        
        PerfilUsuario.objects.create(
            user=user,
            rut=rut,
            tipo_usuario='profesor',
            telefono=telefono
        )
    
    # Crear estudiantes
    estudiantes_data = [
        ('est.2024001', 'Sofia', 'Morales', '78901234-5', '+56 9 7890 1234'),
        ('est.2024002', 'Diego', 'Castro', '89012345-6', '+56 9 8901 2345'),
        ('est.2024003', 'Camila', 'Silva', '90123456-7', '+56 9 9012 3456'),
        ('est.2024004', 'Matías', 'Herrera', '01234567-8', '+56 9 0123 4567'),
        ('est.2024005', 'Valentina', 'Muñoz', '12345678-9', '+56 9 1234 5678'),
        ('est.2024006', 'Joaquín', 'Valencia', '23456789-0', '+56 9 2345 6789'),
        ('est.2024007', 'Francisca', 'Espinoza', '34567890-1', '+56 9 3456 7890'),
        ('est.2024008', 'Benjamín', 'Aguilar', '45678901-2', '+56 9 4567 8901'),
    ]
    
    for username, nombre, apellido, rut, telefono in estudiantes_data:
        user = User.objects.create_user(
            username=username,
            email=f'{username}@liceohualqui.cl',
            password='estudiante123',
            first_name=nombre,
            last_name=apellido
        )
        
        PerfilUsuario.objects.create(
            user=user,
            rut=rut,
            tipo_usuario='estudiante',
            telefono=telefono
        )
    
    print(f"Usuarios creados exitosamente")
    return User.objects.all()

def crear_asignaturas():
    """Crear asignaturas de ejemplo"""
    print("Creando asignaturas...")
    
    asignaturas_data = [
        ('MAT101', 'Matemáticas', 4, 1),
        ('LEN101', 'Lenguaje y Comunicación', 4, 1),
        ('CIE101', 'Ciencias Naturales', 3, 1),
        ('HIS101', 'Historia, Geografía y Ciencias Sociales', 3, 1),
        ('ING101', 'Inglés', 3, 1),
        ('EDU101', 'Educación Física', 2, 1),
        ('ART101', 'Artes Visuales', 2, 1),
        ('MUS101', 'Educación Musical', 2, 1),
    ]
    
    for codigo, nombre, horas, activa in asignaturas_data:
        Asignatura.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'horas_semanales': horas,
                'activa': bool(activa)
            }
        )
    
    print(f"Asignaturas creadas: {Asignatura.objects.count()}")

def crear_cursos():
    """Crear cursos de ejemplo"""
    print("Creando cursos...")
    
    # Obtener profesores
    profesor1 = User.objects.filter(username='prof.perez').first()
    profesor2 = User.objects.filter(username='prof.martinez').first()
    profesor3 = User.objects.filter(username='prof.gonzalez').first()
    
    cursos_data = [
        ('1° Medio A', '1', 'A', 2024, profesor1),
        ('1° Medio B', '1', 'B', 2024, profesor2),
        ('2° Medio A', '2', 'A', 2024, profesor1),
        ('2° Medio B', '2', 'B', 2024, profesor3),
        ('3° Medio A', '3', 'A', 2024, profesor2),
        ('4° Medio A', '4', 'A', 2024, profesor1),
    ]
    
    for nombre, nivel, letra, año, profesor in cursos_data:
        Curso.objects.get_or_create(
            nombre=nombre,
            nivel=nivel,
            letra=letra,
            año=año,
            defaults={
                'profesor_jefe': profesor,
                'total_alumnos': 35
            }
        )
    
    print(f"Cursos creados: {Curso.objects.count()}")

def inscribir_estudiantes():
    """Inscribir estudiantes en cursos"""
    print("Inscribiendo estudiantes en cursos...")
    
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    cursos = Curso.objects.all()
    
    # Inscribir estudiantes en cursos (8 estudiantes en 1° Medio A y 1° Medio B)
    estudiantes_curso1 = estudiantes[:4]  # 4 estudiantes para 1° Medio A
    estudiantes_curso2 = estudiantes[4:8]  # 4 estudiantes para 1° Medio B
    
    for i, estudiante in enumerate(estudiantes_curso1):
        InscripcionCurso.objects.get_or_create(
            estudiante=estudiante,
            curso=cursos[0],  # 1° Medio A
            año=2024,
            defaults={'estado': 'activo'}
        )
    
    for i, estudiante in enumerate(estudiantes_curso2):
        InscripcionCurso.objects.get_or_create(
            estudiante=estudiante,
            curso=cursos[1],  # 1° Medio B
            año=2024,
            defaults={'estado': 'activo'}
        )
    
    print(f"Inscripciones creadas: {InscripcionCurso.objects.count()}")

def crear_horarios():
    """Crear horarios de ejemplo"""
    print("Creando horarios...")
    
    # Obtener datos necesarios
    cursos = Curso.objects.all()
    asignaturas = Asignatura.objects.all()
    profesores = User.objects.filter(perfil__tipo_usuario='profesor')
    
    # Crear horarios para los primeros 2 cursos
    for i, curso in enumerate(cursos[:2]):
        for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']:
            for hora in ['1', '2', '3', '4']:
                # Asignar asignaturas rotando
                asignatura = asignaturas[(int(hora) + i) % len(asignaturas)]
                profesor = profesores[(int(hora) + i) % len(profesores)]
                
                HorarioClases.objects.get_or_create(
                    curso=curso,
                    asignatura=asignatura,
                    dia=dia,
                    hora=hora,
                    defaults={
                        'profesor': profesor,
                        'sala': f'Sala {ord("A") + (int(hora) + i) % 10}'
                    }
                )
    
    print(f"Horarios creados: {HorarioClases.objects.count()}")

def crear_calificaciones():
    """Crear calificaciones de ejemplo"""
    print("Creando calificaciones...")
    
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    cursos = Curso.objects.all()[:2]  # Solo primeros 2 cursos
    asignaturas = Asignatura.objects.all()
    profesores = User.objects.filter(perfil__tipo_usuario='profesor')
    
    for estudiante in estudiantes:
        for curso in cursos:
            for asignatura in asignaturas:
                # Crear 3-4 calificaciones por asignatura
                for i in range(3):
                    fecha = datetime.now() - timedelta(days=i*10)
                    semestre = '1' if i == 0 or i == 2 else '2'
                    tipo = ['nota', 'examen', 'tarea'][i % 3]
                    nota = Decimal(str(round(3.5 + (i * 0.3) + (estudiante.id % 3) * 0.2, 1)))
                    
                    Calificacion.objects.create(
                        estudiante=estudiante,
                        asignatura=asignatura,
                        curso=curso,
                        profesor=profesores[i % len(profesores)],
                        tipo_evaluacion=tipo,
                        semestre=semestre,
                        fecha_evaluacion=fecha.date(),
                        nota=nota,
                        descripcion=f'Evaluación {i+1} de {asignatura.nombre}'
                    )
    
    print(f"Calificaciones creadas: {Calificacion.objects.count()}")

def crear_asistencias():
    """Crear asistencias de ejemplo"""
    print("Creando asistencias...")
    
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    cursos = Curso.objects.all()[:2]
    profesores = User.objects.filter(perfil__tipo_usuario='profesor')
    
    # Crear asistencias para los últimos 20 días
    for i in range(20):
        fecha = datetime.now() - timedelta(days=i)
        
        for estudiante in estudiantes:
            curso = cursos[0] if estudiante.id % 2 == 0 else cursos[1]
            
            # Asignar estado aleatorio pero con tendencia a presente
            import random
            estados = ['presente', 'presente', 'presente', 'presente', 'ausente', 'tardanza', 'justificado']
            estado = random.choice(estados)
            
            Asistencia.objects.create(
                estudiante=estudiante,
                curso=curso,
                fecha=fecha.date(),
                estado=estado,
                observacion=f'Asistencia del {fecha.strftime("%d/%m/%Y")}' if estado != 'presente' else '',
                registrado_por=profesores[i % len(profesores)]
            )
    
    print(f"Asistencias creadas: {Asistencia.objects.count()}")

def crear_noticias():
    """Crear noticias de ejemplo"""
    print("Creando noticias...")
    
    admin = User.objects.filter(is_superuser=True).first()
    
    noticias_data = [
        {
            'titulo': 'Bienvenida al nuevo año escolar 2024',
            'bajada': 'Invitamos a toda la comunidad educativa a iniciar este nuevo período académico con entusiasmo y compromiso.',
            'cuerpo': '''Estimada comunidad educativa del Liceo Juan Bautista de Hualqui:

Es un gusto dar la bienvenida a todos nuestros estudiantes, apoderados y docentes al año escolar 2024. Este año viene cargado de novedades y oportunidades de crecimiento para todos.

Durante el 2024 continuaremos fortaleciendo nuestros programas académicos, implementando nuevas tecnologías en el aula y promoviendo valores de convivencia escolar.

Los esperamos con los brazos abiertos para construir juntos un año lleno de aprendizaje y desarrollo personal.''',
            'categoria': 'administrativo',
            'destacado': True,
            'urgente': False
        },
        {
            'titulo': 'Taller de Robótica para estudiantes de 3° y 4° Medio',
            'bajada': 'Iniciativa pionera que busca fomentar el interés por la tecnología y la innovación.',
            'cuerpo': '''El Liceo Juan Bautista de Hualqui se complace en anunciar la creación del Taller de Robótica, dirigido a estudiantes de 3° y 4° Medio.

Este programa busca:
- Desarrollar habilidades en programación y robótica
- Preparar a los estudiantes para carreras tecnológicas
- Fomentar el trabajo en equipo y la creatividad
- Participar en competencias regionales y nacionales

El taller se realizará los días martes y jueves de 15:30 a 17:00 hrs en el laboratorio de ciencias.''',
            'categoria': 'actividades',
            'destacado': False,
            'urgente': False
        },
        {
            'titulo': 'Importante: Modificación en el horario de llegada',
            'bajada': 'A partir del lunes 15 de enero, se modifíca el horario de llegada al establecimiento.',
            'cuerpo': '''Estimados apoderados y estudiantes:

Informamos que, debido a obras de mejoramiento en el acceso principal del liceo, a partir del lunes 15 de enero se implementará el siguiente horario de llegada:

- Estudiantes de 1° y 2° Medio: 08:00 hrs
- Estudiantes de 3° y 4° Medio: 08:15 hrs

Esta modificación es temporal y permitirá un mejor flujo de vehículos durante las obras de construcción.

Agradecemos su comprensión.''',
            'categoria': 'comunicado',
            'destacado': False,
            'urgente': True
        },
        {
            'titulo': 'Examenes de admisión universitaria 2024',
            'bajada': 'Información importante para estudiantes de 4° medio sobre el proceso de admisión universitaria.',
            'cuerpo': '''A nuestros estudiantes de 4° Medio:

Les recordamos que las fechas para los exámenes de admisión universitaria 2024 son:

- Examen de Matemáticas: 29 de diciembre
- Examen de Lenguaje: 2 de enero
- Examenes de Ciencias: 4 de enero

Es importante que se registren en el DEMRE con anticipación y preparen adecuadamente estos importantes exámenes.

El liceo ofrece talleres de preparación los sábados por la mañana. Consulten en Secretaría de Estudiantes.''',
            'categoria': 'académico',
            'destacado': True,
            'urgente': False
        },
        {
            'titulo': 'Festival de Artes 2024',
            'bajada': 'Una muestra talentos artísticos de nuestros estudiantes en música, teatro y artes visuales.',
            'cuerpo': '''El próximo 20 de febrero se realizará nuestro tradicional Festival de Artes, donde los estudiantes podrán展示ar sus talentos en:

**Programa del Festival:**
- Presentación de bandas musicales
- Teatro y declamación
- Exposición de obras visuales
- Presentación folklórica
- Premio al estudiante artista del año

El evento se realizará en el gimnasio del liceo a partir de las 19:00 hrs. La entrada es libre y gratuita para toda la comunidad.

¡Los esperamos!''',
            'categoria': 'cultura',
            'destacado': False,
            'urgente': False
        }
    ]
    
    for noticia_data in noticias_data:
        Noticia.objects.create(
            titulo=noticia_data['titulo'],
            bajada=noticia_data['bajada'],
            cuerpo=noticia_data['cuerpo'],
            categoria=noticia_data['categoria'],
            destacado=noticia_data['destacado'],
            urgente=noticia_data['urgente'],
            es_publica=True,
            autor=admin
        )
    
    print(f"Noticias creadas: {Noticia.objects.count()}")

def main():
    """Ejecutar toda la creación de datos"""
    print("=" * 60)
    print("Poblando base de datos con datos de ejemplo")
    print("Liceo Juan Bautista de Hualqui - Intranet")
    print("=" * 60)
    
    try:
        crear_usuarios()
        crear_asignaturas()
        crear_cursos()
        inscribir_estudiantes()
        crear_horarios()
        crear_calificaciones()
        crear_asistencias()
        crear_noticias()
        
        print("\n" + "=" * 60)
        print("✅ POBLACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\n📊 RESUMEN:")
        print(f"   • Usuarios: {User.objects.count()}")
        print(f"   • Perfiles: {PerfilUsuario.objects.count()}")
        print(f"   • Asignaturas: {Asignatura.objects.count()}")
        print(f"   • Cursos: {Curso.objects.count()}")
        print(f"   • Inscripciones: {InscripcionCurso.objects.count()}")
        print(f"   • Horarios: {HorarioClases.objects.count()}")
        print(f"   • Calificaciones: {Calificacion.objects.count()}")
        print(f"   • Asistencias: {Asistencia.objects.count()}")
        print(f"   • Noticias: {Noticia.objects.count()}")
        
        print("\n🔐 USUARIOS DE PRUEBA:")
        print("   • Administrador: admin / admin123")
        print("   • Profesor: prof.perez / profesor123")
        print("   • Estudiante: est.2024001 / estudiante123")
        
        print("\n🌐 PUEDE ACCEDER A:")
        print("   • http://localhost:8000/")
        print("   • http://localhost:8000/noticias/")
        print("   • http://localhost:8000/academico/dashboard/")
        print("   • http://localhost:8000/admin/")
        
    except Exception as e:
        print(f"❌ Error durante la población: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
