import os
import sys
import django
from django.template import Template, Context, Engine
from django.template.loader import get_template
from django.conf import settings

# Setup Django
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_templates():
    print("Checking templates for syntax errors...")
    base_dir = settings.BASE_DIR
    errors = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip venv and .git
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Try to compile the template
                    Engine.get_default().from_string(content)
                    
                except Exception as e:
                    rel_path = os.path.relpath(file_path, base_dir)
                    errors.append(f"Error in {rel_path}: {str(e)}")

    if errors:
        print(f"\nFound {len(errors)} template errors:")
        for error in errors:
            print(f"- {error}")
    else:
        print("\nNo template syntax errors found.")

if __name__ == "__main__":
    check_templates()
