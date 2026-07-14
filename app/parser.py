"""Parser del Sheet (Fase 2).

Lee por NAMED RANGE según `cell_map` y produce `SheetNormalizado`. La parte que
habla con la Sheets API vive aparte (adapter); aquí solo se interpreta la forma
cruda {named_range: filas}, para poder probar sin red.

Cualquier desviación del contrato (versión, completitud, valores) levanta un
error de dominio: NUNCA un score parcial silencioso (ARCHITECTURE §8.3).
"""

from pydantic import ValidationError

from app.cell_map import (
    FACTORES,
    RANGE_EMPRESA,
    RANGE_VERSION,
    TEMPLATE_VERSION,
)
from app.domain import FactorCrudo, RespuestaCruda, SheetNormalizado

Raw = dict[str, list[list]]


class ContratoPlantillaError(Exception):
    """El Sheet no cumple el contrato del parser."""


class PlantillaVersionError(ContratoPlantillaError):
    """`template_version` no es una versión conocida."""


class PlantillaIncompletaError(ContratoPlantillaError):
    """Falta un named range, o un valor está ausente / fuera de rango."""


def _scalar(raw: Raw, name: str) -> str:
    if name not in raw:
        raise PlantillaIncompletaError(f"falta el named range '{name}'")
    filas = raw[name]
    if not filas or not filas[0] or str(filas[0][0]).strip() == "":
        raise PlantillaIncompletaError(f"'{name}' vacío")
    return str(filas[0][0]).strip()


def _columna(raw: Raw, name: str) -> list:
    if name not in raw:
        raise PlantillaIncompletaError(f"falta el named range '{name}'")
    return [fila[0] if fila else None for fila in raw[name]]


def parse_sheet(raw: Raw) -> SheetNormalizado:
    version = _scalar(raw, RANGE_VERSION)
    if version != TEMPLATE_VERSION:
        raise PlantillaVersionError(
            f"versión '{version}' desconocida (esperada '{TEMPLATE_VERSION}')"
        )

    empresa = _scalar(raw, RANGE_EMPRESA)

    factores = []
    for f in FACTORES:
        califs = _columna(raw, f["rango_calif"])
        if len(califs) != f["n_preguntas"]:
            raise PlantillaIncompletaError(
                f"factor {f['id']}: se esperaban {f['n_preguntas']} CALIFICA, "
                f"llegaron {len(califs)}"
            )

        obs = _columna(raw, f["rango_obs"])
        respuestas = []
        for i, c in enumerate(califs):
            if c is None or (isinstance(c, str) and c.strip() == ""):
                raise PlantillaIncompletaError(
                    f"factor {f['id']} pregunta {i}: CALIFICA vacía"
                )
            try:
                respuestas.append(
                    RespuestaCruda(factor_id=f["id"], pregunta_idx=i, califica=c)
                )
            except ValidationError as e:
                raise PlantillaIncompletaError(
                    f"factor {f['id']} pregunta {i}: CALIFICA inválida ({c!r})"
                ) from e

        # Separador entre notas: sin él se pegan y la IA no distingue una de otra.
        observaciones = " | ".join(
            str(o).strip() for o in obs if o is not None and str(o).strip()
        )
        factores.append(
            FactorCrudo(
                factor_id=f["id"],
                nombre=f["nombre"],
                respuestas=respuestas,
                observaciones=observaciones,
            )
        )

    return SheetNormalizado(
        template_version=version, empresa=empresa, factores=factores
    )
