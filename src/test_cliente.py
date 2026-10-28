import pytest, cliente

from unittest.mock import patch

from cliente import con_reintento, consultar_modelo


@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    cliente.costo_total_sesion = 0
    yield


def test_con_reintento_espera_entre_intentos():
    intentos = {"n": 0}

    def funcion_que_falla_una_vez():
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise TimeoutError("simulado")
        return "ok"

    with patch("cliente.time.sleep") as mock_sleep:
        resultado = con_reintento(funcion_que_falla_una_vez)

    assert resultado == "ok"
    mock_sleep.assert_called_once()


def test_con_reintento_agota_intentos():
    def siempre_falla():
        raise TimeoutError("simulado")

    with patch("cliente.time.sleep"):
        with pytest.raises(TimeoutError):
            con_reintento(siempre_falla, intentos=3)


def test_con_reintento_no_reintenta_value_error():
    llamadas = {"n": 0}

    def funcion_con_value_error():
        llamadas["n"] += 1
        raise ValueError("no reintentable")

    with patch("cliente.time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            con_reintento(funcion_con_value_error, intentos=3)

    assert llamadas["n"] == 1
    mock_sleep.assert_not_called()


def test_consultar_modelo_convierte_error():
    error_simulado = TimeoutError("simulado")

    with patch("cliente.con_reintento", side_effect=error_simulado):
        with pytest.raises(RuntimeError):
            consultar_modelo("pregunta de prueba")


def test_registrar_costo_acumula():
    cliente.costo_total_sesion = 0
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}}
    costo = cliente.registrar_costo(respuesta_falsa)

    assert costo == cliente.COSTO_POR_1000_TOKENS
    assert cliente.costo_total_sesion == cliente.COSTO_POR_1000_TOKENS
