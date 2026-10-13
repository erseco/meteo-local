# 85. Consenso de la red del barrio: la lluvia y la humedad

Fecha: 2026-10-13 · Estado: aceptado

## Contexto

La web describía lo de ahora como «de la estación de casa», con las vecinas
de Weather Underground (ADR 0060) solo para decir si llueve, y lo aprendido
ya contaba la lluvia de Montflorit con las vecinas (ADR 0070). Juanjo,
13-10-2026: «la idea es que el tiempo se calcule a partir de la pequeña red
de estaciones caseras, ampliado con todo el resto de datos que recoge la app.
Quizás lo único que quiero que siga igual es la temperatura» y «mi idea es
que mi estación no sea la principal sino que los datos se hagan por consenso
de las 4 o 3 que hay ahora». Sin avisos en la página: «debe hacerlo
silenciosamente».

Al repasar el código, tres cosas salían solo del pluviómetro de casa, cuyo
cero no es fiable (ADR 0017): la lluvia de hoy y de la última hora de «Ara»,
la persistencia de las primeras horas de la previsión y el riesgo por la
lluvia medida en una hora. Además, «Ara» decía «Plou en una estació veïna»
cuando no llovía en casa, y la intensidad era siempre la de casa.

## Decisión

Versión 3.76.0 (`casa.consens`, `casa.consens_pluja`).

- **La red, para la lluvia**: la estación de casa y las tres vecinas que
  cuentan para «plou ara» (ICERDA6, ICERDA18 e ICERDA28; ICERDA48 pierde
  demasiada lluvia, ADR 0070), con las que se hayan podido leer.
- **Lluvia de la última hora y de hoy**: la mediana de la red. La de hoy de
  cada vecina se suma por incrementos desde medianoche, porque su total del
  día no siempre vuelve a cero a medianoche local.
- **Llueve ahora**: como hasta ahora, si llueve en cualquiera de las cuatro
  (ADR 0060): una sola estación que marca lluvia casi nunca se equivoca
  (0 a 2 horas de 1.643, ADR 0070), y exigir dos retrasaría el «plou». Con
  la intensidad mediana de las que la marcan. La página dice «Plou», con la
  intensidad si la hay, sin decir de qué estación sale.
- **Persistencia** de las cuatro primeras horas (estadistica.md, apartado 5)
  y **riesgo por la lluvia medida** (`riscos.de_l_estacio`): con la mediana
  de la red. El riesgo ya no exige que llueva en casa en ese momento.
- **Humedad**: con la mediana del punto de rocío de casa y de las cuatro
  vecinas, y la temperatura de casa. El rocío, el agua que hay en el aire, es
  el mismo en todo el barrio; la humedad relativa depende de la temperatura,
  y la de casa es la que enseña la página.
- **Se queda la de casa**: la temperatura, que es la de la zona más fría del
  barrio (ADR 0081; Juanjo, 12-10-2026: «quiero que siga siendo así»), y la
  presión, porque las de las vecinas no están calibradas (el 12-10-2026 a la
  misma hora marcaban de 1007 a 1019 hPa).
- Lo que marcaba la estación de casa queda en `ara_casa` como
  `…_estacio`, para comparar.
- **Lo aprendido no cambia**: los modelos propios se entrenan con la lluvia
  de casa de la hora anterior (`pluja_1h_emes`) y la variante de las vecinas
  ya añade la mediana de las vecinas (ADR 0070). El final de la lluvia
  (ADR 0049) y la comprobación del aviso de lluvia (ADR 0022) siguen con la
  lluvia de casa cada 5 minutos, porque de las vecinas solo se guarda la
  lluvia por horas.

## Alternativas descartadas

- **La mediana también para «llueve ahora»**: perdería la lluvia débil que
  ve una sola estación y llegaría tarde.
- **La humedad relativa mediana de la red**: las vecinas están en zonas más
  cálidas y darían una humedad baja para la temperatura de casa.
- **Avisar en la página de qué estación sale cada dato**: Juanjo no lo
  quiere; «D'on surt» y «Fonts» lo explican.

## Riesgos y limitaciones

- Las vecinas dan el rocío en grados enteros: la humedad tiene un margen de
  unos ±3 %.
- Con cuatro estaciones, la mediana es la media de las dos del medio: si
  llueve en dos y no en las otras dos, la lluvia es la mitad de la de las que
  la marcan.
- Sin vecinas (clave caducada, red caída) o en la reserva de IONOS, todo
  vuelve a ser de casa, como antes.

## Validación

- `tests/test_estacio_casa.py`, `test_consens_de_la_xarxa`: la mediana con el
  cero de casa, la lluvia de hoy por incrementos, la intensidad de las que
  marcan, la humedad con el rocío mediano y, sin vecinas, todo de casa.
  `tests/test_riscos.py`, `test_pluja_de_la_xarxa`. 413 pruebas en verde.
- En el NAS (13-10-2026, 06:30, con una copia del registro): rocío de 18 °C
  en las cinco estaciones y 18,3 °C en casa, humedad del 98 %; sin lluvia.
- `probar-web` con lluvia simulada, en Chromium, Firefox y WebKit, en móvil y
  escritorio, en catalán y en castellano: «Plou: 2,4 mm/h» y, sin intensidad,
  «Llueve»; sin errores propios (los únicos, de IONOS, que no deja leer los
  datos desde una web local).
