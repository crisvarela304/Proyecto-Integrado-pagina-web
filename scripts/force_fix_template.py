import os
import re

def fix_template():
    file_path = r'C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps\administrativo\templates\administrativo\historial_actividad.html'
    
    print(f"Reading file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the problematic block pattern (multiline or single line)
    # We want to replace the whole User block inside the <td>
    
    # Target: 
    # div with class fw-bold small
    # FOLLOWED BY
    # small with class text-muted
    
    # We will search for the specific lines we want to fix
    
    # Regex to find the name block
    # It might look like: <div class="fw-bold small">...</div>\n<small class="text-muted"...>...</small>
    
    # We will just replace the specific sensitive parts to be safe
    
    # Fix 1: The Full Name / Username fallback
    # Match: <div class="fw-bold small">...</div>
    regex_name = r'<div class="fw-bold small">\s*(?:\{\%.*?\%\}|{{).*?(?:\{\%.*?\%\}|}})\s*</div>'
    
    replacement_name = '<div class="fw-bold small">{{ log.usuario.get_full_name|default:log.usuario.username }}</div>'
    
    new_content = re.sub(regex_name, replacement_name, content, flags=re.DOTALL)
    
    # Fix 2: The Username handle
    # Match: <small class="text-muted" style="font-size:0.75rem">...{{...}}...</small>
    regex_handle = r'<small class="text-muted" style="font-size:0.75rem">\s*@?\{\{.*?\}\}\s*</small>'
    
    replacement_handle = '<small class="text-muted" style="font-size:0.75rem">@{{ log.usuario.username }}</small>'
    
    new_content = re.sub(regex_handle, replacement_handle, new_content, flags=re.DOTALL)

    if content != new_content:
        print("Found patterns and replaced them.")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ File updated successfully.")
    else:
        print("⚠️ No changes made. Patterns might not match.")
        # Fallback: Force write the specific string if we can identify the location context
        if 'log.usuario.get_full_name' in content:
             print("Content exists but regex missed. Using direct string replacement of known bad blocks if possible.")

if __name__ == '__main__':
    fix_template()
