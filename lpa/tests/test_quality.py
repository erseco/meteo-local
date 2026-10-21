# SPDX-License-Identifier: AGPL-3.0-or-later
"""Failure modes and guarantees: a broken or ambiguous source never becomes good news."""
import datetime as dt
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from lpa import collect as C
from lpa import grafcan as G
from lpa import history as H
from lpa import nature as N
from lpa import observations as O
from lpa import radar as R
from lpa import wunderground as W
from lpa.tests.test_lpa import NOW, feed, forecast
from lpa.tests.test_radar import BOUNDS, png, scan


def station_forecast(*hours_and_values):
    """One Open-Meteo multi-location response with the same series for every station."""
    times = [int((NOW + dt.timedelta(hours=h)).timestamp()) for h, _ in hours_and_values]
    values = [v for _, v in hours_and_values]
    return json.dumps([{'hourly': {'time': times, 'temperature_2m': values}} for _ in O.STATIONS])


class ForecastContract(unittest.TestCase):
    def test_irregular_or_short_timelines_are_rejected(self):
        f = forecast()
        f['hourly']['time'][5] += 1800
        with self.assertRaisesRegex(ValueError, 'Invalid hourly timeline'):
            C.forecast_rows(f, NOW)
        f = forecast()
        f['hourly']['wind_direction_10m'] = []
        with self.assertRaisesRegex(ValueError, 'Incomplete forecast: wind_direction_10m'):
            C.forecast_rows(f, NOW)
        # Only 10 future hours remain: an almost expired forecast must not be published.
        late = NOW + dt.timedelta(hours=158)
        with self.assertRaisesRegex(ValueError, 'Less than 24 hours'):
            C.forecast_rows(forecast(), late)

    def test_hourly_rows_keep_direction_humidity_and_night(self):
        f = forecast()
        f['hourly']['is_day'] = [0] * 168
        f['hourly']['wind_direction_10m'] = [45] * 168
        row = C.forecast_rows(f, NOW)[0]
        self.assertEqual((row['direccio'], row['es_dia']), (45, 0))
        self.assertEqual(row['humitat'], 20.0)


class AlertContract(unittest.TestCase):
    def entry(self, event='Moderate wind warning', onset='2026-10-20T12:00:00Z', expires='2026-10-21T12:00:00Z'):
        return (f'<entry><cap:areaDesc>{C.P.ALERT_AREA}</cap:areaDesc><cap:event>{event}</cap:event>'
                f'<cap:onset>{onset}</cap:onset><cap:expires>{expires}</cap:expires></entry>')

    def test_feed_identity_and_freshness_are_required(self):
        with self.assertRaisesRegex(ValueError, 'Expected Meteoalarm Atom feed'):
            C.parse_alerts('<rss/>', NOW)
        with self.assertRaisesRegex(ValueError, 'no freshness timestamp'):
            C.parse_alerts('<feed xmlns="http://www.w3.org/2005/Atom"/>', NOW)
        future = (NOW + dt.timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(ValueError, 'stale or future'):
            C.parse_alerts(feed(updated=future), NOW)

    def test_expired_ambiguous_and_unknown_warnings(self):
        expired = self.entry(expires='2026-10-20T14:00:00Z')
        self.assertEqual(C.parse_alerts(feed(expired), NOW), [])
        with self.assertRaisesRegex(ValueError, 'offsets'):
            C.parse_alerts(feed(self.entry(onset='2026-10-20T12:00:00')), NOW)
        # An unknown level must fail loudly rather than be shown as a mild warning.
        with self.assertRaisesRegex(ValueError, 'Unknown local warning severity'):
            C.parse_alerts(feed(self.entry(event='Minor wind warning')), NOW)

    def test_repeated_entries_are_one_warning_in_canary_time(self):
        rows = C.parse_alerts(feed(self.entry() * 2), NOW)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['nivel'], 'groc')
        self.assertTrue(rows[0]['inicio'].endswith('+01:00'))


