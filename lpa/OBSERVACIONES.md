# Observaciones, fuentes y aprendizaje local

La interfaz tiene una página **Estaciones**, disponible en `es/observaciones.html`.
Muestra la hora real de cada lectura, su proveedor, zona y estado. Los datos
caducados no se presentan como el tiempo actual. Los errores de las fuentes no
se convierten en ceros ni en ausencia de lluvia.

## Fuentes integradas

- **AEMET — C659M, Plaza de la Feria:** referencia de costa urbana, 15 m.
- **AEMET — C658X, Tafira:** referencia diferenciada, 269 m.
- **METAR GCLP — aeropuerto:** observaciones de NOAA Aviation Weather Center.
  Se convierten nudos a km/h y se conserva el parte original. No se inventa
  precipitación a partir de la ausencia de fenómenos en el METAR.
- **Red escolar del CEP Gran Canaria Noroeste:** catálogo de 14 estaciones
  enlazadas a Weathercloud. Se intentan consultar sus datos públicos como invitado.
  Un centro incluido en el mapa no equivale a una estación activa: los registros
  que llevan meses o años sin renovarse se señalan como antiguos.
- **Weathercloud, Las Palmas GC Arenales:** estación particular urbana, ID
  `2199568870`, 30 m. Se consulta como invitado con el mismo control de unidades.
- **Weather Underground, MONTAÑETA2:** estación particular `ILASPA64`, La
  Montañeta, 309 m. Se leen muestras agregadas de cinco minutos incluidas en el
  JSON de la página pública, u observaciones actuales cuando están presentes.
  Se comprueba el bloque de unidades (`metric`, `metric_si` o `imperial`),
  convirtiendo °F a °C, mph a km/h o m/s a km/h cuando corresponde. Se descartan
  muestras con `qcStatus=-1` y se conservan los otros estados del proveedor.
  No se confunden extremos o medias del día con condiciones actuales. La presión
  y la lluvia se omiten porque el bloque consultado no permite asegurar las
  magnitudes adecuadas. No se extraen ni se utilizan las claves embebidas de WU.
  Una página pública sin muestras utilizables puede variar según el servidor
  desde el que se consulta: se marca como no disponible, sin sustituirla por un
  resumen diario ni por otra estación. La primera ejecución en Actions no obtuvo
  muestras de WU aunque sí se pudieron descargar desde el entorno local.
- **GRAFCAN, La Isleta:** Geonica METEODATA-3016CP `3705`, identificador
  interno `thing=14`, a 6 m. Son dos identificadores de la misma estación.
  Se reutilizan seis consultas de lectura del panel público para temperatura,
  humedad, viento medio, viento máximo, dirección y presión. Los filtros de
  calidad del panel se conservan. La presión no se etiqueta como reducida al
  nivel del mar sin metadatos que lo confirmen. La lluvia queda pendiente de
  contrastar con la API: el panel transforma ciertos datos inválidos o ausentes
  en ceros y no queremos presentar esos ceros como medidas.

La comprobación inicial del 20 de octubre de 2026 obtuvo lecturas recientes en
las dos estaciones de AEMET, el aeropuerto, **IES Villa de Firgas** y **CEIP Agaete
Pepe Dámaso**. La disponibilidad cambia; la web calcula el estado de cada lectura.

### Contratos y límites

AEMET se consulta mediante el XML público utilizado por su propia web:
`/es/api-eltiempo/udat/tablas-graficas/horario/9/<indicativo>`. Se leen los
atributos UTC, no los atributos `local`, y se comprueba la identidad de la estación.
El XML lleva su codificación declarada y campos vacíos que se conservan como
valores ausentes. Esta vía no requiere clave y puede cambiar; un fallo queda
identificado. No se confunde con el contrato documentado de AEMET OpenData.

Weathercloud declara que no ofrece API pública de descarga. El adaptador usa
únicamente el endpoint GET de la vista pública de invitado, sin iniciar sesión,
sin claves privadas y sin guardar cookies ni tokens. Comprueba las unidades de
la página antes de interpretar los valores. Es un acceso **no documentado** y de
mejor esfuerzo; si cambia, la fuente se marca como no disponible. No se extraen
imágenes mediante OCR ni se usan extremos diarios como observaciones actuales.

Las estaciones conservan sus datos por separado. La presión en la estación de
AEMET no se mezcla con la presión reducida al nivel del mar. Las acumulaciones
horarias de lluvia no se mezclan con intensidades en mm/h. No se deduce que esté
lloviendo ahora porque haya llovido durante la última hora.

Weather Underground y el panel Grafana de GRAFCAN son accesos públicos de mejor
esfuerzo, no contratos de API garantizados. Sus lecturas se identifican y no
entrenan los ajustes automáticos de la costa. Las consultas revisadas de GRAFCAN
están en `grafcan-queries.json`; se envían desde el recolector, nunca desde el
navegador de los visitantes. No hay consultas SQL suministradas por usuarios.

## Polen e información sísmica

**SEAIC / Polenes.com:** se utiliza la publicación anónima de lectura
`graphPollenData`, la misma que usan sus gráficos, para la estación `28`, Las
Palmas de Gran Canaria. La consulta abarca 90 días. Se guarda la fecha de la
muestra, sin inventar una hora. Los valores ausentes no pasan a cero. Alternaria
se identifica como hongo y se expresa en esporas/m³; el polen, en granos/m³.
Más de tres días se marca como dato antiguo. La prueba del 20-10-2026 recuperó
registros cuya última fecha era el 01-09-2026: no es una lectura del día ni una
previsión. Los recuentos se deduplican y persisten en `pollen/` de `lpa-data`,
sin mezclarse con el entrenamiento meteorológico. El acceso no es una API
documentada y queda explícitamente no disponible si cambia o falla.

