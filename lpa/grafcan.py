# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read the anonymous public GRAFCAN dashboard while API access is pending.

Queries are reviewed copies of public panel queries, never supplied by visitors.
No credentials, datasource configuration or arbitrary SQL endpoints are exposed
to the generated website. Provisional readings do not train city corrections.
"""
import datetime as dt
import json
from pathlib import Path
import urllib.request

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


def collect(now):
    return parse(get_payload(now))
