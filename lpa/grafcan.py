# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read authenticated GRAFCAN observations, with an anonymous local fallback.

Queries are reviewed copies of public panel queries, never supplied by visitors.
No credentials, datasource configuration or arbitrary SQL endpoints are exposed
to the generated website. Provisional readings do not train city corrections.
"""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

DASHBOARD = 'https://metrics.grafcan.es/d/Ss-8yBhGz/single-weather-station?orgId=1&var-thing_location=14'
STATION = {'id': 'GRAFCAN-3705', 'name': 'La Isleta · Geonica 3705',
           'provider': 'GRAFCAN · panel público', 'region': 'La Isleta',
           'category': 'urban', 'latitude': None, 'longitude': None,
           'elevation_m': 6, 'max_age_minutes': 35, 'thing_id': 14, 'url': DASHBOARD,
           'detail': 'METEODATA-3016CP (3705), thing 14. Datos provisionales; no se usan para calibrar la previsión. Precipitación pendiente de validar con la API.'}


def query_payload(now):
    template = json.loads((Path(__file__).parent / 'grafcan-queries.json').read_text())
    queries = []
    for field, panel in template['queries'].items():
        sql = panel['rawSql'].replace('$thing_location', '14').replace('$__interval', "'10m'")
        queries.append({'refId': field, 'datasource': {'type': 'grafana-postgresql-datasource',
                        'uid': template['datasource_uid']}, 'rawSql': sql, 'rawQuery': True,
                        'format': 'time_series', 'intervalMs': 600000, 'maxDataPoints': 24})
    return {'queries': queries, 'from': str(int((now - dt.timedelta(hours=2)).timestamp() * 1000)),
            'to': str(int(now.timestamp() * 1000))}


def get_payload(now):
    request = urllib.request.Request('https://metrics.grafcan.es/api/ds/query',
        data=json.dumps(query_payload(now)).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read(1_000_000))


def parse(payload):
    from .observations import number, timestamp
    rows = {}
    for field, result in payload['results'].items():
        if field not in (
                'temperature_c', 'relative_humidity_pct', 'gust_kmh', 'wind_kmh', 'pressure_hpa', 'wind_direction'):
            continue
        if result.get('error') or result.get('status', 200) != 200:
            continue
        for frame in result.get('frames', []):
            fields = frame['schema']['fields']
            values = frame['data']['values']
            times = next((values[i] for i, f in enumerate(fields) if f['type'] == 'time'), [])
            measurements = next((values[i] for i, f in enumerate(fields) if f['type'] == 'number'), [])
            if len(times) != len(measurements):
                raise ValueError('Incomplete GRAFCAN series')
            for moment, raw in zip(times, measurements):
                value = number(raw)
                if value is None:
                    continue
                time = timestamp(moment).isoformat()
                row = rows.setdefault(time, {'observed_at': time, 'provisional': True,
                    'pressure_kind': 'unspecified', 'measurement_period_minutes': 10})
                row[field] = value
    if not rows:
        raise ValueError('No usable GRAFCAN dashboard observations')
    return list(rows.values())


API = 'https://sensores.grafcan.es/api/v1.0/'
# Names, sensor and units verified against the official thing=14 catalogue.
API_FIELDS = {
    'Air temperature (avg.)': ('temperature_c', '°C', 1),
    'Relative humidity (avg.)': ('relative_humidity_pct', '%', 1),
    'Wind speed (avg.)': ('wind_kmh', 'm/s', 3.6),
    'Wind speed (max.)': ('gust_kmh', 'm/s', 3.6),
    'Wind direction (avg.)': ('wind_direction', '°', 1),
    'Atmosferic pressure (avg.)': ('pressure_hpa', 'mbar', 1),
    'Dew point (avg.)': ('dewpoint_c', '°C', 1),
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward the API credential to a redirect target."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api_json(url, key):
    """Fetch only the fixed HTTPS API origin; never log credentials or bodies."""
    if not url.startswith(API):
        raise ValueError('Unexpected GRAFCAN pagination URL')
    request = urllib.request.Request(url, headers={
        'Accept': 'application/json', 'Authorization': 'Api-Key ' + key})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('GRAFCAN response exceeds limit')
        return json.loads(raw)


def api_items(path, key, reader=api_json):
    """Follow bounded official pagination, preserving the original time filter."""
    url, seen = API + path, set()
    for _ in range(5):
        if url in seen or not url.startswith(API):
            raise ValueError('Unexpected GRAFCAN pagination URL')
        seen.add(url)
        page = reader(url, key)
        yield from page['results']
        url = page.get('next')
        if not url:
            return
    raise ValueError('GRAFCAN pagination exceeds limit')


def source_metadata(authenticated=None):
    if authenticated is None:
        authenticated = bool(os.environ.get('GRAFCAN_API_KEY', '').strip())
    if not authenticated:
        return dict(STATION)
    return {**STATION, 'provider': 'GRAFCAN · API oficial',
            'url': 'https://sensores.grafcan.es/',
            'detail': 'METEODATA-3016CP (3705), thing 14. API oficial; se excluyen lecturas inválidas. Datos provisionales, sin calibración local. Lluvia no integrada.'}


def parse_api(streams, observations):
    """Keep each timestamp and quality flag; reject unknown units or sensors."""
    from .observations import number, timestamp
    fields = {}
    for stream in streams:
        if stream.get('thing') != API + 'things/14/' or stream.get('sensor') != API + 'sensors/21/':
            continue
        spec = API_FIELDS.get(stream.get('name'))
        if spec and stream.get('unitOfMeasurement', {}).get('symbol') == spec[1]:
            fields[API + 'datastreams/' + str(stream['id']) + '/'] = spec
    rows = {}
    for item in observations:
        spec = fields.get(item.get('datastream'))
        validity = item.get('validity')
        if not spec or validity not in ('valid', 'validationPending'):
            continue
        value = number(item.get('result'))
        if value is None:
            continue
        try:
            moment = timestamp(item['resultTime']).isoformat()
        except (ValueError, TypeError, KeyError):
            continue
        row = rows.setdefault(moment, {'observed_at': moment, 'provisional': True,
            'pressure_kind': 'unspecified', 'source_validity': {}, **source_metadata(True)})
        field = spec[0]
        # A conflicting duplicate must not silently win by response order.
        converted = round(value * spec[2], 3)
        if field in row and row[field] != converted:
            raise ValueError('Conflicting GRAFCAN observations')
        row[field] = converted
        row['source_validity'][field] = validity
    if not rows:
        raise ValueError('No usable authenticated GRAFCAN observations')
    return list(rows.values())


def collect(now, reader=api_json):
    key = os.environ.get('GRAFCAN_API_KEY', '').strip()
    if not key:
        return parse(get_payload(now))
    streams = list(api_items('datastreams/?thing=14', key, reader))
    params = urllib.parse.urlencode({'datastream__thing': 14, 'ordering': '-result_time',
        'result_time_after': (now - dt.timedelta(hours=2)).isoformat(),
        'result_time_before': now.isoformat()})
    observations = api_items('observations/?' + params, key, reader)
    return parse_api(streams, observations)
