# 115. Una descripción en cada control, también con el dedo

Fecha: 2026-10-21 · Estado: aceptado

## Contexto

Al añadir el selector «Part baixa · Part alta» de la gráfica (ADR 0096),
Juanjo pidió una descripción al pasar el ratón, porque no tenía claro que se
entendiera a la primera, y añadió: «en realidad habría que poner
descripciones por todo el programa, la mayoría de controles o botones no la
tienen». El inventario de todas las páginas y de la gráfica en grande dio
208 controles, 141 sin descripción; quitando los repetidos y los
desplegables, unos 32 distintos. Además, el `title` solo sale con el ratón:
en el móvil y la tableta nadie lo veía. La única burbuja que se abría
tocando era la de la parte alta (ADR 0087).

## Decisión

- **Mantener el dedo medio segundo** sobre un control con `title` abre su
  descripción en la misma burbuja de la parte alta (`comu.js`, `PREMUT_MS`),
  y el control no hace nada; un toque normal hace lo de siempre, y si el dedo
  se mueve (desplazar, arrastrar), no se abre. Dentro de una ventana (la
  gráfica en grande) la burbuja va en la ventana, que está por encima. Sin
  el menú del navegador ni la selección de texto en esos controles. Con el
  ratón, el `title` de siempre.
- **Cada control lleva su descripción**: las cinco pestañas (`comu.js`,
  `DESCRIPCIO_PESTANYA`), «Desplega-ho tot», el viento, la humedad y el UV de
  la gráfica, «Surto», «Torno» y cada medio de «Si surts», las ocho fichas de
  «Consultes», las casillas y los botones de «Notificacions» y la antelación
  de «Fiabilitat». Juanjo aprobó los textos en bloque. Quedan sin
  descripción los desplegables, que dicen lo que contienen, y las etiquetas
  de la parte alta, que ya abren su burbuja al tocarlas.
- **Un control nuevo lleva su descripción** desde el principio.

## Consecuencias

- Las descripciones en castellano van en `montflorit/es.js` (las de
  JavaScript) e `i18n/es.json` (las del HTML).
- La versión castellana de «Si surts» cambia «Surto» y «Torno» buscando
  `>Surto <select`, porque la etiqueta lleva ahora atributos.

## Validación

Inventario con Playwright antes y después (de 141 a 53 sin descripción, todos
desplegables o etiquetas de la parte alta); mantener el dedo emulado en
Chrome de Android y Safari de iPhone: la burbuja sale con su texto, también
sobre la gráfica en grande, y la ficha o el botón no cambian; un toque corto
cambia la ficha. `probar-web` sin errores en Chrome y Firefox; Safari sin
pantalla se cuelga en «Notificacions» también con la versión publicada antes
de este cambio. axe-core sin incidencias en claro y oscuro. El 21-10-2026,
con la 3.175.0 publicada, Juanjo lo probó en su móvil: al mantener el dedo
sale la burbuja y no el menú del sistema.
