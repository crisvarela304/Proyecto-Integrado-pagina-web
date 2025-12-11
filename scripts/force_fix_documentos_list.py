import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/documentos/templates/documentos/documentos_list.html'

print(f"Reading {file_path}...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: {{ [whitespace] documento.creado_por.get_full_name|default:documento.creado_por.username [whitespace] }}
    # Using generic pattern to catch split lines
    pattern = r'\{\{\s*documento\.creado_por\.get_full_name\|default:documento\.creado_por\.username\s*\}\}'
    pattern_generic = r'\{\{[^}]*documento\.creado_por\.get_full_name[^}]*\}\}'

    # Replacement: Single line
    replacement = '{{ documento.creado_por.get_full_name|default:documento.creado_por.username }}'
    
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("Specific pattern not found. Trying generic...")
        match = re.search(pattern_generic, content, re.DOTALL)

    if match:
        print(f"Found match: {match.group(0)!r}")
        new_content = content.replace(match.group(0), replacement)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")
    else:
        print("No broken tags found.")
        if "creado_por" in content:
            idx = content.find("creado_por")
            print(f"Context: {repr(content[idx-50:idx+100])}")

except Exception as e:
    print(f"Error: {e}")
