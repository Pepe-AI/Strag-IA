"""Render del PDF (Fase 4).

`construir_html` es PURO (str de entrada → str de salida): arma el layout Stragia de
2 páginas. Se prueba sin WeasyPrint. `render_pdf` (chunk 3) le añade el radar y hace
HTML→PDF. El diseño es de marca fija; la paleta sale del asset de Stragia.
"""

import base64
import html as _html
import io
import math
from functools import lru_cache
from pathlib import Path

from app.domain import FactorScore, HallazgoRenderable, ReportePDF

_ASSET_LOGO = Path(__file__).parent / "assets" / "stragia_logo.png"

# Números "playful" de la pág. 2, ciclando la paleta de marca (como el diseño).
_NUM_COLORS = ["#d76b2c", "#17a2c4", "#123a5e"]

# Etiquetas cortas de los ejes del radar (como el diseño).
_ETIQUETA_RADAR = {
    1: "Planeación", 2: "Equipo", 3: "Gestión", 4: "Prospección",
    5: "Fidelización", 6: "Marketing", 7: "Mercado",
}

_CSS = """
@page { size: Letter; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Helvetica Neue', Arial, sans-serif; color: #22303c; }
.page {
  position: relative; width: 8.5in; min-height: 11in; background: #faf6ef;
  padding: 0.55in 0.6in 0; display: flex; flex-direction: column;
}
.page.first { page-break-after: always; }
.serif { font-family: Georgia, 'Times New Roman', serif; }

/* Header */
.header { display: flex; justify-content: space-between; align-items: flex-start; }
.logo { height: 74px; }
.head-right { text-align: right; }
.doc-title { font-size: 20px; font-weight: 800; color: #123a5e; line-height: 1.15; letter-spacing: .3px; }
.doc-sub { margin-top: 8px; font-size: 11px; color: #8b9098; }
.rule { height: 3px; background: #123a5e; margin: 14px 0 22px; }

/* Cards row */
.cards { display: flex; gap: 20px; }
.card { background: #ffffff; border: 1px solid #e6e3db; border-radius: 12px; padding: 20px; }
.card-label { font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #8b9098; text-align: center; }
.card-global { width: 38%; display: flex; flex-direction: column; align-items: center; }
.card-radar { width: 62%; }

/* Ring */
.ring-wrap { position: relative; width: 150px; height: 150px; margin: 14px 0 6px; }
.ring-center { position: absolute; top: 0; left: 0; width: 150px; height: 150px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; }
.pct { font-size: 34px; font-weight: 700; color: #123a5e; }
.pct-label { font-size: 9px; letter-spacing: 1.5px; color: #8b9098; }
.score { margin-top: 8px; font-size: 15px; color: #22303c; }
.score-num { font-size: 46px; font-weight: 700; color: #123a5e; }
.score-label { font-size: 10px; letter-spacing: 2px; color: #8b9098; margin-top: 2px; }
.pill { margin: 14px 0; background: #d76b2c; color: #fff; font-weight: 700;
  letter-spacing: 3px; font-size: 13px; padding: 8px 22px; border-radius: 6px; }
.banda-msg { font-size: 12.5px; line-height: 1.5; color: #3a4653; text-align: center; }

.radar { display: block; width: 100%; margin-top: 6px; }

/* Desglose */
.desglose { margin-top: 26px; }
.desglose-head { display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 2px solid #123a5e; padding-bottom: 6px; }
.dh-title { font-size: 15px; font-weight: 800; color: #123a5e; letter-spacing: .5px; }
.dh-sub { font-size: 10px; color: #8b9098; }
.desglose-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 40px; margin-top: 16px; }
.factor-row { }
.factor-line { display: flex; justify-content: space-between; align-items: baseline; }
.factor-name { font-size: 12.5px; font-weight: 700; color: #123a5e; }
.factor-score { font-size: 12.5px; color: #8b9098; }
.factor-score b { color: #d76b2c; }
.bar { height: 6px; background: #e9e6df; border-radius: 4px; margin-top: 6px; overflow: hidden; }
.bar-fill { height: 6px; background: #123a5e; border-radius: 4px; }

/* Footer */
.footer { margin-top: auto; margin-left: -0.6in; margin-right: -0.6in;
  background: #0f2f4c; color: #cdd6df; padding: 12px 0.6in; display: flex;
  justify-content: space-between; align-items: center; font-size: 10px; }
.foot-brand { font-weight: 800; letter-spacing: 2px; }
.foot-brand2 { color: #17a2c4; }

/* Página 2 */
.p2-title { font-size: 24px; font-weight: 800; color: #123a5e; border-left: 5px solid #d76b2c;
  padding-left: 12px; }
.p2-sub { font-size: 11px; color: #8b9098; padding-left: 17px; margin-top: 2px; margin-bottom: 20px; }
.accion-list { display: flex; flex-direction: column; gap: 12px; }
.accion-card { display: flex; gap: 16px; align-items: flex-start; background: #fff;
  border: 1px solid #e6e3db; border-left: 5px solid #d76b2c; border-radius: 8px; padding: 16px 18px; }
.ac-num { font-family: Georgia, serif; font-size: 30px; font-weight: 700; min-width: 34px; text-align: center; }
.ac-body { flex: 1; }
.ac-line { display: flex; justify-content: space-between; align-items: baseline; }
.ac-name { font-size: 14px; font-weight: 700; color: #123a5e; }
.ac-score { font-size: 12.5px; color: #8b9098; }
.ac-score b { color: #d76b2c; }
.ac-text { font-size: 12px; line-height: 1.5; color: #3a4653; margin-top: 6px; }
"""


