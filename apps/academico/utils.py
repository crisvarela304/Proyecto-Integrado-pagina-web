from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    try:
        template = get_template(template_src)
        html  = template.render(context_dict)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if not pdf.err:
            return result.getvalue()
        return None
    except Exception as e:
        # Re-raise or log
        raise e

# --- REPORTLAB CERTIFICATES ---
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.utils import timezone
import io

def generar_certificado_alumno_regular(alumno):
    """Genera un PDF de alumno regular usando ReportLab"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Configuración de fuentes y diseño
    c.setTitle(f"Certificado Alumno Regular - {alumno.username}")
    
    # Encabezado
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 100, "CERTIFICADO DE ALUMNO REGULAR")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 130, "Liceo Juan Bautista de Hualqui")
    
    # Línea separadora
    c.line(100, height - 140, width - 100, height - 140)
    
    # Cuerpo
    text_y = height - 200
    c.setFont("Helvetica", 12)
    
    c.drawString(100, text_y, f"Se certifica que el alumno/a:")
    text_y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, text_y, f"{alumno.first_name} {alumno.last_name}")
    text_y -= 15
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, text_y, f"RUT: {alumno.username}") # Asumiendo username es RUT
    
    text_y -= 50
    c.setFont("Helvetica", 12)
    c.drawString(100, text_y, "Es alumno regular del establecimiento para el año escolar en curso.")
    
    # Obtener curso activo
    from .models import InscripcionCurso
    inscripcion = InscripcionCurso.objects.filter(estudiante=alumno, estado='activo').first()
    curso_nombre = inscripcion.curso.nombre if inscripcion else "Sin curso asignado"
    
    text_y -= 30
    c.drawString(100, text_y, f"Curso: {curso_nombre}")
    
    # Footer y Fecha
    text_y = 150
    fecha_hoy = timezone.now().strftime("%d de %B de %Y")
    c.drawString(100, text_y, f"Fecha de emisión: {fecha_hoy}")
    
    # Firma simulada
    c.line(width/2 - 100, 100, width/2 + 100, 100)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, 85, "Dirección Académica")
    c.drawCentredString(width/2, 70, "Liceo Juan Bautista")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer

def generar_certificado_notas(alumno):
    """Genera un informe simple de notas usando ReportLab"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setTitle(f"Informe de Notas - {alumno.username}")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 80, "INFORME DE CALIFICACIONES")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 100, f"Estudiante: {alumno.get_full_name()}")
    
    # Tabla simple de notas
    y = height - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, y, "Asignatura")
    c.drawString(350, y, "Promedio")
    c.line(70, y-5, 500, y-5)
    y -= 25
    
    c.setFont("Helvetica", 11)
    
    # Obtener notas (lógica simplificada para demo/rapidez)
    # En un caso real, esto llamaría a un servicio de cálculo de promedios
    from .models import Calificacion, Asignatura
    asignaturas = Asignatura.objects.filter(curso__inscripciones__estudiante=alumno).distinct()
    
    for asig in asignaturas:
        notas = Calificacion.objects.filter(estudiante=alumno, asignatura=asig)
        if notas.exists():
            # Calcular promedio simple
            promedio = sum([n.nota for n in notas]) / len(notas)
            c.drawString(70, y, asig.nombre[:40])
            c.drawString(350, y, f"{promedio:.1f}")
            y -= 20
            
    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, 50, "Documento generado automáticamente para fines informativos.")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
