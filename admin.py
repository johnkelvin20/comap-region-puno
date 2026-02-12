from flask import render_template, request, jsonify, session
from app_helpers import buscar_persona_por_dni, buscar_personas_por_nombre
from app_helpers import actualizar_vigencia


def admin_view():
    if not session.get("admin"):
        from flask import redirect, url_for
        return redirect(url_for("login_page"))
    return render_template("admin.html")

def buscar_dni_admin_view():
    if not session.get("admin"):
        return jsonify({"success": False, "error":"No autorizado"})
    dni = request.json.get("dni")
    persona = buscar_persona_por_dni(dni)
    if not persona:
        return jsonify({"success": False})
    return jsonify({
    "success": True,
    "nombres_apellidos": persona["nombres_apellidos"],
    "condicion": persona.get("condicion",""),
    "colegiatura": persona.get("colegiatura",""),
    "vigencia": persona.get("vigencia",""),
    "fila": persona["_fila"],
    "foto_url": persona.get("foto_url") or "/static/avatar_neutro_carnet.png"
})



def buscar_nombre_admin_view():
    if not session.get("admin"):
        return jsonify({"success": False, "error":"No autorizado"})
    texto = request.json.get("nombre","").strip()
    resultados = buscar_personas_por_nombre(texto)
    return jsonify({"success": True, "resultados": resultados})




def actualizar_vigencia_admin_view():
    if not session.get("admin"):
        return jsonify({"success": False, "error": "No autorizado"})

    data = request.json

    try:
        fila = data.get("fila")
        vigencia = data.get("vigencia")

        if not fila:
            return jsonify({"success": False, "error": "Fila no enviada"})

        if not vigencia:
            return jsonify({"success": False, "error": "Vigencia vacía"})

        ok = actualizar_vigencia(int(fila), vigencia)

        if not ok:
            return jsonify({
                "success": False,
                "error": "No se pudo actualizar en Google Sheets"
            })

        return jsonify({"success": True})

    except Exception as e:
        print("❌ Error actualizar_vigencia_admin:", e)
        return jsonify({
            "success": False,
            "error": "Error interno del servidor"
        })


