# 96. Una gráfica de la previsión encima de los tramos

Fecha: 2026-10-16 · Estado: aceptado

## Contexto

La previsión de la portada es una lista de tramos (Matí, Tarda, Nit, Demà
matí, Demà tarda) que se despliegan en tablas hora a hora. Para ver de un
vistazo cómo irá el día hay que leer varias tarjetas. Juanjo pidió «un
resumen visual … donde se vea la temperatura, el estado del cielo, la
lluvia, avisos, peligros» que fuera «muy visual y muy claro», y propuso
ponerlo antes de «D'on surt». Se le propuso arriba de «Previsió» (al final
de la página quedaba debajo de las tablas y repetía lo que se acababa de
leer) y un meteograma, el patrón de Yr o meteoblue; lo aprobó. Señaló que
una línea vertical de «ara» no tenía sentido, porque la gráfica empieza
siempre en la hora en curso.

## Decisión

- **Un meteograma al principio de «Previsió»**, antes de los tramos, de la
  hora en curso hasta el final de la tabla (las 21 h de mañana). Las mismas
  horas y los mismos datos que las tablas (`casa.grafica`), sin nada que no
  esté debajo.
- **De arriba abajo**: la franja de peligro, del color del nivel y con el
  texto de la tabla («Perill alt: pluja»); si no cabe dentro (un aviso de
  pocas horas), al lado, y completo al tocarla. Debajo, «Avui» y «Demà»,
  separados por una raya discontinua a medianoche, y el cielo, un icono cada
  3 h (cada 2 h si hay sitio), el de lluvia si llueve en alguna hora del
  bloque. El cielo queda aparte, arriba: nada llega a su fila.
- **Temperatura y lluvia en la misma zona**, las barras detrás de la línea,
  como en los meteogramas habituales (Juanjo: «mezclando ambas, con las barras
  por detrás, será lo mejor y más natural»). La línea lleva un borde del
  color del fondo para verse sobre las barras. Desde la 3.96.1 la línea es
  una curva suave (cúbica monótona, la «monotoneX» de d3: pasa por cada hora
  y no sube ni baja más que los datos) con un relleno rojo muy tenue debajo,
  detrás de las barras (Juanjo: «tiene picos… que parezca más profesional»).
- **La temperatura**: la cifra, debajo de cada icono del cielo, la de la
  hora del medio de su bloque (Juanjo: «no quedaría bien la temperatura bajo
  el cielo?»): cielo y temperatura se leen juntos. La línea, sin cifras, dice
  si sube o baja. Antes llevaba la máxima y la mínima de cada día y la de la
  hora en curso; esta, prevista, no coincidía con la medida de «Ara», y dos
  cifras iguales a distinta altura parecían un error. La máxima exacta puede
  caer entre dos iconos: está en el resumen del día y en cada tramo.
- **La lluvia**: la altura es la cantidad, no la probabilidad (con la
  probabilidad, una hora de 0,5 mm y una de 45 mm salían iguales). Escala fija,
  para que un día de llovizna no parezca un diluvio, y de raíz cuadrada, para
  que 1 o 2 mm se vean: arriba del todo, 40 mm en una hora. Azul lleno si es
  probable (desde el 50 %), claro si solo es posible (del 20 al 50 %) y sin
  barra por debajo, los mismos umbrales que el cielo de la tabla. La pluja
  forta (desde 40 mm en una hora) en naranja y la torrencial (desde 80) en
  rojo: las intensidades del manual de estilo de Meteocat, las palabras de la
  columna «Cel» (ADR 0043). Los avisos no colorean las barras: van en la
  franja. Los milímetros, con su unidad, en la hora más fuerte de cada
  episodio.
- **La noche**, sombreada en gris, de la puesta a la salida del sol: un color
  que no se confunda con la lluvia.
- **El eje empieza por «Ara»**, sin línea vertical: la gráfica empieza siempre
  en la hora en curso. Cada hora lleva una marca: larga y con número las que
  tocan (cada 3 h, o 2), corta y sin número la resta (Juanjo, 16-10-2026).
- **Debajo, una leyenda** de una palabra por clave, sin paréntesis:
  Temperatura y Nit, y cada clase de lluvia solo cuando sale: «Pluja, 50 % o
  més», «Pluja, del 20 al 50 %», Pluja forta y Pluja torrencial. Desde la
  3.97.1 la probabilidad va en cifras; hasta entonces ponía «Pluja probable» y
  «Pluja possible». Juanjo: «entre lluvia probable y puede llover no hay
  diferencia para un usuario normal»; los porcentajes son los mismos umbrales
  que el cielo de la tabla (`PROB_PLUJA` y `PROB_POSSIBLE` de `casa.js`).
  Desde la 3.97.2, también «Pluja, del 10 al 20 %», en turquesa
  (`PROB_POCA`, solo en la gráfica): en el archivo de 2024-2026, con un 10-20 %
  llovió una de cada siete horas, y por debajo del 20 % caía una de cada cinco
  horas de lluvia, que la gráfica no enseñaba. Desde el 1 % se descartó (por
  debajo del 5 % llueve menos de una vez de cada cien) y desde el 5 %, porque
  añadía marcas con poca información. El color, propio y no un azul más
  claro (Juanjo: «el color que se diferencie de los que ya hay»). La tabla no
  cambia: «possible pluja» sigue siendo desde el 20 %.