**IGN:** se descarga el GeoRSS oficial de sismología y se filtran las coordenadas
de la región canaria (26–30,5 N, 19–12 O). No se convierte un feed vacío en una
afirmación de ausencia de actividad sísmica. El texto horario del RSS no declara
zona horaria: se conserva como texto del IGN, sin adjudicarle hora canaria o UTC.
Los enlaces de detalle solo apuntan al dominio oficial. No se emiten alertas ni
pronósticos sísmicos.

## Redes institucionales pendientes

- GRAFCAN / Gobierno de Canarias: la documentación es pública, pero una petición
  de observaciones ejecutada en Swagger devuelve HTTP 403 sin credenciales.
  Se ha solicitado una clave gratuita; seguimiento en
  [issue #1](https://github.com/erseco/meteo-local/issues/1). Mientras tanto,
  La Isleta se consulta mediante el panel público, con datos provisionales.
- Cabildo de Gran Canaria: se localizó HD Meteo, pero el acceso comprobado
  devolvió HTTP 503. Falta validar un acceso a las observaciones originales,
  separadas de las estimaciones espaciales de la plataforma.
- Ayuntamiento de Las Palmas: hay estaciones de riego documentadas, pero no se
  ha validado el acceso a sus medidas ni a las tres estaciones de Smart Beach.

La página muestra estos límites y enlaces a las instituciones. No hay endpoints,
credenciales ni datos inventados para simular su integración. Para activarlos se
necesita una URL pública verificable o autorización y credenciales del proveedor,
además de comprobar unidades, ubicación, fecha y condiciones de reutilización.

## Persistencia

En GitHub Actions, las observaciones y previsiones se guardan en la rama
**`lpa-data`**, separada del código. El workflow crea esa rama si no existe y
restaura el historial antes de cada recogida. Los commits de datos no disparan
el despliegue de `lpa`, y nunca se hace `force push` al historial.

Los archivos diarios JSONL se deduplican por estación y fecha real de observación.
Se archiva como máximo una consulta de previsión por hora UTC, con la hora real
cuando se obtuvo y las coordenadas y altitud de cada estación de referencia.
Se mantienen 90 días en los archivos activos; las versiones anteriores de Git
siguen existiendo en el historial de la rama. Solo contiene datos meteorológicos
públicos, no claves ni datos personales de suscriptores.

La descarga de previsiones para las estaciones reintenta hasta tres veces los
fallos transitorios. Si sigue fallando, conserva las observaciones e indica el
tipo de error; no inventa previsiones ni comparaciones para rellenar el historial.

El servidor local guarda por defecto en
`~/.local/share/meteo-local/lpa`; se puede cambiar con `--state-dir`.
Docker usa el volumen persistente `lpa-history`, montado en `/state`.
No se debe ejecutar `docker compose down -v` si se quiere conservar ese volumen.

## Comprobación y correcciones

1. Se guardan las previsiones para las coordenadas y altitud de **cada estación**.
2. Se comparan temperaturas observadas con previsiones emitidas entre 2 y 6 horas
   antes. Nunca se cuenta una previsión descargada después de la observación.
3. Se usa una observación por hora y estación, cercana a la hora nominal. Repetir
   una lectura no aumenta la muestra.
4. Se exigen al menos 14 días distintos. La primera mitad se usa para estimar un
   sesgo y la segunda para probarlo, con al menos 72 comparaciones en cada mitad.
5. La corrección solo se acepta si reduce el error absoluto medio al menos un
   10 % y obtiene una mejora en al menos el 95 % de 1.000 remuestreos por días.
   El ajuste está limitado a ±3 °C.
6. Solo la estación de Plaza de la Feria puede ajustar la previsión de la costa
   urbana a 2–6 horas. Se conserva la temperatura sin ajustar en los datos y se
   indica explícitamente la corrección. Tafira, aeropuerto y escuelas no se
   promedian para corregir todo el municipio.

La validación en Plaza de la Feria no demuestra precisión para todos los barrios.
No se crea un aprendizaje local de lluvia con METAR ni se afirman capacidades
que todavía no se han comprobado. Al principio el estado es **recogiendo datos**;
no existe una mejora demostrada hasta acumular y evaluar las observaciones.

## Referencias

- <https://www.aemet.es/es/eltiempo/observacion/ultimosdatos?l=C659M>
- <https://www.aemet.es/es/eltiempo/observacion/ultimosdatos?l=C658X>
- <https://aviationweather.gov/data/api/>
- <https://cep-gc-noroeste.github.io/mapa-estaciones-meteorologicas/>
- <https://weathercloud.net/en/faq>
- <https://opendata.sitcan.es/dataset/sistema-de-observacion-meteorologica-de-canarias>
- <https://datosabiertos.laspalmasgc.es/>
- <https://opendata.idegrancanaria.es/>
- <https://metrics.grafcan.es/d/Ss-8yBhGz/single-weather-station?orgId=1&var-thing_location=14>
- <https://app.weathercloud.net/d2199568870>
- <https://www.wunderground.com/dashboard/pws/ILASPA64>
- <https://www.polenes.com/>
- <https://www.ign.es/ign/RssTools/sismologia.xml>
