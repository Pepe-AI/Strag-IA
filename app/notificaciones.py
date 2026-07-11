"""Notificaciones y observabilidad (Fase 6).

El registro por corrida es un log estructurado (JSON) a stdout — que en Render ES
la tabla de corridas (sin DB). Un evento `started` sin `success`/`failed` para un
`run_id` señala un job muerto (ARCHITECTURE §9). En fallo, además, email.
"""

import json
import logging
from collections.abc import Callable
from typing import Literal

_log = logging.getLogger("stragia.corrida")

Estado = Literal["started", "success", "failed"]


def evento_corrida(estado: Estado, run_id: str, **campos) -> None:
    """Emite un evento estructurado de la corrida (una línea JSON)."""
    _log.info(json.dumps({"estado": estado, "run_id": run_id, **campos}, ensure_ascii=False))


def ejecutar_corrida(
    run_id: str,
    trabajo: Callable[[], None],
    enviar_email: Callable[[str, Exception], None],
) -> Estado:
    """Envuelve el trabajo de una corrida (fire-and-forget): emite started y luego
    success, o failed + email si algo revienta. El fallo NO se propaga: notificar
    ES el manejo del error."""
    evento_corrida("started", run_id)
    try:
        trabajo()
    except Exception as e:
        evento_corrida("failed", run_id, error=str(e))
        enviar_email(run_id, e)
        return "failed"
    evento_corrida("success", run_id)
    return "success"
