#!/usr/bin/env python
"""
Script para agregar más estudiantes y funcionalidades de profesor
Sistema de Intranet del Liceo Juan Bautista de Hualqui
"""

import os
import sys
import django
from datetime import datetime, date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import Asignatura, Curso, InscripcionCurso, Calificacion, Asistencia, HorarioClases
from documentos.models import ComunicadoPadres

def crear_mas_estudiantes():
    """Crea más estudiantes ficticios"""
    print("👥 Creando más estudiantes ficticios...")
    
    estudiantes_data = [
        {
            'username': 'est.2024004',
            'email': 'camila.silva@liceo.cl',
            'first_name': 'Camila',
            'last_name': 'Silva',
            'password': 'estudiante123',
            'rut': '20876543-2',
            'tipo_usuario': 'estudiante',
            'curso': '1A'
        },
        {
            'username': 'est.2024005',
            'email': 'matias.rios@liceo.cl',
            'first_name': 'Matías',
            'last_name': 'Ríos',
            'password': 'estudiante123',
            'rut': '19567890-3',
            'tipo_usuario': 'estudiante',
            'curso': '1A'
        },
        {
            'username': 'est.2024006',
            'email': 'sofia.castro@liceo.cl',
            'first_name': 'Sofía',
            'last_name': 'Castro',
            'password': 'estudiante123',
            'rut': '19876543-4',
            'tipo_usuario': 'estudiante',
            'curso': '1B'
        },
        {
            'username': 'est.2024007',
            'email': 'felipe.morales@liceo.cl',
            'first_name': 'Felipe',
            'last_name': 'Morales',
            'password': 'estudiante123',
            'rut': '20123456-5',
            'tipo_usuario': 'estudiante',
            'curso': '1B'
        },
        {
            'username': 'est.2024008',
            'email': 'valentina.torres@liceo.cl',
            'first_name': 'Valentina',
            'last_name': 'Torres',
            'password': 'estudiante123',
            'rut': '20456789-6',
            'tipo_usuario': 'estudiante',
            'curso': '2A'
        },
        {
            'username': 'est.2024009',
            'email': 'alonso.espinoza@liceo.cl',
            'first_name': 'Alonso',
            'last_name': 'Espinoza',
            'password': 'estudiante123',
            'rut': '19876543-7',
            'tipo_usuario': 'estudiante',
            'curso': '2A'
        },
        {
            'username': 'est.2024010',
            'email': 'cristobal.valenzuela@liceo.cl',
            'first_name': 'Cristóbal',
            'last_name': 'Valenzuela',
            'password': 'estudiante123',
            'rut': '20234567-8',
            'tipo_usuario': 'estudiante',
            'curso': '2B'
        },
        {
            'username': 'est.2024011',
            'email': 'alejandra.rojas@liceo.cl',
            'first_name': 'Alejandra',
            'last_name': 'Rojas',
            'password': 'estudiante123',
            'rut': '19567890-9',
            'tipo_usuario': 'estudiante',
            'curso': '2B'
        }
    ]
    
    # Mapear cursos
    cursos_map = {}
    for curso in Curso.objects.all():
        cursos_map[f"{curso.nivel}{curso.letra}"] = curso
    
    for data in estudiantes_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
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
        
        # Inscribir en curso
        curso = cursos_map.get(data['curso'])
        if curso:
            InscripcionCurso.objects.get_or_create(
                estudiante=user,
                curso=curso,
                defaults={'año': 2024}
            )
        
        print(f"   ✅ {user.first_name} {user.last_name} - {data['curso']}")
    
    print(f"   📊 Total estudiantes creados: {len(estudiantes_data)}")

