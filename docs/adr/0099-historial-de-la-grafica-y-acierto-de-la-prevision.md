# 99. Historial de la gráfica y acierto de la previsión

Fecha: 2026-10-17 · Estado: aceptado

## Contexto

Juanjo, el 17-10-2026, al hablar de qué más podía tener la configuración de
la gráfica: lo medido sobre lo previsto, «o que se pueda ir hacia atrás sin
límite, no?», y «algún índice o indicador de lo buena que es la
predicción? en teoría con el tiempo debería mejorar, eso se podría indicar
de algún modo».

El NAS ya guardaba lo necesario: la estación de casa hora a hora desde el
4 de octubre (`estacio-casa.csv`), la lluvia de las vecinas y de Meteocat, y
cada hora la previsión publicada con lo que mostraba la web (`mostrat` de
`casa-AAAA-MM.jsonl`) desde el 5, para el aprendizaje (ADR 0012).

## Decisión

- **`historial.py`** prepara, para cada día desde el 4 de octubre, hora a
  hora, lo medido (temperatura de la estación; lluvia como la cuenta el
  aprendizaje, None si no se sabe) y lo que decía la previsión de las 7 de
  ese día (la primera publicación de las 7; si falta, la última desde las
  5), y el acierto. `publica.sh` sube a IONOS en cada publicación el índice
  (`historial.json`) y los dos últimos días; los anteriores se subieron una
  vez. `rep-dades.sh` acepta esos nombres exactos, JSON, hasta doce
  archivos por envío.
- **La vista en grande** lleva ‹ y › para ir día a día hacia atrás, hasta el
  primero, y «Avui» para volver. Un día pasado se ve entero: la temperatura
  medida, la lluvia medida en barras y, en punteado tenue, la temperatura que
  decía la previsión de las 7; sin opciones (no hay viento ni parte alta
  medidos). Hoy, con «Avui» o «Tot», las horas ya pasadas van delante, y una
  raya marca «Ara». La ficha de cada hora pasada dice lo medido y lo previsto.
- **El acierto**, debajo de la gráfica, como conclusión y con los casos
  (método en la metodología, apartado 17 bis): «Temperatura: s’equivoca de
  mitjana 0,9 °C» y «Pluja: quan diu que plourà (50 % o més), plou 7 de cada
  10 vegades; quan diu que no (menys del 20 %), no plou 19 de cada 20»;
  los 30 días anteriores al lado, para ver si mejora, y la temperatura por
  meses cuando hay más de uno. Con pocos datos (menos de 48 horas, menos de
  20 casos), «encara poques dades». En cada día pasado, su propio acierto.

- **Solo con el botón «Com encerta»** (3.112.0; Juanjo, 17-10-2026: «ahora
  sale ya con la estimación pasada. No, debe salir como antes, la estimación
  pasada hazla a través de un botón que la active, así no se mezcla con los
  datos de predicción actuales»): por defecto la vista enseña la previsión
  sola, como antes. Con «Com encerta» (icono de diana), hoy añade delante
  las horas pasadas, y en todos los días la previsión de las 7 punteada y el
  acierto. Las flechas siguen a la vista: un día pasado sin el botón enseña
  solo lo medido. Se recuerda en el dispositivo y solo afecta a la vista en
  grande.

- **La antelación, de 1 a 23 horas** (3.113.0; Juanjo, 17-10-2026: «la de
  las 7 está muy lejos de las horas de la tarde y noche… si elijo 1h, me
  salga la gráfica con lo que se predijo 1h antes de cada hora y con el
  error, lo mismo con 2h, etc»): en lugar de la previsión de las 7, el
  historial guarda para cada hora lo que mostraba la web en la publicación
  de N horas antes de que empezara (N de 1 a 23: cada publicación cubre 24
  horas, contando la que ya ha empezado), y el acierto para cada N. Con
  «Com encerta», un selector «Antelació ‹ 1 h ›» elige N (por defecto 1 h,
  se recuerda); la curva punteada y el texto son los de esa antelación. Con
  los datos del 5 al 17-10: 0,7 °C de error con 1 h, 0,8 con 3 h, 1,0 con
  6 y 12 h. Unos 14 KB por día.
