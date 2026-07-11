"""
Mapa de celdas — contrato del parser para la plantilla v2.

v2: cuestionario de 52 preguntas (reemplaza al de 49). Cambian los factores 3, 4, 5
y el conteo del 7; las columnas y la escala CALIFICA 0..4 se mantienen.

Generado por `crear_plantilla.gs`. El parser lee SIEMPRE por NAMED RANGE
(no por coordenadas A1): si la plantilla mueve filas, el named range sigue a la
celda y el parser no se rompe. Lectura recomendada vía Sheets API
`spreadsheets.values.batchGet(ranges=[...nombres...])`.

Desbloquea el TBD de la Fase 2 (PLAN.md). Si la plantilla cambia de layout, se
sube TEMPLATE_VERSION aquí y en el Sheet, y el parser rechaza versiones que no
conozca.
"""

TEMPLATE_VERSION = "v2"

# Named ranges escalares
RANGE_EMPRESA = "empresa"
RANGE_VERSION = "template_version"

# Estos existen en el Sheet (cálculo en vivo) pero el parser NO los usa:
# el scoring se RECALCULA desde calif_f* crudas (ARCHITECTURE §7), porque la
# API puede devolver valores de fórmula cacheados/viejos.
RANGE_PUNTAJE = "puntaje"
RANGE_PORCENTAJE = "porcentaje"
RANGE_BANDA = "banda"

# Un named range de CALIFICA y uno de OBSERVACIONES por factor.
# Las OBSERVACIONES son por pregunta; el parser concatena las de cada factor
# para producir FactorCrudo.observaciones (grounding de la IA, ARCHITECTURE §3.2).
FACTORES = [
    {"id": 1, "nombre": "Planeación y estrategia comercial", "n_preguntas": 7,
     "rango_calif": "calif_f1", "rango_obs": "obs_f1"},
    {"id": 2, "nombre": "Equipo de ventas", "n_preguntas": 9,
     "rango_calif": "calif_f2", "rango_obs": "obs_f2"},
    {"id": 3, "nombre": "Gestión y medición comercial", "n_preguntas": 7,
     "rango_calif": "calif_f3", "rango_obs": "obs_f3"},
    {"id": 4, "nombre": "Prospección y Pipeline", "n_preguntas": 6,
     "rango_calif": "calif_f4", "rango_obs": "obs_f4"},
    {"id": 5, "nombre": "Fidelización y Crecimiento de Clientes", "n_preguntas": 6,
     "rango_calif": "calif_f5", "rango_obs": "obs_f5"},
    {"id": 6, "nombre": "Marketing digital", "n_preguntas": 12,
     "rango_calif": "calif_f6", "rango_obs": "obs_f6"},
    {"id": 7, "nombre": "Mercado y competencia", "n_preguntas": 5,
     "rango_calif": "calif_f7", "rango_obs": "obs_f7"},
]

TOTAL_PREGUNTAS = 52  # 7 + 9 + 7 + 6 + 6 + 12 + 5

# Reglas de completitud que el parser debe exigir (ARCHITECTURE §6, §8.3):
#  - RANGE_VERSION debe ser == TEMPLATE_VERSION (si no: error de versión).
#  - cada rango_calif trae exactamente n_preguntas valores enteros 0..4.
#  - RANGE_EMPRESA no vacío.
#  - cualquier celda CALIFICA vacía o fuera de 0..4 -> fallo de completitud,
#    NUNCA un score parcial silencioso.
