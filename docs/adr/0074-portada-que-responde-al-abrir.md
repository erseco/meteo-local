# 74. Portada que responde al abrir

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

Juanjo pidió analizar si la información de Temps a Montflorit se obtiene con
facilidad: «que fuese una app que solo de abrirse ya se ve lo que uno quiere
… clara, completa y realmente útil, sin tener que abrir ventanas ni enlaces».
Después añadió: «quiero una aplicación fácil de usar y ver lo que interesa,
sin tener que descifrar cifras, textos, etc.».

El examen de la versión 3.63.1 en el móvil (un informe de trabajo y dos
revisiones independientes de Codex, del mismo día, no publicados) encontró:

- La cabecera ocupaba un tercio de la primera pantalla del móvil.
- El resumen del día existía, pero solo en «Consultes › Avui».
- La etiqueta «Mode vigilància (pluja al radar)» salía junto a «No plou» y
  «Serè», y quien no conocía la web no sabía qué se vigilaba.
- La pestaña «Perill» llevaba un punto rojo durante 24 horas aunque el
  peligro hubiera acabado, al lado de «Ara no hi ha cap situació de perill».
- En «Si surts», la respuesta quedaba debajo de los selectores.
- Los cortes de luz del barrio solo estaban en «Consultes › Llum».
- De madrugada, «Demà» solo llegaba a las 7 h.

## Decisión

Versión 3.64.0.

- **Resumen del día bajo «Ara»**, en «El temps»: el mismo texto de
  «Consultes › Avui» (hecho en el servidor por `bot.resum`), sin la línea
  «Ara mateix», que ya es la tarjeta de encima, y sin la de la ropa, que es
  cosa de «Si surts» (Juanjo: «lo de la ropa en pantalla principal, no es un
  poco frivolo?»). Desde las 18 h (`HORA_DEMA`, la del bot) sale también el
  de mañana. Las funciones que dibujan esos textos pasan de `consultes.js` a
  `comu.js`.
- **Tarjeta «Ara» más corta**: la humedad y la presión, juntas en una línea
  pequeña; el viento sin la estación ni la hora, que van en «D'on surt». Si
  el viento viene de las estaciones vecinas (ADR 0064, aún no activado), se
  dice en la tarjeta, porque «D'on surt» todavía no lo cuenta.
- **Una sola invitación a los avisos en la portada**: «Per rebre la
  previsió cada dia i saber quan plourà uns 15 minuts abans, activa els
  avisos», bajo el resumen. Junta las dos que pedía el ADR 0072 (cada
  apartado con aviso configurable dice cómo activarlo). Sin resumen (la
  página de casa, `casa.json`, no lo lleva), vuelve a la tarjeta «Ara».
- **Sin «Mode normal» ni «Mode vigilància»**: queda «Actualitzat a les … ·
  propera: …», y un «?» que explica cada cuánto se actualiza la página y por
  qué (`textActualitzacio`). El modo sigue existiendo en el servidor (ADR
  0010); solo deja de mostrarse con nombre.
- **Las pestañas, en una barra fija abajo en el móvil** (hasta 40 rem de
  ancho), como en las aplicaciones, y sin la línea de debajo del título. En
  pantallas anchas, todo sigue arriba como antes.
- **«Atrás», como en una aplicación** (Juanjo: «al ir hacia atrás fuese a la
  pagina principal y si pulso otra vez, entonces se sale de la app»): de la
  portada a otra página el navegador lo apunta; entre las demás, la nueva
  sustituye a la anterior (`location.replace`); volver a la portada desde
  otra página es `history.back()` si se venía de ella. El cambio de idioma
  tampoco se apunta. Quien entra por un enlace a otra página (un aviso
  compartido) sale con «atrás». `comNavega` decide; una marca en
  `sessionStorage` dice a la página nueva que se venía de la portada.
  **Corregido por el ADR 0076**: una página de explicación abierta desde una
  pestaña sí se apunta, para que «atrás» vuelva a ella.
- **Punto rojo de «Perill», solo con un peligro activo** sin ver. Corrige el
  ADR 0071, que lo mantenía 24 horas desde el inicio (`PERILL_NOU_H`, que
  desaparece). Juanjo preguntó por un punto verde para los ya pasados; se
  descartó: un punto en una pestaña pide mirar algo, el rojo y el verde se
  confunden con daltonismo, y el historial ya está en «Perill».
- **En «Perill», lo acabado en gris**: franja y título sin el color del
  nivel, que queda para lo que pasa ahora.
- **«Si surts» responde arriba**: bajo los selectores, una línea con los
  medios que van bien («Bé: a peu, bici o patinet, moto i cotxe.» o «Bé en
  tots els mitjans.») y una por cada uno de los demás, con su motivo. Cada
  medio conserva su veredicto. Los botones para elegir medios, que se
  recuerdan, quedan plegados en «Mitjans: 5 de 5», desde la 3.72.2 «Tria els mitjans (5 de 5)»: con el rótulo anterior, Juanjo, con medios quitados, creyó que ya no se podían marcar.
- **Cortes de luz del barrio en «Avisos actius»**, en «El temps» y «Si
  surts»: dentro o en el límite del barrio, con clientes, horas y calles
  estimadas (dicho así), y «Detall» a «Consultes › Llum». No llevan el
  enlace al historial de «Perill», que no los guarda. **Desde el ADR 0075**,
  cada aviso lleva «›» a su detalle, sin «Detall» ni enlace general.
