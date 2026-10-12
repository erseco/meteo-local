# 84. Control de altas y bajas

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

Con la app de Google Play (ADR 0082), Juanjo preguntó si quien recibe avisos y
deja de usar la app se queda para siempre en IONOS. No: la suscripción se borra
con «Desactiva» o cuando el servicio de notificaciones la da por muerta, al
desinstalar la app o quitar el permiso; mientras la tenga instalada, sigue
recibiendo avisos, que es lo que se busca. Juanjo pidió llevar un control de
altas, bajas e inactividad, y que le llegaran también las altas del bot.

Ya le llegaba un mensaje por cada alta del bot, cada alta de los avisos de la
web y cada alta y baja del canal, y los lunes un informe con los totales.

## Decisión

Versión 3.75.3.

- **Solo totales** (Juanjo, 12-10-2026: «no quiero datos de los usuarios, me
  interesa el total, no saber de donde viene cada uno»).
- **Registro de movimientos** (`~/.temps-bot/moviments.json` en IONOS, 400
  días): por cada alta, baja, bloqueo del bot o dirección muerta de la web, el
  día, el canal («bot» o «web») y el tipo. Nada más: ni el chat, ni la
  dirección de notificaciones, ni qué se elige. Lo escribe `B.moviment`, con su
  propio cerrojo, porque el bot y `push.py` corren a la vez.
- **Bot**: alta en `/start` y primera orden; baja con `/baixa`; «bloqueig»
  cuando Telegram responde que la persona ha bloqueado el bot (`B.treu`).
- **Avisos de la web**: `push.py` compara cada minuto las suscripciones con las
  de la vuelta anterior: las nuevas son altas; las que faltan, bajas
  («Desactiva») o muertas, si el servicio de notificaciones las acaba de
  rechazar (404 o 410).
- **Mensajes a Juanjo**, como antes: cada alta del bot y de la web, con el
  total («alta nova als avisos de la web (ja en són 7)»).
- **Informe de los lunes** (`bot.py informe`, a las 9 h, que ya daba los
  totales y el uso del bot): añade cuántas altas, bajas y direcciones muertas
  ha habido en la web, y cuántas altas, bajas y bloqueos en el bot, en los
  últimos 7 días.
- **Página «Privacitat»**: «Es compten les altes i les baixes de cada dia,
  sense saber qui», en los avisos de la web y en el bot.

## Alternativas descartadas

- **Guardar desde dónde se activó cada suscripción** (app, web instalada o
  navegador), para saber cuántas altas venían de la app. Se hizo en la 3.75.0 y
  se quitó en la 3.75.3: era un dato más de cada persona, y Juanjo solo quiere
  los totales. Las instalaciones de la app ya las cuenta Google en Play
  Console («Estadísticas»), sin que la app recoja nada.
- **Medir la inactividad** (quién deja de abrir la app): la app tendría que
  avisar al servidor cada vez que se abre, que es seguir el uso de cada
  persona. Lo más parecido sin seguimiento son las direcciones muertas.
- **Borrar a quien lleve tiempo sin abrir la app**: dejaría sin avisos, sin
  decirlo, a quien la tiene instalada para las emergencias.
- **Un mensaje por cada baja o un resumen aparte**: van en el informe de los
  lunes, un solo mensaje.

## Riesgos

- Una dirección muerta solo se descubre cuando toca enviarle algo: quien solo
  eligió la riera puede tardar meses en salir como baja.

## Validación

- Pruebas: `test_altes_i_baixes_nomes_els_totals` (`test_push.py`),
  `test_moviments_del_bot` y `test_moviments_a_l_informe` (`test_bot.py`):
  cada movimiento lleva solo el día, el canal y el tipo.
- En IONOS (12-10-2026), tras desplegar: `push.py` corre cada minuto sin
  errores y el texto del informe sale con los movimientos.
- `web/`, `bot/subscripcio.php` y lo que se guarda de cada suscripción quedan
  como antes de la 3.75.0.