def crear_calificaciones():
    """Crea calificaciones de ejemplo para los estudiantes"""
    print("📊 Creando calificaciones de ejemplo...")
    
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    asignaturas = Asignatura.objects.all()[:4]  # Solo las primeras 4 asignaturas
    cursos = Curso.objects.filter(nivel__in=['1', '2'])
    
    calificaciones_data = []
    
    for curso in cursos:
        inscripciones = InscripcionCurso.objects.filter(curso=curso)
        
        for inscripcion in inscripciones:
            estudiante = inscripcion.estudiante
            
            for asignatura in asignaturas:
                # Crear 3 calificaciones por asignatura
                for i in range(1, 4):
                    nota = round(3.5 + (i * 1.5) + (estudiante.id % 2), 1)  # Notas entre 3.5 y 7.0
                    fecha = date.today() - timedelta(days=30 - (i * 10))
                    
                    calificacion, created = Calificacion.objects.get_or_create(
                        estudiante=estudiante,
                        asignatura=asignatura,
                        curso=curso,
                        numero_evaluacion=i,
                        defaults={
                            'nota': nota,
                            'fecha_evaluacion': fecha,
                            'descripcion': f'Evaluación {i} de {asignatura.nombre}'
                        }
                    )
                    if created:
                        calificaciones_data.append(f"{estudiante.first_name} - {asignatura.codigo} - Nota: {nota}")
    
    print(f"   ✅ {len(calificaciones_data)} calificaciones creadas")
    for cal in calificaciones_data[:10]:  # Mostrar solo las primeras 10
        print(f"      {cal}")

def crear_asistencias():
    """Crea registros de asistencia de ejemplo"""
    print("📅 Creando registros de asistencia...")
    
    estudiantes = User.objects.filter(perfil__tipo_usuario='estudiante')
    cursos = Curso.objects.filter(nivel__in=['1', '2'])
    
    asistencias_data = []
    
    # Crear asistencia para los últimos 20 días
    for curso in cursos:
        inscripciones = InscripcionCurso.objects.filter(curso=curso)
        
        for inscripcion in inscripciones:
            estudiante = inscripcion.estudiante
            
            for dias_atras in range(20):
                fecha = date.today() - timedelta(days=dias_atras)
                
                # Solo registrar días laborables (lunes a viernes)
                if fecha.weekday() < 5:  # 0=lunes, 4=viernes
                    # 90% de asistencia aproximada
                    estado = 'presente' if dias_atras % 10 != 0 else 'ausente'
                    
                    asistencia, created = Asistencia.objects.get_or_create(
                        estudiante=estudiante,
                        curso=curso,
                        fecha=fecha,
                        defaults={
                            'estado': estado,
                            'observaciones': 'Asistencia regular' if estado == 'presente' else 'Injustificado'
                        }
                    )
                    if created and dias_atras < 5:  # Solo mostrar las más recientes
                        asistencias_data.append(f"{estudiante.first_name} - {fecha} - {estado}")
    
    print(f"   ✅ Registros de asistencia creados")
    for asistencia in asistencias_data[:5]:  # Mostrar solo las primeras 5
        print(f"      {asistencia}")

def crear_horarios():
    """Crea horarios de ejemplo para profesores"""
    print("🕐 Creando horarios de clases...")
    
    try:
        profesor = User.objects.get(username='prof.perez')
        asignaturas = Asignatura.objects.all()[:4]
        cursos = Curso.objects.filter(nivel__in=['1', '2'])
        
        # Horarios para un profesor
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        horas_clase = [
            ('08:00', '08:45'),
            ('09:00', '09:45'),
            ('10:15', '11:00'),
            ('11:15', '12:00'),
            ('13:30', '14:15'),
            ('14:30', '15:15')
        ]
        
        for i, (dia, hora_inicio, hora_fin) in enumerate([(dia, h[0], h[1]) for dia in dias_semana for h in horas_clase]):
            if i < len(asignaturas) * 2:  # Limitar el número de clases
                asignatura = asignaturas[i % len(asignaturas)]
                curso = cursos[i % len(cursos)]
                
                HorarioClases.objects.get_or_create(
                    profesor=profesor,
                    asignatura=asignatura,
                    curso=curso,
                    dia_semana=dia,
                    hora_inicio=hora_inicio,
                    defaults={
                        'sala': f'Sala {i % 5 + 1}0',
                        'observaciones': 'Clase regular'
                    }
                )
        
        print(f"   ✅ Horarios creados para profesor {profesor.first_name} {profesor.last_name}")
        
    except User.DoesNotExist:
        print("   ❌ No se encontró el profesor de ejemplo")

