# Trigger de Apps Script (Fase 7)

Botón **"Stragia → Generar diagnóstico"** en el Google Sheet. Solo dispara un POST
fire-and-ack al webhook (Fase 5); no parsea ni puntúa.

Contrato con el servicio:

```
POST  <WEBHOOK_URL>/v1/diagnosticos
Header:  X-Stragia-Secret: <WEBHOOK_SECRET>
Body:    { "sheetId": "<id del Sheet>", "nombre": "<named range 'empresa'>" }
Espera:  202  (todo lo pesado corre después, en el servicio)
```

## Requisito previo

El Sheet debe tener el **named range `empresa`** (lo crea la plantilla canónica /
`crear_plantilla.gs`, fuera del alcance de esta fase). Si no existe, el `nombre` irá
vacío y el servidor lo validará.

## Instalación (manual)

1. En el Sheet: **Extensiones → Apps Script** (crea un proyecto *bound* al Sheet).
2. Pega el contenido de **`Codigo.gs`** en el editor.
3. Muestra el manifiesto (**Project Settings → "Show appsscript.json"**) y pega
   **`appsscript.json`** (define los scopes: leer el Sheet + llamada externa).
4. Configura los secretos en **Project Settings → Script Properties**:
   - `WEBHOOK_URL` = base del servicio (p. ej. `https://stragia.onrender.com`)
   - `WEBHOOK_SECRET` = el mismo secreto que valida el webhook
   *(o corre la función `configurar()` una vez y luego borra los valores del código).*
5. Ejecuta `generarDiagnostico` una vez desde el editor para **autorizar** los scopes.
6. **Recarga el Sheet** → aparece el menú **"Stragia"**.

> El secreto vive en Script Properties, **nunca** en el código commiteado.

## Verificación (manual — no hay tests pytest)

1. Levanta el servicio con un secreto conocido:
   ```
   WEBHOOK_SECRET=xxx INPUT_FOLDER_ID=yyy uvicorn app.main:app --port 8000
   ```
   Para exponerlo a Apps Script durante pruebas, usa un túnel (p. ej. `cloudflared`/
   `ngrok`) y pon esa URL en `WEBHOOK_URL`.
2. En el Sheet: **Stragia → Generar diagnóstico**.
3. Esperado:
   - Toast **"Diagnóstico en proceso…"** en el Sheet.
   - En el log del servicio: `POST /v1/diagnosticos → 202` con un `runId`.
4. Casos de error (toast con el código): secreto mal → `401`; sheet no autorizado →
   `403`; demasiados clics → `429`.

## Notas

- **Idempotencia:** un doble clic es seguro — el servicio sobrescribe el PDF por
  nombre (Fase 6). No se muta el Sheet.
- **Fire-and-ack:** `UrlFetchApp` es síncrono, pero el `202` vuelve en <1s (el
  trabajo corre en background), así que el límite de ~6 min de Apps Script no aplica.
