from flask import render_template, request, jsonify
from app_helpers import buscar_persona_por_dni, client  # funciones comunes extraídas de app.py

def publico_view():
    return render_template("publico.html")

def buscar_dni_publico_view():
    dni = request.json.get("dni")
    persona = buscar_persona_por_dni(dni)

    if not persona:
        return jsonify({"success": False})

    vigencia = persona.get("vigencia", "").upper()
    foto_url = persona.get("foto_url") or "/static/avatar_neutro_carnet.png"

    historial = client.open_by_key("14gRL3ijGFaxbgOeeuOPgzyKdX3Td7-jyiseS9cnAX6w").worksheet("HISTORIAL")
    registros = historial.get_all_records(value_render_option="FORMATTED_VALUE")
    dni = str(dni).strip().zfill(8)
    registros_dni = [
        r for r in registros
        if str(r.get("DNI","")).strip().zfill(8) == dni
    ]
    if registros_dni:
        ultimo = registros_dni[-1]
        emitido = f"{ultimo.get('Fecha','—')} {ultimo.get('Hora','—')}"
    else:
        emitido = "—"

    return jsonify({
        "success": True,
        "nombres_apellidos": persona.get("nombres_apellidos", "—"),
        "colegiatura": persona.get("colegiatura", "—"),
        "condicion": persona.get("condicion", "—"),
        "vigencia": vigencia,
        "foto_url": foto_url,
        "emitido": emitido
    })
