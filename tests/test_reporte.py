"""Ensamblado del reporte para el PDF (Fase 4, parte determinista).

`mensaje_banda` es fijo por banda (no lo decide la IA). `ensamblar_reporte` junta
scoring + hallazgos + metadatos en el `ReportePDF` que consumirá el renderer.
"""

from app.domain import HallazgoRenderable
from app.reporte import ensamblar_reporte, mensaje_banda
from app.scoring import calcular_scoring
from vase import sheet_vase

_BAJO = "Baja madurez comercial, debilidades críticas."
_MEDIO = "Media madurez comercial con debilidades detectadas."


def test_mensaje_banda_bajo_y_medio_verbatim():
    assert mensaje_banda("BAJO") == _BAJO
    assert mensaje_banda("MEDIO") == _MEDIO


def test_mensaje_banda_devuelve_texto_para_cada_banda():
    for b in ("BAJO", "MEDIO", "ALTO"):
        assert isinstance(mensaje_banda(b), str) and mensaje_banda(b).strip()


def test_ensamblar_reporte():
    res = calcular_scoring(sheet_vase())
    debilidades = [
        HallazgoRenderable(
            factor_id=5,
            factor_nombre="Postventa / cuentas clave",
            media=1.5,
            texto="Postventa sin proceso definido.",
            severidad="alta",
        ),
    ]

    rep = ensamblar_reporte(
        res, debilidades, empresa="VASE Sísmica", fecha="2026-06-30"
    )

    assert rep.empresa == "VASE Sísmica"
    assert rep.fecha == "2026-06-30"
    assert rep.puntaje == res.puntaje
    assert rep.porcentaje == res.porcentaje
    assert rep.banda == res.banda
    assert rep.mensaje_banda == mensaje_banda(res.banda)
    assert len(rep.radar) == 7  # los 7 factores (radar + desglose)
    assert rep.debilidades == debilidades
