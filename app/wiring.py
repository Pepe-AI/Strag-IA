"""Cableado de producción (Fase 8): construye clientes reales desde la config y
arma el checker de allowlist y el procesador que usa el webhook.

`armar_procesador` (pegamento) se prueba con fakes; los `construir_*` reales usan
el SDK y se verifican en el smoke e2e.
"""

from collections.abc import Callable
from functools import lru_cache

from app.config import Config, cargar_config
from app.email_smtp import crear_enviador
from app.gemini import crear_cliente_gemini
from app.google_clients import (
    construir_credenciales_sa,
    construir_credenciales_usuario,
    construir_drive,
    construir_sheets,
)
from app.notificaciones import ejecutar_corrida
from app.pipeline import ejecutar_pipeline, fecha_hoy
from app.security import sheet_en_carpeta


def armar_procesador(
    *,
    sheets,
    drive,
    gemini,
    results_folder_id: str,
    enviar_email: Callable[[str, Exception], None],
    pipeline_fn=ejecutar_pipeline,
) -> Callable[[str, str, str], None]:
    """Envuelve el pipeline en `ejecutar_corrida` (started/success/failed + email)."""

    def procesar(sheet_id: str, nombre: str, run_id: str) -> None:
        ejecutar_corrida(
            run_id,
            trabajo=lambda: pipeline_fn(
                sheet_id,
                fecha_hoy(),
                sheet_service=sheets,
                drive_service=drive,
                gemini=gemini,
                results_folder_id=results_folder_id,
            ),
            enviar_email=enviar_email,
        )

    return procesar


def _construir_clientes(cfg: Config):
    creds_sa = construir_credenciales_sa(cfg.service_account_info)
    creds_user = construir_credenciales_usuario(
        cfg.oauth_client_id, cfg.oauth_client_secret, cfg.oauth_refresh_token
    )
    return {
        "sheets": construir_sheets(creds_sa),  # SA: lee el Sheet
        "drive_sa": construir_drive(creds_sa),  # SA: allowlist (parents)
        "drive_user": construir_drive(creds_user),  # OAuth-user: sube el PDF
        "gemini": crear_cliente_gemini(cfg.gemini_api_key, cfg.gemini_model),
    }


def construir_allowlist_checker(cfg: Config, drive=None) -> Callable[[str], bool]:
    if drive is None:
        drive = construir_drive(construir_credenciales_sa(cfg.service_account_info))
    return lambda sheet_id: sheet_en_carpeta(sheet_id, drive, cfg.input_folder_id)


@lru_cache(maxsize=1)
def servicios() -> tuple[Callable[[str], bool], Callable[[str, str, str], None]]:
    """Construye (una vez) el checker de allowlist y el procesador reales desde env."""
    cfg = cargar_config()
    clientes = _construir_clientes(cfg)
    enviar = crear_enviador(cfg.email) if cfg.email else (lambda rid, e: None)
    checker = construir_allowlist_checker(cfg, drive=clientes["drive_sa"])
    procesador = armar_procesador(
        sheets=clientes["sheets"],  # SA lee
        drive=clientes["drive_user"],  # OAuth-user sube
        gemini=clientes["gemini"],
        results_folder_id=cfg.results_folder_id,
        enviar_email=enviar,
    )
    return checker, procesador
