import os
import re

# Target files
FILES_TO_FIX = [
    r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps\usuarios\templates\usuarios\panel_profesor.html",
    r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps\academico\templates\academico\profesor_gestionar_calificaciones.html",
    r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps\usuarios\templates\usuarios\panel_estudiante.html"
]

def fix_split_tags(file_path):
    print(f"Propagating fixes to: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generic fix for {{ variable }} split across lines
    pattern = r'\{\{([^}]+?)\}\}'
    
    def intelligent_replacer(match):
        full_tag = match.group(0)
        # Verify if it contains newlines or excessive inner spacing that looks like a split
        if '\n' in full_tag:
            print(f"Fixing literal tag: {full_tag[:40]}...")
            inner = match.group(1)
            # Flatten to single line
            clean_inner = re.sub(r'\s+', ' ', inner).strip()
            return f"{{{{ {clean_inner} }}}}"
        return full_tag

    new_content = re.sub(pattern, intelligent_replacer, content, flags=re.DOTALL)
    
    # Also fix {% tag %} split across lines
    block_pattern = r'\{%([^%]+?)%\}'
    def block_replacer(match):
        full_tag = match.group(0)
        if '\n' in full_tag:
            print(f"Fixing block tag: {full_tag[:40]}...")
            inner = match.group(1)
            clean_inner = re.sub(r'\s+', ' ', inner).strip()
            return f"{{% {clean_inner} %}}"
        return full_tag

    new_content = re.sub(block_pattern, block_replacer, new_content, flags=re.DOTALL)

    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully fixed split tags.")
    else:
        print("No split tags found to fix.")

if __name__ == "__main__":
    for file_path in FILES_TO_FIX:
        fix_split_tags(file_path)
