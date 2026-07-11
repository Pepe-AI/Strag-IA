"""Tests de contrato del parser: cada Sheet mal formado debe fallar CLARO,
nunca producir un score parcial silencioso (ARCHITECTURE §8.3)."""

import pytest

from app.parser import (
    PlantillaIncompletaError,
    PlantillaVersionError,
    parse_sheet,
)
from vase import raw_completo


def test_version_desconocida():
    raw = raw_completo()
    raw["template_version"] = [["v99"]]  # versión que el parser no conoce
    with pytest.raises(PlantillaVersionError):
        parse_sheet(raw)


def test_named_range_calif_faltante():
    raw = raw_completo()
    del raw["calif_f3"]
    with pytest.raises(PlantillaIncompletaError):
        parse_sheet(raw)


def test_conteo_de_preguntas_incorrecto():
    raw = raw_completo()
    raw["calif_f1"] = raw["calif_f1"][:-1]  # una pregunta de menos
    with pytest.raises(PlantillaIncompletaError):
        parse_sheet(raw)


def test_celda_calif_vacia():
    raw = raw_completo()
    raw["calif_f1"][0] = []  # celda sin valor
    with pytest.raises(PlantillaIncompletaError):
        parse_sheet(raw)


def test_calif_fuera_de_rango():
    raw = raw_completo()
    raw["calif_f1"][0] = [5]  # fuera de 0..4
    with pytest.raises(PlantillaIncompletaError):
        parse_sheet(raw)


def test_empresa_vacia():
    raw = raw_completo()
    raw["empresa"] = [[""]]
    with pytest.raises(PlantillaIncompletaError):
        parse_sheet(raw)
