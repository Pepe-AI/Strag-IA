# PLAN — Secuencia de construcción

La **arquitectura** (componentes, contratos, decisiones) está en
[`docs/ARCHITECTURE.md`](./ARCHITECTURE.md); el contexto y el dominio en
[`docs/BRIEF.md`](./BRIEF.md) y [`CLAUDE.md`](../CLAUDE.md). Este documento es solo
la **secuencia de build**: pasos ordenados, incrementales y cada uno verificable por
sí solo. No repite la arquitectura ni contiene código.

**Filosofía: inside-out / test-first.** Empezamos por el núcleo puro y determinista
(el scoring), que se verifica de inmediato contra un resultado conocido, y crecemos
hacia afuera capa por capa. Cada paso "cierra" con su prueba (las de la §8 de la
arquitectura). Así, si algo se rompe más adelante, sabemos que el núcleo ya estaba
probado.

> **Cómo leer cada paso.** Cada uno trae: **Objetivo · Qué se construye · Conceptos
> clave · Dependencias · Criterio de aceptación · TBD/bloqueos**. Los "Conceptos
> clave" explican el *por qué* y el *cómo* en lenguaje sencillo — el plan también es
> material de aprendizaje.

---

## Acuerdo de trabajo para las sesiones de build

Léelo antes de ejecutar cualquier paso. Aplica a todas las sesiones:

- **Enseñar mientras se programa.** Antes de escribir una pieza, explicar en español
  sencillo qué va a hacer y por qué; después de escribirla, repasar qué quedó.
- **Trozos pequeños y revisables.** Nunca volcar un bloque gigante de código de una
  sola vez. Avanzar en incrementos que se puedan leer y entender.
- **Pausar para seguir el hilo.** Esperar el visto bueno **paso por paso**; no
  encadenar varios pasos sin revisión.
- **Cada paso llega con su test.** No se considera terminado un paso sin su criterio
  de aceptación corriendo en verde.
- **No inventar.** Ante un TBD o una firma de librería desconocida: detenerse y
  preguntar, o verificar con context7 (ver Protocolo en `CLAUDE.md`). No fabricar
  coordenadas, APIs ni configuración.

---

## Hallazgos previos que condicionan el plan

Verificado con **context7** (Google Workspace Drive), porque define scopes y la
idempotencia (afecta Fases 5 y 6):

- `drive.file` **solo** cubre archivos creados por la app o compartidos vía **Google
  Picker / file picker** — **no** archivos compartidos al email de la cuenta de
  servicio. Por eso la cuenta de servicio **no puede mover ni leer los `parents`** del
  Sheet del consultor con `drive.file`.
- Mover el Sheet a `/procesados` exigiría el scope **`drive` completo** → viola
  mínimo privilegio. **Decisión: no se mueve ni se muta el Sheet** (ver Fase 6).
- El allowlist por carpeta padre (`files.get(...parents)`) necesita
  **`drive.metadata.readonly`** (solo lectura), no `drive.file`.
- Leer el contenido del Sheet va por **Sheets API** (`spreadsheets.readonly`), que sí
  respeta el compartido por email — es independiente de los scopes de Drive.

**Scopes finales de la cuenta de servicio:** `spreadsheets.readonly` +
`drive.metadata.readonly` + `drive.file`. Sin escritura al Sheet, sin `drive` completo.

---

## Fase 1 — Núcleo determinista (motor de scoring)

**Objetivo.** Dado un conjunto de calificaciones crudas (las `CALIFICA` de los 7
factores; 52 en la plantilla v2), calcular medias por factor, PUNTAJE, % y banda
**exactamente**, sin tocar red ni IA.

**Qué se construye.**
- Los modelos de dominio en pydantic (`RespuestaCruda`, `FactorScore`,
  `ResultadoScoring`, el tipo `Banda`), tal como los define `ARCHITECTURE.md §3.2`.
- El motor de scoring como **funciones puras** (`§7` de la arquitectura): media por
  factor → media de las 7 medias → `% = PUNTAJE/4×100` → banda.

