import os
import requests
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env (por ejemplo GEMINI_API_KEY)
# hacia el entorno del proceso. Sin esta línea, os.getenv("GEMINI_API_KEY")
# devolvería None aunque el .env exista, porque nada lo habría leído todavía.
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODELO = "gemini-3.5-flash-lite"
# El documento de la lección usa "gemini-2.0-flash", pero ese modelo ya fue
# dado de baja por Google (aparece como "Shut down" en su documentación).
# Usamos "gemini-3.8-flash", el modelo Flash vigente más reciente.
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={GEMINI_API_KEY}"
HEADERS = {"Content-Type": "application/json"}


def armar_peticion(pregunta, system_instruction, response_schema=None):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": pregunta}]}],
    }
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        }
    return body


def enviar_peticion(cuerpo):
    try:
        respuesta = requests.post(URL, json=cuerpo, headers=HEADERS, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise TimeoutError("No se pudo contactar al proveedor. Puede ser momentáneo.")
    if respuesta.status_code in (401, 403):
        raise ValueError("Credencial inválida o sin permiso. Revisa tu GEMINI_API_KEY.")
    if respuesta.status_code == 429 or respuesta.status_code >= 500:
        raise TimeoutError(
            "El proveedor no pudo procesar la petición. Hay que esperar y reintentar."
        )
    respuesta.raise_for_status()
    return respuesta.json()


def extraer_texto(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(
            "La respuesta no trae el texto generado en el lugar esperado."
        )
