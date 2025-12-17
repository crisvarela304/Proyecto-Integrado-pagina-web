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


def generar_reporte_asistencia(alumno, fecha_inicio=None, fecha_fin=None):
    """Genera un informe PDF de asistencia del estudiante"""
    from datetime import date, timedelta
    from .models import Asistencia, InscripcionCurso
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setTitle(f"Reporte de Asistencia - {alumno.username}")
    
    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 60, "REPORTE DE ASISTENCIA")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 80, "Liceo Juan Bautista de Hualqui")
    
    # Línea
    c.line(70, height - 90, width - 70, height - 90)
    
    # Datos del estudiante
    y = height - 120
    c.setFont("Helvetica", 11)
    c.drawString(70, y, f"Estudiante: {alumno.get_full_name()}")
    y -= 20
    rut = getattr(alumno.perfil, 'rut', alumno.username) if hasattr(alumno, 'perfil') else alumno.username
    c.drawString(70, y, f"RUT: {rut}")
    
    # Curso
    inscripcion = InscripcionCurso.objects.filter(estudiante=alumno, estado='activo').first()
    y -= 20
    if inscripcion:
        c.drawString(70, y, f"Curso: {inscripcion.curso.nombre}")
    
    # Rango de fechas
    if not fecha_inicio:
        fecha_inicio = date.today().replace(day=1)
    if not fecha_fin:
        fecha_fin = date.today()
    
    y -= 30
    c.drawString(70, y, f"Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
    
    # Obtener asistencias
    asistencias = Asistencia.objects.filter(
        estudiante=alumno,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).order_by('-fecha')
    
    total = asistencias.count()
    presentes = asistencias.filter(estado='presente').count()
    ausentes = asistencias.filter(estado='ausente').count()
    tardanzas = asistencias.filter(estado='tardanza').count()
    porcentaje = round((presentes / total * 100), 1) if total > 0 else 100
    
    # Estadísticas
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, y, "RESUMEN")
    c.line(70, y-5, 200, y-5)
    y -= 25
    
    c.setFont("Helvetica", 11)
    c.drawString(70, y, f"Total de días: {total}")
    y -= 18
    c.drawString(70, y, f"Presente: {presentes}")
    y -= 18
    c.drawString(70, y, f"Ausente: {ausentes}")
    y -= 18
    c.drawString(70, y, f"Tardanzas: {tardanzas}")
    y -= 25
    c.setFont("Helvetica-Bold", 12)
    color_porcentaje = "red" if porcentaje < 85 else "black"
    c.drawString(70, y, f"Porcentaje de asistencia: {porcentaje}%")
    
    # Detalle
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(70, y, "DETALLE")
    c.line(70, y-5, 200, y-5)
    y -= 25
    
    # Tabla
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, y, "Fecha")
    c.drawString(200, y, "Estado")
    c.drawString(350, y, "Observación")
    y -= 15
    
    c.setFont("Helvetica", 10)
    for asist in asistencias[:20]:  # Limitar a 20 registros
        if y < 80:
            break
        c.drawString(70, y, asist.fecha.strftime('%d/%m/%Y'))
        c.drawString(200, y, asist.get_estado_display())
        obs = asist.observacion[:30] + '...' if asist.observacion and len(asist.observacion) > 30 else (asist.observacion or '-')
        c.drawString(350, y, obs)
        y -= 15
    
    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, 40, f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
