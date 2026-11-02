from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, StringConstraints

from backend.gen import generar_ascii
from backend.auth import exigir_sesion


app = FastAPI(title="aiscii")


class Peticion(BaseModel):
    descripcion: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]


class Respuesta(BaseModel):
    ascii: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/generar", response_model=Respuesta, dependencies=[Depends(exigir_sesion)])
async def generar(peticion: Peticion):
    dibujo = await generar_ascii(peticion.descripcion)
    return Respuesta(ascii=dibujo)


# Servir frontend junto a la api
app.frontend(
    "/",
    directory=Path(__file__).resolve().parent.parent / "frontend" / "dist",
    check_dir=False,
)
