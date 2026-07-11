"""Pipeline de generación del diagnóstico (Fase 8).

`ejecutar_pipeline` encadena los pasos ya construidos y probados. Los colaboradores
externos (lector de Sheets, render, subida) se inyectan con defaults de producción,
para poder probar el cableado con fakes.
"""

import datetime

from app.drive_io import nombre_pdf, subir_pdf
from app.hallazgos import generar_hallazgos
from app.parser import parse_sheet
from app.render import render_pdf
from app.reporte import ensamblar_reporte
from app.scoring import calcular_scoring
from app.sheets_adapter import leer_raw


def fecha_hoy() -> str:
    return datetime.date.today().strftime("%d/%m/%Y")


def ejecutar_pipeline(
    sheet_id: str,
    fecha: str,
    *,
    sheet_service,
    drive_service,
    gemini,
    results_folder_id: str,
    leer_raw_fn=leer_raw,
    render_fn=render_pdf,
    subir_fn=subir_pdf,
) -> dict:
    """Lee el Sheet, puntúa, redacta hallazgos, renderiza y sube el PDF.

    La empresa sale del Sheet (named range `empresa`, vía parser) — fuente de verdad.
    """
    raw = leer_raw_fn(sheet_service, sheet_id)
    sheet = parse_sheet(raw)
    resultado = calcular_scoring(sheet)
    debilidades = generar_hallazgos(resultado, sheet.empresa, gemini)
    reporte = ensamblar_reporte(
        resultado, debilidades, empresa=sheet.empresa, fecha=fecha
    )
    pdf = render_fn(reporte)
    archivo = nombre_pdf(sheet.empresa, fecha)
    return subir_fn(drive_service, results_folder_id, archivo, pdf)
