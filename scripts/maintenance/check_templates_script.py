import os
import django
from django.conf import settings
from django.template import loader, TemplateDoesNotExist, TemplateSyntaxError

import sys
# Agregar directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_templates():
    print("Iniciando validación de templates...")
    with open('validation_results.txt', 'w', encoding='utf-8') as log:
        log.write("Iniciando validación...\n")
        
    base_dir = settings.BASE_DIR
    templates_checked = 0
    errors_found = 0

    # Recorrer todos los directorios del proyecto
    for root, dirs, files in os.walk(base_dir):
        # Ignorar venv y .git
        if 'venv' in root or '.git' in root or 'node_modules' in root:
            continue
            
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                # Intentar cargar el template
                try:
                    # Usamos una ruta relativa para simular cómo lo carga Django
                    rel_path = os.path.relpath(file_path, base_dir)
                    
                    # Hack: si el archivo está en una carpeta 'templates', tratamos de cargar desde ahí
                    if 'templates' in rel_path:
                        # Extraer la parte después de 'templates/'
                        parts = rel_path.split(os.sep)
                        try:
                            idx = parts.index('templates')
                            template_name = os.path.join(*parts[idx+1:])
                            
                            # Intentar cargar
                            loader.get_template(template_name)
                            templates_checked += 1
                        except (ValueError, IndexError):
                            pass
                        except TemplateDoesNotExist:
                            # Puede ser un partial o estar en una ruta no estándar, intentamos leerlo directo
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                try:
                                    django.template.Template(content)
                                    templates_checked += 1
                                except TemplateSyntaxError as e:
                                    msg = f"❌ Error de sintaxis en {rel_path}: {e}"
                                    print(msg)
                                    with open('validation_results.txt', 'a', encoding='utf-8') as log:
                                        log.write(f"{msg}\n")
                                    errors_found += 1
                        except TemplateSyntaxError as e:
                            msg = f"❌ Error de sintaxis en {template_name} ({rel_path}): {e}"
                            print(msg)
                            with open('validation_results.txt', 'a', encoding='utf-8') as log:
                                log.write(f"{msg}\n")
                            errors_found += 1
                    
                except Exception as e:
                    msg = f"⚠️ Error procesando {file}: {e}"
                    print(msg)
                    with open('validation_results.txt', 'a', encoding='utf-8') as log:
                        log.write(f"{msg}\n")

    print(f"\nResumen: {templates_checked} templates verificados. {errors_found} errores encontrados.")
    with open('validation_results.txt', 'a', encoding='utf-8') as log:
        log.write(f"\nResumen: {templates_checked} templates verificados. {errors_found} errores encontrados.\n")

if __name__ == '__main__':
    check_templates()
