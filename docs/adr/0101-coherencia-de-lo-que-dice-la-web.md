# 101. Coherencia de lo que dice la web: un solo estado de la lluvia, reglas fijas y un revisor con IA

Fecha: 2026-10-18 · Estado: aceptado

## Contexto

En unos días Juanjo encontró varias contradicciones que nadie había visto y
que ninguna prueba detectaba:

- la ficha de Meteocat en «Perill» seguía diciendo el domingo «Observat ara…
  dissabte 17 de 19 a 22 h» (ADR 0092);
- el radar decía «Pluja a sobre» mientras ninguna estación medía lluvia («lo
  decía el radar: lluvia encima, pero no había»);
- una cuenta atrás de lluvia convivía con una hora «sense pluja».

Juanjo: «no debería comprobar la coherencia de todo lo que se anuncia en la
web? … puede haber incoherencias de otro tipo que no te he dicho o que
todavía no hemos detectado. la ia debe estar atenta a ellas, también cuando
se mandan las previsiones, alertas, etc. hazlo todo».

Un inventario del código (todo lo que la web y el bot afirman, de dónde sale
cada cosa y qué pares pueden contradecirse) dio 25 pares y dos fallos claros.
La causa común: cada bloque decide con sus propios datos y sus propios
umbrales.

## Decisión

### 1. Un solo estado de la lluvia (`casa.estat_pluja`)

`pluja_ara` se calcula una vez en el NAS: `plou` (alguna estación del barrio
que cuenta ha medido lluvia en los últimos 15 minutos), `radar_sobre` (el
radar la pone encima, llegada en 5 minutos o menos o ya pasada, y ninguna
estación la mide), `arriba` y `possible` (el radar la ve venir, 50 % y 20 %)
o `no`. Manda lo medido, luego el radar, luego el modelo. De él salen el
recuadro del radar de la portada y del bot, que con `radar_sobre` dice «Pluja
a sobre segons el radar · cap estació del barri no en mesura». Las tres
primeras horas de la tabla se ajustan a él (`ajusta_hores`): si el radar la
pone encima o la ve llegar dentro de una hora, esa hora no puede decir «sense
pluja». Esto vale también con la previsión anterior, que no llevaba el
radar.

### 2. Lo que se arregla del inventario

- **Fallos**: los riesgos propios no se cerraban nunca (`avisos_bot` miraba
  `ara`, que no existe; los que llevaban días abiertos se cierran sin avisar);
  la web y el bot decían «llindars de l'AEMET» y los umbrales son de Meteocat
  desde el 16-10-2026.
- **Radar**: si llueve encima, no sale «la més propera»; la lluvia de la
  tabla que solo viene de la que acaba de caer (persistencia) no se presenta
  como «pluja que el radar encara no veu»; «Plou» no va con «0 mm avui»; la
  nota «els models no veuen aquesta pluja» usa la lluvia del barrio
  (mediana), la misma que «Ara».
- **Fechas**: los avisos de AEMET dicen el día («Des del dilluns 19…»), no
  «demà», porque la ficha se relee otros días. Una ficha de un aviso que aún
  no ha empezado dice «Previst · Comença …», no «Actiu ara» (`comenca`).
- **Umbrales y palabras, una sola regla**: la intensidad del aviso de lluvia
  usa las franjas de AEMET del radar (2, 15, 30 y 60 mm/h; antes, «forta»
  desde 4); las etiquetas del tramo «ratxes» y «calor», los umbrales del
  riesgo propio (más de 72 km/h y de 36,8 °C; una prueba lo comprueba); la
  nieve, con un decimal y redondeada (no «0 cm»); el riesgo «Pluja intensa
  prevista» y las etiquetas «pluja forta / torrencial» solo cuentan las horas
  en que puede llover (20 % o más) y, si ninguna llega al 50 %, dicen la
  probabilidad.
- **Si surts**: el temps violent de Meteocat cuenta como las tormentas; «ni el
  radar… hi veuen pluja» solo si el radar de verdad no ve nada; por debajo del
  20 %, donde la tabla dice «sense pluja», «poca probabilitat de pluja» en vez
  de «pot ploure» (el umbral aprendido no cambia, ADR 0069); «Sense pluja ni
  vent fort a l'anada ni a la tornada» en los vehículos, que solo miran esas
  horas; y, como con los planes de Protecció Civil, se dice que el consejo no
  tiene en cuenta el peligro de la riera ni un incendio cercano.
