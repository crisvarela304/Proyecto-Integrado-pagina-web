
import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from administrativo.models import RegistroActividad
from administrativo.services import LiceoOSService

def verify_logging():
    print("--- VERIFICANDO SISTEMA DE LOGS ---")
    
    # 1. Crear usuario dummy
    user, _ = User.objects.get_or_create(username='log_tester')
    
    # 2. Registrar evento manualmente
    print("Intentando registrar evento...")
    LiceoOSService.registrar_evento(
        usuario=user,
        tipo_accion='test',
        descripcion='Evento de prueba del sistema de logs',
        detalles='Detalles técnicos de prueba'
    )
    
    # 3. Verificar persistencia
    ultimo_log = RegistroActividad.objects.filter(usuario=user).first()
    
    if ultimo_log:
        print(f"[OK] Log encontrado: {ultimo_log.descripcion}")
        print(f"     Fecha: {ultimo_log.fecha}")
        print(f"     Tipo: {ultimo_log.tipo_accion}")
    else:
        print("[FAIL] No se encontró el log en la base de datos.")
        
    # 4. Verificar recuperación para dashboard
    logs_recientes = LiceoOSService.get_historial_actividad(limite=5)
    print(f"\n[OK] Logs recientes recuperados: {len(logs_recientes)}")
    for log in logs_recientes:
        print(f" - {log}")

if __name__ == "__main__":
    verify_logging()