**Conceptos clave (en sencillo).**
- **Función pura:** una función que, con las mismas entradas, siempre devuelve la
  misma salida y no toca nada externo (ni red, ni archivos, ni reloj). El scoring lo
  es a propósito: lo hace trivial de probar y elimina la posibilidad de resultados
  que cambian "por arte de magia". Es la razón de empezar por aquí.
- **pydantic:** una librería que valida datos contra un *esquema* (los tipos y reglas
  que declaramos). Si llega un `CALIFICA` que no es 0–4, falla en la frontera en vez
  de envenenar el cálculo silenciosamente.
- **Promedio de promedios:** el PUNTAJE no es "suma total / ideal"; es la media de
  las 7 medias de factor. Es la regla de dominio que no se puede violar.

**Dependencias.** Ninguna (es el cimiento).

**Criterio de aceptación.** Un test **golden-file** con el caso base de **VASE**
(estructura histórica de 49, conservado como golden de matemática): las `CALIFICA`
crudas conocidas → `PUNTAJE 2.37 / 4`, `59.3 %`, banda `BAJO`, y las 7 medias
esperadas. Se escribe **el test primero** (test-first) y luego la implementación
hasta que pasa.

**TBD/bloqueos.** Ninguno: el scoring se deriva del archivo de VASE, ya conocido.

---

## Fase 2 — Parser del Sheet (contra el mapa de celdas)

**Objetivo.** Convertir un Sheet leído en el modelo normalizado (`SheetNormalizado`)
de forma fiable, recalculando siempre desde crudo y fallando claro si el Sheet está
mal.

**Qué se construye.**
- El **mapa de celdas versionado** como fuente de verdad (`ARCHITECTURE.md §6`):
  named ranges / coordenadas por `CALIFICA` y `OBSERVACIONES`, celda
  `template_version`, chequeo de completitud. Se construye con un **placeholder**
  (el mapa real es un TBD duro) y un fixture sintético.
- El **parser** puro: del Sheet crudo → `SheetNormalizado`, validando versión y
  completitud.
- Un **adapter de lectura** de Sheets aislado (la pieza que sí habla con la API),
  separado de la lógica del parser para poder probar el parser sin red.

**Conceptos clave (en sencillo).**
- **Contrato / fuente de verdad:** el mapa de celdas es el *único* lugar donde vive
  "qué celda es qué". El parser nunca lleva coordenadas sueltas; si la plantilla
  cambia, se toca un solo archivo. Eso evita bugs silenciosos por celdas movidas.
- **Adapter aislado:** separar "hablar con Google" de "interpretar los datos" permite
  probar la interpretación con datos de mentira (fixtures) sin llamadas reales —
  rápido, gratis y determinista.
- **Recalcular desde crudo:** la API puede devolver valores de fórmula **cacheados y
  viejos**; por eso el parser toma las `CALIFICA` crudas y el scoring las recalcula.

**Dependencias.** Fase 1 (produce la entrada del scoring).

**Criterio de aceptación.** Tests de **contrato** con fixtures (sin red): celda
faltante → fallo de completitud; `template_version` desconocida → error de versión;
Sheet incompleto → fallo de validación explícito. Ningún caso degenerado produce un
score parcial silencioso.

**TBD/bloqueos.** **[TBD duro]** coordenadas reales del mapa de celdas: se derivan del
archivo de VASE como parte del build; hasta entonces, placeholder + fixture sintético,
marcado para enchufar.

---

## Fase 3 — Módulo de IA / hallazgos (Gemini mockeado)

**Objetivo.** Producir los hallazgos en prosa, validados y aterrizados, sin que la IA
toque jamás un número, con manejo de fallo (un reintento → fallback).

El diagnóstico resalta **solo debilidades**; las fortalezas se evalúan (radar y
scoring) pero no se redactan.

**Qué se construye.**
- La **pre-selección determinista** de los **factores débiles** (banda baja/media),
  como función pura sobre los scores.
