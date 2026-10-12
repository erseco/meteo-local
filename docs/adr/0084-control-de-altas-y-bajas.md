# 84. Control de altas y bajas

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

Con la app de Google Play (ADR 0082), Juanjo preguntó si quien recibe avisos y
deja de usar la app se queda para siempre en IONOS. No: la suscripción se borra
con «Desactiva» o cuando el servicio de notificaciones la da por muerta, al
desinstalar la app o quitar el permiso; mientras la tenga instalada, sigue
recibiendo avisos, que es lo que se busca. Juanjo pidió llevar un control de
altas, bajas e inactividad, con un aviso por cada alta y también las del bot
(«si, hazlo asi con las altas del bot»).

Ya llegaba a Juanjo un mensaje por cada alta del bot, cada alta de los avisos
de la web (con el total) y cada alta y baja del canal. Faltaban de dónde viene
cada alta, las bajas y un resumen.

## Decisión

Versión 3.75.0; 3.75.1, el resumen dentro del informe de los lunes.

- **Registro de movimientos** (`~/.temps-bot/moviments.json` en IONOS, 400
  días): cada alta, baja, bloqueo del bot o dirección muerta de la web, con el
  día, el canal y, en las altas de la web, el origen. **Sin identificadores**:
  ni el chat ni la dirección de notificaciones. Lo escribe `B.moviment`, con su
  propio cerrojo, porque el bot y `push.py` corren a la vez.
- **Bot**: alta en `/start` y primera orden; baja con `/baixa`; «bloqueig»
  cuando Telegram responde que la persona ha bloqueado el bot (`B.treu`).
- **Avisos de la web**: `push.py` compara cada minuto las suscripciones con las
  de la vuelta anterior: las nuevas son altas; las que faltan, bajas
  («Desactiva») o muertas, si el servicio de notificaciones las acaba de
  rechazar (404 o 410).
- **Origen de cada alta de la web**: la web lo envía con la suscripción
  (`origenAvisos()` en `comu.js`) y `subscripcio.php` lo guarda: «app», si la
  sesión se abrió desde la app de Play (Chrome le pone a la página la
  referencia `android-app://io.github.meteo_montflorit`); «installada», si es
  la web instalada; «navegador», si no. Se recuerda solo durante la sesión
  (`sessionStorage`), porque la app y Chrome comparten lo que se guarda en el
  dispositivo. El origen del alta se queda aunque luego se cambien las
  opciones desde otro sitio. Las suscripciones anteriores salen como «sense
  origen».
- **Aviso a Juanjo en cada alta de la web**, con el origen, lo que se elige y
  el total desglosado:
  > Temps a Montflorit: alta nova als avisos de la web (app Android): perill,
  > riera. Total: 7 (app Android 3, web instal·lada 2, navegador 2).
  
  Las del bot y del canal siguen como estaban.
- **Resumen semanal en el informe de los lunes** (`bot.py informe`, a las 9 h,
  que ya daba los totales del bot, de la web y del canal y el uso del bot): se
  añaden las altas de los últimos 7 días (con su origen), las bajas y las
  direcciones muertas de la web, y las altas, bajas y bloqueos del bot; y, en
  el total de la web, de dónde se activaron. Un solo mensaje, no dos.
- **Página «Privacitat»**: dice que se guarda desde dónde se activaron los
  avisos y que se cuentan las altas y las bajas de cada día, sin saber quién.

## Alternativas descartadas

- **Medir la inactividad** (quién deja de abrir la app): la app tendría que
  avisar al servidor cada vez que se abre, que es seguir el uso de cada
  persona. Lo contrario de lo que dice «Privacitat» («ni estadístiques de qui
  la fa servir») y de lo declarado en Play (el identificador, solo para los
  avisos). Lo más parecido sin seguimiento son las direcciones muertas.
- **Borrar a quien lleve tiempo sin abrir la app**: dejaría sin avisos, sin
  decirlo, a quien la tiene instalada para las emergencias.
- **Un mensaje por cada baja**: van en el resumen semanal, para no interrumpir.
- **Las instalaciones de Play**: ya las cuenta Google en Play Console
  («Estadísticas»), sin que la app recoja nada.

## Riesgos

- Una dirección muerta solo se descubre cuando toca enviarle algo: quien solo
  eligió la riera puede tardar meses en salir como baja.
- El origen «app» depende de la referencia que pone Chrome al abrir la TWA; si
  un navegador no la pone, la alta sale como «web instal·lada».

## Validación

- Pruebas: `test_alta_amb_origen_i_moviments` (`test_push.py`),
  `test_moviments_del_bot` y `test_moviments_a_l_informe` (`test_bot.py`);
  ninguna guarda ni muestra un identificador.
- `subscripcio.php` con PHP 8.2 y un servidor local (12-10-2026): el alta desde
  la app guarda «app»; un cambio posterior con «navegador» no lo cambia; un
  origen inventado no se guarda.
- Playwright en Chromium, Firefox y WebKit, con la referencia de la app
  simulada: «app» al abrir y al cambiar de página; en otra pestaña,
  «navegador». La referencia real de la TWA no se puede reproducir aquí: se
  verá en el primer aviso de alta desde la app.
