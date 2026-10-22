BANCO_DE_PROMPTS = [
    {
        "nombre": "clasificar_categoria_ticket",
        "system_instruction": (
            "Responde únicamente con un JSON con las claves 'categoria' "
            "('facturacion', 'soporte_tecnico', 'ventas' u 'otros') y "
            "'confianza' (0 a 1)."
        ),
        "ejemplo_usuario": "No puedo iniciar sesión en mi cuenta desde ayer.",
        "claves_esperadas": ["categoria", "confianza"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria": {"type": "STRING"},
                "confianza": {"type": "NUMBER"},
            },
            "required": ["categoria", "confianza"],
        },
    },
    {
        "nombre": "extraer_datos_contacto",
        "system_instruction": (
            "Responde únicamente con un JSON con las claves 'nombre', "
            "'email' y 'telefono', extraídas del texto del usuario. "
            "Si un dato no aparece, usa una cadena vacía."
        ),
        "ejemplo_usuario": (
            "Hola, soy Laura Gómez, mi correo es laura.gomez@example.com "
            "y mi teléfono es 555-123-4567."
        ),
        "claves_esperadas": ["nombre", "email", "telefono"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "nombre": {"type": "STRING"},
                "email": {"type": "STRING"},
                "telefono": {"type": "STRING"},
            },
            "required": ["nombre", "email", "telefono"],
        },
    },
    {
        "nombre": "resumir_texto",
        "system_instruction": (
            "Responde únicamente con un JSON con las claves 'resumen' "
            "(máximo 20 palabras) y 'num_palabras' (cantidad de palabras "
            "del resumen)."
        ),
        "ejemplo_usuario": (
            "La reunión de ayer sirvió para definir el calendario del "
            "proyecto: el diseño termina en marzo, el desarrollo en mayo "
            "y las pruebas con clientes empiezan en junio."
        ),
        "claves_esperadas": ["resumen", "num_palabras"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "resumen": {"type": "STRING"},
                "num_palabras": {"type": "INTEGER"},
            },
            "required": ["resumen", "num_palabras"],
        },
    },
    {
        "nombre": "detectar_idioma",
        "system_instruction": (
            "Responde únicamente con un JSON con las claves 'idioma' "
            "(nombre del idioma en español) y 'codigo' (código ISO 639-1 "
            "de dos letras)."
        ),
        "ejemplo_usuario": "Je voudrais réserver une table pour deux personnes.",
        "claves_esperadas": ["idioma", "codigo"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "idioma": {"type": "STRING"},
                "codigo": {"type": "STRING"},
            },
            "required": ["idioma", "codigo"],
        },
    },
]
