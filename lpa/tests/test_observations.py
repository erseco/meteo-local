# SPDX-License-Identifier: AGPL-3.0-or-later
import datetime as dt
import json
import tempfile
import unittest
from unittest.mock import patch
from lpa import observations as O, history as H

NOW = dt.datetime(2026,10,20,16,30,tzinfo=dt.timezone.utc)
XML = '''<?xml version='1.0' encoding='ISO-8859-15'?><root><estacion id_c="C659M"><periodo utc="2026-10-20T16:00:00" local="2026-10-20T18:00:00"><temperatura>23.9</temperatura><humedad>65</humedad><vel_viento>12</vel_viento><precipitacion>0.0</precipitacion><presion></presion></periodo></estacion></root>'''


class Observations(unittest.TestCase):
    def test_aemet_uses_utc_not_peninsular_local(self):
        row = O.aemet(XML,O.STATIONS[0])[0]
        self.assertEqual(row['observed_at'],'2026-10-20T16:00:00+00:00')
        self.assertEqual(row['rain_mm'],0)
        self.assertIsNone(row['pressure_hpa'])
        self.assertEqual(row['rain_period_minutes'],60)
        with self.assertRaises(ValueError): O.aemet(XML,O.STATIONS[1])

    def test_metar_converts_knots_but_never_invents_rain(self):
        row=O.metar(json.dumps([{'icaoId':'GCLP','obsTime':int(NOW.timestamp()),'temp':24,'wspd':10,'wgst':20,'altim':1017}]))[0]
        self.assertEqual(row['wind_kmh'],18.5)
        self.assertEqual(row['gust_kmh'],37)
        self.assertEqual(row['pressure_kind'],'sea_level')
        self.assertIsNone(row['rain_mm'])
        self.assertIsNone(row.get('relative_humidity_pct'))

    def test_bad_frozen_future_and_missing_values(self):
        row=O.validate({'observed_at':NOW.isoformat(),'temperature_c':500,'relative_humidity_pct':102},O.STATIONS[0],NOW)
        self.assertEqual(row['status'],'invalid')
        self.assertIsNone(row['temperature_c'])
        row=O.validate({'observed_at':(NOW-dt.timedelta(hours=3)).isoformat(),'temperature_c':22},O.STATIONS[0],NOW)
        self.assertEqual(row['status'],'stale')
        row=O.validate({'observed_at':(NOW+dt.timedelta(hours=1)).isoformat(),'temperature_c':22},O.STATIONS[0],NOW)
        self.assertEqual(row['status'],'invalid')
        self.assertIsNone(O.number('NaN'))
        self.assertIsNone(O.number('inf'))
        with self.assertRaises(ValueError): O.timestamp('2026-10-20T16:00')

    def test_school_timestamp_units_and_old_station(self):
        row=O.school(json.dumps({'temp_current':[int(NOW.timestamp())*1000,22], 'wspdavg_current':[int(NOW.timestamp())*1000,4]}))[0]
        self.assertEqual(row['wind_kmh'],14.4)
        self.assertEqual(O.timestamp(row['observed_at']),NOW)
        self.assertIsNone(row['rain_mm'])
        row=O.school(json.dumps({'last_update':int((NOW-dt.timedelta(days=30)).timestamp())}))[0]
        self.assertEqual(O.validate(row,O.SCHOOL_STATIONS[0],NOW)['status'],'stale')

    def test_source_failure_never_stops_other_sources(self):
        def reader(url):
            if url.endswith('C659M'):return XML
            raise TimeoutError()
        def school(station):raise TimeoutError()
        result=O.collect(NOW,reader,school)
        self.assertEqual(result['stations'][0]['status'],'ok')
        self.assertTrue(all(s['status']=='unavailable' for s in result['stations'][1:]))
        self.assertEqual(len(result['stations']),17)


class History(unittest.TestCase):
    def test_deduplication_and_distinct_utc_dst_instants(self):
        with tempfile.TemporaryDirectory() as root:
            rows=[{'id':'C659M','observed_at':'2026-10-25T00:00:00+00:00','temperature_c':20},
                  {'id':'C659M','observed_at':'2026-10-25T01:00:00+00:00','temperature_c':20}]
            for _ in range(2):H.append(root,'observations',rows,lambda r:(r['id'],r['observed_at']))
            self.assertEqual(len(H.load(root,'observations')),2)

    def test_no_retrospective_forecast_leakage(self):
        observed=[{'id':'C659M','observed_at':NOW.replace(minute=0).isoformat(),'temperature_c':24}]
        valid=observed[0]['observed_at']
        after=[{'station':'C659M','issued_at':NOW.isoformat(),'values':[{'valid_at':valid,'temperature_c':24}]}]
        self.assertEqual(H.pairs(observed,after),[])
        before=[{'station':'C659M','issued_at':(NOW-dt.timedelta(hours=3,minutes=30)).isoformat(),'values':[{'valid_at':valid,'temperature_c':22}]}]
        self.assertEqual(H.pairs(observed,before)[0]['predicted'],22)
        self.assertEqual(len(H.pairs(observed*3,before*2)),1)

    def test_training_requires_independent_days_and_rejects_drift(self):
        rows=[]
        for day in range(14):
            for hour in range(12):
                rows.append({'valid_at':(NOW-dt.timedelta(days=14-day)+dt.timedelta(hours=hour)).isoformat(),'predicted':20,'observed':22})
        self.assertEqual(H.calibrate(rows[:24])['status'],'learning')
        good=H.calibrate(rows)
        self.assertEqual(good['status'],'validated')
        self.assertEqual(good['bias_c'],2)
        # A reversal in the unseen period must not be called a useful correction.
        for row in rows[84:]:row['observed']=18
        self.assertEqual(H.calibrate(rows)['status'],'rejected')

    def test_update_keeps_observations_when_forecast_archive_fails(self):
        with tempfile.TemporaryDirectory() as root:
            observed=O.validate({'observed_at':NOW.isoformat(),'temperature_c':22},O.STATIONS[0],NOW)
            data={'generat':NOW.isoformat(),'hores':[],'lpa':{'observations':{'_archive':[observed]}}}
            def reader(url):raise TimeoutError()
            summary=H.update(data,root,reader)
            self.assertEqual(summary['observations'],1)
            self.assertEqual(summary['matched_samples'],0)
            self.assertTrue(summary['forecast_error'])
            self.assertNotIn('_archive',data['lpa']['observations'])

    def test_station_forecast_has_own_coordinates_and_real_issue_time(self):
        def reader(url):
            self.assertIn('28.113%2C28.078%2C27.923',url)
            return json.dumps([{'hourly':{'time':[int((NOW+dt.timedelta(hours=1)).timestamp())],'temperature_2m':[22]}} for _ in O.STATIONS])
        result=H.station_forecasts(NOW,reader)
        self.assertEqual(len(result),3)
        self.assertEqual(result[0]['issued_at'],NOW.isoformat())


if __name__=='__main__':unittest.main()
