#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de ejemplo completos
Sistema de Intranet del Liceo Juan Bautista de Hualqui
"""

import os
import sys
import django
from datetime import datetime, date, time, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from comunicacion.models import CategoriaNoticia, Noticia
from academico.models import Asignatura, Curso, InscripcionCurso, Calificacion, HorarioClases, Asistencia, TipoExamen, Examen
from documentos.models import CategoriaDocumento, Documento, ComunicadoPadres

def limpiar_datos():
    """Limpia todos los datos existentes (excepto superusuarios)"""
    print("🗑️  Limpiando datos existentes...")
    
    # Eliminar en orden de dependencias
    ComunicadoPadres.objects.all().delete()
    Examen.objects.all().delete()
    Documento.objects.all().delete()
    CategoriaDocumento.objects.all().delete()
    Asistencia.objects.all().delete()
    HorarioClases.objects.all().delete()
    Calificacion.objects.all().delete()
    InscripcionCurso.objects.all().delete()
    Curso.objects.all().delete()
    Asignatura.objects.all().delete()
    Noticia.objects.all().delete()
    CategoriaNoticia.objects.all().delete()
    PerfilUsuario.objects.all().delete()
    
    # No eliminar usuarios completamente, solo limpiar datos de prueba
    usuarios = User.objects.filter(is_superuser=False)
    for user in usuarios:
        user.delete()

def crear_usuarios():
    """Crea usuarios de prueba con diferentes roles"""
    print("👥 Creando usuarios...")
    
    usuarios_data = [
        {
            'username': 'admin',
            'email': 'admin@liceo.cl',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'password': 'admin123',
            'rut': '12345678-9',
            'tipo_usuario': 'administrativo',
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'prof.perez',
            'email': 'perez@liceo.cl',
            'first_name': 'Juan Carlos',
            'last_name': 'Pérez',
            'password': 'profesor123',
            'rut': '15678345-2',
            'tipo_usuario': 'profesor',
            'is_staff': True
        },
        {
            'username': 'prof.martinez',
            'email': 'martinez@liceo.cl',
            'first_name': 'María Elena',
            'last_name': 'Martínez',
            'password': 'profesor123',
            'rut': '12345789-3',
            'tipo_usuario': 'profesor'
        },
        {
            'username': 'est.2024001',
            'email': 'estudiante1@liceo.cl',
            'first_name': 'Ana Sofía',
            'last_name': 'González',
            'password': 'estudiante123',
            'rut': '21234567-8',
            'tipo_usuario': 'estudiante'
        },
        {
            'username': 'est.2024002',
            'email': 'estudiante2@liceo.cl',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'password': 'estudiante123',
            'rut': '21876543-1',
            'tipo_usuario': 'estudiante'
        },
        {
            'username': 'est.2024003',
            'email': 'estudiante3@liceo.cl',
            'first_name': 'Isabella',
            'last_name': 'López',
            'password': 'estudiante123',
            'rut': '22567890-4',
            'tipo_usuario': 'estudiante'
        },
        {
            'username': 'apoderado.lopez',
            'email': 'apoderado1@email.cl',
            'first_name': 'Patricia',
            'last_name': 'López',
            'password': 'apoderado123',
            'rut': '11234567-5',
            'tipo_usuario': 'apoderado'
        }
    ]
    
    usuarios_creados = []
    
    for data in usuarios_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'is_staff': data.get('is_staff', False),
                'is_superuser': data.get('is_superuser', False),
            }
        )
        
        if created:
            user.set_password(data['password'])
            user.save()
            
        # Crear o actualizar perfil
        perfil, _ = PerfilUsuario.objects.get_or_create(
            user=user,
            defaults={
                'rut': data['rut'],
                'tipo_usuario': data['tipo_usuario']
            }
        )
        usuarios_creados.append((user, perfil))
        print(f"   ✅ {user.username} ({data['tipo_usuario']})")
    
    return usuarios_creados

def crear_categorias_noticias():
    """Crea categorías de noticias"""
    print("📰 Creando categorías de noticias...")
    
    categorias = [
        ('académico', 'Académico', '#007bff'),
        ('actividades', 'Actividades', '#28a745'),
        ('convivencia', 'Convivencia Escolar', '#ffc107'),
        ('eventos', 'Eventos', '#17a2b8'),
        ('deportes', 'Deportes', '#fd7e14'),
        ('cultura', 'Cultura', '#6f42c1'),
        ('administrativo', 'Administrativo', '#6c757d'),
        ('comunicado', 'Comunicado', '#dc3545')
    ]
    
    for cat_slug, cat_name, color in categorias:
        CategoriaNoticia.objects.get_or_create(
            slug=cat_slug,
            defaults={'nombre': cat_name, 'color': color}
        )
        print(f"   ✅ {cat_name}")

def crear_asignaturas():
    """Crea asignaturas del liceo"""
    print("📚 Creando asignaturas...")
    
    asignaturas_data = [
        ('LENG', 'Lenguaje y Comunicación', 6),
        ('MATE', 'Matemática', 6),
        ('HIST', 'Historia y Geografía', 4),
        ('BIOL', 'Biología', 3),
        ('QUIM', 'Química', 3),
        ('FISIC', 'Física', 3),
        ('INGL', 'Inglés', 3),
        ('EDFI', 'Educación Física', 3),
        ('ART', 'Artes Visuales', 2),
        ('MUSI', 'Música', 2)
    ]
    
    for codigo, nombre, horas in asignaturas_data:
        Asignatura.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'horas_semanales': horas
            }
        )
        print(f"   ✅ {codigo} - {nombre}")

def crear_cursos():
    """Crea cursos del liceo"""
    print("🏫 Creando cursos...")
    
    cursos_data = [
        ('1', 'A', 2024),
        ('1', 'B', 2024),
        ('2', 'A', 2024),
        ('2', 'B', 2024),
        ('3', 'A', 2024),
        ('3', 'B', 2024),
        ('4', 'A', 2024),
        ('4', 'B', 2024)
    ]
    
    profesor_jefe = User.objects.get(username='prof.perez')
    
    for nivel, letra, año in cursos_data:
        nombre = f"{nivel}° Medio {letra}"
        Curso.objects.get_or_create(
            nivel=nivel,
            letra=letra,
            año=año,
            defaults={
                'nombre': nombre,
                'profesor_jefe': profesor_jefe,
                'total_alumnos': 35
            }
        )
        print(f"   ✅ {nombre}")

def crear_categorias_documentos():
    """Crea categorías de documentos"""
    print("📄 Creando categorías de documentos...")
    
    categorias = [
        ('Académico', 'Documentos académicos y curriculares', '#007bff', 'bi-book'),
        ('Administrativo', 'Documentos administrativos', '#28a745', 'bi-gear'),
        ('Convivencia', 'Documentos de convivencia escolar', '#ffc107', 'bi-people'),
        ('Reglamentos', 'Reglamentos y normativas', '#17a2b8', 'bi-shield-check'),
        ('Comunicados', 'Comunicados oficiales', '#dc3545', 'bi-megaphone'),
        ('Formularios', 'Formularios y solicitudes', '#6f42c1', 'bi-file-earmark'),
        ('Certificados', 'Certificados y diplomas', '#fd7e14', 'bi-award'),
        ('Recursos', 'Recursos educativos', '#20c997', 'bi-collection')
    ]
    
    for nombre, desc, color, icono in categorias:
        CategoriaDocumento.objects.get_or_create(
            nombre=nombre,
            defaults={
                'descripcion': desc,
                'color': color,
                'icono': icono
            }
        )
        print(f"   ✅ {nombre}")

def crear_noticias():
    """Crea noticias de ejemplo"""
    print("📰 Creando noticias...")
    
    categorias = {
        'académico': CategoriaNoticia.objects.get(slug='académico'),
        'actividades': CategoriaNoticia.objects.get(slug='actividades'),
        'eventos': CategoriaNoticia.objects.get(slug='eventos'),
        'administrativo': CategoriaNoticia.objects.get(slug='administrativo')
    }
    
    admin_user = User.objects.get(username='admin')
    profesor_user = User.objects.get(username='prof.perez')
    
    noticias_data = [
        {
            'titulo': 'Inicio del año escolar 2024',
            'bajada': 'El liceo da la bienvenida a todos los estudiantes para el nuevo año académico',
            'cuerpo': 'Es un honor darles la bienvenida a este nuevo año escolar. Este 2024 viene cargado de nuevos desafíos y oportunidades de crecimiento. Invitamos a toda la comunidad educativa a participar activamente en las actividades programadas.',
            'categoria': 'administrativo',
            'destacado': True,
            'autor': admin_user
        },
        {
            'titulo': 'Taller de robótica para estudiantes',
            'bajada': 'Iniciamos un nuevo taller de robótica dirigido a estudiantes de 3° y 4° Medio',
            'cuerpo': 'El liceo ha adquirido nuevos equipos de robótica que permitirán a nuestros estudiantes desarrollar habilidades en programación y automatización. El taller comenzará el próximo lunes y está dirigido a estudiantes de 3° y 4° Medio.',
            'categoria': 'actividades',
            'destacado': True,
            'autor': profesor_user
        },
        {
            'titulo': 'Feria científica escolar 2024',
            'bajada': 'Convocamos a todos los estudiantes a participar en la feria científica del establecimiento',
            'cuerpo': 'La feria científica es una oportunidad única para que los estudiantes presenten sus proyectos de investigación. Este año esperamos una gran participación y proyectos innovadores que reflejen el potencial de nuestros jóvenes.',
            'categoria': 'eventos',
            'destacado': False,
            'autor': profesor_user
        },
        {
            'titulo': 'Plan de estudios actualizado',
            'bajada': 'Conoce los cambios en el plan de estudios para este año académico',
            'cuerpo': 'Hemos actualizado nuestro plan de estudios para alinearlo con los nuevos estándares del MINEDUC. Los cambios incluyen nuevas metodologías de enseñanza y evaluación que buscan mejorar el aprendizaje de nuestros estudiantes.',
            'categoria': 'académico',
            'destacado': False,
            'autor': admin_user
        }
    ]
    
    for noticia_data in noticias_data:
        categoria = categorias[noticia_data['categoria']]
        Noticia.objects.create(
            titulo=noticia_data['titulo'],
            bajada=noticia_data['bajada'],
            cuerpo=noticia_data['cuerpo'],
            categoria=categoria,
            destacado=noticia_data['destacado'],
            autor=noticia_data['autor']
        )
        print(f"   ✅ {noticia_data['titulo']}")

def crear_examenes():
    """Crea exámenes programados"""
    print("📝 Creando exámenes...")
    
    # Crear tipos de examen
    tipos_examen = []
    for nombre, desc in [('Prueba', 'Prueba regular'), ('Examen', 'Examen semestral'), ('Certamen', 'Certamen'), ('Control', 'Control de lectura')]:
        tipo, _ = TipoExamen.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc}
        )
        tipos_examen.append(tipo)
    
    # Asignaturas y cursos
    asignaturas = Asignatura.objects.all()[:4]  # Solo las primeras 4
    cursos = Curso.objects.filter(nivel__in=['1', '2'])
    profesor = User.objects.get(username='prof.perez')
    
    # Crear exámenes para las próximas 4 semanas
    for i, (asignatura, curso) in enumerate(zip(asignaturas, cursos)):
        for j, tipo in enumerate(tipos_examen[:2]):  # Solo 2 tipos
            fecha = date.today() + timedelta(days=i*7 + j*3)
            Examen.objects.get_or_create(
                titulo=f"{tipo.nombre} de {asignatura.nombre}",
                defaults={
                    'descripcion': f'{tipo.descripcion} correspondiente al {j+1}° semestre',
                    'tipo_examen': tipo,
                    'curso': curso,
                    'asignatura': asignatura,
                    'profesor': profesor,
                    'fecha_aplicacion': fecha,
                    'hora_inicio': time(8, 0),
                    'duracion_minutos': 90,
                    'sala': f'Sala {curso.nivel}{j+1}0'
                }
            )
            print(f"   ✅ {tipo.nombre} - {asignatura.nombre} - {curso}")

def crear_comunicados():
    """Crea comunicados para padres"""
    print("📢 Creando comunicados...")
    
    admin_user = User.objects.get(username='admin')
    cursos = list(Curso.objects.all()[:4])
    
    comunicados_data = [
        {
            'titulo': 'Reunión de apoderados primer semestre',
            'contenido': 'Se cita a todos los apoderados a la reunión de inicio del primer semestre. La reunión se realizará en el gimnasio del establecimiento el día viernes 15 de marzo a las 19:00 hrs.',
            'urgencia': 'importante',
            'dirigido_a': 'apoderados',
            'cursos_objetivo': cursos[:2]
        },
        {
            'titulo': 'Suspensión de clases por elecciones',
            'contenido': 'Informamos que el día sábado 30 de marzo se suspenderán las clases debido a las elecciones municipales. Las actividades se reanudarán el lunes 1 de abril.',
            'urgencia': 'normal',
            'dirigido_a': 'todos',
            'cursos_objetivo': []
        },
        {
            'titulo': 'Semana de exámenes finales',
            'contenido': 'La semana del 22 al 26 de abril se realizará la semana de exámenes finales. Se solicita a los estudiantes prepararse adecuadamente y a los apoderados apoyar en el estudio.',
            'urgencia': 'importante',
            'dirigido_a': 'estudiantes',
            'cursos_objetivo': [cursos[2]]  # Solo 3° y 4° medio
        }
    ]
    
    for comunicado_data in comunicados_data:
        comunicado = ComunicadoPadres.objects.create(
            titulo=comunicado_data['titulo'],
            contenido=comunicado_data['contenido'],
            urgencia=comunicado_data['urgencia'],
            dirigido_a=comunicado_data['dirigido_a'],
            publicado_por=admin_user
        )
        comunicado.cursos_objetivo.set(comunicado_data['cursos_objetivo'])
        print(f"   ✅ {comunicado_data['titulo']}")

def crear_inscripciones_cursos():
    """Crea inscripciones de estudiantes a cursos"""
    print("📝 Creando inscripciones...")
    
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    cursos = Curso.objects.all()[:2]  # Solo 1° y 2° medio
    
    for estudiante in estudiantes:
        for curso in cursos:
            InscripcionCurso.objects.get_or_create(
                estudiante=estudiante,
                curso=curso,
                defaults={'año': 2024}
            )
    
    print(f"   ✅ {estudiantes.count()} estudiantes inscritos en {cursos.count()} cursos")

def main():
    """Función principal"""
    print("="*60)
    print("Poblando base de datos con datos de ejemplo COMPLETOS")
    print("Liceo Juan Bautista de Hualqui - Intranet Extendida")
    print("="*60)
    
    # Crear datos en orden
    crear_usuarios()
    print()
    
    crear_categorias_noticias()
    print()
    
    crear_asignaturas()
    print()
    
    crear_cursos()
    print()
    
    crear_categorias_documentos()
    print()
    
    crear_noticias()
    print()
    
    crear_examenes()
    print()
    
    crear_comunicados()
    print()
    
    crear_inscripciones_cursos()
    print()
    
    print("="*60)
    print("✅ Base de datos poblada exitosamente!")
    print()
    print("👥 USUARIOS CREADOS:")
    print("   • admin / admin123 (Administrador)")
    print("   • prof.perez / profesor123 (Profesor)")
    print("   • prof.martinez / profesor123 (Profesora)")
    print("   • est.2024001 / estudiante123 (Estudiante)")
    print("   • est.2024002 / estudiante123 (Estudiante)")
    print("   • est.2024003 / estudiante123 (Estudiante)")
    print("   • apoderado.lopez / apoderado123 (Apoderado)")
    print()
    print("🌐 URLS DISPONIBLES:")
    print("   • http://127.0.0.1:8000/ (Inicio)")
    print("   • http://127.0.0.1:8000/noticias/ (Noticias)")
    print("   • http://127.0.0.1:8000/documentos/ (Documentos)")
    print("   • http://127.0.0.1:8000/extract_info/ (Exámenes)")
    print("   • http://127.0.0.1:8000/extract_info/comunicados/ (Comunicados)")
    print("   • http://127.0.0.1:8000/admin/ (Panel Admin)")
    print("="*60)

if __name__ == '__main__':
    main()
