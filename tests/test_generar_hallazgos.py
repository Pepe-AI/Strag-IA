"""Orquestación de la IA con Gemini MOCKEADO (Fase 3).

Probamos NUESTRA lógica: validar (cobertura completa), reintentar una vez, y fallar
seguro al segundo fallo. El diagnóstico lleva TODAS las debilidades.
"""

import json

import pytest

from app.domain import EntradaIA
from app.hallazgos import (
    IAFallidaError,
    construir_prompt,
    generar_hallazgos,
    preseleccionar_factores,
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


def test_construir_prompt_incluye_grounding_y_factores():
    res = calcular_scoring(sheet_vase())
    deb = preseleccionar_factores(res)
    entrada = EntradaIA(
        empresa="VASE Sísmica",
        porcentaje_global=res.porcentaje,
        banda_global=res.banda,
        factores_debilidad=deb,
    )

    prompt = construir_prompt(entrada)

    assert "VASE Sísmica" in prompt
    assert "Postventa / cuentas clave" in prompt  # un factor preseleccionado
    assert "NO inventes" in prompt  # guardrail
    assert "JSON" in prompt  # formato de salida pedido
    assert "fortaleza" not in prompt.lower()  # ya no se piden fortalezas
