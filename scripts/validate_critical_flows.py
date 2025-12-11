
import os
import sys
import django
from datetime import date

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from academico.models import Curso, Asignatura, InscripcionCurso, Calificacion
from core.models import ConfiguracionAcademica

def run_checks():
    print("--- INICIANDO VALIDACIÓN DE FLUJOS CRÍTICOS ---")
    
    # 1. Configuración Básica
    try:
        conf = ConfiguracionAcademica.get_actual()
        print(f"[OK] Configuración Académica: Año {conf.año_actual}, Semestre {conf.semestre_actual}")
    except Exception as e:
        print(f"[FAIL] Configuración Académica: {e}")
        return

    # 2. Verificar o crear Curso de prueba
    try:
        curso, _ = Curso.objects.get_or_create(
            nivel='1', letra='Z', 
            defaults={'año': conf.año_actual, 'nombre': '1° Medio Z'}
        )
        print(f"[OK] Curso de prueba verificado: {curso}")
    except Exception as e:
        print(f"[FAIL] Curso: {e}")
        return

    # 3. Flujo de Matrícula (Simulación de apps.usuarios.views)
    print("\n--- TEST: MATRÍCULA ---")
    rut_estudiante = "99.999.999-9"
    try:
        # Limpiar test previo
        User.objects.filter(username=rut_estudiante).delete()
        
        user_est = User.objects.create_user(username=rut_estudiante, password='password123')
        PerfilUsuario.objects.create(user=user_est, rut=rut_estudiante, tipo_usuario='estudiante')
        
        # EL FIX CRÍTICO: Matrícula SIN apoderado
        InscripcionCurso.objects.create(
            estudiante=user_est,
            curso=curso,
            # apoderado=None,  <-- ESTO NO DEBE ESTAR
            año=conf.año_actual,
            estado='activo'
        )
        print("[OK] Matrícula exitosa (InscripcionCurso creado sin error).")
    except TypeError as te:
        if "unexpected keyword argument 'apoderado'" in str(te):
             print("[FAIL] CRÍTICO: El error de 'apoderado' persiste en el código simulado.")
        else:
             print(f"[FAIL] Error de tipo en matrícula: {te}")
    except Exception as e:
        print(f"[FAIL] Error en matrícula: {e}")

    # 4. Asignación de Profesor y Notas
    print("\n--- TEST: PROFESOR Y NOTAS ---")
    rut_profe = "88.888.888-8"
    try:
        # Limpiar
        User.objects.filter(username=rut_profe).delete()
        
        profe = User.objects.create_user(username=rut_profe, password='password123', is_staff=True) # Staff para simplificar
        PerfilUsuario.objects.create(user=profe, rut=rut_profe, tipo_usuario='profesor')
        
        asignatura, _ = Asignatura.objects.get_or_create(codigo='MAT101', defaults={'nombre': 'Matemáticas Test'})
        
        # Calificar
        Calificacion.objects.create(
            estudiante=user_est,
            asignatura=asignatura,
            curso=curso,
            profesor=profe,
            tipo_evaluacion='nota',
            semestre='1',
            fecha_evaluacion=date.today(),
            numero_evaluacion=1,
            nota=6.5
        )
        print("[OK] Calificación creada correctamente.")
        
    except Exception as e:
        print(f"[FAIL] Error en flujo profesor/notas: {e}")

    print("\n--- FIN DE VALIDACIÓN ---")

if __name__ == "__main__":
    run_checks()
