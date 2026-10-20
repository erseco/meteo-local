# Tiempo en Las Palmas de Gran Canaria

Adaptación del fork `erseco/meteo-local` sobre la versión 3.169.0 de
[jjdeharo/meteo-local](https://github.com/jjdeharo/meteo-local), commit
`3405f28689b8a52f8da7c7c2d9db83df07d5c9cc`.

Se reutilizan el generador, la interfaz en castellano, los gráficos, las tablas,
el selector de salida y las consultas del original. Los adaptadores de Las Palmas
están en `lpa/`; no se reescribe ni sustituye la aplicación original.

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
la publicación, sin commits automáticos. GitHub puede retrasar las ejecuciones;
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
python3 -m pip install numpy pillow
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
consulta en Git. `lpa.serve` hace esa actualización sin commits automáticos.
La API gratuita de Open-Meteo tiene condiciones y límites de uso; revisar su
licencia antes de un despliegue comercial.

## Qué funciona y qué falta

| Función | Adaptación |
|---|---|
| Interfaz, gráficos, tablas y tema | Los del original, generados en castellano |
| Previsión y probabilidad de lluvia | Open-Meteo `best_match`, coordenadas públicas aproximadas `28.124, -15.436` |
| Hora y cambio de horario | `Atlantic/Canary`; consulta por Unix time y fechas con desfase explícito |
| Temperatura, humedad y viento actuales | Estimación del modelo; se identifican como estimación, no observación |
| Sol e índice UV | Open-Meteo para Las Palmas |
| Aire | CAMS global; índice calculado con las funciones del original, sin correcciones catalanas |
| Avisos oficiales | AEMET vía Meteoalarm, zona **Norte de Gran Canaria** |
| Si sales | Interfaz y reglas meteorológicas del original; umbrales provisionales, sin validación local |
| Estaciones locales y contraste con lo medido | No disponible hasta integrar una fuente local |
| Radar y llegada/final de lluvia | No disponible hasta validar cobertura y proveedor local |
| Protección Civil, incendios y restricciones | No disponible; no se usa Meteocat, INUNCAT ni Pla Alfa |
| Crecidas de barrancos | No disponible; no se traslada el modelo de Sant Cugat |
| Guaguas, tráfico, luz y polen | No disponible; no se presentan datos de Cataluña |
| Aprendizaje, correcciones y fiabilidad | No disponible hasta disponer de observaciones e historial locales |
| Notificaciones y Telegram | Requieren backend y credenciales propios; desactivados |
| Aplicación Android del original | No se anuncia ni se usa su asociación de dominio |

No se afirma una equivalencia funcional completa: se conserva la aplicación y
su navegación, y cada servicio sin equivalente local aparece como no disponible.
Una fuente que falla conserva `null` y un error; no equivale a «sin avisos» ni a
«sin incidencias». No se usa ningún historial ni calibración de Montflorit.
La capa actual no acumula un registro de aprendizaje local.

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
