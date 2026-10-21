# 117. La vista previa al compartir un enlace (Open Graph)

Fecha: 2026-10-21 · Estado: aceptado

## Contexto

Juanjo preguntó si convenía «aplicar OG data». Las páginas solo tenían
`<title>` y `<meta name="description">`: al compartir un enlace por WhatsApp,
Telegram o las redes (el botón de compartir de la página, los grupos, los
avisos del bot que enlazan a su ficha) salía como mucho el título y un texto,
sin imagen. El agente recomendó las etiquetas Open Graph con una imagen fija
por lengua, en una versión aparte; Juanjo: «no hace falta [enseñármelo], lo
puedes aplicar todo».

## Decisión

- **`montflorit.py` (`open_graph`) añade a cada página pública** `og:type`,
  `og:site_name`, `og:title`, `og:description`, `og:url`, `og:locale` (y la
  otra lengua como `og:locale:alternate`), `og:image` con su tamaño y texto
  alternativo, y `twitter:card`. El título y la descripción se toman de la
  propia página ya traducida: nada se escribe dos veces. Las páginas sin
  descripción (fuentes, cómo funciona, privacidad) van sin
  `og:description`.
- **Una imagen fija por lengua** (`web/img/og-ca.png`, `og-es.png`, 1200 ×
  630, unos 19 KB): el icono, el nombre, qué es y la dirección.
- **Sin el tiempo del momento en la imagen**: WhatsApp y Telegram guardan la
  vista previa días, y enseñaría un tiempo caducado.
- De paso, los títulos en castellano de «Consultas», «Privacidad» y «Riera»,
  que seguían diciendo «Temps a Montflorit».

## Consecuencias

- La vista previa es la de la página: un enlace a `#grafica` o a la ficha de
  un aviso enseña la de la página que lo contiene.
- Los servicios que ya tengan un enlace guardado no lo renuevan enseguida.

## Validación

`tests/test_montflorit.py` (`test_vista_previa_en_compartir`): las etiquetas
en catalán y castellano, la dirección de cada lengua y las dos imágenes.