@lru_cache(maxsize=1)
def _logo_data_uri() -> str:
    if not _ASSET_LOGO.exists():
        return ""
    b64 = base64.b64encode(_ASSET_LOGO.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _esc(texto: str) -> str:
    return _html.escape(str(texto))


def _anillo_svg(porcentaje: float) -> str:
    r = 52
    c = 2 * math.pi * r
    dash = max(0.0, min(1.0, porcentaje / 100)) * c
    return (
        f'<svg viewBox="0 0 120 120" width="150" height="150">'
        f'<circle cx="60" cy="60" r="{r}" fill="none" stroke="#e9e6df" stroke-width="11"/>'
        f'<circle cx="60" cy="60" r="{r}" fill="none" stroke="#123a5e" stroke-width="11"'
        f' stroke-linecap="round" stroke-dasharray="{dash:.1f} {c:.1f}"'
        f' transform="rotate(-90 60 60)"/>'
        f"</svg>"
    )


def _header(reporte: ReportePDF, con_titulo: bool) -> str:
    logo = f'<img class="logo" src="{_logo_data_uri()}"/>'
    sub = f"{_esc(reporte.empresa)} · {_esc(reporte.fecha)}"
    if con_titulo:
        right = (
            '<div class="head-right">'
            '<div class="doc-title">DIAGNÓSTICO DE VENTAS<br>& MARKETING DIGITAL</div>'
            f'<div class="doc-sub">{sub}</div></div>'
        )
    else:
        right = f'<div class="head-right"><div class="doc-sub">{sub}</div></div>'
    return f'<div class="header">{logo}{right}</div><div class="rule"></div>'


def _footer(pagina: str) -> str:
    return (
        '<div class="footer">'
        '<span class="foot-brand">STRAGIA <span class="foot-brand2">SALES SCIENCE</span></span>'
        f'<span class="foot-info">contacto@stragia.com · www.stragia.com · {pagina}</span>'
        "</div>"
    )


def _fila_desglose(f: FactorScore) -> str:
    ancho = max(0.0, min(1.0, f.media / 4)) * 100
    return (
        '<div class="factor-row">'
        f'<div class="factor-line"><span class="factor-name">{_esc(f.nombre)}</span>'
        f'<span class="factor-score"><b>{f.media:.1f}</b>/4</span></div>'
        f'<div class="bar"><div class="bar-fill" style="width:{ancho:.1f}%"></div></div>'
        "</div>"
    )


def _tarjeta_accion(i: int, d: HallazgoRenderable) -> str:
    color = _NUM_COLORS[(i - 1) % len(_NUM_COLORS)]
    return (
        '<div class="accion-card">'
        f'<div class="ac-num" style="color:{color}">{i}</div>'
        '<div class="ac-body">'
        f'<div class="ac-line"><span class="ac-name">{_esc(d.factor_nombre)}</span>'
        f'<span class="ac-score"><b>{d.media:.1f}</b>/4</span></div>'
        f'<div class="ac-text">{_esc(d.texto)}</div></div>'
        "</div>"
    )


def construir_html(reporte: ReportePDF, radar_data_uri: str = "") -> str:
    """Arma el HTML de las 2 páginas. `radar_data_uri` = PNG del radar (vacío en tests)."""
    # Desglose: los 7 factores, de mayor a menor media.
    desglose = "".join(
        _fila_desglose(f) for f in sorted(reporte.radar, key=lambda x: -x.media)
    )
    # Plan de acción: las debilidades ya vienen ordenadas por prioridad (severidad).
    acciones = "".join(
        _tarjeta_accion(i, d) for i, d in enumerate(reporte.debilidades, start=1)
    )

    pagina1 = (
        '<div class="page first">'
        + _header(reporte, con_titulo=True)
        + '<div class="cards">'
        '<section class="card card-global">'
        '<div class="card-label">RESULTADO GLOBAL</div>'
        f'<div class="ring-wrap">{_anillo_svg(reporte.porcentaje)}'
        f'<div class="ring-center"><div class="pct">{reporte.porcentaje:.0f}%</div>'
        '<div class="pct-label">CUMPLIMIENTO</div></div></div>'
        f'<div class="score"><span class="score-num">{reporte.puntaje:.1f}</span> / 4</div>'
        '<div class="score-label">PUNTAJE DE MADUREZ</div>'
        f'<div class="pill">{_esc(reporte.banda)}</div>'
        f'<div class="banda-msg">{_esc(reporte.mensaje_banda)}</div>'
        "</section>"
        '<section class="card card-radar">'
        '<div class="card-label">RADAR DE FACTORES</div>'
        f'<img class="radar" src="{radar_data_uri}"/>'
        "</section>"
        "</div>"
        '<div class="desglose">'
        '<div class="desglose-head"><span class="dh-title">DESGLOSE POR FACTOR</span>'
        '<span class="dh-sub">Ordenado de mayor a menor · escala 0–4</span></div>'
        f'<div class="desglose-grid">{desglose}</div>'
        "</div>"
        + _footer("01 / 02")
        + "</div>"
    )

    pagina2 = (
        '<div class="page">'
        + _header(reporte, con_titulo=False)
        + '<div class="p2-title">HACIA DÓNDE DIRIGIR TU ENERGÍA</div>'
        '<div class="p2-sub">Plan de acción por factor · ordenado de mayor a menor prioridad</div>'
        f'<div class="accion-list">{acciones}</div>'
        + _footer("02 / 02")
        + "</div>"
    )

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>{pagina1}{pagina2}</body></html>"
    )


