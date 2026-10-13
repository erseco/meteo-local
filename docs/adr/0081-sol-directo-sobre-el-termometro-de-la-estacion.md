# 81. Sol directo sobre el termómetro de la estación

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

Juanjo preguntó si, cuando a su estación le da el sol y sube mucho, se corrige
con las estaciones cercanas: «mi estación está en una zona del barrio
normalmente más fría que el resto y quiero que siga siendo así, pero en el caso
de que dé el sol se podría sacar de las otras?». Y luego: «¿no se puede mirar
directamente la radiación en lugar de suponer?», y que el pico «va variando con
el sol», a veces también por la tarde.

Con las lecturas cada 5 minutos de Ecowitt (9 al 12-10-2026), las mañanas
soleadas la estación sube de 3 a 5 °C entre las 8:35 y las 9:05 y luego baja
un poco, mientras las vecinas suben poco a poco (el 9: 9,2 °C a las 8:30, 14,7
a las 9:05; vecinas, 10,5 a las 9). Los días nublados (5 y 7) no pasa. El
resto del día, la estación marca alrededor de 1 °C menos que la mediana de las
vecinas.

El sensor de radiación no lo ve: durante el salto marca de 20 a 37 W/m², lo
mismo que a las 9:45 o 10:00 sin pico, y mucho menos que los 100 W/m² del 11 a
las 10:30, también sin pico.

## Decisión

Versión 3.72.0. `sol_estacio.py`:

- **Se detecta por el salto de la estación, no por la hora ni por la
  radiación**, para que valga a cualquier hora y en cualquier época:
  - empieza, de día (radiación > 0), si la estación ha subido 1,5 °C o más en
    los últimos 30 minutos y está 1,5 °C o más por encima de lo esperado;
  - sigue mientras esté 0,7 °C o más por encima, de día y como mucho 3 horas.
- **Lo esperado**: la mediana de las vecinas de Weather Underground leídas en
  los últimos 30 minutos (al menos dos) más la **diferencia habitual** de la
  estación, la mediana de (casa − vecinas) en las horas en punto de los últimos
  30 días, sin las horas con sol directo. Así la zona más fría se conserva.
- **Mientras dura**, «Ara» muestra la temperatura esperada, sin nota: en la
  3.72.1 se quitó la que decía «Estimada: el sol toca l'estació» (Juanjo:
  «quita lo de que está dando el sol... esos detalles no interesan a la
  gente»); el método sigue explicado en «D'on surt». La
  **humedad relativa** también se corrige: se recalcula con el punto de rocío
  medido, que el sol no cambia, y la temperatura esperada (Juanjo: «si lo ves
  conveniente aplica lo mismo al resto de mediciones»). La presión y la lluvia
  no las toca el sol.
- **No se aprende de esas horas**: cada episodio se apunta en
  `registre/sol-estacio.csv`, y sus horas no cuentan para la corrección de la
  temperatura de la previsión (`aprenentatge.mostres`).
- **Para comparar con ayer llevan la temperatura esperada** (versión 3.75.4;
  `sol_estacio.amb_esperades`, desde `registre.temperatures_casa` y
  `casa.py`), la misma cuenta que «Ara». Hasta la 3.75.3 se quitaban, y como
  la comparación de un tramo necesita todas sus horas, la mañana de los días
  de sol se quedaba sin «graus més o menys que ahir». Juanjo (13-10-2026):
  «no es que no haya datos, solo no hay datos de mi estación». Si en esa hora
  no hay dos vecinas o no hay diferencia habitual, la hora se quita, como
  antes.
- `python3 sol_estacio.py omple [DIES]` repasa el historial cada 5 minutos y
  apunta los episodios pasados (donde hay vecinas por horas).
- La subida a Weather Underground (ADR 0059) sigue con lo que mide la
  estación: es una medida, no una estimación.

## Alternativas descartadas

- **Por la radiación**: no lo ve (arriba).
- **Por la hora** (8:30–9:30): cambia con la época, y en verano o invierno
  también hay tardes (Juanjo).
- **Sustituir la temperatura por la de las vecinas sin más**: perdería la
  zona más fría de la estación.

## Consecuencias

- «Ara» no enseña los picos de sol, y lo que se aprende de la estación queda
  limpio.
- Si las vecinas no se pueden leer, o hay menos de 24 horas comparables, no
  se corrige (como hasta ahora).

## Riesgos y limitaciones

- Un cambio de tiempo real muy brusco de día (una entrada de aire cálido)
  podría parecer un pico; para eso se exige también estar por encima de las
  vecinas.
- Mejor aún sería que el sol no llegara al termómetro (una sombra o un
  protector de radiación): la corrección es una red de seguridad.
- Sin 24 horas comparables o sin dos vecinas leídas en la última media hora,
  no se corrige; la reserva de IONOS tampoco corrige (no tiene el registro de
  la estación ni el de las vecinas).
- La diferencia habitual es una para todo el día, pero cambia con la hora: del
  9 al 12-10-2026, de −0,5 a −0,9 °C de 8 a 10 h y hasta −2,7 °C por la tarde
  (mediana −1,2 °C). A primera hora la temperatura esperada puede quedar unos
  0,5 °C baja. Hipótesis pendiente: con un mes de datos (desde el
  09-11-2026), decidir si se calcula por franjas horarias.

## Validación

- `tests/test_sol_estacio.py`: el salto del 9 de octubre se detecta, sigue y
  acaba; sin salto, de noche, sin diferencia habitual o con una sola vecina, no
  se decide; la diferencia habitual sin las horas de sol; la humedad con el
  punto de rocío; apuntar y alargar un episodio. 407 pruebas en verde.
- 3.75.4: `test_les_hores_de_sol_amb_la_temperatura_esperada` (la hora de sol
  con la esperada; con una sola vecina o sin diferencia habitual, fuera). Con
  el registro del NAS del 12-10-2026 (diferencia habitual −1,1 °C), las 9 h
  pasan a 12,9 °C (vecinas 14, 14, 14 y 15) y las 10 h a 14,9 °C (16, 15, 16 y
  16). 412 pruebas en verde.
