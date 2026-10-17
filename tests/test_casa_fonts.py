# SPDX-License-Identifier: AGPL-3.0-or-later
"""casa.py ante fuentes congeladas o caídas (revisión del 07-10-2026), sin red."""
import datetime as dt
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import casa  # noqa: E402
import prevision as P  # noqa: E402

AHORA = dt.datetime(2026, 10, 7, 18, 30).astimezone()



class Fonts(unittest.TestCase):
    def setUp(self):
        self.ahora, self.get_recent, self.get = P.AHORA, P.get_recent, P.get
        P.AHORA = AHORA

    def tearDown(self):
        P.AHORA, P.get_recent, P.get = self.ahora, self.get_recent, self.get

    def test_sense_ensemble_la_previsio_segueix(self):
        def get(url):
            if "ensemble" in url:
                raise RuntimeError("502")
            return json.dumps({"hourly": {"time": []}})
        P.get = get
        errors = []
        h, e = casa.modelos(AHORA, errors)
        self.assertEqual((h, e), ({"time": []}, {}))
        self.assertTrue(errors and errors[0].startswith("ensemble: "))
        with self.assertRaises(RuntimeError):
            casa.modelos(AHORA)        # sense llista d'errors, com abans: falla

    def test_open_meteo_es_torna_a_provar(self):
        # 17-10-2026: Open-Meteo respon 503 uns segons; es torna a provar dues vegades, només si és transitori.
        import io
        import urllib.error
        error = lambda codi: urllib.error.HTTPError("u", codi, "x", {}, io.BytesIO())
        respostes, esperes = [error(503), error(503), "ok"], []

        def get(url):
            r = respostes.pop(0)
            if isinstance(r, Exception):
                raise r
            return r
        P.get = get
        self.assertEqual(P.get_reintenta("u", dorm=esperes.append), "ok")
        self.assertEqual(esperes, [5, 15])
        respostes[:] = [error(503)] * 3
        with self.assertRaises(urllib.error.HTTPError):
            P.get_reintenta("u", dorm=esperes.append)          # al tercer, prou
        respostes[:], esperes[:] = [error(400), "ok"], []
        with self.assertRaises(urllib.error.HTTPError):
            P.get_reintenta("u", dorm=esperes.append)          # un error de la consulta no es reintenta
        self.assertEqual(esperes, [])


if __name__ == "__main__":
    unittest.main()
