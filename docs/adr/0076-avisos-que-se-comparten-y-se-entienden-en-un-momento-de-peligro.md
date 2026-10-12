# 76. Avisos que se comparten y se entienden en un momento de peligro

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

Juanjo: «quiero que se pueda compartir para poder enviar el mensaje
rápidamente a otros, puede llevar a una página ad hoc que explique la alerta
… tanto la riera como las alertas calculadas por la app».

Al revisar la versión 3.65.0:

- **Compartir:** el botón de cada ficha de «Perill» enviaba solo el título y
  el enlace.
- **Más información de la riera y del tiempo extremo** (los dos avisos que
  calcula la web): llevaba a la metodología técnica, en GitHub, con fórmulas
  y solo en castellano.
- **La riera no salía en la portada**, solo en «Perill», porque los datos
  públicos no llevan su estado.
- **En la tabla de previsión**, el peligro que calcula la web no se veía. Un
  tramo con lluvia muy fuerte decía «pluja forta», y Juanjo: «eso en sí no
  indica ningún peligro especial».

Al ver el ejemplo:

- «demasiado texto para leerlo en un momento de peligro, condénsalo», primero
  de las explicaciones y luego del propio aviso;
- «los botones de compartir tienen que copiar automáticamente» y, después,
  «me refiero a compartir, debe salir el menú de compartir».

## Decisión

Versión 3.66.0.

- **Compartir el aviso entero.** El botón de cada ficha de «Perill» abre el
  menú de compartir del dispositivo con el mensaje completo (sin las líneas
  que son solo un enlace y, si ha acabado, con el final) y el enlace a la
  ficha. Donde no hay menú (algunos navegadores de ordenador, o fuera de
  `https`), se copia solo, al momento: primero de la forma clásica
  (`execCommand`), que funciona también sin `https`; si no, con el
  portapapeles del navegador. Solo si nada de eso funciona se muestra el
  texto ya seleccionado. Nunca se pide copiar a mano.
- **Una explicación corta de los avisos propios**, en «Com funciona», en
  catalán y castellano: «L'avís de la riera de Sant Cugat» (`#riera`) y «Els
  avisos de temps extrem de la web» (`#temps-extrem`). Arriba, destacado,
  qué hacer o qué significa; después, los umbrales en una lista corta y una
  línea con el enlace a la metodología. Las fichas de la riera y del tiempo
  extremo llevan «Què vol dir aquest avís» a esos apartados, en lugar de «Més
  informació» a la metodología. `avisos_bot.ENLLAC_RIERA` y `ENLLAC_PROPI`
  apuntan allí, en la lengua de quien lo lee.
- **Los avisos de la riera y del tiempo extremo, condensados**: primero qué
  hacer, después un solo dato y una nota corta. El de la riera: «No t'acostis
  a la riera. / 54 mm en 3 hores a Sant Cugat (a les 07:26) i el radar en veu
  venir més: amb aquesta pluja ja s'ha desbordat altres vegades. / Avís en
  proves, orientatiu i no oficial.». Los finales, en una línea, sin la nota.
  El del tiempo extremo termina con «Calculat per aquesta web, no oficial.».
  Son los mismos textos de Telegram, del móvil y de «Perill».
- **La riera activa, en «Avisos actius»** de «El temps» y de «Si surts»: el
  título y «No t'acostis a la riera.», con «›» a su ficha exacta de «Perill».
  Sale del historial de `avisos.json`, que la página ya leía cada 5 minutos
  para el punto rojo. `idFitxa` pasa de `perill.js` a `comu.js`.
- **El peligro, en la tabla de previsión.** Cada hora junta los avisos de la
  AEMET y los riesgos que calcula la web (`riscos`) y lleva la barra de color
  de la columna de avisos. El tramo lleva la franja lateral del color del
  nivel y, en la cabecera, «⚠ Avís taronja: pluja molt forta», y se abre
  solo. Se nombra solo lo que da el nivel más alto: con un amarillo de la
  AEMET por lluvia y un naranja de la web, «taronja: pluja molt forta».
- **El aviso de la AEMET no se repite** en el resumen del día de la portada:
  ya sale arriba, en «Avisos actius». En «Consultes › Avui» se queda.
- **«Atrás» vuelve a donde se estaba** desde una página de explicación
  («Com funciona», «Fonts i crèdits»…). De una pestaña a una de esas páginas
  el navegador lo apunta; entre pestañas se sigue sustituyendo, y «El temps»
  vuelve a la portada deshaciendo todos los pasos (`history.go`). Corrige el
  ADR 0074: desde «Què vol dir aquest avís», «atrás» llevaba a la portada y no
  al aviso.
- **El Pla Alfa de «Perill», con su botón de compartir** (era la 3.65.1, que
  se retiró antes de desplegarse para publicarla con todo esto; ADR 0075).

## Alternativas descartadas

- **Una página nueva para cada aviso propio.** Dos apartados en «Com
  funciona», que ya está traducida y enlazada, son menos piezas.
- **Mostrar el estado de la riera desde los datos públicos.** Habría que
  publicar `riera`, que hoy es privado (ADR 0027). El historial de «Perill»
  ya dice lo que cuenta: si hay aviso y de qué nivel.
- **Una tabla de umbrales en «Com funciona».** La traducción automática de la
  página trabaja por párrafos y elementos de lista, no por celdas: va en
  lista.

## Consecuencias

- Un aviso se reenvía con un toque, entero, y quien lo recibe llega a su
  ficha y, desde allí, a una explicación breve.
- La portada enseña todos los peligros activos, la riera incluida, y la
  previsión marca cuándo.

## Evidencia

- Ejemplo con datos inventados sobre los publicados del 12-10-2026: lluvia,
  aviso amarillo de la AEMET, riesgo naranja de la web de 7 a 8 h y peligro
  de la riera.
- En Chromium, sin `https` (la copia local por la IP de casa), sin menú de
  compartir: el botón copia el aviso entero con el enlace, leído después del
  portapapeles.

## Riesgos y limitaciones

- El menú de compartir solo existe en `https` y en los navegadores que lo
  ofrecen; la copia de prueba local no lo enseña.
- La riera llega a la portada con hasta 5 minutos de retraso (la lectura del
  historial).

## Validación

- 393 pruebas en verde, con nuevas para compartir (menú y copia), el peligro
  por hora y por tramo, las líneas del resumen y «atrás».
- «Atrás» en Chromium, Firefox y WebKit: Perill → «Què vol dir aquest avís» →
  atrás, a Perill → atrás, a la portada → atrás, fuera; «El temps» desde la
  explicación, a la portada.
- `probar-web` (tres navegadores, móvil, tableta y escritorio, claro y
  oscuro) en «El temps», «Perill», «Si surts», «Consultes» y «Com funciona»,
  en catalán y castellano, sin errores ni desbordamiento; axe-core sin
  incidencias.

## Ampliación del 12-10-2026 (3.66.1): «pluja» o «possible pluja»

El resumen del día decía «Pluja: possible de 7 a 10 h (probabilitat fins al
95 %)»: «possible» con un 95 %. Ahora usa las palabras de la columna «Cel» de
la tabla (Juanjo: «hazlo»): «pluja» desde el 50 % y «possible pluja» desde el
20 %, en cada franja: «Pluja de 7 a 10 h (probabilitat fins al 95 %); possible
pluja de 18 a 19 h (fins al 25 %).». Lo mismo en «Aquesta nit: …», en
«Consultes › Avui» y «Demà», y en el resumen diario de Telegram y del móvil
(`bot.text_franges`).

