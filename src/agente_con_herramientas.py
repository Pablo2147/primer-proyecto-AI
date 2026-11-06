from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)

# ChatPromptTemplate: plantilla del prompt como lista de mensajes
# MessagesPlaceholder: espacio reservado para mensajes dinámicos (scratchpad del agente)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

# Paso 1. Configurar entorno y herramientas
load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", timeout=10)


def formatear_monto(monto: float) -> str:
    """Formatea un monto sin decimales y con punto como separador de miles."""
    return f"${monto:,.0f}".replace(",", ".")


@tool
def consultar_saldo_cuenta(numero_cuenta: str) -> str:
    """Consulta el saldo actual de una cuenta
    bancaria a partir de su número de cuenta.
    Usar cuando el usuario pregunta cuánto dinero
    tiene en su cuenta."""
    # Base de datos simulada: número de cuenta -> saldo disponible
    saldos = {
        "CTA-1001": 1250000,
        "CTA-2002": 87300,
    }
    saldo = saldos.get(numero_cuenta)
    # Si la cuenta no existe, se informa en texto para que el agente lo comunique
    if saldo is None:
        return "No se encontró una cuenta con ese número."
    return f"El saldo de la cuenta {numero_cuenta} es de {formatear_monto(saldo)}."


@tool
def calcular_cuota_prestamo(monto: float, tasa_anual: float, meses: int) -> str:
    """Calcula la cuota mensual de un préstamo
    según el monto solicitado, la tasa de interés
    anual (en porcentaje, por ejemplo 12 para 12%)
    y el plazo en meses. Usar cuando el usuario
    pregunta cuánto pagaría por mes por un préstamo."""
    # Tasa mensual en decimal: 12% anual -> 0.01 mensual
    tasa_mensual = tasa_anual / 100 / 12

    # Si la tasa es 0, la cuota es simplemente el monto dividido en partes iguales
    if tasa_mensual == 0:
        cuota = monto / meses
    else:
        cuota = monto * tasa_mensual / (1 - (1 + tasa_mensual) ** -meses)

    total_pagado = cuota * meses
    # Devuelve texto (str) para que el agente pueda razonar y redactar la respuesta
    return (
        f"La cuota mensual es de {formatear_monto(cuota)}. "
        f"Total a pagar en {meses} meses: {formatear_monto(total_pagado)}."
    )


# Lista de herramientas que el agente tendrá disponibles
herramientas = [consultar_saldo_cuenta, calcular_cuota_prestamo]

# Prompt: rol del asistente, pregunta del usuario y scratchpad del agente
prompt_agente = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente virtual de un banco. Usa las "
            "herramientas disponibles para responder con datos "
            "reales. No inventes saldos ni cálculos.",
        ),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

# Paso 2. Armar el agente con AgentExecutor
agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

# return_intermediate_steps=True permite verificar qué herramienta eligió el agente
ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True,
    return_intermediate_steps=True,
)

# Paso 3. Validar con intermediate_steps
# Pruebas manuales: cada pregunta debería disparar una herramienta distinta.
# Formato: (pregunta, herramienta esperada)
pruebas = [
    ("¿Cuál es el saldo de mi cuenta CTA-1001?", "consultar_saldo_cuenta"),
    (
        "Si pido un préstamo de 1.000.000 al 12% anual a 24 meses, "
        "¿cuánto pago por mes?",
        "calcular_cuota_prestamo",
    ),
]

for pregunta, herramienta_esperada in pruebas:
    print(f"\n=== Pregunta: {pregunta}")
    resultado = ejecutor_agente.invoke({"entrada": pregunta})
    print("Respuesta:", resultado["output"])

    # Cada paso es (accion, observacion): qué herramienta llamó el modelo y qué devolvió
    herramientas_usadas = []
    for accion, observacion in resultado["intermediate_steps"]:
        herramientas_usadas.append(accion.tool)
        print(accion.tool, accion.tool_input, "->", observacion)

    # Confirma que el agente eligió la herramienta correcta
    estado = "OK" if herramienta_esperada in herramientas_usadas else "FALLÓ"
    print(
        f"[{estado}] esperada: {herramienta_esperada} | usadas: {herramientas_usadas}"
    )
