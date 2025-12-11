import os
import sys
import re
import django
from django.conf import settings
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def get_all_url_names():
    """Recursively fetch all registered URL names (with namespaces)."""
    url_names = set()
    resolver = get_resolver()
    
    def _extract_names(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if isinstance(pattern, URLPattern):
                if pattern.name:
                    full_name = f"{prefix}:{pattern.name}" if prefix else pattern.name
                    url_names.add(full_name)
                    # Also add non-namespaced version if it's in root (though less common with include)
            elif isinstance(pattern, URLResolver):
                # Check for namespace
                new_prefix = prefix
                if pattern.namespace:
                     new_prefix = f"{prefix}:{pattern.namespace}" if prefix else pattern.namespace
                
                _extract_names(pattern.url_patterns, new_prefix)

    _extract_names(resolver.url_patterns)
    return url_names

def find_url_usages(apps_dir):
    """Scan templates for {% url 'name' ... %} usages."""
    usages = []
    # Regex to capture: {% url 'view_name' ... %} or {% url "view_name" ... %}
    # handling optional spaces
    url_pattern = re.compile(r'{%\s*url\s+[\'"]([\w:-]+)[\'"]\s*')
    
    for root, dirs, files in os.walk(apps_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for i, line in enumerate(content.split('\n')):
                        matches = url_pattern.findall(line)
                        for match in matches:
                            usages.append({
                                'file': path,
                                'line': i + 1,
                                'url_name': match
                            })
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    return usages

def main():
    print("Collecting valid URL names...")
    valid_names = get_all_url_names()
    print(f"Found {len(valid_names)} valid URL patterns.")
    # for name in sorted(valid_names):
    #     print(f"  - {name}")

    print("\nScanning templates for URL usages...")
    apps_dir = os.path.join(settings.BASE_DIR, 'apps')
    usages = find_url_usages(apps_dir)
    print(f"Found {len(usages)} URL references in templates.")

    errors = 0
    print("\nChecking for broken links...")
    print("-" * 60)
    
    # Exceptions that might be dynamic or internal
    ignored = {'admin:index', 'admin:password_change', 'admin:logout'} 

    for usage in usages:
        name = usage['url_name']
        if name not in valid_names and name not in ignored:
            # Try fuzzy match? No, strict for now.
            print(f"[ERROR] Invalid URL: '{name}'")
            print(f"        File: {os.path.relpath(usage['file'], project_root)}")
            print(f"        Line: {usage['line']}")
            errors += 1

    if errors == 0:
        print("\n✅ All template URL references match valid views!")
    else:
        print(f"\n❌ Found {errors} broken URL references.")

if __name__ == '__main__':
    main()
