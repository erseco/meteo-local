# SPDX-License-Identifier: AGPL-3.0-or-later
"""La boira de l'hora en curs i la vigilància d'ICON (nuvols.py, boira.py; ADR 0100)."""
import datetime as dt
import os
import sys
import unittest

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ARREL)
import boira as B  # noqa: E402
import nuvols as NV  # noqa: E402

ARA = dt.datetime(2026, 10, 17, 8, 40).astimezone()


class Boira(unittest.TestCase):
    def test_el_metar_de_la_boira(self):
        self.assertTrue(NV.te_boira("METAR LELL 170630Z VRB02KT 0150 R31/0375N FG VV002 16/15 Q1019"))
        self.assertTrue(NV.te_boira("METAR LELL 170430Z AUTO 28002KT 4000 BR BCFG BKN001 16/15 Q1019"))
        # La boirina no és boira, ni la «FG» d'un altre mot.
        self.assertFalse(NV.te_boira("METAR LELL 170400Z 29002KT 4000 BR BKN001 16/15 Q1019"))
        self.assertFalse(NV.te_boira(None))

    def test_nomes_si_es_recent(self):
        obs = [{"t": ARA - dt.timedelta(minutes=10), "brut": "METAR LELL 170630Z 0150 FG VV002"}]
        self.assertTrue(NV.boira_ara(obs, ARA))
        self.assertFalse(NV.boira_ara(obs, ARA + dt.timedelta(hours=1)))
        self.assertFalse(NV.boira_ara([], ARA))

    def test_observada_amb_la_casa_saturada(self):
        self.assertTrue(B.observada("FG VV002", 99))
        self.assertFalse(B.observada("FG VV002", 85))
        self.assertFalse(B.observada("BR", 100))
