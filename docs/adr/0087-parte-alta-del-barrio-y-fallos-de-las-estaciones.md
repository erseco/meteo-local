# 87. La parte alta del barrio y qué pasa si fallan las estaciones

Fecha: 2026-10-13 · Estado: aceptado

## Contexto

La estación de casa está en el carrer Canaletes, junto a la riera, en la
zona más fría del barrio; ICERDA6 también está junto a la riera. ICERDA18,
ICERDA28 e ICERDA48 están en la parte alta. Juanjo, 13-10-2026: en su calle
los coches tienen hielo casi todos los días en invierno y casi cada año se
llega a −4 °C (en 2024 y 2025), cosa que no pasa en el resto; como las
temperaturas de la web son siempre las de la riera, propuso decir que son de
ahí y cuánto hay que sumar para el resto, «1, 2... grados, dependiendo del
momento y del frío». Pidió «riera» y no «zona baja», que no se entiende, y la
cifra junto a la temperatura de cada tramo. Y que el programa prevea qué
hace si fallan las estaciones, las de abajo, las de arriba o el servicio
entero: «aparte de avisarme para tomar decisiones, la web debe seguir
funcionando».

## Evidencia

- Verano y otoño de 2026 (27-07 a 06-10, cada 10 minutos): la parte alta,
  menos casa, de +0,1 a +0,4 °C de noche y de +1,4 a +1,9 °C de 12 a 18 h
  (`calibracio/part_alta.py`, sin las horas con sol directo sobre el
  termómetro). ICERDA6, de noche, 0,3 °C más fría que casa; ICERDA18, casi
  igual que casa a todas horas; ICERDA28 e ICERDA48, unos 2 °C más cálidas
  por la tarde.
- Invierno de 2025-2026 (mínimas diarias de Weather Underground, 143
  noches): la parte alta, +0,5 °C de mediana y +0,8 °C en las 20 noches con
  casa a 2 °C o menos; fue un invierno suave (mínima de casa, −2,5 °C).
- Enero y febrero de 2024 y de 2025 (mínimas diarias de las vecinas y medias
  de 4 horas o de un día de casa, lo que guarda Ecowitt): la mínima de arriba
  (ICERDA18 o, sin ella, ICERDA28) supera a la de ICERDA6 en **2 °C de
  mediana y hasta 4 °C**, los dos inviernos; la media del día de arriba, a la
  de casa, en 1,1 °C (hasta 3,7). El 14-01-2025: ICERDA6, −5 °C; ICERDA28,
  −4; ICERDA18, −1; la media de 4 horas más baja de casa, −3,9 °C (su mínima
  real, más baja). Lo que Juanjo ve en su calle se confirma; el invierno de
  2025-2026 fue la excepción. Datos en `calibracio/dades/hivern/` (no se
  suben).

## Decisión

Versión 3.78.0.

- **Las vecinas, marcadas**: `config.VEINES` lleva `alta` (ICERDA18,
  ICERDA28 e ICERDA48).
- **«Ara»**: debajo de la temperatura, «Vora la riera. A la part alta, 2 °C
  més.» cuando la mediana de las vecinas de arriba leídas en la última media
  hora (al menos dos) se separa un grado o más (`part_alta.ara`). Es una
  medida.
- **Previsión**: cada fila lleva `dif_alta`, la diferencia habitual a esa hora
  en los últimos 30 días del registro (al menos 10 casos por hora, sin las
  horas con sol directo); si no hay bastantes, la de partida
  (`calibracio/part_alta.json`). La recalcula el NAS en cada pasada, así que
  sigue la época del año. Junto a la temperatura del tramo, «(+2 a la part
  alta)» si la máxima (de día) o la mínima (de noche) se separan un grado o
  más.
- **Heladas**: si la mínima de la riera llega a 0 °C y la de la parte alta
  no, «glaçada vora la riera».
- **Si falla la estación de casa**, «Ara» sale de las vecinas
  (`casa.ara_sense_casa`): la temperatura, la de ICERDA6, para que siga
  siendo la de la riera; sin ella, la de la parte alta menos su diferencia
  habitual a esa hora; la lluvia y la humedad, por consenso (ADR 0085); sin
  presión. La previsión ya se corregía sin la estación (ADR 0017).
- **Si fallan las de arriba**, no se da la diferencia de ahora y la
  previsión usa la habitual. **Si falla Weather Underground entero**, todo
  sale de casa, como antes del ADR 0060. **Si fallan casa y Weather
  Underground**, no hay «Ara», como hasta ahora, y la previsión sigue.
- **Avisos a Juanjo** (`estacions.py`, en cada pasada del NAS, con la cola
  de reintentos de `avis_privat`): una vez cuando falla y otra cuando
  vuelve; la estación de casa a los 30 minutos, la parte alta (menos de dos
  de arriba) y Weather Underground entero a la hora, y cada vecina sola al
  día. Sin Weather Underground no se avisa de la parte alta ni de cada
  vecina. Estado en `/estat/estacions-falla.json`.
- La web no dice el nombre de la calle; «D'on surt» explica la riera y la
  parte alta, y «Com es llegeix la previsió» (antes «… la taula», Juanjo:
  «cambia taula por previsió») lo que quiere decir «+2 a la part alta», solo
  si algún tramo lo lleva (3.78.1).
- En el móvil, la línea de la temperatura del tramo se parte por trozos
  enteros («19–24 °C», «(+2 a la part alta)», «· semblant a ahir»): con el
  añadido no cabía y se salía (Juanjo: «en movil … se desborda»). Medido en
  Chromium, Firefox y WebKit a 320, 360, 375 y 412 px, en catalán y
  castellano.

## Alternativas descartadas

- **Un conmutador «carrer Canaletes»** o dos temperaturas: más trabajo para
  quien lee por una diferencia que muchas veces no llega a un grado.
- **La temperatura principal, la del barrio** (la de casa más la diferencia
  habitual): sería una estimación en vez de una medida, y la diferencia va y
  viene.
- **«Zona baixa»**: Juanjo, «no se entiende».

## Riesgos y limitaciones

- La diferencia habitual es una mediana de 30 días: suaviza las noches de
  helada fuerte, que son pocas. Pendiente: con el invierno hora a hora,
  comprobar si conviene un ajuste para las noches despejadas y sin viento, y
  solo si la validación lo respalda.
- Las vecinas dan grados enteros: la diferencia tiene medio grado de margen.
- Con ICERDA6 en lugar de casa, la temperatura de «Ara» va en grados
  enteros.
- El calor (36 °C) y el riesgo por frío siguen calculándose con la
  temperatura de la riera.

## Validación

- `tests/test_part_alta.py`: la diferencia de ahora, la tabla con el registro
  y la de partida, «Ara» con ICERDA6, con la parte alta y sin vecinas, y los
  avisos (a los 30 minutos, una sola vez, al volver, sin repetir cuando falla
  todo Weather Underground). `tests/test_web.py`,
  `test_part_alta_al_costat_de_la_temperatura`. 423 pruebas en verde.
- En el NAS (13-10-2026, con una copia del registro): diferencia de ahora
  0,9 °C (no sale la línea); en la previsión, de +1,6 a +1,8 °C por la
  tarde. Sin la estación de casa, con las vecinas reales: 18 °C con ICERDA6
  (casa marcaba 18,1) y 18,4 °C con la parte alta.
- `probar-web` en Chromium, Firefox y WebKit, móvil y escritorio, y axe-core
  sin errores en catalán y castellano.
