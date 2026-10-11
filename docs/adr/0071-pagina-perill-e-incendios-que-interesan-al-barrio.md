# 71. Página «Perill» e incendios que interesan al barrio

Fecha: 2026-10-11 · Estado: aceptado

## Contexto

La noche del 10 al 11-10-2026 llegó por Telegram y al móvil el aviso de un
incendio forestal en Montcada i Reixac, a 5,0 km (de 23:09 a 00:30). Juanjo:
«montcada, ripollet o sabadell no están en collserola; interesan los incendios
en collserola o muy cercanos aquí, no ripollet», y después: «los incendios en
cerdanyola, aunque no esté dentro de collserola, también me interesa». Con el
límite oficial del parque se comprobó que toda la parte de Montcada a unos
5 km de casa queda fuera de Collserola; Montcada sí tiene parque, desde
1,8 km de casa. Ripollet, Sabadell, Barberà y Badia no tienen.

Además, los avisos de peligro solo se veían al llegar y desaparecían. Juanjo
propuso «un botón de alertas … con incendios, desbordamiento de riera y otros
avisos de peligro, con un historial … y enlaces cuando se pueda para obtener
más información». Se aprobó, con el nombre «Perill» y no «Alertes» para no
confundirla con la campana de «Avisos al mòbil» ni con el bloque «Avisos
actius» («hazlo así»).

## Decisión

### Qué incendios avisan (`entorn.py`, `config.py`)

- **Dentro del Parc Natural de la Serra de Collserola, a cualquier distancia**
  (Juanjo: «todo el parque»). Se pregunta a la capa pública del límite del
  parque del Consorci (`Límit_Parc_de_Collserola`, ArcGIS) si el punto cae
  dentro, con `COLLSEROLA_MARGE_KM` (200 m) de margen porque la posición de la
  actuación es aproximada. Una consulta por incendio, solo para los que pasan
  los otros filtros; el límite no se copia en el repositorio.
- **En Cerdanyola, siempre**.
- **En los demás municipios del parque (`MUNICIPIS_COLLSEROLA`, los nueve del
  Consorci), solo a `ENTORN_RADI_KM` (3 km) o menos**: «incluye las
  poblaciones dentro de collserola como montcada, pero solo si son cercanas».
  Empezó en 5 km; el mismo 11-10-2026, tras recibir un incendio de Montcada
  a 4,8 km, Juanjo lo bajó: «5km es demasiado, ponlo a 3km» (3.63.1).
- Los demás, no, por cerca que estén. A Bombers se le piden los incendios de
  vegetación de la caja `INCENDIS_CAIXA`, que abarca el parque y 6 km
  alrededor de casa; siguen fuera los de vegetación urbana y los acabados.

### Cómo se dice

- Cada aviso de peligro empieza por un símbolo (Juanjo: «deben comenzar
  siempre por ese círculo rojo»; el incendio era el único que no lo llevaba).
  Los círculos, para los niveles, cada uno con su color (Juanjo: «cada uno
  con su color»; ADR 0065). Lo que no tiene nivel lleva un símbolo propio, no
  un círculo que se leería como un «nivel rojo» que nadie ha dado (Juanjo:
  «dejar los círculos para este tipo de niveles»): el incendio, 🔥 al empezar,
  con la franja roja en «Perill», y 🟢 al acabar, el extremo seguro de la
  escala. Si un día entran los rayos, irían con ⚡.
- Dentro del parque, dicho claramente en el título y en el texto (Juanjo:
  «debe decirlo claramente»): «Incendi forestal dins del Parc de Collserola
  (Molins de Rei)» y «… a Molins de Rei, dins del Parc Natural de Collserola,
  a uns 13 km de Montflorit». En Cerdanyola, «Incendi forestal a Cerdanyola
  del Vallès»; en los demás, «a prop de Montflorit: Montcada i Reixac».
  Igual en `/avisos_actius` del bot y en «Avisos actius» de la web.
