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
from .public_data import SITE, DESCRIPTION, dataset

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


HOME = (
    '<main id="lpa-home">'
    '<div id="lh-alerts" aria-live="polite"></div>'
    '<section id="lh-now" class="lh-hero lh-sky-cloud" aria-label="El tiempo ahora"><p>Cargando el tiempo…</p></section>'
    '<section id="lh-hours" class="lh-card"><h2>Próximas 48 horas</h2><p class="lh-empty">Cargando previsión…</p></section>'
    '<div class="lh-top">'
    '<section id="lh-days" class="lh-card"><h2>7 días</h2></section>'
    '<section id="lh-radar" class="lh-card"><h2>Radar de Canarias</h2><p class="lh-empty">Cargando radar…</p></section>'
    '</div><div class="lh-grid">'
    '<section id="lh-wind" class="lh-card"><h2>Viento</h2></section>'
    '<section id="lh-calima" class="lh-card"><h2>Calima</h2></section>'
    '<section id="lh-sea" class="lh-card"><h2>Mar</h2></section>'
    '<section id="lh-sun" class="lh-card"><h2>Sol y UV</h2></section>'
    '<section id="lh-stations" class="lh-card"><h2>Medido ahora</h2></section>'
    '<section id="lh-air" class="lh-card"><h2>Calidad del aire</h2></section>'
    '</div></main>')


def footer():
    """One informative footer for every page; keeps the upstream credit and version link."""
    def links(items):
        return '<ul>' + ''.join(f'<li><a href="{href}">{html.escape(text)}</a></li>' for text, href in items) + '</ul>'
    return ('<footer class="peu lpa-footer">'
            '<div class="lf-brand"><p class="lf-title">Tiempo en Las Palmas</p>'
            '<p>Previsión, radar, viento, calima y mar en hora canaria. Proyecto independiente: '
            'no es una web oficial ni sustituye los avisos de AEMET.</p>'
            f'<p><a id="versio" href="{P.REPOSITORY}/tree/lpa" target="_blank" rel="noopener">versión lpa-{P.VERSION}</a></p></div>'
            '<nav aria-label="Más páginas"><p class="lf-head">Explorar</p>' + links((
                ('El tiempo', './'), ('Radar y mar', 'radar.html'), ('Avisos', 'perill.html'),
                ('Estaciones', 'observaciones.html'), ('Consultas', 'consultes.html'), ('Si sales', 'sortir.html'))) + '</nav>'
            '<div><p class="lf-head">Datos</p>' + links((
                ('Fuentes y créditos', 'fuentes.html'), ('Datos abiertos', 'datos.html'), ('JSON', 'weather.json'),
                ('Privacidad', 'privacitat.html'), ('Avisos oficiales de AEMET', P.AEMET_ALERTS))) + '</div>'
            '<div><p class="lf-head">Créditos</p>'
            '<p>Open-Meteo (CC BY 4.0), AEMET, CAMS, GRAFCAN y Puertos del Estado.</p>'
            '<p>Basado en <a href="https://github.com/jjdeharo/meteo-local">meteo-local</a> de Juan José de Haro. '
            'Código <a href="https://www.gnu.org/licenses/agpl-3.0.html">AGPL v3</a> · contenidos '
            '<a href="https://creativecommons.org/licenses/by-sa/4.0/deed.es">CC BY-SA 4.0</a>.</p></div>'
            '</footer>')


