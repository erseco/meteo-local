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

## Cambio del 18-10-2026 (3.138.2): la ficha alargada por AEMET

El revisor encontró en el historial de «Perill» la ficha de tormentas del
17-10 con «fins a mitjanit» en el texto y final a las 03:59 del 18. La hora
era la buena: AEMET juntó en ese aviso el del día siguiente de 0 a 4 h y lo
alargó (`tanca_aemet`); el texto es el que publicó al principio. No era un
desfase de zona horaria, como suponía el revisor. Juanjo aprobó que la ficha
lo diga en vez de enseñar al revisor a callarlo: al alargarse, la ficha guarda
el final con que se publicó (`allargat_de`) y, debajo de la línea de cuándo
dura, dice «L'AEMET l'ha allargat fins a dg. 18/10, 03:59», también en el
texto que se comparte. La ficha del 17-10 se completó a mano en el estado del
NAS. Los mensajes de Telegram y del navegador no cambian: se enviaron con el
final que tenían.

## Falsa alarma del 18-10-2026: asterisco con hueco

El revisor avisó cuatro veces (filas 9–10, 11–12, 12–13 y, a las 12:58,
14–15 y 15–16) de que el «*» salía en horas futuras y no en una intermedia,
y lo tomaba por un fallo que debía limitarse a la hora en curso. No lo es: la
persistencia cubre las cuatro primeras filas (ADR 0007) y cada fila lleva la
cifra mayor, la del modelo o la de la persistencia. A las 12:58, con 0,5 mm en
la última hora, la persistencia daba 47,5 %, 40 % y 34 % para las tres horas
siguientes, y el modelo, 54 %, 39 % y 14 %: la fila 13–14 era del modelo y
las otras dos, de la persistencia. Se explica en `revisor-instruccions.md`;
el cálculo no cambia.

## Cambio del 18-10-2026 (3.138.5): la leyenda del asterisco explica el hueco

