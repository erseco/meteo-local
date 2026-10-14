# 82. App de Android para Google Play

Fecha: 2026-10-12 · Estado: aceptado (en revisión en Google Play; rechazada el 13 y el 14-10-2026)

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
  `io.github.meteo_montflorit` y nombre «Montflorit al dia», también bajo el
  icono. Juanjo pidió que se distinguiera de la web instalada, que bajo el
  icono pone «Montflorit», y que el nombre no fuera solo del tiempo: la web da
  también avisos de peligro, trenes, tráfico, cortes de luz, aire y polen
  («no es solo meteo, dice muchas cosas esta web»). Android 16 (API 36) como objetivo, que es lo que exige Play, y
  Android 7 (API 24) como mínimo, lo que pide la biblioteca de Google
  (`androidbrowserhelper` 2.7.4).
- **Avisos**: los mismos de la web (ADR 0048). La TWA delega las
  notificaciones en la app (`enableNotifications`), así que salen con el
  nombre y el icono de la app, y Android 13 o posterior pide el permiso como a
  cualquier app.
- **La web dice que la app es suya**: `montflorit/.well-known/assetlinks.json`
  lleva la huella de la clave de firma; sin él, la app enseñaría la barra de
  dirección. `montflorit.py` lo copia con el resto de `montflorit/`. Lleva dos
  huellas: la de la clave de Google («firma de apps de Play», la de lo que se
  instala desde Play; está en Play Console, «Firma de aplicaciones») y la de
  la clave de subida (la del APK instalado a mano).
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
- La app abre en catalán hasta que se elige otro idioma; desde la 3.74.0, la
  web recuerda el elegido (ADR 0083).
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
- En el móvil de Juanjo (12-10-2026), con el APK servido en la red de casa:
  Play Protect lo bloquea porque no conoce al desarrollador («Más detalles» →
  «Instalar de todos modos»); instalada, «parece que todo va bien».
- Play Console (12-10-2026): app creada, versión 1 (1.0.0) en la prueba
  interna, con Juanjo como único probador; huella de la clave de Google
  añadida a `assetlinks.json`.
- Ficha y formularios (12-10-2026), con Juanjo revisando los textos y las
  imágenes: ficha en catalán (predeterminada) y castellano, con los textos y
  las imágenes de `android/fitxa/` (descripción corta «El temps del barri i
  alertes de perill: temps, incendis i riera.»); categoría «Tiempo»; contacto
  `jjdeharo@gmail.com` y la web; política de privacidad `privacitat.html`;
  sin anuncios ni cuentas; clasificación IARC «informativa» con contenido en
  línea; público de 13 años en adelante (no infantil); seguridad de los
  datos: solo un identificador (la dirección de las notificaciones),
  opcional, cifrado en tránsito, no compartido, borrable con «Desactiva»;
  icono y cabeceras etiquetados como hechos con IA, las capturas no; solo
  España.
- El sistema de permisos de Claude Code no deja al agente pulsar «Crear
  aplicación» ni preparar la versión de producción: esos pasos los hace
  Juanjo.
- Versión de producción 1 (1.0.0), solo España, enviada a revisión por Juanjo
  el 12-10-2026, con la publicación gestionada desactivada: si Google la
  aprueba, sale sola en la tienda.
- Pendiente: el resultado de la revisión. Después, añadir al manifiesto de la
  web `related_applications` con la app de Play, para que Chrome en Android
  ofrezca la app en lugar de instalar la web (propuesto, sin decidir).

## Cambio del 13-10-2026: rechazada por la política de afirmaciones engañosas

Google rechazó el primer envío el 13-10-2026 («Falta el enlace a la fuente de
información gubernamental»): la app muestra información de organismos
públicos y la descripción los citaba sin enlace. Para una app no asociada a
ninguno, Google pide en la descripción las fuentes oficiales con su dirección
y un aviso visible de que no representa a ninguna entidad pública. Juanjo
aprobó el texto («aplícalo») y la descripción larga (`android/fitxa/llarga-ca.txt`
y `llarga-es.txt`) lleva ahora, tras el primer párrafo, «No és una app
oficial: no representa cap organisme públic ni hi està vinculada…», y en
«D'on surt» cada fuente con su enlace (en el idioma del texto cuando existe;
todas comprobadas ese día), sin dejar ninguna. Se añadieron las que faltaban
desde las versiones 3.77-3.81: las observaciones del aeropuerto de Sabadell
(Aviation Weather Center, NOAA) y los modelos de ECMWF y NOAA. Unos 2.900 y
3.000 caracteres de los 4.000. Cambiado en Play Console y enviado otra vez a
revisión el mismo día, con los mismos once cambios del primer envío.


## Cambio del 14-10-2026: rechazada otra vez; fuentes oficiales con enlace directo y aviso dentro de la app

Google volvió a rechazarla el 14-10-2026 por el mismo motivo, aunque la
descripción ya llevaba el aviso y los enlaces. Google no dice qué falta. Lo
que se vio al revisarlo:

- La descripción no citaba todos los organismos públicos cuyos datos usa la
  app: faltaban los datos abiertos de la Generalitat (planes de Protecció
  Civil), los avisos de peligro de Meteocat, el Parc Natural de Collserola y
  Meteoalarm, por donde llegan los avisos de AEMET.
- Casi todos los enlaces llevaban a la portada del organismo, no a la página
  donde publica el dato.
- El aviso de que no es oficial estaba solo en la descripción. Google pide
  también «aclarar o añadir la información en la app», y a otros
  desarrolladores les rechazaron varias veces con el aviso solo en la ficha
  (caso gema-app, septiembre de 2026).

Juanjo aprobó los tres cambios («sí, hazlo»):

1. En la descripción (`android/fitxa/llarga-ca.txt` y `llarga-es.txt`),
   «D'on surt» pasa a ser «Fonts oficials (organismes públics)», con cada
   organismo y el enlace a la página concreta del dato (todos comprobados ese
   día, en el idioma del texto cuando existe), y «Altres fonts» para las que
   no son públicas, también con enlace. Al final se repite el aviso de que no
   es oficial. Unos 3.650 y 3.760 caracteres de los 4.000.
2. En la web (y por tanto en la app), una línea nueva en el pie de todas las
   páginas, «No és una web oficial ni representa cap organisme públic.»,
   junto al enlace a «Fonts i crèdits», y un párrafo al principio de esa
   página con el mismo aviso (3.83.1).
3. Al reenviar, una nota en inglés en el campo «¿Qué has hecho para
   solucionar este problema?» de Play Console, que dice dónde están el aviso y
   las fuentes.

Validación: pruebas, `probar-web` (tres navegadores, escritorio, móvil y
tableta, tema claro y oscuro, sin desbordamiento) y axe-core sin infracciones
en `index.html` y `fonts.html`, en catalán y en castellano. Si la rechazan
también así, el siguiente paso es la apelación.
