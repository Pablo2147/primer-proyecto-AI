# Agente con memoria (versión final): un agente de LangChain con dos herramientas
# (consulta de estado de envío y cálculo de costo) que recuerda la conversación
# previa de cada sesión.

# --- Importaciones ---
# Carga variables de entorno desde el archivo .env (ej. la API key de Google)
from dotenv import load_dotenv

# BaseModel y Field sirven para definir el esquema de argumentos de una herramienta
from pydantic import BaseModel, Field

# Decorador para convertir una función de Python en una herramienta del agente
from langchain_core.tools import tool

# Almacén de mensajes en memoria RAM para guardar el historial del chat
from langchain_core.chat_history import (
    InMemoryChatMessageHistory,
)

# Envoltorio que agrega memoria (historial) a cualquier runnable
from langchain_core.runnables.history import (
    RunnableWithMessageHistory,
)

# Plantillas para construir el prompt y marcadores de posición de mensajes
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

# Cliente del modelo de lenguaje Gemini de Google
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
)

# Clases para crear el agente y ejecutar su ciclo de razonamiento/herramientas
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)

# --- Configuración del modelo ---
# Lee el archivo .env para que las credenciales estén disponibles
load_dotenv()
# Instancia el modelo de lenguaje que usará el agente
modelo = ChatGoogleGenerativeAI(model="gemini-2.0-flash")


# --- Bloque 1: herramienta con args_schema ---
# Esquema explícito de argumentos: el modelo lee las descripciones de cada
# campo para saber qué valor enviar al llamar la herramienta.
class ArgumentosConsultaEnvio(BaseModel):
    # Dato obligatorio: identifica el envío a consultar
    numero_seguimiento: str = Field(description="Número de seguimiento del envío.")
    # Dato opcional: por defecto no se incluye el historial
    incluir_historial: bool = Field(
        default=False, description="Si es True, incluye el historial completo."
    )


# Base de datos simulada de envíos (número de seguimiento -> datos del envío)
ESTADOS = {
    "AR12345": {
        # Estado más reciente del envío
        "actual": "en tránsito, llega en 2 días",
        # Etapas por las que ya pasó el envío
        "historial": [
            "recibido en depósito",
            "en tránsito",
        ],
    },
}


# El primer parámetro es el nombre con el que el modelo ve la herramienta (distinto
# del nombre de la función) y args_schema le indica qué argumentos acepta.
@tool("consultar_estado_envio_con_historial", args_schema=ArgumentosConsultaEnvio)
def consultar_estado_envio_detallado(
    numero_seguimiento: str, incluir_historial: bool = False
) -> str:
    """Consulta el estado de un envío, con la
    opción de incluir su historial completo."""
    # Busca el envío; .get devuelve None si el número no existe
    envio = ESTADOS.get(numero_seguimiento)
    # Si no existe, avisa en lugar de lanzar un error
    if envio is None:
        return f"No se encontró un envío con el " f"número {numero_seguimiento}."
    # Sin historial: devuelve solo el estado actual
    if not incluir_historial:
        return envio["actual"]
    # Con historial: une las etapas en un solo texto separado por comas
    historial = ", ".join(envio["historial"])
    return f"{envio['actual']} (historial: {historial})"


# El docstring es importante: el modelo lo lee para decidir cuándo usar
# la herramienta. Aquí el esquema de argumentos se infiere de la firma.
@tool
def calcular_costo_envio(peso_kg: float, distancia_km: float) -> str:
    """Calcula el costo estimado de un envío
    según su peso y la distancia a recorrer.
    Usar cuando el usuario pregunta cuánto va a
    costar enviar algo."""
    # Tarifa base de 500 + 120 por kg + 3 por km
    costo = 500 + (peso_kg * 120) + (distancia_km * 3)
    return f"El costo estimado es de ${costo:.2f}."


# --- Bloque 2: agente y ejecutor ---
# Lista de herramientas que el agente tiene disponibles
herramientas = [
    consultar_estado_envio_detallado,
    calcular_costo_envio,
]

# Define la estructura de mensajes que recibe el modelo en cada turno
prompt_agente = ChatPromptTemplate.from_messages(
    [
        # Instrucciones generales para el modelo
        (
            "system",
            "Eres un asistente que responde preguntas "
            "usando las herramientas disponibles cuando "
            "las necesites.",
        ),
        # Aquí se insertan los mensajes anteriores de la conversación (memoria)
        MessagesPlaceholder("chat_history"),
        # Mensaje actual del usuario
        ("human", "{entrada}"),
        # Espacio donde el agente guarda sus llamadas a herramientas y resultados
        MessagesPlaceholder("agent_scratchpad"),
    ]
)


# Crea el agente que decide si llamar a una herramienta o responder directo
agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

# Ejecutor que corre el ciclo: modelo -> herramienta -> modelo -> respuesta
ejecutor_agente = AgentExecutor(agent=agente, tools=herramientas)


# --- Bloque 3: memoria entre interacciones ---

# Diccionario que guarda un historial por cada sesión (session_id -> historial)
historiales = {}


def obtener_historial(session_id: str):
    # Si la sesión es nueva, crea un historial vacío para ella
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


# Envuelve el ejecutor para que lea y actualice el historial automáticamente
agente_con_memoria = RunnableWithMessageHistory(
    ejecutor_agente,
    obtener_historial,  # función que entrega el historial según la sesión
    input_messages_key="entrada",  # clave del input con el mensaje del usuario
    history_messages_key="chat_history",  # placeholder del prompt para el historial
)

# --- Ejecución ---
# Identifica la sesión; mensajes con el mismo session_id comparten memoria
config = {"configurable": {"session_id": "cliente_456"}}

# Consulta: el agente debería usar la herramienta de estado con historial
resultado = agente_con_memoria.invoke(
    {"entrada": ("¿Cuál es el estado del envío " "AR12345, con su historial?")}, config
)

# Muestra la respuesta final del agente
print(resultado["output"])
