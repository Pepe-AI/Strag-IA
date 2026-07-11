"""Fixtures de test.

- `sheet_vase()`: caso de MATEMÁTICA conocido (datos reales de VASE, estructura
  histórica de 49). Auto-contenido: NO depende de `cell_map`, así el golden del
  scoring no se mueve cuando cambia el contrato de producción.
- `raw_completo()`: forma cruda estilo `batchGet` válida y COMPLETA, derivada del
  `cell_map` vigente (sea v1, v2…). Para los tests del parser/adapter.
"""

from app.cell_map import FACTORES, TEMPLATE_VERSION
from app.domain import FactorCrudo, RespuestaCruda, SheetNormalizado

# --- Golden de matemática (VASE, estructura histórica 49) ---

VASE_CALIFICA: dict[int, list[int]] = {
    1: [4, 2, 4, 2, 4, 4, 2],
    2: [0, 4, 0, 3, 4, 0, 4, 2, 2],
    3: [0, 0, 2, 2, 4],
    4: [4, 4, 0, 0, 2, 2, 0, 4],
    5: [2, 0, 4, 0],
    6: [4, 4, 4, 4, 4, 0, 4, 0, 2, 2, 2, 0],
    7: [4, 4, 3, 4],
}

_VASE_NOMBRES = {
    1: "Planeación y estrategia comercial",
    2: "Equipo de ventas",
    3: "Formación de ventas",
    4: "Desempeño de ventas",
    5: "Postventa / cuentas clave",
    6: "Marketing digital",
    7: "Mercado y competencia",
}


def sheet_vase() -> SheetNormalizado:
    """`SheetNormalizado` de VASE (entrada directa del scoring). Auto-contenido."""
    factores = [
        FactorCrudo(
            factor_id=fid,
            nombre=_VASE_NOMBRES[fid],
            respuestas=[
                RespuestaCruda(factor_id=fid, pregunta_idx=i, califica=c)
                for i, c in enumerate(califs)
            ],
        )
        for fid, califs in VASE_CALIFICA.items()
    ]
    return SheetNormalizado(
        template_version="v1", empresa="VASE Sísmica", factores=factores
    )


# --- Fixture de parser: completo y válido según el cell_map vigente ---

def raw_completo(empresa: str = "Empresa Demo") -> dict[str, list[list]]:
    """Forma cruda `batchGet` válida y completa, generada del `cell_map` actual.

    Usa CALIFICA=2 en todas las preguntas (valor válido cualquiera); el objetivo es
    ejercitar el parser, no un score concreto.
    """
    raw: dict[str, list[list]] = {
        "empresa": [[empresa]],
        "template_version": [[TEMPLATE_VERSION]],
    }
    for f in FACTORES:
        raw[f["rango_calif"]] = [[2] for _ in range(f["n_preguntas"])]
        raw[f["rango_obs"]] = [[""] for _ in range(f["n_preguntas"])]
    return raw
