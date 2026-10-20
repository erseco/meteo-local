# SPDX-License-Identifier: AGPL-3.0-or-later
"""Optional public-page observations; no embedded API keys are extracted or used."""
import json
import re

STATION = {'id': 'ILASPA64', 'name': 'La Montañeta · MONTAÑETA2',
           'provider': 'Weather Underground · particular', 'region': 'La Montañeta',
           'category': 'urban', 'latitude': 28.056, 'longitude': -15.453,
           'elevation_m': 309, 'max_age_minutes': 35,
           'url': 'https://www.wunderground.com/dashboard/pws/ILASPA64',
           'detail': 'Muestras agregadas de 5 minutos de la página pública; sin API key. Acceso no documentado y sin calibración automática.'}


def parse(page):
    from .observations import number, timestamp
    match = re.search(r'<script\b[^>]*id=[\'"]app-root-state[\'"][^>]*>(.*?)</script>', page, re.S)
    if not match:
        raise ValueError('Weather Underground public page contract changed')
    state = json.loads(match[1])
    rows = {}
    def walk(value):
        if isinstance(value, dict):
            # Only interval observations count: summaries and daily extremes do not.
            records = value.get('observations')
            if isinstance(records, list):
                for item in records:
                    units = item.get('imperial', {})
                    temp = number(units.get('tempAvg'))
                    if item.get('stationID') != STATION['id'] or temp is None or item.get('qcStatus') == -1:
                        continue
                    if item.get('obsTimeUtc') is None:
                        continue
                    moment = timestamp(item['obsTimeUtc']).isoformat()
                    def convert(key, factor):
                        val = number(units.get(key))
                        return None if val is None else round(val * factor, 1)
                    rows[moment] = {'observed_at': moment, 'temperature_c': round((temp - 32) / 1.8, 1),
                        'relative_humidity_pct': number(item.get('humidityAvg')),
                        'wind_kmh': convert('windspeedAvg', 1.609344),
                        'gust_kmh': convert('windgustHigh', 1.609344),
                        'measurement_period_minutes': 5, 'provider_qc_status': item.get('qcStatus'),
                        'rain_mm': None, 'pressure_hpa': None}
            for key, child in value.items():
                if key not in ('url', 'headers', 'token', 'observations'):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(state)
    if not rows:
        raise ValueError('No interval observations for the requested PWS')
    return list(rows.values())
