# 109. La API de Meteocat, de reserva de la página de avisos

Fecha: 2026-10-19 · Estado: aceptado

## Contexto

Los avisos de peligro de Meteocat (SMP) se leen en cada pasada de la página de
predicción general de meteo.cat (`smp.py`, ADR 0067 y 0071). La página no es
una API: si cambia o no carga, la web se queda sin los avisos de Meteocat y
solo avisan los de AEMET (ADR 0092).

El 19-10-2026 el Meteocat dio de alta a Juanjo en su API (clave hasta el
31-10-2027). Se le explicó por correo que la web muestra sus avisos citándolo
y que los lee cada 15 minutos (cada 6 con riesgo), unas 3.000 consultas al
mes, y respondió subiendo el plan de 100 a 1.500 consultas al mes («et
permet fer consultes cada 30 minuts») y que avisará si puede ampliarlo.

## Decisión

- La página sigue siendo la fuente principal: se lee en cada pasada, sin
  cuota.
- Si la página falla (no carga, no trae los avisos o trae algo que no se sabe
  leer), los episodios se piden a `/pronostic/v2/smp/episodis-oberts?data=`
  (fecha de hoy), con la misma lectura (`smp.de_la_comarca`). Se consulta
  como mucho cada 30 minutos (`smp.API_CADA_MIN`): entre tanto se usa la
  última respuesta, guardada en `/estat/cache-web/smp-api.json`. Un mes de 31
  días son 1.488 consultas.
- La clave va en `~/.config/meteo-local/meteocat.env` (`METEOCAT_API_KEY`) del
  NAS, fuera del repositorio, y en la copia cifrada `claus-nas`.
- A Juanjo se le dice por Telegram cuándo cambia la situación: la página cae
  y llegan por la API («api»), no llega nada y avisan los de AEMET («cap»),
  o se vuelve a leer la página. La marca `smp-falla` guarda cuál.
- Los créditos (`web/fonts.html`) dicen que los avisos se leen de la web de
  Meteocat o, si falla, de su API.

## Alternativas descartadas

- **La API como fuente principal.** Con 1.500 consultas, los avisos se
  leerían cada 30 minutos en vez de cada 15, o cada 6 con riesgo: en un
  peligro, peor. Se vuelve a mirar si Meteocat amplía la cuota a unas 3.000.
- **Preguntar al Meteocat si se puede usar la página pública.** Descartado por
  Juanjo (19-10-2026): una negativa podría quitar lo que ya funciona.

## Consecuencias

- Una caída de la página ya no deja la web sin avisos de Meteocat; durante
  esa caída los avisos tienen hasta 30 minutos de retraso.
- La prueba diaria (`smp.comprova`) también prueba la API si falla la página.

## Evidencia

- Correo del Meteocat (Unitat de Serveis a l'Usuari i al Client) del
  19-10-2026 y `/quotes/v1/consum-actual`, que muestra el plan
  «Predicció_1500» (1.500 consultas al mes).
- El 19-10-2026 a las 17:00, con cuatro avisos vigentes para el Vallès
  Occidental, `de_la_comarca` dio exactamente lo mismo leyendo la página y la
  API (comparación de los JSON ordenados).
- La API exige el parámetro `data` (sin él, «Els paràmetres 'data' és
  necessari», 400) y solo acepta de hoy a tres días después.

## Riesgos y limitaciones

- Las condiciones de la API piden no difundir los datos a terceros; el
  Meteocat amplió la cuota sabiendo que es para mostrarlos en la web, con la
  cita de la fuente que ya lleva.
- Si fallan a la vez la página y la API, se sigue como antes (ADR 0092).

## Validación

`tests/test_smp.py`: la reserva da los mismos avisos que la página, el error
dice las dos fuentes si fallan las dos, la API no se consulta más de una vez
cada 30 minutos, una respuesta que no es la lista no se guarda, y la marca y
los mensajes a Juanjo en cada cambio de situación.
