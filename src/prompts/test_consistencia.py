import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from banco import BANCO_DE_PROMPTS
from consumir_gemini import (
    armar_peticion,
    enviar_peticion,
    extraer_texto,
    parsear_respuesta_json,
)

registro = {}

for prompt in BANCO_DE_PROMPTS:
    exitos = 0
    intentos = 3
    for intento in range(intentos):
        url, body = armar_peticion(
            prompt["ejemplo_usuario"],
            prompt["system_instruction"],
            prompt.get("response_schema"),
        )
        try:
            respuesta = enviar_peticion(url, body)
            texto = extraer_texto(respuesta)
            datos = parsear_respuesta_json(texto)
            if all(clave in datos for clave in prompt["claves_esperadas"]):
                exitos += 1
        except (ValueError, RuntimeError) as error:
            print(f"  intento {intento + 1} falló: {error}")
        time.sleep(1)
    print(f"{prompt['nombre']}: {exitos}/{intentos} respuestas válidas")
    registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}

ruta_registro = Path(__file__).resolve().parent / "registro_resultados.json"
with open(ruta_registro, "w", encoding="utf-8") as archivo:
    json.dump(registro, archivo, indent=2, ensure_ascii=False)
