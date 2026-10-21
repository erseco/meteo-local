# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate deterministic network-free browser data at the current clock."""
import datetime as dt
import json
import sys

from lpa.collect import AIR, FORECAST, MARINE, collect, publish
from lpa.tests.test_lpa import feed, forecast, hourly_payload


def create(destination):
    now = dt.datetime.now(dt.UTC).replace(minute=0, second=0, microsecond=0)
    def reader(url, params):
        if url == FORECAST:
            return json.dumps(forecast(now))
        if url in (AIR, MARINE):
            payload = json.loads(hourly_payload(params, now, 1.2 if url == MARINE else 10))
            if 'dust' in payload['hourly']:
                # Clear air now with a moderate calima episode later in the forecast.
                payload['hourly']['dust'] = [8] * len(payload['hourly']['time'])
                payload['hourly']['dust'][-6] = 60
            return json.dumps(payload)
        # An active official warning must coexist with the hourly forecast.
        start = (now - dt.timedelta(hours=1)).isoformat()
        end = (now + dt.timedelta(hours=6)).isoformat()
        entry = ('<entry><cap:areaDesc>Norte de Gran Canaria</cap:areaDesc>'
                 '<cap:event>Moderate rain warning</cap:event>'
                 f'<cap:onset>{start}</cap:onset><cap:expires>{end}</cap:expires></entry>')
        return feed(entry, updated=now.isoformat())
    data = collect(now, reader, include_observations=False)
    from lpa.observations import SCHOOL_STATIONS, STATIONS, URBAN_STATIONS, validate
    data['lpa']['observations'] = {'stations': [validate({'observed_at':now.isoformat(),'temperature_c':22.5,'relative_humidity_pct':65,'wind_kmh':10}, station, now) for station in STATIONS + URBAN_STATIONS + SCHOOL_STATIONS[:1]], 'providers': []}
    data['lpa']['history'] = {'observations':3,'matched_samples':0,'retention_days':90,'method':'Temperatura a 2–6 horas; validación temporal y remuestreo por días.','stations':{s['id']:{'status':'learning','samples':0,'days':0} for s in STATIONS},'forecast_error':None}
    data['lpa']['environment'] = {
        'pollen': {'status':'stale', 'last_count':{'date':str(now.date()-dt.timedelta(days=40)),
            'values':[{'taxon':'Gramíneas','value':0,'unit':'granos/m³'},{'taxon':'Alternaria (hongo)','value':2,'unit':'esporas/m³'}]},
            'detail':'Recuento observado, no pronóstico.'},
        'earthquakes': {'status':'ok','events':[], 'detail':'Eventos de Canarias incluidos en el GeoRSS consultado.'}}
    import base64
    import io

    from PIL import Image
    image=Image.new('RGB',(1000,580),'#e5f1f7'); output=io.BytesIO();image.save(output,format='PNG')
    picture='data:image/png;base64,'+base64.b64encode(output.getvalue()).decode()
    data['lpa']['radar']={'status':'ok','observed_at':now.isoformat(),'max_age_minutes':45,
        'frames':[{'observed_at':(now-dt.timedelta(minutes=10)).isoformat(),'image':picture},
                  {'observed_at':now.isoformat(),'image':picture}],
        'legend':[{'color':'#0000fc','label':'12–18 dBZ'}],
        'detail':'Reflectividad en dBZ. No equivale a lluvia medida en el suelo.'}
    publish(destination, data)


if __name__ == '__main__': create(sys.argv[1])
