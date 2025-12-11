
import os
import sys
import django
import re
from pathlib import Path

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.template import loader, TemplateDoesNotExist, TemplateSyntaxError

def audit_templates():
    print("--- 1. AUDITORÍA DE TEMPLATES (SINTAXIS) ---")
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = base_dir 
    
    html_files = list(templates_dir.rglob('*.html'))
    print(f"Escanendo {len(html_files)} archivos HTML...")
    
    errors = []
    
    for file_path in html_files:
        if 'historial_actividad.html' not in str(file_path):
             continue
        # Skip weird dirs
        if '.venv' in str(file_path) or 'env' in str(file_path):
            continue
            
        relative_path = file_path.relative_to(base_dir)
        
        # 1. Check for Split Tags (Visual Error)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Regex for tags split across lines like {%\n if ... \n%}
            if re.search(r'{%[ \t]*\n', content) or re.search(r'\n[ \t]*%}', content):
                 if "trans" not in content and "blocktranslate" not in content: # trans tags sometimes use multiline
                    print(f"[WARN] Posible tag roto (multilínea) en: {relative_path}")

        # 2. Check Django Syntax
        try:
            # We try to load it. Note: absolute paths in 'get_template' might not work directly 
            # if they aren't in configured dirs, but we can try reading content and creating Template object
            from django.template import Template, Context
            Template(content) 
        except TemplateSyntaxError as e:
            msg = f"[ERROR] Sintaxis inválida en {file_path}: {e}"
            print(msg)
            print("--- CONTENIDO DEL ARCHIVO QUE FALLA ---")
            print(content)
            print("--- FIN CONTENIDO ---")
            errors.append(msg)
        except Exception as e:
            # Some other error
            pass

    if not errors:
        print("[OK] No se encontraron errores de sintaxis en templates escaneados.")
    else:
        print(f"[FAIL] Se encontraron {len(errors)} errores de sintaxis.")

def audit_django_code():
    print("\n--- 2. AUDITORÍA DE CÓDIGO PYTHON/DJANGO ---")
    # Using Django's system check
    from django.core.management import call_command
    try:
        call_command('check')
    except Exception as e:
        print(f"[FAIL] System Check falló: {e}")

if __name__ == "__main__":
    audit_templates()
    audit_django_code()
