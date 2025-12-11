import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/academico/templates/academico/recursos/gestionar_recursos.html'

print(f"Reading {file_path}...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find the broken tag with any amount of whitespace/newlines
    # Pattern: {{ recurso.archivo.size|filesizeformat [whitespace] }}
    pattern = r'\{\{\s*recurso\.archivo\.size\|filesizeformat\s*\}\}'
    
    # Replacement: Single line, clean
    replacement = '{{ recurso.archivo.size|filesizeformat }}'
    
    new_content, count = re.subn(pattern, replacement, content)

    if count > 0:
        print(f"Found {count} broken tags. Fixing...")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")
    else:
        print("No broken tags found (or regex didn't match).")
        # Fallback debug
        if "filesizeformat" in content:
            print("Warning: 'filesizeformat' exists but regex missed it. Context:")
            start = content.find("filesizeformat") - 20
            end = content.find("filesizeformat") + 50
            print(repr(content[start:end]))

except Exception as e:
    print(f"Error: {e}")
