# 72. Cortes de luz, límites del barrio y compartir

Fecha: 2026-10-11 · Estado: aceptado

## Contexto

Juanjo preguntó si se podía «indicar la existencia de cortes eléctricos
indicando las calles implicadas de Montflorit». Al mismo tiempo pidió que
«cualquier pagina o consulta de meteo-montflorit» se pueda compartir, «así si
hay un incendio o un corte puedo enviar el enlace directo a esta información
a otros».

## Decisión

### Fuente de los cortes (`llum.py`)

- **La capa pública del mapa de averías de e-distribución**
  (`ESP_Prod_power_cut_View`, ArcGIS de Enel), la misma que dibuja el mapa de
  su web: averías y trabajos programados en curso, con municipio, clientes
  afectados, inicio, hora prevista de vuelta y una nota. **Sin calles**: el
  punto es aproximado a propósito («la ubicación … es orientativa», dice
  e-distribución; un corte de un cliente es una vivienda). Se comprobó que la
  capa pública es una vista y que la original pide credenciales.
- **Las calles y los portales sí existen**, pero solo de los trabajos
  programados de los próximos 7 días, en el buscador de Endesa
  (`wtp-pro.endesa.com`, que Juanjo encontró), que lee `descargos/mapData`.
  Está protegido por Imperva contra la lectura automática: una petición normal
  recibe un error y solo responde a un navegador real. **No se lee**: sería
  saltarse una protección puesta a propósito, y puede bloquear el NAS o dejar
  de funcionar. Se enlaza («Talls programats per carrer (Endesa)») y queda
  pendiente pedir permiso a e-distribución (Juanjo: «hazlo como dices»). El
  buscador solo lista los municipios con cortes programados en los 7 días
  siguientes (comprobado el 11-10-2026: sus 56 municipios de la provincia de
  Barcelona son los de sus datos); sin ninguno, Cerdanyola no sale, y el enlace
  lo dice («Cerdanyola només hi surt quan en té», 3.59.2). Su
  API oficial de averías es solo para comercializadoras y por CUPS.
- **Solo los del barrio**: dentro de los límites de Montflorit o a
  `LLUM_MARGE_KM` (150 m) o menos de ellos, por lo aproximado del punto
  (Juanjo: «limita los avisos a un radio menor … así evitaríamos falsas
  alarmas fuera del barrio»). Se dice «al barri» o «al límit del barri», no
  una distancia ni una calle.
- **No es un aviso de peligro**: un corte de luz es una molestia, como los de
  carretera (ADR 0053). Es una consulta: «Llum» en «Consultes» (icono «zap-off»
  de Lucide) y `/llum` en el bot. La nota de e-distribución va como la publica,
  en castellano, salvo la que no dice nada («No hay información adicional»).
- **Enlaces**: el mapa de e-distribución centrado en el barrio (la aplicación
  de ArcGIS que hay dentro de su página de averías admite `center`, `level` y
  `locale`; Juanjo: «si es posible centrado en montflorit») y el buscador por
  calles de Endesa.
- **Vigilancia** (Juanjo: «hay que vigilar que este servicio funcione»): la
  prueba diaria (`aprenentatge.diari`) comprueba que la capa responde y trae
  los campos que se usan; si no, se le dice una vez a Juanjo por Telegram, y
  otra cuando vuelve (marca `llum-falla`).

### Calle probable y avisos (3.59.0)

- **Calle probable** (Juanjo: «da una calle probable o un par, determina cómo,
  basado en las coordenadas, avisando que el servicio no ofrece este dato y es
  una estimación»): la calle con nombre más cercana al punto del corte, de
  `montflorit-carrers.geojson` (las vías con nombre de OpenStreetMap que tocan
  el barrio o están a 300 m, sin caminos ni escaleras, pero con el carrer de la
  Riera, que está marcado como pista), y una segunda si está a 40 m más o menos
  de la primera; ninguna si la más cercana está a más de 150 m. Cada texto dice
  que es una estimación y que e-distribución no da este dato.
- **Avisos** (Juanjo: «añade esto a las alertas de telegram y de la app»):
  categoría nueva «Talls de llum al barri» en el bot y en los avisos del
  navegador, que cada uno activa si quiere, y en el canal. Al aparecer un corte
  y al dejar de constar, con 🔌 (no tiene nivel) y el mapa centrado; tocar la
  notificación abre «Llum». Un corte de menos de 3 clientes no se anuncia (es
  una o dos casas): se ve en «Llum». No va a «Perill»: no es peligro. Un corte
  se reconoce entre pasadas por su código y su hora de inicio, porque el
  identificador interno de la capa cambia cuando Enel la rehace.

