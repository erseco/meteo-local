# 77. Mapa de cada corte de luz y la tabla explicada en corto

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

El mapa del barrio (ADR 0072) solo servía para enseñar los límites. Juanjo
preguntó si se le podía dar otra utilidad práctica. De las propuestas:

- La riera destacada en el mapa: «no me parece, todos saben donde está la
  riera, para ir a cerdanyola hay que cruzarla».
- Los cortes de luz: «el 2 sí, pero en ese mapa no salen los nombres de las
  calles», y «hay que evitar que quede tan cargado de nombres que no se pueda
  visualizar bien».

Además, sobre las notas de la tabla de previsión: «dice cosas poco útiles … no
debería salir ahí tan específico, solo lo que significa».

## Decisión

Versión 3.67.0.

- **Un mapa por corte en «Consultes › Llum»**: un recorte del barrio de unos
  600 × 450 m alrededor del punto aproximado de e-distribución, con:
  - el punto y un círculo alrededor, porque es aproximado;
  - las calles probables (`llum.carrers_probables`) resaltadas en naranja y
    con su nombre;
  - como mucho cuatro nombres de calles cercanas (a unos 290 m o menos).
- **Sin cargarlo de nombres**: cada nombre va a lo largo de su calle, en un
  tramo casi recto (la cuerda, al menos el 90 % del recorrido) donde quepa.
  No va si pisaría otro nombre (centros a menos de 60 unidades del dibujo) o
  el punto. Los nombres van cortos: «Sant Jeroni» y no «Carrer de Sant
  Jeroni»; «Av. Guiera». El recorte se ve a buen tamaño en el móvil, sin
  ampliarlo.
- **Las piezas, propias y sin pedir nada fuera**. `eines/mapa_barri.py`
  genera, a partir de OpenStreetMap:
  - `web/img/mapa-base.svg`, el fondo sin rótulos;
  - `web/img/carrers.json`, el trazado de cada calle con nombre (78) en las
    coordenadas del dibujo, y la proyección.
  `consultes.js` dibuja encima el punto, las calles y los nombres.
- **El mapa general del barrio** («Com funciona») rotula las calles
  principales (primary, secondary y tertiary de OpenStreetMap): como mucho
  ocho, separadas y sin cortarse en el borde. Hoy salen Santa Rosa, Av.
  Guiera, Av. Flor de Maig y Boters.
- **Cada corte publica su punto**, redondeado a 4 decimales (unos 10 m: el
  punto ya es aproximado), y **deja de publicar su distancia a casa**
  (`km`), que con dos o tres puntos diría dónde está. Dentro sigue sirviendo
  para ordenarlos.
- **«Com es llegeix la taula» (desde el 13-10-2026, «Com es llegeix la previsió»), solo lo que significa cada cosa**: qué son
  «Prob.» y «Pluja (mm)», el asterisco («hi compta la pluja que cau ara al
  barri»), la cruz («la pluja que el radar veu acostar-se»), la barra de
  color, el viento y que más allá de 24 horas es menos segura. Fuera de la
  tabla el método (de dónde se aprende la probabilidad y desde cuándo se
  corrige la temperatura): ya está en «D'on surt». Fuera `textAprenentatge`.

## Alternativas descartadas

- **La riera destacada en el mapa**: Juanjo, por lo dicho arriba.
- **Incendios y tráfico en el mapa**: se avisan a 3 y 5 km, fuera del
  barrio; harían falta otros mapas, y la distancia ya basta.
- **Todos los nombres de calle a la vez**: ilegible en el móvil.
- **Teselas de un servidor de mapas**: cada visita pediría a un tercero
  (ADR 0073, privacidad), y el mapa propio basta.

## Consecuencias

- Al ver un corte, se ve dónde es y qué calles toca, aproximado.
- Si cambian los límites o las calles, se rehacen el mapa general, el fondo
  y `carrers.json` con `eines/mapa_barri.py`.

## Evidencia

- Ejemplo con un corte inventado en 41,4803 N 2,1318 E: calles probables,
  Carrer de Catalunya y Avinguda de la Flor de Maig. El mapa rotula Av. Flor
  de Maig, Catalunya, Víctor Català, Doña Amelia, Mallorca y València (en
  Firefox, Provença en lugar de Mallorca, por el ancho de la letra).

## Riesgos y limitaciones

- Las incidencias de tráfico publican la carretera, el punto kilométrico y
  la distancia a casa: juntando muchas se podría acotar la zona. No se ha
  tocado; queda anotado.
- El fondo y las calles son de cuando se generaron; una calle nueva no sale
  hasta rehacerlos.

## Validación

- 394 pruebas en verde, con nuevas para los nombres cortos, la ventana y los
  nombres que no se pisan.
- `probar-web` (tres navegadores, móvil, tableta y escritorio, claro y
  oscuro) en «Consultes › Llum», en catalán y castellano, en «Com funciona» y
  en la portada: sin errores ni desbordamiento; axe-core sin incidencias.
- Juanjo lo miró en su móvil con el ejemplo («perfecto, publica»).

## Actualización (13-10-2026, versión 3.79.2)

**«D'on surt», en corto.** Juanjo: «hay demasiado texto» y «no hablas de las
5 estaciones locales usadas». Pasa de unas 1.300 palabras en 15 apartados a
unas 300 en 7 (estaciones del barrio, viento, previsión, probabilidad,
primeras horas, avisos y actualización), con las cinco estaciones sin
nombres (dos junto a la riera y tres en la parte alta) y un enlace a «Com
funciona» para el detalle. Lo provisional se dice en cada punto (Juanjo: «lo
das como fuente única y no es así, es solo temporal»): el viento de Sant
Cugat, hasta que se pueda hacer con las estaciones del barrio; la diferencia
con la parte alta en las noches de helada; el cálculo de la probabilidad con
los datos del barrio; la hora en que para la lluvia y el aviso de la riera.
La diferencia con la parte alta se explica como lo que es, medida y
cambiante, no como «+2» fijo. Sale un dato caducado («ara, RainViewer»: hoy
manda Meteocat). «Fonts i crèdits» y «Com funciona» cuentan también las
cinco estaciones y el viento provisional.

**«Com funciona», al día (3.79.3).** Juanjo: «revisa toda la página». La
probabilidad dice que sale del archivo de Sabadell y Sant Cugat de momento y
que cada día se entrena otra con la lluvia del barrio; la temperatura, que es
la de junto a la riera y que hay una corrección con el registro propio en
entrenamiento; dos apartados nuevos en «Una previsió que aprèn» (la
diferencia con la parte alta y el viento, provisional); la lluvia que llega
con probabilidad baja, recalculada con el cálculo actual (una de cada nueve
horas de lluvia, con menos del 5 %); «D'on surt» ya no se presenta como
detallado. Fuera «en un servidor domèstic» y las menciones al idioma de la
metodología y de los ADR (Juanjo: «el que lo abra ya lo verá»).

