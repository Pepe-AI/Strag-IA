"""Adapter de lectura de Google Sheets (Fase 2).

Única pieza que habla con la Sheets API. Recibe el `service` por inyección
(googleapiclient discovery) para poder probar la lógica sin red. Pide los named
ranges del contrato con `batchGet` y devuelve la forma cruda {named_range: filas}
que consume el parser.

El `service` real se construye al cablear (Fase 8):
    build("sheets", "v4", credentials=...)   # scope spreadsheets.readonly
"""

from app.cell_map import FACTORES, RANGE_EMPRESA, RANGE_VERSION

Raw = dict[str, list[list]]


def ranges_a_leer() -> list[str]:
    """Named ranges que el parser necesita. NO incluye puntaje/%/banda
    (cálculos en vivo): el scoring se recalcula desde crudo."""
    nombres = [RANGE_VERSION, RANGE_EMPRESA]
    for f in FACTORES:
        nombres.append(f["rango_calif"])
        nombres.append(f["rango_obs"])
    return nombres


def leer_raw(service, spreadsheet_id: str) -> Raw:
    nombres = ranges_a_leer()
    resp = (
        service.spreadsheets()
        .values()
        .batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=nombres,
            valueRenderOption="UNFORMATTED_VALUE",
        )
        .execute()
    )
    # valueRanges vuelve en el MISMO orden que `nombres` (verificado, Sheets API v4).
    value_ranges = resp.get("valueRanges", [])
    return {
        nombre: vr.get("values", []) for nombre, vr in zip(nombres, value_ranges)
    }
