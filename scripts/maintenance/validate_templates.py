import os
import sys
import django
from django.conf import settings
from django.template import Template, Context, TemplateSyntaxError

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def validate_templates():
    print(f"DEBUG: settings.BASE_DIR is {settings.BASE_DIR}")
    apps_dir = os.path.join(settings.BASE_DIR, 'apps')
    print(f"Starting Template Validation in: {apps_dir}")
    
    errors = []
    checked_count = 0
    
    for root, dirs, files in os.walk(apps_dir):
        for file in files:
            if file.endswith('.html'):
                checked_count += 1
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Compile template
                    template = Template(content)
                    
                except TemplateSyntaxError as e:
                    errors.append(f"❌ Syntax Error in {os.path.relpath(full_path, project_root)}: {e}")
                except Exception as e:
                    errors.append(f"⚠️  Error reading {os.path.relpath(full_path, project_root)}: {e}")
    
    report_path = os.path.join(project_root, 'validation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"Authorization complete. Checked {checked_count} files. Found {len(errors)} errors.\n")
        if errors:
            f.write("\n".join(errors))
        else:
            f.write("All templates valid.")
            
    print(f"Analyzed {checked_count} templates. Found {len(errors)} errors. See: validation_report.txt")

if __name__ == '__main__':
    validate_templates()