- **Resumen del día**: la lluvia de 0 a 6 h de la tarjeta de hoy es «De
  matinada» («Aquesta nit» del resumen de mañana va de 18 a 6 h); la
  temperatura «d'aquí a mitjanit» incluye la medida ahora.
- **El bot**: «no plou» ya no va con un icono de lluvia.

Se dejan, con su motivo: la hora en que pararía la lluvia (radar, en
entrenamiento, ADR 0049) frente a la persistencia de la tabla, que es
estadística y está validada; los ecos débiles que ponen el modo vigilancia
(pendiente de decidir con un mes de datos, a partir del 07-11-2026); los
umbrales aprendidos de «Si surts» (ADR 0069), y el plan de Protecció Civil
oculto por no tener motivo meteorológico (ADR 0062).

### 3. Reglas fijas y revisor con IA (`revisor.py`)

En el NAS, tras cada publicación y aparte del reloj:

- **Reglas fijas** (`regles`), sin IA, en cada pasada: ninguna ficha abierta
  habla de horas pasadas, «Observat ara» solo con la observación vigente, la
  hora en curso dice «Plou ara» si llueve, y las páginas no dicen «No plou» y
  «Pluja a sobre» sin aclarar que es el radar.
- **El revisor** (Claude, `C.REVISOR_MODEL` = `claude-sonnet-5-5`, con el
  Claude Code y el token del contenedor; una sola respuesta, sin
  herramientas) se despierta solo cuando: ha salido un aviso a los vecinos;
  es la hora de los resúmenes (05:50, antes de los de 6, 7 y 8, y 20:50, antes
  del de mañana); falla una regla nueva, o cambia lo que concluye la web
  (llueve o no, el modo, los avisos y sus niveles, las fichas abiertas), como
  mucho cada 30 minutos (`C.REVISOR_MIN_MIN`). Lee las páginas ya dibujadas
  (portada, «Si surts» y «Perill», con Chromium sin pantalla y los datos que
  se acaban de publicar), el resumen del bot, los últimos avisos y los datos
  medidos y oficiales, y dice qué es falso, caducado o contradictorio. Se le
  pasa lo que ya ha contado los dos últimos días, para que no lo repita.
- **Qué hace con lo que encuentra** (Juanjo, 18-10-2026: «me parece bien»):
  - corrige solo lo que únicamente quita líneas de una ficha o de un aviso
    enviado (`treu_linies`); lo comprueba el código, no la IA. La corrección
    vive en `correccions.json`, `avisos_bot` la aplica en cada pasada mientras
    el texto siga siendo el corregido, y el bot edita los mensajes de Telegram
    de las últimas 48 horas (`bot.corregeix`). Los avisos al navegador ya
    llegados no se pueden corregir. El reloj publica en el minuto siguiente;
  - lo demás (cambiar un texto, cerrar una ficha) se lo pregunta a Juanjo con
    botones (Aplicar / Dejar); nunca inventa un aviso ni envía nada a los
    vecinos;
  - avisa siempre a Juanjo por el bot de los agentes: un mensaje por cada
    corrección, con «Deshacer»; uno por revisión con lo grave y lo medio que
    hay que arreglar en el código; lo leve, al registro
    (`registre/revisor.jsonl`, `revisor.py estat`).

## Alternativas descartadas

- **Que la IA escriba los avisos**: los avisos de peligro tienen que salir en
  el momento y siempre igual; los errores encontrados no eran de entender el
  texto oficial, que llega con datos estructurados, sino del manejo propio.
- **Que la IA corrija sin límites**: una corrección equivocada que quite un
  aviso vigente hace más daño que una línea caducada.
- **Una revisión en cada pasada**: con la lluvia, decenas al día; con los
  desencadenantes, unas pocas, y en épocas secas, casi solo las de los
  resúmenes.

## Consecuencias

- Coste: una revisión tarda de 50 a 75 segundos y gasta lo equivalente a unos
  0,35-0,40 USD de la API (va con la suscripción del token). Con dos al día y
  las de los avisos y cambios, de 2 a 10 al día según el tiempo.
