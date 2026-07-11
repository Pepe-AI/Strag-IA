"""Ensamblado del reporte (Fase 4, parte determinista).

Junta el resultado del scoring + los hallazgos de la IA + metadatos en un
`ReportePDF`. La frase por banda es fija (la elige Python, nunca la IA).
"""

from app.domain import Banda, HallazgoRenderable, ReportePDF, ResultadoScoring

# Frases fijas por banda (las provee el cliente; nunca la IA).
# TODO: ALTO (≥80%) sigue pendiente — placeholder hasta recibir el texto.
_MENSAJES_BANDA: dict[str, str] = {
    "BAJO": "Baja madurez comercial, debilidades críticas.",
    "MEDIO": "Media madurez comercial con debilidades detectadas.",
    "ALTO": "[PLACEHOLDER — mensaje ALTO pendiente]",
}


def mensaje_banda(banda: Banda) -> str:
    return _MENSAJES_BANDA[banda]


def ensamblar_reporte(
    resultado: ResultadoScoring,
    debilidades: list[HallazgoRenderable],
    empresa: str,
    fecha: str,
) -> ReportePDF:
    return ReportePDF(
        empresa=empresa,
        fecha=fecha,
        puntaje=resultado.puntaje,
        porcentaje=resultado.porcentaje,
        banda=resultado.banda,
        mensaje_banda=mensaje_banda(resultado.banda),
        radar=resultado.factores,
        debilidades=debilidades,
    )
