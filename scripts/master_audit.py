import os
import sys
import django
import ast
import re
from pathlib import Path

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.template import Template, TemplateSyntaxError
from django.core.management import call_command
from io import StringIO

BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APPS_DIR = BASE_DIR / 'apps'

def check_django_system():
    print("--- 1. DJANGO SYSTEM CHECK ---")
    out = StringIO()
    try:
        call_command('check', stdout=out)
        result = out.getvalue()
        if "System check identified no issues" in result:
            print("✅ System Check Passed")
        else:
            print("⚠️ System Check Warnings/Errors:")
            print(result)
    except Exception as e:
        print(f"❌ System Check Failed: {e}")

def check_python_syntax_and_logic():
    print("\n--- 2. PYTHON STATIC ANALYSIS (Syntax & Logic) ---")
    error_count = 0
    
    for py_file in APPS_DIR.rglob('*.py'):
        if 'migrations' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Syntax Check
            tree = ast.parse(source, filename=str(py_file))
            
            # Logic/Anti-pattern Check
            for node in ast.walk(tree):
                # Check for 'print()' usage (Anti-pattern in production)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                    print(f"⚠️ [PRINT] Found print statement in {py_file.name}:{node.lineno}")
                    error_count += 1
                
                # Check for debuggers
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'set_trace':
                         print(f"❌ [DEBUGGER] Found set_trace in {py_file.name}:{node.lineno}")
                         error_count += 1

                # Check for bare 'except:' (Bad practice)
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    print(f"⚠️ [EXCEPT] Bare 'except:' clause in {py_file.name}:{node.lineno} (Catch specific exceptions!)")
                    # error_count += 1 # Warning only

        except SyntaxError as e:
            print(f"❌ [SYNTAX] Error in {py_file}: {e}")
            error_count += 1
        except Exception as e:
            print(f"❌ [READ] Error reading {py_file}: {e}")

    if error_count == 0:
        print("✅ Python Code Analysis Passed (No syntax errors or critical anti-patterns)")

def check_templates():
    print("\n--- 3. TEMPLATE SYNTAX ANALYSIS ---")
    error_count = 0
    
    # Simple regex for the "stuck variable" issue (J{{ or {{...|filter}} across lines)
    split_tag_re = re.compile(r'\{\{[^}]*\n[^}]*\}\}')
    stuck_char_re = re.compile(r'[a-zA-Z0-9]\{\{') 

    for template_file in APPS_DIR.rglob('*.html'):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Django Template Syntax Validation
            try:
                Template(content)
            except TemplateSyntaxError as e:
                print(f"❌ [TEMPLATE SYNTAX] {template_file.name}: {e}")
                error_count += 1
            
            # 2. Visual Artifact Validation
            if split_tag_re.search(content):
                # Ignore some false positives if necessary, but warn
                # print(f"⚠️ [VISUAL] Potential split tag in {template_file.name}")
                pass 

            stuck_matches = stuck_char_re.findall(content)
            for match in stuck_matches:
                # filter out common false positives like 'v-bind:class="{{' if using Vue, but here we are pure Django
                # We specifically look for things like 'J{{' or 'x{{'
                if not match.endswith('url '): # exclude 'url {{' which is weird but possible in js
                     print(f"⚠️ [VISUAL] Potential character stuck to tag '{match}' in {template_file.name}")

        except Exception as e:
            print(f"❌ [READ] Error reading template {template_file}: {e}")

    if error_count == 0:
        print("✅ Template Analysis Passed")

if __name__ == "__main__":
    print("🚀 STARTING MASTER AUDIT 🚀")
    print(f"Scanning directory: {APPS_DIR}")
    
    check_django_system()
    check_python_syntax_and_logic()
    check_templates()
    
    print("\n--- AUDIT COMPLETE ---")