- El mensaje del incendio enlaza el mapa de actuaciones de Bombers.
- Desde la 3.58.1, la distancia a Montflorit va siempre en el título, al
  empezar y al acabar, porque es lo que se ve en la notificación y en la ficha
  plegada de «Perill» (Juanjo: «tiene que poner la distancia a Montflorit,
  siempre»): «Incendi forestal a Montcada i Reixac, a 2,5 km de Montflorit».
  El texto ya no la repite.

### Página «Perill» (`web/perill.html`, `web/perill.js`)

- Pestaña entre «El temps» y «Si surts» (Juanjo: «creo que debe estar entre
  el tiempo y si sales»), icono «triangle-alert» de Lucide. En castellano,
  «Peligro». En el móvil el menú pasa a dos filas: con cuatro pestañas no
  caben en una sin quitar rótulos.
- Arriba, una explicación breve con «Nou:», y la pestaña con «Nou!», con las
  mismas reglas que la campana (ADR 0048): hasta que se entra en la página o,
  para todos, hasta el 18-10-2026, una semana. `comu.js` lo hace igual para
  las dos (`NOVETATS`).
- **Un punto rojo en la pestaña** cuando hay una situación de peligro nueva
  que no se ha visto, se tengan activados los avisos o no (Juanjo: «permanecerá
  un tiempo razonable … decide tú»): mientras está activa o hasta 24 horas
  después de empezar (`PERILL_NOU_H`), y hasta que se abre «Perill».
- Contenido: lo que está activo ahora; las situaciones acabadas de los
  últimos 30 días; los meses anteriores, plegados, uno por mes, hasta un año
  (Juanjo: «historial mensual … luego se agrupan en acordeones los meses
  anteriores, de momento hasta un año»). Cada situación, una ficha con el
  color de su círculo, el texto del aviso tal como llegó, desde cuándo y, si
  ha acabado, hasta cuándo, con 🟢 y el detalle plegado.
- Entran los avisos de peligro y de la riera: incendios, AEMET, planes de
  Protecció Civil, el tiempo excepcional que calcula la web y la riera. No
  entran la lluvia en 15 minutos ni la previsión del día.
- **Más información**, si el texto no lleva ya un enlace: Bombers (en el
  texto), el comunicado del plan (en el texto) o la página de Protecció
  Civil, la página de avisos de AEMET para Cataluña y, para la riera y el
  tiempo excepcional, que calcula la web, su apartado de la metodología.
- «Avisos actius» de «El temps» enlaza «Perill» para ver el historial.
- Tocar la notificación de un aviso de peligro o de la riera abre «Perill»
  (`bot/push.py`); la de lluvia sigue abriendo la página del tiempo.

### Avisos de Meteocat sin plan y Pla Alfa

Juanjo preguntó si quedaba algún peligro sin tener en cuenta; se le
propusieron dos y aprobó los dos («de acuerdo, hazlo así»):

- **Avisos de peligro de Meteocat** para el Vallès Occidental: antes solo se
  leían con un plan de Protecció Civil a la vista (ADR 0067), y Meteocat los
  emite mucho más a menudo; un aviso alto de Meteocat con AEMET en amarillo y
  sin plan no se veía. Ahora `smp.py` se lee en cada pasada y se tratan como
  los de AEMET: aviso al aparecer o al subir de grado (la clave es el
  meteoro y su primer día, para que una nueva emisión no cuente como aviso
  nuevo; la primera vez solo se apuntan), ficha en «Perill» hasta el final
  de su última franja, enlace a la predicción general de meteo.cat, y, sin
  plan, su línea en «Avisos actius» de la web y en `/avisos_actius`. El
  meteoro y el umbral, en catalán también en castellano (ADR 0067).
- **Pla Alfa de Cerdanyola desde el nivel 3 y cierres de Collserola**: solo en
  «Ara» de «Perill», sin aviso, sin historial y sin punto rojo, porque cambia
  cada día (ADR 0046); la ficha lo dice: «El fixen cada dia els Agents
  Rurals; no arriba com a avís». `avisos.json` lleva `pla_alfa`.

### Datos (`avisos_bot.py`)

