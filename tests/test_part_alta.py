# SPDX-License-Identifier: AGPL-3.0-or-later
"""La parte alta del barrio, «Ara» sin la estación de casa y la vigilancia de
las estaciones (ADR 0087), sin red."""
import datetime as dt
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import casa  # noqa: E402
import estacions as ES  # noqa: E402
import part_alta as PA  # noqa: E402

TZ = dt.timezone(dt.timedelta(hours=2))
ARA = dt.datetime(2026, 10, 13, 16, 0, tzinfo=TZ)


def veina(est, t, rosada=10, minuts=5, plou=False):
    return {"estacio": est, "hora": (ARA - dt.timedelta(minutes=minuts)).isoformat(timespec="minutes"),
            "temperatura": t, "humitat": 60, "rosada": rosada, "pluja_1h": 0.0, "pluja_avui": 0.0,
            "plou": plou, "compta": est != "ICERDA48", "intensitat": 0.0, "files": []}


class PartAlta(unittest.TestCase):
    def test_ara_mesurada(self):
        vs = [veina("ICERDA6", 18), veina("ICERDA18", 20), veina("ICERDA28", 21), veina("ICERDA48", 22)]
        self.assertEqual(PA.ara(18.4, vs, ARA), 2.6)            # mediana 21 − 18,4
        # Una sola de arriba, o lecturas viejas: no se dice.
        self.assertIsNone(PA.ara(18.4, [veina("ICERDA28", 21)], ARA))
        self.assertIsNone(PA.ara(18.4, [veina("ICERDA18", 20, minuts=50), veina("ICERDA28", 21, minuts=50)], ARA))
        self.assertIsNone(PA.ara(None, vs, ARA))

    def test_per_hores_amb_el_registre_i_la_de_partida(self):
        casa_h, veines_h = {}, {e: {} for e in PA.ALTES}
        for d in range(12):
            c = (ARA - dt.timedelta(days=d + 1)).strftime("%Y-%m-%dT%H:%M")    # a les 16 h
            casa_h[c] = 20.0
            for e in PA.ALTES:
                veines_h[e][c] = 23.0
        t = PA.per_hores(ARA, casa_h, veines_h, eps=[])
        self.assertEqual(t[14], 3.0)                                # del registro: 12 tardes (16 h = 14 UTC)
        self.assertEqual(t[3], PA.inicial()[3])                     # sin bastantes, la de partida
        files = PA.a_les_hores([{"hora": "2026-10-13T15:00", "fins": "2026-10-13T16:00"}], {13: 1.0, 14: 3.0})
        self.assertEqual(files[0]["dif_alta"], 2.0)

    def test_hora_solar_als_dos_costats_del_canvi_dhora(self):
        # Las 15 h de verano y las 14 h de invierno son la misma hora de sol.
        self.assertEqual(PA.hora_solar("2026-10-24T15:00"), 13)
        self.assertEqual(PA.hora_solar("2026-10-26T14:00"), 13)
        self.assertEqual(PA.hora_solar("2027-03-29T15:00"), 13)
        # La hora que se repite en octubre (ADR 0089): dos horas de sol.
        self.assertEqual(PA.hora_solar("2026-10-25T02:00+02:00"), 0)
        self.assertEqual(PA.hora_solar("2026-10-25T02:00+01:00"), 1)
        self.assertEqual(PA.hora_solar(ARA), 14)

    def test_el_mes_del_canvi_no_barreja_hores_de_sol(self):
        # 15 días antes y 15 después del 25-10-2026: la parte alta, 3 °C más
        # cálida a las 13 UTC (15 h de verano, 14 h de invierno) y nada el
        # resto. Con la hora del reloj, la de las 15 h mezclaba las dos.
        ara = dt.datetime(2026, 11, 9, 20, 0, tzinfo=dt.timezone(dt.timedelta(hours=1)))
        casa_h, veines_h = {}, {e: {} for e in PA.ALTES}
        for d in range(1, 30):
            dia = (ara - dt.timedelta(days=d)).date()
            for h in range(24):
                t = dt.datetime(dia.year, dia.month, dia.day, h, tzinfo=dt.timezone.utc)
                c = PA.P.ZONA.fromutc(t.replace(tzinfo=PA.P.ZONA)).strftime("%Y-%m-%dT%H:%M")
                casa_h[c] = 10.0
                for e in PA.ALTES:
                    veines_h[e][c] = 13.0 if h == 13 else 10.0
        t = PA.per_hores(ara, casa_h, veines_h, eps=[])
        self.assertEqual(t[13], 3.0)
        self.assertEqual(t[12], 0.0)
        self.assertEqual(t[14], 0.0)
        files = PA.a_les_hores([{"hora": "2026-11-10T14:00", "fins": "2026-11-10T15:00"}], t)
        self.assertEqual(files[0]["dif_alta"], 1.5)                 # de 14 a 15 h de invierno: 13 y 14 UTC

    def test_la_de_partida_te_les_24_hores(self):
        t = PA.inicial()
        self.assertEqual(sorted(t), list(range(24)))
        self.assertGreater(t[14], 1)                                 # tarde: la parte alta, más cálida
        self.assertLess(abs(t[3]), 1)                                # de noche, casi igual


