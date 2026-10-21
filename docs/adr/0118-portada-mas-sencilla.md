# 118. Una portada más sencilla: la conclusión arriba

Fecha: 2026-10-21 · Estado: aceptado

## Contexto

Juanjo pidió «la aplicación del tiempo más sencilla y atractiva». El agente
hizo una maqueta en un lienzo de diseño (la portada actual al lado de la
propuesta, en el móvil claro y oscuro y en el ordenador). Juanjo preguntó si
la gráfica seguía teniendo sus opciones; el agente vio que en la maqueta la
había sustituido por una tira más simple, que dejaba sin ver las franjas
elegidas (viento, humedad…), y recomendó conservar la gráfica de verdad.
Juanjo pidió implementarla «con la posibilidad de volver atrás»: se hizo en
una rama aparte, enseñada en el servidor local con los datos del momento y
con una simulación de avisos. Juanjo: «me gusta, publica la portada nueva».

## Decisión

- **«Ara», destacada** (`.targeta.ara.heroi`): una tarjeta azul oscura con
  la conclusión arriba, la temperatura en grande con la parte alta al lado
  (sin el termómetro, para que quepa) y los datos en pastillas. El radar
  sigue dentro, en su recuadro.
- **La conclusión la escribe el programa** (`casa.fraseCelAra`): el cel de
  los dos tramos que vienen, con las mismas piezas de la tabla
  (`resumTrams`); si el tramo en curso solo tiene una hora, empieza por el
  siguiente; con el mismo cielo, una sola frase («Aquesta tarda i aquesta
  nit, ennuvolat.»). Debajo, la línea de lluvia de siempre
  (`liniaPlujaPrevista`, con su cuenta atrás) o «Sense pluja prevista.». Si
  llueve o el radar ve lluvia, solo el cielo: la lluvia la dice el radar. Si
  los modelos no ven lluvia pero hay aviso de lluvia o tempestades en 24
  horas (`casa.avisDePluja`), lo dice: «Els models no hi veuen pluja, però
  hi ha avís: mira'l a dalt.» (ADR 0101: lo oficial manda).
- **La riera, debajo de «Ara», solo cuando anuncia algo** (`casa.estatPortada`):
  si llueve en la cuenca o hay riesgo, con el título y el color de la página
  «Riera» (`comu.titolRiera`, `COLOR_NIVELL`, que pasan de `riera.js` a
  `comu.js` para que las dos digan lo mismo), y no si su aviso ya sale arriba,
  en «Avisos actius». Lleva a «Riera». En la 3.178.0 había además una línea
  «Ara no hi ha cap avís.» y la riera salía también sin nada que decir; en
  la 3.178.1 se quitan (Juanjo, 21-10-2026: «que solo aparezcan cuando
  anuncien algo»).
- **Los avisos activos, más visibles**: el bloque sigue plegado (ADR 0094),
  pero con el fondo y el borde del color del más grave y el título más
  grande, para no quedar a la sombra de «Ara».
- **Fuera de la portada, el resumen de texto de hoy y el de mañana**: lo
  dicen la conclusión y los tramos. Sin datos de «ara», el de hoy, como
  siempre. Se retira el código que añadía la cuenta atrás a ese resumen
  (`posaComptePluja`).
- **Los enlaces a los radares, dentro de «D'on surt»**.
- **La gráfica, igual**, con sus opciones recordadas.
- **En todo el sitio**: la letra Figtree (SIL OFL 1.1, servida desde
  `web/fonts`, sin Google; crédito en «Fonts») y las tarjetas algo más
  redondeadas, para que las demás páginas no desentonen.

## Alternativas descartadas

- **Una tira hora a hora en lugar de la gráfica**, como en la maqueta: más
  simple, pero quien había encendido una franja dejaba de verla al abrir.
- **Los avisos dentro de la tarjeta de la riera**, siempre en el mismo sitio:
  con peligro, lo primero que hay que ver es el aviso, arriba.
- **Figtree desde Google Fonts**: cada visita avisaría a Google.
- **La temperatura máxima y mínima en «Ara»**, como en la maqueta: ya las
  dicen los tramos justo debajo.

## Consecuencias

- La portada del móvil queda algo más corta (de unos 1.600 a unos 1.500 px
  con los datos del 21-10-2026); los tramos conservan su aspecto.
- La conclusión depende de los tramos: si cambia cómo se calcula el cielo de
  un tramo, cambia también la frase, y no pueden contradecirse.

## Validación

Pruebas (`test_frase_de_dalt_de_la_portada` en `test_web.py`, y la frase en
castellano en `test_montflorit.py`), Ruff y ESLint; `probar-web` de la
portada en Chromium, Firefox y WebKit, en móvil y escritorio, claro y
oscuro, con los datos del momento y con una simulación de un aviso naranja
de viento y uno amarillo de lluvia; las demás páginas en Chromium y Firefox,
móvil y escritorio; axe-core sin incidencias en todas, en los dos temas,
también con los avisos de la simulación.
