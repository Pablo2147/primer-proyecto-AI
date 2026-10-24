import time
from typing import Callable, Any
from cliente_api import armar_peticion, enviar_peticion, extraer_texto


def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_segundos: int = 2,
) -> Any:
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                raise
            print(
                f"Intento {intento} de {intentos} falló por límite de uso. Reintentando..."
            )
            time.sleep(espera_segundos)


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
    return extraer_texto(respuesta)
