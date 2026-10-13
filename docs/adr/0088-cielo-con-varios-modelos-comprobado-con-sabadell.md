# 88. El cielo, con varios modelos y comprobado con el aeropuerto de Sabadell

Fecha: 2026-10-13 · Estado: aceptado

## Contexto

El 13-10-2026, a las 16:43, la tabla decía «Serè» de 16 a 19 h y Juanjo veía
más de la mitad del cielo tapado. Preguntó si el cielo se calibraba o «sale lo
que sale sin mirar nunca si acierta». No se calibraba: era la nubosidad de un
solo modelo, AROME (`cloud_cover` de `meteofrance_seamless`), y nunca se
comparaba con nada. Las nubes de AROME saltan de una hora a otra. Esa tarde,
para casa, daba un 100 % a las 16 h, un 14 % a las 17 h y un 0 % a las 18 h.
ICON-EU daba entre el 68 y el 89 % y GFS, el 100 %. El aeropuerto de Sabadell
observaba «FEW020 BKN030 BKN040», entre 5 y 7 octavos tapados.

La estación de casa no sirve para medir las nubes con la radiación: en días
de sol su máximo ronda los 150 W/m², cuando a pleno sol en octubre serían
unos 550-600. El sensor queda a la sombra parte del día.

Juanjo pidió (13-10-2026) usar varios modelos ya y que el cielo aprenda con
lo observado en el aeropuerto de Sabadell, y que en la hora en curso mande lo
observado.

## Decisión

- **El cielo de cada hora es la media ponderada de cuatro modelos**: AROME
  (`meteofrance_seamless`), ICON-EU, ECMWF IFS y GFS (`nuvols.py`, `MODELS`).
  ECMWF y GFS llegan en una petición aparte a Open-Meteo cada uno; si falla
  uno, el cielo sale de los demás (desde la 3.81.1: el mismo día de
  publicarlo, Open-Meteo, sobrecargado, rechazaba ECMWF y no siempre GFS). Se empieza con los cuatro al 25 %.
- **La observación es el METAR del aeropuerto de Sabadell** (LELL, a unos
  7 km), cada media hora, día y noche. Se lee del servicio público de la
  NOAA (aviationweather.gov, en JSON) y da cuánto tapa cada capa, en octavos.
  El cielo tapado es el de la capa que más tapa, en el punto medio de su
  intervalo: FEW 19 %, SCT 44 %, BKN 75 %, OVC 100 %. Si el servicio da un
  error, se reintenta una vez.
- **En la hora en curso manda lo observado**, si el último METAR tiene 45
  minutos o menos y da capas de nubes. Si no da capas (CAVOK, NSC, NCD), no
  se usa: solo dice que no hay nubes por debajo de unos 1.500 m.
- **Se registra todo.** Lo observado, por horas, en `registre/nuvols-sabadell.csv`
  (el %, si había capas y los METAR). Lo que daba cada modelo, todas sus
  nubes y las bajas, va en el registro de la previsión (`nuvols_<modelo>` y
  `nuvols_baixos_<modelo>` en `casa-AAAA-MM.jsonl`).
- **Cada día, en `aprenentatge.diari`, se busca la mezcla que menos se
  equivoca** en los últimos 30 días. Se prueban todos los pesos múltiplos de
  0,1 que suman 1. Las horas con capas se comparan con todas las nubes de la
  mezcla; las horas sin capas, con sus nubes bajas, que tendrían que ser cero.
  Como el radar (ADR 0026), solo cambia con bastantes datos (300 horas
  observadas en 14 días) y si la mezcla nueva se equivoca al menos un 5 %
  menos, salvo que exista `aprenentatge/atura`. Los pesos se guardan en
  `aprenentatge/nuvols-pesos.json`, se usan en la pasada siguiente y se
  avisa a Juanjo por Telegram.
- **La página lo explica** en «D'on surt», en «Com funciona», en «Fonts i
  crèdits» y, desde la 3.81.2, en «Com es llegeix la previsió»: qué parte del
  cielo tapa cada nombre, cuándo sale la lluvia en su lugar y que la hora en
  curso es lo observado en Sabadell (Juanjo, 13-10-2026: «no hay nada sobre
  el cel»).
