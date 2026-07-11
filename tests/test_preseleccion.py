"""Pre-selección determinista de factores (Fase 3, parte pura).

El diagnóstico resalta TODAS las debilidades: Python elige todos los factores
bajos/medios (sin tope) para que la IA escriba sobre cada uno. Los factores altos
se siguen evaluando (radar) pero no generan hallazgo textual.
"""

from app.hallazgos import preseleccionar_factores
from app.scoring import calcular_scoring
from vase import sheet_vase


def test_preseleccion_vase_todos_los_debiles_ordenados():
    res = calcular_scoring(sheet_vase())
    deb = preseleccionar_factores(res)

    # TODOS los factores bajos/medios (el 7 es ALTO y queda fuera), media asc
    assert [f.factor_id for f in deb] == [5, 3, 4, 2, 6, 1]


def test_preseleccion_vase_solo_bajos_o_medios():
    res = calcular_scoring(sheet_vase())
    deb = preseleccionar_factores(res)

    assert all(f.banda in ("BAJO", "MEDIO") for f in deb)
    medias = [f.media for f in deb]
    assert medias == sorted(medias)  # más severo (más bajo) primero
