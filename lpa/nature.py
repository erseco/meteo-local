# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public IGN seismic information and dated SEAIC pollen counts, kept separate."""
import concurrent.futures
import datetime as dt
import json
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET

IGN = 'https://www.ign.es/ign/RssTools/sismologia.xml'
POLLEN = 'https://www.polenes.com/'
POLLEN_NAMES = dict(enumerate(('Alnus', 'Alternaria (hongo)', 'Artemisa', 'Betula',
    'Carex', 'Castanea', 'Cupresáceas', 'Fraxinus', 'Gramíneas', 'Mercurialis',
    'Morus', 'Olea', 'Palmáceas', 'Pinus', 'Plantago', 'Platanus', 'Populus',
    'Amarantáceas', 'Quercus', 'Rumex', 'Ulmus', 'Urticáceas'), 1))


def earthquakes(xml):
    from .observations import number
    root = ET.fromstring(xml)
    if root.tag != 'rss' or 'IGN' not in root.findtext('./channel/title', ''):
        raise ValueError('Unexpected IGN feed')
    events = []
    for item in root.findall('./channel/item'):
        lat = number(item.findtext('{http://www.w3.org/2003/01/geo/wgs84_pos#}lat'))
        lon = number(item.findtext('{http://www.w3.org/2003/01/geo/wgs84_pos#}long'))
        if lat is None or lon is None or not (26 <= lat <= 30.5 and -19 <= lon <= -12):
            continue
        link = item.findtext('link', '').replace('http://', 'https://', 1)
        if urllib.parse.urlsplit(link).hostname != 'www.ign.es':
            continue
        description = item.findtext('description', '')
        magnitude = re.search(r'magnitud\s+([\d.]+)', description)
        events.append({'title': item.findtext('title', ''), 'description': description,
                       'latitude': lat, 'longitude': lon, 'url': link,
                       'magnitude': number(magnitude[1]) if magnitude else None})
    return {'status': 'ok', 'provider': 'IGN', 'url': IGN, 'events': events,
            'detail': 'Eventos de Canarias incluidos en el GeoRSS consultado. Información sísmica, no predicción meteorológica. Las horas se conservan tal como las publica IGN; el RSS no declara su zona horaria.'}


def pollen_rows(now):
    """Subscribe only to the same anonymous read-only publication as the public chart."""
    from websockets.sync.client import connect
    start = (now.date() - dt.timedelta(days=90)).strftime('%Y%m%d')
    end = now.date().strftime('%Y%m%d')
    rows = []
    with connect('wss://www.polenes.com/websocket', open_timeout=12, close_timeout=2,
                 max_size=1_000_000) as socket:
        socket.send(json.dumps({'msg': 'connect', 'version': '1', 'support': ['1']}))
        deadline = time.monotonic() + 20
        for _ in range(1000):
            message = json.loads(socket.recv(timeout=max(.1, deadline - time.monotonic())))
            if message.get('msg') == 'connected':
                socket.send(json.dumps({'msg': 'sub', 'id': 'lpa-pollen', 'name': 'graphPollenData',
                                        'params': [start, end, 28]}))
            elif message.get('msg') == 'ping':
                socket.send(json.dumps({'msg': 'pong', 'id': message.get('id')}))
            elif message.get('msg') == 'added':
                fields = message.get('fields', {})
                if fields.get('idEstacion') == 28:
                    rows.append(fields)
            elif message.get('msg') == 'ready' and 'lpa-pollen' in message.get('subs', []):
                return rows
            elif message.get('msg') in ('nosub', 'failed', 'error'):
                raise ValueError('Public SEAIC publication unavailable')
            if time.monotonic() >= deadline:
                raise TimeoutError('SEAIC collection timed out')
    raise ValueError('Incomplete SEAIC subscription')


def pollen(samples, now):
    from .observations import number
    archive = {}
    for row in samples:
        if row.get('idEstacion') != 28:
            continue
        try:
            day = dt.datetime.strptime(str(row['fecha']), '%Y%m%d').date()
        except (ValueError, KeyError):
            continue
        if day > now.date():
            continue
        values = [{'taxon': name, 'value': value, 'unit': 'esporas/m³' if key == 2 else 'granos/m³'}
                  for key, name in POLLEN_NAMES.items()
                  if (value := number(row.get(str(key)))) is not None and 0 <= value <= 1_000_000]
        if values:
            archive[day] = {'station': 28, 'date': day.isoformat(), 'values': values}
    if not archive:
        raise ValueError('No dated SEAIC counts for Las Palmas')
    last = archive[max(archive)]
    return {'status': 'ok' if (now.date() - max(archive)).days <= 3 else 'stale',
            'provider': 'SEAIC / Polenes.com', 'url': POLLEN,
            'station': 'Las Palmas de Gran Canaria', 'last_count': last,
            'detail': 'Recuento observado, no pronóstico. La fecha del recuento puede ser anterior a la descarga. Alternaria es un hongo y se expresa en esporas/m³.',
            '_archive': [archive[day] for day in sorted(archive)]}


def collect(now, reader=None, pollen_reader=pollen_rows):
    from .observations import get_text
    reader = reader or get_text
    result = {'generated_at': now.isoformat()}
    tasks = {'earthquakes': lambda: earthquakes(reader(IGN)),
             'pollen': lambda: pollen(pollen_reader(now), now)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(task): key for key, task in tasks.items()}
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                result[key] = future.result()
            except Exception as error:
                result[key] = {'status': 'unavailable', 'url': IGN if key == 'earthquakes' else POLLEN,
                               'detail': type(error).__name__ + ': fuente temporalmente no disponible'}
    return result
