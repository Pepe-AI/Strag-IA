/**
 * Stragia — trigger del Sheet (Fase 7).
 *
 * SOLO dispara: hace un POST fire-and-ack al webhook con { sheetId, nombre } y el
 * secreto en header. NO parsea ni puntúa — toda la lógica vive en el servicio Python.
 *
 * Config (Project Settings → Script Properties, o corre configurar() una vez):
 *   WEBHOOK_URL     base del servicio, p. ej. https://stragia.onrender.com
 *   WEBHOOK_SECRET  el mismo secreto que valida el webhook
 */

var ENDPOINT = '/v1/diagnosticos';

/** Menú al abrir el Sheet. */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Stragia')
    .addItem('Generar diagnóstico', 'generarDiagnostico')
    .addToUi();
}

/** Handler del botón: dispara el webhook y muestra un toast. */
function generarDiagnostico() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var props = PropertiesService.getScriptProperties();
  var url = props.getProperty('WEBHOOK_URL');
  var secret = props.getProperty('WEBHOOK_SECRET');

  if (!url || !secret) {
    ss.toast('Falta configurar WEBHOOK_URL / WEBHOOK_SECRET (Script Properties).',
             'Stragia — error de configuración', 8);
    return;
  }

  // El nombre de la empresa sale del named range `empresa` (mismo dato que parsea Python).
  var rango = ss.getRangeByName('empresa');
  var nombre = rango ? String(rango.getValue()).trim() : '';

  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: { 'X-Stragia-Secret': secret },
    payload: JSON.stringify({ sheetId: ss.getId(), nombre: nombre }),
    muteHttpExceptions: true,
  };

  try {
    var resp = UrlFetchApp.fetch(url.replace(/\/+$/, '') + ENDPOINT, options);
    var code = resp.getResponseCode();
    if (code === 202) {
      ss.toast('Diagnóstico en proceso. El PDF aparecerá en la carpeta de resultados.',
               'Stragia', 6);
    } else {
      ss.toast('El servidor respondió ' + code + '. Revisa el secreto y los permisos.',
               'Stragia — error', 8);
    }
  } catch (err) {
    ss.toast('No se pudo contactar el servicio: ' + err, 'Stragia — error', 8);
  }
}

/**
 * Setea las Script Properties UNA vez. Edita los valores, ejecútalo desde el editor,
 * y luego borra los valores de aquí para no dejar el secreto en el código
 * (o hazlo desde Project Settings → Script Properties, sin tocar este archivo).
 */
function configurar() {
  PropertiesService.getScriptProperties().setProperties({
    WEBHOOK_URL: 'https://TU-SERVICIO.onrender.com',
    WEBHOOK_SECRET: 'PEGA-AQUI-EL-SECRETO',
  });
}
