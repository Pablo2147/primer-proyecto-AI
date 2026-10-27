import time, random
from typing import Callable, Any
from cliente_api import armar_peticion, enviar_peticion, extraer_texto


def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_base: float = 2,
    espera_maxima: float = 30,
) -> Any:
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                raise
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            time.sleep(espera + random.uniform(0, espera * 0.1))


def consultar_modelo(
    pregunta: str,
    system_instruction: str = "",
) -> str:
    cuerpo = armar_peticion(pregunta, system_instruction)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(cuerpo))
    except TimeoutError:
        raise RuntimeError(
            "El servicio no respondió tras varios intentos. Intenta más tarde."
        )
    registrar_costo(respuesta)
    return extraer_texto(respuesta)


COSTO_POR_1000_TOKENS = 0.002  # referencial, ajusta según el modelo que uses

costo_total_sesion = 0.0


def registrar_costo(respuesta: dict) -> float:
    global costo_total_sesion
    uso = respuesta.get("usageMetadata", {})
    total_tokens = uso.get("totalTokenCount", 0)
    costo_estimado = (total_tokens / 1000) * COSTO_POR_1000_TOKENS
    costo_total_sesion += costo_estimado
    return costo_estimado
