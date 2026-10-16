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
- **Fuera de entrada**: el viento, la parte alta y el UV, que ya están en las
  tablas, y tocar una hora para ver sus datos. Se añadirán si se echan en
  falta.
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