def build(destination):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        montflorit.construeix(temp)
        spanish_names = [page.name for page in (Path(temp) / 'es').glob('*.html')]
        shutil.copytree(temp, dest, dirs_exist_ok=True)
    # The original Spanish pages and shared assets are kept in their expected layout.
    # Spanish output is staged in es/ and promoted to the root below.
    for name in spanish_names:
        source = dest / 'es' / name
        text = source.read_text()
        # Public URLs point to this fork; no upstream canonical or Android association.
        text = text.replace('https://meteo-montflorit.github.io/', SITE)
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
                  'Las observaciones y las imágenes del radar se identifican por su antigüedad. '
                  'Los consejos de salida son orientativos; sus umbrales no están validados aquí.</p>'
                  '<p><a href="observaciones.html">Estaciones e historial</a> · <a href="radar.html">Radar y mar</a> · <a href="fuentes.html">Fuentes y funciones disponibles</a> · '
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
        if source.name == 'index.html':
            # The visual home replaces the upstream forecast page; comu.js keeps theme, menus and data loading.
            text, count = re.subn(r'<main\b[^>]*>.*?</main>', lambda m: HOME, text, flags=re.S)
            if count != 1:
                raise ValueError('Upstream home layout changed')
            for script in ('grafica.js', 'casa.js'):
                text = replace_once(text, f'<script src="../{script}"></script>', '')
            text = re.sub(r'<p class="ruta">.*?</p>', '<p class="ruta">Previsión, radar, viento, calima y mar, en hora canaria.</p>', text, flags=re.S)
            text = replace_once(text, '</head>', '<link rel="stylesheet" href="../lpa-style.css"><link rel="stylesheet" href="../lpa-home.css"></head>')
            text = replace_once(text, '</body>', '<script src="../lpa-home.js"></script></body>')
        if source.name == 'perill.html':
            text, count = re.subn(r'<main\b[^>]*>.*?</main>', '<main>' + notice + '<p>Avisos oficiales de AEMET para Norte de Gran Canaria, recibidos a través de Meteoalarm.</p><p id="avis-dades" hidden></p><section id="perill" aria-live="polite"><p>Cargando avisos…</p></section></main>', text, flags=re.S)
            if count != 1:
                raise ValueError('Upstream warnings layout changed')
            text = re.sub(r'<details\b[^>]*>.*?</details>', '', text, flags=re.S)
            text = text.replace('src="../perill.js"', 'src="../lpa-alerts.js"')
        if source.name in ('avisos.html', 'telegram.html'):
            key = 'notificaciones'
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
    radar_page = static_page(template,'Radar y mar',
        '<p>Imágenes observadas de AEMET y gráficos de Puertos del Estado. Consulte la fecha y el tipo de dato.</p>'
        '<section id="lpa-radar"><h2>Radar de Canarias</h2><p>Cargando radar…</p></section>'
        '<section id="lpa-marine"><h2>Mar y puerto</h2></section>')
    radar_page = re.sub(r'<h1>.*?</h1>','<h1>Radar y mar</h1>',radar_page,flags=re.S)
    radar_page = radar_page.replace('</head>','<link rel="stylesheet" href="../lpa-style.css"></head>')
    radar_page = radar_page.replace('</body>','<script src="../lpa-time.js"></script><script src="../lpa-station-page.js"></script><script src="../lpa-ui.js"></script><script src="../lpa-extras.js"></script></body>')
    (dest / 'es/radar.html').write_text(radar_page)
    data_page=static_page(template,'Datos abiertos',
        '<p>Previsión y observaciones con fecha, unidades y fuente.</p>'
        '<p><a href="../weather.json">Descargar JSON</a> · <a href="../llms.txt">Guía de consulta para asistentes</a></p>'
        '<div id="lpa-public-snapshot"><p>La próxima recogida publicará aquí los datos.</p></div><!-- snapshot-end -->')
    data_page=re.sub(r'<h1>.*?</h1>','<h1>Datos del tiempo</h1>',data_page,flags=re.S)
    data_page=data_page.replace('</head>','<script id="lpa-dataset" type="application/ld+json">'+json.dumps(dataset(),ensure_ascii=False)+'</script></head>')
    (dest/'es/datos.html').write_text(data_page)
    for page in (dest / 'es').glob('*.html'):
        text = page.read_text()
        # Replace the river tab (no Canary equivalent) and the outing advice with stations and radar;
        # keep the mobile bar at five items.
        def station_nav(match):
            nav = match[0]
            for old, new in (('riera.html', '<a href="observaciones.html"><svg aria-hidden="true"><use href="#i-waves"></use></svg>Estaciones</a>'),
                             ('sortir.html', '<a href="radar.html"><svg aria-hidden="true"><use href="#i-radar"></use></svg>Radar</a>')):
                nav, count = re.subn(r'<a\b[^>]*href="' + re.escape(old) + r'"[^>]*>.*?</a>', new, nav, flags=re.S)
                if count != 1:
                    raise ValueError(f'Upstream navigation anchor changed: {old}')
            return nav
        text = re.sub(r'<nav class="pagines"[^>]*>.*?</nav>', station_nav, text, flags=re.S)
        if page.name == 'radar.html':
            text = re.sub(r'(<nav class="pagines".*?<a href="radar.html")', r'\1 aria-current="page"', text, flags=re.S)
        text, count = re.subn(r'<footer class="peu">.*?</footer>', lambda m: footer(), text, flags=re.S)
        if count > 1:
            raise ValueError('Unexpected footer layout')
        # Keep public metadata alongside the original interface.
        text=re.sub(r'<meta name="description"[^>]*>','<meta name="description" content="'+html.escape(DESCRIPTION,quote=True)+'">',text)
        text=re.sub(r'<meta name="robots"[^>]*>','',text)
        text=re.sub(r'<link rel="canonical"[^>]*>','',text)
        canonical=SITE+('' if page.name=='index.html' else page.name)
        title={'index.html':'Tiempo en Las Palmas · 7 días','radar.html':'Radar y mar · Las Palmas',
            'observaciones.html':'Estaciones meteorológicas · Las Palmas','datos.html':'Datos del tiempo · Las Palmas',
            'perill.html':'Avisos meteorológicos · Las Palmas','sortir.html':'Si sales · Las Palmas',
            'fiabilitat.html':'Historial y fiabilidad · Las Palmas','consultes.html':'Consultar el tiempo · Las Palmas'}.get(page.name,'Fuentes y funcionamiento · Las Palmas')
        text=re.sub(r'<title>.*?</title>','<title>'+title+'</title>',text,flags=re.S)
        robots='index,follow' if page.name in ('index.html','radar.html','observaciones.html','datos.html','perill.html','fuentes.html') else 'noindex,follow'
        meta=('<meta name="robots" content="'+robots+'">'
              '<link rel="canonical" href="'+canonical+'">'
              '<link rel="alternate" type="application/json" title="Datos meteorológicos" href="../weather.json">'
              '<meta property="og:type" content="website"><meta property="og:locale" content="es_ES">'
              '<meta property="og:url" content="'+canonical+'">'
              '<meta property="og:title" content="'+title+'">'
              '<meta property="og:description" content="'+html.escape(DESCRIPTION,quote=True)+'">')
        if page.name=='index.html':
            meta+='<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'WebSite',
                'name':'Tiempo en Las Palmas','url':SITE,'inLanguage':'es',
                'description':DESCRIPTION,'hasPart':{'@type':'Dataset','@id':SITE+'datos.html#dataset','url':SITE+'datos.html'}},ensure_ascii=False)+'</script>'
        text=text.replace('</head>',meta+('' if '../lpa-style.css' in text else '<link rel="stylesheet" href="../lpa-style.css">')+'</head>')
        page.write_text(text)
    shutil.copyfile(HERE / 'style.css', dest / 'lpa-style.css')
    # Barranco floods are not modelled here: the upstream river page only redirects home.
    (dest / 'es' / 'riera.html').write_text(redirect_page('./'))
    # Promote the generated Spanish pages; keep /es/ as redirects only.
    spanish_pages = list((dest / 'es').glob('*.html'))
    names = {page.name for page in spanish_pages}
    for page in dest.glob('*.html'):
        if page.name not in names:
            page.unlink()
    for page in spanish_pages:
        text = page.read_text().replace(montflorit.IDIOMA_RECORDAT, '')
        text = text.replace('data-arrel="../"', 'data-arrel="./"')
        text = re.sub(r'((?:href|src)=")\.\./', r'\1', text)
        (dest / page.name).write_text(text)
        target = '../' + ('' if page.name == 'index.html' else page.name)
        canonical = SITE + ('' if page.name == 'index.html' else page.name)
        page.write_text('<!doctype html><html lang="es"><head><meta charset="utf-8">'
                        '<title>Tiempo en Las Palmas</title><meta name="robots" content="noindex,follow">'
                        f'<link rel="canonical" href="{canonical}">'
                        f'<meta http-equiv="refresh" content="0;url={target}"></head><body>'
                        f'<a href="{target}">Abrir la página en español</a>'
                        f'<script>location.replace({json.dumps(target)}+location.search+location.hash)</script></body></html>')
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
            text = replace_once(text, "nom: (esDema ? NOM_TRAM_DEMA : NOM_TRAM)[g.nom](),",
                "nom: (g.dia.toDateString() !== ara.toDateString() && !esDema ? g.dia.toLocaleDateString('es', {weekday:'long', day:'numeric', month:'short'}) + ' · ' : '') + (esDema ? NOM_TRAM_DEMA : NOM_TRAM)[g.nom](),")
            text = text.replace('ratxa: 72, calor: 36.8', 'ratxa: Infinity, calor: Infinity')
            text = re.sub(r' A l’hora en curs, el cel és el que s’observa a l’aeroport de Sabadell, si hi veu núvols\.', ' El cielo procede del modelo, sin observación local.', text)
            text = replace_once(text, 'async function calOfertaAvisos() {', 'async function calOfertaAvisos() { return false;')
        if path.name == 'grafica.js':
            text = replace_once(text, "if (dies < -1) return d.toLocaleDateString(IDIOMA.codi === 'es' ? 'es' : 'ca', { weekday: 'long' });",
                "if (dies < -1 || dies > 1) return d.toLocaleDateString(IDIOMA.codi === 'es' ? 'es' : 'ca', { weekday: 'long', day: 'numeric', month: 'short' });")
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
    for source, name in (('home.js', 'lpa-home.js'), ('home.css', 'lpa-home.css'), ('time.js', 'lpa-time.js'), ('ui.js', 'lpa-ui.js'), ('alerts.js', 'lpa-alerts.js'), ('station-page.js', 'lpa-station-page.js'), ('extras.js','lpa-extras.js')):
        shutil.copyfile(HERE / source, dest / name)
    # Never cache weather/alerts or register upstream push handlers.
    (dest / 'sw.js').write_text("// LPA: no offline weather cache or push backend.\n")
    for folder in (dest / '.well-known', dest / 'img'):
        if folder.exists():
            shutil.rmtree(folder)
    manifest = json.loads((dest / 'manifest.webmanifest').read_text())
    manifest.update(name='Tiempo en Las Palmas', short_name='Las Palmas', lang='es', start_url='./',
                    description='Previsión para Las Palmas de Gran Canaria, en hora canaria.')
    (dest / 'manifest.webmanifest').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (dest / 'README.md').write_text(f'# Tiempo en Las Palmas\n\nSource: {P.REPOSITORY}/tree/lpa\n\nUpstream: https://github.com/jjdeharo/meteo-local\n')
    (dest/'llms.txt').write_text('# Tiempo en Las Palmas de Gran Canaria\n\n'
        '> Proyecto independiente. Previsión de modelos y observaciones de estaciones; no es un servicio oficial.\n\n'
        '## Recursos públicos\n\n'
        f'- [JSON documentado]({SITE}weather.json): schema_version, generated_at, expires_at, unidades en los nombres de los campos.\n'
        f'- [Datos legibles sin JavaScript]({SITE}datos.html): resumen actualizado y metadatos Dataset.\n'
        f'- [Fuentes y condiciones]({SITE}fuentes.html).\n'
        f'- [Interfaz]({SITE}): previsión de siete días en hora canaria.\n\n'
        '## Semántica\n\n'
        'Zona horaria Atlantic/Canary; fechas ISO 8601 con desplazamiento. Comprobar generated_at/expires_at y la antigüedad de cada estación. '
        'forecast es una estimación; observations contiene mediciones. null o unavailable no significa cero. '
        'La precipitación horaria es la acumulación del intervalo start/end, sin multiplicar de nuevo por la probabilidad. '
        'Los resúmenes diarios corresponden al día local completo. Más allá de tres días aumenta la incertidumbre. '
        'El radar muestra reflectividad, no confirma lluvia en superficie. Cada fuente conserva sus condiciones de uso.\n\n'
        'Este archivo es una guía de acceso; no garantiza indexación ni citas por parte de buscadores o asistentes.\n')
    (dest/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(
            '<url><loc>'+SITE+name+'</loc></url>' for name in
            ('','observaciones.html','radar.html','perill.html','fuentes.html','datos.html'))+'</urlset>')
    return dest


