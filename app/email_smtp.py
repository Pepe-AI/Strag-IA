"""Envío de email de alerta por SMTP (Fase 8).

Solo se usa cuando una corrida falla (ARCHITECTURE §9). `smtplib.SMTP` se inyecta
para poder probar sin red; el sender resultante encaja en `ejecutar_corrida`.
"""

import smtplib
from collections.abc import Callable
from email.message import EmailMessage

from pydantic import BaseModel


class EmailConfig(BaseModel):
    host: str
    port: int = 587
    user: str
    password: str
    email_from: str
    email_to: str


def _construir_mensaje(cfg: EmailConfig, run_id: str, error: Exception) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = cfg.email_from
    msg["To"] = cfg.email_to
    msg["Subject"] = f"[Stragia] Falló un diagnóstico ({run_id})"
    msg.set_content(
        f"La generación del diagnóstico (run {run_id}) falló y no se produjo PDF.\n\n"
        f"Error: {error}\n\n"
        "Revisa los logs del servicio para el detalle."
    )
    return msg


def enviar_email_smtp(
    cfg: EmailConfig,
    run_id: str,
    error: Exception,
    smtp_factory=smtplib.SMTP,
) -> None:
    """Envía la alerta vía SMTP con STARTTLS (Gmail: smtp.gmail.com:587)."""
    msg = _construir_mensaje(cfg, run_id, error)
    with smtp_factory(cfg.host, cfg.port) as servidor:
        servidor.starttls()
        servidor.login(cfg.user, cfg.password)
        servidor.send_message(msg)


def crear_enviador(
    cfg: EmailConfig, smtp_factory=smtplib.SMTP
) -> Callable[[str, Exception], None]:
    """Devuelve un `enviar_email(run_id, error)` listo para `ejecutar_corrida`."""

    def enviar(run_id: str, error: Exception) -> None:
        enviar_email_smtp(cfg, run_id, error, smtp_factory=smtp_factory)

    return enviar
