"""Motor de scoring determinista (ARCHITECTURE §7).

Funciones puras: dadas las CALIFICA crudas, calculan medias por factor, PUNTAJE,
% y banda. Recalcula SIEMPRE desde crudo; nunca confía en fórmulas cacheadas.
"""

from collections.abc import Sequence

from app.domain import Banda, FactorScore, ResultadoScoring, SheetNormalizado


def _media(valores: Sequence[float]) -> float:
    return sum(valores) / len(valores)


def banda_desde_porcentaje(porcentaje: float) -> Banda:
    if porcentaje < 60:
        return "BAJO"
    if porcentaje < 80:
        return "MEDIO"
    return "ALTO"


def calcular_scoring(sheet: SheetNormalizado) -> ResultadoScoring:
    factores = [
        FactorScore(
            factor_id=f.factor_id,
            nombre=f.nombre,
            media=_media([r.califica for r in f.respuestas]),
            observaciones=f.observaciones,
        )
        for f in sheet.factores
    ]
    puntaje = _media([f.media for f in factores])
    porcentaje = puntaje / 4 * 100
    return ResultadoScoring(
        factores=factores,
        puntaje=puntaje,
        porcentaje=porcentaje,
        banda=banda_desde_porcentaje(porcentaje),
    )
