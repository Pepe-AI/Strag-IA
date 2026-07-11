"""Módulo de IA / hallazgos (Fase 3).

El diagnóstico resalta SOLO debilidades. Parte pura: a partir del scoring, Python
pre-selecciona los factores débiles (banda baja/media) y la IA escribe prosa sobre
ellos; nunca elige factores ni números. Los factores altos se siguen evaluando
(radar) pero no generan hallazgo textual.
"""

import json
from typing import Protocol

from pydantic import ValidationError

from app.domain import (
    EntradaIA,
    FactorParaIA,
    HallazgoRenderable,
    ResultadoScoring,
    SalidaIA,
)
from app.scoring import banda_desde_porcentaje


class HallazgoInvalidoError(Exception):
    """La salida de la IA no cumple el esquema o una regla de negocio."""


class IAFallidaError(Exception):
    """La IA no produjo una salida válida ni tras el reintento (fallback seguro)."""


class ClienteIA(Protocol):
    """Interfaz del cliente de IA. El Gemini real y el doble de tests la cumplen."""

    def generar(self, prompt: str) -> str: ...


def banda_de_factor(media: float):
    """Banda de un factor desde su media (mismos umbrales que el global)."""
    return banda_desde_porcentaje(media / 4 * 100)


def preseleccionar_factores(resultado: ResultadoScoring) -> list[FactorParaIA]:
    """TODOS los factores débiles (banda baja/media) sobre los que la IA redactará,
    los más severos (media más baja) primero. Sin tope: se muestran todas las
    debilidades encontradas."""
    debilidades = []
    for f in resultado.factores:
        banda = banda_de_factor(f.media)
        if banda in ("BAJO", "MEDIO"):
            debilidades.append(
                FactorParaIA(
                    factor_id=f.factor_id,
                    nombre=f.nombre,
                    media=f.media,
                    banda=banda,
                    observaciones=f.observaciones,
                )
            )

    debilidades.sort(key=lambda x: x.media)
    return debilidades


def validar_salida(raw: str | dict, deb_ids: set[int]) -> SalidaIA:
    """Valida la salida cruda de la IA: JSON → esquema pydantic → reglas de negocio.

    Levanta HallazgoInvalidoError ante cualquier desviación. Nunca devuelve datos
    sin validar.
    """
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise HallazgoInvalidoError(f"JSON malformado: {e}") from e
    else:
        data = raw

    try:
        salida = SalidaIA.model_validate(data)
    except ValidationError as e:
        raise HallazgoInvalidoError(f"no cumple el esquema: {e}") from e

    deb = [h.factor_id for h in salida.debilidades]

    if len(set(deb)) != len(deb):
        raise HallazgoInvalidoError("factor_id duplicado")
    # Cobertura completa: deben aparecer TODAS las debilidades preseleccionadas
    # (ni de más —factor no preseleccionado/alto— ni de menos).
    if set(deb) != deb_ids:
        faltan = deb_ids - set(deb)
        sobran = set(deb) - deb_ids
        raise HallazgoInvalidoError(
            f"cobertura incorrecta de debilidades (faltan {faltan or '∅'}, sobran {sobran or '∅'})"
        )
    if any(not h.texto.strip() for h in salida.debilidades):
        raise HallazgoInvalidoError("texto vacío")

    return salida


def enriquecer(
    salida: SalidaIA, resultado: ResultadoScoring
) -> list[HallazgoRenderable]:
    """Combina la prosa de la IA con metadatos del scoring (severidad, media, nombre).

    La severidad sale de la banda del factor (BAJO→alta, MEDIO→media).
    """
    por_id = {f.factor_id: f for f in resultado.factores}

    def _ren(h) -> HallazgoRenderable:
        fs = por_id[h.factor_id]
        severidad = "alta" if banda_de_factor(fs.media) == "BAJO" else "media"
        return HallazgoRenderable(
            factor_id=fs.factor_id,
            factor_nombre=fs.nombre,
            media=fs.media,
            texto=h.texto,
            severidad=severidad,
        )

    return [_ren(h) for h in salida.debilidades]


def construir_prompt(entrada: EntradaIA) -> str:
    """Capa base + grounding/guardrails. La capa-persona del cliente es TBD."""

    def _factor_linea(f: FactorParaIA) -> str:
        obs = f.observaciones.strip() or "(sin observaciones)"
        return f"- factor {f.factor_id} «{f.nombre}» (media {f.media:.2f}/4, {f.banda}). Observaciones: {obs}"

    lineas = [
        "Eres un analista de ventas. Redacta hallazgos BREVES y concretos.",
        "Reglas: usa SOLO la información dada; NO inventes cifras, datos ni causas.",
        f"Empresa: {entrada.empresa}. Cumplimiento global: "
        f"{entrada.porcentaje_global:.1f}% ({entrada.banda_global}).",
        "Escribe una debilidad por cada factor en DEBILIDADES.",
        "DEBILIDADES:",
        *[_factor_linea(f) for f in entrada.factores_debilidad],
        'Responde SOLO JSON: {"debilidades":[{"factor_id":int,"texto":str}]}',
    ]
    return "\n".join(lineas)


def generar_hallazgos(
    resultado: ResultadoScoring, empresa: str, cliente: ClienteIA
) -> list[HallazgoRenderable]:
    """Una llamada a la IA, un reintento si la salida es inválida, luego fallback seguro.

    Devuelve las debilidades ya enriquecidas, o levanta IAFallidaError sin emitir
    nunca salida sin validar.
    """
    deb_factores = preseleccionar_factores(resultado)
    if not deb_factores:  # sin debilidades (todos los factores altos): nada que redactar
        return []
    entrada = EntradaIA(
        empresa=empresa,
        porcentaje_global=resultado.porcentaje,
        banda_global=resultado.banda,
        factores_debilidad=deb_factores,
    )
    prompt = construir_prompt(entrada)
    deb_ids = {f.factor_id for f in deb_factores}

    ultimo_error = None
    for _ in range(2):  # 1 intento + 1 reintento
        raw = cliente.generar(prompt)
        try:
            salida = validar_salida(raw, deb_ids)
            return enriquecer(salida, resultado)
        except HallazgoInvalidoError as e:
            ultimo_error = e

    raise IAFallidaError(
        f"la IA no produjo salida válida tras el reintento: {ultimo_error}"
    ) from ultimo_error
