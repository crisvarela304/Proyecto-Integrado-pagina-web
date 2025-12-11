import os
import re

APP_DIR = r"C:\Users\crist\Proyecto integrado corregido\Proyecto Integrado pagina web\apps"

def scan_templates():
    print("[*] SCANNING TEMPLATES (Ultra Strict Mode)...")
    issues = 0
    
    # patterns
    regex_multiline = re.compile(r'\{\{[^}]*[\n\r]+[^}]*\}\}')
    regex_no_spaces = re.compile(r'{%\s*if\s+.*[^ ]==[^ ].*\s*%}') # if x==y
    regex_bad_quote = re.compile(r"value\s*=\s*['\"]\{\{.*default:['\"]\s*\}\}['\"]") # default:' }} typo
    
    for root, dirs, files in os.walk(APP_DIR):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, APP_DIR)
                
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.splitlines()
                except UnicodeDecodeError:
                    print(f"[X] [ENCODING] {rel_path}: File is not valid UTF-8!")
                    issues += 1
                    continue

                # 1. Check for Multi-line tags (The "Letras Raras" cause)
                if regex_multiline.search(content):
                    print(f"[!] [RISKY TAG] {rel_path}: Found variable tag split across lines.")
                    issues += 1

                # 2. Check for Syntax logic (spaces)
                for i, line in enumerate(lines):
                    if "==" in line and "{%" in line:
                         if re.search(r'[^ ]==|==[^ ]', line):
                             print(f"[!] [SYNTAX] {rel_path}:{i+1}: Missing space around '==' operator.")
                             issues += 1
                
                # 3. Check for Unclosed Braces count
                if content.count('{{') != content.count('}}'):
                    print(f"[X] [UNBALANCED] {rel_path}: Unequal curly braces {{ }} count.")
                    issues += 1

    return issues

def scan_python():
    print("\n[*] SCANNING PYTHON CODE (Professional Standards)...")
    issues = 0
    
    for root, dirs, files in os.walk(APP_DIR):
        for file in files:
            if file.endswith(".py") and "migrations" not in root:
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, APP_DIR)
                
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    # 1. Leftover Debugging
                    if "print(" in line.strip() and not line.strip().startswith('#'):
                        print(f"[!] [CLEANUP] {rel_path}:{i+1}: Leftover 'print()' statement.")
                        issues += 1
                    
                    # 2. Hardcoded Paths
                    if "C:\\Users" in line:
                        print(f"[X] [HARDCODED] {rel_path}:{i+1}: Hardcoded absolute path found.")
                        issues += 1
                        
    return issues

if __name__ == "__main__":
    t_issues = scan_templates()
    p_issues = scan_python()
    
    total = t_issues + p_issues
    print(f"\n[=] Ultra Scan Complete. Issues found: {total}")