- **Los tramos de la previsión, plegados de entrada**, salvo los que tienen
  aviso o fenómeno: el resumen del día ya dice lo que viene, y así se ven
  juntos mañana, tarde y noche. Corrige el ADR 0041, que abría el primero.
- **«Demà» entero también de madrugada**: la tabla llega siempre a las 21 h
  del día siguiente del calendario (`casa.previsio`). Antes, de 0 a 7 h,
  «mañana» era el día del tramo en curso y «Consultes › Demà» llegaba solo a
  las 7 h. Ahora son entre 24 y 45 filas.
- **Una cifra si la mínima y la máxima coinciden**: «16 °C», no «entre 16 °C
  i 16 °C» (`bot.text_temperatura`).

## Alternativas descartadas

- **Mostrar el estado de la R4 como «servei alternatiu per carretera»**
  (segundo informe de Codex). El aviso de carretera que llevaba la R4 era
  uno general de Rodalies para 19 líneas, del 06-10-2026 a las 17:13, sin
  retirar, y se veían trenes de la R4 circulando. «Amb incidències» era lo
  correcto.
- **Aire, polen, UV y sol en la portada** (los dos informes de Codex). Son
  más niveles y cifras para todos cuando interesan a unos pocos: siguen a un
  toque en «Consultes».
- **Dos columnas en el ordenador**. En el ordenador ya cabe todo en una
  pantalla, y añadirían complejidad sin ganar nada.
- **Una miniatura del radar en la portada**. Coste medio (recorte, cita de
  Meteocat, peso) y el recuadro del radar ya avisa cuando se acerca lluvia.
- **Decir la distancia de la lluvia del radar** en lugar del modo. Los datos
  no la llevan, y si la lluvia no se acerca, la portada no dice nada (Juanjo,
  10-10-2026: «si no anuncia nada como ahora mejor que no salga»).

## Consecuencias

- La primera pantalla del móvil enseña el tiempo de ahora y el resumen del
  día. Con avisos activos, estos van primero y el resumen baja.
- La portada y «Consultes › Avui» dicen lo mismo, porque salen del mismo
  texto del servidor.
- La tabla de previsión tiene hasta 45 filas de madrugada. Los riesgos y el
  registro siguen con las 24 primeras.
- La página privada de casa (`casa.html` con `casa.json`) no tiene resumen
  ni cortes de luz: esos datos solo están en los públicos.

## Evidencia

- Datos publicados del 12-10-2026 a las 05:30 y a las 05:45
  (`bilateria.org/app/meteo-local/montflorit.json`): 26 filas que acababan
  el 13-10 a las 07:00; «Consultes › Demà»: «(fins a les 7 h) Temperatura:
  entre 16 °C i 16 °C».
- Avisos de Rodalies leídos con `trens.avisos_renfe()` el 12-10-2026: el de
  «Servei alternatiu per carretera en tot el seu recorregut» para R4 es
  general, de 19 líneas, con inicio el 06-10-2026 a las 17:13.
- `casa.previsio` con el código nuevo, el 12-10-2026 a las 06:33: 39 filas,
  hasta el 13-10 a las 21:00.

## Riesgos y limitaciones

- La barra inferior va justa a 320 px de ancho: cabe, sin desbordar.
- «Atrás» depende de `sessionStorage`; si el navegador no lo permite, la
  navegación vuelve a ser la de siempre (cada página se apunta).
- iPhone sin probar en un aparato real; sí en WebKit.

## Validación

- 391 pruebas en verde, con nuevas para el punto de «Perill», el resumen de
  la portada, los cortes de luz, el resumen de «Si surts», «atrás» y la
  previsión de madrugada.
- `probar-web` en Chromium, Firefox y WebKit, en móvil, tableta y escritorio,
  con tema claro y oscuro, en catalán y castellano: sin errores de
  JavaScript ni desbordamiento. Los únicos avisos son los de leer IONOS desde
  `localhost`, que no lo permite: la página usa entonces la copia local.
- 320 y 360 px en Chromium y Firefox, en las páginas principales en catalán
  y castellano: sin desbordamiento y con las pestañas enteras.
- «Atrás» en Chromium, Firefox y WebKit: tras Perill → Si surts → Consultes
  → Perill, atrás lleva a la portada y otra vez, fuera; la pestaña «El
  temps» hace lo mismo; el idioma no se apunta.
- axe-core (WCAG 2.1 AA y buenas prácticas) sin incidencias en siete páginas,
  en claro y oscuro, en móvil y escritorio.
- Juanjo lo probó en su móvil con un servidor local, con datos reales y con
  datos de prueba (un incendio activo y un corte de luz inventados).

## Ampliación del 12-10-2026 (3.70.1): el selector de idioma, sin icono

Juanjo preguntó si hacía falta el símbolo de idioma delante de «CA ES». No:
el selector, con la lengua elegida resaltada, se entiende solo, y el icono
ocupaba unos 30 px en la botonera del móvil. Fuera el icono (`montflorit.py`,
`selector_idioma`), y el selector, un poco separado de los botones de acción
(`margin-right`). El grupo sigue llamándose «Idioma» para los lectores de
pantalla.

