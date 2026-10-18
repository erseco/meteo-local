# 103. La cantidad de lluvia: el máximo de modelos por hora y la esperada en los totales

Fecha: 2026-10-18 · Estado: aceptado

## Contexto

La evaluación de los métodos del 18-10-2026 (informe de Codex,
`Informes/meteo-local/2026-10-18-evaluacion-metodos-prediccion.md`) decía
que los milímetros son «sistemáticamente conservadores»: en octubre, a una
hora vista, 88 mm previstos por 20 caídos, y proponía separar una cantidad
central calibrada de un escenario alto, sin cambiar el máximo por una media
sin comprobarla. Juanjo pidió hacerlo («Continua», tras la pieza 1).

## Evidencia

Con el archivo 2024-2026 (`calibracio/dades`, las dos estaciones de
Meteocat, 94.380 horas-estación) y la probabilidad validada por semanas
(`calibracio/pluja_casa.py`), en la carpeta de trabajo de la sesión, sin
tocar el repositorio:

- **Por hora, si llueve**, a corto plazo el máximo de los tres modelos da
  2,07 mm por hora de lluvia frente a 2,14 medidos (3.787 mm por 3.898 en
  1.825 horas): sin sesgo. La media de los tres se queda en 1,28 (−40 %). Una
  regresión ridge con los modelos (lineal o sobre logaritmos, ajustada en
  las horas con lluvia) baja el error absoluto de 2,10 a 1,64-1,89 mm, pero
  aplana: da 2-4 mm en las horas en que caen 19. Un día antes, el máximo se
  queda un tercio corto (1,43 por 2,15).
- **Por horas según lo que decía la página**: en las de 50 % o más que
  llovieron, el máximo se pasa un tercio (2.994 por 2.252 mm); en las de
  menos del 20 % que llovieron (605 horas, 828 mm) no da casi nada (161):
  es la lluvia que ningún modelo ve.
- **El exceso está en las sumas.** En los 426 tramos del día con paraguas
  (alguna hora con 20 % o más), sumar los milímetros de todas las horas da
  6.360 mm por 3.644 medidos, con un error medio de 10,1 mm por tramo; sumar
  solo las horas de 50 % o más, 4.026 mm y 7,5 de error; la cantidad
  esperada, probabilidad por milímetros de cada hora, 3.796 mm y 6,8 de
  error (correlación 0,67 frente a 0,64). Un día antes, la esperada da
  2.600 por 3.440 (6,6 de error frente a 9,4): corta, por la lluvia que los
  modelos no ven con esa antelación.
- **El máximo no es un escenario alto**: queda por debajo de lo medido en
  el 52 % de las horas con lluvia a corto plazo y en el 67 % un día antes.
  Con el doble, en el 36 % y el 51 %.
- En octubre (`historial`, 1 h), de los 88,7 mm previstos, 66,5 estaban en
  11 horas con 70 % o más en las que cayeron 13,7: un exceso real de unos
  pocos episodios de tormenta prevista, sobre una muestra de 12 horas de
  lluvia.

## Decisión

- **La cantidad de cada hora sigue siendo el máximo de los tres modelos
  finos** (ADR 0007): es la cantidad «si llueve», como dice la leyenda, no
  sesga a corto plazo, distingue mejor que nada el chubasco de la llovizna y
  es la única que no rebaja la lluvia fuerte. Ni la media ni una regresión
  la mejoran para lo que se usa (la intensidad de la hora, los fenómenos del
  tramo, «Si surts»).
- **El total de cada tramo y el del acierto son la cantidad esperada**: la
  probabilidad de cada hora por sus milímetros (1 en la hora en que ya
  llueve; sin probabilidad, 1 si el modelo da lluvia). En la web
  (`resumTrams`, «60 %, uns 14 mm») y en «Com encerta» («Pluja esperada:
  en preveia X mm i en van caure Y»; `historial.py`, formato 4). Es la suma
  que menos se equivoca y la única sin sesgo a corto plazo.
- **No se añade un «hasta X mm»**: el máximo de modelos no cubre lo que cae
  en la mitad de las horas con lluvia; un escenario alto de verdad exigiría
  un modelo de cuantiles que no se ha hecho. «Si surts» mantiene para el
  coche la suma de máximos en 3 horas («fins a»), decidida en el ADR 0039
  como escenario prudente frente a los umbrales de Meteocat.
- Las cifras de «Com encerta» anteriores a la 3.143.0 (la suma de los
  milímetros previstos) no son comparables con las nuevas.

## Alternativas descartadas

- **La media de los modelos por hora**: −40 % en las horas con lluvia.
- **Una regresión de la cantidad** (ridge, lineal o logarítmica): menor
  error absoluto, pero aplana los extremos y, en los totales por tramo,
  solo mejora la esperada con el máximo en un 7 % a corto plazo (9,7 frente
  a 10,4 mm por día) a cambio de dos cantidades distintas por hora, una
  mostrada y otra para sumar.
- **Un factor por antelación** (1,5 a un día): corrige el sesgo medio a
  costa de más error por hora (2,36 frente a 2,02) y de inflar la llovizna.

## Validación

- `tests/test_web.py` (`test_resum_per_trams_del_dia`: 0,8·45 + 6·0,3·2 =
  39,6 mm donde antes 57) y `tests/test_historial_grafica.py` (los mm
  esperados). 567 pruebas en verde.
- El análisis: `analisi_mm.py`, `analisi_mm2.py` y `analisi_mm3.py` en la
  carpeta de trabajo de la sesión del 18-10-2026 (no se conservan en el
  repositorio; las cifras están arriba y en `docs/estadistica.md`, 6 bis).