- El esquema `SalidaIA` (pydantic, solo `debilidades`) + **reglas de negocio**: cada
  `factor_id` debe estar en los preseleccionados, ninguna "debilidad" sobre un factor
  de banda alta, **cobertura completa** (todas las debilidades, una por factor débil).
  Luego el enriquecido `HallazgoRenderable`
  (se inyectan media y severidad, derivadas, no las da la IA). Ver `ARCHITECTURE.md §3.3`.
- El **cliente de Gemini** (una sola llamada, baja temperatura) detrás de una interfaz
  pequeña, para poder sustituirlo en tests.

**Conceptos clave (en sencillo).**
- **Por qué mockear el LLM en los tests:** un "mock" es un doble de mentira que
  devuelve lo que nosotros digamos. Probamos **nuestra** lógica (validación, reglas,
  reintento, fallback), no el modelo; así los tests son deterministas, sin costo y sin
  red. El modelo real se prueba aparte, manualmente.
- **La IA solo escribe prosa:** recibe factores ya elegidos con su media/banda y las
  `OBSERVACIONES`; no puede inventar un factor ni contradecir el radar. Severidad y
  números se inyectan en Python *después* de validar.
- **Fallback seguro:** si la salida no valida ni tras un reintento, no se renderiza
  basura; la corrida se marca `failed` y se notifica.

**Dependencias.** Fase 1 (scores que alimentan la pre-selección y el grounding).

**Criterio de aceptación.** Con Gemini **mockeado**: salida válida → hallazgos
enriquecidos correctos; salida malformada → reintento → fallback; salida que viola una
regla (p. ej. debilidad en factor alto) → rechazada. Nunca se usa salida sin validar.

**TBD/bloqueos.** **[TBD duro]** prompt del analista (capa-persona, la entrega el
cliente). Se construye con un prompt base + nuestra capa de grounding/guardrails
(`§3.3.1`); la capa-persona se enchufa después sin tocar el resto.

---

## Fase 4 — Renderer del PDF (diseño Stragia, 2 páginas)

**Objetivo.** Dado un `ReportePDF` ya calculado y validado, producir el PDF de **dos
páginas** del diseño Stragia (pág. 1: resultado global + radar + desglose de los 7;
pág. 2: plan de acción — solo factores débiles con su hallazgo).

**Qué se construye.**
- `mensaje_banda` determinista (frase fija por banda; no la IA).
- El **radar** como PNG con matplotlib (7 ejes, escala 0–4 contra el máximo 4).
- `construir_html(reporte) -> str` (**puro, testeable**) con el layout Stragia (logo
  embebido como data URI, anillo %, barras de desglose, tarjetas de pág. 2).
- `render_pdf(reporte) -> bytes`: HTML + radar → **WeasyPrint**.

**Conceptos clave (en sencillo).**
- **Render determinista:** el renderer no decide nada (ni scores ni qué hallazgos);
  solo pinta lo que recibe. Misma entrada → mismo PDF.
- **HTML separado del PDF:** "construir HTML" es una función pura que se prueba sin
  WeasyPrint (asserts de contenido); "HTML→PDF" se aísla para el caveat de libs
  nativas en Windows.

**Dependencias.** Fases 1 y 3 (proveen scores y hallazgos del `ReportePDF`).

**Criterio de aceptación.** (1) `construir_html` incluye empresa, %, banda,
`mensaje_banda`, los 7 factores del desglose y el texto de cada debilidad. (2) Smoke:
`render_pdf` produce un PDF **válido de 2 páginas**. El detalle visual se valida a ojo
contra el diseño entregado.

**TBD/bloqueos.** Textos de `mensaje_banda` para **MEDIO** y **ALTO** (solo tengo el de
BAJO, del diseño) → placeholder hasta recibirlos. Hex/tipografías exactos de marca →
aproximo del asset. **Verificar con context7** las firmas de WeasyPrint y matplotlib.

---

## Fase 5 — Webhook + seguridad

**Objetivo.** Exponer el endpoint fire-and-ack: validar, responder `202` rápido y
lanzar el pipeline en background.

**Qué se construye.**
- La app FastAPI con el `POST`, los modelos `WebhookPayload` / `WebhookAck`, la
  validación del **secreto compartido** (env var), **rate-limit** básico y las
  respuestas `202/400/401/403/429` (`ARCHITECTURE.md §3.1`).
