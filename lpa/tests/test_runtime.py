# SPDX-License-Identifier: AGPL-3.0-or-later
"""Command-line entry points, local server, network readers and the sharing card."""
import io
import json
import tempfile
import threading
import unittest
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

from lpa import collect as C
from lpa import observations as O
from lpa import og_image, serve
from lpa.tests.test_lpa import NOW, feed, forecast, hourly_payload


class FakeResponse(io.BytesIO):
    """Minimal urlopen response: a readable body and a charset header."""

    def __init__(self, body, charset=None):
        super().__init__(body)
        self.headers = MagicMock()
        self.headers.get_content_charset.return_value = charset

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def reader(url, params):
    if url == C.FORECAST:
        return json.dumps(forecast())
    if url == C.ALERTS:
        return feed()
    return hourly_payload(params)


class NetworkReaders(unittest.TestCase):
    def test_fetch_encodes_parameters_and_identifies_the_project(self):
        with patch.object(C.urllib.request, 'urlopen', return_value=FakeResponse(b'{"ok":1}')) as opener:
            self.assertEqual(C.fetch('https://example.test/api', {'a': 1, 'b': 'x y'}), '{"ok":1}')
        request = opener.call_args[0][0]
        self.assertEqual(request.full_url, 'https://example.test/api?a=1&b=x+y')
        self.assertIn('meteo-local-lpa/', request.get_header('User-agent'))

    def test_station_text_respects_declared_xml_encoding(self):
        xml = '<?xml version="1.0" encoding="ISO-8859-1"?><a>Montañeta</a>'.encode('latin-1')
        with patch.object(O.urllib.request, 'urlopen', return_value=FakeResponse(xml, 'utf-8')):
            self.assertIn('Montañeta', O.get_text('https://example.test/x.xml'))
        with patch.object(O.urllib.request, 'urlopen', return_value=FakeResponse('ñ'.encode())):
            self.assertEqual(O.get_text('https://example.test/plain'), 'ñ')

    def test_school_payload_without_samples(self):
        self.assertEqual(O.school(json.dumps({'last_update': 1792500000})),
                         [{'observed_at': '2026-10-20T12:40:00+00:00'}])
        with self.assertRaises(ValueError):
            O.school(json.dumps({'temp_current': 'broken'}))


class CollectRuntime(unittest.TestCase):
    def test_failed_observation_collection_keeps_institutional_sources(self):
        environment = {'pollen': {'status': 'ok', 'last_count': {'date': '2026-10-19', 'values': []}}}
        with patch.object(O, 'collect', side_effect=RuntimeError('offline')), \
                patch('lpa.nature.collect', return_value=environment), \
                patch('lpa.radar.collect', return_value={'status': 'unavailable', 'frames': []}):
            data = C.collect(NOW, reader)
        self.assertEqual(data['lpa']['observations']['stations'], [])
        self.assertTrue(data['lpa']['observations']['providers'])
        self.assertIn('observaciones: no se pudo completar la recogida', data['errors'])
        self.assertIn('Último recuento observado', data['consultes']['es']['pollen'])
        self.assertEqual(data['lpa']['radar']['status'], 'unavailable')

    def test_finalize_persists_history_or_strips_private_archives(self):
        data = {'lpa': {'observations': {'_archive': [1]}, 'environment': {'pollen': {'_archive': [2]}}}}
        C.finalize(data)
        self.assertNotIn('_archive', data['lpa']['observations'])
        self.assertNotIn('_archive', data['lpa']['environment']['pollen'])
        with patch('lpa.history.update') as update:
            C.finalize(data, '/tmp/state')
        update.assert_called_once_with(data, '/tmp/state')

    def test_main_publishes_and_reports_missing_forecast(self):
        for hours, code in (([{}], 0), (None, 1)):
            data = {'hores': hours, 'errors': ['aire: offline']}
            with patch.object(C, 'collect', return_value=data), patch.object(C, 'publish') as publish, \
                    patch('sys.argv', ['collect', '/tmp/out/montflorit.json']), \
                    patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(C.main(), code)
            publish.assert_called_once_with('/tmp/out/montflorit.json', data)
            self.assertIn('aire: offline', output.getvalue())


class LocalServer(unittest.TestCase):
    def test_json_is_never_cached_but_pages_are(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / 'montflorit.json').write_text('{}')
            (Path(temp) / 'index.html').write_text('<!doctype html>')
            quiet = type('Quiet', (serve.Handler,), {'log_message': lambda *args: None})
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(quiet, directory=temp))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f'http://127.0.0.1:{server.server_address[1]}/'
                with urllib.request.urlopen(base + 'montflorit.json?t=1') as response:
                    self.assertEqual(response.headers['Cache-Control'], 'no-store')
                with urllib.request.urlopen(base + 'index.html') as response:
                    self.assertIsNone(response.headers['Cache-Control'])
            finally:
                server.shutdown()
                server.server_close()

    def test_refresh_survives_a_failed_collection(self):
        stop = threading.Event()
        calls = []

        def collect():
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError('offline')
            stop.set()
            return {'generat': 'now', 'errors': []}

        with patch.object(serve, 'collect', side_effect=collect), \
                patch.object(serve, 'finalize', side_effect=lambda data, state: data), \
                patch.object(serve, 'publish') as publish, patch.object(stop, 'wait'), \
                patch('sys.stdout', new_callable=io.StringIO) as output:
            serve.refresh('/tmp/out/montflorit.json', stop, None)
        self.assertEqual(len(calls), 2)
        publish.assert_called_once()
        self.assertIn('LPA update failed: offline', output.getvalue())

    def test_main_builds_serves_and_stops_the_updater(self):
        server = MagicMock()
        server.serve_forever.side_effect = KeyboardInterrupt
        with patch.object(serve, 'build', return_value='/tmp/site') as build, \
                patch.object(serve, 'ThreadingHTTPServer', return_value=server) as factory, \
                patch.object(serve, 'refresh'), \
                patch('sys.argv', ['serve', '--directory', '/tmp/site', '--port', '0']):
            with self.assertRaises(KeyboardInterrupt):
                serve.main()
        build.assert_called_once_with('/tmp/site')
        self.assertEqual(factory.call_args[0][0], ('127.0.0.1', 0))
        server.server_close.assert_called_once()


class SharingCard(unittest.TestCase):
    def test_card_size_and_committed_asset(self):
        card = og_image.draw()
        self.assertEqual((card.mode, card.size), ('RGB', og_image.SIZE))
        self.assertTrue(og_image.OUTPUT.is_file())
        self.assertTrue(og_image.island_rings(), 'Gran Canaria coastline must be found')

    def test_font_falls_back_without_installed_fonts(self):
        with patch.object(og_image, 'FONTS', ('/missing/{}.otf', '/missing/{}.ttf')):
            self.assertIsNotNone(og_image.font('Bold', 20))
        self.assertIsNotNone(og_image.font('Bold', 20))


if __name__ == '__main__':
    unittest.main()
