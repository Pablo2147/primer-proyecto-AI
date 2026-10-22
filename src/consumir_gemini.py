import os
import requests
import json
import re
from dotenv import load_dotenv
  
load_dotenv()
  
def armar_peticion(pregunta, system_instruction, response_schema=None):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    api_key = os.getenv("GEMINI_API_KEY")
    modelo = "gemini-3.1-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {
    	"systemInstruction": {
        	"parts": [ { "text": system_instruction } ]
    	},
    	"contents": [
        	{ "parts": [ { "text": pregunta } ] }
    	]
	}
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    return url, body
  
def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=60)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos segundos.")
    try:
        datos = respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")
    if not respuesta.ok:
        detalle = datos.get("error", {}).get("message", "sin detalle") if isinstance(datos, dict) else "sin detalle"
        raise RuntimeError(f"El servicio respondió con error {respuesta.status_code}: {detalle}")
    return datos
  
def extraer_texto(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no trae el texto generado en el lugar esperado.")
def parsear_respuesta_json(texto):
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
         datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON válido.")
    if not isinstance(datos, dict):
        raise ValueError("La respuesta no tiene la estructura esperada.")
    return datos
