# 91. Los planes de Protección Civil en prealerta, con ficha en «Perill»

Fecha: 2026-10-15 · Estado: aceptado

## Contexto

El 15-10-2026 la portada mostraba en «Avisos actius» «Protecció Civil: pla
d'inundacions (INUNCAT) en fase de prealerta». Al tocarla, llevaba a «Perill»,
que decía «Ara no hi ha cap situació de perill». Juanjo: «si hago clic me lleva
a la sección de avisos y me dice que ahora no hay nada. Si hay algo debería
salir con un enlace para ampliar la información si es que existe».

La causa: «Perill» (ADR 0071) se construye con el historial de los avisos
enviados, y la prealerta no envía aviso (ADR 0051), así que no tenía ficha. El
comunicado de Protección Civil en PDF, que viene en los datos (`comunicat`),
tenía que verse en esa ficha (ADR 0075) y no salía en ningún sitio. La línea
del plan llevaba además a `perill.html` sin más, no a su ficha, también en
alerta o emergencia.

## Decisión

- `avisos_bot.py` añade a `avisos.json` los planes en prealerta que muestra la
  web (`plans_prealerta`: plan, nombre, fase, desde cuándo, motivo y
  comunicado), sin avisar ni guardarlos en el historial, como el Pla Alfa.
- «Perill» les hace una ficha en «Ara», con la franja de la prealerta: el
  título de la portada, «Actiu ara · Des de…», que la prealerta no llega como
  aviso, qué quiere decir la fase, el motivo tal como lo publica Protección
  Civil (en catalán también en la página en castellano) y el enlace
  «Comunicat de Protecció Civil (PDF)»; sin comunicado, la página de Protección
  Civil. Con el botón de compartir de las demás fichas. Su dirección es fija
  por plan (`perill.html#pla-inuncat`).
- La línea del plan en la portada lleva a su ficha: en prealerta, esa; en
  alerta o emergencia, la del episodio abierto en el historial (`idFitxa`); si
  aún no se ha leído el historial, la ficha fija.
- Con un plan en prealerta, «Perill» ya no dice que no hay nada.

## Consecuencias

- La prealerta sigue sin avisar al móvil ni a Telegram (ADR 0051): solo se ve
  en la web.
- No queda en el historial: cuando acaba, la ficha desaparece de «Ara».

## Cómo se validó

- Pruebas: `plans_prealerta` en `avisos.json` (solo prealerta y solo esos
  campos) y la dirección de la ficha calculada en la portada, con Node.
- En local, con los datos del 15-10-2026: de la portada a la ficha en catalán
  y castellano, en Chromium (móvil) y Firefox (ordenador), sin errores de
  JavaScript; el enlace abre el comunicado del día. axe-core sin infracciones
  en «Perill» y en la portada.