class StationForecastHistory(unittest.TestCase):
    def test_station_forecast_shape_and_value_filters(self):
        with self.assertRaisesRegex(ValueError, 'multi-location'):
            H.station_forecasts(NOW, lambda url: json.dumps({'hourly': {}}))
        broken = json.dumps([{'hourly': {'time': [1, 2], 'temperature_2m': [20]}} for _ in O.STATIONS])
        with self.assertRaisesRegex(ValueError, 'Incomplete station forecast'):
            H.station_forecasts(NOW, lambda url: broken)
        # Past hours, hours beyond 26 h and impossible values are dropped.
        with self.assertRaisesRegex(ValueError, 'No future station forecast'):
            H.station_forecasts(NOW, lambda url: station_forecast((-1, 20), (30, 20), (3, 99), (4, None)))
        rows = H.station_forecasts(NOW, lambda url: station_forecast((-1, 20), (3, 21.5), (30, 20)))
        self.assertEqual([v['temperature_c'] for v in rows[0]['values']], [21.5])

    def test_permanent_http_errors_are_not_retried(self):
        calls = []

        def reader(url):
            calls.append(url)
            raise urllib.error.HTTPError(url, 404, 'Not Found', {}, None)

        with tempfile.TemporaryDirectory() as root:
            data = {'generat': NOW.isoformat(), 'hores': [], 'lpa': {'observations': {'_archive': []}}}
            summary = H.update(data, root, reader, wait=lambda _: None)
        self.assertEqual(len(calls), 1)
        self.assertIn('HTTP 404', summary['forecast_error'])

    def test_rate_limits_are_retried_three_times_then_reported(self):
        calls = []

        def reader(url):
            calls.append(url)
            raise urllib.error.HTTPError(url, 429, 'Too Many Requests', {}, None)

        waits = []
        with tempfile.TemporaryDirectory() as root:
            data = {'generat': NOW.isoformat(), 'hores': [], 'lpa': {'observations': {'_archive': []}}}
            summary = H.update(data, root, reader, wait=waits.append)
        self.assertEqual(len(calls), 3)
        self.assertEqual(waits, [1, 2])
        self.assertIn('HTTP 429', summary['forecast_error'])

    def test_retention_removes_only_expired_days(self):
        with tempfile.TemporaryDirectory() as root:
            for kind in ('observations', 'forecasts', 'pollen'):
                (Path(root) / kind).mkdir()
                (Path(root) / kind / '2026-01-01.jsonl').write_text('')
                (Path(root) / kind / '2026-10-01.jsonl').write_text('')
            data = {'generat': NOW.isoformat(), 'hores': [], 'lpa': {'observations': {'_archive': []}}}
            H.update(data, root, lambda url: station_forecast((3, 21)), wait=lambda _: None)
            for kind in ('observations', 'pollen'):
                self.assertEqual(sorted(p.name for p in (Path(root) / kind).iterdir()), ['2026-10-01.jsonl'])

    def test_validated_correction_applies_only_to_coastal_two_to_six_hours(self):
        hours = [{'hora': (NOW + dt.timedelta(hours=h - 1)).isoformat(), 'fins': (NOW + dt.timedelta(hours=h)).isoformat(),
                  'temperatura': 22.0} for h in (1, 3, 6, 8)]
        data = {'generat': NOW.isoformat(), 'hores': hours, 'lpa': {'observations': {'_archive': []}},
                'consultes': {'es': {'avui': 'Estimación de Open-Meteo, sin calibración local.'}}}

        def calibrate(rows):
            return {'status': 'validated', 'bias_c': 0.8, 'samples': 200, 'days': 20}

        with tempfile.TemporaryDirectory() as root, patch.object(H, 'calibrate', side_effect=calibrate):
            H.update(data, root, lambda url: station_forecast((3, 21)), wait=lambda _: None)
        self.assertEqual([h['temperatura'] for h in data['hores']], [22.0, 22.8, 22.8, 22.0])
        self.assertEqual(data['hores'][1]['temperatura_sense_ajust'], 22.0)
        self.assertNotIn('ajust_lpa_c', data['hores'][0])
        self.assertEqual(data['lpa']['temperature_adjustment']['station'], 'C659M')
        self.assertIn('ajuste validado', data['consultes']['es']['avui'])

    def test_calibration_waits_for_enough_independent_samples(self):
        rows = [{'station': 'C659M', 'valid_at': f'2026-09-{d:02d}T12:00:00+00:00', 'observed': 22, 'predicted': 21}
                for d in range(1, 16)]
        result = H.calibrate(rows)
        self.assertEqual((result['status'], result['bias_c'], result['days']), ('learning', None, 15))
        self.assertEqual(result['mae_c'], 1)
        self.assertEqual(H.calibrate([])['samples'], 0)


