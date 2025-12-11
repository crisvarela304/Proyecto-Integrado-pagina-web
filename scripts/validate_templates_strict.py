import os
import django
from django.conf import settings
from django.template import loader, TemplateDoesNotExist, TemplateSyntaxError
import sys

# Setup Django environment
project_root = r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web"
sys.path.append(project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def validate_templates():
    base_dir = settings.BASE_DIR
    apps_dir = os.path.join(base_dir, 'apps')
    
    error_count = 0
    checked_count = 0
    
    print(f"Scanning templates in: {apps_dir}")
    print("-" * 50)

    for root, dirs, files in os.walk(apps_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                # Calculate relative path for loader, this is a heuristic
                # Assuming standard structure apps/app_name/templates/app_name/file.html
                # We try to load by relative path from 'templates' folder
                
                rel_path = None
                if 'templates' in file_path:
                   parts = file_path.split('templates' + os.sep)
                   if len(parts) > 1:
                       rel_path = parts[1]
                
                if rel_path:
                    checked_count += 1
                    try:
                        loader.get_template(rel_path)
                        # print(f"[OK] {rel_path}")
                    except TemplateSyntaxError as e:
                        print(f"[ERROR] Syntax Error in {rel_path}")
                        print(f"  -> {str(e)}")
                        error_count += 1
                    except TemplateDoesNotExist:
                        # Sometimes paths are not directly loadable if they are partials or misaligned
                        # We try to compile the string directly as a fallback to check syntax
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            django.template.Template(content)
                            # print(f"[OK-Direct] {rel_path}")
                        except TemplateSyntaxError as e:
                             print(f"[ERROR] Syntax Error (Direct Load) in {file_path}")
                             print(f"  -> {str(e)}")
                             error_count += 1
                        except Exception as e:
                             print(f"[WARN] Could not validate {file_path}: {e}")
                    except Exception as e:
                        print(f"[ERROR] Unexpected error in {rel_path}: {e}")
                        error_count += 1

    print("-" * 50)
    print(f"Validation Complete.")
    print(f"Templates Checked: {checked_count}")
    print(f"Errors Found: {error_count}")

if __name__ == "__main__":
    validate_templates()
