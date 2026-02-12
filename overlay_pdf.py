from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from zoneinfo import ZoneInfo  # ✅ Zona horaria Perú
from io import BytesIO
from pypdf import PdfReader, PdfWriter

# ================= CONFIGURACIÓN =================
MM = 2.83465  # 1 mm = 2.83465 puntos


def crear_overlay_pdf(datos):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    pdfmetrics.registerFont(TTFont("OldEnglish", "OLDENGL.TTF"))

    X_CENTRO = 105 * MM

    # 🔤 NOMBRES
    c.setFont("OldEnglish", 34)
    c.drawCentredString(
        X_CENTRO,
        168 * MM,
        str(datos["nombres_apellidos"]).title()
    )

    # 🎓 COLEGIATURA (4 dígitos)
    colegiatura = str(datos["colegiatura"]).zfill(4)
    c.setFont("OldEnglish", 25)
    c.drawString(98 * MM, 152 * MM, colegiatura)

    # ✅ CONDICIÓN
    c.setFont("Times-Bold", 30)
    c.drawCentredString(
        110 * MM,
        118 * MM,
        str(datos["condicion"]).upper()
    )

    # 📌 VIGENCIA
    c.setFont("Times-Bold", 22)
    c.drawString(
        40 * MM,
        104 * MM,
        datos["vigencia"].upper()
    )

    # 📅 FECHA
    meses = [
        "enero","febrero","marzo","abril","mayo","junio",
        "julio","agosto","septiembre","octubre","noviembre","diciembre"
    ]
    hoy = datetime.now(ZoneInfo("America/Lima"))  # ✅ Hora Perú
    fecha = f"Puno, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

    c.setFont("Times-Roman", 20)
    c.drawCentredString(146 * MM, 65 * MM, fecha)

    # 🔐 PIE DE PÁGINA
    c.setFont("Times-Roman", 10)
    c.drawCentredString(X_CENTRO + 19 * MM, 13 * MM, f"Colegiado N.° {colegiatura}")
    c.drawCentredString(X_CENTRO + 19 * MM, 9 * MM, hoy.strftime("%d/%m/%Y"))
    c.drawCentredString(X_CENTRO + 19 * MM, 5 * MM, hoy.strftime("%H:%M:%S"))

    c.save()
    buffer.seek(0)
    return buffer


def fusionar_pdfs(overlay_buffer, plantilla_pdf):
    """
    Fusiona el overlay con la plantilla indicada
    """
    base = PdfReader(plantilla_pdf)
    overlay = PdfReader(overlay_buffer)

    writer = PdfWriter()
    page = base.pages[0]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

    salida = BytesIO()
    writer.write(salida)
    salida.seek(0)
    return salida
