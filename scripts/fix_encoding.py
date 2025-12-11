import os

def fix_file_encoding():
    file_path = r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps\comunicacion\templates\comunicacion\noticias_list.html"
    try:
        # Try reading with latin-1 or cp1252 to capture non-utf8 bytes
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        
        # Write back as utf-8
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Converted {file_path} to UTF-8")
    except Exception as e:
        print(f"❌ Failed to convert: {e}")

if __name__ == "__main__":
    fix_file_encoding()