def crear_comunicados_profesor():
    """Crea comunicados adicionales"""
    print("📢 Creando comunicados adicionales...")
    
    try:
        admin_user = User.objects.get(username='admin')
        profesor_user = User.objects.get(username='prof.perez')
        cursos = list(Curso.objects.filter(nivel__in=['1', '2'])[:2])
        
        comunicados_data = [
            {
                'titulo': 'Información importante para estudiantes',
                'contenido': 'Se recuerda a todos los estudiantes la importancia de mantener al día sus calificaciones y asistir puntualmente a las clases.',
                'urgencia': 'importante',
                'dirigido_a': 'estudiantes',
                'cursos_objetivo': cursos,
                'autor': admin_user
            },
            {
                'titulo': 'Recordatorio para apoderados',
                'contenido': 'Los apoderados están invitados a revisar regularmente el avance académico de sus hijos a través de la plataforma.',
                'urgencia': 'normal',
                'dirigido_a': 'apoderados',
                'cursos_objetivo': cursos,
                'autor': profesor_user
            }
        ]
        
        for comunicado_data in comunicados_data:
            comunicado = ComunicadoPadres.objects.create(
                titulo=comunicado_data['titulo'],
                contenido=comunicado_data['contenido'],
                urgencia=comunicado_data['urgencia'],
                dirigido_a=comunicado_data['dirigido_a'],
                publicado_por=comunicado_data['autor']
            )
            comunicado.cursos_objetivo.set(comunicado_data['cursos_objetivo'])
            print(f"   ✅ {comunicado_data['titulo']}")
            
    except Exception as e:
        print(f"   ❌ Error creando comunicados: {e}")

def main():
    """Función principal"""
    print("="*70)
    print("Agregando ESTUDIANTES y funcionalidades de PROFESOR")
    print("Liceo Juan Bautista de Hualqui - Intranet Educativa")
    print("="*70)
    
    try:
        crear_mas_estudiantes()
        print()
        
        crear_calificaciones()
        print()
        
        crear_asistencias()
        print()
        
        crear_horarios()
        print()
        
        crear_comunicados_profesor()
        print()
        
        print("="*70)
        print("✅ Base de datos expandida exitosamente!")
        print()
        print("👥 ESTUDIANTES ADICIONALES CREADOS:")
        print("   • Camila Silva - 1° Medio A")
        print("   • Matías Ríos - 1° Medio A")
        print("   • Sofía Castro - 1° Medio B")
        print("   • Felipe Morales - 1° Medio B")
        print("   • Valentina Torres - 2° Medio A")
        print("   • Alonso Espinoza - 2° Medio A")
        print("   • Cristóbal Valenzuela - 2° Medio B")
        print("   • Alejandra Rojas - 2° Medio B")
        print()
        print("📊 FUNCIONALIDADES AGREGADAS:")
        print("   ✅ Calificaciones por asignatura y estudiante")
        print("   ✅ Registros de asistencia diarios")
        print("   ✅ Horarios de clases para profesores")
        print("   ✅ Comunicados dirigidos por tipo de usuario")
        print()
        print("🔐 USUARIOS DISPONIBLES PARA PROFESORES:")
        print("   • prof.perez / profesor123 (Con cursos asignados)")
        print("   • admin / admin123 (Administrador)")
        print("   • 13+ estudiantes para gestión de notas")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error durante la expansión: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