- `nas/reloj.sh` cambia: hay que copiarlo al NAS y reconstruir el contenedor.
  `publica.sh` deja `avisos.json` junto al estado para el revisor.
- El bot guarda el número de cada mensaje de aviso que envía (sin más datos,
  y lo borra a los 3 días con el aviso) para poder corregirlo.

## Evidencia

- 18-10-2026 a las 6:40: Meteocat aún daba las franjas del sábado en el aviso
  vigente; la ficha decía «Observat ara».
- Inventario del código del 18-10-2026: 25 pares que pueden contradecirse y
  los dos fallos, comprobados en el código (`avisos_bot.py`, `casa.py` no
  escribe `ara`; `config.py`, umbrales de Meteocat).
- Revisión de prueba con los datos de las 7:14 (antes de los arreglos):
  encontró, entre otras cosas, las fichas cerradas de AEMET con «demà»; la de
  las 7:40, «Actiu ara» en avisos que empiezan el lunes. Las dos, corregidas.
  También dio dos falsas alarmas (la barra vertical de la tabla y la franja
  del resumen), explicadas ahora en sus instrucciones.

## Riesgos y limitaciones

- La IA puede equivocarse: por eso solo quita líneas sola, y todo se le dice
  a Juanjo con el texto de antes y de después.
- Lo que se corrige en la web es una corrección de los datos, no del
  programa: el fallo vuelve hasta que se arregle el código.
- Si Chromium no está, el revisor trabaja sin las páginas dibujadas.

## Validación

`tests/test_revisor.py` (reglas, correcciones solo de líneas, que la
corrección caduca si el texto cambia, que va al bot, cuándo se despierta, un
mensaje por revisión), `tests/test_bot.py` (edición de los mensajes enviados,
una vez y no pasadas las 48 horas; cierre de los riesgos propios),
`tests/test_web.py` (el radar con el estado único, las etiquetas con los
umbrales de config, «Si surts»), `tests/test_riscos.py`, `tests/test_smp.py`
y `tests/test_pluja_arriba.py`. Dos revisiones reales con Sonnet 5.5 y los
datos del momento. La web, vista en Chromium y Firefox, en escritorio y
móvil.

## Cambio del 18-10-2026 (3.136.1): lo que vio la primera revisión en el NAS

La primera revisión real (07:46, 34 s, 0,17 USD) encontró tres cosas, y se
arreglan en el código:

- La ficha de AEMET de tormentas, abierta con la versión anterior, no llevaba
  cuándo empieza y decía «Actiu ara»: las fichas abiertas de AEMET lo toman
  de su clave (`aemet:tipus:inici`).
- «Avisos actius (3)» en «Si surts» tenía 4 líneas al desplegarlo: Meteocat
  da un aviso por meteoro. Las líneas de Meteocat se agrupan por fenómeno
  (`smp.textos` da el fenómeno), como en el bloque plegado.
- Una ficha creada el día 16 decía «demà» de su día: la nota del revisor
  cubre ahora las fichas creadas antes del 18-10-2026, no solo las cerradas.

## Cambio del 18-10-2026 (3.136.2): el texto de antes y el de después

El mensaje de una corrección automática lleva el texto de antes y el de
después, sin el HTML de Telegram, y el de una propuesta, el texto actual y el
propuesto (Juanjo: «sí, añádelo»). Hasta ahora solo decía dónde estaba el
error y por qué.

## Cambio del 18-10-2026 (3.138.1): el asterisco de la persistencia

El revisor encontró «*» («Hi compta la pluja que cau ara al barri») y «Pluja
feble» en la tabla con «No plou» arriba. La persistencia sube las primeras
horas por la lluvia de la última hora (`consens_pluja(...)["pluja_1h"]`),
aunque ya haya parado: el cálculo es el validado, el rótulo era inexacto.
Ahora dice «Hi compta la pluja de l'última hora al barri, encara que ja hagi
parat», y «Com funciona», «Si ha plogut a l'última hora…» en vez de «Si ja
plou». La parte alta redondeada («1 °C més» con 0,5) era la regla de Juanjo
del 13-10-2026 y se le explica al revisor.
