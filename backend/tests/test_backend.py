import asyncio
import json

import httpx
import pytest

from backend.main import app


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("AI_BASE_URL", "https://proveedor.example.com/v1/")
    monkeypatch.setenv("AI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("AI_MODEL", "modelo-de-prueba")
    async def enviar(entrada):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as cliente:
            return await cliente.request("POST", "/api/generar", json=entrada)

    return lambda entrada: asyncio.run(enviar(entrada))


@pytest.mark.parametrize("descripcion", ["  un gato  ", "x" * 200])
def test_generar_ascii(cliente, monkeypatch, descripcion):
    async def proveedor_simulado(self, url, **kwargs):
        assert url == "https://proveedor.example.com/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer clave-de-prueba"
        assert kwargs["json"]["model"] == "modelo-de-prueba"
        assert kwargs["json"]["messages"][-1]["content"] == descripcion.strip()
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"content": "```text\n  /\\_/\\\n ( o.o )\n```"}}]},
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", proveedor_simulado)
    respuesta = cliente({"descripcion": descripcion})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"ascii": "  /\\_/\\\n ( o.o )"}


@pytest.mark.parametrize("entrada", [{}, {"descripcion": "   "}, {"descripcion": "x" * 201}])
def test_entrada_invalida(cliente, monkeypatch, entrada):
    async def no_debe_llamar(self, *args, **kwargs):
        pytest.fail("Una entrada inválida no debe consumir la API de IA")

    monkeypatch.setattr(httpx.AsyncClient, "post", no_debe_llamar)
    assert cliente(entrada).status_code == 422


@pytest.mark.parametrize("fallo,estado", [("http", 502), ("timeout", 504), ("formato", 502)])
def test_error_del_proveedor(cliente, monkeypatch, fallo, estado):
    async def proveedor_simulado(self, url, **kwargs):
        peticion = httpx.Request("POST", url)
        if fallo == "timeout":
            raise httpx.ReadTimeout("detalle privado", request=peticion)
        if fallo == "http":
            return httpx.Response(401, request=peticion, text="detalle privado")
        return httpx.Response(200, request=peticion, json={"respuesta": "detalle privado"})

    monkeypatch.setattr(httpx.AsyncClient, "post", proveedor_simulado)
    respuesta = cliente({"descripcion": "un gato"})

    assert respuesta.status_code == estado
    assert isinstance(respuesta.json()["detail"], str)
    assert "detalle privado" not in json.dumps(respuesta.json())
