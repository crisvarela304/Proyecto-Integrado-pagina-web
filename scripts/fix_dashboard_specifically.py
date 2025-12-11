import os
import re

TARGET_FILE = r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps\administrativo\templates\administrativo\dashboard.html"

def fix_dashboard():
    if not os.path.exists(TARGET_FILE):
        print(f"File not found: {TARGET_FILE}")
        return

    print(f"Reading {TARGET_FILE}...")
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    original_len = len(content)
    
    # 1. Fix the "J{{ ... }}" artifact by normalizing the Student Initials block
    # We look for the general pattern of first_name|first followed by last_name|first, possibly separated by garbage
    
    # Pattern: {{ ...first_name|first }} [junk] {{ ...last_name|first }}
    initials_pattern = re.compile(
        r'\{\{\s*alerta\.estudiante\.first_name\|first\s*\}\}\s*\{\{\s*alerta\.estudiante\.last_name\|first\s*\}\}', 
        re.DOTALL | re.IGNORECASE
    )
    
    # Replace with clean single line
    content = initials_pattern.sub(
        r'{{ alerta.estudiante.first_name|first }}{{ alerta.estudiante.last_name|first }}', 
        content
    )
    
    # 2. Fix the "naturaltime" artifact
    # Pattern: {{ [junk] actividad.fecha|naturaltime [junk] }}
    naturaltime_pattern = re.compile(
        r'\{\{\s*actividad\.fecha\|naturaltime\s*\}\}', 
        re.DOTALL | re.IGNORECASE
    )
    content = naturaltime_pattern.sub(r'{{ actividad.fecha|naturaltime }}', content)

    # 3. Fix the "motivo" loop artifact
    # Pattern: {{ [junk] motivo [junk] }}
    motivo_pattern = re.compile(r'\{\{\s*motivo\s*\}\}', re.DOTALL | re.IGNORECASE)
    content = motivo_pattern.sub(r'{{ motivo }}', content)

    # 4. Aggressive cleanup of ANY {{ }} tag that spans multiple lines
    def clean_multiline_tags(match):
        tag = match.group(0)
        if '\n' in tag:
            print(f"Collapsing multiline tag: {tag[:40]}...")
            return re.sub(r'\s+', ' ', tag)
        return tag

    content = re.sub(r'\{\{[^}]+\}\}', clean_multiline_tags, content)

    if len(content) != original_len or content != open(TARGET_FILE, 'r', encoding='utf-8').read():
        print("Changes detected. Writing fix...")
        with open(TARGET_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Dashboard fixed successfully.")
    else:
        print("No matches found or file already clean. (This might indicate the patterns didn't match the bad content)")

if __name__ == "__main__":
    fix_dashboard()
