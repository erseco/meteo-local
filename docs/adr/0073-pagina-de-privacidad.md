# 73. Página de privacidad

Fecha: 2026-10-11 · Estado: aceptado

## Contexto

Juanjo preguntó si los datos que recogen la web, Telegram y la app debían ir
en una página aparte o si bastaba con «Fonts i crèdits». Lo que había estaba
repartido en tres sitios (un párrafo en «Fonts i crèdits», bajo «Avís», y
notas en «Avisos» y «Telegram») y faltaba información: el aviso a Juanjo de
cada alta y baja del canal llevaba el nombre y el @usuario de la persona, el
bot guarda también el idioma y la fecha de alta, no se decía que la web no usa
cookies ni contadores ni que las preferencias se quedan en el dispositivo, ni
que los servidores registran la IP, ni quién es el responsable y cómo
contactar.

## Decisión

- **Página propia, «Privacitat»** (`web/privacitat.html`; «Privacidad» en
  castellano), enlazada en el pie de todas las páginas junto a «Fonts i
  crèdits». Corta, en una pantalla, con la idea principal delante y destacada
  con una franja (no en negrita): «Aquesta web no recull dades de qui la
  visita: no fa servir galetes, ni estadístiques de qui la fa servir, ni
  comptadors de visites, ni publicitat, i no carrega res d'altres webs»
  (Juanjo: «también habría que decir que no se recopilan datos, ni
  estadísticas, ni cookies», «estadísticas de los usuarios, se entiende»).
  Después, quién la hace y el contacto (el correo de Juanjo), lo que se queda
  en el dispositivo, los servidores, los avisos del navegador, el bot, el
  canal y para qué.
- **El recuento de órdenes del bot** se dice tal cual («sense saber qui»): no
  es una estadística de usuarios.
- **Sin el nombre en el aviso de altas y bajas del canal** (Juanjo: «quita el
  nombre»): solo el total. Así es cierto que «aquesta web només en compta el
  total».
- «Fonts i crèdits» ya no habla de datos personales; «Avisos» y «Telegram»,
  en una línea con el enlace a «Privacitat».

## Validación

- Comprobado en el código y en las cabeceras de los servidores que la web no
  pone cookies, no tiene contadores ni estadísticas y no carga recursos de
  terceros.
- `tests/test_bot.py`: el aviso de altas del canal, sin el nombre.
- La página en catalán y castellano, en el móvil; axe-core sin incidencias.
