import os
import sys
import django
import re
from pathlib import Path

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

BASE_DIR = Path(settings.BASE_DIR)

def check_templates():
    print("\n🔍 AUDITORÍA DE TEMPLATES")
    print("="*50)
    
    template_errors = []
    
    for root, dirs, files in os.walk(BASE_DIR):
        if 'venv' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 1. Check for unclosed tags (basic heuristic)
                    tags = ['if', 'for', 'block', 'with']
                    for tag in tags:
                        open_count = len(re.findall(r'{%\s*' + tag + r'\s', content))
                        close_count = len(re.findall(r'{%\s*end' + tag + r'\s*%}', content))
                        
                        if open_count != close_count:
                            template_errors.append(f"❌ {file}: Desbalance de etiquetas '{tag}' (Abiertas: {open_count}, Cerradas: {close_count})")

                    # 2. Check for missing loads
                    if 'crispy' in content and '{% load crispy_forms_tags %}' not in content:
                         template_errors.append(f"⚠️ {file}: Usa crispy forms pero falta {{% load crispy_forms_tags %}}")
                    
                    if 'static' in content and '{% load static %}' not in content:
                         template_errors.append(f"⚠️ {file}: Usa static pero falta {{% load static %}}")

                except Exception as e:
                    template_errors.append(f"❌ Error leyendo {file}: {e}")

    if template_errors:
        for error in template_errors:
            print(error)
    else:
        print("✅ No se encontraron errores obvios en los templates.")

def check_code_quality():
    print("\n🔍 AUDITORÍA DE CÓDIGO (Python)")
    print("="*50)
    
    code_warnings = []
    
    for root, dirs, files in os.walk(BASE_DIR):
        if 'venv' in root or '.git' in root or 'migrations' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 1. Check for print statements (should use logging)
                    if 'print(' in content and 'scripts' not in root:
                        code_warnings.append(f"⚠️ {file}: Contiene 'print()'. Usar logging en producción.")
                        
                    # 2. Check for hardcoded secrets (basic)
                    if 'SECRET_KEY =' in content and 'config/settings.py' not in file_path:
                         code_warnings.append(f"❌ {file}: Posible SECRET_KEY hardcodeada.")

                except Exception as e:
                    pass

    if code_warnings:
        for warning in code_warnings[:10]: # Limit output
            print(warning)
        if len(code_warnings) > 10:
            print(f"... y {len(code_warnings) - 10} más.")
    else:
        print("✅ Código Python parece limpio de anti-patrones básicos.")

def check_settings():
    print("\n🔍 AUDITORÍA DE CONFIGURACIÓN")
    print("="*50)
    
    if settings.DEBUG:
        print("⚠️  DEBUG = True (Recuerda cambiar a False en producción)")
    
    if 'django.middleware.security.SecurityMiddleware' not in settings.MIDDLEWARE:
         print("❌ Falta SecurityMiddleware")
         
    # Check Database Connection
    db_conn = connections['default']
    try:
        c = db_conn.cursor()
        print("✅ Conexión a base de datos exitosa.")
    except OperationalError:
        print("❌ Error conectando a la base de datos.")

    # Check Static/Media Roots
    if not os.path.exists(settings.STATIC_ROOT) and not settings.DEBUG:
         print(f"⚠️ STATIC_ROOT no existe: {settings.STATIC_ROOT}")
         
    if not os.path.exists(settings.MEDIA_ROOT):
         print(f"⚠️ MEDIA_ROOT no existe: {settings.MEDIA_ROOT}")

    print("✅ Configuración revisada.")

if __name__ == '__main__':
    print("🚀 INICIANDO AUDITORÍA PROFUNDA DEL PROYECTO")
    check_templates()
    check_code_quality()
    check_settings()
    print("\n🏁 AUDITORÍA FINALIZADA")
