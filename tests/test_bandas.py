"""Regresión de las bandas (ARCHITECTURE §7): < 60 BAJO · 60–79 MEDIO · ≥ 80 ALTO.

Se ejercita por la API pública `calcular_scoring`, construyendo entradas cuyas
CALIFICA producen un % conocido. Incluye los bordes exactos 60.0 y 80.0.
"""

import pytest

from app.domain import FactorCrudo, RespuestaCruda, SheetNormalizado
from app.scoring import calcular_scoring


def _sheet_uniforme(califs: list[int]) -> SheetNormalizado:
    """7 factores con la misma lista de CALIFICA → misma media en todos."""
    factores = [
        FactorCrudo(
            factor_id=fid,
            nombre=f"F{fid}",
            respuestas=[
                RespuestaCruda(factor_id=fid, pregunta_idx=i, califica=c)
                for i, c in enumerate(califs)
            ],
        )
        for fid in range(1, 8)
    ]
    return SheetNormalizado(template_version="v1", empresa="X", factores=factores)


@pytest.mark.parametrize(
    "califs, porcentaje_esperado, banda_esperada",
    [
        ([0], 0.0, "BAJO"),
        ([2], 50.0, "BAJO"),
        ([2, 2, 2, 3, 3], 60.0, "MEDIO"),  # borde inferior de MEDIO
        ([3], 75.0, "MEDIO"),
        ([3, 3, 3, 3, 4], 80.0, "ALTO"),  # borde inferior de ALTO
        ([4], 100.0, "ALTO"),
    ],
)
def test_banda_segun_porcentaje(califs, porcentaje_esperado, banda_esperada):
    res = calcular_scoring(_sheet_uniforme(califs))
    assert res.porcentaje == pytest.approx(porcentaje_esperado)
    assert res.banda == banda_esperada
