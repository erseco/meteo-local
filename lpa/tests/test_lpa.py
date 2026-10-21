# SPDX-License-Identifier: AGPL-3.0-or-later
"""Contract, source isolation, missing-provider and Canary DST regression tests."""
import datetime as dt
import json
from html.parser import HTMLParser
from urllib.parse import urlsplit
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from lpa import collect as C, profile as P
from lpa.build import build, replace_once

NOW = dt.datetime(2026, 10, 20, 15, tzinfo=dt.timezone.utc)


def forecast(now=NOW):
    start = int(now.replace(hour=0).timestamp())
    times = [start + n * 3600 for n in range(168)]
    h = {key: [20.0] * 168 for key in C.HOURLY}
    h.update(time=times, precipitation=[0.4] * 168, precipitation_probability=[35] * 168,weather_code=[0]*168)
    return {'hourly': h, 'current': {'time': int(now.timestamp()), 'temperature_2m': 22},
            'daily': {'time': times[::24], 'sunrise': times[7::24], 'sunset': times[19::24], 'uv_index_max': [5]*7,
                      'temperature_2m_max':[24]*7,'temperature_2m_min':[19]*7,
                      'precipitation_sum':[1]*7,'precipitation_probability_max':[35]*7,
                      'weather_code':[2]*7,'wind_speed_10m_max':[15]*7}}


def hourly_payload(params, now=NOW, value=10):
    """Answer any Open-Meteo hourly request with the fields it asked for."""
    times = forecast(now)['hourly']['time'][:24 * params.get('forecast_days', 1)]
    h = {field: [value] * len(times) for field in params['hourly'].split(',')}
    h['time'] = times
    return json.dumps({'hourly': h})


def feed(entry='', updated=None):
    updated = updated or NOW.isoformat()
    return (f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2">'
            f'<updated>{updated}</updated>{entry}</feed>')


def warning(area=P.ALERT_AREA):
    return (f'<entry><cap:areaDesc>{area}</cap:areaDesc><cap:event>Severe wind warning</cap:event>'
            '<cap:onset>2026-10-20T12:00:00Z</cap:onset><cap:expires>2026-10-21T12:00:00Z</cap:expires></entry>')


