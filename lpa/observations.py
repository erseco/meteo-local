# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public station observations, with explicit location, units and freshness.

AEMET's public website XML is a best-effort fallback to its documented OpenData
API. Weathercloud's guest GET endpoint is undocumented and optional: changes or
missing observations are reported, never converted into dry/zero measurements.
"""
import concurrent.futures
import datetime as dt
import http.cookiejar
import json
import math
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from . import profile as P
from . import grafcan, wunderground

UTC = dt.timezone.utc
AEMET_BASE = 'https://www.aemet.es/es/api-eltiempo/udat/tablas-graficas/horario/9/'
METAR = 'https://aviationweather.gov/api/data/metar?ids=GCLP&hours=3&format=json'
GRAFCAN = 'https://opendata.sitcan.es/upload/meteorologia/estaciones.csv'
STATIONS = [
    {'id': 'C659M', 'name': 'Plaza de la Feria', 'provider': 'AEMET', 'region': 'Costa urbana',
     'latitude': 28.113, 'longitude': -15.421, 'elevation_m': 15, 'max_age_minutes': 90},
    {'id': 'C658X', 'name': 'Tafira', 'provider': 'AEMET', 'region': 'Tafira',
     'latitude': 28.078, 'longitude': -15.453, 'elevation_m': 269, 'max_age_minutes': 90},
    {'id': 'GCLP', 'name': 'Aeropuerto de Gran Canaria', 'provider': 'METAR / NOAA', 'region': 'Aeropuerto · referencia regional',
     'latitude': 27.923, 'longitude': -15.389, 'elevation_m': 24, 'max_age_minutes': 75},
]
# Public school locations from the CEP Gran Canaria Noroeste map, rounded to 3 decimals.
SCHOOLS = [
    ('0812576475', 'IES Santiago Santana', 'Arucas', 28.116, -15.511),
    ('0072329617', 'CEIP Agustín Hernández Díaz', 'Moya', 28.113, -15.583),
    ('5899117986', 'IES Doramas', 'Moya', 28.115, -15.574),
    ('6444548125', 'IES Villa de Firgas', 'Firgas', 28.111, -15.562),
    ('1176904045', 'CEIP La Ladera', 'La Aldea de San Nicolás', 27.986, -15.789),
    ('4937896000', 'CEIP Los Quintana', 'Gáldar', 28.117, -15.669),
    ('6677261936', 'CEIP Artenara', 'Artenara', 28.021, -15.650),
    ('1145068075', 'CEIP Caideros', 'Gáldar', 28.076, -15.647),
    ('1628385614', 'CEIP Trapiche', 'Arucas', 28.135, -15.538),
    ('4531697272', 'CEIP Tasarte', 'La Aldea de San Nicolás', 27.922, -15.758),
    ('8709904980', 'CEIP Agaete Pepe Dámaso', 'Agaete', 28.105, -15.703),
    ('5809973024', 'CEIP Miguel de Santiago', 'Guía', 28.136, -15.629),
    ('7901818023', 'IES La Aldea de San Nicolás', 'La Aldea de San Nicolás', 27.980, -15.782),
    ('0371428440', 'IES Teror', 'Teror', 28.060, -15.544),
]
SCHOOL_STATIONS = [dict(id=code, name=name, provider='Weathercloud · red escolar', region=town,
                        category='school', latitude=lat, longitude=lon, elevation_m=None, max_age_minutes=35)
                   for code, name, town, lat, lon in SCHOOLS]
URBAN_STATIONS = [
    {'id': '2199568870', 'name': 'Las Palmas GC Arenales', 'provider': 'Weathercloud · particular',
     'category': 'urban', 'region': 'Arenales', 'latitude': 28.116, 'longitude': -15.423,
     'elevation_m': 30, 'max_age_minutes': 35},
    wunderground.STATION, grafcan.STATION,
]
LIMITS = {'temperature_c': (-25, 60), 'relative_humidity_pct': (0, 100),
          'wind_kmh': (0, 250), 'gust_kmh': (0, 350), 'pressure_hpa': (700, 1100),
          'rain_mm': (0, 500), 'rain_rate_mmh': (0, 500), 'dewpoint_c': (-50, 50)}


def get_text(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'meteo-local-lpa/' + P.VERSION})
    with urllib.request.urlopen(request, timeout=12) as response:
        raw = response.read(2_000_000)
        encoding = response.headers.get_content_charset()
        if raw.startswith(b'<?xml'):
            match = re.search(br'encoding=[\'"]([^\'"]+)', raw[:100])
            encoding = match[1].decode() if match else encoding
        return raw.decode(encoding or 'utf-8')


def number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(str(value).replace(',', '.'))
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def timestamp(value):
    if isinstance(value, (float, int)):
        return dt.datetime.fromtimestamp(value / 1000 if value > 10**11 else value, UTC)
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Observation timestamp has no timezone')
    return result.astimezone(UTC)


def validate(row, station, now):
    """Keep invalid variables missing; never let an old sample masquerade as now."""
    row = {**station, **row}
    moment = timestamp(row['observed_at'])
    row['observed_at'] = moment.isoformat(timespec='seconds')
    age = (now - moment).total_seconds() / 60
    row['age_minutes'] = round(age, 1)
    row['quality_flags'] = []
    for key, (low, high) in LIMITS.items():
        value = number(row.get(key))
        if value is not None and not low <= value <= high:
            value = None
            row['quality_flags'].append(key + ':out_of_range')
        row[key] = value
    if age < -5:
        row['status'] = 'invalid'
        row['quality_flags'].append('future_timestamp')
    elif age > station['max_age_minutes']:
        row['status'] = 'stale'
    elif not any(row[k] is not None for k in LIMITS):
        row['status'] = 'invalid'
    else:
        row['status'] = 'ok'
    return row


def aemet(xml, station):
    """Parse UTC observation times, never the XML's peninsular/local attributes."""
    # XML passed as text has already been decoded using its declared encoding.
    root = ET.fromstring(re.sub(r'<\?xml[^>]+\?>', '', xml))
    source = root.find('estacion')
    if source is None or source.get('id_c') != station['id']:
        raise ValueError('AEMET returned another station or changed its schema')
    fields = {'temperatura': 'temperature_c', 'humedad': 'relative_humidity_pct',
              'vel_viento': 'wind_kmh', 'vel_racha': 'gust_kmh', 'presion': 'pressure_hpa',
              'precipitacion': 'rain_mm'}
    rows = []
    for period in source.findall('periodo'):
        moment = dt.datetime.fromisoformat(period.attrib['utc']).replace(tzinfo=UTC)
        row = {value: number(period.findtext(key)) for key, value in fields.items()}
        row.update(observed_at=moment.isoformat(), rain_period_minutes=60,
                   pressure_kind='station', wind_direction=period.findtext('dir_viento'))
        rows.append(row)
    if not rows:
        raise ValueError('AEMET has no hourly observations')
    return rows


