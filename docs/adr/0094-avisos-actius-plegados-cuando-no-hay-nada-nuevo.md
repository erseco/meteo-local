# 94. «Avisos actius» plegado cuando no hay nada nuevo

Fecha: 2026-10-16 · Estado: aceptado

## Contexto

Juanjo, sobre la portada de la 3.90.0: «la pantalla inicial se ha ido
complicando con información. ¿Se te ocurre alguna mejora que, sin perder
información, permita una lectura más clara? Sobre todo al entrar en la página
inicial, la primera impresión».

Medido en un Pixel 7 con los avisos del día (INUNCAT en alerta con dos avisos
de Meteocat dentro y uno amarillo de AEMET): la cabecera ocupaba un 15 % de la
primera pantalla, «Avisos actius» un 55 % (ocho líneas, con los textos
íntegros de Meteocat: umbrales y hora de emisión), la temperatura asomaba
abajo y «El temps avui», lo que se quiere saber al abrir, quedaba fuera. El
bloque usaba a la vez franja de color, texto en naranja, negrita, cursiva, «?»
y «›». Arriba había dos horas distintas: «Actualitzat a les 09:21» y «Ara a
Montflorit (09:20)».

Propuesta de Juanjo: «la primera vez que se entra la tarjeta Avisos actius
aparece desplegada, pero, si no hay cambios, las veces sucesivas aparecería
plegada, indicando entre paréntesis el número de avisos». Objeción del agente:
plegado del todo, «(3)» no dice cuáles son; el sábado a las 11, con el aviso de
lluvia intensa a las 12, se vería solo el número porque nada habría cambiado
desde ayer, contra el criterio de que lo esencial se vea al abrir y de
«seguridad e información ante todo» (ADR 0093). Acordado (Juanjo: «sí, hazlo
en local»; tras probarlo en el móvil: «correcto, publica»): el mecanismo de
Juanjo con dos estados.

## Decisión

Versión 3.91.0.

- **«Avisos actius» es un plegable** (`details`), en «El temps» y en «Si
  surts», con el título «Avisos actius (3)»: el número cuenta cada aviso,
  también los cortes de luz.
- **Plegado, una línea por aviso**, con la franja de su nivel y «›» a su
  ficha de «Perill»: quién, qué y cuándo (`curtsAvisos`). La de Meteocat va a
  la ficha de Meteocat también cuando hay un plan, aunque desplegado su texto
  vaya dentro del del plan (3.91.1; Juanjo: «si pulso sobre meteocat me lleva
  a protección civil»). Protecció Civil: «pla d'inundacions (INUNCAT) en alerta».
  Meteocat: una línea por fenómeno con el nivel más alto y las horas
  (`smp.per_fenomen`, que ya llevaban los datos desde el ADR 0093); con datos
  anteriores sin `fenomens`, las líneas enteras, para que no falte ninguna.
  AEMET: «avís groc per tempestes, demà de 12:00 a mitjanit». La riera, los
  incendios, el Pla Alfa y los cierres, su título. El tiempo extremo propio:
  «Risc groc calculat per aquesta web: vent molt fort (75 km/h)». Los cortes
  de luz: el título y si es avería o trabajos. Las formas de las horas son las
  de cada fuente (Meteocat «de 12 a 24 h», AEMET «de 12:00 a mitjanit»).
- **Desplegado, los textos completos de antes**, sin cambiar nada (el oficial
  de Meteocat tal cual, ADR 0067; la cita de AEMET en castellano).
- **Se despliega solo la primera vez y cuando cambia el conjunto**: un aviso
  nuevo, un nivel que sube, uno que acaba, unas horas distintas. Lo que cuenta
  como cambio es la huella de las líneas cortas (`dataset.clau` de cada una:
  fuente, fenómeno, nivel y horas), independiente del idioma; la hora de
  emisión de un texto no cuenta. **Un aviso rojo no se pliega nunca** al
  cargar.
- **Lo visto se recuerda en el dispositivo** (`localStorage`,
  `meteo.avisos-vistos`), común a «El temps» y «Si surts»: se marca al pintar
  el bloque desplegado y al plegarlo o desplegarlo a mano. Sin memoria
  (navegación privada), cada vez desplegado.
- **Dentro de una misma página manda la persona**: la web repinta el bloque
  cada pocos minutos; si los avisos no han cambiado, se queda como lo dejó
  (`PLEC_AVISOS`); si cambian, se despliega en ese momento.
- **Una sola hora en la portada**: la línea «Actualitzat a les … · propera: …
  ?» pasa al pie de la tarjeta «Ara», y el título de la tarjeta deja de llevar
  la hora de la medida (difería un minuto de la otra y parecía un error). En
  «Si surts» sigue arriba, que no tiene tarjeta «Ara». Los avisos de datos
  (actualización que no llega, fuentes que fallan) siguen arriba.
- `NOM_RISC` pasa de `casa.js` a `comu.js`, porque la línea corta del tiempo
  extremo lo necesita también en «Si surts».

