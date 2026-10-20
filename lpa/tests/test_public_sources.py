# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify provenance, interval units and honest missing/stale-data handling."""
import datetime as dt
import json
import tempfile
import unittest
from unittest.mock import patch
from lpa import grafcan as G, wunderground as W, nature as N, history as H

NOW = dt.datetime(2026, 10, 20, 17, 30, tzinfo=dt.timezone.utc)


class PublicSources(unittest.TestCase):
    def test_grafcan_frames_keep_units_nulls_and_provisional_status(self):
        frame = {'schema': {'fields': [{'name':'Time','type':'time'}, {'name':'result','type':'number'}]},
                 'data': {'values': [[int(NOW.timestamp()*1000)], [23.8]]}}
        rows = G.parse({'results': {'temperature_c': {'status':200,'frames':[frame]},
                                   'pressure_hpa': {'status':500,'error':'source failure'}}})
        self.assertEqual(rows[0]['temperature_c'],23.8)
        self.assertTrue(rows[0]['provisional'])
        self.assertNotIn('pressure_hpa',rows[0])
        self.assertNotIn('rain_mm',rows[0])
        payload = G.query_payload(NOW)
        self.assertEqual(len(payload['queries']),6)
        for query in payload['queries']:
            self.assertNotIn('$thing_location',query['rawSql'])
            self.assertIn('validity_id = 2',query['rawSql'])
        frame['data']['values'][1] = [None]
        with self.assertRaises(ValueError):G.parse({'results':{'temperature_c':{'frames':[frame]}}})

    def test_wunderground_interval_observations_not_daily_extremes(self):
        item = {'stationID':'ILASPA64','obsTimeUtc':NOW.isoformat(),'qcStatus':1,'humidityAvg':70,
                'imperial':{'tempAvg':68,'windspeedAvg':10,'windgustHigh':20,'pressureMax':30,'precipTotal':0}}
        def page(data):return '<script id="app-root-state" type="application/json">'+json.dumps(data)+'</script>'
        row = W.parse(page({'summaries':[item],'x':{'observations':[item]}}))[0]
        self.assertEqual(row['temperature_c'],20)
        self.assertEqual(row['wind_kmh'],16.1)
        self.assertEqual(row['gust_kmh'],32.2)
        self.assertIsNone(row['rain_mm'])
        self.assertIsNone(row['pressure_hpa'])
        with self.assertRaises(ValueError):W.parse(page({'summaries':[item]}))
        item['stationID']='OTHER'
        with self.assertRaises(ValueError):W.parse(page({'observations':[item]}))
        item['stationID']='ILASPA64';item['qcStatus']=-1
        with self.assertRaises(ValueError):W.parse(page({'observations':[item]}))

    def test_ign_filters_canaries_without_inventing_timezones_or_no_activity(self):
        xml='''<rss xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"><channel><title>GeoRSS Sismología IGN</title>
        <item><title>Info.terremoto: 20/10/2026 10:00:00</title><description>magnitud 2.1 en ATLÁNTICO-CANARIAS</description><link>http://www.ign.es/web/ign/test</link><geo:lat>28</geo:lat><geo:long>-16</geo:long></item>
        <item><link>http://www.ign.es/web/ign/test2</link><geo:lat>40</geo:lat><geo:long>-3</geo:long></item>
        </channel></rss>'''
        result=N.earthquakes(xml)
        self.assertEqual(len(result['events']),1)
        self.assertEqual(result['events'][0]['magnitude'],2.1)
        self.assertNotIn('observed_at',result['events'][0])
        self.assertEqual(result['events'][0]['url'],'https://www.ign.es/web/ign/test')
        self.assertEqual(N.earthquakes(xml.replace('<geo:lat>28','<geo:lat>40'))['events'],[])
        with self.assertRaises(ValueError):N.earthquakes('<rss><channel/></rss>')

    def test_pollen_dates_missing_values_and_spores_are_not_zero_current_pollen(self):
        rows=[{'idEstacion':28,'fecha':20260901,'9':0,'2':2},
              {'idEstacion':28,'fecha':20261021,'9':999},
              {'idEstacion':50,'fecha':20261020,'9':5}]
        result=N.pollen(rows,NOW)
        self.assertEqual(result['status'],'stale')
        self.assertEqual(result['last_count']['date'],'2026-09-01')
        self.assertEqual(result['last_count']['values'],[
            {'taxon':'Alternaria (hongo)','value':2.0,'unit':'esporas/m³'},
            {'taxon':'Gramíneas','value':0.0,'unit':'granos/m³'}])
        with self.assertRaises(ValueError):N.pollen([],NOW)

    def test_pollen_subscription_is_anonymous_read_only_and_uses_own_station(self):
        class Socket:
            def __init__(self):
                self.sent=[]; self.messages=iter([{'msg':'connected'}, {'msg':'added','fields':{'idEstacion':28,'fecha':20261020,'9':0}}, {'msg':'ready','subs':['lpa-pollen']}])
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def send(self,message):self.sent.append(json.loads(message))
            def recv(self,timeout):return json.dumps(next(self.messages))
        socket=Socket()
        with patch('websockets.sync.client.connect',return_value=socket):rows=N.pollen_rows(NOW)
        self.assertEqual(len(rows),1)
        self.assertEqual([m['msg'] for m in socket.sent],['connect','sub'])
        self.assertEqual(socket.sent[1]['params'][-1],28)

    def test_environment_failures_are_independent_and_pollen_history_deduplicates(self):
        def failed(_):raise TimeoutError()
        result=N.collect(NOW,reader=failed,pollen_reader=lambda _: [{'idEstacion':28,'fecha':20261020,'9':0}])
        self.assertEqual(result['earthquakes']['status'],'unavailable')
        self.assertEqual(result['pollen']['status'],'ok')
        with tempfile.TemporaryDirectory() as root:
            for _ in range(2):
                data={'generat':NOW.isoformat(),'lpa':{'environment':N.collect(NOW,reader=failed,pollen_reader=lambda _: [{'idEstacion':28,'fecha':20261020,'9':0}])}}
                H.update(data,root,reader=failed,wait=lambda _:None)
                self.assertNotIn('_archive',data['lpa']['environment']['pollen'])
            self.assertEqual(len(H.load(root,'pollen')),1)
            self.assertEqual(data['lpa']['history']['matched_samples'],0)
            self.assertEqual(data['lpa']['history']['pollen_counts'],1)


if __name__ == '__main__':unittest.main()
