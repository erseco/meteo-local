# 106. Validación con avance temporal: cada día se evalúa con el modelo de los días anteriores

Fecha: 2026-10-19 · Estado: aceptado

## Contexto

La evaluación de los métodos del 18-10-2026 (informe de Codex,
`Informes/meteo-local/2026-10-18-evaluacion-metodos-prediccion.md`, apartado
6, hallazgo 3) decía que separar semanas es valioso pero no reproduce una
actualización en el tiempo: la validación cruzada en cuatro grupos de semanas
(`aprenentatge.grupo_semana`, `nuvols.grup_setmana`) podía ajustar con
semanas posteriores a la evaluada. Pedía complementarla con entrenamiento
hasta una fecha y evaluación en días posteriores, repitiendo el avance (la
lógica de `TimeSeriesSplit` de scikit-learn), y separar los episodios que
cruzan el límite de un bloque. Juanjo pidió seguir con este punto («sigue con
el 3», 19-10-2026), tras el competidor (ADR 0104) y la regla de mejora (ADR
0105).

## Decisión

- **La validación del aprendizaje es con avance temporal**
  (`remostreig.avanc`): para cada día del registro con al menos
  `MIN_DIES_ENTRENAMENT = 7` días anteriores, el modelo se ajusta con los
  días anteriores y predice ese día. Los errores se miden en los días
  evaluados, para el candidato y para el competidor por igual (lo que publica
  la web, ADR 0104), y la decisión sigue la regla común (ADR 0105:
  remuestreo por días de los errores evaluados). Es lo que hace el programa:
  reajustarse cada día y aplicarse a los siguientes.
- **No sustituye a la validación por semanas con una segunda regla: la
  reemplaza** en la probabilidad de lluvia y sus variantes (`valida_pluja`,
  `valida_variant`), la temperatura (`valida_temperatura`) y el cielo
  (`nuvols.compara`). Una sola forma de validar en el aprendizaje diario.
- **Los episodios de lluvia que cruzan la medianoche** se apartan del ajuste
  del día que evalúa su parte final (`remostreig.episodis`: horas observadas
  con lluvia separadas por `EPISODI_BUIT_H = 6` horas secas o menos). Si no,
  el modelo habría visto el mismo episodio unas horas antes y saldría mejor
  de lo que es. Solo en la lluvia: la temperatura y el cielo no tienen
  episodios.
- **Siete días mínimos de ajuste**, la misma unidad que las semanas de antes
  y el periodo en que el modelo de la lluvia tiene alguna hora de lluvia que
  aprender en otoño; los siete primeros días del registro solo sirven para
  ajustar. `valida_*` devuelve `avaluades`, `dies_avaluats` y, en la lluvia,
  `hores_pluja_avaluades`; sin días que evaluar, `None`.
- **El archivo 2024-2026 (`calibracio/`) sigue con la validación cruzada por
  semanas**: son análisis de dos años con 3.600 horas de lluvia, donde
  importa la relación estadística y los grupos de semanas cubren todas las
  estaciones del año. Lo que decide a diario sobre el registro propio es lo
  que tiene que reproducir el uso real.
- La selección del radar (dos fuentes fijas, sin ajuste), el final de la
  lluvia (dejando un episodio fuera) y el aire (dejando un día fuera) no
  ajustan coeficientes en el tiempo y no cambian.

## Evidencia

Con el registro del NAS copiado a la carpeta de trabajo de la sesión (del
05-10 al 19-10-2026, 14 días, 12 horas de lluvia en 3 episodios: 6-7/10 de
21 a 00 h, el único que cruza la medianoche; 8/10 a las 20 h; 18/10 de 2 a
13 h), antes de cambiar el código:

| Validación | Evaluado | Brier candidato / web | Seguridad |
|---|---|---|---|
| Cruzada por semanas (hasta ahora) | 5.880 muestras, 12 h de lluvia | 0,0792 / 0,0428 | 0,1 % |
| Avance temporal, 5 días mínimos | 4.671 muestras, 9 días, 7 h de lluvia | 0,0777 / 0,0407 | 2,1 % |
| Avance temporal, 7 días mínimos | 3.528 muestras, 7 días, 7 h de lluvia | 0,1028 / 0,0539 | 2,1 % |

Temperatura: por semanas, 1,07 frente a 0,96 °C (seguridad 10 %); con
avance de 7 días, 1,14 frente a 1,10 °C en 7 días evaluados (39 %). Cielo: 7
días con METAR de Sabadell en los últimos 30, así que con avance temporal no
hay todavía ningún día evaluable (hace falta el octavo) y se quedan los pesos
iguales, como con las semanas (seguridad 0,4 %). Apartar
el episodio del 6-7/10 no cambió ninguna cifra: es el primer día evaluable y
solo aporta una hora al día 7. La decisión de hoy es la misma (sigue el
archivo), con menos muestras evaluadas, que es el precio de no mirar el
futuro.

## Riesgos

- Con avance temporal se evalúa menos (los primeros siete días nunca), así
  que un modelo propio tardará algo más en poder entrar. Es lo honesto: lo
  que se evalúa es lo que el programa habría publicado.
- Con 7 días evaluados el remuestreo por días es grueso (ADR 0105); el
  mínimo de 30 horas de lluvia sigue vigente para decidir.
- `remostreig.avanc` reajusta un modelo por día evaluado: con un año de
  registro serán 360 ajustes diarios de regresión logística, segundos en el
  NAS.

## Validación

- `tests/test_remostreig.py` (`Avanc`: los siete primeros días solo
  entrenan, nunca entra nada posterior al día evaluado, y la hora de las 23
  de un episodio que cruza la medianoche queda fuera del ajuste del día
  siguiente); `tests/test_aprenentatge.py` (días evaluados, muestras y horas
  de lluvia evaluadas; el competidor medido en las mismas muestras
  evaluadas; `None` con menos de ocho días). 574 pruebas en verde.
- La medida de arriba, en la carpeta de trabajo de la sesión del
  19-10-2026, y repetida con el código nuevo (mismas cifras).
