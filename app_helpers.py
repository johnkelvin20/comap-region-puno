import os
import json
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo  # ✅ zona horaria (Python 3.9+)
from oauth2client.service_account import ServiceAccountCredentials


SHEET_ID = "14gRL3ijGFaxbgOeeuOPgzyKdX3Td7-jyiseS9cnAX6w"


# Define el scope de Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Credenciales
if "GOOGLE_CREDENTIALS" in os.environ:
    # Si estamos en Render, usamos la variable de entorno
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
else:
    # Si estamos local, usamos el archivo local
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)

# Conexión con Google Sheets
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Función para buscar persona por DNI
def buscar_persona_por_dni(dni):
    registros = sheet.get_all_records()
    for i, r in enumerate(registros, start=2):
        if str(r["DNI"]) == str(dni):
            r["_fila"] = i
            return r
    return None


def buscar_personas_por_nombre(texto):
    registros = sheet.get_all_records()
    resultados = []
    for i, r in enumerate(registros, start=2):
        if texto.lower() in r["nombres_apellidos"].lower():
            resultados.append({
                "nombres_apellidos": r["nombres_apellidos"],
                "DNI": r["DNI"],
                "vigencia": r.get("vigencia",""),
                "colegiatura": r.get("colegiatura",""),
                "foto_url": r.get("foto_url") or "/static/avatar_neutro_carnet.png",
                "fila": i
            })
    return resultados



def actualizar_vigencia(fila, vigencia):
    try:
        if not fila or int(fila) < 2:
            print("❌ Fila inválida:", fila)
            return False

        headers = sheet.row_values(1)

        if "vigencia" not in headers:
            print("❌ Columna 'vigencia' no existe")
            return False

        col = headers.index("vigencia") + 1
        sheet.update_cell(int(fila), col, vigencia.upper())

        print("✅ Vigencia actualizada en fila", fila)
        return True

    except Exception as e:
        print("❌ Error al actualizar vigencia:", e)
        return False

def vigencia_a_texto(vigencia):
    """
    Convierte '28/02/2026' → 'FEBRERO DE 2026'
    """
    try:
        fecha = datetime.strptime(vigencia, "%d/%m/%Y")
        meses = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SETIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
        ]
        mes = meses[fecha.month - 1]
        return f"{mes} DE {fecha.year}"
    except Exception:
        return str(vigencia).upper()


def guardar_historial(persona):
    """
    Guarda en la hoja HISTORIAL la emisión del certificado.
    """
    historial = client.open_by_key(SHEET_ID).worksheet("HISTORIAL")
    ahora = datetime.now(ZoneInfo("America/Lima"))  # ✅ hora Perú
    historial.append_row([
        ahora.strftime("%d/%m/%Y"),
        ahora.strftime("%H:%M:%S"),
        persona["DNI"],
        persona["nombres_apellidos"],
        persona.get("colegiatura",""),
        vigencia_a_texto(persona.get("vigencia",""))
    ])





def leer_comunicados(limit_anteriores=10):
    """
    Lee la hoja/pestaña COMUNICADOS del mismo Google Sheet.
    Devuelve:
      - principal (dict): comunicado activo (TRUE) o el más reciente
      - anteriores (list[dict]): comunicados para mostrar como "anteriores"
    """
    ws = client.open_by_key(SHEET_ID).worksheet("COMUNICADOS")
    rows = ws.get_all_records()

    data = []
    for r in rows:
        # (1) Ignorar filas vacías
        texto = str(r.get("texto", "")).strip()
        if not texto:
            continue

        # (2) Convertir activo a booleano
        activo_raw = str(r.get("activo", "")).strip().lower()
        activo = activo_raw in ("true", "1", "si", "sí", "x")

        # (3) Guardar todas las columnas que necesitaremos en HTML
        data.append({
            "activo": activo,
            "fecha": str(r.get("fecha", "")).strip(),
            "titulo": str(r.get("titulo", "")).strip(),  # <- IMPORTANTE: título del número de comunicado
            "texto": texto,
            "autor": str(r.get("autor", "")).strip(),
            "link": str(r.get("link", "")).strip(),
        })

    if not data:
        return None, []

    # Ordenar por fecha (YYYY-MM-DD) desc
    def _key_fecha(x):
        try:
            return datetime.strptime(x["fecha"], "%Y-%m-%d")
        except Exception:
            return datetime.min

    data.sort(key=_key_fecha, reverse=True)

    # Principal: el activo TRUE; si no hay, el más reciente
    principal = next((x for x in data if x["activo"]), data[0])

    # Anteriores: todo menos el principal
    anteriores = [x for x in data if x is not principal][:limit_anteriores]

    # Defaults por si alguna columna viene vacía
    principal["titulo"] = principal["titulo"] or "COMUNICADO OFICIAL"
    principal["autor"] = principal["autor"] or "DECANATO COMAP"

    for a in anteriores:
        a["titulo"] = a["titulo"] or "COMUNICADO"
        a["autor"] = a["autor"] or "DECANATO COMAP"

    return principal, anteriores

