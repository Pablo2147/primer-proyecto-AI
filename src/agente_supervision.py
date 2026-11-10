"""Supervisión humana y trazabilidad para un agente de LangChain.

Este módulo tiene tres piezas que trabajan juntas:

1. Aprobación humana (esperar_aprobacion / generar_reembolso): antes de
   ejecutar una acción irreversible, el agente se detiene y le pide permiso
   a una persona por consola.
2. Registro de aprobaciones (registrar_aprobacion): deja constancia en
   memoria de cada decisión (aprobada o no) para poder auditarla.
3. Trazas (registrar_traza / marcar_repeticiones_sospechosas): guarda en un
   archivo cada interacción del agente y permite detectar comportamientos
   raros, como llamar a la misma herramienta varias veces seguidas.
"""

import json
import select
import sys
from datetime import datetime, timezone
from langchain_core.agents import AgentAction
from langchain_core.tools import tool

# Lista global en memoria con todas las decisiones de aprobación tomadas
# durante la ejecución. Se pierde al terminar el programa; para algo
# permanente habría que escribirla a un archivo o base de datos.
registro_aprobaciones = []


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 10) -> bool:
    """Muestra un mensaje y espera la respuesta del supervisor humano.

    Devuelve True solo si la persona escribe "s" antes de que se acabe el
    tiempo. Cualquier otra cosa (escribir "n", otra letra, o no responder)
    cuenta como rechazo: ante la duda, la acción NO se ejecuta.
    """
    print(mensaje)

    # select.select espera hasta que stdin tenga algo para leer o se venza
    # el tiempo límite. Así el agente no queda bloqueado para siempre si
    # nadie está mirando la consola.
    # Nota: select sobre stdin funciona en macOS/Linux, pero no en Windows.
    listo, _, _ = select.select([sys.stdin], [], [], tiempo_limite_segundos)
    if not listo:
        # Se agotó el tiempo sin respuesta: se trata como "no aprobado".
        return False

    respuesta = sys.stdin.readline()
    return respuesta.strip().lower() == "s"


def registrar_aprobacion(
    herramienta: str,
    argumentos: dict,
    aprobado: bool,
) -> None:
    """Agrega a registro_aprobaciones una entrada con qué herramienta se
    quiso usar, con qué argumentos, si se aprobó y cuándo."""
    registro_aprobaciones.append(
        {
            "herramienta": herramienta,
            "argumentos": argumentos,
            "aprobado": aprobado,
            "momento": datetime.now().isoformat(),
        }
    )


# El decorador @tool convierte la función en una herramienta que el agente
# puede decidir llamar. LangChain usa el docstring como descripción para que
# el modelo sepa cuándo y para qué usarla, por eso se deja explícito que la
# acción es irreversible y requiere aprobación.
@tool
def generar_reembolso(numero_pedido: str, monto: float) -> str:
    """Genera un reembolso para un pedido. Acción
    irreversible: requiere aprobación humana antes
    de ejecutarse."""
    # Paso 1: preparar la pregunta que verá el supervisor.
    mensaje = (
        f"El agente quiere reembolsar ${monto} "
        f"para el pedido {numero_pedido}. "
        f"¿Aprobar? (s/n): "
    )

    # Paso 2: pedir la decisión a la persona y guardarla en el registro,
    # tanto si aprueba como si rechaza (así queda constancia de ambos casos).
    aprobado = esperar_aprobacion(mensaje)
    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado,
    )

    # Paso 3: si no hubo aprobación, se corta aquí y no se hace el reembolso.
    # El texto devuelto es lo que "lee" el agente como resultado de la
    # herramienta, así puede explicarle al usuario por qué no se hizo.
    if not aprobado:
        return "Reembolso no aprobado por el " "supervisor humano."

    # Aquí iría la llamada real al sistema de pagos; este ejemplo solo
    # simula el resultado con un mensaje.
    return f"Reembolso de ${monto} generado para " f"el pedido {numero_pedido}."


