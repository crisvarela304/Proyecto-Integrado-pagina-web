
try:
    with open('test_output.txt', 'r', encoding='utf-16') as f:
        lines = f.readlines()
except:
    with open('test_output.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

for i, line in enumerate(lines):
    if "FieldError" in line or "Traceback" in line:
        print("".join(lines[i:i+10]))