Para que quien lee la tabla entienda lo mismo que ahora sabe el revisor, la
leyenda del «*» dice «Xifra que ve de la pluja de l'última hora al barri,
encara que ja hagi parat: els models en donaven menys» (antes, «Hi compta la
pluja de l'última hora al barri, encara que ja hagi parat»), en catalán y
castellano (Juanjo: «sí, aplica la leyenda»). Y la R4 «per carretera» por un
autobús entre Terrassa Nord y Manresa se corrige en el código (ADR 0029).

## Cambio del 18-10-2026 (3.138.6): tres hallazgos leves del revisor

- **«Si surts» daba por acabado un riesgo que volvía**: «Cap a les 15 h
  s'acaba el risc de pluja» con lluvia posible de 16 a 0 h. Si el riesgo
  vuelve dentro de la salida, dice «De 15 a 16 h, sense risc de pluja» (o
  «sense avís oficial per pluja»); «s'acaba» solo si no vuelve.
- **La lluvia de 15 minutos era solo la de casa** y la de la última hora, la
  mediana del barrio: 0,3 mm en 15 minutos y 0 en la hora. Ahora también va
  por consenso (ADR 0085); con las mismas estaciones, las medianas no se
  cruzan. El revisor sabe que «Plou» basta con una estación.
- **El radar marcaba «†» con un 5 %**: la regla de los milímetros no pedía
  probabilidad, y el recuadro, que dice «Pot arribar pluja» desde el 20 %,
  decía que no venía lluvia. Ahora el radar solo sube una hora si su
  probabilidad llega a `PROB_ATENCION` (ADR 0019). En el registro de octubre,
  de 36 horas marcadas por el radar, esta era la única por debajo.

## Cambio del 19-10-2026 (3.148.0): «Si surts» dice que llueve si llueve

A las 06:40, lloviendo (`pluja_ara.estat` «plou», según las estaciones),
«Si surts» decía en bici, moto y coche «Pluja probable a l'anada (6 h)», y a
pie «Pot ploure mentre ets fora». Juanjo: «si llueve, debe decir que llueve
sea por radar, estaciones o ambas». Ahora, si la hora de salida lleva
`plou_ara` (la misma verdad de la lluvia de la portada y la tabla), el motivo
dice «Ara plou al barri, segons les estacions / el radar / les estacions i
el radar» (de `segons_estacio` y `segons_radar` de la hora), y la vuelta
aparte si también ve lluvia («…, i pluja probable a la tornada (9 h)»); a
pie, «Ara plou al barri, segons …: porta paraigua». El nivell no cambia.
Prueba: `tests/test_web.py` (`test_si_ara_plou_ho_diu_i_qui_ho_veu`).

Corrección en la 3.149.0 (el mismo día): a las 07:0x, con los datos de las
06:57, «Si surts» volvía a decir «Pluja probable a l'anada (7 h)» lloviendo:
pasada la hora en punto, la hora en curso de esos datos (de 6 a 7, la que
llevaba `plou_ara`) ya no cuenta y «Ara» es la de 7 a 8. Ahora sale del
estado único de la lluvia de ahora (`pluja_ara`: «plou», con «les estacions»
o, si el radar también la pone encima, «les estacions i el radar»;
«radar_sobre», «el radar»), y solo con «Surto: Ara» (Juanjo: «esto solo hay
que tenerlo en cuenta cuando surto está en ara»); con una hora posterior, la
previsión como siempre.


## Cambio del 19-10-2026 (3.151.0): hallazgos leves del revisor

Comprobados en el código los leves de la noche del 18 al 19:

- **Redondeo distinto en el bot y en la web.** El resumen decía «entre 13 °C
  i 18 °C» y la tabla, 19 °C a las 17 h: el valor era 18,5, que `round()` de
  Python lleva a 18 (al par) y `Math.round` a 19. `bot.graus` y los
  porcentajes del resumen redondean ahora como la web (`floor(x + 0,5)`).
- **La comparación con el día de antes restaba sin redondear.** «Demà tarda
  14–19 °C · 2° més que avui» con «Tarda 15–18 °C»: restaba 19,4 − 17,6 = 1,8
  y redondeaba el resultado. Ahora `comparaTemp` y `bot.compara_temp` restan
  las cifras ya redondeadas, las que se leen en las cabeceras (19 − 18 = 1,
  «semblant»). Con el día de ayer medido, que no se muestra, la diferencia
  puede variar en un grado respecto a la de antes; se prefiere que cuadre con
  lo que se lee.
- **Falsa alarma del revisor: la fila 6–7 sin aviso.** Una barra de aviso de
  una sola fila no tiene sitio para el texto y queda vacía (`ajustaFranges`);
  el texto completo está en el `aria-label` del botón, que el revisor no leía.
  `revisor.Text` lo lee ahora. Las franjas de Meteocat estaban bien.
- **«R4 · Amb incidències» con una incidencia ya resuelta.** Ver ADR 0079: un
  aviso que solo dice que la incidencia se ha resuelto y los trenes recuperan
  los horarios pone la línea «amb retard».
- **Viento «2 (30)»**: no es un fallo de cálculo; el viento de AROME es el
  instantáneo al final de la hora y la racha, el máximo de la hora. Queda por
  decidir con Juanjo.

Pruebas: `tests/test_bot.py` (18,5 → 19; 17,6 frente a 19,4 → 1) y
`tests/test_trens.py` (`test_incidencia_resolta_que_es_recupera_va_amb_retard`).

## Cambio del 19-10-2026 (3.155.0): el viento de cada hora, la media de la hora

El revisor vio en la tabla por horas «3 (37)» en la fila de 17 a 18 (y antes
otro parecido de madrugada): el viento era el de un instante, el de AROME a la
hora en punto (`wind_speed_10m`), y la racha, la máxima de toda la hora; en
una hora de tormenta, con el viento a ráfagas, el instante podía caer en una
calma. La leyenda decía «la mitjana». Juanjo, tras preguntar si había riesgo
de pasarse del límite de Open-Meteo (no: unas 2.900 peticiones al día en el
peor caso, de 10.000; esta añade unas 240): «sí, hazlo y publica». Ahora
`casa.vent_hora` da la media de la hora con el viento cada 15 minutos de
AROME (`minutely_15`, una petición más por pasada), por trapecios; sin esos
datos, la media del principio y el final de la hora, como la temperatura. La
racha no cambia. Con los datos del 19-10-2026, la fila de 17 a 18 pasó de «3
(37)» a «9 (37)». La leyenda dice ahora «La mitjana de l'hora en km/h i,
entre parèntesis, la ratxa més forta de l'hora». Prueba:
`tests/test_casa_fonts.py` (`VentHora`).


## Cambio del 19-10-2026 (3.158.0): los hallazgos del revisor de 11:34 a 14:18

Juanjo: «sí, arregla los del revisor». Cada uno comprobado en el código:

- **Redondeo** (14:18): la racha de 92,5 km/h salía «92» en el aviso
  (Python redondea las mitades a par), «93» en la tabla y «92,5» en la
  portada. `riscos.num` redondea las mitades hacia arriba, como la web, y la
  línea corta de la portada usa `numRisc`, la misma regla que el texto.
- **«Tempesta: aEMET…»** (11:34): `origenTram` pasaba a minúscula la primera
  letra aunque fuera una sigla, y repetía el aviso que el perill del tramo ya
  decía. Ahora no repite la fuente que ya nombra el perill con tormentas y no
  toca las siglas.
- **Hora de «actualitzat» de un plan** (13:10): era la del PDF de Protecció
  Civil (12:08) con el mensaje enviado a las 12:15. El comunicado nuevo pone
  ahora `darrer` con la hora del mensaje, la misma que en el móvil (ADR 0094);
  el texto de la ficha sigue sin cambiar.
- **«A peu»** (11:34): decía «Pot ploure mentre ets fora» con un 60 % y los
  vehículos «Pluja probable a la tornada». A pie hay ahora «Pluja probable
  mentre ets fora: porta paraigua» con el mismo umbral (`plouRodes`).
- **«uns 31 mm» en la cabecera de un tramo** (14:18): es la cantidad esperada
  (ADR 0103), no la suma de la columna, y la página no lo decía. La leyenda
  «Com es llegeix la previsió» lo explica («Pluja del tram») cuando algún
  tramo la muestra.
- **El aviso de la web, activo en «Perill» y ausente de la portada** (13:44):
  cuando la previsión deja de ver el riesgo, la ficha espera 3 horas a
  cerrarse (`RISC_FI_H`, para que el vaivén de los modelos no repita
  mensajes). Durante esa espera ahora lleva `en_pausa`: dice «Ja no es
  preveu» y desde cuándo, y no cuenta como activa ni como «Nou»
  (`perillsNous`), igual que la portada, que ya no la lista. Si el riesgo
  vuelve, deja de estar en pausa.
- La de las 13:44 sobre «77 km/h» frente a «20 (66)» ya la resolvió la
  3.157.0 (la racha, la del modelo que da más; ADR 0018).

Validación: `tests/test_riscos.py`, `tests/test_web.py`,
`tests/test_historial.py`; «Perill» con la ficha en pausa y la leyenda, en
Chromium y Firefox, móvil, claro y oscuro; axe-core sin fallos en las dos
páginas.
