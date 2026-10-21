# Accesos pendientes de Las Palmas

Comprobación: 21 de octubre de 2026. No confundir documentación de una estación
instalada con datos actuales ni datos modelizados con mediciones de un sensor.

| Fuente | Comprobado | Siguiente paso |
|---|---|---|
| GRAFCAN | Clave recibida y autenticación verificada desde Actions. La Isleta 3705/thing 14 ofrece catálogo, unidades, intervalos y validación de medidas. Integración oficial mediante cabecera. | Confirmar condiciones de redistribución y semántica de precipitación antes de integrar lluvia. [Issue #1](https://github.com/erseco/meteo-local/issues/1). |
| Cabildo / SPEGC | HD Meteo integra estaciones y estimaciones espaciales. La consulta de `https://gc.hdmeteo.com/` devolvió 503. | Solicitar el acceso de lectura a observaciones originales y sus condiciones; no tratar el mapa interpolado como otra estación. |
| Ayuntamiento / Smart Beach | La nota municipal documenta tres estaciones en Las Canteras, además del proyecto de riego. | Pedir a Innovación/Ciudad de Mar la API o exportación periódica, identificadores, unidades y fecha de lectura. |
| Ayuntamiento / calidad del aire | El catálogo anuncia «Sensores de calidad del aire» del Gemelo Digital, bajo Mercados. La descarga no se ha verificado; el portal dio 503 y el navegador mostró un error de certificado. | Confirmar acceso y si son sensores exteriores o de interiores; no extrapolarlos al aire de toda la ciudad. |
| Gobierno / calidad del aire | Hay un visor oficial de medidas provisionales y un catálogo de datos validados. Las direcciones antiguas `www3.gobiernodecanarias.org/medioambiente/calidaddelaire/` devolvieron 404. | Localizar el acceso operativo actual y sus estaciones urbanas. Mantener CAMS como estimación, no como medida. |
| Centros de la capital | CEIP El Zardo anuncia una estación en el huerto. IES Los Tarahales documentó Clima/GLOBE en 2013; CEIP Santa Catalina lo citó en 2017. | Consultar al CEP/centros si siguen operativas, modelo, frecuencia y URL o identificador de publicación. No hay un flujo automático actual confirmado. |
| SEAIC | La consulta pública de la estación 28 devuelve datos históricos; último recuento recuperado: 01-09-2026. | Consultar periodicidad actual y reutilización; mostrar la fecha antigua mientras no haya medidas nuevas. |
| Weather Underground | ILASPA64 entrega muestras verificadas localmente, pero la primera consulta desde Actions no obtuvo datos utilizables. Se admiten bloques métricos, SI e imperiales y se distingue cada muestra del resumen diario. | Comprobar disponibilidad desde el alojamiento; si WU no sirve muestras al recolector, solicitar acceso oficial de lectura autorizado o un suministro directo del propietario. No utilizar claves embebidas de la web. |
| Guaguas | Portal municipal 503; consultas de la web 403 o HTTP 200 con «No se pueden acceder a los datos solicitados». Accesos oficiales añadidos a Si sales. | API de lectura operativa o GTFS-RT con marcas temporales y condiciones; no confundir horarios estáticos con llegadas. |
| PORTUS | Mareógrafo 3450 con lecturas; widgets oficiales integrados bajo demanda. Boyas 1414 y 2442 con incidencias en esta comprobación. | Para una API propia, confirmar acceso POEM, reutilización, calidad y referencias. Los widgets conservan los datos en la fuente. |

Para cualquiera de las instituciones basta acceso de **lectura**: URL, catálogo,
ubicación y altitud, unidades, zona horaria, frecuencia, indicadores de calidad y
condiciones de publicación. No hacen falta cuentas administrativas.

La clave de GRAFCAN se guarda como secreto de Actions `GRAFCAN_API_KEY` y se
inyecta solo en el paso de recogida. El recolector envía
`Authorization: Api-Key <clave>` únicamente al origen HTTPS oficial, sin seguir
redirecciones. No se copia a JavaScript, JSON público ni `lpa-data`.
En Docker puede suministrarse como variable de entorno del mismo nombre.


## Referencias verificadas

- <https://sensores.grafcan.es/>
- <https://catedradelagua.ulpgc.es/gc-hdmeteo-com-muestra-10-parametros-meteorologicos-de-gran-canaria-en-tiempo-real/>
- <https://www.laspalmasgc.es/es/ayuntamiento/prensa-y-comunicacion/notas-de-prensa/nota-de-prensa/El-Ayuntamiento-impulsa-la-modernizacion-tecnologica-de-Las-Canteras-con-la-implantacion-del-proyecto-Smart-Beach/>
- <https://datosabiertos.laspalmasgc.es/data/>
- <https://datos.canarias.es/catalogos/general/dataset/calidad-del-aire-de-canarias>
- <https://www3.gobiernodecanarias.org/medusa/edublog/ceipelzardo/>
- <https://www3.gobiernodecanarias.org/medusa/ecoescuela/tamadaba/2013/07/10/el-proyecto-clima-y-la-red-de-estaciones-meteorologicas/>
- <https://ceipscatalina.blogspot.com/2017/09/oferta-educativa-2017-18.html>
