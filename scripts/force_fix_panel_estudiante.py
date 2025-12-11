import os
import re

file_path = r'C:/Users/crist/Proyecto integrado corregido/Proyecto Integrado pagina web/apps/usuarios/templates/usuarios/panel_estudiante.html'

print(f"Reading {file_path}...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: matches the specific tag, allowing for multiline whitespace
    # {{ inscripcion.curso.profesor_jefe.get_full_name|default:"Sin profesor" }}
    
    # We construct a regex that allows \s* (whitespace including newlines) around the dots and pipes
    # But specifically looking for the start and end tokens.
    
    # Simple strategy: Match {{ leading_junk inscripcion... profesor" trailing_junk }}
    pattern = r'\{\{\s*inscripcion\.curso\.profesor_jefe\.get_full_name\|default:"Sin profesor"\s*\}\}'
    
    # Broader pattern in case of very weird spacing
    pattern_generic = r'\{\{[^}]*inscripcion\.curso\.profesor_jefe\.get_full_name[^}]*\}\}'

    # Replacement: Single line, clean
    replacement = '{{ inscripcion.curso.profesor_jefe.get_full_name|default:"Sin profesor" }}'
    
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
        if "profesor_jefe" in content:
            idx = content.find("profesor_jefe")
            print(f"Context: {repr(content[idx-50:idx+100])}")

except Exception as e:
    print(f"Error: {e}")
