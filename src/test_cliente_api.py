from unittest.mock import patch, Mock

import pytest

from cliente_api import enviar_peticion


def test_enviar_peticion_credencial_invalida():
    respuesta_falsa = Mock(status_code=401)

    with patch("cliente_api.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion({"pregunta": "test"})


def test_enviar_peticion_limite_de_uso():
    respuesta_falsa = Mock(status_code=429)

    with patch("cliente_api.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion({"pregunta": "test"})


def test_enviar_peticion_exito():
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}

    with patch("cliente_api.requests.post", return_value=respuesta_falsa):
        resultado = enviar_peticion({"pregunta": "test"})

    assert resultado == {"texto": "respuesta simulada"}