Resultado en el Pixel 7, segunda visita: la primera pantalla enseña los tres
avisos en tres líneas, la tarjeta «Ara» entera con la hora de actualización y
el resumen del día.

## Alternativas descartadas

- **Solo el número al plegar** (la propuesta literal): no dice cuáles son los
  avisos sin tocar nada; se descartó por seguridad e información.
- **Líneas cortas siempre, sin plegable** (la propuesta inicial del agente):
  obligaba a un toque para leer el texto oficial completo; la de Juanjo lo
  conserva a la vista la primera vez y cuando hay novedad.
- **Recordar cómo lo deja cada persona** (como «Desplega-ho tot», ADR 0074):
  Juanjo pidió plegado siempre que no haya cambios; así, lo que una persona
  despliega para leer no se le queda desplegado para siempre.
- Las demás propuestas (una sola tarjeta «Ara» + «Avui», dos columnas en el
  ordenador, no repetir la frase de peligro en cada tramo) quedaron para otro
  momento: con el plegable ya cabe la primera pantalla.

## Consecuencias

- `tests/test_perills.py` comprueba también el bloque plegado: cada tipo de
  alerta tiene su línea corta, y se despliega la primera vez, no la segunda,
  otra vez al cambiar el conjunto y siempre con un rojo.
- Un tipo de aviso nuevo tiene que dejar `dataset.clau` y `dataset.curt` en su
  elemento; sin ellos sale el texto entero, y la prueba de arriba lo detecta
  si falta.
- axe-core, sin incidencias en la portada (catalán y castellano) y «Si surts»,
  desplegado y plegado.

## Cambio del 17-10-2026 (3.118.0): en la portada, siempre plegado

Juanjo: «los avisos activos de la portada siempre colapsados». En «El temps»,
«Avisos actius» se abre plegado siempre, también la primera vez, cuando cambia
el conjunto y con un aviso rojo: plegado ya muestra una línea por aviso con la
franja de su nivel, así que se ve cuáles hay sin tocar nada. Si la persona lo
abre, queda abierto en esa página mientras los avisos no cambien.
`blocAvisos(dades, { plegat: true })` en `casa.js`; «Si surts» sigue con la
regla de arriba (se despliega solo con algo nuevo o rojo). Validación:
Chromium y Firefox con los avisos del momento (Meteocat en rojo): la portada
plegada al cargar, «Si surts» desplegada; prueba en `tests/test_perills.py`.

## Cambio del 17-10-2026 (3.120.0): en la portada, sin desplegable

Juanjo: «en avisos activos quita lo de desplegar, que muestre la información
como sale ahora plegado y al pulsar lleva al detalle del aviso, es para
simplificar la pagina inicial». En «El temps», «Avisos actius» es ahora el
título con el número y una línea corta por aviso, con la franja de su nivel;
cada línea lleva a la ficha de su aviso en «Perill», donde está el texto
entero, el comunicado y el «?» de la fase. Sustituye al «siempre plegado» de
la 3.118.0: `blocAvisos(dades, { curts: true })`. «Si surts» sigue con el
desplegable y la regla de arriba. Validación: Chromium y Firefox, en catalán
y castellano, con los avisos del momento; cada línea lleva a su ficha.

## Cambio del 17-10-2026 (3.121.0): cuándo se publicó cada aviso y «Nou»

Juanjo: «se podría poner en esta pagina inicial la fecha y hora de
publicación del aviso y si tiene actualizacion se sustituye por esta, asi se
sabe si la hemos visto antes o no», y luego «debajo no, cabe al lado, si no
cabe entonces pasa abajo». Cada línea corta de «Avisos actius» (portada y
«Si surts» plegado) acaba con «· publicat avui 00:09» o, si ha cambiado,
«· actualitzat avui 11:10», en gris y en un trozo que no se parte. Lleva la
palabra porque varias líneas ya tienen horas del fenómeno («avui de 12 a
24 h») y una hora suelta se confundiría con ellas.

La hora es la del historial de «Perill» (`inici` y `darrer` de avisos.json),
la misma con que llegaron los avisos al móvil y a Telegram; en un plan de
Protecció Civil, también la de su comunicado más reciente (del nombre del PDF,
`…_202610171110.pdf`), y en un plan en prealerta, sin historial, `des_de`.
Las líneas sin historial (cortes de luz, Pla Alfa) no llevan hora. Las fichas
activas de «Perill» añaden «· actualitzat …» con la misma regla
(`publicacioEpisodi`), para que digan lo mismo que la portada.

«Nou», delante de la línea, en los avisos que este dispositivo no había
mostrado al abrir la página: la clave es el aviso y su hora, así que una
actualización vuelve a salir como nueva. Lo mostrado se guarda en
`localStorage` (`meteo.avisos-llegits`) y la marca se mantiene mientras la
página sigue abierta; no se calcula hasta tener el historial, para que no
parpadee. Validación: Chromium y Firefox, catalán y castellano, con los
avisos del momento; primera visita con «Nou» y la siguiente sin él;
`tests/test_perills.py` con la hora en las líneas.
