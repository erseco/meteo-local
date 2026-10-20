# Tiempo en Las Palmas de Gran Canaria

Adaptación del fork `erseco/meteo-local` sobre la versión 3.169.0 de
[jjdeharo/meteo-local](https://github.com/jjdeharo/meteo-local), commit
`3405f28689b8a52f8da7c7c2d9db83df07d5c9cc`.

Se reutilizan el generador, la navegación en castellano, el selector de salida y
las consultas del original. La portada compacta de siete días y los adaptadores
están en `lpa/`; los archivos del original se conservan para facilitar actualizaciones.

## Interfaz y consulta de datos

La portada muestra una lectura reciente de Plaza de la Feria cuando está
disponible; en su ausencia, la estimación actual del modelo, etiquetada como tal.
El viento y la humedad proceden de esa misma fuente; la probabilidad de lluvia
es siempre previsión del modelo. Los avisos no comprobados y los datos antiguos
siguen visibles. Método, historial y detalles de estaciones quedan desplegables.

Se solicitan **siete días naturales** de Open-Meteo. El resumen de cada día cubre
el día completo; el porcentaje es el máximo de sus probabilidades horarias,
no la probabilidad agregada de todo el día. Las horas muestran los intervalos
futuros disponibles y se desplazan con el dedo, arrastrando con el ratón, con
las flechas de la interfaz o con el teclado. A partir del cuarto día se advierte
mayor incertidumbre; no se presenta todo el horizonte con la misma fiabilidad.

La recogida genera también:

- `weather.json`: contrato público `schema_version=1.0`, unidades, fechas ISO,
  caducidad, previsión diaria/horaria, observaciones por estación, avisos,
  metadatos del radar y ambiente. No incluye imágenes, credenciales ni archivos internos.
- `es/datos.html`: resumen **renderizado al publicar**, legible sin JavaScript,
  con la misma fecha que el JSON y metadatos `Dataset` / `DataDownload` de Schema.org.
- Canonical, descripción, Open Graph y descubrimiento del JSON en el HTML;
  `WebSite` en portada y `sitemap.xml` con las páginas principales.
- `llms.txt`: guía orientativa de acceso y semántica. No es un estándar universal
  ni garantiza que una IA indexe o cite la web.

Los metadatos no convierten el proyecto en fuente oficial. Cada proveedor
conserva sus condiciones; AGPL es la licencia del código, no una licencia general
de los datos recopilados. `robots.txt` solo sería efectivo en la raíz del dominio:
este proyecto en un subdirectorio de GitHub Pages no modifica el de `erseco.github.io`.

## Ramas

- `main`: referencia del original, sin personalización local.
- `lpa`: versión de Las Palmas y rama predeterminada del fork.

La rama predeterminada se cambia en **Settings → Default branch → lpa** del fork.
Ese ajuste es independiente del contenido Git. No elimina ni renombra `main`.
El workflow original continúa comprobando `main`; `lpa.yml` comprueba y publica `lpa`.

## Web en GitHub Pages

El workflow `Las Palmas` genera y despliega la web con cada push a `lpa`,
tras superar las pruebas. Los pull requests ejecutan las comprobaciones, pero
no despliegan. También se puede lanzar manualmente desde **Actions → Las Palmas →
Run workflow**, eligiendo `lpa`.

**Configuración inicial:** en **Settings → Pages → Build and deployment → Source**,
seleccionar **GitHub Actions**. El workflow usa el token del repositorio, sin PAT
ni secretos adicionales. Si Pages no está habilitado, `configure-pages` lo indicará;
el token estándar del workflow no puede habilitarlo por sí solo.

URL prevista: <https://erseco.github.io/meteo-local/>; redirige a la interfaz en
castellano en `/es/`. La URL efectiva se muestra en el entorno `github-pages`.

Cada 15 minutos se programa otra ejecución para recoger datos reales y renovar
la publicación, sin commits en el código. El historial público se persiste en `lpa-data`. GitHub puede retrasar las ejecuciones;
no es una garantía de actualización puntual ni un sistema de alertas en tiempo
real. El cron se ejecuta desde la rama predeterminada, que debe seguir siendo
`lpa`. Las ejecuciones programadas mantienen las pruebas unitarias y la generación;
las pruebas de navegador y accesibilidad se ejecutan al cambiar código o al lanzar
el workflow manualmente.

Los datos ficticios de las pruebas no se publican: la compilación de producción
se hace en otro job y vuelve a consultar las fuentes. Si falla la previsión,
se detiene el despliegue; la web anterior oculta los datos cuando superan las dos
horas. Los fallos de fuentes secundarias aparecen como no disponibles.

## Ejecutar localmente

Desde la raíz del repositorio:

```sh
git switch lpa
python3 -m pip install -r lpa/requirements.txt
python3 -m lpa.serve
```

Abrir <http://127.0.0.1:8080/es/>. El servidor genera la interfaz y consulta los
datos al arrancar y cada 15 minutos. Durante la primera consulta puede aparecer
el aviso de datos no disponibles. No necesita claves, el NAS de Juanjo ni IONOS.
No ejecutar `publica.sh`, `nas/`, `bot/instalar.sh` ni `reserva/instalar.sh` para
esta adaptación: son despliegues específicos del original.

Con Docker, imagen basada en Alpine:

```sh
docker compose -f lpa/compose.yml up -d --build
```

Abrir <http://localhost:8080/es/>. Publica en el puerto 8080 del equipo. Para
acceso público desde Docker, colocar detrás del proxy HTTPS habitual. Telegram,
push y la configuración de un dominio propio no están incluidos.

También se pueden generar los archivos para otro alojamiento:

```sh
python3 -m lpa.build /tmp/meteo-lpa
python3 -m lpa.collect /tmp/meteo-lpa/montflorit.json
```

El alojamiento debe servir esa carpeta y ejecutar la recogida cada 15 minutos;
**no basta con publicar el HTML una vez**. No guardar el resultado de cada
consulta en la rama de código. `lpa.serve` hace esa actualización y conserva el historial en disco.
La API gratuita de Open-Meteo tiene condiciones y límites de uso; revisar su
licencia antes de un despliegue comercial.

## Qué funciona y qué falta

| Función | Adaptación |
|---|---|
| Interfaz, gráficos, tablas y tema | Los del original, generados en castellano |
| Previsión y probabilidad de lluvia | Open-Meteo `best_match`, coordenadas públicas aproximadas `28.124, -15.436` |
| Hora y cambio de horario | `Atlantic/Canary`; consulta por Unix time y fechas con desfase explícito |
| Temperatura, humedad y viento actuales | Estimación del modelo separada de AEMET, METAR y red escolar; página Estaciones con procedencia y antigüedad |
| Sol e índice UV | Open-Meteo para Las Palmas |
| Aire | CAMS global; índice calculado con las funciones del original, sin correcciones catalanas |
| Avisos oficiales | AEMET vía Meteoalarm, zona **Norte de Gran Canaria** |
| Si sales | Interfaz y reglas meteorológicas del original; umbrales provisionales, sin validación local |
| Estaciones locales y contraste con lo medido | AEMET Plaza de la Feria y Tafira, aeropuerto GCLP, Arenales, La Montañeta (WU), La Isleta (GRAFCAN) y catálogo de 14 estaciones escolares; historial y comprobación prospectiva |
| Radar | Secuencia de reflectividad AEMET de Canarias; sin llegada/final de lluvia calculados |
| Mar y puerto | Widgets oficiales de PORTUS: nivel del mar, viento, presión y oleaje previsto; carga bajo demanda |
| Guaguas | Consultas oficiales, rutas, incidencias y códigos de referencia; llegadas dentro de la web pendientes |
| Protección Civil, incendios y restricciones | No disponible; no se usa Meteocat, INUNCAT ni Pla Alfa |
| Crecidas de barrancos | No disponible; no se traslada el modelo de Sant Cugat |
| Polen y esporas | Recuentos de SEAIC para Las Palmas, con fecha real y aviso si son antiguos; sin sustituirlos por polen peninsular |
| Sismicidad | GeoRSS del IGN filtrado para Canarias, separado de la meteorología y sin inventar la zona horaria de sus textos |
| Guaguas, tráfico y luz | No disponible; no se presentan datos de Cataluña |
| Aprendizaje, correcciones y fiabilidad | Historial persistente y validación temporal de temperatura; corrección solo tras superar los requisitos de muestra y mejora |
| Notificaciones y Telegram | Requieren backend y credenciales propios; desactivados |
| Aplicación Android del original | No se anuncia ni se usa su asociación de dominio |

No se afirma una equivalencia funcional completa: se conserva la aplicación y
su navegación, y cada servicio sin equivalente local aparece como no disponible.
Una fuente que falla conserva `null` y un error; no equivale a «sin avisos» ni a
«sin incidencias». No se usa ningún historial ni calibración de Montflorit.
La capa conserva observaciones y previsiones en `lpa-data` (Actions) o en disco/volumen (servidor local y Docker). Véase [OBSERVACIONES.md](OBSERVACIONES.md) para fuentes, contratos, límites y método.

Radar, PORTUS y accesos de transporte: [RADAR-MAR-MOVILIDAD.md](RADAR-MAR-MOVILIDAD.md).
La portada incluye radar y `es/radar.html` reúne radar y gráficos marinos. Los
gráficos oficiales de PORTUS se consultan directamente al cargarlos y no se
archivan en la rama de datos. Las llegadas de Guaguas no están integradas: las
consultas verificadas no proporcionaron muestras utilizables.
Los accesos institucionales pendientes y las gestiones necesarias se detallan en [FUENTES-PENDIENTES.md](FUENTES-PENDIENTES.md).

Las Palmas tiene microclimas: el punto urbano elegido no representa por igual
Las Canteras, Ciudad Alta, Tafira y el resto del municipio. Para otra ubicación,
cambiar `profile.py`, adaptar también las coordenadas de `build.py` y comprobar
las fuentes aplicables; todavía no es un sistema de perfiles para cualquier ciudad.

La lluvia se sirve como acumulación del modelo en el intervalo indicado, sin
volver a multiplicarla por la probabilidad. Los peligros calculados con umbrales
locales de Montflorit no se publican como alertas de Las Palmas.

## Actualizar desde Juanjo

Con el árbol de trabajo limpio y estando en `lpa`:

```sh
./lpa/update-upstream.sh
```

El script trae `upstream/main`, lo fusiona sin reescribir el historial y pasa las
pruebas y la generación. Si hay conflictos o falla una comprobación, se detiene
sin subir cambios. Si pasa, revisar y publicar:

```sh
git diff upstream/main...lpa
git push origin lpa
```

Si una actualización del generador cambia un punto de integración, la generación
falla explícitamente. Revisar `build.py` contra la nueva versión; no eliminar
la comprobación para ocultar el cambio. Después de actualizar, reconstruir el
contenedor o regenerar los archivos del alojamiento.

Para mantener también la copia `main` del fork al día:

```sh
git switch main
git merge --ff-only upstream/main
git push origin main
git switch lpa
```

No se garantiza ausencia de conflictos: la separación reduce los archivos
compartidos, pero una modificación de los contratos del original requiere adaptar
esta capa. La integración continua comprueba las pruebas originales, el contrato
LPA, la generación, tres motores de navegador y accesibilidad.

## Verificación

```sh
TZ=Europe/Madrid python3 -m unittest discover -s tests -b
python3 -m unittest discover -s lpa/tests -v
python3 -m lpa.build /tmp/meteo-lpa
```

La suite original usa fechas locales de Madrid. Esa variable es solo para sus
pruebas; el proceso LPA usa explícitamente `Atlantic/Canary`.
Las pruebas propias cubren separación de fuentes, fallos parciales, feeds de
avisos caducados, acumulaciones y probabilidades, y horas repetidas en octubre.
Las pruebas de navegador usan datos ficticios y comprueban móvil/escritorio,
claro/oscuro, accesibilidad, fuentes fallidas y datos caducados. La CI conserva
capturas. `lpa/tests/browser.cjs` requiere Playwright y axe-core.

Fuentes oficiales de referencia:

- <https://open-meteo.com/en/docs>
- <https://open-meteo.com/en/docs/air-quality-api>
- <https://www.aemet.es/es/eltiempo/prediccion/municipios/horas/tabla/palmas-de-gran-canaria-las-id35016>

Código AGPL-3.0-or-later; contenidos CC BY-SA 4.0. Se conservan las atribuciones
originales. Versión de la adaptación independiente en `lpa/profile.py`.
