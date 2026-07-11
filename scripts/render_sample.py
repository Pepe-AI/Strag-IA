"""Genera un PDF de muestra con `render_pdf` (para verificar WeasyPrint en Linux).

Corre dentro del contenedor de `Dockerfile.pdfcheck`. Escribe el PDF en $OUT
(por defecto /out/diagnostico.pdf, que se monta a una carpeta del host).
"""

import os
import sys

sys.path.insert(0, os.getcwd())

from app.cell_map import FACTORES
from app.domain import FactorScore, HallazgoRenderable, ResultadoScoring
from app.render import render_pdf
from app.reporte import ensamblar_reporte
from app.scoring import banda_desde_porcentaje

medias = [3.14, 2.11, 1.6, 2.0, 1.5, 2.5, 3.75]
factores = [
    FactorScore(factor_id=f["id"], nombre=f["nombre"], media=m)
    for f, m in zip(FACTORES, medias)
]
puntaje = sum(medias) / 7
pct = puntaje / 4 * 100
res = ResultadoScoring(
    factores=factores, puntaje=puntaje, porcentaje=pct, banda=banda_desde_porcentaje(pct)
)

debiles = sorted((f for f in factores if f.media / 4 * 100 < 80), key=lambda x: x.media)
debil = [
    HallazgoRenderable(
        factor_id=f.factor_id,
        factor_nombre=f.nombre,
        media=f.media,
        texto="(placeholder) Aquí irá el hallazgo redactado por la IA a partir de la observación del consultor.",
        severidad="alta" if f.media / 4 * 100 < 60 else "media",
    )
    for f in debiles
]

rep = ensamblar_reporte(res, debil, empresa="VASE Sísmica", fecha="30/06/2026")
pdf = render_pdf(rep)

out = os.environ.get("OUT", "/out/diagnostico.pdf")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "wb") as fh:
    fh.write(pdf)
print("PDF escrito:", out, "|", len(pdf), "bytes")