class StationSources(unittest.TestCase):
    def test_metar_ignores_other_airports_and_requires_las_palmas(self):
        other = {'icaoId': 'GCXO', 'obsTime': int(NOW.timestamp()), 'temp': 20}
        with self.assertRaisesRegex(ValueError, 'No GCLP'):
            O.metar(json.dumps([other]))
        row = O.metar(json.dumps([other, {'icaoId': 'GCLP', 'obsTime': int(NOW.timestamp()), 'temp': 21}]))[0]
        self.assertEqual(row['temperature_c'], 21)
        self.assertIsNone(row['wind_kmh'])
        self.assertIsNone(row['gust_kmh'])

    def opener(self, page, stats='{}'):
        opener = MagicMock()
        responses = iter([page, stats])
        opener.open.side_effect = lambda *args, **kwargs: io.BytesIO(next(responses).encode())
        return opener

    def test_weathercloud_guest_contract_is_verified_before_reading(self):
        station = O.SCHOOL_STATIONS[0]
        good = 'WEATHERCLOUD_CSRF_TOKEN : "abc" var unitsCode = {temp: 0, wspd: 0, bar: 0, rain: 0}'
        with patch.object(O.urllib.request, 'build_opener', return_value=self.opener('<html></html>')):
            with self.assertRaisesRegex(ValueError, 'guest contract changed'):
                O.school_payload(station)
        imperial = good.replace('temp: 0', 'temp: 1')
        with patch.object(O.urllib.request, 'build_opener', return_value=self.opener(imperial)):
            with self.assertRaisesRegex(ValueError, 'units could not be verified'):
                O.school_payload(station)
        opener = self.opener(good, '{"temp_current": []}')
        with patch.object(O.urllib.request, 'build_opener', return_value=opener):
            self.assertEqual(O.school_payload(station), '{"temp_current": []}')
        request = opener.open.call_args_list[1][0][0]
        self.assertIn('WEATHERCLOUD_CSRF_TOKEN=abc', request.full_url)
        self.assertEqual(request.get_header('X-requested-with'), 'XMLHttpRequest')

    def test_failures_explain_the_cause_without_leaking_details(self):
        def reader(url):
            if url == W.STATION['url']:
                return '<html>no data</html>'
            if url == O.METAR:
                # Every report is from the future: none can be shown as current.
                return json.dumps([{'icaoId': 'GCLP', 'obsTime': int((NOW + dt.timedelta(hours=2)).timestamp()), 'temp': 21}])
            raise TimeoutError('https://private.example/?token=secret')

        result = O.collect(NOW, reader, lambda station: (_ for _ in ()).throw(TimeoutError()),
                           grafcan_reader=lambda now: (_ for _ in ()).throw(TimeoutError()))
        stations = {s['id']: s for s in result['stations']}
        self.assertIn('La página no contiene datos JSON utilizables.', stations[W.STATION['id']]['detail'])
        self.assertEqual(stations['GCLP']['status'], 'unavailable')
        self.assertNotIn('secret', json.dumps(result['stations']))


