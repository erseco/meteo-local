# SPDX-License-Identifier: AGPL-3.0-or-later
"""Optional public-page observations; no embedded API keys are extracted or used."""
import json
import re

STATION = {'id': 'ILASPA64', 'name': 'La Montañeta · MONTAÑETA2',
           'provider': 'Weather Underground · particular', 'region': 'La Montañeta',
           'category': 'urban', 'latitude': 28.056, 'longitude': -15.453,
           'elevation_m': 309, 'max_age_minutes': 35,
           'url': 'https://www.wunderground.com/dashboard/pws/ILASPA64',
           'detail': 'Lecturas actuales o muestras agregadas de cinco minutos de la página pública; sin API key. Acceso no documentado y sin calibración automática.'}


def parse(page):
    from .observations import number, timestamp
    blocks = re.findall(r'<script\b[^>]*type=[\'"]application/json[\'"][^>]*>(.*?)</script>', page, re.S)
    if not blocks:
        raise ValueError('Weather Underground public page contract changed')
    state = []
    for block in blocks:
        try:
            state.append(json.loads(block))
        except json.JSONDecodeError:
            continue
    rows = {}
    def walk(value):
        if isinstance(value, dict):
            # Only interval observations count: summaries and daily extremes do not.
            records = value.get('observations')
            if isinstance(records, list):
                for item in records:
                    unit_name = next((key for key in ('metric','metric_si','imperial')
                                      if isinstance(item.get(key),dict) and any(
                                          number(item[key].get(field)) is not None for field in ('tempAvg','temp'))), None)
                    units = item.get(unit_name, {})
                    interval = 'tempAvg' in units
                    temp = number(units.get('tempAvg' if interval else 'temp'))
                    if item.get('stationID') != STATION['id'] or temp is None or item.get('qcStatus') == -1:
                        continue
                    if item.get('obsTimeUtc') is None:
                        continue
                    moment = timestamp(item['obsTimeUtc']).isoformat()
                    def convert(key, factor):
                        val = number(units.get(key))
                        return None if val is None else round(val * factor, 1)
                    factor = {'metric':1,'metric_si':3.6,'imperial':1.609344}[unit_name]
                    rows[moment] = {'observed_at': moment, 'temperature_c': round((temp - 32) / 1.8 if unit_name == 'imperial' else temp, 1),
                        'relative_humidity_pct': number(item.get('humidityAvg' if interval else 'humidity')),
                        'wind_kmh': convert('windspeedAvg' if interval else 'windSpeed', factor),
                        'gust_kmh': convert('windgustHigh' if interval else 'windGust', factor),
                        'measurement_period_minutes': 5 if interval else None, 'provider_qc_status': item.get('qcStatus'),
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
