import os
import sys
import django
import re
from django.template.loader import get_template
from django.conf import settings

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_system():
    print("--- 1. DJANGO SYSTEM CHECK ---")
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    try:
        call_command('check', stdout=out, stderr=out)
        output = out.getvalue()
        if "System check identified no issues" in output:
            print("min: ✅ System check passed.")
        else:
            print(f"⚠️ System check found issues:\n{output}")
    except Exception as e:
        print(f"❌ System check failed: {e}")

def validate_templates(apps_dir):
    print("\n--- 2. TEMPLATE SYNTAX VALIDATION ---")
    errors = []
    checked_count = 0
    
    for root, dirs, files in os.walk(apps_dir):
        for file in files:
            if file.endswith('.html'):
                checked_count += 1
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, apps_dir)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Just try to compile it
                    # We need a template name relative to loaders, but we can try manual compile
                    # Or simpler: load by path? No, standard loaded is better.
                    # Let's rely on standard engine loading via get_template if possible
                    # But get_template needs 'app/template.html' name. 
                    # We can iterate specifically through known app templates or just compile string.
                    from django.template import Template, Context
                    Template(content) # This checks syntax
                except Exception as e:
                    errors.append(f"❌ {rel_path}: {e}")
    
    print(f"Checked {checked_count} templates.")
    if errors:
        for e in errors:
            print(e)
    else:
        print("✅ No syntax errors found.")

def scan_visual_issues(apps_dir):
    print("\n--- 3. DEEP SCAN FOR VISUAL/SPLIT TAGS ---")
    issues = []
    
    # Pattern for {{ ... }} that is NOT closed on the same line
    # We look for {{ that isn't followed by }} within the same line
    split_tag_pattern = re.compile(r'\{\{(?!.*\}\})')
    
    for root, dirs, files in os.walk(apps_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, apps_dir)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        if split_tag_pattern.search(line):
                            # Exclude some false positives if necessary (e.g. JS objects usually use { not {{)
                            # But Django uses {{. 
                            issues.append(f"⚠️ {rel_path}:{i+1} - Potential split tag found: {line.strip()[:40]}...")
                            
                        # Pattern for split block tags {% ... %}
                        if '{%' in line and '%}' not in line:
                            # block/endblock are often fine on their own line? No, {% block x %} is one line.
                            # split block is like "{% if \n x %}" which is arguably ugly but valid syntax,
                            # BUT in this project it caused literal rendering.
                            issues.append(f"⚠️ {rel_path}:{i+1} - Potential split block found: {line.strip()[:40]}...")

                except Exception as e:
                    pass
                    
    if issues:
        print(f"Found {len(issues)} potential visual issues:")
        for i in issues:
            print(i)
    else:
        print("✅ No visual split-tag issues found.")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    apps_dir = os.path.join(base_dir, 'apps')
    
    # Redirect stdout to a file for review
    log_path = os.path.join(base_dir, 'audit_results.md')
    with open(log_path, 'w', encoding='utf-8') as f:
        sys.stdout = f
        check_system()
        validate_templates(apps_dir)
        scan_visual_issues(apps_dir)
    pass
