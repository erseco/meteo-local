# 111. El uso de IA explicado en «Fonts i crèdits» y las condiciones de las fuentes

Fecha: 2026-10-20 · Estado: aceptado

## Contexto

La evaluación VCER de la 3.166.2 (rúbrica de la guía «Vibe coding
responsable», 20-10-2026) dio «Recomendable (85 %)» y señaló tres mejoras:
textos que ya no coincidían con el código, fuentes y condiciones de uso que
faltaban en «Fonts i crèdits», y una nota de IA que no decía qué comprueba la
persona. Juanjo pidió aplicar las dos primeras, quitar el nivel del MIAE del
pie y poner la frase sobre lo que él hace fuera del pie, donde decidiera el
agente («no debe ir en el pie, mira donde ponerlo»).

Textos que no coincidían con el código:

- «Fonts i crèdits» decía que el aviso de Meteocat se lee «mentre hi ha un pla
  de Protecció Civil a la vista»; desde el 11-10-2026 se lee en cada pasada
  (`casa.py`, ADR 0071) y por fenómeno manda Meteocat (ADR 0093).
- «Com funciona» decía «La web té quatre pàgines» y no contaba «Riera»
  (ADR 0107) ni «Fiabilitat» (ADR 0110).
- «Com funciona» decía que no interviene ninguna IA generativa, sin contar el
  revisor de coherencia (`revisor.py`, ADR 0101), que usa Claude y puede
  quitar líneas falsas o caducadas de lo publicado.
- El README hablaba de tres estaciones vecinas; son cuatro (`config.VEINES`).

## Decisión

- **Pie**: «Fet amb IA (Claude Code, octubre de 2026).», sin el nivel del
  MIAE (decisión de Juanjo), con «Fet amb IA» enlazado a la sección nueva.
  También sin el nivel en los README y en la ficha de Google Play.
- **«Com s'ha fet»**, sección nueva de «Fonts i crèdits», antes de «Codi font
  i decisions» (lugar elegido por el agente: es la página de cómo está hecha
  la web y ya la enlaza el pie): la web se programa con IA; el autor dirige el
  contenido y el funcionamiento y revisa el resultado en pantalla; los
  cálculos los hace un programa sin IA y cada método nuevo se comprueba con
  datos reales; el revisor con IA solo puede quitar líneas y propone lo demás
  al autor. «Com funciona» remite a ella al hablar de la IA.
- **Fuentes que faltaban**: las previsiones por horas de Meteocat (API) y de
  AEMET OpenData que compara «Fiabilitat», y las seis estaciones de Sant Cugat
  de Weather Underground del aviso de la riera (`config.RIERA_VEINES`).
- **Condiciones**: una frase en la entrada (se reutilizan según las
  condiciones de AEMET, Meteocat y la Generalitat, sin alterarlas y citando la
  fuente), la cita que pide AEMET para servicios de valor añadido y el
  servicio gratuito de RainViewer.

## Alternativas descartadas

- **La frase sobre lo que hace el autor en el pie**: Juanjo no la quiere ahí.
- **En «Com funciona»**: explica el método de cálculo; cómo se ha hecho la web
  encaja con los créditos y el código fuente.

## Evidencia

Condiciones consultadas el 20-10-2026:

- AEMET, nota legal (<https://www.aemet.es/ca/nota_legal>): para servicios de
  valor añadido, «Informació elaborada utilitzant, entre altres, l'obtinguda
  de l'Agència Estatal de Meteorologia»; no alterar el sentido ni dar a
  entender que AEMET participa.
- Meteocat, avís legal (<https://www.meteo.cat/wpweb/avis-legal/>), apartado
  «Informació continguda a Meteocat»: la información que ofrece libremente se
  puede usar según la Llei 18/2015 (ADR 0019 y 0067).
- Generalitat (pie de interior.gencat.cat): permite reutilizar contenidos y
  datos citando la fuente y la fecha de actualización, sin desnaturalizarlos.
- RainViewer (<https://www.rainviewer.com/api.html>): el servicio gratuito es
  para proyectos personales, educativos y comunitarios, con un crédito visible
  y enlazado; la portada ya lo pone junto a la imagen del radar.

## Riesgos y limitaciones

- **e-distribución**: su aviso legal
  (<https://www.edistribucion.com/es/aviso-legal.html>) no autoriza
  «comunicar públicamente la información contenida en la Web» sin permiso del
  titular. La web muestra los cortes que publica su mapa (ADR 0072). Queda
  para que decida Juanjo; no se ha cambiado nada.
- No se han encontrado las condiciones de Meteoalarm (los avisos son de AEMET
  y se citan con las suyas) ni las del Consorci de Collserola.

## Validación

- `python3 -m unittest discover -s tests -b` y la web generada con
  `montflorit.py web` revisada en catalán y castellano; axe-core sobre
  «Fonts i crèdits» y «Com funciona».
