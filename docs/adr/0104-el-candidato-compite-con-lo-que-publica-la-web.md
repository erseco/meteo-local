# 104. El candidato compite con lo que publica la web

Fecha: 2026-10-19 · Estado: aceptado

## Contexto

La evaluación de los métodos del 18-10-2026 (informe de Codex,
`Informes/meteo-local/2026-10-18-evaluacion-metodos-prediccion.md`, apartado
6, hallazgo 2) señalaba que el competidor del aprendizaje no siempre es el
que sirve la web: `valida_pluja` comparaba el candidato local con los
coeficientes del archivo de tres modelos (`pluja_casa.json`), y
`prob_pluja`, al publicar, usa la variante con ECMWF (`pluja_casa_ecmwf.json`,
ADR 0086) cuando la pasada la tiene, o la de los avisos si está adoptada
(ADR 0097). Un candidato podía entrar o quedarse fuera por compararse con un
modelo que nadie usa. Juanjo pidió empezar por este punto («sí, empieza por
el 1», 19-10-2026).

## Evidencia

Con el registro del NAS copiado a la carpeta de trabajo de la sesión (del
05-10 al 19-10-2026, `casa-2026-10.jsonl` y las estaciones), sin tocar el
repositorio:

- 5.880 muestras con lluvia observada y 12 horas de lluvia distintas; la
  mitad (2.941) lleva la lluvia de ECMWF, así que la web publicó con la
  variante en la mitad de las horas.
- Brier de los coeficientes de tres modelos (el competidor hasta ahora):
  0,03975. Brier de lo que publica la web con el archivo: 0,04282. En las
  horas con ECMWF, 0,0565 frente a 0,0626: estas dos semanas la variante
  acierta algo menos que el modelo de siempre, con 12 horas de lluvia, que
  no permiten concluir nada sobre ECMWF (el archivo 2024-2026 le da un 2,6 %
  de mejora a corto plazo y un 5,5 % a un día).
- El candidato local da 0,0792: lejos de los dos, como decía el informe
  (faltan 18 horas de lluvia para el mínimo de 30).

La temperatura ya comparaba bien: `valida_temperatura` usa
`temperatura()`, la misma función que corrige la tabla.

## Decisión

- **`error_abans` de `valida_pluja` es el Brier de `prob_pluja` con el
  modelo del archivo**, muestra a muestra: la variante de los avisos si está
  adoptada y la pasada la tiene, si no la de ECMWF, si no los tres modelos.
  Es lo que la web publicaría hoy para esas horas, con los mismos datos.
  `prob_pluja` admite las variantes ya leídas (`variants_arxiu()`) para no
  abrir los archivos miles de veces.
- **Las variantes propias (Sant Cugat, vecinas, avisos) siguen comparándose
  con el base propio ajustado en sus mismas horas** (`valida_variant`, ADR
  0057), además de con el archivo publicado.
- **El modelo propio en uso no se congela**: `diari` lo reajusta cada día
  con todo lo registrado («mismo método, más datos»). Por eso, entre
  métodos propios, el competidor justo es el otro método ajustado y
  comprobado por validación cruzada en las mismas semanas, no unos pesos de
  un día concreto. El archivo sí está congelado, y se compara tal como se
  publica.
- La columna `error_pluja_arxiu` de `historial.csv` pasa a ser este Brier
  de lo publicado; las filas anteriores a la 3.144.0 llevan el de tres
  modelos y no son comparables.

## Alternativas descartadas

- **La probabilidad que de verdad se publicó** (`mostrat.probabilitat` del
  registro): es la cifra más fiel al servicio, pero mezcla el radar de las
  dos primeras horas, la hora en curso y las versiones anteriores del
  programa, y no se puede recalcular con los mismos datos que el candidato.
  Queda como comprobación del acierto en «Com encerta», no como competidor.
- **Congelar el modelo propio y comparar solo en los días posteriores a su
  adopción**: con el reajuste diario, el periodo posterior sería siempre de
  un día. La comprobación en periodos posteriores es el punto 3 del informe
  (avance temporal), pendiente.

## Pendiente

- Hallazgo 1 del informe: una sola regla de mejora para todo el programa
  (remuestreo por bloques de días en lugar del 5 %).
- Hallazgo 3: validación con avance temporal y episodios que no crucen el
  límite de una semana.
- El candidato local no lleva la lluvia de ECMWF entre sus señales
  (`RASGOS_PROPIS`) y compite con un modelo que sí la usa en la mitad de las
  horas: una variante propia con ECMWF es posible, sin decidir.

## Validación

- `tests/test_aprenentatge.py`
  (`test_el_competidor_es_el_que_publica_la_web`: con la mitad de las
  muestras con ECMWF, `error_abans` es el Brier de `prob_pluja` y no el de
  los tres modelos). Las pruebas del proyecto en verde.
- La medida con el registro real, arriba, con el código nuevo
  (`aprenentatge.valida_pluja`) y con el cálculo a mano: mismas cifras.
