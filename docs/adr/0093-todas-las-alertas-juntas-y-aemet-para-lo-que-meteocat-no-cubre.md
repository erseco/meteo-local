# 93. Todas las alertas de peligro juntas, y AEMET para lo que Meteocat no cubre

Fecha: 2026-10-16 · Estado: aceptado (cambia el ADR 0092 en qué avisa AEMET)

## Contexto

Con la 3.87.0 publicada, Juanjo vio que el resumen de mañana en «Consultes»
solo decía el aviso amarillo de AEMET, sin el peligro alto de Meteocat:
«¿aquí no sale nada del meteocat?». Y después: «y protección civil, las
alertas de peligro deben ir siempre juntas, que sale tanto en un lado como en
el otro, lo mismo con otras alertas de peligro que ahora no están activas.
Deberías tener un sistema para no dejártelas nunca».

Cada pantalla armaba su propia lista. Revisado el código:

| | Portada | Si surts | Perill | /avisos_actius | Resumen del día |
|---|---|---|---|---|---|
| Protecció Civil | sí | sí | sí | sí | **no** |
| Meteocat | sí | sí | sí | sí | **no** |
| AEMET | sí | sí | **no desde la 3.87.0** | sí | sí |
| Riera | sí | sí | sí | **no** | **no** |
| Incendios | sí | sí | sí | sí | **no** |
| Pla Alfa | sí | sí | sí | sí | **no** |
| Tiempo extremo propio | sí | **no** | sí | sí | **no** |

El resumen del día es el mismo texto en «Avui» y «Demà» de «Consultes», en los
mensajes del bot de las 7 y las 21 h y en /avui y /dema. La tabla por horas de
«El temps» también pintaba solo AEMET.

Sobre AEMET, el ADR 0092 la dejó de reserva (solo si no se podía leer
Meteocat). Juanjo lo corrigió: «si meteocat no tiene aviso y aemet sí, debe
salir aemet, prima la información y seguridad de los usuarios». Y al saber
que de AEMET solo se leían la lluvia y las tormentas: «¿por qué se descartan
algunos avisos de aemet? seguridad e información ante todo». No había motivo
escrito: venía de la primera versión (ADR 0001), que solo decidía entre moto y
coche.

## Decisión

### Meteocat o AEMET, por fenómeno y horas (`smp.py`)

- Un aviso de AEMET está **cubierto** si Meteocat tiene aviso del mismo
  fenómeno en alguna de sus horas (`smp.cobreix`; `casa.py` lo marca con
  `cobert`). Los cubiertos no se muestran ni avisan; los demás sí, como
  siempre. Sin lectura de Meteocat, ninguno está cubierto.
- Fenómenos que Meteocat también avisa: lluvia, viento, calor, frío y nieve.
  Las tormentas, la niebla, el polvo y el resto salen siempre de AEMET.
- Un aviso de AEMET que deja de estar cubierto se avisa: el cubierto no se
  apunta como avisado. Uno ya avisado que pasa a estar cubierto cierra su ficha
  de «Perill» diciendo que ahora se muestra el de Meteocat.
- **AEMET se lee entero**: todos los tipos de Meteoalarm para el Prelitoral de
  Barcelona (`prevision.TIPUS_METEOALARM`: tormentas, inundaciones, lluvia,
  viento, calor, frío, nieve, niebla, riesgo de incendios, fenómenos costeros,
  aludes, polvo y, si llega uno desconocido, «otros fenómenos»).

### Una sola lista, en el mismo orden, en todas partes

- Los tipos son `bot.TIPUS_PERILL`: Protecció Civil, Meteocat, AEMET, riera,
  incendios, Pla Alfa y el tiempo extremo que calcula la web. En ese orden en
  la portada y «Si surts» (`blocAvisos` de `web/comu.js`, que ahora incluye el
  tiempo extremo y lo usan las dos), en /avisos_actius (añade la riera) y en
  el resumen del día (`bot.linies_perill_dia`).
- En el resumen, una línea por alerta: los planes (no tienen final) hoy y
  mañana; Meteocat, una línea por fenómeno con su nivel más alto
  (`smp.per_fenomen`); AEMET, lo no cubierto; la riera y los incendios, solo
  hoy, porque dicen lo que pasa ahora; el Pla Alfa, el nivel de cada día; el
  tiempo extremo, si toca el día, dicho como no oficial. Cada línea lleva a
  «Perill» en «Consultes».
- La riera abierta va en los datos públicos (`perill_riera`, de avisos.json):
  sus datos son privados, su aviso no. Para tenerla al día, `publica.sh` hace
  los avisos antes que los datos públicos.
- La tabla por horas pinta Meteocat («Perill alt de Meteocat per pluja») y lo
  de AEMET que no cubre. «Si surts» cuenta como lluvia probable el aviso de
  cualquiera de los dos, y lo dice como «avís oficial».
