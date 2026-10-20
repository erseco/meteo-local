# Radar, mar y movilidad

## Radar AEMET

`radar.py` consulta el mismo servicio público que el visor de AEMET, sin clave:

- `https://www.aemet.es/es/api-eltiempo/radar/timeline/PPI/CAN`
- `https://www.aemet.es/es/api-eltiempo/radar/leyenda-radar/PPI`
- `bounds-radar/PPI/{fichero}` e `imagen-radar/PPI/{fichero}` bajo esa misma base.

Solo se admite `LPA` y el producto `PPI.Z_005_240`. Se comprueban la fecha con
desplazamiento horario y la fecha UTC del nombre del fichero, se ordenan y
deduplican las imágenes y se descargan como máximo seis, de las últimas dos
horas. Más de 45 minutos se considera antiguo. Las descargas fallidas se omiten;
si ninguna es válida se muestra «no disponible», nunca «sin lluvia».

La imagen se recorta y reduce en la misma proyección Web Mercator que utiliza
el visor oficial. La cartografía de `assets/canarias-coast.json` procede de
`https://www.aemet.es/es/api-eltiempo/lineas_limite/7/CAN`: se ha convertido
TopoJSON a anillos y simplificado a 0,002 grados para este mapa orientativo.
Los colores del raster se conservan con vecino más próximo; la escala es la
publicada por AEMET. Imagen y cartografía se atribuyen a AEMET.

La reflectividad en dBZ **no es una medición de lluvia en superficie**. Un eco
puede no llegar al suelo, la orografía puede ocultar precipitación y el área
gris puede carecer de cobertura. No se convierten colores a mm/h, no se anuncia
la llegada de lluvia y no se entrena con estas imágenes. Los puntos de las
estaciones conservan sus observaciones separadas. La precipitación de GRAFCAN
sigue pendiente de validar.

La portada incluye el visor; `es/radar.html` reúne radar y mar. Las imágenes se
publican dentro del JSON del mismo alojamiento. No se hacen consultas a AEMET
desde el navegador, ni se aumenta la frecuencia de publicación de Actions.
El visor vuelve a leer ese JSON cada cinco minutos mientras está visible y al
volver a la pestaña, comprobando de nuevo la antigüedad de las imágenes.

Referencias: [visor](https://www.aemet.es/es/eltiempo/observacion/radar?w=1),
[ayuda](https://www.aemet.es/es/eltiempo/observacion/radar/ayuda).

## PORTUS / Puertos del Estado

Se utilizan los widgets oficiales documentados en
<https://portus.puertos.es/Portus/docs/widgets.pdf>. Se cargan solo al pulsar el
botón correspondiente, con un enlace alternativo para abrirlos directamente:

- Mareógrafo de Las Palmas 2, estación **3450**: `SeaLevel`, `WindSpeed`,
  `WindSpeedMax`, `WindDir` y `AirPressure` mediante `PortusData/rtChart`.
- Predicción de oleaje atlántico alrededor de Gran Canaria mediante
  `predictionWidget`, `resourceId=oleaje-atl`, variable `WAVE`.

La comprobación del 20/10/2026 utilizó el catálogo público
`https://portus.puertos.es/portussvr/api/estaciones/rt/SEA_LEVEL?locale=es` y
el POST de **lectura** `lastData/station/3450?locale=es`. Respondió con nivel del
mar, viento y presión. Sus valores se dividen por el `factor` de cada parámetro;
el visor oficial identifica la fecha como GMT. No se vuelcan estas respuestas
ni series históricas en nuestro JSON o en `lpa-data`; los gráficos consultan
directamente Puertos del Estado y conservan sus unidades, fechas y controles.

La boya de Las Palmas Este (**1414**) figuraba con «Sin trasmisión» y la de Gran
Canaria (**2442**) «En tierra» en el catálogo `estaciones/rt/WAVE`. Son estados
de aquella comprobación, no una vigilancia de disponibilidad en nuestra web.
El mareógrafo mide dentro del puerto y **no mide la altura de las olas** de
Las Canteras. El oleaje mostrado es una predicción del modelo; no se emite una
recomendación de baño ni se presupone una referencia vertical para el nivel.

La documentación POEM en <https://poem.puertos.es/> redirige a identificación
para acceder a sus colecciones autorizadas. Integrar una API propia requeriría
confirmar acceso, condiciones de reutilización y referencia de cada variable.
El manual de descargas históricas tiene condiciones específicas; no se asume
que se puedan redistribuir aquellas series. El manual de widgets solicita
notificar su uso a `webmaster@puertos.es`; no se ha enviado ningún correo.

## Guaguas Municipales

«Si sales» incluye accesos oficiales a Próxima Guagua, incidencias y planificación
de rutas, además de cuatro códigos de parada contrastados con páginas de líneas.
Un intercambiador tiene varios códigos según línea y sentido.

No hay llegadas integradas. En la comprobación del 20/10/2026, el portal municipal
de datos devolvió 503; algunas páginas de Guaguas y consultas devolvieron 403.
El POST de lectura que usa el JavaScript público
`https://www.guaguas.com/js/ajax/consulta_tiempo_parada.php`, con `paradas=8`,
respondió HTTP 200 con «No se pueden acceder a los datos solicitados». Un HTTP
200 así no es una respuesta válida ni prueba que no vayan a pasar guaguas.

Para habilitar llegadas necesitamos un servicio de lectura operativo con su
documentación y condiciones: API municipal/Guaguas o GTFS-RT, identificador de
parada, línea, sentido, fecha de cálculo y llegada prevista. GTFS estático solo
describe horarios programados. La publicación cada 15 minutos sería demasiado
lenta para una cuenta atrás fiable; se necesitaría un recolector más frecuente
o una consulta directa autorizada con CORS o un proxy con caché breve.

Fuentes: <https://www.guaguas.com/lineas/proxima-guagua>,
<https://www.guaguas.com/lineas/1>, <https://www.guaguas.com/lineas/21>,
<https://www.guaguas.com/lineas/32>,
<https://datosabiertos.laspalmasgc.es/data/>.
