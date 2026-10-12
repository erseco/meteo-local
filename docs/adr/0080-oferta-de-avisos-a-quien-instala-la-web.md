# 80. Oferta de avisos a quien instala la web

Fecha: 2026-10-12 · Estado: aceptado

## Contexto

Juanjo preguntó si quien instala la web en el móvil recibe algún aviso por
defecto (no: hasta que entra en «Avisos» y los activa, ninguno) y si se podía
activar alguno sin que lo hiciera él.

No se puede: el navegador no deja enviar notificaciones sin el permiso de la
persona, y ese permiso solo se puede pedir cuando toca un botón; si se pide al
abrir la página, el móvil lo bloquea o lo esconde. Lo que sí se puede es
ofrecerlo en un solo toque, en el momento en que tiene más sentido (Juanjo:
«si, hazlo»).

## Decisión

Versión 3.71.0.

- **Una tarjeta en la portada, bajo «Ara», sin ventana**:
  > **Avisos de perill al mòbil**
  > Riera, incendis, avisos oficials i temps extrem a Montflorit, al moment.
  > [Activa-ho] · [Ara no]
- **Solo a quien tiene la web instalada** (`display-mode: standalone`, o
  `navigator.standalone` en iPhone), que aún no tiene los avisos activados en
  ese dispositivo, no ha dicho «Ara no» y no tiene las notificaciones
  bloqueadas (`calOfertaAvisos`).
- **«Activa-ho»**: pide el permiso y, si lo da, activa los dos avisos que ya
  vienen marcados en «Avisos» (`AVISOS_PER_DEFECTE`: peligro y riera), sin
  pasar por esa página. Para añadir otros, la campana.
- **«Ara no»**: quita la tarjeta y no vuelve a salir en ese dispositivo
  (`meteo.oferta-avisos`).
- **Lo común para activar los avisos** (las llamadas al servidor, su clave y
  la suscripción) pasa de `avisos.js` a `comu.js`, para que lo usen las dos
  sin repetirlo.

## Alternativas descartadas

- **Activar avisos sin que la persona haga nada**: imposible; el navegador no
  lo permite.
- **Pedir el permiso al abrir la web**: el navegador lo bloquea o lo esconde
  si no viene de un toque, y Juanjo no quiere que nada interrumpa a quien
  llega a leer.
- **Ofrecerlo a todo el mundo, también en el navegador**: quien solo mira la
  web de paso ya tiene la invitación enlazada («…activa els avisos»).

## Consecuencias

- Quien instala la web puede tener los avisos de peligro con un toque.
- El servidor de avisos recibe las altas igual que desde «Avisos».

## Riesgos y limitaciones

- El alta completa (permiso y suscripción real) no se ha probado de forma
  automática: daría de alta un dispositivo de prueba en el servidor real.
  Usa las mismas funciones que la página «Avisos», que funciona. Queda por
  verla en un móvil de verdad.
- iPhone: solo con la web añadida a la pantalla de inicio (iOS 16.4 o
  posterior), como los avisos en general (ADR 0048).

## Validación

- Prueba `test_oferta_d_avisos_nomes_a_qui_te_la_web_installada`: sale solo
  con la web instalada, sin avisos, sin «Ara no» y sin bloqueo.
- Chromium con la web «instalada» simulada: la tarjeta sale bajo «Ara»; «Ara
  no» la quita y no vuelve al recargar; «Avisos» sigue funcionando (botón
  «Activa els avisos», sin errores de JavaScript).
- axe-core sin incidencias en la portada (catalán y castellano) y en
  «Avisos», con tema claro y oscuro.

## Ampliación del 12-10-2026 (3.71.1): sin «al mòbil»

Juanjo, con una captura del ordenador: «pone avisos al mòbil, pero esta
captura está sacada de un ordenador». Los avisos llegan también al ordenador.
La campana se llama ahora «Avisos» (el nombre de su página); la tarjeta,
«Avisos de perill»; en «Privacitat», «Avisos al mòbil o a l'ordinador»; en
«Perill», «…arriben al mòbil, a l'ordinador i a Telegram».

