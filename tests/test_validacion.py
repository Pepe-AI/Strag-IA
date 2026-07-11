"""Validación de dominio: pydantic rechaza datos fuera de contrato en la frontera.

Un CALIFICA fuera de 0..4 o un factor_id fuera de 1..7 no deben poder construirse,
para que un dato inválido nunca llegue al cálculo (riesgo central del proyecto).
"""

import pytest
from pydantic import ValidationError

from app.domain import RespuestaCruda


@pytest.mark.parametrize("califica", [-1, 5, 10])
def test_califica_fuera_de_rango_es_rechazada(califica):
    with pytest.raises(ValidationError):
        RespuestaCruda(factor_id=1, pregunta_idx=0, califica=califica)


@pytest.mark.parametrize("factor_id", [0, 8])
def test_factor_id_fuera_de_rango_es_rechazado(factor_id):
    with pytest.raises(ValidationError):
        RespuestaCruda(factor_id=factor_id, pregunta_idx=0, califica=2)
