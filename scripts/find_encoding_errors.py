import os

def check_encoding(directory):
    print(f"Scanning {directory} for encoding issues...")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html') or file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError:
                    print(f"❌ ENCODING ERROR: {path}")

if __name__ == "__main__":
    check_encoding(r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps")