class RadarFailures(unittest.TestCase):
    def test_oversized_download_is_rejected(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'x' * 8_000_001
        with patch.object(R.urllib.request, 'urlopen', return_value=response):
            with self.assertRaisesRegex(ValueError, 'too large'):
                R.read('https://www.aemet.es/x')
        response.__enter__.return_value.read.return_value = b'ok'
        with patch.object(R.urllib.request, 'urlopen', return_value=response):
            self.assertEqual(R.read('https://www.aemet.es/x'), b'ok')

    def reader(self, legend=None, timeline=None):
        def read(url):
            if 'timeline' in url:
                return json.dumps(timeline if timeline is not None else
                                  [{'Producto': 'PPI.Z_005_240', 'Elementos': [scan()]}]).encode()
            if 'leyenda' in url:
                return json.dumps(legend).encode()
            if 'bounds' in url:
                return json.dumps(BOUNDS).encode()
            return png()
        return read

    def test_changed_contracts_make_the_radar_unavailable(self):
        good = {'Producto': 'PPI', 'Lista RGBA': [{'RGBA': [0, 0, 252, 255], 'Valores': [72, '']}]}
        self.assertEqual(R.collect(R.dt.datetime(2026, 10, 20, 20, tzinfo=R.dt.UTC), self.reader(good))['legend'][0]['label'], '≥72 dBZ')
        now = R.dt.datetime(2026, 10, 20, 20, tzinfo=R.dt.UTC)
        for legend in ({'Producto': 'ECHO', 'Lista RGBA': []},
                       {'Producto': 'PPI', 'Lista RGBA': [{'RGBA': [0, 0, 300, 255], 'Valores': [1, 2]}]},
                       {'Producto': 'PPI', 'Lista RGBA': [{'RGBA': [0, 0, 1, 255], 'Valores': [1]}]}):
            result = R.collect(now, self.reader(legend))
            self.assertEqual((result['status'], result['frames']), ('unavailable', []))
        result = R.collect(now, self.reader(good, timeline=[]))
        self.assertIn('ValueError', result['detail'])

    def test_rasters_that_cannot_be_rendered_are_dropped(self):
        def read(url):
            if 'imagen' in url:
                return b'not a png'
            return self.reader({'Producto': 'PPI', 'Lista RGBA': []})(url)

        result = R.collect(R.dt.datetime(2026, 10, 20, 20, tzinfo=R.dt.UTC), read)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['frames'], [])



class FakeSocket:
    """Scripted DDP messages; records what the client sends."""

    def __init__(self, messages):
        self.messages = [json.dumps(m) for m in messages]
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def send(self, text):
        self.sent.append(json.loads(text))

    def recv(self, timeout):
        return self.messages.pop(0)


class PublicFeeds(unittest.TestCase):
    def pollen(self, messages):
        socket = FakeSocket(messages)
        with patch('websockets.sync.client.connect', return_value=socket):
            return N.pollen_rows(NOW), socket.sent

    def test_seaic_subscription_answers_pings_and_keeps_only_las_palmas(self):
        rows, sent = self.pollen([
            {'msg': 'connected'}, {'msg': 'ping', 'id': 'p1'},
            {'msg': 'added', 'fields': {'idEstacion': 28, 'fecha': 20261019}},
            {'msg': 'added', 'fields': {'idEstacion': 3, 'fecha': 20261019}},
            {'msg': 'ready', 'subs': ['lpa-pollen']}])
        self.assertEqual(rows, [{'idEstacion': 28, 'fecha': 20261019}])
        self.assertEqual([m['msg'] for m in sent], ['connect', 'sub', 'pong'])
        self.assertEqual(sent[1]['params'][2], 28)
        self.assertEqual(sent[2]['id'], 'p1')

    def test_seaic_refusal_is_an_error_not_an_empty_count(self):
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            self.pollen([{'msg': 'connected'}, {'msg': 'nosub', 'id': 'lpa-pollen'}])

    def test_grafcan_pagination_is_bounded_and_stays_on_the_api(self):
        pages = {G.API + 'x': {'results': [1], 'next': G.API + 'x?page=2'},
                 G.API + 'x?page=2': {'results': [2], 'next': None}}
        self.assertEqual(list(G.api_items('x', 'k', lambda url, key: pages[url])), [1, 2])
        loop = {'results': [], 'next': G.API + 'x'}
        with self.assertRaisesRegex(ValueError, 'pagination URL'):
            list(G.api_items('x', 'k', lambda url, key: loop))
        elsewhere = {'results': [], 'next': 'https://attacker.example/steal'}
        with self.assertRaisesRegex(ValueError, 'pagination URL'):
            list(G.api_items('x', 'k', lambda url, key: elsewhere))
        pages_read = []

        def endless(url, key):
            pages_read.append(url)
            return {'results': [], 'next': G.API + f'x?page={len(pages_read) + 1}'}

        with self.assertRaisesRegex(ValueError, 'exceeds limit'):
            list(G.api_items('x', 'k', endless))
        self.assertEqual(len(pages_read), 5)


if __name__ == '__main__':
    unittest.main()
