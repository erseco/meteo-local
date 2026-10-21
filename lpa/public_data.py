# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit, credential-free public contract and a crawler-readable HTML snapshot."""
import datetime as dt
import html
import json
import os
import re
import tempfile
from pathlib import Path

from . import profile as P

SITE = 'https://erseco.github.io/meteo-local/'
DESCRIPTION = 'Previsión de siete días para Las Palmas de Gran Canaria y observaciones identificadas por estación, fuente y antigüedad.'


def dataset(data=None):
    value = {'@context':'https://schema.org','@type':'Dataset',
        '@id':SITE+'datos.html#dataset','name':'Tiempo en Las Palmas · datos públicos',
        'description':DESCRIPTION,'url':SITE+'datos.html','inLanguage':'es',
        'spatialCoverage':{'@type':'Place','name':P.NAME,
            'geo':{'@type':'GeoCoordinates','latitude':P.COORDINATES[0],'longitude':P.COORDINATES[1]}},
        'variableMeasured':['Temperatura del aire','Probabilidad de precipitación',
                            'Precipitación prevista','Velocidad del viento','Humedad relativa'],
        'isBasedOn':[{'@type':'CreativeWork','url':url} for url in
            ['https://open-meteo.com/','https://www.aemet.es/','https://sensores.grafcan.es/',
             'https://aviationweather.gov/','https://www.polenes.com/','https://www.ign.es/']],
        'distribution':{'@type':'DataDownload','encodingFormat':'application/json',
                        'contentUrl':SITE+'weather.json'}}
    if data:
        value['dateModified']=data['generated_at']
        rows=data['forecast']['hourly']
        if rows:value['temporalCoverage']=rows[0]['start']+'/'+rows[-1]['end']
    return value


def normalize(data):
    generated=dt.datetime.fromisoformat(data['generat'])
    hourly=[]
    for row in data.get('hores') or []:
        hourly.append(dict(zip(('start','end','temperature_c','precipitation_mm',
                               'precipitation_probability_pct','weather_code','wind_kmh','gust_kmh','uv_index'),
            [row['hora'],row['fins'],row.get('temperatura'),row.get('pluja_mm'),
             None if row.get('probabilitat') is None else round(row['probabilitat']*100,2),
             row.get('codi'),row.get('vent'),row.get('ratxa'),row.get('uv')]),
             temperature_adjustment_c=row.get('ajust_lpa_c')))
    radar=data.get('lpa',{}).get('radar') or {}
    environment=data.get('lpa',{}).get('environment') or {}
    station_keys=('id','name','provider','region','category','latitude','longitude','elevation_m',
        'status','observed_at','max_age_minutes','temperature_c','relative_humidity_pct',
        'wind_kmh','gust_kmh','rain_mm','rain_period_minutes','rain_rate_mmh',
        'pressure_hpa','pressure_kind','provisional','url')
    return {'schema_version':'1.0','generated_at':generated.isoformat(),
        'expires_at':(generated+dt.timedelta(hours=2)).isoformat(),
        'location':{'name':P.NAME,'latitude':P.COORDINATES[0],'longitude':P.COORDINATES[1],'timezone':P.TIMEZONE},
        'units':{'temperature':'°C','wind':'km/h','humidity':'%',
                 'hourly_precipitation':'mm per start/end interval','probability':'%',
                 'daily.temperature_2m_min':'°C','daily.temperature_2m_max':'°C',
                 'daily.precipitation_sum':'mm per complete local day',
                 'daily.precipitation_probability_max':'maximum hourly probability, %',
                 'daily.wind_speed_10m_max':'km/h','current_model.time':'Unix seconds'},
        'forecast':{'status':'ok' if hourly else 'unavailable','provider':'Open-Meteo','url':'https://open-meteo.com/en/docs','model':'best_match',
            'kind':'model_forecast','daily':data.get('lpa',{}).get('daily_forecast',[]),'hourly':hourly,
            'current_model':data.get('lpa',{}).get('current_model'),
            'temperature_adjustment':data.get('lpa',{}).get('temperature_adjustment'),
            'semantics':'Hourly precipitation_mm is the model accumulation for start/end; probability is separate. Daily summaries cover the complete local day. Longer-range forecasts are less certain.'},
        'observations':[{k:s[k] for k in station_keys if k in s}
            for s in (data.get('lpa',{}).get('observations') or {}).get('stations',[])],
        'alerts':None if data.get('avisos') is None else [
            {'source':'AEMET via Meteoalarm','area':a['zona'],'type':a['tipo'],'level':a['nivel'],
             'starts_at':a['inicio'],'ends_at':a['fin'],'description':a['descripcio'],'url':a['url']}
             for a in data['avisos']],
        'radar':{'status':radar.get('status','unavailable'),'observed_at':radar.get('observed_at'),
            'max_age_minutes':radar.get('max_age_minutes',45),'url':SITE+'radar.html',
            'kind':'reflectivity_dbz','surface_rain_inferred':False},
        'environment':{key:{field:value for field,value in (environment.get(key) or {}).items()
            if field in ('status','provider','url','station','last_count','events','detail')}
            for key in ('pollen','earthquakes')},
        'links':{'human':SITE,'sources':SITE+'fuentes.html','documentation':SITE+'llms.txt'},
        'notes':['Not an official weather service. A station represents its own location.',
            'Recalculate age using observed_at and max_age_minutes; status reflects collection time.',
            'Missing or unavailable values are not zero. Check generated_at/expires_at before treating data as current.',
            'Individual source terms apply; the software license is not a blanket license for provider data.']}


