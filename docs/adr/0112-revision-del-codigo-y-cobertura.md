# 112. Revisión del código (Ruff y ESLint) y cobertura de las pruebas

Fecha: 2026-10-20 · Estado: aceptado

## Contexto

Un desarrollador comentó a Juanjo (20-10-2026) lo primero que mira en un
proyecto así: que tenga pruebas, que se pasen en GitHub con cada cambio, que
haya una revisión automática del código (lint) y que se mida la cobertura,
porque así la IA mejora y encuentra errores; y Dependabot para las
dependencias. El repositorio tenía las pruebas (624) y las pasaba en GitHub
(`.github/workflows/previsio.yml`); no tenía lint ni medía la cobertura.
Juanjo pidió hacer el lint y la cobertura; Dependabot quedó para más
adelante, porque las únicas dependencias son numpy y Pillow (sin versión
fija), las acciones de GitHub y la imagen del contenedor del NAS.

## Decisión

- **Python, con Ruff** (`ruff.toml`): solo las reglas que buscan errores,
  `F` (pyflakes: nombres sin definir, importaciones y variables que sobran),
  `B` (bugbear: trampas habituales) y `E9` (sintaxis). Sin `B905` (`zip` sin
  `strict`): el código junta a propósito listas de distinta longitud. Las de
  estilo (604 avisos con las reglas por defecto de Ruff 0.17, casi todos de
  forma) no se aplican: el código es denso a propósito.
- **JavaScript de la web, con ESLint** (`eslint.config.mjs`): las reglas
  recomendadas. Las páginas cargan scripts clásicos que comparten el ámbito
  global; los nombres que declaran arriba del todo `web/comu.js`,
  `web/grafica.js` y `montflorit/es.js` se leen de esos mismos archivos, para
  no mantener la lista a mano. Se permiten los espacios no separables en los
  textos («35 mm»), los `catch` vacíos (el navegador que no deja guardar) y la
  desestructuración para quitar un campo.
- **Cobertura, con coverage.py** (`.coveragerc`): qué parte del programa
  recorren las pruebas, sin las propias pruebas ni las comprobaciones
  puntuales (`calibracio/`, `eines/`). Se mide en cada cambio y sale en el
  resumen de la acción de GitHub.
- **En GitHub**, en la acción de pruebas: Ruff y ESLint antes de las pruebas
  y la cobertura después, con **versiones fijas** (Ruff 0.17.1, ESLint
  9.39.1, globals 16.5.0, coverage 7.16.2). El NAS solo despliega un commit
  con todas las comprobaciones en verde (`desplegament.py`, ADR 0038): un
  aviso de lint para la publicación, como una prueba que falla. Por eso las
  versiones van fijas: una versión nueva con reglas nuevas no puede parar la
  publicación sin que nadie haya tocado el código.
- **La cobertura no para nada**: no hay mínimo. Un mínimo pararía la
  publicación de un arreglo urgente porque le faltan pruebas; la cifra sirve
  para saber dónde faltan.

## Lo que encontró la primera pasada

Arreglado en la misma versión:

- `montflorit/es.js`: cinco traducciones repetidas («Pluja», «Avís {0}»,
  «avui», «demà», «a {0}»), con el mismo texto: en un objeto de JavaScript
  manda la última, así que una traducción cambiada en la primera no habría
  salido nunca.
- `web/sortir.js`: una función que no se usaba (`nomesAvis`).
- `montflorit.py`: el bucle que escribe las páginas llamaba `html` a cada
  página y tapaba el módulo `html` dentro de la función (hoy no se usaba ahí).
- `wunderground.py`: el error de la clave caducada se lanza con `from ex`,
  para que el registro diga también el error original.
- `aprenentatge.py`, `prevision.py`: dos funciones dentro de un bucle que
  usaban la variable del bucle; se llaman en la misma vuelta (no era un
  fallo), pero ahora la reciben como argumento. En `bot/push.py`, tres casos
  iguales llevan `# noqa: B023`: `prova()` llama la función al momento.
- 16 importaciones que sobraban y variables sin usar en las comprobaciones de
  `calibracio/`.

Falsos avisos, marcados en el código: `repintaAvisos` en `web/comu.js` (la
define la página que la tiene, y se mira antes con `typeof`) y `local` en
`calibracio/veines_model.py` (llega por `exec` de `veines_regles.py`).

Cobertura de partida: **81 %** del código de Python (10.439 instrucciones).
Lo menos cubierto es lo que lee fuentes de fuera: `casa.py` (48 %),
`boira.py` (46 %), `ecowitt.py` (51 %), `grafica_imatge.py` (51 %).

## Alternativas descartadas

- **Todas las reglas de Ruff**: 604 avisos, casi todos de estilo; cambiar
  medio programa sin arreglar nada.
- **Un mínimo de cobertura que pare la publicación**: ver arriba.
- **Cobertura del JavaScript** (c8 o la de Playwright): las pruebas de la web
  son de Python y de página (`probar-web`); medirla exigiría montar otra
  forma de pasarlas. Se puede añadir si un día hay pruebas de JavaScript.
- **Dependabot**, de momento: aportaría poco con tan pocas dependencias.

## Consecuencias

- Antes de subir un cambio: `ruff check .` y `npx eslint web montflorit
  eslint.config.mjs` (con ESLint instalado en la carpeta, `npm install
  --no-save --no-package-lock eslint@9.39.1 globals@16.5.0`; `node_modules`
  no se sube), además de las pruebas (AGENTS.md y README).
- Para subir de versión Ruff o ESLint: probar en local, arreglar lo que salga
  y cambiar la versión en la acción en el mismo commit.

## Evidencia

- Ruff 0.17.1, ESLint 9.39.1 y coverage 7.16.2 en el portátil de Juanjo,
  sobre el commit 8734fbc (3.169.1).

## Riesgos y limitaciones

- La lista de nombres compartidos de ESLint sale de una expresión regular
  sobre las declaraciones de arriba del todo: un nombre global creado de otra
  forma (`window.x = …`) daría un falso aviso, que se ve al momento.

## Validación

- `ruff check .` y ESLint sin avisos; las 624 pruebas pasan, también dentro
  de coverage; la acción de GitHub en verde con los cuatro pasos.
- La web en Chromium, Firefox y WebKit tras los cambios de `es.js`,
  `comu.js` y `sortir.js`.
