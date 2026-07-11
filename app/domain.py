"""Modelos de dominio (ARCHITECTURE §3.2).

pydantic valida todo dato externo en la frontera: un CALIFICA fuera de 0..4 o un
factor_id inválido fallan al construirse, nunca llegan al cálculo.
"""

from typing import Literal

from pydantic import BaseModel, Field

Banda = Literal["BAJO", "MEDIO", "ALTO"]


class RespuestaCruda(BaseModel):
    """Una pregunta puntuada. Solo CALIFICA puntúa; SI/NO es informativo (no se modela)."""

    factor_id: int = Field(ge=1, le=7)
    pregunta_idx: int = Field(ge=0)
    califica: int = Field(ge=0, le=4)


class FactorCrudo(BaseModel):
    """Un factor con sus respuestas crudas y las observaciones (grounding de la IA)."""

    factor_id: int = Field(ge=1, le=7)
    nombre: str
    respuestas: list[RespuestaCruda]
    observaciones: str = ""


class SheetNormalizado(BaseModel):
    """Salida del parser (Fase 2) y entrada del scoring."""

    template_version: str
    empresa: str
    factores: list[FactorCrudo]


class FactorScore(BaseModel):
    """Media de un factor (eje del radar, escala 0..4)."""

    factor_id: int
    nombre: str
    media: float
    observaciones: str = ""


class ResultadoScoring(BaseModel):
    """Salida del scoring: las 7 medias + agregados deterministas."""

    factores: list[FactorScore]
    puntaje: float
    porcentaje: float
    banda: Banda


# --- Modelos de IA / hallazgos (ARCHITECTURE §3.3) ---

Severidad = Literal["alta", "media", "baja"]


class FactorParaIA(BaseModel):
    """Lo que se le pasa a la IA por factor preseleccionado (grounding)."""

    factor_id: int
    nombre: str
    media: float
    banda: Banda
    observaciones: str = ""


class EntradaIA(BaseModel):
    """Lo que se le manda a la IA: factores débiles preseleccionados + contexto global.

    El diagnóstico resalta solo debilidades; las fortalezas se evalúan (radar) pero
    no se redactan.
    """

    empresa: str
    porcentaje_global: float
    banda_global: Banda
    factores_debilidad: list[FactorParaIA]


class HallazgoIA(BaseModel):
    """Salida CRUDA de la IA: solo prosa, atada a un factor. Sin números nuevos."""

    factor_id: int
    texto: str


class SalidaIA(BaseModel):
    """Lo que devuelve la IA, antes de enriquecer: solo debilidades."""

    debilidades: list[HallazgoIA]


class HallazgoRenderable(BaseModel):
    """Hallazgo (debilidad) listo para el PDF: prosa de la IA + metadatos de Python.

    La severidad la deriva Python desde la banda del factor (nunca la IA).
    """

    factor_id: int
    factor_nombre: str
    media: float
    texto: str
    severidad: Severidad


class ReportePDF(BaseModel):
    """Todo lo que el renderer necesita para el PDF (2 páginas). Ya calculado y
    validado; el renderer no decide nada (ARCHITECTURE §3.4)."""

    empresa: str
    fecha: str
    puntaje: float
    porcentaje: float
    banda: Banda
    mensaje_banda: str  # frase fija por banda (determinista; no la IA)
    radar: list[FactorScore]  # los 7 factores (radar + desglose, pág. 1)
    debilidades: list[HallazgoRenderable]  # solo factores débiles, con texto (pág. 2)
