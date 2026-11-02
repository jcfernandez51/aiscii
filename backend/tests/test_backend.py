import asyncio
import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.main import app


@pytest.fixture
def crear_token(monkeypatch):
    # Claves efímeras de prueba: el SDK valida los tokens sin acceder a Clerk.
    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    publica = privada.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_ficticia")
    monkeypatch.setenv("CLERK_JWT_KEY", publica)
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:5173")

    def crear(fallo=None):
        ahora = int(time.time())
        datos = {
            "sub": "user_prueba",
            "sid": "sess_prueba",
            "iss": "https://clerk.example.com",
            "iat": ahora,
            "nbf": ahora - 1,
            "exp": ahora + 60,
            "azp": "http://localhost:5173",
        }
        firma = privada
        if fallo == "caducado":
            datos["exp"] = ahora - 60
        elif fallo == "origen":
            datos["azp"] = "https://otro.example.com"
        elif fallo == "firma":
            firma = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return jwt.encode(datos, firma, algorithm="RS256", headers={"kid": "clave-prueba"})

    return crear


@pytest.fixture
def cliente(monkeypatch, crear_token):
    monkeypatch.setenv("AI_BASE_URL", "https://proveedor.example.com/v1/")
    monkeypatch.setenv("AI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("AI_MODEL", "modelo-de-prueba")
    async def enviar(entrada, autenticar, token):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as cliente:
            headers = {"Authorization": f"Bearer {token or crear_token()}"} if autenticar else {}
            return await cliente.request("POST", "/api/generar", json=entrada, headers=headers)

    return lambda entrada, autenticar=True, token=None: asyncio.run(enviar(entrada, autenticar, token))


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
            json={"choices": [{"message": {"content": "  /\\_/\\\n ( o.o )"}}]},
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


@pytest.mark.parametrize("fallo", ["sin_token", "invalido", "caducado", "origen", "firma"])
def test_rechaza_sin_sesion_valida(cliente, crear_token, monkeypatch, fallo):
    async def no_debe_llamar(self, *args, **kwargs):
        pytest.fail("Una petición sin sesión válida no debe consumir la API de IA")

    monkeypatch.setattr(httpx.AsyncClient, "post", no_debe_llamar)
    token = "token-invalido" if fallo == "invalido" else crear_token(fallo)
    respuesta = cliente({"descripcion": "un pato"}, autenticar=fallo != "sin_token", token=token)

    assert respuesta.status_code == 401
    assert respuesta.headers["www-authenticate"] == "Bearer"
