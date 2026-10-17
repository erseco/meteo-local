# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pruebas del historial de la gráfica y del acierto de la previsión (historial.py, ADR 0099).
El otro test_historial.py es el de la página «Perill».""" 
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ARREL)
import historial as H  # noqa: E402


class Historial(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        reg = self.dir.name
        dia = "2026-10-16"
        with open(os.path.join(reg, "estacio-casa.csv"), "w", encoding="utf-8") as f:
            f.write("fins,pluja_mm,temperatura,humitat,rosada,pressio,solar\n")
            for h in range(1, 25):
                fins = f"{dia}T{h:02d}:00" if h < 24 else "2026-10-17T00:00"
                f.write(f"{fins},{1.0 if h in (20, 21) else 0.0},{15 + h % 10},90,12,1015,0\n")
        # Meteocat sec a totes les hores: el zero de casa val (aprenentatge.pluja_observada).
        import config as C
        for codi in C.ESTACIONES:
            with open(os.path.join(reg, f"meteocat-{codi}.csv"), "w", encoding="utf-8") as f:
                f.write("fins,pluja_mm\n" + "".join(
                    f"{(f'{dia}T{h:02d}:00' if h < 24 else '2026-10-17T00:00')},0.0\n" for h in range(1, 25)))
        # La previsió de les 7 i una altra de les 6 (no és la que compta).
        def emissio(emes, delta):
            hores = []
            for h in range(8, 25):
                fins = f"{dia}T{h:02d}:00" if h < 24 else "2026-10-17T00:00"
                hores.append({"fins": fins, "mostrat": {"temperatura": 15 + h % 10 + delta,
                                                         "probabilitat": 0.8 if h in (20, 21, 22) else 0.05,
                                                         "pluja_mm": 1.0}})
            return json.dumps({"emes": emes, "hores": hores})
        with open(os.path.join(reg, "casa-2026-10.jsonl"), "w", encoding="utf-8") as f:
            f.write(emissio(f"{dia}T06:03+02:00", 5) + "\n" + emissio(f"{dia}T07:03+02:00", 1) + "\n")
        self.dies = H.tots(dt.date(2026, 10, 17), reg)

    def test_mesurat_i_previsio_de_les_7(self):
        d = next(x for x in self.dies if x["dia"] == "2026-10-16")
        self.assertEqual(d["previsio_de"], "2026-10-16T07:03+02:00")
        self.assertEqual(len(d["hores"]), 24)
        f = d["hores"][9]                                  # de 9 a 10
        self.assertEqual((f["hora"], f["temperatura"], f["prev"]["temperatura"]), ("2026-10-16T09:00", 15.0, 16.0))
        self.assertNotIn("prev", d["hores"][3])            # abans de les 7, cap previsió

    def test_encert(self):
        e = next(x for x in self.dies if x["dia"] == "2026-10-16")["encert"]
        # 1 °C d'error a totes les hores amb previsió (de 7 a mitjanit: 17).
        self.assertEqual(e["temperatura"], {"error": 1.0, "hores": 17})
        # Deia pluja a les 19, 20 i 21 (fins 20, 21, 22): va ploure a dues (fins 20 i 21).
        self.assertEqual(e["pluja"]["plou"], [2, 3])
        self.assertEqual(e["pluja"]["sec"], [14, 14])
        i = H.index(self.dies, dt.date(2026, 10, 17))
        self.assertEqual(i["encert"]["darrers"]["temperatura"]["hores"], 17)
        self.assertEqual(list(i["encert"]["mesos"]), ["2026-10"])
        self.assertIn("2026-10-17", i["dies"])

    def test_el_dia_del_canvi_d_hora_te_25_hores(self):
        self.assertEqual(len(H.hores_del_dia(dt.date(2026, 10, 25))), 25)
        self.assertEqual(len(H.hores_del_dia(dt.date(2027, 3, 28))), 23)
