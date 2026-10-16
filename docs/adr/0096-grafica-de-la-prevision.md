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
  texto de la tabla («Perill alt: pluja»), tan largo como quepa y completo al
  tocarla; «Avui» y «Demà», separados por una raya discontinua a medianoche;
  el cielo, un icono cada 3 h (cada 2 h si hay sitio), el de lluvia si
  llueve en alguna hora del bloque; la temperatura en una línea, con la
  máxima y la mínima de cada día en cifras (la de ahora, solo si cabe: ya
  sale en «Ara»); la lluvia, una barra por hora tan alta como la
  probabilidad, más oscura cuantos más milímetros, con los milímetros en la
  hora más fuerte de cada episodio y una raya en el 50 %; la noche,
  sombreada de la puesta a la salida del sol.
- **El eje empieza por «Ara»**, sin línea vertical. Cada hora lleva una
  marca: larga y con número las que tocan (cada 3 h, o 2), corta y sin
  número la resta (Juanjo, 16-10-2026).
- **Debajo, una leyenda corta** (temperatura, probabilidad de lluvia, noche).
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

## Riesgos

- En un móvil estrecho (320 px), 33 horas salen a unos 10 px por hora: los
  iconos van cada 3 h y el texto de la franja se acorta.
- El día del prototipo la lluvia era floja (16 % como mucho): falta ver la
  gráfica con lluvia de verdad.

## Validación

- `probar-web` en Chromium, Firefox y WebKit, en escritorio, móvil y tableta,
  claro y oscuro, sin errores ni desbordamiento; móvil de 320 px y versión en
  castellano en móvil. axe-core sin incidencias en «Previsió».
- Ninguna hora del eje se superpone a «Ara» ni a «Ahora» en los tres
  navegadores, a 320 y 412 px. 477 pruebas en verde.
