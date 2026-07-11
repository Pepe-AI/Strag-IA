"""Adapter de Sheets: traduce una respuesta `batchGet` a la forma cruda.

Se prueba con un `service` falso inyectado (sin red ni google-api-python-client):
lo que se verifica es la LÓGICA del adapter (qué pide y cómo mapea), no un mock.
"""

from app.parser import parse_sheet
from app.sheets_adapter import leer_raw, ranges_a_leer
from vase import raw_completo


class FakeService:
    """Imita service.spreadsheets().values().batchGet(...).execute()."""

    def __init__(self, resp):
        self.resp = resp
        self.captured = {}

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def batchGet(self, **kwargs):
        self.captured = kwargs
        return self

    def execute(self):
        return self.resp


def _resp_desde(raw, nombres):
    return {
        "spreadsheetId": "X",
        "valueRanges": [{"range": n, "values": raw[n]} for n in nombres],
    }


def test_leer_raw_pide_named_ranges_unformatted_y_mapea():
    raw = raw_completo()
    nombres = ranges_a_leer()
    svc = FakeService(_resp_desde(raw, nombres))

    out = leer_raw(svc, "SHEET_ID")

    assert svc.captured["spreadsheetId"] == "SHEET_ID"
    assert svc.captured["ranges"] == nombres
    assert svc.captured["valueRenderOption"] == "UNFORMATTED_VALUE"
    assert out == raw
    # y lo producido alimenta al parser sin romper
    parse_sheet(out)


def test_leer_raw_values_ausente_es_lista_vacia():
    nombres = ranges_a_leer()
    resp = {"valueRanges": [{"range": n} for n in nombres]}  # sin "values"
    out = leer_raw(FakeService(resp), "SHEET_ID")
    assert out[nombres[0]] == []


def test_ranges_no_incluye_los_calculados_en_vivo():
    # El parser recalcula; no debe pedir puntaje/porcentaje/banda.
    nombres = ranges_a_leer()
    assert "puntaje" not in nombres
    assert "porcentaje" not in nombres
    assert "banda" not in nombres