- **Fuera de entrada**: el viento, la parte alta y el UV, que ya están en las
  tablas. Se añadirán si se echan en falta.
- **Tocar una hora** (o pasar el ratón, en el ordenador) muestra encima un
  rótulo con su hora, sus milímetros y su probabilidad («17 h · 6 mm ·
  70 %»), y marca la columna; se quita al tocar fuera o la misma hora. Desde
  la 3.98.0: Juanjo preguntó si se podían poner los milímetros en todas las
  barras («solo pone la lluvia del mayor?»), pero en el móvil cada hora mide
  de 9 a 15 px y la cifra unos 17; con litros sería igual de larga y habría
  que escribir «l/m²». La cifra de la hora más fuerte de cada episodio (desde
  0,5 mm) sigue a la vista.
- **La ficha de cada hora** (desde la 3.101.0; Juanjo, 17-10-2026: «no se
  podrían añadir el resto de datos meteorológicos de previsión de esa
  hora?»): el rótulo pasa a ser una ficha con la hora y el cielo, la
  temperatura, la lluvia (mm y probabilidad) y el viento con sus rachas.
  La parte alta, solo si difiere al menos 1 °C (el mismo redondeo que las
  tablas); la nieve, solo si se espera, y el UV, solo de día y desde 3,
  donde la escala de la OMS ya pide protección. Fuera, el porcentaje de
  nubes (ya lo dice el cielo) y los avisos (la franja está encima de la
  columna). No hay humedad ni dirección del viento en los datos. La ficha
  va al lado de la columna, donde quepa, para no tapar la hora; si no cabe
  a ningún lado (en el móvil, las horas del centro), debajo del eje,
  encima de la leyenda.
- **La gráfica en grande** (desde la 3.101.0; Juanjo, 17-10-2026: «verlo en
  su propia ventana o sección y con posibilidad de alguna configuración»):
  el botón «Amplia», junto a «Desplega-ho tot» (en el móvil, solo el icono,
  para que los dos quepan al lado del título), la abre sobre la página, con
  margen, más alta y con su dirección (`#grafica`) para compartirla. No es
  una página más del menú: sería la misma gráfica repetida. Opciones: qué
  horas (hoy, mañana o todo; hoy y mañana, solo si tienen al menos 3 horas)
  y el viento como capa (media y rachas, escala de 10 en 10 desde 20 km/h).
  La parte alta y el UV no son capas: ya salen en la ficha de cada hora. Lo
  elegido se recuerda en el dispositivo. Se cierra con la X, Esc o tocando
  fuera. Con columnas anchas, el cielo y las horas salen cada hora.
- **El nombre de cada día, por su fecha** (Juanjo, 17-10-2026): de noche la
  tabla llega hasta pasado mañana, y la segunda medianoche decía otra vez
  «Demà»; ahora «Demà passat». El primer nombre se quita si no cabe antes de
  la medianoche («si avui no cabe no se escriba nada, ya se entiende»).
- **También en «Consultes»** (Juanjo, 17-10-2026: «en las fichas de
  consulta: avui y demà también deberá aparecer el gráfico
  correspondiente»): bajo el título de «Avui», la gráfica de ahora a
  medianoche; en «Demà», la de mañana (de 0 h al final de los datos). Con
  menos de 3 horas, ninguna. El dibujo es el mismo: la gráfica y lo que
  necesita (el cielo, la lluvia y el perill de cada hora) pasan de
  `casa.js` a `web/grafica.js`, que cargan la portada y «Consultes».
- **Los textos de los avisos, sin pisarse** (Juanjo, 17-10-2026: «sin que
  se pierda información vital. si es necesario usa dos filas»): dentro de
  la franja, el texto entero (nivel y fenómenos) si cabe. Si no, al lado,
  a la derecha o a la izquierda, solo si allí no hay ninguna franja ni
  otro texto (el texto debajo, solo, «no lo entiendo»). Si tampoco, en una
  fila debajo, con un cuadrito del color del aviso, desde donde empieza;
  si choca con el anterior, en otra fila (hasta tres), y solo si tampoco
  cabe, el nivel solo. Antes iba al lado sin comprobarlo y caía encima del
  texto de otra. Al tocar la franja o su texto, siempre el aviso completo.
  Probado con cuatro avisos seguidos a 320 px: nada se pisa.
