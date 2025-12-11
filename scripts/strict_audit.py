import os
import ast
import sys

def check_file(filepath):
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError as e:
            return [f"SYNTAX ERROR: {e}"]

    for node in ast.walk(tree):
        # Check for print()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
            issues.append(f"Line {node.lineno}: found print() statement. Use logging instead.")
        
        # Check for bare except: pass
        if isinstance(node, ast.ExceptHandler):
            if node.type is None: # Bare except
                issues.append(f"Line {node.lineno}: found bare 'except:'. Catch specific exceptions.")
            
            # Check for silent pass in except
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                 issues.append(f"Line {node.lineno}: found 'except ...: pass'. Silent failure risk.")

    return issues

def scan_project(root_dir):
    print(f"Scanning {root_dir}...")
    issues_found = 0
    for root, dirs, files in os.walk(root_dir):
        if 'migrations' in root or 'scripts' in root or 'venv' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                file_issues = check_file(path)
                if file_issues:
                    print(f"\n[FILE] {path}")
                    for issue in file_issues:
                        print(f"  - {issue}")
                        issues_found += 1
    
    if issues_found == 0:
        print("\n[OK] Great! No critical code quality issues found.")
    else:
        print(f"\n[WARN] Found {issues_found} potential issues.")

if __name__ == "__main__":
    scan_project(os.getcwd())
