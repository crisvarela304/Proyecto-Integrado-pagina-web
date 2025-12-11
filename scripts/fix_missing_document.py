import os
import django
import sys
from django.core.files.base import ContentFile

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from documentos.models import Documento

def fix_documento(doc_id):
    try:
        doc = Documento.objects.get(pk=doc_id)
        print(f"Checking Document ID {doc_id}: {doc.titulo}")
        
        has_file = bool(doc.archivo)
        print(f"Has file field set? {has_file}")
        
        if has_file:
            print(f"File path: {doc.archivo.path}")
            if os.path.exists(doc.archivo.path):
                print("File exists on disk.")
                if os.path.getsize(doc.archivo.path) == 0:
                    print("File is 0 bytes (empty). Recreating...")
                else:
                    print("File seems valid.")
                    return
            else:
                print("File MISSING from disk.")
        else:
            print("No file associated.")

        # Create a dummy Word doc
        print("Creating dummy Word file...")
        # A minimal RTF content masquerading as .doc or just plain text
        # Real .docx is complex, let's just make a text file with .doc extension or simple content.
        dummy_content = b"{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}} \\f0 This is a recovered document.}"
        
        filename = f"documento_recuperado_{doc_id}.doc"
        doc.archivo.save(filename, ContentFile(dummy_content))
        doc.tamaño = doc.archivo.size
        doc.save()
        
        print(f"Fixed! Assigned new file: {doc.archivo.path} ({doc.tamaño} bytes)")

    except Documento.DoesNotExist:
        print(f"Document ID {doc_id} does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_documento(2)