def snapshot(data):
    escape=lambda v:html.escape(str(v))
    def val(value,unit=''):
        return '—' if value is None else escape(value)+unit
    rows=''.join('<tr>'+''.join('<td>'+val(v)+'</td>' for v in
        [d['date'],d.get('temperature_2m_min'),d.get('temperature_2m_max'),
         d.get('precipitation_probability_max'),d.get('precipitation_sum')])+'</tr>'
        for d in data['forecast']['daily'])
    stations=''.join('<li>'+escape(s['name'])+' · '+escape(s.get('provider',''))+
        ' · '+escape(s.get('status','unavailable'))+' · '+val(s.get('temperature_c'),' °C')+
        ' · '+escape(s.get('observed_at','Sin lectura'))+'</li>' for s in data['observations'])
    return ('<p>Actualización: <time datetime="'+escape(data['generated_at'])+'">'+escape(data['generated_at'])+
        '</time>. Caducidad de la publicación: '+escape(data['expires_at'])+'. Hora canaria.</p>'
        '<h3>Previsión · Open-Meteo</h3><p>Estimación del modelo; los días completos incluyen horas ya pasadas. '
        'Más allá de tres días, mayor incertidumbre.</p><div class="lpa-data-table" tabindex="0" role="region" aria-label="Previsión diaria">'
        '<table><caption>Previsión diaria en hora canaria</caption><thead><tr><th scope="col">Día</th>'
        '<th scope="col">Mín. °C</th><th scope="col">Máx. °C</th><th scope="col">Lluvia %</th>'
        '<th scope="col">Lluvia mm</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
        '<h3>Observaciones por estación</h3><ul>'+stations+'</ul>'
        '<p>El estado corresponde a la descarga; compruebe la antigüedad de cada lectura. '
        'Una fuente sin datos no equivale a una medición cero.</p>')


def atomic_text(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False) as f:
        name=f.name
        try:
            f.write(text);f.close();os.replace(name,path)
        finally:
            if os.path.exists(name):os.unlink(name)


def export(directory,data):
    from .collect import write_json
    directory=Path(directory);public=normalize(data)
    write_json(directory/'weather.json',public)
    page=directory/'datos.html'
    if page.exists():
        text=page.read_text()
        text,count=re.subn(r'<div id="lpa-public-snapshot">.*?</div><!-- snapshot-end -->',
            lambda _: '<div id="lpa-public-snapshot">'+snapshot(public)+'</div><!-- snapshot-end -->',text,flags=re.S)
        if count!=1:raise ValueError('Public data HTML anchor changed')
        text,count=re.subn(r'<script id="lpa-dataset" type="application/ld\+json">.*?</script>',
            lambda _: '<script id="lpa-dataset" type="application/ld+json">'+json.dumps(dataset(public),ensure_ascii=False).replace('<','\\u003c')+'</script>',text,flags=re.S)
        if count!=1:raise ValueError('Dataset metadata anchor changed')
        atomic_text(page,text)
