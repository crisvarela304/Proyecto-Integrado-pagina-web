
import re
import os

file_path = r'c:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/administrativo/templates/administrativo/dashboard.html'

def fix_file():
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix 1: Join split {{ ... }} tags
    # Looks for {{ followed by newline and whitespace, captures content, then }}
    # We replace it with {{ content }} (stripping extra whitespace)
    
    # Pattern for the Name tag split
    # {{ alerta.estudiante.first_name|first }}{{
    #                                                     alerta.estudiante.last_name|first }}
    
    # Specific fix for the name part which is very specific
    content = re.sub(
        r'\{\{\s*alerta\.estudiante\.first_name\|first\s*\}\}\s*\{\{\s*\n\s*alerta\.estudiante\.last_name\|first\s*\}\}', 
        r'{{ alerta.estudiante.first_name|first }}{{ alerta.estudiante.last_name|first }}', 
        content
    )

    # General fix for other split tags like {{ motivo }}
    # Matches {{ [newline] [spaces] content [newline/spaces] }}
    def replacer(match):
        inner = match.group(1).strip()
        return f"{{{{ {inner} }}}}"

    content = re.sub(r'\{\{\s*\n\s*(.*?)\s*\}\}', replacer, content, flags=re.DOTALL)
    
    # Additional cleanup for the specific broken span if regex didn't catch it perfectly
    content = content.replace(
        'class="badge bg-danger bg-opacity-10 text-danger border border-danger">{{\n                                                motivo }}</span>',
        'class="badge bg-danger bg-opacity-10 text-danger border border-danger">{{ motivo }}</span>'
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully fixed dashboard.html syntax.")

if __name__ == "__main__":
    fix_file()
