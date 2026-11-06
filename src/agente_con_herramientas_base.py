# Carga variables de entorno desde el archivo .env (por ejemplo, la API key de Google)
from dotenv import load_dotenv

# Decorador que convierte una función de Python en una "herramienta" que el LLM puede invocar
from langchain_core.tools import tool

# Cliente de LangChain para usar los modelos Gemini de Google
from langchain_google_genai import ChatGoogleGenerativeAI

# AgentExecutor: bucle que ejecuta el agente (modelo -> herramienta -> modelo ...)
# create_tool_calling_agent: construye un agente que usa el "tool calling" nativo del modelo
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)

# ChatPromptTemplate: plantilla para armar el prompt como lista de mensajes
# MessagesPlaceholder: espacio reservado donde se insertan mensajes dinámicos
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

# Lee el archivo .env y deja sus variables disponibles en el entorno del proceso
load_dotenv()
# Crea el modelo de lenguaje; timeout=10 cancela la petición si tarda más de 10 segundos
modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", timeout=10)


# Registra la función como herramienta; el docstring es lo que el modelo lee para decidir cuándo usarla
@tool
def buscar_en_documentacion(consulta: str) -> str:
    """Busca información relevante en la
    documentación interna del producto.

    Usar cuando la pregunta es sobre cómo
    funciona algo del sistema."""
    # Documentación simulada: diccionario palabra clave -> texto explicativo
    documentacion = {
        # Entrada sobre la política de reintentos del cliente
        "reintentos": (
            "El cliente reintenta hasta 3 veces "
            "ante un TimeoutError, con espera "
            "creciente."
        ),
        # Entrada sobre cómo se calcula el costo de uso
        "costos": (
            "El costo se calcula a partir de "
            "totalTokenCount, según la tarifa "
            "vigente."
        ),
    }
    # Recorre cada par (clave, texto) de la documentación
    for clave, texto in documentacion.items():
        # Si la clave aparece en la consulta (en minúsculas), devuelve su texto
        if clave in consulta.lower():
            return texto
    # Si ninguna clave coincidió, informa que no hay información
    return "No se encontró información sobre esa " "consulta en la documentación."


# Registra la función como herramienta para el agente
@tool
def calcular(expresion: str) -> str:
    """Evalúa una expresión aritmética simple,
    como '340 + 215'. Usar cuando la pregunta
    requiere un cálculo numérico."""
    # Conjunto de caracteres seguros: dígitos, operadores, paréntesis, punto y espacio
    permitido = set("0123456789+-*/(). ")
    # Si la expresión tiene algún carácter fuera de la lista, se rechaza (protege el eval)
    if not set(expresion) <= permitido:
        return "Expresión no permitida."
    try:
        # Evalúa la expresión y devuelve el resultado como texto
        return str(eval(expresion))
    except Exception as e:
        # Ante cualquier error (p. ej. división por cero o sintaxis inválida) devuelve el mensaje
        return f"Error al evaluar la expresión: {e}"


# Lista de herramientas que el agente tendrá disponibles
herramientas = [buscar_en_documentacion, calcular]

# Define el prompt del agente como una secuencia de mensajes
prompt_agente = ChatPromptTemplate.from_messages(
    [
        # Mensaje de sistema: define el rol y comportamiento del asistente
        (
            "system",
            "Eres un asistente que responde preguntas "
            "usando las herramientas disponibles cuando "
            "las necesites.",
        ),
        # Mensaje del usuario; {entrada} se reemplaza con la pregunta al invocar
        ("human", "{entrada}"),
        # Aquí el agente guarda sus llamadas a herramientas y resultados intermedios
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

# Construye el agente combinando modelo, herramientas y prompt
agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

# Ejecutor que corre el agente en bucle (modelo -> herramienta -> modelo) hasta dar la respuesta final.
# - agent: el agente construido arriba
# - tools: herramientas que el ejecutor puede llamar cuando el modelo lo pida
# - verbose=True: imprime en consola cada paso del razonamiento
# - return_intermediate_steps=True: incluye en el resultado la clave "intermediate_steps"
#   con la lista de (acción, observación), es decir, qué herramientas se llamaron y qué devolvieron
ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True,
    return_intermediate_steps=True,
)

# Ejecuta el agente con una pregunta de ejemplo (debería usar la herramienta calcular)
resultado = ejecutor_agente.invoke({"entrada": "¿Cuánto es 340 más 215?"})

# Imprime la respuesta final del agente
print(resultado["output"])

# Recorre los pasos intermedios del agente (disponibles por return_intermediate_steps=True).
# Cada paso es una tupla (accion, observacion):
# - accion: la llamada que decidió hacer el modelo (herramienta y argumentos)
# - observacion: el texto que devolvió esa herramienta
for accion, observacion in resultado["intermediate_steps"]:
    # Muestra: nombre de la herramienta, argumentos enviados -> resultado obtenido
    print(accion.tool, accion.tool_input, "->", observacion)
