# Agente de envíos con límites de autonomía: cuatro herramientas clasificadas
# por riesgo (bajo, medio, alto), aprobación humana para la de riesgo alto y
# registro de cada interacción en trazas_agente.jsonl.
#
# Correr desde la raíz del repo:  python src/agente_envios_supervisado.py

import json
import select
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()
# gemini-2.0-flash ya no está disponible (404); se usa el mismo modelo que
# agente_con_herramientas.py.
modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", timeout=30)


# --- Supervisión humana (Bloque 23) ---

registro_aprobaciones = []


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 10) -> bool:
    """Pide confirmación por consola. Si no hay respuesta dentro del tiempo
    límite, o la respuesta no es "s", cuenta como rechazo (falla segura)."""
    print(mensaje, end="", flush=True)
    listo, _, _ = select.select([sys.stdin], [], [], tiempo_limite_segundos)
    if not listo:
        print("\nSin respuesta a tiempo: se rechaza.")
        return False
    respuesta = sys.stdin.readline()
    return respuesta.strip().lower() == "s"


def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro_aprobaciones.append(
        {
            "herramienta": herramienta,
            "argumentos": argumentos,
            "aprobado": aprobado,
            "momento": datetime.now().isoformat(),
        }
    )


# --- Datos simulados ---

ENVIOS = {
    "AR12345": {
        "estado": "en tránsito, llega en 2 días",
        "direccion": "Calle Falsa 123",
    },
    "AR67890": {
        "estado": "entregado",
        "direccion": "Av. Libertador 1000",
    },
}

# Cada cambio de dirección guarda la anterior, para poder revertirlo.
registro_cambios_direccion = []


# --- Herramientas ---


# Riesgo BAJO: solo lee información.
@tool
def consultar_estado_envio(numero_seguimiento: str) -> str:
    """Consulta el estado y la dirección de entrega de un envío a partir de
    su número de seguimiento. Riesgo bajo: solo lee, no modifica nada."""
    envio = ENVIOS.get(numero_seguimiento)
    if envio is None:
        return f"No se encontró un envío con el número {numero_seguimiento}."
    return (
        f"Envío {numero_seguimiento}: {envio['estado']}. "
        f"Dirección de entrega: {envio['direccion']}."
    )


# Riesgo BAJO: solo calcula.
@tool
def calcular_costo_envio(peso_kg: float, distancia_km: float) -> str:
    """Calcula el costo estimado de un envío según su peso y la distancia.
    Usar cuando el usuario pregunta cuánto cuesta enviar algo. Riesgo bajo:
    solo calcula, no ejecuta ninguna acción externa."""
    costo = 500 + (peso_kg * 120) + (distancia_km * 3)
    return f"El costo estimado es de ${costo:.2f}."


# Riesgo MEDIO: escribe datos, pero el cambio es reversible.
@tool
def actualizar_direccion_entrega(numero_seguimiento: str, nueva_direccion: str) -> str:
    """Cambia la dirección de entrega de un envío que todavía no fue
    entregado. Riesgo medio: modifica datos, pero es reversible porque se
    guarda la dirección anterior. Usar solo si el usuario pide
    explícitamente cambiar la dirección."""
    envio = ENVIOS.get(numero_seguimiento)
    if envio is None:
        return f"No se encontró un envío con el número {numero_seguimiento}."
    if envio["estado"] == "entregado":
        return f"El envío {numero_seguimiento} ya fue entregado: no se puede cambiar la dirección."

    direccion_anterior = envio["direccion"]
    envio["direccion"] = nueva_direccion
    registro_cambios_direccion.append(
        {
            "numero_seguimiento": numero_seguimiento,
            "direccion_anterior": direccion_anterior,
            "direccion_nueva": nueva_direccion,
            "momento": datetime.now().isoformat(),
        }
    )
    return (
        f"Dirección del envío {numero_seguimiento} actualizada a "
        f"'{nueva_direccion}' (anterior: '{direccion_anterior}')."
    )


