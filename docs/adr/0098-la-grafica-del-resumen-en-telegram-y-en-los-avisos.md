# 98. La gráfica del resumen en Telegram y en los avisos

Fecha: 2026-10-17 · Estado: aceptado

## Contexto

Juanjo, el 17-10-2026: «el gráfico resumen de meteo montflorit me parece una
de las mejores cosas, se podría enviar por telegram en las previsiones? pero
solo la parte de la que se hace la predicción». Después: «las notificaciones
de web y de app saldrán también con imagen?» y «todo junto en una sola
versión».

La gráfica (ADR 0096) se dibuja en el navegador con `web/grafica.js`. El bot
y los avisos de la web viven en IONOS (ADR 0034 y 0048) y solo enviaban
texto. En IONOS no hay navegador; en el NAS, tampoco había.

## Decisión

- **El NAS dibuja las imágenes** en cada publicación (`grafica_imatge.py`,
  desde `publica.sh`): una página temporal con `estil.css`, `comu.js`,
  `grafica.js`, los iconos de `casa.html` y los datos dentro, sin pedir
  nada fuera, que Chromium sin pantalla convierte en PNG (1000 px a doble
  resolución, 100-180 KB); Pillow recorta el blanco de debajo. El dibujo es
  el mismo código que la web: no hay una segunda gráfica que pueda
  separarse. Se descartó redibujarla en Python (dos dibujos que acabarían
  distintos). El contenedor lleva ahora `chromium` y la letra Roboto
  (`fonts-roboto-unhinted`), unos 300 MB más de disco.
- **Solo la parte de la que habla el resumen** (`graficaDia`, la misma que
  «Consultes»): la de hoy, de ahora a medianoche (resúmenes de la mañana y
  /resum); la de mañana, de las 18 h de hoy (la noche, como `bot.resum`) al
  final de mañana (resumen de las 21 h y /dema). En catalán y en castellano:
  cuatro imágenes, `grafica-{avui,dema}-{ca,es}.png`.
- **Suben a IONOS con los datos.** `reserva/rep-dades.sh` acepta además esos
  cuatro nombres exactos, si son PNG de verdad (firma de PNG) y de 600 KB
  como mucho cada uno; el resto de reglas no cambia (ADR 0038 y 0057).
  Quedan en `bilateria.org/app/meteo-local/`, públicas como los datos.
- **El bot y el canal**: el resumen va como pie de la foto (`sendPhoto`, con
  la dirección de la imagen; Telegram la baja y luego se reaprovecha su
  `file_id`). Si el texto pasa de 1.024 caracteres, la foto y después el
  texto. Si la foto no entra, solo el texto.
- **Los avisos de la web y la app**: la notificación del resumen lleva
  `image`. La muestran Chrome, Edge y Samsung Internet, también la app de
  Android (que es Chrome); Firefox y Safari no la admiten
  (browser-compat-data de MDN, 17-10-2026) y sale el texto solo, como antes.
- **Solo si es reciente**: la imagen se usa si tiene menos de 45 minutos
  (`bot.IMATGE_MAX_MIN`); si falta, falla Chromium o IONOS no la recibe, el
  resumen sale solo con texto, como antes.

## Riesgos

- Chromium en el NAS: unos 3 s de trabajo por publicación (cada 15 minutos;
  cada 6 en modo aviso). Si falla, se apunta en el registro y no se detiene
  nada.
- Telegram baja la imagen de IONOS: si no llega, el resumen sale sin ella y
  queda en `errors.log` del bot.
- En Android la imagen suele verse al desplegar la notificación; en el
  ordenador depende del sistema. No comprobado aún en el móvil de Juanjo.

## Validación

- Pruebas: el receptor acepta las cuatro imágenes y rechaza otro nombre,
  algo que no es PNG, un `.png.php` y una de más de 600 KB; el bot elige la
  imagen del día que toca y la descarta si es vieja; foto con pie, foto y
  texto si es largo, solo texto si la foto falla; la notificación lleva
  `image` solo si hay imagen reciente. 489 pruebas en verde.
- Las cuatro imágenes, generadas en local con Chromium a partir de los datos
  del 17-10-2026 y revisadas a ojo; dos pruebas enviadas a Juanjo por
  Telegram antes de publicar.
