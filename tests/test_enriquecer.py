"""Enriquecido: prosa de la IA + metadatos inyectados por Python (Fase 3).

Solo debilidades. La severidad sale de la banda del factor; la media y el nombre,
del scoring. La IA no aporta ningún número.
"""

from app.domain import HallazgoIA, SalidaIA
from app.hallazgos import enriquecer
from app.scoring import calcular_scoring
from vase import sheet_vase


def test_enriquecer_inyecta_severidad_y_metadatos():
    res = calcular_scoring(sheet_vase())
    salida = SalidaIA(
        debilidades=[
            HallazgoIA(factor_id=5, texto="Postventa sin proceso."),  # media 1.5 BAJO
            HallazgoIA(factor_id=6, texto="Marketing irregular."),  # media 2.5 MEDIO
        ]
    )

    deb = enriquecer(salida, res)

    assert deb[0].factor_id == 5
    assert deb[0].factor_nombre == "Postventa / cuentas clave"
    assert deb[0].media == 1.5
    assert deb[0].severidad == "alta"  # BAJO

    assert deb[1].factor_id == 6
    assert deb[1].severidad == "media"  # MEDIO
