# from consumir_gemini import (
#     armar_peticion,
#     enviar_peticion,
#     extraer_texto,
#     parsear_respuesta_json,
# )

import cliente

# from cliente import consultar_modelo

SYSTEM_INSTRUCTION = (
    "Responde únicamente con un JSON con las claves 'sentimiento' "
    "('positivo', 'negativo' o 'neutro') y 'confianza' (0 a 1)."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "sentimiento": {"type": "STRING"},
        "confianza": {"type": "NUMBER"},
    },
    "required": ["sentimiento", "confianza"],
}

PREGUNTA = "El servicio llegó tarde pero el producto está perfecto!."


def main():
    # try:
    #     url, body = armar_peticion(PREGUNTA, SYSTEM_INSTRUCTION, RESPONSE_SCHEMA)
    #     respuesta = enviar_peticion(url, body)
    #     texto = extraer_texto(respuesta)
    #     datos = parsear_respuesta_json(texto)
    # except (ValueError, RuntimeError) as error:
    #     print("No se pudo completar la operación:", error)
    #     return

    # print("Pregunta:", PREGUNTA)
    # print("Respuesta:", datos)

    respuesta = cliente.consultar_modelo("¿Cuál es la capital de Chile?")
    print(respuesta)
    print(f"Costo acumulado de la sesión: ${cliente.costo_total_sesion:.5f}")


if __name__ == "__main__":
    main()
