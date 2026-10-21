# 116. Las nubes y la presión en la gráfica, la presión llevada a la estación

Fecha: 2026-10-21 · Estado: aceptado

## Contexto

Tras la humedad y el UV (ADR 0114), Juanjo preguntó si se podía poner en la
gráfica «el % de cobertura de nubes». El dato ya estaba en cada hora: el
cielo tapado con el que se elige el icono (mezcla de modelos y, en la hora
en curso, lo que observa el aeropuerto de Sabadell; ADR 0088). El agente
propuso un interruptor «Núvols» con una barra gris por hora en escala fija
de 0 a 100 %, y Juanjo: «sí, hazlo y enséñamelo». Al verlo pidió que se
dijera que es el porcentaje de cielo tapado («decide tú»), y preguntó si
era fácil añadir la presión. El agente propuso la presión de AROME llevada
a la estación de casa, apagada por defecto; Juanjo: «sí, hazlo y
enséñamelo», y después «publica».

## Decisión

- **Dos interruptores nuevos, «Pressió» y «Núvols»**, entre la humedad y el
  UV, apagados por defecto y recordados con los demás (`meteo.grafica.3`:
  las claves nuevas faltan y valen «no»). Cada uno solo sale si los datos
  lo traen.
- **Las nubes, una barra gris por hora en escala fija de 0 a 100 %**: un
  30 % se ve igual de bajo cada día. El rótulo de la franja dice «Cel tapat
  pels núvols, 100 %» y la ficha de la hora, «Cel tapat: 60 %», porque en
  el móvil no hay ratón para leer la descripción del interruptor. El valor
  es el mismo que elige el icono (`nuvolsHora`: con lluvia, 50 % como
  mínimo), para que la barra no diga poco bajo un icono de lluvia.
- **La presión, una línea verde azulada en su franja**, al nivel del mar
  como la de la estación. La escala se ajusta a las horas de la gráfica: el
  hPa entero de encima de la máxima arriba, la mínima a un tercio de la
  altura para no tapar la cifra de abajo, y 6 hPa como mínimo para que un
  día quieto no parezca un cambio brusco. La ficha dice «Pressió: 1023 hPa».
- **La presión, llevada a la estación de casa** (`casa.desviacio_pressio`,
  `casa.pressio_hora`): toda la curva se desplaza lo que la estación marca
  de más sobre AROME en este momento. Cada tramo es la media del principio y
  el final, como la temperatura. Sin lectura de casa (las vecinas no tienen
  la presión calibrada) o con una diferencia de más de 5 hPa
  (`DESVIACIO_PRESSIO_MAX`, una lectura mala), la del modelo tal cual.
- `pressure_msl` se pide en la misma consulta de Open-Meteo de siempre: no
  añade ninguna petición.

## Alternativas descartadas

- **Las nubes bajas aparte**: el dato está, pero para saber si hará sol
  basta con cuánto cielo queda tapado.
- **La presión del modelo sin tocar**: 1,3 hPa por debajo de la estación, y
  la gráfica contradiría al recuadro «Ara» (ADR 0101).
- **Una corrección aprendida**: la diferencia es casi constante y la del
  momento ya deja el error en 0,5 hPa; aprender no tiene margen que ganar.
- **Escala fija de presión** (por ejemplo, 990-1040 hPa): la línea saldría
  plana casi siempre.

## Consecuencias

- En el móvil, los controles de la gráfica en grande ocupan tres filas.
- El JSON lleva un campo más por hora (`pressio`).
- La previsión de la presión se apoya en la estación de casa: si se
  descalibra, la curva se desplaza con ella.

## Evidencia

Presión de la estación de casa (registro del NAS, del 04 al 21-10-2026,
420 horas) contra `pressure_msl` de AROME (`meteofrance_seamless`, API
Previous Runs de Open-Meteo): la estación marca 1,33 hPa más de media
(desviación 0,53; entre −0,3 y 3,2). Con la previsión del día anterior, el
error medio del modelo es de 1,2 hPa; desplazándola con la diferencia de la
hora de partida, 0,48 a 1 hora, 0,52 a 6, 0,55 a 24 y 0,63 a 36 horas.

Validación: pruebas (`tests/test_pressio_hora.py`), Ruff y ESLint;
`probar-web` en Chromium, Firefox y WebKit, en escritorio y móvil, claro y
oscuro, en catalán y castellano, con las franjas encendidas; axe-core sin
incidencias en la portada y en la gráfica en grande, en los dos temas y los
dos idiomas. Los datos de la prueba, con la presión calculada por el código
nuevo sobre la previsión publicada, porque la versión anterior no la
descargaba.
