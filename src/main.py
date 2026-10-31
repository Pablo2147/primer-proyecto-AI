# from consumir_gemini import (
#     armar_peticion,
#     enviar_peticion,
#     extraer_texto,
#     parsear_respuesta_json,
# )

import cliente, json
from pipeline_texto import calcular_metricas

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

    # respuesta = cliente.consultar_modelo("¿Cuál es la capital de Chile?")
    # print(respuesta)
    # print(f"Costo acumulado de la sesión: ${cliente.costo_total_sesion:.5f}")

    # consulta = "¿Qué es Python?"

    # referencia = "Python es un lenguaje de programación interpretado."

    # respuesta = cliente.consultar_modelo(consulta)

    # crudo_ref = referencia.split()

    # crudo_resp = respuesta.split()

    # comunes_crudo = set(crudo_ref) & set(crudo_resp)

    # pct_crudo = len(comunes_crudo) / len(set(crudo_ref))

    # tokens_ref = procesar_texto(referencia)

    # tokens_resp = procesar_texto(respuesta)

    # comunes = set(tokens_ref) & set(tokens_resp)

    # pct_proc = len(comunes) / len(set(tokens_ref))

    # print(f"[Caso 1] Coincidencia texto crudo: {pct_crudo:.1%}")

    # print(f"[Caso 1] Coincidencia texto procesado: {pct_proc:.1%}")
    casos = [
        ["¿Qué es Python?", "Python es un lenguaje de programación interpretado."],
        ["¿Cuándo se creó Python?", "Python fue creado en 1991."],
        [
            "¿Qué es una lista en Python?",
            "Una lista es una colección ordenada y modificable.",
        ],
        ["¿Cuál es la capital de Chile?", "La capital de Chile es Santiago."],
        [
            "¿Cuál es el río más largo del mundo?",
            "El río más largo del mundo es el Nilo.",
        ],
        ["¿Cuál es el océano más grande?", "El océano más grande es el Pacífico."],
        ["¿Cuántos continentes hay?", "Hay siete continentes."],
        [
            "¿En qué año llegó el hombre a la Luna?",
            "El hombre llegó a la Luna en 1969.",
        ],
        [
            "¿Quién fue el primer presidente de Estados Unidos?",
            "George Washington fue el primer presidente de Estados Unidos.",
        ],
        [
            "¿En qué año comenzó la Revolución Francesa?",
            "La Revolución Francesa comenzó en 1789.",
        ],
        [
            "¿Quién descubrió América en 1492?",
            "Cristóbal Colón llegó a América en 1492.",
        ],
        [
            "¿Cuántos jugadores tiene un equipo de fútbol en cancha?",
            "Un equipo de fútbol tiene once jugadores en cancha.",
        ],
        [
            "¿Qué país ganó el Mundial de fútbol de 2022?",
            "Argentina ganó el Mundial de fútbol de 2022.",
        ],
        [
            "¿Cada cuántos años se celebran los Juegos Olímpicos?",
            "Los Juegos Olímpicos se celebran cada cuatro años.",
        ],
        [
            "¿Cuántos puntos vale un triple en baloncesto?",
            "Un triple en baloncesto vale tres puntos.",
        ],
        [
            "¿Cuál es el planeta más cercano al Sol?",
            "Mercurio es el planeta más cercano al Sol.",
        ],
        [
            "¿Cuál es la fórmula química del agua?",
            "La fórmula química del agua es H2O.",
        ],
        [
            "¿Qué gas necesitan las plantas para la fotosíntesis?",
            "Las plantas necesitan dióxido de carbono para la fotosíntesis.",
        ],
        [
            "¿Quién escribió Don Quijote de la Mancha?",
            "Miguel de Cervantes escribió Don Quijote de la Mancha.",
        ],
        [
            "¿Qué es una función en programación?",
            "Una función es un bloque de código reutilizable que realiza una tarea.",
        ],
    ]

    resultados = []
    for consulta, referencia in casos:

        respuesta = cliente.consultar_modelo(consulta)

        metricas = calcular_metricas(referencia, respuesta)

        resultados.append(
            {
                "consulta": consulta,
                "respuesta": respuesta,
                **metricas,
            }
        )

    with open("resultados_metricas.json", "w", encoding="utf-8") as archivo:

        json.dump(resultados, archivo, indent=2, ensure_ascii=False)

    peores_casos = sorted(resultados, key=lambda r: r["f1"])

    for caso in peores_casos[:3]:

        print(caso["consulta"], caso["f1"])


if __name__ == "__main__":
    main()
