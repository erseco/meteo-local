# SPDX-License-Identifier: AGPL-3.0-or-later
"""Persistent observations and genuinely prospective forecast verification.

Daily JSONL files are append-only and deduplicated. Issue timestamps are retained;
forecasts downloaded after a measurement can never count as predictions of it.
Only temperature is calibrated. Rain totals, rates and METAR reports are not
interchangeable and no local rain model is claimed.
"""
import datetime as dt
import json
from pathlib import Path
import random
import statistics
import urllib.parse
from . import observations as O

RETENTION_DAYS = 90


def load(directory, kind):
    rows = []
    for path in sorted((Path(directory) / kind).glob('*.jsonl')):
        for line in path.read_text().splitlines():
            rows.append(json.loads(line))
    return rows


def append(directory, kind, rows, key):
    """Use stable identities so a frozen/repeated report does not inflate evidence."""
    grouped = {}
    for row in rows:
        date = (row.get('observed_at') or row['issued_at'])[:10]
        grouped.setdefault(date, []).append(row)
    for date, values in grouped.items():
        path = Path(directory) / kind / (date + '.jsonl')
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        seen = {key(row) for row in previous}
        with path.open('a') as output:
            for row in values:
                identity = key(row)
                if identity not in seen:
                    output.write(json.dumps(row, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n')
                    seen.add(identity)


def station_forecasts(now, reader=O.get_text):
    """Ask for each station's own coordinates and altitude, not the airport as city truth."""
    stations = O.STATIONS
    params = {'latitude': ','.join(str(s['latitude']) for s in stations),
              'longitude': ','.join(str(s['longitude']) for s in stations),
              'elevation': ','.join(str(s['elevation_m']) for s in stations),
              'hourly': 'temperature_2m', 'forecast_days': 2, 'timezone': 'UTC', 'timeformat': 'unixtime',
              'models': 'best_match'}
    payload = json.loads(reader('https://api.open-meteo.com/v1/forecast?' + urllib.parse.urlencode(params)))
    if not isinstance(payload, list) or len(payload) != len(stations):
        raise ValueError('Unexpected multi-location forecast response')
    rows = []
    for station, response in zip(stations, payload):
        h = response['hourly']
        if len(h['time']) != len(h['temperature_2m']):
            raise ValueError('Incomplete station forecast timeline')
        values = [{'valid_at': O.timestamp(t).isoformat(), 'temperature_c': v}
                  for t, value in zip(h['time'], h['temperature_2m'])
                  if now.timestamp() < t <= now.timestamp() + 26 * 3600
                  and (v := O.number(value)) is not None and -25 <= v <= 60]
        if not values:
            raise ValueError('No future station forecast temperatures')
        rows.append({'station': station['id'], 'issued_at': now.isoformat(), 'values': values})
    return rows


def pairs(observed, forecasts):
    """Match independent hourly observations to forecasts issued 2–6 h beforehand."""
    by_target = {}
    for forecast in forecasts:
        issued = O.timestamp(forecast['issued_at'])
        for value in forecast['values']:
            valid = O.timestamp(value['valid_at'])
            lead = (valid - issued).total_seconds() / 3600
            if 2 <= lead <= 6:
                key = (forecast['station'], int(valid.timestamp()))
                candidate = (abs(lead - 3), value['temperature_c'], forecast['issued_at'])
                if key not in by_target or candidate < by_target[key]:
                    by_target[key] = candidate
    selected = {}
    for row in observed:
        if row.get('temperature_c') is None or row.get('status') == 'invalid':
            continue
        time = O.timestamp(row['observed_at']).timestamp()
        hour = round(time / 3600) * 3600
        distance = abs(time - hour)
        if distance > 600:
            continue
        key = (row['id'], hour)
        forecast = by_target.get(key)
        if forecast is not None and (key not in selected or distance < selected[key][0]):
            selected[key] = (distance, {'station': row['id'], 'valid_at': O.timestamp(hour).isoformat(),
                'observed': row['temperature_c'], 'predicted': forecast[1], 'issued_at': forecast[2]})
    return [value[1] for _, value in sorted(selected.items())]


def calibrate(rows):
    """Chronological holdout, then a day-block bootstrap; no training on the test period."""
    days = sorted({row['valid_at'][:10] for row in rows})
    result = {'status': 'learning', 'samples': len(rows), 'days': len(days), 'bias_c': None}
    if rows:
        result['mae_c'] = round(statistics.mean(abs(r['observed'] - r['predicted']) for r in rows), 3)
    if len(days) < 14:
        return result
    middle = days[len(days) // 2]
    train = [r for r in rows if r['valid_at'][:10] < middle]
    test = [r for r in rows if r['valid_at'][:10] >= middle]
    if len(train) < 72 or len(test) < 72:
        return result
    bias = max(-3, min(3, statistics.median(r['observed'] - r['predicted'] for r in train)))
    baseline = statistics.mean(abs(r['observed'] - r['predicted']) for r in test)
    corrected = statistics.mean(abs(r['observed'] - r['predicted'] - bias) for r in test)
    daily = {}
    for row in test:
        daily.setdefault(row['valid_at'][:10], []).append(
            abs(row['observed'] - row['predicted']) - abs(row['observed'] - row['predicted'] - bias))
    improvements = [statistics.mean(values) for values in daily.values()]
    rng = random.Random(0)
    confidence = sum(statistics.mean(rng.choices(improvements, k=len(improvements))) > 0
                     for _ in range(1000)) / 1000
    result.update(test_mae_c=round(baseline, 3), corrected_test_mae_c=round(corrected, 3),
                  confidence=confidence, train_until=middle, candidate_bias_c=round(bias, 3))
    if baseline > 0 and corrected <= baseline * .9 and confidence >= .95:
        result.update(status='validated', bias_c=round(bias, 3))
    else:
        result['status'] = 'rejected'
    return result


def update(data, directory, reader=O.get_text):
    now = O.timestamp(data['generat'])
    directory = Path(directory)
    observed = (data.get('lpa', {}).get('observations') or {}).pop('_archive', [])
    append(directory, 'observations', observed, lambda r: (r['id'], r['observed_at']))
    forecasts = load(directory, 'forecasts')
    hour = now.strftime('%Y-%m-%dT%H')
    forecast_error = None
    if not any(r['issued_at'][:13] == hour for r in forecasts):
        try:
            append(directory, 'forecasts', station_forecasts(now, reader), lambda r: (r['station'], r['issued_at'][:13]))
        except Exception:
            forecast_error = 'No se pudieron registrar las previsiones en los puntos de las estaciones.'
    cutoff = (now - dt.timedelta(days=RETENTION_DAYS)).date().isoformat()
    for kind in ('observations', 'forecasts'):
        for path in (directory / kind).glob('*.jsonl'):
            if path.stem < cutoff:
                path.unlink()
    all_observations = load(directory, 'observations')
    matched = pairs(all_observations, load(directory, 'forecasts'))
    summary = {'retention_days': RETENTION_DAYS, 'observations': len(all_observations),
               'matched_samples': len(matched), 'stations': {}, 'forecast_error': forecast_error,
               'method': 'Temperatura a 2–6 horas; validación temporal y remuestreo por días.'}
    for station in O.STATIONS:
        summary['stations'][station['id']] = calibrate([r for r in matched if r['station'] == station['id']])
    data['lpa']['history'] = summary
    # Only the nearby urban coastal station can calibrate the city's coastal grid.
    # Tafira, airport and school observations are never averaged into this correction.
    model = summary['stations'].get('C659M', {})
    if model.get('status') == 'validated':
        for row in data.get('hores') or []:
            lead = (O.timestamp(row['fins']) - now).total_seconds() / 3600
            if 2 <= lead <= 6 and row.get('temperatura') is not None:
                row['temperatura_sense_ajust'] = row['temperatura']
                row['temperatura'] = round(row['temperatura'] + model['bias_c'], 1)
                row['ajust_lpa_c'] = model['bias_c']
        data['lpa']['temperature_adjustment'] = {'station': 'C659M', 'scope': 'Costa urbana', 'bias_c': model['bias_c']}
        for key, text in data.get('consultes', {}).get('es', {}).items():
            data['consultes']['es'][key] = text.replace('sin calibración local.', 'con ajuste validado de temperatura a 2–6 horas para la costa urbana.')
    # Public compact result; the daily raw records stay in the dedicated data branch.
    from .collect import write_json
    write_json(directory / 'summary.json', summary)
    return summary