def redirect_page(target):
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Tiempo en Las Palmas</title>'
            '<meta name="robots" content="noindex,follow">'
            f'<meta http-equiv="refresh" content="0;url={target}"></head><body><main>'
            f'<p><a href="{target}">Ir al tiempo en Las Palmas</a></p></main></body></html>')


def sources_html():
    items = ''.join(f'<li><strong>{html.escape(k)}</strong>: {html.escape(v)}</li>' for k, v in P.UNAVAILABLE.items())
    return (f'<p>Adaptación de <a href="https://github.com/jjdeharo/meteo-local">meteo-local, de Juanjo de Haro</a>. '
            'Se conserva su interfaz; los adaptadores regionales están separados.</p>'
            '<p>Previsión: <a href="https://open-meteo.com/">Open-Meteo</a>, selección automática best_match, '
            'CC BY 4.0. Aire: CAMS global a través de Open-Meteo, sin corrección local. '
            'Avisos de AEMET a través de Meteoalarm, zona Norte de Gran Canaria. '
            'Observaciones de AEMET, METAR de NOAA, GRAFCAN y estaciones escolares y particulares en Weathercloud y Weather Underground. '
            'Polen y esporas: recuentos fechados de SEAIC; sismicidad: GeoRSS del IGN. '
            'Radar y cartografía: AEMET, reflectividad sin extrapolación de lluvia. '
            'Calima: polvo, PM10 y turbidez de CAMS global vía Open-Meteo, con niveles orientativos. Mar: olas y temperatura del agua de Open-Meteo Marine (CC BY 4.0) y widgets oficiales de Puertos del Estado, cargados bajo demanda. '
            'La disponibilidad y antigüedad de cada lectura se muestran en Estaciones. Los ajustes de temperatura requieren validación temporal; los consejos de salida no tienen validación local.</p>'
            f'<p>Ubicación aproximada: {P.COORDINATES}; zona horaria {P.TIMEZONE}. '
            'Los datos no representan todos los microclimas del municipio.</p>'
            '<p>La previsión, las estaciones y el radar se leen desde el propio alojamiento. Los gráficos de PORTUS '
            'establecen una conexión externa solo al pulsar Cargar gráfico. Preferencias de interfaz en '
            'el almacenamiento del navegador. Sin suscripciones, Telegram ni servicio push propio. '
            'Los enlaces externos aplican sus propias condiciones.</p><ul>' + items + '</ul>'
            f'<p><a href="{P.REPOSITORY}/tree/lpa">Código AGPL-3.0-or-later</a>; contenidos CC BY-SA 4.0; '
            'iconos Lucide ISC. No se modifica la licencia del proyecto original.</p>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    build(parser.parse_args().destination)
