"""Validación de la salida de la IA (Fase 3): esquema pydantic + reglas de negocio.

El diagnóstico lleva TODAS las debilidades: la salida debe cubrir exactamente los
factores débiles preseleccionados. Nunca se usa salida sin validar.
"""

import json

import pytest

from app.hallazgos import (
    HallazgoInvalidoError,
    preseleccionar_factores,
    validar_salida,
)
from app.scoring import calcular_scoring
from vase import sheet_vase


def _deb_ids():
    res = calcular_scoring(sheet_vase())
    return {f.factor_id for f in preseleccionar_factores(res)}


def _payload_completo(deb_ids):
    return {"debilidades": [{"factor_id": fid, "texto": f"hallazgo {fid}"} for fid in sorted(deb_ids)]}


def test_salida_valida_cubre_todas_pasa():
    deb_ids = _deb_ids()
    salida = validar_salida(json.dumps(_payload_completo(deb_ids)), deb_ids)
    assert {h.factor_id for h in salida.debilidades} == deb_ids


def test_json_malformado_rechazado():
    with pytest.raises(HallazgoInvalidoError):
        validar_salida("{esto no es json", _deb_ids())


def test_no_cumple_esquema_rechazado():
    raw = {"debilidades": [{"factor_id": 5}]}  # falta "texto"
    with pytest.raises(HallazgoInvalidoError):
        validar_salida(raw, _deb_ids())


def test_debilidad_sobre_factor_alto_rechazada():
    # el factor 7 (ALTO) no está preseleccionado
    raw = {"debilidades": [{"factor_id": 7, "texto": "x"}]}
    with pytest.raises(HallazgoInvalidoError):
        validar_salida(raw, _deb_ids())


def test_cobertura_incompleta_rechazada():
    deb_ids = _deb_ids()
    payload = _payload_completo(deb_ids)
    payload["debilidades"].pop()  # falta una debilidad
    with pytest.raises(HallazgoInvalidoError):
        validar_salida(payload, deb_ids)


def test_sin_debilidades_rechazado():
    raw = {"debilidades": []}
    with pytest.raises(HallazgoInvalidoError):
        validar_salida(raw, _deb_ids())


def test_factor_duplicado_rechazado():
    deb_ids = _deb_ids()
    payload = _payload_completo(deb_ids)
    payload["debilidades"].append({"factor_id": 5, "texto": "dup"})  # duplica el 5
    with pytest.raises(HallazgoInvalidoError):
        validar_salida(payload, deb_ids)


def test_texto_vacio_rechazado():
    deb_ids = _deb_ids()
    payload = _payload_completo(deb_ids)
    payload["debilidades"][0]["texto"] = "   "
    with pytest.raises(HallazgoInvalidoError):
        validar_salida(payload, deb_ids)
