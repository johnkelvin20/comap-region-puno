from flask import Flask, render_template, request, send_file, session
import publico, login, admin

from overlay_pdf import crear_overlay_pdf, fusionar_pdfs
from app_helpers import (
    actualizar_vigencia,
    guardar_historial,
    buscar_persona_por_dni
)

from io import BytesIO
import zipfile

# ================= CONFIGURACIÓN =================
app = Flask(__name__)
app.secret_key = "COMAP_SECRETO_2026"

# ================= RUTA INICIO =================
@app.route("/")
def inicio():
    comunicado_texto = (
        "COMUNICADO – COLEGIO DE MATEMÁTICOS DEL PERÚ (REGIÓN PUNO)\n\n"
        "Se informa que la plataforma oficial ya se encuentra habilitada para la "
        "consulta pública de condición de colegiatura/habilitación y la verificación "
        "de constancias/certificados.\n\n"
        "Se solicita a los colegiados revisar y mantener actualizados sus datos.\n\n"
        "Atentamente,\n"
        "Decanato – Región Puno."
    )

    return render_template(
        "inicio.html",
        comunicado_texto=comunicado_texto,
        comunicado_fecha="22/01/2026",
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
    return admin.admin_view()

@app.route("/buscar_dni_admin", methods=["POST"])
def buscar_dni_admin():
    return admin.buscar_dni_admin_view()

@app.route("/buscar_nombre_admin", methods=["POST"])
def buscar_nombre_admin():
    return admin.buscar_nombre_admin_view()


# ================= GENERAR ZIP CON 2 PDFs =================
@app.route("/pdf", methods=["POST"])
def generar_pdf():

    dni = request.form.get("dni")
    vigencia = request.form.get("fecha_vencimiento_input")

    persona = buscar_persona_por_dni(dni)
    if not persona:
        return "DNI no encontrado", 404

    # Actualizar datos
    persona["vigencia"] = vigencia
    actualizar_vigencia(persona["_fila"], vigencia)
    guardar_historial(persona)

    # ===== CREAR OVERLAY (UNA VEZ) =====
    overlay_original = crear_overlay_pdf(persona)

    # ===== DUPLICAR OVERLAY EN MEMORIA =====
    overlay_con_firma = BytesIO(overlay_original.getvalue())
    overlay_sin_firma = BytesIO(overlay_original.getvalue())

    # ===== GENERAR LOS DOS PDF =====
    pdf_con_firma = fusionar_pdfs(overlay_con_firma, "plantilla1.pdf")
    pdf_sin_firma = fusionar_pdfs(overlay_sin_firma, "plantilla2.pdf")

    # ===== CREAR ZIP =====
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("CERTIFICADO_CON_FIRMA.pdf", pdf_con_firma.getvalue())
        zipf.writestr("CERTIFICADO_SIN_FIRMA.pdf", pdf_sin_firma.getvalue())

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"certificado_comap_{dni}.zip",
        mimetype="application/zip"
    )

# ================= EJECUCIÓN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

