# BRIEF — Generador automático de diagnósticos de Ventas & MKT Digital

Documento de contexto del proyecto. Se lee una vez al iniciar el diseño y se
consulta como referencia. Recoge el problema, las decisiones tomadas (con su
razón), lo que se rechazó y lo que queda pendiente. **Las decisiones aquí no se
re-litigan**; si algo debe cambiar, se actualiza este documento explícitamente.

---

## 1. Objetivo

Automatizar la generación del diagnóstico de "Score de Ventas & MKT Digital"
para **ahorrarle tiempo al consultor**. Hoy el consultor llena un Excel a mano y
arma el PDF de diagnóstico manualmente; queremos que el PDF se genere solo a
partir del archivo llenado.

## 2. Situación actual y proceso humano

- El consultor (cliente del proyecto) entrevista a **su** cliente en una llamada
  y va llenando un cuestionario de evaluación de ventas y marketing.
- Al terminar la llamada queda un archivo con las respuestas.
- El llenado **sigue siendo manual** — no automatizamos la captura. Lo que se
  automatiza es la **generación del diagnóstico** a partir del archivo terminado.

## 3. Especificación de dominio (el scoring)

El diagnóstico se construye sobre **7 factores de ventas**, evaluados con 52
preguntas en total (cuestionario canónico **v2**, confirmado por el cliente; ver
`app/cell_map.py`):

| # | Factor | Preguntas |
|---|--------|-----------|
| 1 | Planeación y estrategia comercial | 7 |
| 2 | Equipo de ventas | 9 |
| 3 | Gestión y medición comercial | 7 |
| 4 | Prospección y Pipeline | 6 |
| 5 | Fidelización y Crecimiento de Clientes | 6 |
| 6 | Marketing digital | 12 |
| 7 | Mercado y competencia | 5 |

> El cuestionario anterior (49 preguntas: Formación / Desempeño / Postventa) quedó
> **reemplazado**. El caso de **VASE (49)** se conserva solo como **golden de
> matemática** del motor de scoring (estructura histórica), no como contrato.

Reglas de cálculo (la fórmula no cambia entre versiones):

- Cada pregunta se puntúa **0–4** con la columna `CALIFICA`, según la escala
  *Pondera*: Mal=0, Regular=1, Bien=2, Muy Bien=3, Excelente=4.
- La columna `SI/NO` es **solo informativa**; no entra al cálculo. (Confirmado:
  hay preguntas con `SI/NO = N/A` y `CALIFICA = 4`.)
- **Score por factor** = media aritmética de las `CALIFICA` de sus preguntas.
- **PUNTAJE global** = media de las 7 medias de factor.
- **% de cumplimiento** = `PUNTAJE / 4 × 100`. Este es el método "promedio de
  promedios" de la hoja **Evaluación** — el oficial. (En el archivo de ejemplo
  da 2.37 / 4 = **59.3 %**.) Existe en el archivo un segundo cálculo
  suma-total/ideal (116/196 = 59.18 %) que **no se usa**.
- **Bandas:** `< 60 % BAJO` · `60–79 % MEDIO` · `≥ 80 % ALTO`. La banda se
  calcula desde el %, nunca por la IA.
- El **radar de 7 ejes** grafica las 7 medias de factor (escala 0–4) contra el
  máximo (4).
- **El parser recalcula desde las `CALIFICA` crudas**, no confía en fórmulas
  cacheadas (al leer el Sheet por API no se recalculan, y un valor cacheado puede
  estar viejo).

El **entregable** es un PDF de dos páginas que preserva las dos secciones de
resultados del ejemplo: (a) los **hallazgos** narrativos y (b) el **radar**.

## 4. Flujo end-to-end

1. El consultor llena la **plantilla bloqueada en Google Sheets** durante la
   llamada (solo puede escribir en las celdas de respuesta; dropdowns para
   `CALIFICA` 0–4 y `SI/NO`).
2. Al terminar, presiona el botón **"Generar diagnóstico"** (Apps Script atado
   al Sheet).
3. Apps Script hace un **POST fire-and-ack** al webhook del servicio Python con
   `{ sheetId, nombre }` + un **secreto compartido** en header; recibe `202` y
   muestra un toast ("en proceso"). No espera a que termine la generación.
4. El servicio **Python (FastAPI en Render)** trabaja async:
   lee el Sheet con una **cuenta de servicio** → parsea las 52 `CALIFICA` +
   `OBSERVACIONES` desde celdas fijas → **scoring determinista** → **una llamada
   a Gemini** para los hallazgos (aterrizados en `OBSERVACIONES` + scores,
   salida JSON validada con pydantic, baja temperatura, un reintento, pre-filtro
   por factores bajos) → **render del PDF de dos páginas** (radar como PNG de
   matplotlib embebido en un layout HTML→PDF) → **sube el PDF** a la carpeta de
   resultados en Drive → **notifica**.

## 5. Stack tecnológico (decidido)

