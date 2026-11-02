import os

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import HTTPException, Request


def exigir_sesion(request: Request) -> None:
    esquema, _, token = request.headers.get("Authorization", "").partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        raise HTTPException(401, "Debes iniciar sesión para generar un dibujo.", headers={"WWW-Authenticate": "Bearer"})

    clave = os.getenv("CLERK_SECRET_KEY", "").strip()
    origenes = [
        origen.strip()
        for origen in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",")
        if origen.strip()
    ]
    if not clave or not origenes:
        raise HTTPException(503, "El inicio de sesión no está configurado.")

    try:
        sesion = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=clave,
                authorized_parties=origenes,
                accepts_token=["session_token"],
                # Opcional: clave pública para validar sin consultar las claves a Clerk.
                jwt_key=os.getenv("CLERK_JWT_KEY") or None,
            ),
        )
    except Exception:
        raise HTTPException(503, "No se puede comprobar la sesión. Inténtalo de nuevo.") from None

    if not sesion.is_signed_in or not sesion.payload or not sesion.payload.get("sub"):
        raise HTTPException(401, "La sesión no es válida o ha caducado. Inicia sesión de nuevo.", headers={"WWW-Authenticate": "Bearer"})
