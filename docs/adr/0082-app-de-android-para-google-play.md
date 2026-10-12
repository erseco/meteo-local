# 82. App de Android para Google Play

Fecha: 2026-10-12 · Estado: aceptado (en preparación: sin subir a Play)

## Contexto

El 08-10-2026 Juanjo dejó Google Play para más adelante, según el uso (ADR
0048), porque costaba una cuenta, una prueba cerrada con 12 personas durante
14 días y rehacer el paquete cada año a cambio de la misma web con su icono.

El 12-10-2026 volvió a preguntar si merecía la pena. El uso era bajo (3
dispositivos con los avisos de la web y 4 suscriptores del bot), pero Juanjo
tiene cuenta de desarrollador de Play desde hace años, bloqueada desde 2024 y
ya desbloqueada. Las cuentas personales anteriores al 13-11-2023 no tienen que
hacer la prueba cerrada, y en su cuenta la pista «Producción» de una app
antigua está abierta. Con eso, lo que queda lo hace casi todo la IA, y lo que
se gana es que instalarla sea fácil: «búscala en Play» lo entiende todo el
mundo; «añadir a la pantalla de inicio», no. Juanjo: «hazlo».

## Decisión

Versión 3.73.0 de la web; la app empieza en la 1.0.0.

- **Una Trusted Web Activity (TWA)**, el mecanismo de Google para publicar una
  web instalable en Play: la app abre la web publicada a pantalla completa,
  con Chrome por debajo. No lleva código propio ni copia de la web; cada
  cambio de la web llega a la app sin tocarla.
- **Generada con [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap)**
  1.27 (Google Chrome Labs, Apache-2.0) en `android/`, a partir del manifiesto
  de la web publicada (`android/twa-manifest.json`). Identificador
  `io.github.meteo_montflorit`, nombre «Temps a Montflorit» y, bajo el icono,
  «Montflorit». Android 16 (API 36) como objetivo, que es lo que exige Play, y
  Android 7 (API 24) como mínimo, lo que pide la biblioteca de Google
  (`androidbrowserhelper` 2.7.4).
- **Avisos**: los mismos de la web (ADR 0048). La TWA delega las
  notificaciones en la app (`enableNotifications`), así que salen con el
  nombre y el icono de la app, y Android 13 o posterior pide el permiso como a
  cualquier app.
- **La web dice que la app es suya**: `montflorit/.well-known/assetlinks.json`
  lleva la huella de la clave de firma; sin él, la app enseñaría la barra de
  dirección. `montflorit.py` lo copia con el resto de `montflorit/`. Cuando
  Play firme la app con su propia clave («firma de apps de Play»), se añade
  también esa huella.
- **Icono de una sola tinta** (`montflorit/icones/icona-monocrom.svg` y su
  PNG de 192 px, en el manifiesto con `purpose: monochrome`): la nube con
  lluvia de Lucide en blanco sobre fondo transparente, que Android pide para
  la barra de notificaciones.
- **Clave de subida fuera del repositorio**, que es público:
  `~/.config/meteo-montflorit/android/upload.jks` y su contraseña en
  `clau.env`, y una copia cifrada en `meteo-montflorit/meteo-local-registre`
  (`claus/claus-android.tar.gz.gpg`, como las del NAS y de IONOS, ADR 0044).
  Con la firma de apps de Play, si se pierde la clave de subida, Google deja
  cambiarla; la que firma lo que se instala la guarda Google.
- **La versión de la app va aparte de la de la web**: solo cambia cuando cambia
  el envoltorio (icono, nombre, versión de Android que pide Play), no con cada
  versión de la web.
- **Cada año**, cuando Play suba la versión de Android exigida: actualizar
  Bubblewrap, `bubblewrap update` en `android/`, subir `appVersionCode` y
  publicar el paquete nuevo.

## Alternativas descartadas

- **Seguir sin Play**: la web ya se instala, pero hay que saber hacerlo, y es
  lo que más frena a quien no lo ha hecho nunca.
- **App nativa o con Capacitor**: habría que mantener dos programas; la TWA es
  la misma web.
- **PWABuilder**: también usa Bubblewrap por debajo, pero desde una web de
  Microsoft; con la herramienta en el equipo, todo queda en el repositorio.

## Riesgos

- Play rechaza a veces las apps que son solo una web («funcionalidad mínima»).
  Esta funciona sin conexión (las páginas guardadas, ADR 0015), envía avisos y
  se abre en su ventana, pero no está garantizado.
- Sin Chrome (o un navegador compatible con TWA) en el móvil, la app abre la
  web en una pestaña personalizada, con barra de dirección.
- Como la web instalada, la app abre siempre en catalán; en castellano hay que
  pulsar «ES».
- Solo Android; en iPhone, la web (ADR 0015 y 0048).

## Validación

- Pruebas: `test_app_d_android` comprueba que la web publicada lleva
  `assetlinks.json` con el identificador de la app y el icono de una sola
  tinta.
- Compilación (12-10-2026, `android/construeix.sh`): APK firmado de 1,0 MB y
  AAB de 1,1 MB; `aapt2` da `io.github.meteo_montflorit`, versión 1.0.0,
  objetivo API 36. `apksigner` da la huella SHA-256 de la clave de subida, la
  misma que publica la web, y la API de Digital Asset Links de Google ya
  devuelve el vínculo entre la web y la app.
- Para compilar hacen falta el JDK 17 con compilador (`openjdk-17-jdk-headless`;
  el JRE no basta), el SDK en `~/Android/Sdk` con `build-tools;36.1.0` y
  `platforms;android-36`, y un enlace `~/Android/Sdk/bin` a
  `cmdline-tools/latest/bin`, porque Bubblewrap busca ahí `sdkmanager`.
  Configuración de Bubblewrap: `~/.bubblewrap/config.json`.
- Pendiente: instalar el APK en el móvil de Juanjo y comprobar que se abre sin
  barra de dirección y que llegan los avisos; después, la subida a Play.