- El **allowlist de `sheetId`** por carpeta padre en Drive
  (`files.get(...parents)` con `drive.metadata.readonly`): un secreto filtrado no
  procesa Sheets arbitrarios.
- El pipeline corriendo en **`BackgroundTasks`** tras el `202`.

**Conceptos clave (en sencillo).**
- **Fire-and-ack:** el webhook contesta "recibido" (`202`) de inmediato y hace el
  trabajo pesado después; así Apps Script no espera (y su límite de ~6 min es
  irrelevante).
- **Qué es un background task y su límite:** es trabajo que sigue corriendo tras
  responder, **en el mismo proceso**. Ventaja: simple, sin cola. Límite: **no
  sobrevive a un reinicio** (deploy o crash) — ahí muere el job en vuelo.
- **Allowlist ≠ secreto:** el secreto dice "quién llama"; el allowlist dice "qué Sheet
  puede procesar". Son dos defensas distintas (defensa en profundidad).

**Decisión async (resuelta aquí).** `BackgroundTasks` **confirmado**: el servicio es
de pago, **sin spin-down** por inactividad, así que ese riesgo no aplica. Riesgo
residual: un **deploy/crash** mata un job en vuelo y no hay durabilidad ni reintento
automático. Mitigaciones, no rediseño:
- **Recuperación = re-clic** del botón. Es seguro porque el Sheet **no se muta** (Fase 6),
  así que reintentar no corrompe nada.
- **Detección "started sin terminal"** (`ARCHITECTURE.md §9`): un `runId` con evento
  `started` pero sin `success`/`failed` señala el job muerto.
- **Sync-y-espera** queda solo como posible mejora de **UX** (feedback inmediato si el
  Sheet está incompleto), no como mecanismo de robustez.

**Dependencias.** Fases 1–4 (el background task las invoca en orden).

**Criterio de aceptación.** Tests del endpoint con Drive **mockeado**: secreto malo →
`401`; payload malo → `400`; `sheetId` fuera de la carpeta → `403`; exceso de
requests → `429`; válido → `202` + `runId`.

**TBD/bloqueos.** Mecanismo/umbral exactos del rate-limit (supuesto: límite global
bajo). Verificar firmas de FastAPI / google-api-python-client con context7.

---

## Fase 6 — IO de Drive + idempotencia + notificaciones

**Objetivo.** Entregar el PDF en Drive, ser idempotente sin estado y dejar rastro de
cada corrida.

**Qué se construye.**
- **Subida del PDF** a la carpeta de resultados, que es **propiedad de la cuenta de
  servicio** (al ser app-owned, `drive.file` la cubre sin scope extra; la carpeta se
  comparte de vuelta con el consultor para que vea resultados).
- **Idempotencia sin mutar el Sheet** (decidido, ver hallazgos): el PDF se nombra de
  forma **determinista `<empresa>_<fecha>.pdf`**, de modo que un re-clic **sobrescribe**
  el mismo archivo en vez de duplicarlo. No se mueve ni se marca el Sheet del consultor.
- **Notificaciones:** un **evento de log estructurado por corrida**
  (`started` / `success` con la URL del PDF / `failed` con el error) + **email solo en
  fallo** (`ARCHITECTURE.md §9`).

**Conceptos clave (en sencillo).**
- **Idempotencia sin estado:** "hacerlo dos veces da el mismo resultado". Sin base de
  datos, lo logramos con el **nombre determinista**: la segunda corrida pisa el PDF de
  la primera. No hace falta recordar nada entre corridas.
- **Por qué la SA es dueña de la carpeta:** porque `drive.file` solo deja a la app
  tocar lo que ella creó. Si la carpeta de resultados es de la SA, escribir ahí entra
  en `drive.file` y evitamos pedir el scope `drive` completo.
- **Por qué NO movemos el Sheet:** moverlo necesitaría acceso total a Drive (`drive`),
  un riesgo desproporcionado para un proyecto de bajo volumen. La idempotencia por
  nombre del PDF cubre el caso sin ese poder.