def metar(payload):
    rows = []
    for item in json.loads(payload):
        if item.get('icaoId') != 'GCLP':
            continue
        rows.append({'observed_at': timestamp(item['obsTime']).isoformat(),
                     'temperature_c': number(item.get('temp')), 'dewpoint_c': number(item.get('dewp')),
                     'pressure_hpa': number(item.get('altim')), 'pressure_kind': 'sea_level',
                     'wind_kmh': None if number(item.get('wspd')) is None else round(float(item['wspd']) * 1.852, 1),
                     'gust_kmh': None if number(item.get('wgst')) is None else round(float(item['wgst']) * 1.852, 1),
                     'wind_direction': item.get('wdir'), 'clouds': item.get('clouds'),
                     'raw_report': item.get('rawOb'), 'rain_mm': None})
    if not rows:
        raise ValueError('No GCLP METAR observations')
    return rows


def school_payload(station):
    """Use only the public guest view and its read-only GET; no login or token storage."""
    base = 'https://app.weathercloud.net'
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    page_url = base + '/d' + station['id']
    with opener.open(page_url, timeout=10) as response:
        page = response.read(1_500_000).decode()
    match = re.search(r'WEATHERCLOUD_CSRF_TOKEN\s*:\s*"([^"]+)"', page)
    if not match:
        raise ValueError('Weathercloud public guest contract changed')
    units = re.search(r'var unitsCode\s*=\s*\{(.*?)\}', page, re.S)
    if not units or any(re.search(r'\b' + key + r'\s*:\s*0\b', units[1]) is None
                        for key in ('temp', 'wspd', 'bar', 'rain')):
        raise ValueError('Weathercloud units could not be verified')
    params = urllib.parse.urlencode({'code': station['id'], 'WEATHERCLOUD_CSRF_TOKEN': match[1]})
    request = urllib.request.Request(base + '/device/stats?' + params,
                                    headers={'Referer': page_url, 'X-Requested-With': 'XMLHttpRequest'})
    with opener.open(request, timeout=10) as response:
        return response.read(200_000).decode()


