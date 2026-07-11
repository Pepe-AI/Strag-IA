"""Notificaciones / observabilidad (Fase 6).

Registro por corrida = log estructurado (started/success/failed) + email en fallo
(ARCHITECTURE §9). `enviar_email` se inyecta; el SMTP real llega en la Fase 8.
"""

import json
import logging

from app.notificaciones import ejecutar_corrida, evento_corrida

_LOGGER = "stragia.corrida"


def _estados(caplog):
    return [json.loads(r.getMessage())["estado"] for r in caplog.records]


def test_evento_corrida_emite_json(caplog):
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        evento_corrida("started", "run123", sheet_id="S1")
    data = json.loads(caplog.records[-1].getMessage())
    assert data == {"estado": "started", "run_id": "run123", "sheet_id": "S1"}


def test_ejecutar_corrida_exito_sin_email(caplog):
    emails = []
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        estado = ejecutar_corrida(
            "r1", trabajo=lambda: None, enviar_email=lambda rid, e: emails.append(rid)
        )
    assert estado == "success"
    assert _estados(caplog) == ["started", "success"]
    assert emails == []


def test_ejecutar_corrida_fallo_emite_failed_y_email(caplog):
    emails = []

    def trabajo():
        raise ValueError("boom")

    with caplog.at_level(logging.INFO, logger=_LOGGER):
        estado = ejecutar_corrida(
            "r2",
            trabajo=trabajo,
            enviar_email=lambda rid, e: emails.append((rid, str(e))),
        )
    assert estado == "failed"
    assert _estados(caplog) == ["started", "failed"]
    assert emails == [("r2", "boom")]  # el fallo NO se propaga; se notifica


def test_email_que_revienta_no_tumba_la_corrida(caplog):
    def trabajo():
        raise ValueError("boom")

    def enviar_que_falla(rid, e):
        raise RuntimeError("SMTP caído")

    with caplog.at_level(logging.INFO, logger=_LOGGER):
        estado = ejecutar_corrida("r3", trabajo=trabajo, enviar_email=enviar_que_falla)

    assert estado == "failed"  # no propaga el error del email
