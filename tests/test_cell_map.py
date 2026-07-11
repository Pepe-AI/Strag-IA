"""Guardas del contrato `cell_map` — fija la estructura canónica (v2, 52 preguntas)."""

from app.cell_map import FACTORES, TEMPLATE_VERSION, TOTAL_PREGUNTAS

# Estructura canónica confirmada por el cliente (cuestionario de 52).
EXPECTED = [
    (1, "Planeación y estrategia comercial", 7),
    (2, "Equipo de ventas", 9),
    (3, "Gestión y medición comercial", 7),
    (4, "Prospección y Pipeline", 6),
    (5, "Fidelización y Crecimiento de Clientes", 6),
    (6, "Marketing digital", 12),
    (7, "Mercado y competencia", 5),
]


def test_version_es_v2():
    assert TEMPLATE_VERSION == "v2"


def test_factores_coinciden_con_el_contrato():
    got = [(f["id"], f["nombre"], f["n_preguntas"]) for f in FACTORES]
    assert got == EXPECTED


def test_total_preguntas_52():
    assert TOTAL_PREGUNTAS == 52 == sum(f["n_preguntas"] for f in FACTORES)


def test_named_ranges_unicos():
    rangos = [f["rango_calif"] for f in FACTORES] + [f["rango_obs"] for f in FACTORES]
    assert len(rangos) == len(set(rangos))
