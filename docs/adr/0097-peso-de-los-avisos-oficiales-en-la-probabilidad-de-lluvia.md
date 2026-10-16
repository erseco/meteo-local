# 97. Peso de los avisos oficiales en la probabilidad de lluvia

Fecha: 2026-10-16 · Estado: en curso (falta el histórico de avisos)

## Contexto

El 16-10-2026 la página daba para el sábado 17 por la tarde entre un 6 y un
16 % de lluvia, con un aviso de peligro alto de Meteocat por intensidad de
lluvia (más de 40 mm en 30 minutos) en el Vallès Occidental, uno amarillo de
AEMET por lluvia y tormentas y el INUNCAT en alerta. La probabilidad sale
solo de los modelos (apartado 6 de la metodología: «los avisos se muestran
tal cual»); AROME daba 0 mm, ICON-EU 0,7, ECMWF 3,9 y GFS, que no entra en
la fórmula, 14,8.

Imponer el aviso a la tabla («possible pluja» en cada hora con aviso) se
descartó: un aviso de tormentas cubre toda la comarca y en un punto concreto
a menudo no llueve, y Juanjo recordó que un plan de Protecció Civil que
mandaba sobre lo calculado dio consejos de lluvia en días secos (ADR 0008 y
0062). Juanjo: «sí, aplica el 2», que el peso del aviso salga de los datos.

La variante del modelo propio con los avisos (ADR 0047) solo aprende del
registro del barrio, que el 16-10-2026 tenía 5 horas de lluvia de las 30 que
necesita, y no tenía los de Meteocat.

## Decisión

- **El aviso entra como señal de la regresión del archivo**, no como regla:
  `avis_aemet` (aviso de AEMET por lluvia o tormentas en el Prelitoral de
  Barcelona que cubre la hora) y, si hay su histórico, `avis_meteocat` y
  `avis_meteocat_alt` (aviso de Meteocat por lluvia o tiempo violento en el
  Vallès Occidental, y de peligro alto o más, grado 3 o más). Se ajusta con
  las mismas previsiones archivadas y la lluvia de Sabadell y Sant Cugat
  (`calibracio/pluja_casa_avisos.py`), sobre el modelo con ECMWF (ADR 0086).
- **Solo cuentan los avisos ya emitidos al prever**: una hora antes del
  tramo a corto plazo y un día antes en la previsión de un día vista. Un
  aviso de AEMET sustituido o cancelado por un mensaje posterior ya emitido
  no cuenta.
- **Se adopta solo si la mejora es segura**: con las mismas muestras, en
  semanas que el modelo no ha visto, se equivoca menos que el modelo sin
  avisos en al menos el 95 % de 2.000 remuestreos por días, a corto plazo y
  un día antes, y la fiabilidad no se separa más de 5 puntos en ningún tramo
  con 150 horas o más. `pluja_casa_avisos.json` lleva `adoptat`; la página
  lo usa solo si es true y la pasada tiene los avisos
  (`aprenentatge.prob_pluja`). Si no, todo sigue como antes.
- **El histórico**: AEMET OpenData (`/api/avisos_cap/archivo`, desde el
  18-06-2018) y la API v2 de Meteocat (`/smp/episodis-oberts?data=…`, la
  misma estructura que lee la página), con `calibracio/avisos_descarrega.py`.
  Las claves son de Juanjo y no van en el repositorio. Los datos de Meteocat
  no se difunden (sus condiciones); se publican solo los pesos.
- **Desde la 3.97.0 el registro apunta también el aviso de Meteocat** de cada
  hora (`avis_meteocat`, `avis_meteocat_alt`; `casa.senyals_avis` y
  `smp.graus_pluja`), para que el modelo propio pueda aprenderlo.

## Alternativas descartadas

- **Que el aviso mande en la tabla** (cielo «possible pluja» y paraguas en las
  horas con aviso): un umbral a ojo que repetiría el error del ADR 0062.
- **Decir solo la contradicción en cada hora**: se puede añadir si hace falta;
  la franja de peligro ya sale encima de esas horas.
- **Esperar al registro del barrio**: meses de otoño hasta las 30 horas de
  lluvia, y sin la historia de 2024-2026.

## Riesgos y limitaciones

- El histórico de Meteocat es el estado final de cada día: un aviso que se
  rebajó o se anuló después no aparece, aunque se conociera al prever.
- La cuota mensual del plan gratuito de Meteocat no está publicada; si es
  baja, los unos 1.000 días del archivo tardarán meses en bajar, y mientras
  el modelo se ajusta solo con AEMET.
- Las horas con aviso son pocas en el archivo: puede que la mejora no llegue
  al 95 % y el modelo no se adopte.

## Validación

`tests/test_registre_casa.py`: las señales de Meteocat de cada hora (lluvia y
peligro alto sí, viento no; sin lectura, None). El ajuste y su resultado se
anotarán aquí cuando haya histórico.
