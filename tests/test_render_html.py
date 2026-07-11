"""`construir_html` (Fase 4): layout Stragia de 2 páginas, función PURA.

Se prueba sin WeasyPrint: solo se verifica que el HTML contenga los datos correctos.
El detalle visual se valida a ojo abriendo el HTML en el navegador.
"""

from app.domain import HallazgoRenderable
from app.render import construir_html
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
            texto="Sin estrategia de retención, cada cliente que se va es ingreso perdido.",
            severidad="alta",
        ),
        HallazgoRenderable(
            factor_id=3,
            factor_nombre="Gestión y medición comercial",
            media=1.6,
            texto="Sin CRM ni KPIs, el equipo opera a ciegas.",
            severidad="alta",
        ),
    ]
    return ensamblar_reporte(res, deb, empresa="VASE Sísmica", fecha="30/06/2026")


def test_html_contiene_encabezado_y_banda():
    html = construir_html(_reporte())
    assert "VASE Sísmica" in html
    assert "30/06/2026" in html
    assert "BAJO" in html
    assert "debilidades críticas" in html  # mensaje_banda (BAJO)


def test_html_contiene_los_7_factores_del_desglose():
    rep = _reporte()
    html = construir_html(rep)
    for f in rep.radar:
        assert f.nombre in html


def test_html_contiene_texto_de_cada_debilidad():
    rep = _reporte()
    html = construir_html(rep)
    for d in rep.debilidades:
        assert d.texto in html


def test_html_tiene_dos_paginas():
    html = construir_html(_reporte())
    assert html.count('class="page') == 2  # "page first" y "page"


def test_html_inyecta_el_radar():
    html = construir_html(_reporte(), radar_data_uri="data:image/png;base64,ABC123")
    assert "data:image/png;base64,ABC123" in html
