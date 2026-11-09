# Agente con memoria: un agente de LangChain que usa herramientas y
# recuerda la conversación previa de cada sesión.

# --- Importaciones ---
# Carga variables de entorno desde el archivo .env (ej. la API key de Google)
from dotenv import load_dotenv

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


# --- Herramienta ---
# El docstring es importante: el modelo lo lee para decidir cuándo usar
# la herramienta.
@tool
def calcular_costo_envio(peso_kg: float, distancia_km: float) -> str:
    """Calcula el costo estimado de un envío
    según su peso y la distancia a recorrer.
    Usar cuando el usuario pregunta cuánto va a
    costar enviar algo."""
    # Tarifa base de 500 + 120 por kg + 3 por km
    costo = 500 + (peso_kg * 120) + (distancia_km * 3)
    return f"El costo estimado es de ${costo:.2f}"


# Lista de herramientas que el agente tiene disponibles
herramientas = [calcular_costo_envio]

# --- Prompt del agente ---
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

# --- Agente y ejecutor ---
# Crea el agente que decide si llamar a una herramienta o responder directo
agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

# Ejecutor que corre el ciclo: modelo -> herramienta -> modelo -> respuesta
ejecutor_agente = AgentExecutor(agent=agente, tools=herramientas)

# --- Memoria ---
# Diccionario que guarda un historial por cada sesión (session_id -> historial)
historiales = {}


def obtener_historial(session_id: str):
    """Devuelve el historial de la sesión; lo crea si todavía no existe."""
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
config = {"configurable": {"session_id": "cliente_123"}}

# Primera consulta: el agente debería usar la herramienta de costo de envío
resultado_1 = agente_con_memoria.invoke(
    {"entrada": ("¿Cuánto cuesta enviar un paquete de " "2kg a 300km?")}, config
)

# Muestra la respuesta final del agente
print(resultado_1["output"])