- Cada aviso de peligro y de la riera lleva `episodi` (de qué suceso es) y,
  si hace falta, `enllac` y `fins` (los de AEMET no tienen mensaje de final:
  acaban a su hora). `historial` agrupa los avisos por suceso: el primero lo
  abre, los siguientes actualizan el texto y se quedan el peor nivel, y el
  final lo cierra. Un plan que deja de mostrarse (ADR 0062) se cierra.
- Se guarda `HISTORIAL_DIES` (366) días en el estado y va en `avisos.json`,
  que ya se publica en IONOS (la página lo lee de allí) y que, desde ahora,
  va también en la copia de GitHub, la reserva de la web.
- El NAS y la reserva de IONOS llevan estados distintos: cada uno une su
  historial con el del último `avisos.json` publicado (`fusiona`), para que el
  que vuelve a publicar no borre lo que el otro vio mientras tanto.

## Alternativas descartadas

- **Quitar de «Perill» los avisos de AEMET y de Protecció Civil**, que ya
  salen arriba de «El temps» y de «Si surts» mientras están activos (Juanjo lo
  planteó): se quedan. Sin ellos el historial quedaría cojo, «Ara» podría
  decir que no hay peligro con un aviso rojo activo y la notificación llevaría
  a una página sin su aviso. Juanjo: «déjalo como está».

- **Un círculo rojo para todos los avisos de peligro**: el color dice el
  nivel desde el ADR 0065; Juanjo prefirió «cada uno con su color».
- **⚠️ para lo que no tiene nivel**: en «Perill» todo es peligro y solo diría
  «sin nivel»; 🔥 dice qué pasa antes de leer.
- **El historial dentro de `montflorit.json`**: se escribe antes que los
  avisos y la reserva de IONOS no lo regenera; `avisos.json` ya está donde
  hace falta.
- **Copiar el límite del parque en el repositorio**: la capa no declara
  licencia y el Consorci la mantiene (editada el 09-10-2026); se consulta.
- **Señal de peligro nuevo solo para quien no tiene avisos**: Juanjo la quiere
  «independientemente de las alertas recibidas».

## Riesgos

- La capa del límite de Collserola, como las de Bombers, es la de un visor,
  no un conjunto de datos documentado: si falla, falla la parte de incendios
  (`None` y un error), como ya pasaba con Bombers.
- Los nombres de municipio de Bombers se comparan sin distinguir mayúsculas;
  si Bombers escribe uno de otra manera («Papiol, el»), ese municipio solo
  avisaría dentro del parque.
- La fecha del «Nou!» (18-10-2026) supone publicar el 11-10-2026: si se
  publica más tarde, hay que moverla.

## Validación

- `tests/test_entorn.py`: qué incendios interesan (Ripollet y Badia no;
  Montcada a 2,5 km sí y a 3,8 km no; Molins de Rei dentro del parque sí;
  Cerdanyola sí), el 🔥, el enlace a Bombers y el texto del parque.
- `tests/test_historial.py`: comienzo y final en una entrada, subida de nivel,
  episodio nuevo tras uno acabado, plan oculto que se cierra, un año, y la
  unión con el historial del otro servidor.
- `tests/test_web.py`: «Nou!» de la campana y de «Perill» con sus fechas;
  `tests/test_push.py`: la riera abre «Perill».
- `tests/test_smp.py`: Meteocat sin plan en `/avisos_actius`, sin la línea de
  «no hay aviso»; aviso a la segunda pasada, una sola vez, de nuevo al subir
  de grado, y sin cambios si Meteocat no responde.
- Capa del parque comprobada el 11-10-2026: casa, a 20 m del límite; un punto
  de Collserola en Barcelona, dentro; Montcada a 5 km, fuera.
- Web con un historial de ejemplo hecho con los textos reales (incendio activo
  en Collserola, aviso amarillo de AEMET, incendio de Montcada acabado, riera,
  plan INUNCAT y dos de agosto) en Chromium, Firefox y WebKit, escritorio,
  móvil y tableta, claro y oscuro, en catalán y castellano; axe-core sin
  incidencias en «Perill» y en «El temps».
