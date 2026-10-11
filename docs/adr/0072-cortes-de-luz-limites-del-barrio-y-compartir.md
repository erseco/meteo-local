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

- **No hay un límite oficial**: lo dice el Ayuntamiento. La moción que el
  Pleno aprobó el 26-03-2026 (exp. 177/2026/0022) empieza por «La delimitació
  dels barris de Cerdanyola del Vallès ha tingut històricament una manca de
  planificació i delimitació oficial» e insta a crear una comisión que la
  redacte; el último reparto, informal, fue el del AMB en 2016 (22 barrios).
  En OpenStreetMap, Wikidata y la Enciclopèdia Catalana Montflorit es un
  punto.
- **Lo que hay publicado** (revisado el 11-10-2026), de más a menos útil:
  - El «Mapa de barris» (figura 11) del diagnóstico del Pla Local d'Adaptació
    al Canvi Climàtic (2023, en Participa311, proceso «paesc»), tomado del Pla
    Local d'Habitatge de 2021, con la nota «No existeix una delimitació
    aprovada de barris». Dibuja Montflorit como el contorno de este ADR: la
    parte urbana de Collserola y, al otro lado de la riera, hasta el límite con
    Sant Ramon, entre Parc Tecnològic y Guiera. Diferencia posible, sin
    confirmar por la resolución de la imagen (979 px): deja fuera un entrante
    al este, junto a la riera, con un rótulo de tres líneas que podría ser el
    poblado de Ca n'Oliver. La memoria del Pla Local d'Habitatge (seu-e.cat)
    no trae ese mapa: trabaja por cuatro zonas grandes.
  - El «àmbit estadístic» 0826601 Montflorit del AMB (2020, propuesta de
    ámbitos estadísticos metropolitanos, p. 58): suma de secciones censales,
    acaba en la riera e incluye todo Collserola del término. No sirve.
  - Las secciones censales 10 y 11 («aprox. Montflorit - Can Cerdà», flaixos
    electorales del Ayuntamiento); la 011 acaba en la riera e incluye el
    bosque. No sirven.
- **El contorno vigente (11-10-2026, tarde): el del mapa de barrios del
  PLACC**, el único dibujo municipal, calcado sobre él y retocado por Juanjo en
  el editor con ese mapa superpuesto. Es un solo polígono: la parte urbana de
  Collserola y, al otro lado de la riera, hasta el carrer de Santa Rosa, entre
  Parc Tecnològic y Guiera.
- **Más el recinto del poblado ibérico de Ca n'Oliver**, con 8 m de margen
  (contorno de OpenStreetMap). El mapa del PLACC lo dibuja (la mancha oscura
  junto al barrio) pero la línea del barrio pasa por fuera, porque sigue la
  parte construida, como el Pla Local d'Habitatge del que sale. Las fuentes lo
  sitúan en Montflorit: la página de patrimonio del Ayuntamiento («situat en un
  turó de la serra de Collserola, al barri de Montflorit»), el folleto del
  museo («Carrer de València, 19 (Montflorit)») y la ficha del Parc Natural de
  Collserola («in the Montflorit neighbourhood»). Estar dentro del parque no lo
  excluye del barrio. Solo el recinto: el resto del turó se queda fuera, como
  en el mapa (Juanjo: «has incluido más de lo que se ve»).
- **Antes (mañana del 11-10-2026)**: la zona residencial de OpenStreetMap (way
  346465228) más la parte del otro lado de la riera, que confirmaban la Festa
  Major de Montflorit 2022 (actos en el «Carrer Àngel Guimerà (Chopos)» y en el
  Col·legi Turó de Guiera) y la Viquipèdia («finques de pisos baixos a la zona
  del Passeig dels Pollancres»), retocada a mano por Juanjo. Se sustituyó al
  encontrarse el mapa del PLACC.
- **El editor** (`eines/limits.py`) abre el mapa, guarda en un borrador
  (`eines/limits-esborrany.geojson`) que la web no usa y, con `aplica`, lo
  pasa a `montflorit-limits.geojson`. Cambiar los límites no cambia la
  versión: son datos.
- **Mapa de referencia superpuesto** (`--fons IMATGE S,O,N,E`; Juanjo:
  «hazlo editable … solo el azul actual y el del pdf para superponer»): una
  imagen ya reproyectada a esos límites, con una casilla para mostrarla u
  ocultarla. La imagen no se guarda en el repositorio, que es público: el mapa
  del PLACC es del Ayuntamiento. Para el PLACC se situó ajustando su contorno
  municipal al de OpenStreetMap (relación 346442), con unos 8 m por píxel; la
  riera de los dos mapas coincide.
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

### Enlace para activar los avisos (3.61.0)

Lo que Juanjo pedía con «todos los avisos que tengan una alerta configurable
(como la luz) deben tener un enlace, como ya has hecho con la pestaña
peligros» era esto (la 3.60.0 lo entendió como el enlace dentro de cada
mensaje, que se queda): cada apartado con un aviso configurable dice cómo
activarlo, como «Perill» («Per rebre'ls al moment, activa els avisos»), con el
enlace a «Avisos». «Llum» (talls de llum), «Avui» y «Demà» de «Consultes» (la
previsió de cada dia) i la targeta d'ara d'«El temps» (la pluja 15 minuts
abans), en letra pequeña bajo el contenido.

### Mapa de los límites en la web (3.63.0)

Juanjo: «me gustaría ponerlo en la página para que se vean los límites … además
habría que poner las fuentes».

- **En «Com funciona»**, sección «El barri» (`#barri`), tras «Què ofereix»:
  qué es el barrio para la web, que no hay límites oficiales y para qué
  sirven (los cortes de luz, dentro o a menos de 150 m). «Llum» enlaza a ella
  («Què compta com a barri: el mapa dels límits»). No va en «Llum» mismo: es
  una consulta que se mira deprisa.
- **Un dibujo propio en SVG** (`web/img/montflorit-limits.svg`, 55 KB), hecho
  con `eines/mapa_barri.py` a partir del contorno y de las calles, la riera y
  el verde de OpenStreetMap, con los nombres de los barrios vecinos, escala,
  norte y «© OpenStreetMap». Se amplía con el visor de imágenes. Se descartó
  un mapa interactivo con teselas de OpenStreetMap: la web pediría datos a
  servidores de fuera cada vez que alguien la abre, y hoy no pide ninguno
  (página «Privacitat»). El mapa es claro también con el tema oscuro, como un
  plano impreso.
- **Las fuentes, en «Fonts i crèdits»**, con enlace a cada una: la moción del
  Pleno, el PLACC en la dirección estable de cerdanyola.cat (la de
  Participa311 caduca), la página de patrimonio del Ayuntamiento y la ficha
  del Parc Natural de Collserola en catalán.
- Validado: pruebas, `probar-web` (Chromium, Firefox y WebKit; escritorio,
  móvil y tableta; claro y oscuro) sin errores propios ni desbordamiento,
  axe-core sin incidencias en «Com funciona» (ca y es), «Fonts» y «Llum», y el
  visor abre el mapa en Chromium y Firefox.

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
