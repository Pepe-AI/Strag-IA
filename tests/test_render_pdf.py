"""Chunk 3: radar PNG (matplotlib) + render_pdf (WeasyPrint).

`radar_png` corre en cualquier lado (matplotlib). `render_pdf` necesita las libs
nativas de WeasyPrint: el test se SALTA donde no están (p. ej. Windows sin GTK) y
corre en CI/Render.
"""

import pytest

from app.domain import HallazgoRenderable
from app.render import radar_png, render_pdf
from app.reporte import ensamblar_reporte
from app.scoring import calcular_scoring
from vase import sheet_vase


def _reporte():
    res = calcular_scoring(sheet_vase())
    deb = [
        HallazgoRenderable(
            factor_id=5,
            factor_nombre="Fidelización y Crecimiento de Clientes",
            media=1.5,
            texto="Sin retención, cada cliente que se va es ingreso perdido.",
            severidad="alta",
        ),
    ]
    return ensamblar_reporte(res, deb, empresa="VASE Sísmica", fecha="30/06/2026")


def test_radar_png_es_un_png_valido():
    png = radar_png(_reporte().radar)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 1000


def _weasyprint_ok() -> bool:
    try:
        from weasyprint import HTML  # noqa: F401

        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _weasyprint_ok(), reason="WeasyPrint sin libs nativas (Windows sin GTK)"
)
def test_render_pdf_es_un_pdf():
    pdf = render_pdf(_reporte())
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 2000
