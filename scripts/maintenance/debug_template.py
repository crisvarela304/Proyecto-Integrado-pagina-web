import os
import sys
import django
from django.template.loader import get_template

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    t = get_template('academico/profesor_mis_estudiantes.html')
    print("TEMPLATE COMPILED SUCCESSFULLY")
except Exception as e:
    print(f"TEMPLATE ERROR: {e}")
    # Print the line number if available
    if hasattr(e, 'django_template_source'):
         print(e.django_template_source[1])