- **Un plan de Protección Civil se mantiene a la vista con un aviso de su
  fenómeno, de AEMET o de Meteocat** (`prevision.pla_per_temps`). Antes, solo
  con lluvia o tormentas de AEMET: un plan de viento, de nieve o de calor, o
  uno con aviso solo de Meteocat, se ocultaba a las 24 horas. Un plan sin
  fenómeno meteorológico (contaminación) se muestra siempre.

### Para no dejarse ninguna

`tests/test_perills.py` mete una alerta de cada tipo y comprueba que salen en
/avisos_actius, en el resumen de hoy y en el de mañana (salvo riera e
incendios), en catalán y castellano, y en el bloque de la web; que la portada
y «Si surts» usan ese bloque tal cual; que cada aviso de peligro que crea
`avisos_bot.py` tiene su tipo, y que un tipo nuevo sin marca hace fallar la
prueba. Las instrucciones del repositorio lo piden.

## Cambio del 16-10-2026 (3.88.1)

La ficha cerrada de un aviso de AEMET que pasa a cubrir Meteocat decía «🟢
Acabat», y Juanjo preguntó si se había retirado: el aviso seguía vigente. Ahora
lleva `substituit_per` (la ficha de Meteocat) y «Perill» dice «Substituït per
l'avís de Meteocat», con enlace a esa ficha, sin el círculo verde.

## Cambio del 16-10-2026 (3.90.0): de dónde sale cada aviso, también en el móvil

La etiqueta de peligro de cada tramo decía «Avís taronja: pluja» para un
aviso de Meteocat, que habla de grado de peligro. Ahora dice «Perill alt:
pluja», como la franja vertical («Perill alt · pluja»), y si hay de las dos
maneras, juntas («Perill alt: pluja · Avís groc: tempestes»; `textPerillCurt`).
De dónde sale cada cosa (`textPerill`, «Perill alt de Meteocat per pluja»;
`origenTempesta`, si la tempesta es de un aviso o de los modelos) sale al
pasar el ratón y, para el móvil (Juanjo: «¿en móvil esta info se ve?»), en
una línea al abrir el tramo y en un mensaje breve al tocar la franja vertical.

## Alternativas descartadas

- **AEMET solo de reserva** (ADR 0092): calla avisos que Meteocat no da.
- **Las dos fuentes siempre**: repite el mismo fenómeno con niveles distintos y
  confunde (el amarillo de AEMET junto al alto de Meteocat).
- **Generar todas las listas en un solo sitio y pintarlas igual**: el bot
  (texto de Telegram) y la web (elementos con ayuda y enlaces) tienen formas
  distintas; lo que se garantiza es el contenido, con la prueba.

## Consecuencias

- El sábado 17: Protecció Civil, Meteocat (alto por lluvia) y AEMET (amarillo
  por tormentas) en todas partes; el amarillo de AEMET por lluvia ya no sale y
  su ficha de «Perill» se cierra.
- Llegarán avisos de AEMET que antes se descartaban (viento, calor, frío,
  niebla…), cuando Meteocat no los cubra.

## Evidencia

- Datos reales del 16-10-2026, 08:20: AEMET con lluvia (dos avisos) y
  tormentas amarillos de 12 a 24 h del sábado; Meteocat, lluvia alta. Con
  `casa.py`: las dos de lluvia salen `cobert`, las tormentas no; INUNCAT en
  alerta, visible; la tabla, «Perill alt de Meteocat per pluja».
- Feed de Meteoalarm del mismo día: `Moderate rain warning`, `Moderate
  thunderstorm warning`, `Moderate coastalevent warning`.

## Riesgos y limitaciones

- La correspondencia entre fenómenos de AEMET y de Meteocat es por nombre;
  un meteoro de Meteocat con otro nombre no cubriría a AEMET (saldrían los
  dos).
- En la reserva de IONOS la riera del resumen sale del avisos.json de la
  pasada anterior.

## Validación

477 pruebas, con `tests/test_perills.py` y las nuevas de `tests/test_smp.py`.
Con los datos reales: la web en local en Chromium y Firefox, móvil y
escritorio (portada, «Si surts», «Consultes › Demà»), sin errores de
JavaScript ni desbordamiento; axe-core (WCAG 2.1 AA y buenas prácticas) sin
infracciones en la portada, «Si surts», «Consultes» y «Perill», en catalán y
castellano.

## La etiqueta del tramo, solo plegado (17-10-2026)

Juanjo: «cuando despliego una franja horaria quiero que desaparezcan estas
alertas de peligro porque ya salen en vertical además del color que hay a la
izquierda, así se simplifica la visualización» y «plegadas sí aparecen,
desplegadas no». Desde la 3.113.1, la etiqueta de peligro de la cabecera de
cada tramo («⚠ Perill molt alt: pluja · Avís groc: tempestes») se ve con el
tramo plegado y se oculta al desplegarlo: entonces lo dicen la barra de
color de cada hora y el borde del tramo. Desde la 3.114.2, también la del
fenómeno destacado («tempesta»): desplegado queda el resumen normal, sin
avisos («que solo quede el resumen normal, sin avisos»).
