
import os
import re
import sys
from pathlib import Path

# Setup simple Django-like environment detection
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Colors for terminal
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def color_print(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

# 1. FIND ALL TEMPLATE FILES
def get_all_templates():
    templates = set()
    for root, dirs, files in os.walk(BASE_DIR):
        if 'venv' in root or '.git' in root: continue
        for file in files:
            if file.endswith('.html'):
                # Store relative path from templates folder if possible
                full_path = Path(root) / file
                # Try to normalize to what Django expects (e.g. 'usuarios/login.html')
                # Heuristic: look for 'templates' in path
                parts = full_path.parts
                if 'templates' in parts:
                    idx = parts.index('templates')
                    rel_path = "/".join(parts[idx+1:])
                    templates.add(rel_path)
    return templates

# 2. FIND TEMPLATE REFERENCES IN CODE
def find_template_references():
    references = []
    
    # Regex patterns
    patterns = [
        (r"render\s*\(\s*request\s*,\s*['\"]([^'\"]+\.html)['\"]", "View render"),
        (r"template_name\s*=\s*['\"]([^'\"]+\.html)['\"", "Class View"),
        (r"include\s+['\"]([^'\"]+\.html)['\"]", "Template Include"),
        (r"extends\s+['\"]([^'\"]+\.html)['\"]", "Template Extends")
    ]
    
    for root, dirs, files in os.walk(BASE_DIR):
        if 'venv' in root or '.git' in root: continue
        
        for file in files:
            if file.endswith(('.py', '.html')):
                path = Path(root) / file
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        for pat, type_ in patterns:
                            matches = re.finditer(pat, content)
                            for m in matches:
                                ref = m.group(1)
                                references.append({
                                    'file': str(path),
                                    'ref': ref,
                                    'type': type_
                                })
                except:
                    pass
    return references

def audit_templates():
    color_print("\n🔎 AUDITORÍA DE TEMPLATES FALTANTES", color=YELLOW)
    existing_templates = get_all_templates()
    references = find_template_references()
    
    issues = 0
    for ref in references:
        # Normalize ref (replace \ with /)
        target = ref['ref'].replace('\\', '/')
        
        # Check exact match
        if target not in existing_templates:
            # Check if it might be a partial path issue, but strict check is better
            color_print(f"❌ '{target}' referenciado en {Path(ref['file']).name} ({ref['type']}) NO FUE ENCONTRADO.", RED)
            issues += 1
            
    if issues == 0:
        color_print("✅ Todas las referencias a templates parecen válidas.", GREEN)

# 3. SECURITY SCAN
def audit_security():
    color_print("\n🛡️ AUDITORÍA DE SEGURIDAD Y CALIDAD", color=YELLOW)
    
    suspicious_patterns = [
        (r"csrf_exempt", "Uso de csrf_exempt (Riesgo CSRF)"),
        (r"\|safe", "Uso de filtro |safe (Riesgo XSS)"),
        (r"mark_safe", "Uso de mark_safe (Riesgo XSS)"),
        (r"eval\(", "Uso de eval() (Ejecución Arbitraria)"),
        (r"exec\(", "Uso de exec() (Ejecución Arbitraria)"),
        (r"pdb\.set_trace", "Debugger pdb olvidado"),
        (r"print\(", "Uso de print() (Usar logger)"),
        (r"except\s*:", "Except genérico desnudo (Oculta errores)"),
        (r"raw\(", "SQL Crudo (Posible Inyección SQL)"),
    ]
    
    for root, dirs, files in os.walk(BASE_DIR):
        if 'venv' in root or '.git' in root or 'scripts' in root: continue
        
        for file in files:
            if file.endswith(('.py', '.html')):
                path = Path(root) / file
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    for i, line in enumerate(lines):
                        for pat, desc in suspicious_patterns:
                            if re.search(pat, line):
                                # Ignore migrations and tests usually
                                if 'migrations' in str(path) or 'tests' in str(path): continue
                                
                                color_print(f"⚠️ {path.name}:{i+1} -> {desc}", RED)
                                print(f"   Contexto: {line.strip()[:100]}")
                except:
                    pass

if __name__ == "__main__":
    audit_templates()
    audit_security()
