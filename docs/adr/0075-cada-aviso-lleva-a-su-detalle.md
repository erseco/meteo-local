# 75. Cada aviso lleva a su detalle

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

Con la portada nueva (ADR 0074), el resumen del día decía «Trens de
Cerdanyola: R4 amb incidències, R7 amb incidències…», pero no llevaba a
ningún sitio. Juanjo: «que hay que hacer si alguien quiere saber cuales son?
se aplica lo mismo para cualquier alerta».

Cada aviso de la portada lo resolvía a su manera:

- los trenes, sin enlace;
- los incendios y el Pla Alfa, «Mapa», a webs de fuera;
- los planes, el comunicado en PDF;
- los cortes de luz, «Detall»;
- y el bloque entero, un enlace general al final, «Historial i detall a
  «Perill»».

## Decisión

Versión 3.65.0.

- **Cada línea con un detalle detrás lleva «›» a la derecha y se toca
  entera**, como en las aplicaciones del móvil. Sin palabras añadidas.
- **Siempre a una página de esta web**: los avisos de peligro (planes,
  Meteocat, incendios, Pla Alfa, cierres, riesgo previsto y AEMET), a
  «Perill»; los cortes de luz, a «Consultes › Llum»; los trenes del resumen
  del día, a «Consultes › Trens»; los avisos de la AEMET del resumen, a
  «Perill». Lo mismo en el resumen de «Consultes › Avui» y «Demà».
- **Fuera de la portada «Mapa», «Detall», el PDF y el enlace general.** Los
  enlaces externos ya están en las fichas de «Perill» (comunicado de
  Protección Civil, mapa de Bombers, Pla Alfa de los Agents Rurals) y en
  «Consultes › Llum» (mapa de e-distribución, buscador de Endesa).
- **Cómo se hace**: `ambDetall` (en `comu.js`) añade a la línea un enlace sin
  texto, con su nombre para lectores de pantalla («Detall: …»), que la cubre
  entera por debajo del texto; la «›» la dibuja el estilo (`.amb-detall`). El
  «?» de los planes queda por encima. `detallLinia` decide qué líneas del
  resumen llevan detalle y adónde.
- **Un enlace a otro punto de la misma página no se apunta en el historial**
  (la «›» de los trenes dentro de «Consultes»), para que «atrás» siga
  llevando a la portada (ADR 0074).
- **En el móvil, desplazar hasta un punto de la página deja sitio a la barra
  de pestañas** (`scroll-padding-bottom`): lo que se busca no queda detrás
  de ella. Se vio al probar: la línea quedaba debajo de la barra.

## Alternativas descartadas

- **Mantener «Mapa», «Detall» y el PDF en la portada.** Cada aviso hacía una
  cosa distinta, y había que adivinar qué se podía tocar.
- **Llevar cada aviso a su ficha exacta de «Perill»** (`perill.html#id`). Las
  fichas tienen dirección propia, pero el bloque de la portada sale de otros
  datos y habría que emparejar cada aviso con su ficha. Se deja para más
  adelante: los activos ya salen arriba en «Perill» y casi nunca hay más de
  uno o dos a la vez.

## Consecuencias

- Todas las líneas con detalle se tocan igual, y «atrás» devuelve a la
  portada.
- La portada no lleva a ninguna web de fuera desde los avisos: lo externo
  está a un toque más, en el detalle.

## Evidencia

- Con datos de prueba (un incendio, un aviso amarillo de la AEMET y un corte
  de luz inventados, sobre los datos publicados del 12-10-2026), cada línea
  lleva a su sitio.

## Riesgos y limitaciones

- Una línea nueva en el resumen del bot que empiece de otra forma no llevará
  «›» hasta añadirla a `DETALL_LINIA`.

## Validación

- Pruebas: `test_linies_del_resum_amb_detall`.
- Chromium, Firefox y WebKit a 412 px: corte de luz → «Consultes › Llum»;
  incendio y AEMET → «Perill»; trenes → «Consultes › Trens»; dentro de
  «Consultes», la «›» de los trenes cambia de consulta. Y «atrás», a la
  portada en todos los casos.
- `probar-web` (tres navegadores, móvil, tableta y escritorio, claro y
  oscuro) en «El temps», «Si surts», «Consultes», «Perill» y la portada en
  castellano, sin errores ni desbordamiento; axe-core sin incidencias.