class AraSenseCasa(unittest.TestCase):
    def test_amb_icerda6_vora_la_riera(self):
        vs = [veina("ICERDA6", 15, rosada=8), veina("ICERDA18", 17), veina("ICERDA28", 18)]
        a = casa.ara_sense_casa(vs, {14: 1.5}, ARA)
        self.assertEqual(a["temperatura"], 15)
        self.assertIsNone(a["pressio"])
        self.assertEqual(a["humitat"], round(casa.SE.humitat(10, 15)))   # rocío mediano 10

    def test_sense_icerda6_la_part_alta_menys_la_diferencia(self):
        vs = [veina("ICERDA18", 17), veina("ICERDA28", 18)]
        self.assertEqual(casa.ara_sense_casa(vs, {14: 1.5}, ARA)["temperatura"], 16.0)
        self.assertIsNone(casa.ara_sense_casa([veina("ICERDA28", 18)], {14: 1.5}, ARA))
        self.assertIsNone(casa.ara_sense_casa([], {14: 1.5}, ARA))


class Vigilancia(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.dir.name, "estat.json")
        self.enviats = []

    def tearDown(self):
        self.dir.cleanup()

    def pas(self, minuts, casa_ok, veines):
        return ES.vigila(casa_ok, veines, ARA + dt.timedelta(minutes=minuts), self.enviats.append, self.ruta)

    def test_la_casa_avisa_als_30_minuts_i_quan_torna(self):
        totes = list(casa.C.VEINES)
        self.assertEqual(self.pas(0, False, totes), [])
        self.assertEqual(self.pas(20, False, totes), [])
        m = self.pas(30, False, totes)
        self.assertEqual(len(m), 1)
        self.assertIn("l'estació de casa no respon des de les 16:00", m[0])
        self.assertEqual(self.pas(45, False, totes), [])            # una sola vez
        self.assertEqual(self.pas(60, True, totes), ["Temps a Montflorit: l'estació de casa torna a respondre."])

    def test_sense_weather_underground_un_sol_avis(self):
        self.pas(0, True, [])
        m = self.pas(60, True, [])
        self.assertEqual(len(m), 1)
        self.assertIn("Weather Underground", m[0])
        self.assertEqual(self.pas(24 * 60, True, []), [])           # ni la parte alta ni cada vecina
        m = self.pas(24 * 60 + 15, True, list(casa.C.VEINES))
        self.assertEqual(m, ["Temps a Montflorit: Weather Underground torna a respondre."])

    def test_la_part_alta_i_una_veina(self):
        self.pas(0, True, ["ICERDA6", "ICERDA18"])
        self.assertIn("part alta", self.pas(60, True, ["ICERDA6", "ICERDA18"])[0])
        m = self.pas(24 * 60, True, ["ICERDA6", "ICERDA18"])
        self.assertEqual(sorted(x.split()[5] for x in m), ["ICERDA28", "ICERDA48"])

    def test_sense_claus_no_es_vigila(self):
        # La reserva de IONOS no té les claus d'Ecowitt ni de Weather Underground.
        self.assertEqual(self.pas(0, None, None), [])
        self.assertEqual(self.pas(48 * 60, None, None), [])
        self.assertEqual(ES._llegeix(self.ruta), {})

    def test_el_que_ja_no_es_vigila_s_oblida(self):
        self.pas(0, False, [])
        self.assertEqual(self.pas(60, None, None), [])
        self.assertEqual(ES._llegeix(self.ruta), {})


if __name__ == "__main__":
    unittest.main()
