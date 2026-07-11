"""Golden-file del motor de scoring contra el caso real de VASE.

Los valores esperados se derivaron del archivo de ejemplo (hojas "Score ventas &
digital" y "Evaluación"). El .xlsx se usa SOLO como fuente de estos números; el
mapa de celdas de producción vive en `app/cell_map.py` (Fase 2).
"""

import pytest

from app.scoring import calcular_scoring
from vase import sheet_vase


def test_golden_vase_medias_por_factor():
    res = calcular_scoring(sheet_vase())
    medias = {f.factor_id: f.media for f in res.factores}

    assert medias[1] == pytest.approx(3.142857142857143)
    assert medias[2] == pytest.approx(2.111111111111111)
    assert medias[3] == pytest.approx(1.6)
    assert medias[4] == pytest.approx(2.0)
    assert medias[5] == pytest.approx(1.5)
    assert medias[6] == pytest.approx(2.5)
    assert medias[7] == pytest.approx(3.75)


def test_golden_vase_puntaje_porcentaje_banda():
    res = calcular_scoring(sheet_vase())

    assert res.puntaje == pytest.approx(2.3719954648526076)
    assert res.porcentaje == pytest.approx(59.29988662131519)
    assert res.banda == "BAJO"