- **Python (FastAPI) en Render** — toda la lógica.
- **Gemini + pydantic** — un solo paso generativo, validado.
- **Google Apps Script** — trigger (botón en el Sheet).
- **HTML→PDF (WeasyPrint o Chromium headless) + matplotlib** — render.
- **Google Sheets/Drive API vía cuenta de servicio** — datos e IO.
- **Idempotencia:** mover el Sheet/registro procesado a una carpeta
  `/procesados` (sin base de datos).
- **Alertas de error** por email si un diagnóstico falla.

## 6. Opciones rechazadas (y por qué) — NO reintroducir

- **Kommo + WhatsApp:** este proyecto es batch y basado en archivos, no
  conversacional. No hay lead, conversación, CRM ni mensajería. Incluirlos
  re-importa toda la complejidad (PATCH a custom fields, Salesbot, race
  conditions) de la que el proyecto justamente se aleja.
- **n8n:** su único rol sería una cáscara delgada de trigger + IO. El botón de
  Apps Script es más confiable (event-driven, sin polling), resuelve sin
  ambigüedad cuándo el archivo está terminado, y elimina una pieza hospedada. La
  lógica vive en Python de todos modos.
- **PostgreSQL / Redis:** el flujo es stateless, síncrono y de bajo volumen. No
  hay sesión ni estado que persistir. Una base relacional sin un esquema que la
  pida es sobre-ingeniería. Si se quiere histórico, un Sheet/log basta.
- **LangGraph:** es para flujos agénticos, con estado y cíclicos. Esto es un
  pipeline lineal con **una** llamada al LLM; LangGraph agrega dependencia y
  boilerplate por cero beneficio, y ni siquiera resuelve el trigger/IO.

## 7. Restricciones

- **Cuenta de Google personal (NO Workspace):** no existen shared drives. El
  acceso se da compartiendo las carpetas de entrada y resultados con el **email
  de la cuenta de servicio**. Límite de ejecución de Apps Script ~6 min
  (irrelevante con el patrón fire-and-ack).
- **Volumen bajo y síncrono:** el consultor llena el Sheet en vivo con su cliente,
  así que no puede haber dos diagnósticos en proceso simultáneo. No se necesita
  manejo de concurrencia ni colas.
- **IA full-auto por ahora.** El diseño debe permitir insertar un **gate de
  aprobación humana** después (sin rehacer el flujo) si aparecen alucinaciones o
  salidas no deseadas.

## 8. Artefactos de referencia

- `Sales___digital_Score_-_Vase_sismica_2026.xlsx` — ejemplo de **INPUT**
  (empresa: VASE Sísmica). Layout manual y frágil; su bloque de marketing está
  roto (`#REF!`) y fuera de alcance. **Sirve solo para derivar la lógica de
  scoring**, no como plantilla final.
- `Propuesta_de_consultoría_de_ventas_-_Entec_2026_v2.pdf` — ejemplo de
  **FORMATO de salida** (empresa: ENTEC). Es un deck de 6 láminas, pero el
  entregable v1 es un **PDF de dos páginas** que preserva las secciones de
  resultados (hallazgos + radar).
- **VASE y ENTEC son empresas distintas.** Los dos archivos son referencias de
  lógica y de formato respectivamente; **no cruzar sus números.**

## 9. Pendientes (TBD)

- **Plantilla canónica del Sheet + mapa de celdas exacto** (qué celda tiene cada
  `CALIFICA`, los 7 bloques, named ranges). Es el contrato del parser. **Se
  produce como paso 1 del build**, no se espera de un tercero.
- **Diseño del PDF** — lo entrega el equipo de diseño. Construir el render con un
  layout placeholder y enchufar el diseño final cuando llegue.
- **Prompt del analista de ventas para la IA** — lo entrega el cliente final. Se
  parte en **capa-persona** (criterio/tono del cliente) + **capa-grounding /
  schema / guardrails** (nuestra). Construir con un prompt base mientras tanto.
- **Esquema exacto de salida de la IA** (cantidad de hallazgos, orden, severidad) y
  detalle de entrega/notificación. Se fija en `docs/ARCHITECTURE.md`.
  **Decidido:** el diagnóstico resalta **solo debilidades**; las fortalezas se
  evalúan (radar y scoring) pero **no se muestran** como sección textual.

## 10. Fuera de alcance (v1)

- El bloque de scoring de marketing (29 preguntas) y el `SCORE GENERAL` combinado
  sobre 312.
- Cualquier integración conversacional / WhatsApp / CRM.
- Multi-tenant, alta concurrencia o alto volumen.

## 11. Definición de "hecho" (v1)

El consultor llena el Sheet bloqueado, presiona el botón, y en poco tiempo
aparece en la carpeta de resultados de Drive un **PDF de dos páginas correcto**
(scores y radar bien calculados, banda correcta, hallazgos aterrizados en las
observaciones), con una **alerta de error** si algo falla en el proceso.
