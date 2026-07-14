"""Orquestación de la IA con Gemini MOCKEADO (Fase 3).

Probamos NUESTRA lógica: validar (cobertura completa), reintentar una vez, y fallar
seguro al segundo fallo. El diagnóstico lleva TODAS las debilidades.
"""

import json

import pytest

from app.domain import EntradaIA, FactorParaIA
from app.hallazgos import (
    IAFallidaError,
    construir_prompt,
    generar_hallazgos,
)
from app.scoring import calcular_scoring
from vase import sheet_vase

# Cubre los 6 factores débiles de VASE, en orden de severidad.
_RAW_OK = json.dumps(
    {
        "debilidades": [
            {"factor_id": 5, "texto": "Postventa sin proceso."},
            {"factor_id": 3, "texto": "Formación informal."},
            {"factor_id": 4, "texto": "Desempeño irregular."},
            {"factor_id": 2, "texto": "Equipo sin estructura."},
            {"factor_id": 6, "texto": "Marketing irregular."},
            {"factor_id": 1, "texto": "Estrategia poco clara."},
        ]
    }
)


class ClienteFalso:
    """Doble de Gemini: devuelve las respuestas que le demos, en orden."""

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = 0

    def generar(self, prompt: str) -> str:
        self.llamadas += 1
        return self.respuestas.pop(0)


def test_exito_primer_intento_cubre_todas():
    res = calcular_scoring(sheet_vase())
    cli = ClienteFalso([_RAW_OK])

    deb = generar_hallazgos(res, "VASE Sísmica", cli)

    assert cli.llamadas == 1
    assert [h.factor_id for h in deb] == [5, 3, 4, 2, 6, 1]
    assert deb[0].severidad == "alta"  # factor 5, BAJO
    assert deb[-1].severidad == "media"  # factor 1, MEDIO


def test_reintenta_una_vez_y_tiene_exito():
    res = calcular_scoring(sheet_vase())
    cli = ClienteFalso(["{json roto", _RAW_OK])

    deb = generar_hallazgos(res, "VASE Sísmica", cli)

    assert cli.llamadas == 2
    assert len(deb) == 6


def test_fallback_tras_dos_fallos():
    res = calcular_scoring(sheet_vase())
    cli = ClienteFalso(["{roto", "tambien roto"])

    with pytest.raises(IAFallidaError):
        generar_hallazgos(res, "VASE Sísmica", cli)

    assert cli.llamadas == 2  # 1 intento + 1 reintento, no más


def test_construir_prompt_aterriza_en_observaciones_y_prohibe_numeros():
    entrada = EntradaIA(
        empresa="VASE Sísmica",
        porcentaje_global=59.3,
        banda_global="BAJO",
        factores_debilidad=[
            FactorParaIA(
                factor_id=5,
                nombre="Fidelización y Crecimiento de Clientes",
                media=1.5,
                banda="BAJO",
                observaciones="No hay estrategia de recompra; se pierde el cliente tras la venta",
            )
        ],
    )

    prompt = construir_prompt(entrada)

    assert "VASE Sísmica" in prompt
    assert "Fidelización y Crecimiento de Clientes" in prompt
    # la OBSERVACIÓN (la evidencia) llega al prompt y se le presenta como tal
    assert "No hay estrategia de recompra" in prompt
    assert "Observación del consultor" in prompt
    # guardrails
    assert "NO inventes" in prompt
    assert "NO menciones puntajes" in prompt  # que no repita el número
    assert "JSON" in prompt
    assert "fortaleza" not in prompt.lower()
    # no le damos la media: si no la ve, no puede repetirla
    assert "1.5" not in prompt
