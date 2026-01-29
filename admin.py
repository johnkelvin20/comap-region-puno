from flask import render_template, request, jsonify, session
from app_helpers import buscar_persona_por_dni, buscar_personas_por_nombre

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
        "foto_url": persona.get("foto_url","")
    })

def buscar_nombre_admin_view():
    if not session.get("admin"):
        return jsonify({"success": False, "error":"No autorizado"})
    texto = request.json.get("nombre","").strip()
    resultados = buscar_personas_por_nombre(texto)
    return jsonify({"success": True, "resultados": resultados})
