import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_ID = "14gRL3ijGFaxbgOeeuOPgzyKdX3Td7-jyiseS9cnAX6w"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
    for r in registros:
        if texto.lower() in r["nombres_apellidos"].lower():
            resultados.append({
                "nombres_apellidos": r["nombres_apellidos"],
                "DNI": r["DNI"],
                "foto_url": r.get("foto_url", "")
            })
    return resultados
from datetime import datetime

def actualizar_vigencia(fila, vigencia):
    """
    Actualiza la columna 'vigencia' de una persona en Google Sheets.
    """
    headers = sheet.row_values(1)
    if "vigencia" in headers:
        col = headers.index("vigencia") + 1
        sheet.update_cell(fila, col, vigencia.upper())

def guardar_historial(persona):
    """
    Guarda en la hoja HISTORIAL la emisión del certificado.
    """
    historial = client.open_by_key(SHEET_ID).worksheet("HISTORIAL")
    ahora = datetime.now()
    historial.append_row([
        ahora.strftime("%d/%m/%Y"),
        ahora.strftime("%H:%M:%S"),
        persona["DNI"],
        persona["nombres_apellidos"],
        persona.get("colegiatura",""),
        persona.get("vigencia","")
    ])
