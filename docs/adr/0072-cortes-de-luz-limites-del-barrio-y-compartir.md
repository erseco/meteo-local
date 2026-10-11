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
  pendiente pedir permiso a e-distribución (Juanjo: «hazlo como dices»). Su
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
