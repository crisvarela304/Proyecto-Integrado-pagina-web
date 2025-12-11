
try:
    with open('test_output.txt', 'r', encoding='utf-16') as f:
        content = f.read()
except:
    with open('test_output.txt', 'r', encoding='utf-8') as f:
        content = f.read()

print(content)