class Sources(unittest.TestCase):
    def test_forecast_probability_units_and_interval(self):
        rows = C.forecast_rows(forecast(), NOW)
        self.assertEqual(rows[0]['probabilitat'], .35)
        self.assertEqual(rows[0]['pluja_mm'], .4)
        self.assertEqual(rows[0]['hora'], '2026-10-20T16:00+01:00')
        self.assertIsNone(rows[0]['plou_ara'])
        self.assertGreaterEqual(len(rows), 24)

    def test_forecast_rejects_null_region_and_truncated_series(self):
        f = forecast()
        f['hourly']['temperature_2m'] = [None] * 72
        with self.assertRaises(ValueError): C.forecast_rows(f, NOW)
        f = forecast()
        f['hourly']['precipitation'].pop()
        with self.assertRaises(ValueError): C.forecast_rows(f, NOW)

    def test_actual_instants_across_canary_dst(self):
        now = dt.datetime(2026, 10, 25, 0, tzinfo=dt.timezone.utc)
        rows = C.forecast_rows(forecast(now), now)
        self.assertEqual(rows[0]['hora'], '2026-10-25T01:00+01:00')
        self.assertEqual(rows[0]['fins'], '2026-10-25T01:00+00:00')
        self.assertEqual(rows[1]['hora'], '2026-10-25T01:00+00:00')

    def test_daily_dates_survive_the_october_change(self):
        # Open-Meteo returns daily midnights at the request offset (+01:00 before the change).
        midnights = [int(dt.datetime(2026, 10, d, tzinfo=dt.timezone(dt.timedelta(hours=1))).timestamp()) for d in (24, 25, 26)]
        self.assertEqual([C.day_of(t, 3600) for t in midnights], ['2026-10-24', '2026-10-25', '2026-10-26'])
        self.assertEqual(C.local(midnights[2]).date().isoformat(), '2026-10-25')

    def test_warning_area_and_empty_success(self):
        rows = C.parse_alerts(feed(warning() + warning('Prelitoral de Barcelona')), NOW)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['nivel'], 'taronja')
        self.assertEqual(rows[0]['tipo'], 'vent')
        self.assertEqual(C.parse_alerts(feed(), NOW), [])

    def test_hourly_warning_contract_and_interval_boundaries(self):
        start = NOW + dt.timedelta(hours=1)
        end = start + dt.timedelta(hours=1)
        xml = warning().replace('2026-10-20T12:00:00Z', start.isoformat()).replace('2026-10-21T12:00:00Z', end.isoformat())
        def reader(url, params):
            if url == C.FORECAST: return json.dumps(forecast())
            if url == C.ALERTS: return feed(xml)
            raise TimeoutError()
        data = C.collect(NOW, reader, include_observations=False)
        hours = data['hores']
        self.assertEqual(hours[0]['avisos'], [])
        self.assertEqual(hours[1]['avisos'], [{'font':'aemet', 'tipus':['vent'], 'nivell':'taronja'}])
        self.assertEqual(hours[2]['avisos'], [])
        self.assertEqual(data['avisos'][0]['tipo'], 'vent')
        self.assertEqual(data['avisos'][0]['nivel'], 'taronja')

    def test_stale_and_invalid_feeds_are_not_empty_successes(self):
        for xml in ('<html/>', feed(updated='2026-10-18T00:00:00Z'), '<feed>'):
            with self.assertRaises(Exception): C.parse_alerts(xml, NOW)

    def test_failed_sources_never_mean_dry_safe_or_no_incidents(self):
        def reader(url, params):
            if url == C.FORECAST: return json.dumps(forecast())
            raise TimeoutError('source offline')
        data = C.collect(NOW, reader, include_observations=False)
        self.assertIsNone(data['avisos'])
        self.assertIsNone(data['aire'])
        self.assertIsNone(data['trens'])
        self.assertIsNone(data['plou_ara'])
        self.assertIsNone(data['aprenentatge'])
        self.assertIsNone(data['riscos'])
        self.assertGreaterEqual(len(data['hores']), 24)
        self.assertEqual(data['lpa']['sources']['avisos'], 'unavailable')

    def test_requests_never_use_catalan_sources_or_calibrations(self):
        requests = []
        def reader(url, params):
            requests.append((url, params))
            if url == C.FORECAST: return json.dumps(forecast())
            if url == C.ALERTS: return feed()
            return hourly_payload(params)
        with patch.object(C.prevision, 'leer_calibracion', side_effect=AssertionError('local training forbidden')):
            data = C.collect(NOW, reader, include_observations=False)
        self.assertEqual(data['errors'], [])
        self.assertFalse(data['aire']['corregit'])
        self.assertEqual(len(requests), 5)
        for url, params in requests:
            if params and url != C.MARINE:
                self.assertEqual(params['latitude'], 28.124)
                self.assertEqual(params['longitude'], -15.436)
                self.assertEqual(params['timezone'], 'Atlantic/Canary')
        self.assertTrue(all(p['domains'] == 'cams_global' for u, p in requests if u == C.AIR))
        self.assertEqual(data['lpa']['calima']['now']['nivel'], 'none')
        self.assertEqual(data['lpa']['marine']['now']['wave_height'], 10)

    def test_calima_levels_and_peak(self):
        self.assertIsNone(C.dust_level(None))
        self.assertEqual([C.dust_level(v) for v in (0, 19.9, 20, 60, 150, 500)],
                         ['none', 'none', 'light', 'moderate', 'intense', 'very_intense'])
        payload = json.loads(hourly_payload({'hourly': ','.join(C.DUST), 'forecast_days': 4}))
        payload['hourly']['dust'][40] = 180
        calima = C.parse_calima(payload, NOW)
        self.assertEqual(calima['peak']['dust'], 180)
        self.assertEqual(calima['peak']['nivel'], 'intense')
        self.assertTrue(calima['now']['hora'] == '2026-10-20T16:00+01:00')
        payload['hourly']['dust'] = [None] * len(payload['hourly']['dust'])
        with self.assertRaises(ValueError): C.parse_calima(payload, NOW)

    def test_marine_requires_sea_values(self):
        payload = json.loads(hourly_payload({'hourly': ','.join(C.MARINE_FIELDS), 'forecast_days': 3}))
        self.assertEqual(len(C.parse_marine(payload, NOW)['hours']), 57)
        payload['hourly']['wave_height'] = [None] * len(payload['hourly']['wave_height'])
        with self.assertRaises(ValueError): C.parse_marine(payload, NOW)

    def test_atomic_output(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'data.json'
            C.write_json(path, {'ok': True})
            self.assertEqual(json.loads(path.read_text()), {'ok': True})
            self.assertEqual([p.name for p in Path(temp).iterdir()], ['data.json'])


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.dest = build(cls.temp.name)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_upstream_contract_breaks_loudly(self):
        with self.assertRaises(ValueError): replace_once('new upstream', 'old upstream', 'adapter')

    def test_generated_source_and_timezone_isolation(self):
        js = (self.dest/'comu.js').read_text()
        self.assertIn('const DADES_URL = ARREL;', js)
        self.assertIn('const CASA_COORD = [28.124, -15.436]', js)
        self.assertNotIn('navigator.serviceWorker.register(', js)
        for file in self.dest.glob('*.js'):
            subprocess.run(['node', '--check', str(file)], check=True, capture_output=True)
        page = (self.dest/'index.html').read_text()
        self.assertIn('Las Palmas', page)
        self.assertIn('lpa-time.js', page)
        self.assertNotIn('io.github.meteo_montflorit', page)
        self.assertNotIn('Radar de Meteocat', page)
        self.assertFalse((self.dest/'.well-known/assetlinks.json').exists())

    def test_unavailable_services_have_no_active_scripts(self):
        for name in ('avisos.html','telegram.html'):
            page = (self.dest/name).read_text()
            self.assertIn('Función no disponible', page)
            self.assertNotIn('<script src=', page)
        # Barranco floods are not offered: the old river page only leads home.
        river = (self.dest/'riera.html').read_text()
        self.assertIn('url=./', river)
        self.assertNotIn('<script src=', river)

    def test_home_navigation_and_footer(self):
        index = (self.dest/'index.html').read_text()
        nav = index[index.index('<nav class="pagines"'):]
        nav = nav[:nav.index('</nav>')]
        self.assertIn('href="radar.html"', nav)
        self.assertNotIn('sortir.html', nav)
        self.assertNotIn('riera.html', nav)
        for section in ('lh-hours', 'lh-days', 'lh-radar', 'lh-wind', 'lh-calima', 'lh-sea'):
            self.assertIn(f'id="{section}"', index)
        self.assertNotIn('Guaguas', (self.dest/'sortir.html').read_text())
        for page in self.dest.glob('*.html'):
            text = page.read_text()
            if '<footer' in text:
                self.assertEqual(text.count('class="peu lpa-footer"'), 1, page.name)
                self.assertIn('Juan José de Haro', text)

    def test_spanish_root_assets_manifest_and_legacy_bookmarks(self):
        class Resources(HTMLParser):
            def __init__(self):
                super().__init__(); self.paths = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'script' and attrs.get('src'):
                    self.paths.append(attrs['src'])
                if tag == 'link' and attrs.get('rel') in ('stylesheet', 'manifest', 'apple-touch-icon'):
                    self.paths.append(attrs['href'])
        # Rebuilding an existing output must not treat legacy redirects as source pages.
        build(self.dest)
        for page in self.dest.glob('*.html'):
            text = page.read_text()
            self.assertIn('<html lang="es"', text)
            self.assertNotIn('data-arrel="../"', text)
            self.assertNotIn('meteo.idioma', text)
            resources = Resources(); resources.feed(text)
            for resource in resources.paths:
                self.assertFalse(urlsplit(resource).scheme)
                self.assertTrue((self.dest / resource).is_file(), resource)
            legacy = (self.dest/'es'/page.name).read_text()
            self.assertIn('noindex,follow', legacy)
            self.assertIn('location.search+location.hash', legacy)
            self.assertNotIn('src="', legacy)
        self.assertEqual(json.loads((self.dest/'manifest.webmanifest').read_text())['start_url'], './')
        self.assertNotIn('meteo-local/es/', (self.dest/'sitemap.xml').read_text())
        self.assertNotIn('meteo-local/es/', (self.dest/'llms.txt').read_text())

    def test_canary_calendar_in_a_foreign_browser_timezone(self):
        script = (Path(__file__).parents[1]/'time.js').read_text() + '''
const assert = require('node:assert/strict');
let d = new LpaDate('2026-07-01T12:00:00Z');
assert.equal(d.getHours(),13);
assert.equal(d.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'}),'13:00');
assert.equal(new LpaDate('2026-01-01T12:00').toISOString(),'2026-01-01T12:00:00.000Z');
assert.equal(new LpaDate('2026-07-01T12:00').toISOString(),'2026-07-01T11:00:00.000Z');
d = new LpaDate('2026-10-25T00:30:00Z');
assert.equal(d.getHours(),1);
assert.equal(d.getTimezoneOffset(),-60);
d = new LpaDate('2026-10-25T01:30:00Z');
assert.equal(d.getHours(),1);
assert.equal(d.getTimezoneOffset(),0);
d.setMinutes(45);
assert.equal(d.toISOString(),'2026-10-25T01:45:00.000Z');
d = new LpaDate(2026,6,1,12); d.setDate(2);
assert.equal(d.toISOString(),'2026-07-02T11:00:00.000Z');
'''
        subprocess.run(['node','-e',script], env={**os.environ,'TZ':'America/New_York'}, check=True, capture_output=True)


if __name__ == '__main__': unittest.main()