- **Todos los avisos de la hora en la franja** (Juanjo, 17-10-2026: con
  perill alt de Meteocat por lluvia y aviso amarillo de AEMET por
  tormentas, la franja solo decía el primero; «que la franja diga las dos
  cosas»): el color es el del nivel más alto y el texto los dice todos, del
  más alto al más bajo («Perill alt: pluja · Avís groc: tempestes»). Cada
  fenómeno, una sola vez y en su nivel más alto: un amarillo de AEMET por
  lluvia no se repite bajo un naranja de lluvia intensa de la web. Vale
  también para la barra de las tablas y la etiqueta de cada tramo, que usan
  lo mismo (`avisHora`, `perillTram`).
- **El cielo, la temperatura y la hora, cada hora si hay sitio** (Juanjo,
  17-10-2026: «la gráfica está bastante vacía, mejor que salga cada hora»):
  desde 30 px por hora; si no, cada 2 (desde 18 px) o cada 3.
- **El origen de cada aviso en la franja** (Juanjo, 17-10-2026: «añade el
  origen: meteocat, aemet, etc»): «Perill alt (Meteocat): pluja · Avís groc
  (AEMET): tempestes»; los de la web, «(aquesta web)». Solo en la gráfica:
  las tablas lo dicen al tocar la barra. Debajo de la franja, cada aviso va
  por separado, con el cuadrito de su nivel, y abre las filas que hagan
  falta: con cuatro avisos seguidos a 320 px, el rojo se quedaba sin sitio
  con el límite de tres filas.
- **La imagen para Telegram y los avisos** sale de esta misma gráfica (ADR
  0098).
- **El techo de la lluvia, por escalones** (3.101.1; Juanjo, 17-10-2026: «las
  columnas me parecen cortas» y «no sería mejor una escala variable?»): en
  lugar de 40 mm siempre, el primer escalón de 10, 20, 40, 80 o 160 mm que
  cubre la lluvia más fuerte de la gráfica, nunca menos de 10 mm, con una
  raya fina arriba y su cifra («10 mm»), como la del viento. Una escala que
  se ajustara justo al máximo haría que 1 mm pareciera una tromba; con los
  escalones, la llovizna sigue viéndose pequeña y el naranja y el rojo
  siguen avisando de la fuerte y la torrencial. Con los datos del 17-10, los
  6,9 mm de la noche pasan del 41 % al 83 % de la altura. La cifra de mm que
  no cabe sin pisar otra ya no se escribe: sale en la ficha de la hora.
- **SVG dibujado desde `casa.js`**, sin bibliotecas ni conexiones externas,
  con el ancho real de la pantalla (se redibuja al cambiar de tamaño) para que
  el texto no se encoja en el móvil, y con los colores del tema claro y
  oscuro. La gráfica no va para los lectores de pantalla (`aria-hidden`):
  una descripción oculta dice que los mismos datos están en las tablas.

## Alternativas descartadas

- **Al final, antes de «D'on surt»**: la vería poca gente y repetiría las
  tablas.
- **Una cinta por tramos** (una columna por tramo): se lee al instante pero
  no enseña cómo cambian la temperatura y la lluvia a lo largo del día. Queda
  como alternativa si el meteograma no se leyera bien en el móvil.
- **Una biblioteca de gráficas**: añadiría una dependencia para un dibujo
  sencillo.
- **La altura de la lluvia por probabilidad, con una raya en el 50 %** (la
  3.94.0): la lluvia fuerte salía tan pequeña como la débil.
- **Temperatura y lluvia en zonas separadas**: se probó, primero con la lluvia
  baja y después con la misma altura; juntas se leen mejor y caben más altas.
- **Barras con los colores de aviso** (desde 20, 40 y 90 mm, los umbrales de
  AEMET): no corresponden a ninguna escala de nombres y obligaban a inventar
  una etiqueta («pluja d'avís»). El aviso ya está en la franja.

## Riesgos

- En un móvil estrecho (320 px), 33 horas salen a unos 10 px por hora: los
  iconos van cada 3 h y el texto de la franja se acorta.
- La lluvia se probó con datos simulados (una tormenta con 45 y 85 mm en una
  hora y un aviso naranja propio); falta verla con un episodio real.
- La escala se corta en 40 mm: por encima, la barra llena y el color (forta,
  torrencial) dicen cuánto.

## Validación

- `probar-web` en Chromium, Firefox y WebKit, en escritorio, móvil y tableta,
  claro y oscuro, sin errores ni desbordamiento; móvil de 320 px y versión en
  castellano en móvil. axe-core sin incidencias en «Previsió».
- Ninguna hora del eje se superpone a «Ara» ni a «Ahora» en los tres
  navegadores, a 320 y 412 px. 478 pruebas en verde, una de ellas para las
  intensidades de las barras.
- 3.95.0 y 3.96.0, con datos simulados de tormenta: los mismos navegadores,
  tamaños y temas, y axe-core sin incidencias. En un móvil de 320 px, un
  primer bloque de menos de 3 horas no lleva icono ni cifra.
