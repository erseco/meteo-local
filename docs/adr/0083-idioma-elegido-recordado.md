# 83. Idioma elegido, recordado

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

La web instalada y la app de Android (ADR 0082) abren siempre el inicio en
catalán (`start_url` del manifiesto). Quien la usa en castellano tenía que
pulsar «ES» cada vez. Juanjo: «que abra en catalán y recuerde el idioma
elegido, en la web también».

## Decisión

Versión 3.74.0.

- **Al pulsar «CA» o «ES»** en el selector, `comu.js` guarda el idioma en el
  dispositivo (`localStorage`, `meteo.idioma`).
- **Al abrir cualquier página pública**, un guion corto en su `<head>`
  (`IDIOMA_RECORDAT`, que `montflorit.py` pone tras los enlaces `hreflang`)
  mira el idioma guardado y, si no es el de la página, la cambia por la misma
  página en el otro idioma con `location.replace`, antes de pintarla y sin
  añadir un paso al historial. Conserva la consulta y el ancla de la
  dirección (`?…#…`), para que un enlace compartido lleve a lo mismo.
- **Sin elegir**, nada cambia: el inicio, también el de la web instalada y el
  de la app, sale en catalán, y un enlace a una página en castellano se abre en
  castellano.
- La app no se toca: abre la web, y la web hace lo demás. La app comparte con
  Chrome lo guardado en el dispositivo, así que el idioma elegido en uno vale
  para el otro.

## Alternativas descartadas

- **Seguir el idioma del móvil**: Juanjo quiere el catalán por defecto, y un
  móvil en castellano no dice qué prefiere quien lo usa en Montflorit.
- **Guardar el idioma también al entrar por un enlace en castellano**: quien
  recibe un aviso compartido en castellano no ha elegido nada; solo cuenta el
  selector.
- **Hacerlo en `comu.js`**, al final de la página: se vería un instante la
  página en el otro idioma antes de cambiar.

## Validación

- `test_en_castella` (en `test_montflorit.py`): todas las páginas públicas, en las
  dos lenguas, llevan el guion después de los `hreflang`, y `comu.js` guarda la
  elección.
- Playwright en Chromium, Firefox y WebKit con la web construida en local
  (12-10-2026): sin elegir, `/` en catalán y `/es/sortir.html` en castellano;
  tras pulsar «ES», `/` lleva a `/es/` y `/consultes.html?q=trens#x` a
  `/es/consultes.html?q=trens#x`; tras pulsar «CA», `/es/` lleva a `/`.