def radar_png(factores: list[FactorScore]) -> bytes:
    """Radar de 7 ejes como PNG (transparente). Polígono navy + relleno cian; la
    telaraña (radios/anillos) en negro para contraste (estilo aprobado)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fs = sorted(factores, key=lambda x: x.factor_id)
    labels = [_ETIQUETA_RADAR.get(f.factor_id, f.nombre.split()[0]) for f in fs]
    vals = [f.media for f in fs]
    n = len(fs)
    angles = [i / float(n) * 2 * math.pi for i in range(n)] + [0.0]
    v = vals + vals[:1]

    fig = plt.figure(figsize=(4.4, 4.4))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 4)
    ax.plot(angles, v, color="#123a5e", linewidth=2)  # contorno del polígono (datos)
    ax.fill(angles, v, color="#17a2c4", alpha=0.22)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9, color="#123a5e")
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["1", "2", "3", "4"], fontsize=7, color="#8b9098")
    ax.spines["polar"].set_color("#000000")  # anillo exterior de la telaraña
    ax.grid(color="#000000", linewidth=0.6)  # radios + anillos (NO el polígono)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return buf.getvalue()


def render_pdf(reporte: ReportePDF) -> bytes:
    """Genera el radar, lo embebe y produce el PDF con WeasyPrint.

    Import perezoso de WeasyPrint: en Windows sin libs nativas falla aquí (no al
    importar el módulo), y el resto de `render` sigue usable/testeable.
    """
    from weasyprint import HTML

    png = radar_png(reporte.radar)
    uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    html = construir_html(reporte, radar_data_uri=uri)
    return HTML(string=html).write_pdf()
