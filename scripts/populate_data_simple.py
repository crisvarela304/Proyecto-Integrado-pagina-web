#!/usr/bin/env python
"""
Script simplificado para poblar la base de datos
Sistema de Intranet del Liceo Juan Bautista de Hualqui
"""

import os
import sys
import django
from datetime import datetime, date, time, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from comunicacion.models import Noticia
from academico.models import Asignatura, Curso, InscripcionCurso, TipoExamen, Examen
from documentos.models import CategoriaDocumento, ComunicadoPadres

def crear_usuarios():
    """Crea usuarios de prueba"""
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
            'username': 'apoderado.lopez',
            'email': 'apoderado1@email.cl',
            'first_name': 'Patricia',
            'last_name': 'López',
            'password': 'apoderado123',
            'rut': '11234567-5',
            'tipo_usuario': 'apoderado'
        }
    ]
    
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
        PerfilUsuario.objects.get_or_create(
            user=user,
            defaults={
                'rut': data['rut'],
                'tipo_usuario': data['tipo_usuario']
            }
        )
        print(f"   ✅ {user.username} ({data['tipo_usuario']})")

def crear_asignaturas():
    """Crea asignaturas básicas"""
    print("📚 Creando asignaturas...")
    
    asignaturas_data = [
        ('LENG', 'Lenguaje y Comunicación', 6),
        ('MATE', 'Matemática', 6),
        ('HIST', 'Historia y Geografía', 4),
        ('BIOL', 'Biología', 3),
        ('QUIM', 'Química', 3),
        ('INGL', 'Inglés', 3),
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
    """Crea cursos básicos"""
    print("🏫 Creando cursos...")
    
    try:
        profesor_jefe = User.objects.get(username='prof.perez')
    except User.DoesNotExist:
        profesor_jefe = None
    
    cursos_data = [
        ('1', 'A', 2024),
        ('1', 'B', 2024),
        ('2', 'A', 2024),
        ('2', 'B', 2024),
    ]
    
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

def crear_noticias():
    """Crea noticias de ejemplo"""
    print("📰 Creando noticias...")
    
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
            'cuerpo': 'El liceo ha adquirido nuevos equipos de robótica que permitirán a nuestros estudiantes desarrollar habilidades en programación y automatización.',
            'categoria': 'actividades',
            'destacado': True,
            'autor': profesor_user
        },
        {
            'titulo': 'Feria científica escolar 2024',
            'bajada': 'Convocamos a todos los estudiantes a participar en la feria científica del establecimiento',
            'cuerpo': 'La feria científica es una oportunidad única para que los estudiantes presenten sus proyectos de investigación.',
            'categoria': 'eventos',
            'destacado': False,
            'autor': profesor_user
        },
        {
            'titulo': 'Plan de estudios actualizado',
            'bajada': 'Conoce los cambios en el plan de estudios para este año académico',
            'cuerpo': 'Hemos actualizado nuestro plan de estudios para alinearlo con los nuevos estándares del MINEDUC.',
            'categoria': 'académico',
            'destacado': False,
            'autor': admin_user
        }
    ]
    
    for noticia_data in noticias_data:
        Noticia.objects.create(
            titulo=noticia_data['titulo'],
            bajada=noticia_data['bajada'],
            cuerpo=noticia_data['cuerpo'],
            categoria=noticia_data['categoria'],
            destacado=noticia_data['destacado'],
            autor=noticia_data['autor']
        )
        print(f"   ✅ {noticia_data['titulo']}")

def crear_examenes():
    """Crea exámenes programados"""
    print("📝 Creando exámenes...")
    
    # Crear tipos de examen
    tipos_data = [('Prueba', 'Prueba regular'), ('Examen', 'Examen semestral')]
    for nombre, desc in tipos_data:
        TipoExamen.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc}
        )
    
    try:
        asignaturas = list(Asignatura.objects.all()[:3])
        cursos = list(Curso.objects.filter(nivel__in=['1', '2'])[:2])
        profesor = User.objects.get(username='prof.perez')
        
        for i, asignatura in enumerate(asignaturas):
            for j, curso in enumerate(cursos):
                fecha = date.today() + timedelta(days=i*7 + j*3)
                tipo = TipoExamen.objects.first()
                
                Examen.objects.get_or_create(
                    titulo=f"Prueba de {asignatura.nombre}",
                    defaults={
                        'descripcion': 'Prueba correspondiente al primer semestre',
                        'tipo_examen': tipo,
                        'curso': curso,
                        'asignatura': asignatura,
                        'profesor': profesor,
                        'fecha_aplicacion': fecha,
                        'hora_inicio': time(8, 0),
                        'duracion_minutos': 90,
                        'sala': f'Sala {i+j+1}0'
                    }
                )
                print(f"   ✅ Prueba - {asignatura.nombre} - {curso}")
    except Exception as e:
        print(f"   ❌ Error creando exámenes: {e}")

def crear_categorias_documentos():
    """Crea categorías de documentos"""
    print("📄 Creando categorías de documentos...")
    
    categorias = [
        ('Académico', 'Documentos académicos', '#007bff', 'bi-book'),
        ('Administrativo', 'Documentos administrativos', '#28a745', 'bi-gear'),
        ('Comunicados', 'Comunicados oficiales', '#dc3545', 'bi-megaphone'),
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

def crear_comunicados():
    """Crea comunicados para padres"""
    print("📢 Creando comunicados...")
    
    try:
        admin_user = User.objects.get(username='admin')
        cursos = list(Curso.objects.all()[:2])
        
        comunicados_data = [
            {
                'titulo': 'Reunión de apoderados primer semestre',
                'contenido': 'Se cita a todos los apoderados a la reunión de inicio del primer semestre.',
                'urgencia': 'importante',
                'dirigido_a': 'apoderados',
                'cursos_objetivo': cursos
            },
            {
                'titulo': 'Suspensión de clases por elecciones',
                'contenido': 'Informamos que el día sábado se suspenderán las clases debido a las elecciones.',
                'urgencia': 'normal',
                'dirigido_a': 'todos',
                'cursos_objetivo': []
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
    except Exception as e:
        print(f"   ❌ Error creando comunicados: {e}")

def main():
    """Función principal"""
    print("="*60)
    print("Poblando base de datos con datos SIMPLIFICADOS")
    print("Liceo Juan Bautista de Hualqui - Intranet")
    print("="*60)
    
    # Crear datos en orden
    try:
        crear_usuarios()
        print()
        
        crear_asignaturas()
        print()
        
        crear_cursos()
        print()
        
        crear_noticias()
        print()
        
        crear_examenes()
        print()
        
        crear_categorias_documentos()
        print()
        
        crear_comunicados()
        print()
        
        print("="*60)
        print("✅ Base de datos poblada exitosamente!")
        print()
        print("👥 USUARIOS CREADOS:")
        print("   • admin / admin123 (Administrador)")
        print("   • prof.perez / profesor123 (Profesor)")
        print("   • est.2024001 / estudiante123 (Estudiante)")
        print("   • est.2024002 / estudiante123 (Estudiante)")
        print("   • apoderado.lopez / apoderado123 (Apoderado)")
        print()
        print("🌐 URLS DISPONIBLES:")
        print("   • http://127.0.0.1:8000/ (Inicio)")
        print("   • http://127.0.0.1:8000/noticias/ (Noticias)")
        print("   • http://127.0.0.1:8000/documentos/ (Documentos)")
        print("   • http://127.0.0.1:8000/admin/ (Panel Admin)")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error durante la población: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
