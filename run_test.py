import sys
import os
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

with open('test_output_python.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    sys.stderr = f
    try:
        execute_from_command_line(['manage.py', 'test', 'apps.mensajeria', '--failfast'])
    except Exception as e:
        print(e)
