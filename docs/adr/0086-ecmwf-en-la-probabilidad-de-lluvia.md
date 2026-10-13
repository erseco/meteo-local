# 86. ECMWF en la probabilidad de lluvia

Fecha: 2026-10-13 · Estado: aceptado

**13-10-2026 (ADR 0088).** ECMWF IFS entra también en el cielo, como uno de los cuatro modelos que se mezclan.

## Contexto

La probabilidad de lluvia sale de una regresión logística con la lluvia de
AROME HD, AROME e ICON-EU (ADR 0021). Los modelos globales (ECMWF, GFS, UKMO)
se descartaron al principio porque sus celdas de unos 25 km incluían mar (ADR
0001). El 13-10-2026, comprobado en Open-Meteo, ECMWF IFS ya está en abierto a
unos 9 km, con la celda que toca al barrio tierra adentro. Juanjo pidió
probarlo («prueba ecmwf») y, con el resultado delante, «hazlo así».

## Evidencia

Previsiones archivadas de ECMWF IFS de 9 km en casa (Previous Runs API de
Open-Meteo, `calibracio/ecmwf_descarrega.py`) contra la lluvia de Sabadell y
Sant Cugat, con la validación de siempre: cuatro grupos de semanas, cada uno
juzgado por un modelo ajustado sin él, y las mismas muestras con ECMWF y sin
él (`calibracio/ecmwf_prova.py` y `calibracio/pluja_casa_ecmwf.py`):

- **A corto plazo** (todo el archivo, 2024-2026; 47.676 muestras, 1.825 con
  lluvia): error de Brier de 0,02252 a 0,02195, un **2,5 %** menos; positivo
  en los cuatro grupos (+3,2, +2,1, +2,9 y +1,9 %).
- **Un día antes** (solo desde el 01-10-2025, cuando ECMWF abrió los datos de
  9 km; 17.712 muestras, 692 con lluvia): de 0,02726 a 0,02575, un **5,5 %**
  menos; positivo en los cuatro grupos (+5,0, +7,4, +4,2 y +4,1 %).
- Con la lluvia de casa (octubre de 2025 a julio de 2026, 289 horas con
  lluvia), ajustado aparte por antelación: +1,6 % a corto plazo y +4,8 % un
  día antes.
- Cuando AROME e ICON-EU no coinciden, también mejora (+2,0 % a corto plazo y
  +2,7 % un día antes, con el archivo).

## Decisión

Versión 3.77.0.

- **ECMWF como un modelo más en la probabilidad**, con las señales de los
  otros (`aprenentatge.RASGOS_ECMWF`): $`\ln(1 + \text{mm})`$, si da lluvia
  (0,1 mm o más), la cantidad por la antelación, si la dan los cuatro y si
  solo la da él.
- **Un modelo del archivo aparte**, `calibracio/pluja_casa_ecmwf.json`,
  ajustado con las horas que tienen ECMWF: las de corto plazo de todo el
  archivo y las de un día antes desde octubre de 2025. Mientras manda el
  modelo del archivo, `prob_pluja` usa este si la pasada tiene ECMWF; si no,
  el de siempre (`pluja_casa.json`), que no cambia.
- **Una consulta aparte a Open-Meteo** (`casa.modelos`): si falla, la
  probabilidad sale sin ECMWF y la página no dice nada.
- **No entra en los milímetros** de la tabla, que siguen siendo el máximo de
  los tres modelos finos, ni en la temperatura, el cielo o el viento.
- Su lluvia se guarda en el registro de cada pasada (`pluja_ecmwf_ifs`), para
  que los modelos propios puedan usarla más adelante.
- Créditos: «Fonts i crèdits», «Com funciona» y «D'on surt».

## Alternativas descartadas

- **Entrenarlo solo en el NAS** y adoptarlo cuando ganara un 5 % con los
  datos propios: habría tardado meses, porque hace falta que llueva, y la
  evidencia del archivo ya cubre un año a un día vista.
- **Sustituir los pesos del modelo de siempre**: el periodo 2024-2025 no tiene
  ECMWF de 9 km a un día vista, y sin ECMWF en una pasada la página se
  quedaría sin modelo ajustado.
- **ECMWF de 25 km o el de IA (AIFS)**: celda con mar.

## Riesgos y limitaciones

- A un día vista, un solo año de datos.
- En ese año, a un día vista, los dos modelos se pasan en el tramo del 59 %
  (llovió el 49 % con ECMWF y el 51 % sin él, con validación cruzada), y con
  ECMWF el tramo del 24 % se queda corto (llovió el 32 %, sin él el 27 %). El
  error total baja igualmente.
- ECMWF publica cuatro pasadas al día: a corto plazo va más desfasado que
  AROME, y por eso aporta poco ahí.
- No se ha podido confirmar de qué fuente salen los datos de 9 km a corto plazo
  anteriores a octubre de 2025 en el archivo de Open-Meteo.
- Los modelos propios del NAS se siguen comparando con el modelo del archivo
  sin ECMWF hasta que el registro tenga bastantes horas con su lluvia.
- La celda de ECMWF está a unos 6,5 km del barrio.

## Validación

- axe-core sin errores en «Fonts i crèdits», «Com funciona» y la portada, en catalán y castellano.
- `tests/test_aprenentatge.py`, `test_ecmwf_com_un_model_mes`: las señales,
  el modelo con ECMWF solo si la pasada lo tiene, el modelo guardado mejora al
  menos un 5 % a un día vista y, con un modelo propio, no cambia nada.
  `tests/test_casa_fonts.py`: sin ECMWF (o vacío), la previsión sigue. 414
  pruebas en verde.
- En el NAS (13-10-2026, con una copia del registro): ECMWF se lee y la
  probabilidad cambia en 33 de 38 horas; de 14 a 17 h, donde ECMWF da algo de
  lluvia y los otros no, sube del 1 % al 5-6 %.
