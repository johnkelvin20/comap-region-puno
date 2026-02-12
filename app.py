from flask import Flask, render_template, request, send_file, session
from datetime import datetime

import publico
import login
import admin

from admin import (
    admin_view,
    buscar_dni_admin_view,
    buscar_nombre_admin_view,
    actualizar_vigencia_admin_view
)

from overlay_pdf import crear_overlay_pdf, fusionar_pdfs


# ===== IMPORTS DESDE app_helpers (Sheets + lógica de certificados) =====
# (Lee comunicados desde la hoja COMUNICADOS)
# (Y usa las funciones del sistema de certificados)
from app_helpers import (
    leer_comunicados,      # Lee comunicado principal y anteriores desde Google Sheets
    vigencia_a_texto,      # Convierte fecha a texto (para PDFs)
    buscar_persona_por_dni,# Busca persona por DNI en Sheets
    actualizar_vigencia,   # Actualiza vigencia en Sheets
    guardar_historial      # Guarda historial en Sheets
)



from io import BytesIO
import zipfile


# ================= CONFIGURACIÓN =================
app = Flask(__name__)
app.secret_key = "COMAP_SECRETO_2026"


# ================= RUTA INICIO =================
@app.route("/")
def inicio():
    """
    ✅ Lee comunicado principal y anteriores desde Google Sheets (hoja COMUNICADOS)
    ✅ Si falla, muestra fallback (para que la web nunca se caiga)
    """

    # ===== FALLBACK LOCAL (si Sheets falla, tu web NO se cae) =====
    comunicado_texto_fallback = (
        "COMUNICADO – COLEGIO DE MATEMÁTICOS DEL PERÚ (REGIÓN PUNO)\n\n"
        "Se informa que la plataforma oficial ya se encuentra habilitada para la "
        "consulta pública de condición de colegiatura/habilitación y la verificación "
        "de constancias/certificados.\n\n"
        "Se solicita a los colegiados revisar y mantener actualizados sus datos.\n\n"
        "Atentamente,\n"
        "Decanato – Región Puno."
    )
    comunicado_fecha_fallback = "22/01/2026"

    try:
        # ===== INTENTO: leer desde Google Sheets =====
        principal, anteriores = leer_comunicados(limit_anteriores=10)

        # Debug (opcional): ver en consola qué lee del Sheet
        print("✅ Principal:", principal)
        print("✅ Anteriores:", len(anteriores))

        if not principal:
            raise Exception("No hay comunicado principal en la hoja COMUNICADOS")

        return render_template(
            "inicio.html",
            comunicado_texto=principal.get("texto", ""),
            comunicado_fecha=principal.get("fecha", ""),
            comunicado_titulo=principal.get("titulo", "COMUNICADO OFICIAL"),
            comunicado_autor=principal.get("autor", "DECANATO COMAP"),
            comunicado_link=principal.get("link", ""),
            comunicados=anteriores,  # enviamos también titulo/autor/fecha/texto para anteriores
            es_admin=session.get("admin", False)
        )

    except Exception as e:
        print("❌ Error leyendo COMUNICADOS:", e)

        return render_template(
            "inicio.html",
            comunicado_texto=comunicado_texto_fallback,
            comunicado_fecha=comunicado_fecha_fallback,
            comunicado_titulo="COMUNICADO OFICIAL",
            comunicado_autor="DECANATO COMAP",
            comunicado_link="",
            comunicados=[],
            es_admin=session.get("admin", False)
        )



# ================= PÚBLICO =================
@app.route("/publico")
def publico_page():
    return publico.publico_view()

@app.route("/buscar_dni_publico", methods=["POST"])
def buscar_dni_publico():
    return publico.buscar_dni_publico_view()

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login_page():
    return login.login_view()

@app.route("/logout")
def logout_page():
    return login.logout_view()

# ================= ADMIN =================
@app.route("/admin")
def admin_page():
    return admin_view()

@app.route("/buscar_dni_admin", methods=["POST"])
def buscar_dni_admin():
    return buscar_dni_admin_view()

@app.route("/buscar_nombre_admin", methods=["POST"])
def buscar_nombre_admin():
    return buscar_nombre_admin_view()

@app.route("/actualizar_vigencia_admin", methods=["POST"])
def actualizar_vigencia_admin():
    return actualizar_vigencia_admin_view()



# ================= GENERAR ZIP CON 2 PDFs =================
@app.route("/pdf", methods=["POST"])
def generar_pdf():

    dni = (request.form.get("dni") or "").strip().zfill(8)
    vigencia_raw = (request.form.get("fecha_vencimiento_input") or "").strip()

    if not dni or not vigencia_raw:
        return "Faltan datos (dni o vigencia)", 400

    # --- Normalizar FECHA ---
    # fecha_archivo: YYYY-MM-DD (para nombres de archivos)
    # vigencia_para_helpers: DD/MM/YYYY (para vigencia_a_texto y guardar en Sheets)
    try:
        if "-" in vigencia_raw:  # ejemplo: 2026-03-15
            fecha_archivo = vigencia_raw
            vigencia_para_helpers = datetime.strptime(vigencia_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        else:  # ejemplo: 15/03/2026
            vigencia_para_helpers = vigencia_raw
            fecha_archivo = datetime.strptime(vigencia_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return "Formato de fecha inválido", 400

    # Texto para el PDF (MARZO DE 2026, etc.)
    vigencia_pdf = vigencia_a_texto(vigencia_para_helpers)

    persona = buscar_persona_por_dni(dni)
    if not persona:
        return "DNI no encontrado", 404

    # Guardar en REPORTE como fecha exacta (DD/MM/YYYY para mantener consistencia)
    persona["vigencia"] = vigencia_para_helpers
    actualizar_vigencia(persona["_fila"], vigencia_para_helpers)

    # Guardar en HISTORIAL (tu función ya convierte a letras)
    guardar_historial(persona)

    # Para el PDF: usar vigencia en letras
    persona["vigencia"] = vigencia_pdf

    # ===== CREAR OVERLAY (UNA VEZ) =====
    overlay_original = crear_overlay_pdf(persona)

    # ===== DUPLICAR OVERLAY EN MEMORIA =====
    overlay_con_firma = BytesIO(overlay_original.getvalue())
    overlay_sin_firma = BytesIO(overlay_original.getvalue())

    # ===== GENERAR LOS DOS PDF =====
    pdf_con_firma = fusionar_pdfs(overlay_con_firma, "plantilla1.pdf")
    pdf_sin_firma = fusionar_pdfs(overlay_sin_firma, "plantilla2.pdf")
    fecha_hoy_archivo = datetime.now().strftime("%Y-%m-%d")

    # ===== NOMBRES DE ARCHIVOS =====
    zip_name = f"CERTIF_COMAP_{dni}_{fecha_hoy_archivo}.zip"
    pdf_name_con = f"CERTIF_COMAP_{dni}_CON_FIRMA_{fecha_hoy_archivo}.pdf"
    pdf_name_sin = f"CERTIF_COMAP_{dni}_SIN_FIRMA_{fecha_hoy_archivo}.pdf"


    # ===== CREAR ZIP =====
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(pdf_name_con, pdf_con_firma.getvalue())
        zipf.writestr(pdf_name_sin, pdf_sin_firma.getvalue())

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=zip_name,
        mimetype="application/zip"
    )


# ================= EJECUCIÓN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