def school(payload):
    values = json.loads(payload)
    fields = {'temp': 'temperature_c', 'hum': 'relative_humidity_pct', 'bar': 'pressure_hpa',
              'wspdavg': 'wind_kmh', 'wspd': 'wind_kmh', 'wspdhi': 'gust_kmh', 'rainrate': 'rain_rate_mmh'}
    samples = {}
    for source, target in fields.items():
        pair = values.get(source + '_current')
        if not isinstance(pair, list) or len(pair) != 2 or number(pair[0]) is None:
            continue
        moment = timestamp(float(pair[0])).isoformat()
        row = samples.setdefault(moment, {'observed_at': moment, 'pressure_kind': 'sea_level', 'rain_mm': None})
        value = number(pair[1])
        row[target] = round(value * 3.6, 1) if value is not None and target in ('wind_kmh', 'gust_kmh') else value
    if not samples and number(values.get('last_update')) is not None:
        return [{'observed_at': timestamp(float(values['last_update'])).isoformat()}]
    if not samples:
        raise ValueError('Weathercloud has no timestamped public observations')
    return list(samples.values())


def institutional_sources():
    return [
        {'name': 'GRAFCAN / Gobierno de Canarias', 'url': 'https://sensores.grafcan.es/',
         'status': 'partial', 'detail': 'La Isleta se consulta mediante el panel público, con estado propio de cada lectura. Clave gratuita de la API solicitada; seguimiento en GitHub #1.'},
        {'name': 'Cabildo de Gran Canaria / HD Meteo', 'url': 'https://gc.hdmeteo.com/',
         'status': 'not_configured', 'detail': 'Plataforma localizada; acceso de observaciones originales pendiente de validar, separado de sus estimaciones espaciales.'},
        {'name': 'Ayuntamiento de Las Palmas de Gran Canaria', 'url': 'https://datosabiertos.laspalmasgc.es/',
         'status': 'not_configured', 'detail': 'Estaciones de Smart Beach en Las Canteras y de riego documentadas; acceso a sus medidas pendiente de validar.'},
    ]


def collect(now=None, reader=get_text, school_reader=school_payload, grafcan_reader=grafcan.collect):
    now = (now or dt.datetime.now(UTC)).astimezone(UTC)
    latest, archive, providers = [], [], []
    def task(station):
        public = dict(station)
        public.setdefault('url', ('https://www.aemet.es/es/eltiempo/observacion/ultimosdatos?l=' + station['id']
                         if station['provider'] == 'AEMET' else
                         'https://aviationweather.gov/data/metar/?ids=GCLP' if station['id'] == 'GCLP' else
                         'https://app.weathercloud.net/d' + station['id']))
        try:
            if station['id'] == grafcan.STATION['id']:
                rows = grafcan_reader(now)
            elif station['id'] == wunderground.STATION['id']:
                rows = wunderground.parse(reader(public['url']))
            elif station['provider'] == 'AEMET':
                rows = aemet(reader(AEMET_BASE + station['id']), station)
            elif station['id'] == 'GCLP':
                rows = metar(reader(METAR))
            else:
                rows = school(school_reader(station))
            checked = [validate(row, public, now) for row in rows]
            # A corrupt future report must not hide an older valid report.
            usable = [r for r in checked if r['status'] != 'invalid']
            if not usable:
                raise ValueError('No valid station observations')
            last = max(usable, key=lambda row: timestamp(row['observed_at']))
            return last, checked, None
        except Exception as error:
            # Do not leak session query strings or tokens in public failures.
            public.update(status='unavailable', detail=type(error).__name__ + ': no se pudieron obtener medidas válidas')
            if station['id'] == wunderground.STATION['id'] and type(error) is ValueError:
                reasons = {'Weather Underground public page contract changed': 'La página no contiene datos JSON utilizables.',
                           'No interval observations for the requested PWS': 'La página no contiene muestras fechadas de esta estación.'}
                if str(error) in reasons:
                    public['detail'] += ' · ' + reasons[str(error)]
            return public, [], None
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for last, checked, _ in pool.map(task, STATIONS + URBAN_STATIONS + SCHOOL_STATIONS):
            latest.append(last)
            archive.extend(r for r in checked if r['status'] != 'invalid')
    # Institutional availability is distinct from a station outage.
    return {'stations': latest, 'providers': institutional_sources(), '_archive': archive,
            'generated_at': now.isoformat(), 'attribution': 'AEMET; NOAA Aviation Weather Center; GRAFCAN; Weather Underground; centros y particulares / Weathercloud'}
