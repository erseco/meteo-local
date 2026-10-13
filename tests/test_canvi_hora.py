# SPDX-License-Identifier: AGPL-3.0-or-later
"""Proves del canvi d'hora (sense xarxa): Open-Meteo posa a tota la sèrie el
desfase del moment de la consulta, i la web ha de fer servir l'hora real."""
import datetime as dt
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import casa  # noqa: E402
import config as C  # noqa: E402
import prevision as P  # noqa: E402
import registre as R  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot"))
import bot as B  # noqa: E402


def resposta(desfase_h, inici, n):
    """Com respon Open-Meteo: totes les hores amb el mateix desfase."""
    t0 = dt.datetime.fromisoformat(inici)
    return {"utc_offset_seconds": desfase_h * 3600,
            "hourly": {"time": [(t0 + dt.timedelta(hours=x)).strftime("%Y-%m-%dT%H:%M") for x in range(n)]}}


class HoresLocals(unittest.TestCase):
    def test_octubre_l_hora_que_es_repeteix(self):
        # 25-10-2026: a les 3 (estiu) tornen a ser les 2. Consultat el 24, en
        # hora d'estiu, Open-Meteo ho dona tot a GMT+2 i sense hora repetida.
        r = P.horas_locales(resposta(2, "2026-10-25T00:00", 6))
        self.assertEqual(r["hourly"]["time"], ["2026-10-25T00:00", "2026-10-25T01:00", "2026-10-25T02:00+02:00",
                                               "2026-10-25T02:00+01:00", "2026-10-25T03:00", "2026-10-25T04:00"])

    def test_març_l_hora_que_no_hi_es(self):
        # 28-03-2027: a les 2 (hivern) passen a ser les 3.
        r = P.horas_locales(resposta(1, "2027-03-28T00:00", 5))
        self.assertEqual(r["hourly"]["time"], ["2027-03-28T00:00", "2027-03-28T01:00", "2027-03-28T03:00",
                                               "2027-03-28T04:00", "2027-03-28T05:00"])

    def test_desfase_de_la_consulta_i_no_de_l_hora(self):
        # El 13-10-2026 Open-Meteo donava el 26-10 a GMT+2: les seves 22 h
        # són les 21 h d'hivern.
        r = P.horas_locales(resposta(2, "2026-10-26T22:00", 1))
        self.assertEqual(r["hourly"]["time"], ["2026-10-26T21:00"])
        # En hora d'hivern, l'estiu va una hora més tard.
        r = P.horas_locales(resposta(1, "2027-04-02T10:00", 1))
        self.assertEqual(r["hourly"]["time"], ["2027-04-02T11:00"])

    def test_sol_i_dates(self):
        r = P.horas_locales({"utc_offset_seconds": 7200,
                             "daily": {"time": ["2026-10-26"], "sunrise": ["2026-10-26T08:05"],
                                       "sunset": ["2026-10-26T19:02"]}})
        self.assertEqual(r["daily"], {"time": ["2026-10-26"], "sunrise": ["2026-10-26T07:05"],
                                      "sunset": ["2026-10-26T18:02"]})

    def test_clau_hora(self):
        estiu = dt.datetime(2026, 10, 25, 0, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(P.clau_hora(estiu), "2026-10-25T02:00+02:00")
        self.assertEqual(P.clau_hora(estiu + dt.timedelta(hours=1)), "2026-10-25T02:00+01:00")
        self.assertEqual(P.clau_hora(estiu + dt.timedelta(hours=2)), "2026-10-25T03:00")
        self.assertEqual(P.clau_hora(dt.datetime(2026, 10, 13, 17, 0, tzinfo=dt.timezone.utc)), "2026-10-13T19:00")


class TaulaAmbCanvi(unittest.TestCase):
    def previsio(self, desfase_h, inici, desde):
        r = P.horas_locales(resposta(desfase_h, inici, 72))
        h = r["hourly"]
        h["temperature_2m_meteofrance_seamless"] = [15.0] * 72
        for m in C.MODELOS_FINOS:
            h[f"precipitation_{m}"] = [0.0] * 72
        return casa.previsio(desde, h, {}, [])

    def test_octubre_dues_franges_de_2_a_3(self):
        files = self.previsio(2, "2026-10-24T00:00", dt.datetime(2026, 10, 25, 0, 30).astimezone())
        hores = [f["hora"] for f in files[:5]]
        self.assertEqual(hores, ["2026-10-25T00:00", "2026-10-25T01:00", "2026-10-25T02:00+02:00",
                                 "2026-10-25T02:00+01:00", "2026-10-25T03:00"])
        # Cada fila acaba on comença la següent, i totes duren una hora.
        for a, b in zip(files, files[1:]):
            self.assertEqual(a["fins"], b["hora"])
            fi, ini = (dt.datetime.fromisoformat(x).astimezone() for x in (a["fins"], a["hora"]))
            self.assertEqual(fi - ini, dt.timedelta(hours=1))
        self.assertEqual(files[-1]["fins"], "2026-10-26T21:00")

    def test_març_sense_franja_de_2_a_3(self):
        files = self.previsio(1, "2027-03-27T00:00", dt.datetime(2027, 3, 28, 0, 30).astimezone())
        self.assertEqual([f["hora"][11:13] for f in files[:4]], ["00", "01", "03", "04"])
        self.assertEqual(files[-1]["fins"], "2027-03-29T21:00")

    def test_el_bot_compara_i_ordena_les_hores(self):
        files = self.previsio(2, "2026-10-24T00:00", dt.datetime(2026, 10, 25, 0, 30).astimezone())
        hores = [B.hora_local(f["hora"]) for f in files]
        self.assertEqual(hores, sorted(hores))
        dades = {"hores": files}
        # A les 2.30 d'hivern, la segona franja de 2 a 3.
        moment = dt.datetime(2026, 10, 25, 1, 30, tzinfo=dt.timezone.utc)
        self.assertEqual(B.hora_ara(dades, moment)["hora"], "2026-10-25T02:00+01:00")


class Registre(unittest.TestCase):
    def test_les_dues_hores_de_2_a_3_no_es_trepitgen(self):
        dir_abans = R.DIR
        with tempfile.TemporaryDirectory() as d:
            R.DIR = d
            try:
                utc = dt.datetime(2026, 10, 25, 0, 0, tzinfo=dt.timezone.utc)
                R.apunta_meteocat("XF", {utc + dt.timedelta(hours=x): float(x) for x in range(3)})
                with open(os.path.join(d, "meteocat-XF.csv"), encoding="utf-8") as f:
                    files = f.read().split()
            finally:
                R.DIR = dir_abans
        self.assertEqual(files[1:], ["2026-10-25T02:00+02:00,0.0", "2026-10-25T02:00+01:00,1.0", "2026-10-25T03:00,2.0"])


if __name__ == "__main__":
    unittest.main()