def registrar_traza(
    session_id: str,
    entrada: str,
    resultado: dict,
) -> None:
    """Guarda una interacción del agente como una
    línea JSON en trazas_agente.jsonl: qué se
    preguntó, qué herramientas se usaron y con qué
    argumentos, y la respuesta final. Si "resultado"
    no trae "intermediate_steps" (por ejemplo, con
    return_intermediate_steps=False), acciones queda
    como una lista vacía en vez de fallar."""

    # Se arma un diccionario con todo lo que interesa de esta interacción.
    registro = {
        # UTC para que las horas sean comparables sin importar la zona.
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Identifica la conversación/cliente, para agrupar trazas después.
        "session_id": session_id,
        # Lo que el usuario le pidió al agente.
        "entrada": entrada,
        # intermediate_steps es una lista de pares (AgentAction, observación):
        #   - AgentAction: qué herramienta eligió el agente y con qué input.
        #   - observación: lo que devolvió esa herramienta.
        # Se usa .get(..., []) para no fallar si el agente no los devolvió.
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        # La respuesta que el agente le dio finalmente al usuario.
        "respuesta_final": resultado["output"],
    }

    # Formato JSON Lines (.jsonl): un JSON por línea. Se abre en modo "a"
    # (append) para ir agregando sin borrar lo anterior, y ensure_ascii=False
    # mantiene tildes y ñ legibles en vez de escapes como ó.
    with open("trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def marcar_repeticiones_sospechosas(
    archivo: str = "trazas_agente.jsonl",
) -> None:
    """Recorre un archivo de trazas y marca las
    sesiones donde la misma herramienta se invocó
    varias veces seguidas: un candidato a revisar a
    mano, no una conclusión definitiva."""
    # Se cargan todas las trazas: cada línea del archivo es un JSON.
    try:
        with open(archivo, encoding="utf-8") as f:
            registros = [json.loads(linea) for linea in f]
    except FileNotFoundError:
        # Aún no hay trazas: se avisa con un mensaje claro en vez de
        # dejar que el programa termine con un error.
        print(
            f"No se encontró '{archivo}'. Corre "
            "registrar_traza al menos una vez antes "
            "de revisar repeticiones."
        )
        return

    for registro in registros:
        # Se extrae solo la secuencia de nombres de herramientas usadas,
        # en orden. Ej.: ["buscar_pedido", "generar_reembolso", "generar_reembolso"]
        herramientas = [a["herramienta"] for a in registro.get("acciones", [])]

        # Se compara cada herramienta con la anterior; si son iguales, el
        # agente la llamó dos veces seguidas (posible bucle o reintento).
        for i in range(1, len(herramientas)):
            if herramientas[i] == herramientas[i - 1]:
                print(
                    f"Revisar: {registro['session_id']} usó "
                    f"'{herramientas[i]}' dos veces seguidas"
                )
                # Con una repetición basta para marcar la sesión; se pasa
                # a la siguiente para no imprimir avisos duplicados.
                break


# Este bloque solo corre al ejecutar el archivo directamente
# (python agente_supervision.py), no cuando otro módulo lo importa.
# Sirve como demo del flujo completo sin necesidad de un LLM real.
if __name__ == "__main__":
    entrada = "Reembolsa $1500 del pedido PED789"
    argumentos = {"numero_pedido": "PED789", "monto": 1500.0}

    # .invoke ejecuta la herramienta como lo haría el agente: pedirá
    # aprobación por consola y devolverá el texto del resultado.
    respuesta = generar_reembolso.invoke(argumentos)
    print(respuesta)
    print("registro:", registro_aprobaciones)

    # Se simula a mano lo que devolvería un AgentExecutor, para poder probar
    # registrar_traza sin montar un agente completo.
    # Resultado con la misma forma que devuelve AgentExecutor
    resultado = {
        "output": respuesta,
        "intermediate_steps": [
            (
                AgentAction(
                    tool="generar_reembolso",
                    tool_input=argumentos,
                    log="",
                ),
                respuesta,
            )
        ],
    }

    # Se guarda la traza en el archivo y luego se revisa si hay repeticiones.
    registrar_traza("cliente_456", entrada, resultado)
    marcar_repeticiones_sospechosas()