**Dependencias.** Fase 4 (produce el PDF) y Fase 5 (orquesta el background task).

**Criterio de aceptación.** Con Drive **mockeado**: el upload usa el nombre
determinista y sobrescribe en re-run; se emiten los eventos de log esperados; en fallo
se dispara el email. Verificación del scope real (carpeta propiedad de la SA) en el
smoke de la Fase 8.

**TBD/bloqueos.** Confirmar en build que la carpeta de resultados es efectivamente de
la SA. Verificar firmas de google-api-python-client (Drive `files.create`/`update`) con
context7.

---

## Fase 7 — Apps Script (trigger)

**Objetivo.** El botón en el Sheet dispara el webhook y le da feedback inmediato al
consultor, sin hacer nada de lógica.

**Qué se construye.**
- El script atado al Sheet: botón **"Generar diagnóstico"** → `POST` fire-and-ack con
  `{ sheetId, nombre }` + el **secreto en header** (leído de `PropertiesService`) →
  `202` → **toast** "en proceso".

**Conceptos clave (en sencillo).**
- **El trigger solo dispara:** no parsea, no puntúa, no espera. Toda la lógica vive en
  Python (un solo lugar testeable). Apps Script es notoriamente difícil de probar; por
  eso se mantiene mínimo.
- **Secreto fuera del código:** `PropertiesService` guarda el secreto como propiedad
  del script, no escrito en el código fuente.

**Dependencias.** Fase 5 (el endpoint debe existir para apuntarle).

**Criterio de aceptación.** Manual: un clic dispara el `POST` (verificable en el log
del servicio) y muestra el toast. No hay lógica de negocio en el script.

**TBD/bloqueos.** Ninguno técnico; depende de tener la URL del servicio desplegado.

---

## Fase 8 — Cableado end-to-end + smoke

**Objetivo.** Que todo el pipeline funcione junto contra servicios reales en staging.

**Qué se construye.**
- El **ensamblado** del pipeline real dentro del background task
  (`parser → scoring → IA → render → upload → notificación`) con el **adapter de Sheets
  real** conectado.
- Un **smoke end-to-end** en staging con un Sheet de prueba (mapa de celdas placeholder
  + datos conocidos) → PDF en la carpeta de resultados.

**Conceptos clave (en sencillo).**
- **Smoke test:** una prueba de "¿enciende sin humo?" — recorre el camino real completo
  una vez para detectar problemas de integración que los tests con mocks no ven (auth
  real, permisos, formatos).
- **Enchufar lo que faltaba:** cuando lleguen los TBD (mapa real, diseño del PDF,
  prompt-persona), se conectan en sus puntos ya preparados, sin reestructurar.

**Dependencias.** Todas las fases anteriores.

**Criterio de aceptación.** Un clic real (Fase 7) produce el PDF correcto en Drive; un
fallo provocado produce email + evento `failed` en el log. Los scores del PDF de prueba
coinciden con el golden esperado.

**TBD/bloqueos.** Los tres TBD duros (mapa, diseño, prompt) siguen como placeholders
hasta que el cliente/diseño los entreguen; el smoke valida la *tubería*, no el diseño
final.

---

## Supuestos y bloqueos (resumen)

- **[TBD duro]** Mapa de celdas, diseño del PDF, prompt-persona: se construyen con
  placeholder y quedan marcados para enchufar (Fases 2, 4, 3).
- **[Verificado context7]** Scopes de Drive y la imposibilidad de mover el Sheet con
  `drive.file` (ver "Hallazgos previos").
- **[Decidido]** Idempotencia: no mutar el Sheet; PDF `<empresa>_<fecha>.pdf` sobrescribe
  en re-runs; cuenta de servicio dueña de la carpeta de resultados; solo scopes de
  lectura + `drive.file`.
- **[Supuesto]** Rate-limit: límite global bajo; mecanismo/umbral exactos por definir
  (Fase 5).
- **Regla transversal:** verificar firmas de Gemini SDK, WeasyPrint, matplotlib y
  google-api-python-client con **context7** en su fase — nunca de memoria.
