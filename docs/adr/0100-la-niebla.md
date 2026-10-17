# 100. La niebla

Fecha: 2026-10-17 · Estado: en curso (la hora en curso, aplicada; ICON, en vigilancia hasta el 17-11-2026)

## Contexto

El 17-10-2026 por la mañana había niebla en Montflorit y la web no decía nada
(Juanjo: «investiga por qué ahora hay niebla y la predicción del tiempo no
dice nada sobre esto»). Comprobado en los datos:

- El aeropuerto de Sabadell (METAR LELL) daba niebla desde las 6:30
  (visibilidad de 100 a 150 m, «FG VV002»); la estación de casa, 99-100 % de
  humedad y la temperatura en el punto de rocío.
- El tipo de tiempo de cada hora (`codi`, el que da «Boira») sale solo de
  AROME (`weather_code` de `meteofrance_seamless`), que en Open-Meteo no da
  visibilidad y no dio niebla. ICON sí: código 45 de 4 a 9 h y 720 m de
  visibilidad a las 9. ECMWF y GFS, no.
- En la hora en curso, el METAR de Sabadell solo se usaba para el % de cielo
  tapado (ADR 0088): «FG VV002» pasaba a «tapado al 100 %», y la web decía
  «Cobert».

Juanjo añadió: «Sabadell está a varios km y aquí tenemos la riera al lado
que muchas veces tiene niebla ella sola, no en Sabadell».

## Decisión

- **La hora en curso**: «Boira» (código 45) si el METAR de Sabadell, de los
  últimos 45 minutos, da niebla (FG, BCFG, PRFG, MIFG, FZFG; la neblina, BR,
  no) y la estación de casa está saturada (`C.HUMITAT_BOIRA`, 97 %). Es una
  observación oficial; la humedad de casa evita decirlo cuando Montflorit
  está seco.
- **La humedad, la de la estación de casa** (3.112.0): junto a la riera, no
  la media del barrio. A las 10 h del 17-10 la del barrio daba el 96 % y la
  de casa el 99 %, con niebla.
- **La confirmación de Juanjo** (3.112.0; «cuando los datos son favorables
  a niebla me mandas un mensaje y yo te respondo, así hay confirmación
  visual»): con casa al 98 % o más y sin lluvia, de 7 a 23 h y como mucho
  una vez cada 6 horas, el bot de los agentes le pregunta si ve niebla
  junto a la riera, con botones (sí, no, no lo sé); la respuesta se apunta
  en `registre/boira-confirmacions.csv`, y el mensaje cambia a «Apuntado: …».
  Las respuestas se miran cada minuto desde el reloj del NAS (3.112.2): antes
  solo en cada publicación, y el toque llegaba tarde para Telegram, que lo
  rechazaba, y el mensaje no cambiaba (Juanjo, 17-10-2026: «si se repiten
  dame confirmación de que mi respuesta se ha registrado»).
  Las respuestas se leen sin marcarlas como leídas, para no quitar nada a
  quien lea ese chat. Servirá para ajustar una regla de la riera con la
  humedad, la temperatura y el viento.
- **La niebla de la riera sola** no se dice todavía: en el barrio no hay nada
  que mida la visibilidad, y la humedad sola no basta. Del 4 al 17-10-2026,
  99 de 315 horas tenían en casa el 98 % o más y la temperatura a medio grado
  del rocío (88 sin lluvia), casi siempre de noche y al amanecer; no se sabe
  en cuántas había niebla.
- **ICON, en vigilancia antes de usarlo** (`boira.py`): una vez por hora,
  desde `publica.sh`, se apunta lo que da ICON para las próximas 12 horas
  (`registre/boira-icon.csv`). `boira.py resum` lo compara, con 1 a 6 horas
  de antelación, con la niebla de Sabadell con casa saturada y con casa
  saturada sin lluvia (lo que se tiene de la riera): aciertos, fallos y
  falsas alarmas. Se decide con un mes de datos, a partir del 17-11-2026.

## Riesgos

- La niebla que solo está en la riera no sale en la hora en curso.
- Un mes de otoño puede traer pocos episodios de niebla.

## Validación

- Pruebas: el METAR con FG y BCFG es niebla y con BR no; solo si es
  reciente; observada solo con casa saturada.
