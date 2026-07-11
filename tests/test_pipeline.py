"""Pipeline completo (Fase 8): leer→parse→score→IA→render→subir.

Se prueba el CABLEADO end-to-end con colaboradores falsos (sin red ni WeasyPrint):
scoring/parser/IA son reales; el lector, el render y la subida se inyectan.
"""

import json

from app.pipeline import ejecutar_pipeline
from vase import raw_completo

# Gemini falso: cubre los 7 factores (raw_completo = todo 2.0 → todos débiles).
_SALIDA = json.dumps(
    {"debilidades": [{"factor_id": i, "texto": f"hallazgo {i}"} for i in range(1, 8)]}
)


class GeminiFalso:
    def generar(self, prompt: str) -> str:
        return _SALIDA


def test_ejecutar_pipeline_cablea_todos_los_pasos():
    raw = raw_completo("ACME")
    subidas = []

    def subir_fn(drive, folder, nombre, pdf):
        subidas.append((folder, nombre, pdf))
        return {"id": "NEW_ID"}

    res = ejecutar_pipeline(
        "SHEET1",
        "10/07/2026",
        sheet_service=object(),
        drive_service=object(),
        gemini=GeminiFalso(),
        results_folder_id="FRES",
        leer_raw_fn=lambda svc, sid: raw,
        render_fn=lambda reporte: b"%PDF-fake",
        subir_fn=subir_fn,
    )

    assert res == {"id": "NEW_ID"}
    folder, nombre, pdf = subidas[0]
    assert folder == "FRES"
    assert nombre == "ACME_10_07_2026.pdf"  # nombre determinista (saneado)
    assert pdf == b"%PDF-fake"