- **Si deja de llegar el METAR**, la página sigue con los modelos. La
  comparación diaria avisa a Juanjo si hace más de un día que no se apunta
  ninguna hora.

## Alternativas descartadas

- **Seguir solo con AROME**: es el que más se equivoca de los cuatro con las
  nubes (Evidencia).
- **Medir las nubes con la radiación de la estación de casa**: el sensor
  queda a la sombra.
- **Radiación del satélite o de una estación de Meteocat**: solo valen de
  día y dan una estimación, no una observación de las nubes. Juanjo eligió
  Sabadell para las dos cosas.
- **Contar las horas sin capas como cielo despejado**: con CAVOK o NSC puede
  haber nubes altas. Contadas como 0 %, todos los modelos parecen equivocarse
  unos 40 puntos de cielo tapado.
- **Corregir el sesgo de los modelos con el METAR**: los modelos dan, de
  media, más nubes de las que observa Sabadell, también en las horas con capas
  (de 19 a 32 puntos). Parte puede ser de nubes altas que el METAR no recoge.
  Una corrección aprendida así podría quitar nubes que sí hay. Solo se aprenden
  los pesos.

## Consecuencias

- El cielo cambia menos de una hora a otra y sale menos «Serè» con nubes de
  verdad: en los 17 días de la Evidencia, AROME dio «Serè» 12 horas en que
  Sabadell observaba la mitad del cielo tapado o más; la media de los cuatro,
  ninguna.
- La media también suaviza los extremos: «Serè» y «Cobert» salen menos.
- Dos peticiones más a Open-Meteo por pasada y una a aviationweather.gov.
  Unos 4 KB más por línea del registro de la previsión.
- El bot de Telegram y la tarjeta de «Ara» usan el mismo dato (`nuvols` de
  cada hora): cambian igual.

## Evidencia

- Prueba con el archivo, repetible: METAR de LELL del 27-09 al 13-10-2026
  (aviationweather.gov, unos 800 informes) contra la previsión archivada de
  Open-Meteo (`historical-forecast-api`, los cuatro modelos) para las
  coordenadas de casa: 378 horas en 17 días, 246 con capas y 132 sin capas.
- Error medio, en puntos de cielo tapado, con la comparación de la Decisión:
  AROME 28,8; ICON-EU 29,7; ECMWF 27,0; GFS 29,3. Media de los cuatro, 25,8.
  La mejor mezcla posible (AROME 0,3, ICON-EU 0,1, ECMWF 0,4, GFS 0,2), 25,7:
  empezar con todos iguales es casi lo mejor.
- Si las horas sin capas contaran como despejadas: AROME 44,7, ICON-EU 40,7,
  ECMWF 37,9, GFS 43,2. En esas horas los modelos daban de media entre un 44
  y un 54 % de cielo tapado, sobre todo nubes medias y altas.
- La previsión archivada es la de las primeras horas de cada pasada del
  modelo; la de la página llega a 45 horas. Hipótesis pendiente: que a más
  antelación la mezcla también acierte más que AROME. Lo dirá el registro.

## Riesgos y limitaciones

- Sabadell está a unos 7 km; con niebla o nubes bajas
  locales el cielo puede ser otro en Montflorit.
- El METAR no siempre recoge las nubes altas. Por eso, en las horas sin capas,
  la comparación no castiga las nubes medias y altas de los modelos, y el
  aprendizaje no puede saber si las hay de verdad.
- El tanto por ciento observado es aproximado: la capa que más tapa, en el
  punto medio de su intervalo de octavos.
- aviationweather.gov es un servicio público documentado de la NOAA, sin
  clave. Si cambia su formato, `nuvols.llegeix` falla y la página sigue con
  los modelos; el aviso diario lo dice.

## Validación

- Pruebas: `tests/test_nuvols.py` (lectura del METAR, horas, observación de
  ahora, mezcla, comparación diaria y aviso sin observaciones).
- En local, el 13-10-2026 a las 16:52, la hora de 16 a 17 pasó de «Serè»
  (AROME, 14 %) a 75 % observado, «Molt ennuvolat»; las siguientes, a la media
  de los cuatro (45 y 48 %).
