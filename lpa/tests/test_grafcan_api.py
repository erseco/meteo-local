# SPDX-License-Identifier: AGPL-3.0-or-later
"""Official API authentication, units, timestamps, quality and bounded pagination."""
import datetime as dt
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from lpa import grafcan as G
from lpa.tests.test_public_sources import NOW


def stream(code, name, unit):
    return {'id': code, 'name': name, 'thing': G.API + 'things/14/',
            'sensor': G.API + 'sensors/21/', 'unitOfMeasurement': {'symbol': unit}}


def observation(code, value, validity='valid', time=NOW.isoformat()):
    return {'datastream': G.API + f'datastreams/{code}/', 'result': value,
            'validity': validity, 'resultTime': time}


class GrafcanAPI(unittest.TestCase):
    def test_official_units_quality_and_sensor_identity(self):
        streams = [stream(1912, 'Air temperature (avg.)', '°C'),
                   stream(1921, 'Wind speed (avg.)', 'm/s'),
                   stream(1918, 'Atmosferic pressure (avg.)', 'mbar')]
        rows = G.parse_api(streams, [observation(1912, 23.39, 'validationPending'),
            observation(1921, 2.65), observation(1918, 1016.95),
            observation(1912, -999, 'invalid')])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['temperature_c'], 23.39)
        self.assertEqual(rows[0]['wind_kmh'], 9.54)
        self.assertEqual(rows[0]['pressure_kind'], 'unspecified')
        self.assertEqual(rows[0]['source_validity']['temperature_c'], 'validationPending')
        self.assertEqual(rows[0]['provider'], 'GRAFCAN · API oficial')
        self.assertNotIn('rain_mm', rows[0])
        self.assertTrue(rows[0]['provisional'])
        streams[0]['unitOfMeasurement']['symbol'] = '°F'
        with self.assertRaises(ValueError):
            G.parse_api(streams, [observation(1912, 75)])
        streams[0] = stream(1912, 'Air temperature (avg.)', '°C')
        streams[0]['thing'] = G.API + 'things/15/'
        with self.assertRaises(ValueError):
            G.parse_api(streams, [observation(1912, 23)])

    def test_missing_unknown_quality_and_naive_timestamps_are_not_measurements(self):
        streams = [stream(1912, 'Air temperature (avg.)', '°C')]
        for obs in [observation(1912, None), observation(1912, 20, None),
                    observation(1912, 20, 'unknown'), observation(1912, 20, time='2026-10-20T17:00:00')]:
            with self.subTest(obs=obs), self.assertRaises(ValueError):
                G.parse_api(streams, [obs])
        with self.assertRaises(ValueError):
            G.parse_api(streams, [observation(1912, 20), observation(1912, 21)])

    def test_each_sensor_keeps_its_own_timestamp(self):
        rows = G.parse_api([stream(1912, 'Air temperature (avg.)', '°C'),
                           stream(1921, 'Wind speed (avg.)', 'm/s')],
            [observation(1912, 23), observation(1921, 2, time=(NOW-dt.timedelta(minutes=10)).isoformat())])
        self.assertEqual(len(rows), 2)
        self.assertNotIn('wind_kmh', rows[0])
        self.assertNotIn('temperature_c', rows[1])

    def test_collect_filters_two_hours_and_follows_official_pages(self):
        seen = []
        def reader(url, key):
            self.assertEqual(key, 'test-only-credential')
            seen.append(url)
            if 'datastreams/?' in url:
                return {'results': [stream(1912, 'Air temperature (avg.)', '°C')], 'next': None}
            if 'page=2' in url:
                return {'results': [observation(1912, 23)], 'next': None}
            return {'results': [], 'next': url + '&page=2'}
        with patch.dict('os.environ', {'GRAFCAN_API_KEY': 'test-only-credential'}):
            rows = G.collect(NOW, reader)
        self.assertEqual(rows[0]['temperature_c'], 23)
        params = parse_qs(urlsplit(seen[1]).query)
        self.assertEqual(params['datastream__thing'], ['14'])
        self.assertEqual(params['result_time_after'], [(NOW-dt.timedelta(hours=2)).isoformat()])
        self.assertNotIn('test-only-credential', json.dumps(rows))
        with self.assertRaises(ValueError):
            list(G.api_items('datastreams/?thing=14', 'test',
                lambda *_: {'results': [], 'next': 'https://example.org/steal'}))
        with self.assertRaises(ValueError):
            list(G.api_items('datastreams/?thing=14', 'test',
                lambda *_: {'results': [], 'next': G.API + 'datastreams/?thing=14'}))

    def test_authorization_header_never_enters_query_and_redirects_are_rejected(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def read(self, _): return b'{"results": []}'
        with patch.object(G.urllib.request, 'build_opener') as build:
            build.return_value.open.return_value = Response()
            G.api_json(G.API + 'things/', 'test-only-credential')
            request = build.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header('Authorization'), 'Api-Key test-only-credential')
            self.assertNotIn('test-only-credential', request.full_url)
        self.assertIsNone(G.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.org/'))
        with self.assertRaises(ValueError): G.api_json('https://example.org/', 'test')

    def test_configured_api_failures_do_not_silently_fall_back(self):
        with patch.dict('os.environ', {'GRAFCAN_API_KEY': 'test'}), patch.object(G, 'get_payload') as dashboard:
            with self.assertRaises(HTTPError):
                G.collect(NOW, lambda *_: (_ for _ in ()).throw(HTTPError(G.API, 403, 'Forbidden', {}, None)))
            dashboard.assert_not_called()
        with patch.dict('os.environ', {'GRAFCAN_API_KEY': ''}), patch.object(G, 'get_payload') as dashboard, patch.object(G, 'parse', return_value=['fallback']):
            self.assertEqual(G.collect(NOW), ['fallback'])
            dashboard.assert_called_once_with(NOW)
