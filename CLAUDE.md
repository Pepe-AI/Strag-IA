# CLAUDE.md

Generador automático de diagnósticos de **Score de Ventas & MKT Digital**. Un
consultor llena una plantilla bloqueada en Google Sheets durante una llamada con
su cliente, presiona un botón, y el sistema produce un PDF de diagnóstico de dos
páginas (scores + radar de 7 ejes en la pág. 1; plan de acción por debilidad en la
pág. 2) en Drive.

Contexto completo, decisiones y opciones rechazadas: ver `docs/BRIEF.md`.
Diseño estructural y plan de build: ver `docs/ARCHITECTURE.md` y `docs/PLAN.md`.

## Protocolo ante información faltante (leer antes de cualquier tarea)

- Si un dato necesario para proceder no está en este archivo, en `docs/BRIEF.md`
  o en los archivos reales del repo: **detente y pregunta. No fabriques** valores,
  coordenadas de celda, firmas de función/API, rutas ni configuración para avanzar.
- Los **TBD del BRIEF son bloqueos duros** (mapa de celdas del Sheet, diseño del
  PDF, prompt del analista). Al toparte con uno sin resolver, pregunta; no asumas.
- **Verifica el uso de librerías y APIs contra su documentación real** (usa el MCP
  context7); no recuerdes firmas ni comportamientos de memoria.
- Todo lo relativo al input se deriva del **archivo de ejemplo real** (el Excel de
  VASE), no del resumen del BRIEF ni de memoria.
- Mantén visibles los **supuestos y preguntas abiertas**. Un supuesto sin marcar
  es un bug, no un detalle.

## Stack

- **Python (FastAPI) en Render** — único lugar con lógica de negocio.
- **Gemini + pydantic** — una sola llamada de IA, salida validada por esquema.
- **Google Apps Script** — botón "Generar diagnóstico" en el Sheet (trigger).
- **HTML→PDF (WeasyPrint o Chromium headless) + matplotlib** — render del PDF.
- **Google Sheets/Drive API vía cuenta de servicio** — lectura del Sheet y subida del PDF.

## Reglas de dominio (NO violar — un error aquí produce diagnósticos incorrectos en silencio)

- **Alcance:** solo los **7 factores de ventas** (49 preguntas). El bloque de
  marketing del archivo fuente está fuera de alcance y se ignora.
- **CALIFICA es el único score:** cada pregunta se puntúa 0–4 con `CALIFICA`
  (Mal=0, Regular=1, Bien=2, Muy Bien=3, Excelente=4). `SI/NO` es informativo;
  **nunca** se usa para puntuar.
- **Score por factor** = media aritmética de las `CALIFICA` de sus preguntas.
- **PUNTAJE global** = media de las 7 medias de factor.
  **% de cumplimiento = PUNTAJE / 4 × 100.** Es el método "promedio de promedios"
  (hoja Evaluación), **no** suma-total/ideal.
- **Bandas** (deterministas, calculadas desde el %, nunca por la IA):
  `< 60% BAJO` · `60–79% MEDIO` · `≥ 80% ALTO`.
- **Siempre recalcular desde las celdas `CALIFICA` crudas.** Nunca confiar en
  valores cacheados de fórmulas del Sheet.

## Reglas de IA

- Exactamente **una** llamada a Gemini, temperatura baja, aterrizada
  estrictamente en `OBSERVACIONES` + scores. **Nunca inventar** cifras, datos ni
  causas que no estén en el input.
- La IA redacta **solo prosa** (hallazgos). Números, %, bandas y valores del
  radar son deterministas y nunca los decide la IA.
- Pre-filtrar: generar hallazgos sobre todo de los factores **bajos**. Un
  hallazgo nunca debe contradecir el radar (sin "debilidad" para un factor alto).
- **El diagnóstico muestra solo debilidades.** Las fortalezas se **evalúan** (entran
  al scoring y al radar de 7 ejes) pero **no** se redactan como hallazgo ni aparecen
  como sección de fortalezas en el PDF. La IA no genera prosa de fortalezas.
- Salida en **JSON validado con pydantic** antes de usarse. **Nunca renderizar
  salida de IA sin validar.** Si falla la validación: un reintento, luego
  fallback seguro.
- El diseño debe permitir insertar un **gate de aprobación humana** después sin
  rehacer el flujo (hoy corre full-auto).

## Flujo (resumen)

1. Apps Script (botón) → POST fire-and-ack al webhook con `sheetId` + secreto
   compartido en header. Devuelve 202 y muestra un toast. Python trabaja async.
2. Python: cuenta de servicio lee el Sheet → parsea celdas fijas →
   scoring determinista → Gemini (hallazgos) → render PDF → sube a Drive → notifica.

## Auth y seguridad

- Cuenta de Google **personal (no Workspace)** → no hay shared drives. Las
  carpetas de entrada y resultados se comparten con el **email de la cuenta de
  servicio**.
- **Validar el secreto compartido** (header) en el webhook; el endpoint está
  expuesto a internet.
- Secretos solo por variables de entorno en Render. Nunca commitear llaves.

## Convenciones de código

- Python con type hints. **pydantic para todo dato externo** (payload del Sheet,
  salida de la IA).
- Parseo y scoring deben ser deterministas y cubiertos por **tests unitarios**.
- Mantener la lógica fuera del trigger: Apps Script solo dispara, no parsea ni puntúa.

## Comandos (a finalizar al hacer el scaffolding)

```
# servir:   uvicorn app.main:app --reload
# tests:    pytest
# lint:     ruff check .
# formato:  ruff format .
```

## NO hacer (decisiones ya cerradas — ver BRIEF para el porqué)

- **No** reintroducir Kommo, WhatsApp, n8n, Redis ni LangGraph.
- **No** agregar base de datos relacional (Postgres): el flujo es stateless.
  Si se quiere histórico, un Sheet/log basta.
- **No** confiar en fórmulas cacheadas del Sheet; recalcular siempre.
- **No** dejar que la IA calcule scores/bandas ni que su salida llegue al PDF
  sin validación pydantic.
- **No** incluir el árbol de carpetas ni el plan paso a paso en este archivo.
