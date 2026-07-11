"""Armado del procesador (Fase 8): envuelve el pipeline en el ciclo de corrida.

Se prueba el pegamento (éxito → sin email; fallo → email) con un pipeline falso;
los clientes reales de Google se verifican en el smoke e2e.
"""

from app.wiring import armar_procesador


def test_procesador_exito_no_manda_email():
    emails = []
    proc = armar_procesador(
        sheets=None,
        drive=None,
        gemini=None,
        results_folder_id="F",
        enviar_email=lambda rid, e: emails.append(rid),
        pipeline_fn=lambda *a, **k: {"id": "ok"},
    )
    proc("S1", "ACME", "run1")
    assert emails == []


def test_procesador_fallo_manda_email():
    emails = []

    def boom(*a, **k):
        raise ValueError("x")

    proc = armar_procesador(
        sheets=None,
        drive=None,
        gemini=None,
        results_folder_id="F",
        enviar_email=lambda rid, e: emails.append((rid, str(e))),
        pipeline_fn=boom,
    )
    proc("S1", "ACME", "run2")
    assert emails == [("run2", "x")]