- **Desmarcar «Com encerta» vuelve a hoy** con la previsión de siempre, y
  las flechas de los días pasados solo salen con el botón activo (Juanjo:
  «si se desmarca el botón com encerta … debe volver al día de hoy y
  mostrar la predicción estándar»).

## Riesgos

- La franja de avisos no sale en los días pasados: el historial de avisos
  está en «Perill».
- Con 3 horas de lluvia prevista en octubre, el acierto de la lluvia tardará
  semanas en poder darse.
- Los días anteriores al 5 de octubre no tienen la previsión de las 7.

## Validación

- Pruebas: el día con lo medido y la previsión de las 7 (no la de las 6), el
  error y los casos de lluvia, los días de 23 y 25 horas del cambio de hora;
  el receptor acepta el historial y rechaza otro nombre o un archivo que no
  es JSON.
- Con el registro real del NAS: 14 días, 187 horas con las dos cosas,
  0,87 °C de error; 3 horas con lluvia prevista. En Chromium, Firefox y
  WebKit, escritorio y móvil: navegar hasta el 4 de octubre y volver.

## Cambio del 17-10-2026 (3.123.0): la navegación en el tiempo, junta

Juanjo, ante la vista con «Com encerta» (día ‹ ›, luego los botones de la
vista y luego la antelación): «la antelacion no debería ir a continuación de
HOY? … asi la navegación temporal queda junta. O quizás los botones que ahora
hay enmedio pasarlos arriba, decide tu». Las dos cosas: arriba, los botones
que eligen qué se ve (horas, viento, partes, «Com encerta»); debajo, el día y
la antelación en un mismo bloque (`.vg-temps`), en una fila si caben (en el
ordenador) y, si no, una debajo de la otra (en el móvil).

## Cambio del 18-10-2026 (3.137.0): los milímetros previstos

Juanjo: «en la sección com encerta quiero incluir los mm de lluvia
predichos». El historial guarda también los milímetros que mostraba la web
(`prev` = [temperatura, probabilidad, mm]) y, para cada antelación, la suma
de los previstos y de los medidos en las horas que tienen los dos (`mm`). Con
«Com encerta», la gráfica dibuja los previstos como una barra de contorno
discontinuo junto a la de lo que llovió (con su clave en la leyenda), la ficha
de cada hora pasada dice «prevista: 30 %, 0,8 mm», y el texto de debajo da los
totales del día o de los últimos 30 días. Los milímetros previstos son los de
la tabla, el máximo de los modelos finos: el 17-10-2026 la previsión de 2 h
antes sumaba 17,2 mm y no llovió nada en el barrio.

Como cada publicación solo reescribe los dos últimos días, `historial.py`
lleva un número de formato (`FORMAT`, apuntado en
`registre/historial-format`): si cambia, la pasada siguiente rehace todos los
días. Los días se pueden leer igual sin los milímetros (dos valores en
`prev`). Validación: `tests/test_historial_grafica.py`; el historial real
del NAS generado aparte, y la vista con «Com encerta» en Chromium y Firefox.

Y los textos, más claros (Juanjo: «no me queda claro todo esto. es el resumen
del mes? por qué dice que hay 7 horas de lluvia prevista?»):

- El resumen de la vista de hoy cuenta también las horas de hoy ya pasadas
  (antes, solo los días acabados) y dice el periodo con fechas («Des del 4
  d'octubre fins ara (15 dies)»; «Els darrers 30 dies» solo cuando hay 30).
- La lluvia, en recuento y igual en el resumen y en cada día: «de les 12
  hores en què deia que plouria (50 % o més), en va ploure 5; de les 206 en
  què deia que no (menys del 20 %), en va ploure 1», con el aviso de que aún
  son pocas si no llegan a 20. El día sumaba antes los aciertos de las dos
  cosas («va encertar 23 de 24 hores») y parecía bueno aunque fallara toda la
  lluvia.
- Los milímetros, como cantidad: «Quantitat de pluja: en preveia 78,5 mm i
  en van caure 18,7».
