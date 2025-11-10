import time
import requests
from datetime import datetime, timedelta
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------
# CONFIGURACIÓN DE TU API SMS
# -----------------------------
API_BASE = "http://panel.kyrabo.com/app/smsapi/index.php"
TIPO = "text"
CONTACTO = "525611410191,525531071864,525561223338,528143801177,525525553022,"

# -----------------------------
# CONFIGURACIÓN DE GOOGLE SHEETS
# -----------------------------
GOOGLE_SHEETS_CREDENTIALS = "credenciales.json"
DOCUMENTO_SHEETS = "Registro_SMS"

# -----------------------------
# DEFINICIÓN DE RUTAS CON INTERVALOS
# -----------------------------
RUTAS = [
    {
        "nombre": "Código Corto",
        "intervalo_horas": 1,
        "api_key": "58f5864592a0b",
        "sender_id": "PROCOM SC",
        "pestana": "Registro_CodigoCorto",
        "ultimo_envio": None
    },
    {
        "nombre": "Código Largo",
        "intervalo_horas": 1,
        "api_key": "590ba4a2a4ebe",
        "sender_id": "PROCOM LC",
        "pestana": "Registro_CodigoLargo",
        "ultimo_envio": None
    },
    {
        "nombre": "TEDEXIS_LC",
        "intervalo_horas": 3,
        "api_key": "6876e69b1513e",
        "sender_id": "Tedexis",
        "pestana": "Registro_TedexisLC",
        "ultimo_envio": None
    }
]

# -----------------------------
# CONECTAR A PESTAÑA DE GOOGLE SHEETS
# -----------------------------
def conectar_sheets(nombre_documento, nombre_pestana):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
        cliente = gspread.authorize(creds)
        libro = cliente.open(nombre_documento)
        hoja = libro.worksheet(nombre_pestana)
        return hoja
    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ La pestaña '{nombre_pestana}' no fue encontrada en el documento '{nombre_documento}'.")
        return None
    except Exception as e:
        print(f"⚠️ Error al conectar con Google Sheets: {e}")
        return None

# -----------------------------
# ENVIAR SMS Y REGISTRAR
# -----------------------------
def enviar_sms(contactos, mensaje, api_key, sender_id, nombre_documento, nombre_pestana, nombre_ruta, intervalo_horas):
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg_encoded = urllib.parse.quote(mensaje)
    url = f"{API_BASE}?key={api_key}&type={TIPO}&contacts={contactos}&senderid={sender_id}&msg={msg_encoded}"

    try:
        respuesta = requests.get(url)
        estado = "✅ Enviado" if respuesta.status_code == 200 else f"⚠️ Error {respuesta.status_code}"
    except Exception as e:
        estado = f"❌ Error: {e}"

    print(f"[{hora_actual}] {estado} → {contactos}")
    print(f"📝 Registrando en Google Sheets ({nombre_pestana})...")

    with open("log_sms.txt", "a", encoding="utf-8") as f:
        f.write(f"{hora_actual} - {contactos} - {estado} - {mensaje} - {sender_id}\n")

    hoja = conectar_sheets(nombre_documento, nombre_pestana)
    if hoja:
        hoja.append_row([hora_actual, contactos, estado, mensaje, sender_id])
        print(f"✅ Registro completado en Google Sheets para {nombre_ruta}.\n")
    else:
        print(f"⚠️ No se pudo registrar en Google Sheets para {nombre_ruta}.\n")

    print(f"⏳ Esperando {intervalo_horas}h para el siguiente envío de {nombre_ruta}...\n")

# -----------------------------
# CICLO AUTOMÁTICO MULTIRUTA CON INTERVALOS
# -----------------------------
def ciclo_automatico():
    while True:
        ahora = datetime.now()
        hora = ahora.hour

        if 7 <= hora < 24:
            for ruta in RUTAS:
                if ruta["ultimo_envio"] is None or ahora - ruta["ultimo_envio"] >= timedelta(hours=ruta["intervalo_horas"]):
                    mensaje = f"Hola equipo Kyrabo! Este es un mensaje desde {ruta['nombre']} enviado a las {ahora.strftime('%d/%m/%Y %H:%M:%S')}."
                    enviar_sms(CONTACTO, mensaje, ruta["api_key"], ruta["sender_id"], DOCUMENTO_SHEETS, ruta["pestana"], ruta["nombre"], ruta["intervalo_horas"])
                    ruta["ultimo_envio"] = ahora
        else:
            print(f"[{ahora.strftime('%H:%M:%S')}] 🌙 Fuera de horario (00:00 a 07:00). Esperando 30 minutos...\n")
            time.sleep(1800)

        time.sleep(60)

if __name__ == "__main__":
    ciclo_automatico()