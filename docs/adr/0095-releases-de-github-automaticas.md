# 95. Las releases de GitHub las crea una acción con cada etiqueta

Fecha: 2026-10-16 · Estado: aceptado

## Contexto

El enlace «versió» del pie de la web lleva a la release de esa versión en
GitHub (`montflorit.NOTES`, ADR 0028). Las releases se creaban a mano al
publicar, con el mensaje del commit de la versión como notas, y dejaron de
crearse después de la v3.63.0 (11-10-2026): desde entonces solo se ponían
las etiquetas. Al publicar la 3.91.0 se vio que faltaban 63 releases y que
el enlace del pie llevaba a una página que no existía. Juanjo: «el 1 hay que
arreglarlo».

## Decisión

- **Las 63 releases que faltaban se han creado** (v3.64.0 a v3.91.0), cada
  una con el título de su etiqueta y, como notas, el mensaje del commit
  etiquetado, igual que las anteriores. Su fecha de publicación es el
  16-10-2026; la de la etiqueta es la real.
- **Una acción de GitHub crea la release con cada etiqueta `v*`**
  (`.github/workflows/release.yml`): título de la etiqueta y mensaje del
  commit etiquetado; si la release ya existe, no hace nada. Una norma escrita
  que hay que recordar no se cumple: el mecanismo lo hace solo.
- Publicar una versión sigue siendo subir `VERSION`, hacer el commit y poner
  la etiqueta (`git tag vX.Y.Z` y `git push --tags`); nada más.

## Alternativas descartadas

- **Crearlas desde `publica.sh` en el NAS**: el NAS publica la web, no el
  código, y no tiene permiso de escritura sobre el repositorio del código.
- **Que el pie enlace la lista de releases** en lugar de la versión: la lista
  ya está en «Fonts i crèdits» y el pie debe llevar a las notas de la versión
  que se está viendo (ADR 0028).

## Consecuencias

- La acción se estrena con la primera etiqueta posterior a este ADR; si
  fallara, el enlace del pie volvería a romperse, así que al publicar la
  siguiente versión se comprueba una vez que la release existe.