# Riesgo ALTO: mueve dinero de forma irreversible -> aprobación humana previa.
@tool
def generar_reembolso(numero_pedido: str, monto: float) -> str:
    """Genera un reembolso de dinero para un pedido. Riesgo alto: acción
    irreversible con impacto económico; requiere aprobación humana antes de
    ejecutarse."""
    mensaje = (
        f"El agente quiere reembolsar ${monto} para el pedido "
        f"{numero_pedido}. ¿Aprobar? (s/n): "
    )
    aprobado = esperar_aprobacion(mensaje)
    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado,
    )
    if not aprobado:
        return "Reembolso no aprobado por el supervisor humano."
    return f"Reembolso de ${monto} generado para el pedido {numero_pedido}."


# --- Agente ---

herramientas = [
    consultar_estado_envio,
    calcular_costo_envio,
    actualizar_direccion_entrega,
    generar_reembolso,
]

prompt_agente = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente de una empresa de envíos. Usa las herramientas "
            "disponibles solo cuando el usuario lo pida. Si un reembolso no es "
            "aprobado por el supervisor humano, informa al usuario y NO lo "
            "vuelvas a intentar.",
        ),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

# return_intermediate_steps=True: sin esto, la traza no tendría las acciones.
ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    return_intermediate_steps=True,
)


# --- Trazas (Bloque 23) ---


def texto_respuesta(output) -> str:
    """Con Gemini 3 la respuesta llega como lista de bloques
    ({"type": "text", "text": ..., "extras": {"signature": ...}}).
    Se guarda solo el texto para que la traza sea legible."""
    if isinstance(output, list):
        return "".join(
            bloque.get("text", "") for bloque in output if isinstance(bloque, dict)
        )
    return str(output)


def registrar_traza(session_id: str, entrada: str, resultado: dict) -> None:
    """Guarda una interacción como una línea JSON en trazas_agente.jsonl:
    qué se preguntó, qué herramientas se usaron y con qué argumentos, y la
    respuesta final."""
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": texto_respuesta(resultado["output"]),
    }
    with open("trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def marcar_repeticiones_sospechosas(archivo: str = "trazas_agente.jsonl") -> None:
    """Marca las sesiones donde la misma herramienta se invocó varias veces
    seguidas: un candidato a revisar a mano, no una conclusión definitiva."""
    try:
        with open(archivo, encoding="utf-8") as f:
            registros = [json.loads(linea) for linea in f]
    except FileNotFoundError:
        print(f"No se encontró '{archivo}'.")
        return

    for registro in registros:
        herramientas_usadas = [a["herramienta"] for a in registro.get("acciones", [])]
        for i in range(1, len(herramientas_usadas)):
            if herramientas_usadas[i] == herramientas_usadas[i - 1]:
                print(
                    f"Revisar: {registro['session_id']} usó "
                    f"'{herramientas_usadas[i]}' dos veces seguidas"
                )
                break


# --- Ejecución: un caso por nivel de riesgo ---

if __name__ == "__main__":
    casos = [
        ("cliente_101", "¿Cuánto cuesta enviar 2kg a 300km?"),  # bajo
        ("cliente_102", "¿Cuál es el estado del envío AR12345?"),  # bajo
        (
            "cliente_103",
            "Cambia la dirección de entrega del envío AR12345 a Av. Siempre Viva 742",
        ),  # medio
        ("cliente_104", "Reembolsa el pedido P1 por $100"),  # alto (aprobar: s)
        ("cliente_105", "Reembolsa el pedido P2 por $5000"),  # alto (rechazar: n)
    ]

    for session_id, entrada in casos:
        print(f"\n[{session_id}] {entrada}")
        resultado = ejecutor_agente.invoke({"entrada": entrada})
        print(f"\n-> {texto_respuesta(resultado['output'])}")
        registrar_traza(session_id, entrada, resultado)

    print("\nAprobaciones:", registro_aprobaciones)
    print("Cambios de dirección:", registro_cambios_direccion)
    print("\nRevisión de repeticiones:")
    marcar_repeticiones_sospechosas()
