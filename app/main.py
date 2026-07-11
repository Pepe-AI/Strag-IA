"""Servicio FastAPI — webhook fire-and-ack (Fase 5).

Valida (secreto → rate-limit → allowlist), agenda el pipeline en background y
responde 202 rápido (ARCHITECTURE §3.1, §4). Toda la lógica pesada corre después
del 202; el trigger (Apps Script) no espera.

Las piezas externas (settings, checker de allowlist, procesador, rate-limiter) se
inyectan como dependencias → mockeables en tests; los clientes reales se cablean en
la Fase 8.
"""

import os
import uuid
from collections.abc import Callable

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.security import RateLimiter, validar_secreto

app = FastAPI(title="Stragia — diagnósticos")


# --- contratos ---

class WebhookPayload(BaseModel):
    sheetId: str
    nombre: str


class WebhookAck(BaseModel):
    status: str = "accepted"
    runId: str


class Settings(BaseModel):
    secret: str
    input_folder_id: str


# --- dependencias (overridable en tests; clientes reales en Fase 8) ---

def get_settings() -> Settings:
    return Settings(
        secret=os.getenv("WEBHOOK_SECRET", ""),
        input_folder_id=os.getenv("INPUT_FOLDER_ID", ""),
    )


def get_allowlist_checker() -> Callable[[str], bool]:
    """Checker real (allowlist por carpeta de Drive), construido una vez desde env.
    Import perezoso: no carga el SDK de Google al importar el módulo."""
    from app.wiring import servicios

    return servicios()[0]


def get_procesador() -> Callable[[str, str, str], None]:
    """Procesador real (pipeline completo + notificaciones), una vez desde env."""
    from app.wiring import servicios

    return servicios()[1]


_RATE = RateLimiter(max_solicitudes=int(os.getenv("RATE_MAX", "10")), ventana_seg=60)


def get_rate_limiter() -> RateLimiter:
    return _RATE


# --- 422 → 400 (el contrato usa 400 Bad Request para payload malformado) ---

@app.exception_handler(RequestValidationError)
async def _payload_invalido(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": "payload inválido"})


@app.post("/v1/diagnosticos", status_code=202, response_model=WebhookAck)
def crear_diagnostico(
    payload: WebhookPayload,
    background: BackgroundTasks,
    request: Request,
    x_stragia_secret: str = Header(default=""),
    settings: Settings = Depends(get_settings),
    checker: Callable[[str], bool] = Depends(get_allowlist_checker),
    procesar: Callable[[str, str, str], None] = Depends(get_procesador),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> WebhookAck:
    if not validar_secreto(x_stragia_secret, settings.secret):
        raise HTTPException(status_code=401, detail="secreto inválido")

    clave = request.client.host if request.client else "desconocido"
    if not limiter.permitir(clave):
        raise HTTPException(status_code=429, detail="demasiadas solicitudes")

    if not checker(payload.sheetId):
        raise HTTPException(status_code=403, detail="sheetId no autorizado")

    run_id = uuid.uuid4().hex
    background.add_task(procesar, payload.sheetId, payload.nombre, run_id)
    return WebhookAck(runId=run_id)
