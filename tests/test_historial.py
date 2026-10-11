# SPDX-License-Identifier: AGPL-3.0-or-later
"""El historial de avisos de peligro para la página «Perill» (avisos_bot.py, ADR 0071)."""
import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import avisos_bot as AB  # noqa: E402

ARA = dt.datetime(2026, 10, 11, 12, 0).astimezone()


def avis(minuts, episodi, nivell, text="t", **extra):
    hora = (ARA + dt.timedelta(minutes=minuts)).isoformat(timespec="minutes")
    return {"id": f"perill:{episodi}:{minuts}", "tipus": "perill", "nivell": nivell, "hora": hora,
            "ca": text, "es": text, "episodi": episodi, **extra}


class Historial(unittest.TestCase):
    def test_comencament_i_final_en_una_sola_entrada(self):
        estat = {}
        AB.historial(estat, [avis(0, "incendi:x", "incendi", "🔥 foc")], ARA)
        h = AB.historial(estat, [avis(60, "incendi:x", "fi", "🟢 acabat")], ARA)
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0]["inici"][11:16], h[0]["fi"][11:16]), ("12:00", "13:00"))
        self.assertEqual((h[0]["ca"], h[0]["fi_ca"]), ("🔥 foc", "🟢 acabat"))

    def test_si_puja_de_nivell_es_queda_el_pitjor_i_el_text_nou(self):
        estat = {}
        AB.historial(estat, [avis(0, "riera:a", "atencio", "atenció")], ARA)
        AB.historial(estat, [avis(30, "riera:a", "perill", "perill")], ARA)
        h = AB.historial(estat, [avis(60, "riera:a", "groc", "després")], ARA)
        self.assertEqual(len(h), 1)
        self.assertEqual((h[0]["nivell"], h[0]["ca"]), ("perill", "després"))

    def test_un_episodi_nou_despres_d_un_d_acabat(self):
        estat = {}
        AB.historial(estat, [avis(0, "propi", "groc"), avis(10, "propi", "fi")], ARA)
        h = AB.historial(estat, [avis(600, "propi", "taronja")], ARA)
        self.assertEqual(len(h), 2)
        self.assertFalse(h[1].get("fi"))

    def test_sense_episodi_no_hi_va(self):
        estat = {}
        pluja = {"id": "pluja:x", "tipus": "pluja", "nivell": None, "hora": ARA.isoformat(), "ca": "p", "es": "p"}
        self.assertEqual(AB.historial(estat, [pluja], ARA), [])

    def test_un_pla_que_ja_no_es_mostra_acaba(self):
        estat = {"oficials": {"plans": {"INUNCAT": {"fase": "alerta", "nom": "d'inundacions"}}}}
        AB.historial(estat, [avis(0, "pla:INUNCAT", "pc")], ARA)
        self.assertFalse(estat["historial"][0].get("fi"))
        estat["oficials"]["plans"]["INUNCAT"]["ocult"] = True
        h = AB.historial(estat, [], ARA + dt.timedelta(hours=2))
        self.assertEqual(h[0]["fi"][11:16], "14:00")

    def test_es_guarda_un_any(self):
        estat = {}
        AB.historial(estat, [avis(0, "aemet:pluja:x", "groc", fins=ARA.isoformat())], ARA)
        self.assertEqual(len(AB.historial(estat, [], ARA + dt.timedelta(days=300))), 1)
        self.assertEqual(AB.historial(estat, [], ARA + dt.timedelta(days=AB.HISTORIAL_DIES + 1)), [])

    def test_s_uneix_amb_el_publicat_per_l_altre_servidor(self):
        # El NAS torna després que la reserva hagi vist un incendi i el seu final.
        reserva = AB.historial({}, [avis(0, "incendi:r", "incendi"), avis(30, "incendi:r", "fi")], ARA)
        estat = {}
        AB.historial(estat, [avis(-600, "propi", "groc")], ARA)
        h = AB.historial(estat, [], ARA + dt.timedelta(hours=1), reserva)
        self.assertEqual([e["clau"] for e in h], ["propi", "incendi:r"])
        self.assertEqual(h[1]["fi"][11:16], "12:30")
        # Si l'altre ja l'ha tancat, val el final.
        obert = AB.historial({}, [avis(0, "riera:a", "atencio")], ARA)
        tancat = AB.historial({}, [avis(0, "riera:a", "atencio"), avis(60, "riera:a", "fi")], ARA)
        self.assertEqual(AB.fusiona(obert, tancat)[0]["fi"][11:16], "13:00")

    def test_un_avis_nou_continua_l_episodi_obert_de_l_altre(self):
        reserva = AB.historial({}, [avis(0, "incendi:x", "incendi", "primer")], ARA)
        h = AB.historial({}, [avis(15, "incendi:x", "incendi", "repetit")], ARA, reserva)
        self.assertEqual(len(h), 1)
        h = AB.historial({"historial": h}, [avis(60, "incendi:x", "fi")], ARA)
        self.assertTrue(all(e.get("fi") for e in h))


if __name__ == "__main__":
    unittest.main()
