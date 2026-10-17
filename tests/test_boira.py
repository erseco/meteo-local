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


class Confirmacio(unittest.TestCase):
    """La pregunta a Juanjo quan casa és saturada i la seva resposta (ADR 0100)."""

    def setUp(self):
        import json
        import tempfile
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        B.PREGUNTES = os.path.join(self.dir.name, "p.csv")
        B.CONFIRMACIONS = os.path.join(self.dir.name, "c.csv")
        B.CONFIG_BOT = os.path.join(self.dir.name, "bot.json")
        json.dump({"token": "x", "chat_id": 7}, open(B.CONFIG_BOT, "w"))
        self.casa = os.path.join(self.dir.name, "casa.json")
        self.crides = []

        def telegram(metode, **p):
            self.crides.append((metode, p))
            if metode == "sendMessage":
                return {"message_id": 41}, {"chat_id": 7}
            if metode == "getUpdates":
                return [{"callback_query": {"id": "q", "data": "boira:si", "from": {"id": 7},
                                            "message": {"message_id": 41}}}], {"chat_id": 7}
            return True, {"chat_id": 7}
        B.telegram = telegram
        self.nv = NV.llegeix
        NV.llegeix = lambda get: []
        self.addCleanup(setattr, NV, "llegeix", self.nv)

    def casa_amb(self, hum, plou=False):
        import json
        json.dump({"ara_casa": {"humitat_estacio": hum, "plou": plou}}, open(self.casa, "w"))

    def test_pregunta_una_vegada_i_apunta_la_resposta(self):
        self.casa_amb(99)
        self.assertEqual(B.pregunta(ARA, self.casa), 41)
        self.assertIsNone(B.pregunta(ARA + dt.timedelta(hours=1), self.casa))     # no fins d'aquí a 6 h
        self.assertEqual(B.respostes(ARA), 1)
        self.assertEqual(B.respostes(ARA), 0)                                     # una sola vegada
        # El missatge diu el que s'ha apuntat abans de respondre el toc.
        metodes = [m for m, _ in self.crides]
        self.assertLess(metodes.index("editMessageReplyMarkup"), metodes.index("answerCallbackQuery"))
        self.assertIn("answerCallbackQuery", [m for m, _ in self.crides])

    def test_no_pregunta_si_no_toca(self):
        self.casa_amb(90)
        self.assertIsNone(B.pregunta(ARA, self.casa))
        self.casa_amb(99, plou=True)
        self.assertIsNone(B.pregunta(ARA, self.casa))
        self.casa_amb(99)
        self.assertIsNone(B.pregunta(ARA.replace(hour=3), self.casa))              # de nit no
