# 105. Una sola regla de mejora: remuestreo por bloques de días o episodios

Fecha: 2026-10-19 · Estado: aceptado

## Contexto

La evaluación de los métodos del 18-10-2026 (informe de Codex,
`Informes/meteo-local/2026-10-18-evaluacion-metodos-prediccion.md`, apartado
6, hallazgo 1) decía que el criterio del 5 % no demuestra una mejora sólida:
un 5 % puede ser azar con pocos episodios y una mejora menor puede ser
consistente con muchos datos. Seguía vigente en la probabilidad de lluvia y
la temperatura (`aprenentatge.py`, `MILLORA_MINIMA`), la elección de radar
(`radar_fonts.py`), el final de la lluvia (`fi_pluja.py`) y la corrección
del aire (`aire.py`, `AIRE_MILLORA`), mientras el cielo (`nuvols.py`, ADR
0088) y la variante del archivo con avisos (ADR 0097) ya usaban remuestreo
por días. Regla de Juanjo (14-10-2026, ante el cielo con otro criterio):
«para ser coherentes y evitar problemas en el futuro no habría que hacerlo
todo…?»; y el 13-10-2026: un umbral elegido probando «no está usando ninguna
metodología estadística». El 19-10-2026 pidió seguir con este punto («sí,
sigue con el 2»).

## Decisión

- **Una sola regla, en `remostreig.py`**: el candidato sustituye al método
  en uso si se equivoca menos en al menos el **95 %** de **2.000
  remuestreos por bloques** (*bootstrap* con reposición), con los mismos
  casos para los dos. Los errores de cada caso (cuadrático, absoluto o en
  minutos) se suman por bloque y se compara la suma en cada remuestreo.
  `seguretat(errors_nou, errors_actual, blocs)` da la proporción;
  `guanya(seguretat)` decide. Con menos de dos bloques no hay seguridad.
- **El bloque es el día de la hora observada** en la lluvia, la temperatura,
  el radar, el aire y el cielo, porque las horas de un mismo día se parecen
  y no son casos independientes; en el **final de la lluvia, el episodio**,
  que es la unidad natural de esa regla (cada pasada de un episodio predice
  el mismo final). El informe pedía «bloques adecuados a la duración de los
  episodios»: en el Vallès los episodios de lluvia caben casi siempre en un
  día, y el día ya es el bloque del cielo y de la variante con avisos; usar
  dos reglas de bloque distintas sería lo que se quería evitar.
- **Lo que no cambia**: los mínimos de datos para empezar a decidir (30
  horas de lluvia, 14 días de temperatura, 30 casos de lluvia del radar en 3
  días, 3 episodios, 72 horas y 2 estaciones del aire, 300 horas en 14 días
  del cielo), la validación cruzada por semanas o dejando un episodio o un
  día fuera, la propuesta que espera un día y se puede parar (`atura`), y
  las variantes propias de la lluvia, que además de ganar al archivo tienen
  que ganar al base en sus mismas horas (`seguretat_base`).
- Cada decisión guarda su seguridad (`model.json`, `radar-font.json`,
  `fi-pluja-proposat.json`, `aire-correccio.json`, `nuvols-pesos.json`) y los
  avisos a Juanjo la dicen («guanya en el X % dels remostrejos per dies»).
- El 95 % no es la probabilidad de acertar en el futuro: dice que, con los
  datos que hay, la ventaja no se explica por el azar de qué días han caído.

## Evidencia

Con el registro del NAS copiado a la carpeta de trabajo de la sesión (del
05-10 al 19-10-2026), con el código nuevo, qué decide la regla nueva y qué
habría decidido el 5 %:

| Qué | Datos | Error nuevo / actual | Seguridad | Regla nueva | Regla del 5 % |
|---|---|---|---|---|---|
| Probabilidad de lluvia, modelo local | 5.880 muestras, 12 h de lluvia | 0,0792 / 0,0428 | 0,1 % | no | no |
| · con Sant Cugat (vs base) | 12 h | 0,0759 / 0,0759 | 79 % | no | no |
| · con los avisos (vs base) | 8 h | 0,0358 / 0,0351 | 8 % | no | no |
| · con las vecinas (vs base) | 12 h | 0,0763 / 0,0763 | 70 % | no | no |
| Temperatura, corrección propia | 14 días | 1,07 / 0,96 °C | 10 % | no | no |
| Radar: RainViewer vs Meteocat | 6.048 pares, 236 con lluvia, 5 días | 0,0266 / 0,0328 | 97,7 % | se queda RainViewer | se queda |
| Final de la lluvia: 30 % durante 10 min vs 20 % durante 15 | 40 casos, 5 episodios | 40,6 / 48,1 min | 96,5 % | sí (propuesta del 18-10) | sí (−16 %) |
| Aire, NO₂, factor 0,65 | 653 h, 30 días | 7,8 / 13,9 µg/m³ | 100 % | sí | sí |
| Aire, O₃, factor 0,71 | 651 h | 14,7 / 17,6 | 99,8 % | sí | sí |
| Cielo, pesos ajustados vs iguales | 131 h, 7 días | 32,5 / 30,5 puntos | 0,4 % | no | — |

Hoy las dos reglas deciden lo mismo en todo. La diferencia está en lo que
exigen: el final de la lluvia gana por episodios en el 96,5 %, cerca del
límite, porque de los 5 episodios pierde en el más largo (21 de los 40
casos, 37,4 frente a 36,0 minutos) y gana en los otros; el 5 % lo daba por
bueno de sobra (−16 %). El radar, con un 19 % menos de error, gana en el
97,7 % de los remuestreos: 5 días de lluvia pesan.

## Alternativas descartadas

- **Mantener el 5 % y añadir el remuestreo como segunda condición**: dos
  reglas en vez de una, y el 5 % no tiene base estadística.
- **Bloques de varios días o de episodios de lluvia en la probabilidad**:
  más fieles a la duración de un episodio, pero exigirían definir episodios
  en series con huecos y dejarían el cielo y los avisos con otro bloque. Si
  algún día un episodio largo cruza días, el remuestreo por días lo contará
  como dos bloques parecidos: la seguridad saldrá algo alta. Queda como
  hipótesis a revisar con los primeros episodios de varios días.
- **Un intervalo de confianza del error** en vez de la proporción de
  remuestreos: dice lo mismo con más cifras que explicar.

## Pendiente

- Hallazgo 3 del informe: validación con avance temporal (entrenar hasta una
  fecha y evaluar después) y episodios que no crucen el límite de una semana.
- `historial.csv` del aprendizaje no guarda la seguridad (añadir una columna
  obligaría a rehacer el archivo); está en `model.json` y en los avisos.

## Validación

- `tests/test_remostreig.py` (gana siempre y nunca; una mejora grande en un
  solo día no es segura y la misma hora a hora sí lo sería, por eso los
  bloques; una pequeña y constante sí; sin dos bloques no hay seguridad).
  `tests/test_aprenentatge.py`, `tests/test_radar_fonts.py`,
  `tests/test_aire.py`, `tests/test_consultes.py` y `tests/test_nuvols.py`
  adaptados; 571 pruebas en verde.
- La medida de arriba, con el código nuevo y los datos del NAS, en la
  carpeta de trabajo de la sesión del 19-10-2026.