### Límites de Montflorit (`montflorit-limits.geojson`)

- No hay un límite oficial publicado: en OpenStreetMap, Wikidata y la
  Enciclopèdia Catalana Montflorit es un punto; la sección censal 011 acaba en
  la riera e incluye el bosque; el mapa de barrios del Ayuntamiento estaba en
  un diagnóstico cuyo enlace ha caducado.
- **La parte de Collserola**: la zona residencial de OpenStreetMap (way
  346465228), con el museo y el poblado de Ca n'Oliver, que la Viquipèdia
  sitúa «a la part de muntanya del barri».
- **La parte del otro lado de la riera** (Juanjo: «montflorit se extiende
  también hacia cerdanyola unas calles más allá de la riera»): de la Avinguda
  de la Flor de Maig y el carrer de l'Escala al de Josep Llimona, hasta el
  carrer de Santa Rosa. Lo confirman la Festa Major de Montflorit 2022 (actos
  en el «Carrer Àngel Guimerà (Chopos)» y en el Col·legi Turó de Guiera,
  revista del Ayuntamiento) y la Viquipèdia («finques de pisos baixos a la
  zona del Passeig dels Pollancres»).
- **Juanjo lo retocó a mano** en un mapa editable y lo guardó: es el que vale.
  Lo volvió a retocar después de publicar la 3.58.0 (el borde junto al carrer
  de la Riera y, al norte, justo por debajo del carrer de Santa Rosa) y pidió
  guardar el editor para seguir afinándolo: `eines/limits.py` abre el mapa,
  guarda en un borrador (`eines/limits-esborrany.geojson`) que la web no usa y,
  con `aplica`, lo pasa a `montflorit-limits.geojson`. Cambiar los límites no
  cambia la versión: son datos.
- Se guarda en el repositorio como GeoJSON, con la fuente y la licencia ODbL de
  OpenStreetMap, para otros usos (Juanjo: «guarda estos datos, podremos
  usarlos más adelante para otras cosas»).

### Compartir

- **Botón en la cabecera de todas las páginas**, con el icono «share-2» de
  Lucide (Juanjo: «decide tú»). Comparte la dirección de lo que se ve, con la
  opción elegida (`consultes.html#llum`).
- **Botón en cada ficha de «Perill»**: comparte el enlace directo a ese aviso
  (`perill.html#a-…`). Al abrirlo, la página va al aviso, despliega su mes y su
  detalle y lo destaca unos segundos.
- En el móvil se abre el menú de compartir del sistema (`navigator.share`);
  donde no lo hay, se copia el enlace y se dice «Enllaç copiat».

### Cada aviso, con su enlace (3.60.0)

Juanjo: «todos los avisos que tengan una alerta configurable (como la luz)
deben tener un enlace, como ya has hecho con la pestaña peligros». Cada aviso
de peligro, riera, lluvia y cortes de luz lleva al final «Més informació a
Temps a Montflorit», en la lengua de quien lo recibe: peligro y riera, a su
ficha de «Perill» (el mismo id que el botón de compartir, `id_fitxa`,
comprobado contra `web/perill.js`); los cortes, a «Llum»; la lluvia, a «El
temps» (además del radar). La notificación del navegador abre esa misma
página, con la ficha, y no repite el enlace en el texto. El historial de
«Perill» guarda el aviso sin el enlace: ya se está en la web.

## Alternativas descartadas

- **Leer el buscador de Endesa con un navegador sin pantalla en el NAS**:
  funciona, pero es saltarse su protección (ver arriba).
- **Poner una calle cercana al punto del corte** (geocodificación inversa):
  el punto es aproximado; sería dar una calle que puede ser falsa.
- **Cortes de luz en «Perill» o en «Situacions de perill»**: no son peligro.
- **Un radio de 1 km alrededor de casa** (primera versión): llegaba al parque
  tecnológico y a la Ginesta, que no son el barrio.

## Riesgos

- La capa de Enel es la de un visor, no un servicio documentado: lo vigila la
  prueba diaria.
- Sin historial todavía, no se sabe cuántos cortes hay en el barrio.

## Validación

- `tests/test_llum.py`: solo los del barrio (dentro, al límite, fuera), el
  texto del bot (sin la nota vacía, singular, enlaces) y la prueba diaria.
- `tests/test_web.py`: compartir con el menú del sistema y, sin él, copiar.
- Capa real el 11-10-2026: 23 cortes en España, ninguno en el barrio; prueba
  diaria correcta. Mapa centrado comprobado en un móvil.
- Web con un corte de ejemplo en «Llum» y un enlace directo a un aviso de
  agosto en «Perill», en Chromium, Firefox y WebKit, a 320 y 390 px; axe-core
  sin incidencias.
