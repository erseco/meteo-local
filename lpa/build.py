# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate the original Spanish UI with an isolated Las Palmas adapter.

Upstream source files remain byte-for-byte unchanged. Required source anchors
are checked so incompatible upstream changes fail during CI, not at deployment.
"""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
import tempfile

import montflorit
from . import profile as P

HERE = Path(__file__).parent


def replace_once(text, old, new):
    """Fail explicitly when upstream changes a required integration point."""
    if text.count(old) != 1:
        raise ValueError(f"Upstream integration anchor changed: {old[:90]}")
    return text.replace(old, new)


def rebrand(text):
    """Translate identities consistently in JS keys and their Spanish values."""
    for old, new in (
        ("Temps a Montflorit", "Tiempo en Las Palmas"),
        ("Montflorit al dia", "Las Palmas al día"),
        ("Montflorit (Cerdanyola del Vallès)", P.NAME),
        ("Cerdanyola del Vallès", P.NAME), ("Cerdanyola", "Las Palmas"),
        ("Montflorit", P.NAME), ("Bellaterra", P.NAME),
        ("meteo-montflorit.github.io", "erseco.github.io/meteo-local"),
        ("41.482,2.135", "28.124,-15.436"),
    ):
        text = text.replace(old, new)
    # Data are exclusively same-origin; upstream private infrastructure is not used.
    text = re.sub(r'https://bilateria\.org/[^\s\'"<>`)]*', 'fuentes.html', text)
    text = re.sub(r'https://t\.me/[^\s\'"<>`)]*', 'telegram.html', text)
    return text


def static_page(template, title, body):
    scripts = re.findall(r'<script>.*?</script>', template, re.S)
    theme = next((script for script in scripts if 'meteo.fosc' in script), '')
    template = re.sub(r'<main\b[^>]*>.*?</main>', '<main><section class="targeta"><h2>' +
                      html.escape(title) + '</h2>' + body + '</section></main>', template, flags=re.S)
    template = re.sub(r'<script\b[^>]*>.*?</script>', '', template, flags=re.S)
    template = re.sub(r'<button\b[^>]*>.*?</button>', '', template, flags=re.S)
    return template.replace('</head>', theme + '</head>')


def build(destination):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        montflorit.construeix(temp)
        shutil.copytree(temp, dest, dirs_exist_ok=True)
    # The original Spanish pages and shared assets are kept in their expected layout.
    # The root has no duplicate untranslated application.
    for source in (dest / 'es').glob('*.html'):
        text = source.read_text()
        # Public URLs point to this fork; no upstream canonical or Android association.
        text = text.replace('https://meteo-montflorit.github.io/', 'https://erseco.github.io/meteo-local/es/')
        text = re.sub(r'data-notes="[^"]*"', f'data-notes="{P.REPOSITORY}/tree/lpa"', text)
        text = re.sub(r'<nav class="idiomes".*?</nav>', '', text, flags=re.S)
        text = re.sub(r'<link rel="alternate"[^>]*>', '', text)
        text = re.sub(r'<meta name="apple-itunes-app"[^>]*>', '', text)
        text = rebrand(text)
        text = re.sub(r'<p id="app-android".*?</p>', '', text, flags=re.S)
        text = text.replace('https://www.meteo.cat/observacions/radar', P.AEMET_ALERTS).replace('Radar de Meteocat', 'Avisos de AEMET')
        text = re.sub(r'https://github.com/meteo-montflorit/meteo-local/releases[^"<]*', P.REPOSITORY + '/tree/lpa', text)
        notice = ('<section id="lpa-status" class="targeta" aria-label="Estado de las fuentes">'
                  '<h2>Datos para Las Palmas</h2><p>Hora canaria. Previsión de Open-Meteo; los ajustes locales se indican cuando están validados. '
                  'Las observaciones se identifican por estación y antigüedad. El radar no está integrado. '
                  'Los consejos de salida son orientativos; sus umbrales no están validados aquí.</p>'
                  '<p><a href="observaciones.html">Estaciones e historial</a> · <a href="fuentes.html">Fuentes y funciones disponibles</a> · '
                  f'<a href="{P.AEMET_ALERTS}">Avisos oficiales de AEMET</a></p></section>')
        text, count = re.subn(r'(<main\b[^>]*>)', lambda m: m[1] + notice, text)
        if count != 1:
            raise ValueError(f'Expected one main in {source.name}')
        # Replace stale explanatory claims about instruments, learned thresholds and radar.
        if source.name in ('index.html', 'sortir.html'):
            text = re.sub(r'<details\b[^>]*>\s*<summary>.*?(?:D’on surt|D\'on surt|De dónde sale|Cómo se decide|Com es decideix).*?</details>',
                          '', text, flags=re.S)
        text = text.replace('<script src="../comu.js">', '<script src="../lpa-time.js"></script>\n<script src="../comu.js">')
        text = replace_once(text, '</body>', '<script src="../lpa-ui.js"></script>\n</body>')
        if source.name == 'perill.html':
            text, count = re.subn(r'<main\b[^>]*>.*?</main>', '<main>' + notice + '<p>Avisos oficiales de AEMET para Norte de Gran Canaria, recibidos a través de Meteoalarm.</p><p id="avis-dades" hidden></p><section id="perill" aria-live="polite"><p>Cargando avisos…</p></section></main>', text, flags=re.S)
            if count != 1:
                raise ValueError('Upstream warnings layout changed')
            text = re.sub(r'<details\b[^>]*>.*?</details>', '', text, flags=re.S)
            text = text.replace('src="../perill.js"', 'src="../lpa-alerts.js"')
        if source.name in ('riera.html', 'avisos.html', 'telegram.html'):
            key = {'riera.html': 'riera', 'avisos.html': 'notificaciones',
                   'telegram.html': 'notificaciones', 'fiabilitat.html': 'aprenentatge'}[source.name]
            text = static_page(text, 'Función no disponible', '<p>' + html.escape(P.UNAVAILABLE[key]) + '</p>'
                               '<p><a href="./">Volver al tiempo</a> · <a href="fuentes.html">Ver fuentes</a></p>')
        if source.name in ('fonts.html', 'com-funciona.html', 'privacitat.html'):
            text = static_page(text, 'Fuentes, funcionamiento y privacidad', sources_html())
        source.write_text(text)
    (dest / 'es' / 'fuentes.html').write_text(static_page((dest / 'es/fonts.html').read_text(), 'Fuentes y disponibilidad', sources_html()))
    template = (dest / 'es/fonts.html').read_text()
    station_page = static_page(template, 'Observaciones e historial', '<p>Cada lectura corresponde a su estación. Costa, Tafira y aeropuerto tienen condiciones distintas.</p><div id="lpa-observations"><p>Cargando observaciones…</p></div>')
    station_page = re.sub(r'<h1>.*?</h1>', '<h1>Estaciones e historial</h1>', station_page, flags=re.S)
    station_page = station_page.replace('</head>', '<link rel="stylesheet" href="../lpa-style.css"></head>')
    station_page = station_page.replace('</body>', '<script src="../lpa-time.js"></script><script src="../lpa-station-page.js"></script><script src="../lpa-ui.js"></script></body>')
    for name in ('observaciones.html', 'fiabilitat.html'):
        (dest / 'es' / name).write_text(station_page)
    for page in (dest / 'es').glob('*.html'):
        text = page.read_text()
        # Replace the unavailable upstream river tab; keep the mobile bar at five items.
        def station_nav(match):
            nav, count = re.subn(r'<a\b[^>]*href="riera.html"[^>]*>.*?</a>',
                '<a href="observaciones.html"><svg aria-hidden="true"><use href="#i-waves"></use></svg>Estaciones</a>', match[0], flags=re.S)
            if count != 1:
                raise ValueError('Upstream river navigation anchor changed')
            return nav
        text = re.sub(r'<nav class="pagines"[^>]*>.*?</nav>', station_nav, text, flags=re.S)
        page.write_text(text)
    shutil.copyfile(HERE / 'style.css', dest / 'lpa-style.css')
    # Redirect every root HTML entry point to its Spanish counterpart, retaining deep links.
    (dest / 'observaciones.html').touch()
    for path in dest.glob('*.html'):
        path.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Tiempo en Las Palmas</title>'
                        f'<meta http-equiv="refresh" content="0;url=es/{path.name}"><a href="es/{path.name}">Abrir</a>'
                        f'<script>location.replace("es/{path.name}"+location.search+location.hash)</script></html>')
    for path in dest.glob('*.js'):
        text = path.read_text()
        if path.name == 'comu.js':
            text = replace_once(text, "const DADES_URL = 'https://bilateria.org/app/meteo-local/';", 'const DADES_URL = ARREL;')
            text = replace_once(text, 'const CASA_COORD = [41.5, 2.1];', 'const CASA_COORD = [28.124, -15.436];')
            text = replace_once(text, "const SERVIDOR_AVISOS = DADES_URL + 'subscripcio.php';", "const SERVIDOR_AVISOS = 'notificaciones-no-disponibles';")
            text, count = re.subn(r'function blocDadesVelles\(dades\) \{.*?\n\}', '''function blocDadesVelles(dades) {
  const p = element('p', 'avis', 'Datos caducados. Consulte AEMET para la previsión y los avisos vigentes.');
  const a = element('a', null, ' Abrir AEMET');
  a.href = 'https://www.aemet.es/es/eltiempo/prediccion/municipios/palmas-de-gran-canaria-las-id35016';
  p.append(a); return p;
}''', text, flags=re.S)
            if count != 1:
                raise ValueError('Upstream stale-data component changed')
            text, count = re.subn(r'function textActualitzacio\(horari\) \{.*?\n\}', '''function textActualitzacio(horari) {
  return 'Actualización prevista cada 15 minutos. Datos en hora canaria. Si falla una fuente, se indica como no disponible.';
}''', text, flags=re.S)
            if count != 1:
                raise ValueError('Upstream update explanation changed')
            # No history is claimed or manufactured for the new installation.
            text = replace_once(text, "const miraPerill = () => llegeixDades('avisos.json').then((d) => {", "const miraPerill = () => Promise.resolve({historial: []}).then((d) => {")
            text = re.sub(r"if \('serviceWorker' in navigator\) navigator\.serviceWorker\.register\(.*?;", '', text)
        if path.name == 'casa.js':
            text = replace_once(text, 's + probHora(f) * (f.pluja_mm || 0)', 's + (f.pluja_mm || 0)')
            text = replace_once(text, 'function nivellRatxa(ratxa) {', 'function nivellRatxa(ratxa) { return null;')
            text = text.replace('ratxa: 72, calor: 36.8', 'ratxa: Infinity, calor: Infinity')
            text = re.sub(r' A l’hora en curs, el cel és el que s’observa a l’aeroport de Sabadell, si hi veu núvols\.', ' El cielo procede del modelo, sin observación local.', text)
            text = replace_once(text, 'async function calOfertaAvisos() {', 'async function calOfertaAvisos() { return false;')
        if path.name == 'sortir.js':
            text = text.replace('Ara no hi ha dades dels trens.', 'No hay datos de servicio de Guaguas Municipales ni Global.')
            text = replace_once(text, 'const LLINDARS_PLUJA_INICI = { curt: { pluja: 0.4, risc: 0.1 }, llarg: { pluja: 0.6, risc: 0.1 } };', 'const LLINDARS_PLUJA_INICI = { curt: { pluja: 0.5, risc: 0.2 }, llarg: { pluja: 0.5, risc: 0.2 } };')
        if path.name == 'consultes.js':
            text = replace_once(text, 'if (text && avis) caixa.append(enllacAvisos(avis()));', '// LPA: notification backend is unavailable.')
            text = text.replace("Estimació del model europeu CAMS per a una zona d’uns 10 km al voltant de Bellaterra, no mesurada a Montflorit", 'Estimación del modelo global CAMS; no es una medición local ni incluye corrección con estaciones locales')
        if path.name == 'es.js':
            text = text.replace(' A la hora en curso, el cielo es el que se observa en el aeropuerto de Sabadell, si ve nubes.', ' El cielo procede del modelo, sin observación local.')
            text = text.replace('Los milímetros que caerían si llueve.', 'Acumulación prevista por el modelo durante la hora anterior al final del intervalo.')
            text = text.replace('En la cabecera, la probabilidad más alta de sus horas y la lluvia que se espera: los milímetros de cada hora pesados por su probabilidad. No es la suma de la columna Lluvia, que dice lo que caería si llueve.', 'En la cabecera, la probabilidad máxima de las horas y la suma de las acumulaciones previstas. No se vuelven a multiplicar por la probabilidad.')
        if path.name in ('consultes.js', 'es.js'):
            text = text.replace('model europeu CAMS', 'modelo global CAMS').replace('modelo europeo CAMS', 'modelo global CAMS')
            text = text.replace('uns 10 km', 'abast regional').replace('unos 10 km', 'alcance regional')
        # Local calendar operations use the site timezone, including for mainland visitors.
        text = text.replace('new Date(', 'new LpaDate(')
        path.write_text(rebrand(text))
    for source, name in (('time.js', 'lpa-time.js'), ('ui.js', 'lpa-ui.js'), ('alerts.js', 'lpa-alerts.js'), ('station-page.js', 'lpa-station-page.js')):
        shutil.copyfile(HERE / source, dest / name)
    # Never cache weather/alerts or register upstream push handlers.
    (dest / 'sw.js').write_text("// LPA: no offline weather cache or push backend.\n")
    for folder in (dest / '.well-known', dest / 'img'):
        if folder.exists():
            shutil.rmtree(folder)
    manifest = json.loads((dest / 'manifest.webmanifest').read_text())
    manifest.update(name='Tiempo en Las Palmas', short_name='Las Palmas', lang='es', start_url='./es/',
                    description='Previsión para Las Palmas de Gran Canaria, en hora canaria.')
    (dest / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (dest / 'README.md').write_text(f'# Tiempo en Las Palmas\n\nSource: {P.REPOSITORY}/tree/lpa\n\nUpstream: https://github.com/jjdeharo/meteo-local\n')
    return dest


def sources_html():
    items = ''.join(f'<li><strong>{html.escape(k)}</strong>: {html.escape(v)}</li>' for k, v in P.UNAVAILABLE.items())
    return (f'<p>Adaptación de <a href="https://github.com/jjdeharo/meteo-local">meteo-local, de Juanjo de Haro</a>. '
            'Se conserva su interfaz; los adaptadores regionales están separados.</p>'
            '<p>Previsión: <a href="https://open-meteo.com/">Open-Meteo</a>, selección automática best_match, '
            'CC BY 4.0. Aire: CAMS global a través de Open-Meteo, sin corrección local. '
            'Avisos de AEMET a través de Meteoalarm, zona Norte de Gran Canaria. '
            'Observaciones de AEMET, METAR de NOAA, GRAFCAN y estaciones escolares y particulares en Weathercloud y Weather Underground. '
            'Polen y esporas: recuentos fechados de SEAIC; sismicidad: GeoRSS del IGN. '
            'La disponibilidad y antigüedad de cada lectura se muestran en Estaciones. Los ajustes de temperatura requieren validación temporal; los consejos de salida no tienen validación local.</p>'
            f'<p>Ubicación aproximada: {P.COORDINATES}; zona horaria {P.TIMEZONE}. '
            'Los datos no representan todos los microclimas del municipio.</p>'
            '<p>La página consulta solo los JSON de su propio alojamiento. Preferencias de interfaz en '
            'el almacenamiento del navegador. Sin suscripciones, Telegram ni servicio push propio. '
            'Los enlaces externos aplican sus propias condiciones.</p><ul>' + items + '</ul>'
            f'<p><a href="{P.REPOSITORY}/tree/lpa">Código AGPL-3.0-or-later</a>; contenidos CC BY-SA 4.0; '
            'iconos Lucide ISC. No se modifica la licencia del proyecto original.</p>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    build(parser.parse_args().destination)
