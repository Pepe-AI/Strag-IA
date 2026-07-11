"""Tests de contrato del parser contra `cell_map` (Fase 2).

El parser consume la forma cruda (estilo Sheets `batchGet`) y produce
`SheetNormalizado`, o falla claro. No toca red: las entradas son fixtures que se
adaptan al `cell_map` vigente.
"""

from app.cell_map import FACTORES, TEMPLATE_VERSION
from app.parser import parse_sheet
from app.scoring import calcular_scoring
from vase import raw_completo


def test_parse_estructura():
    sheet = parse_sheet(raw_completo("ACME"))

    assert sheet.empresa == "ACME"
    assert sheet.template_version == TEMPLATE_VERSION
    assert [f.factor_id for f in sheet.factores] == [1, 2, 3, 4, 5, 6, 7]
    conteos = {f.factor_id: len(f.respuestas) for f in sheet.factores}
    assert conteos == {f["id"]: f["n_preguntas"] for f in FACTORES}


def test_parse_alimenta_scoring():
    sheet = parse_sheet(raw_completo())
    res = calcular_scoring(sheet)

    assert len(res.factores) == 7
    assert 0 <= res.porcentaje <= 100
    assert res.banda in ("BAJO", "MEDIO", "ALTO")
