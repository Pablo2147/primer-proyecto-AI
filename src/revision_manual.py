revision_manual = [
    # 5 casos con menor f1
    {
        "consulta": "¿Cuántos continentes hay?",
        "f1": 0.03,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": ("responde 6, pero lista además responde con 4, 5 y 7 continentes"),
    },
    {
        "consulta": "¿Qué es Python?",
        "f1": 0.04,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "definición correcta pero con características y usos que exceden la referencia"
        ),
    },
    {
        "consulta": "¿Qué es una lista en Python?",
        "f1": 0.05,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": ("explicación correcta con ejemplos de código y métodos "),
    },
    {
        "consulta": "¿Qué es una función en programación?",
        "f1": 0.08,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "concepto bien explicado, pero añade partes, ejemplo y ventajas no pedidas"
        ),
    },
    {
        "consulta": "¿Quién descubrió América en 1492?",
        "f1": 0.10,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": (
            "nombra a Colón, pero agrega matices sobre pueblos indígenas y vikingos que alargan la respuesta"
        ),
    },
    # 5 casos con mayor f1
    {
        "consulta": "¿Cuál es el planeta más cercano al Sol?",
        "f1": 1.00,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "respuesta breve y exacta: Mercurio",
    },
    {
        "consulta": "¿Qué país ganó el Mundial de fútbol de 2022?",
        "f1": 0.78,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "responde Argentina de forma directa",
    },
    {
        "consulta": "¿Quién fue el primer presidente de Estados Unidos?",
        "f1": 0.72,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": ("George Washington, con su periodo 1789-1797 correcto"),
    },
    {
        "consulta": "¿Cuál es la capital de Chile?",
        "f1": 0.67,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "responde Santiago de forma directa",
    },
    {
        "consulta": "¿Cuántos jugadores tiene un equipo de fútbol en cancha?",
        "f1": 0.55,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": ("11 jugadores, aclarando 10 de campo y 1 portero"),
    },
]


import json

with open("revision_manual.json", "w", encoding="utf-8") as archivo:

    json.dump(revision_manual, archivo, indent=2, ensure_ascii=False)
