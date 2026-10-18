# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pruebas del historial de la gráfica y del acierto de la previsión (historial.py, ADR 0099).
El otro test_historial.py es el de la página «Perill».""" 
import datetime as dt
import json
import os
import shutil
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
        # Sol directe sobre el termòmetre de 12:10 a 13:20 (ADR 0081): toca les hores
        # en punt de les 13 (i, per tant, els trams de 12 a 13 i de 13 a 14).
        with open(os.path.join(reg, "sol-estacio.csv"), "w", encoding="utf-8") as f:
            f.write(f"inici,fi,exces_max\n{dia}T12:10+02:00,{dia}T13:20+02:00,3.1\n")
        self.dies = H.tots(dt.date(2026, 10, 17), reg)

    def test_mesurat_i_previsions_per_antelacio(self):
        d = next(x for x in self.dies if x["dia"] == "2026-10-16")
        self.assertEqual(len(d["hores"]), 24)
        f = d["hores"][9]                                  # de 9 a 10
        # La temperatura del tram és la mitjana de les lectures de les 9 (24 °C) i
        # de les 10 (15 °C), que és el que anuncia la previsió (auditoria del
        # 18-10-2026: abans es comparava amb la lectura del final).
        self.assertEqual((f["hora"], f["temperatura"]), ("2026-10-16T09:00", 19.5))
        self.assertIsNone(d["hores"][0]["temperatura"])     # de 0 a 1: sense lectura de les 0
        # Les hores tocades pel sol porten la marca; les altres, no.
        self.assertTrue(d["hores"][12].get("sol") and d["hores"][13].get("sol"))
        self.assertFalse(d["hores"][11].get("sol") or d["hores"][14].get("sol"))
        # La de les 7:03, 2 h abans (16 °C); la de les 6:03, 3 h abans (20 °C).
        self.assertEqual(f["prev"]["2"][0], 16.0)
        self.assertEqual(f["prev"]["3"][0], 20.0)
        self.assertNotIn("prev", d["hores"][3])            # cap publicació abans de les 3

    def test_encert_per_antelacio(self):
        e = next(x for x in self.dies if x["dia"] == "2026-10-16")["encert"]
        # Amb 1 h: el tram de 6 a 7 (mitjana 21,5 °C) amb la de les 6:03 (27 °C: 5,5
        # d'error) i el de 7 a 8 (22,5) amb la de les 7:03 (24: 1,5). Cada publicació
        # dona una hora per antelació.
        self.assertEqual(e["1"]["temperatura"], {"error": 3.5, "hores": 2})
        # Els mm esperats (probabilitat 0,05 per 1 mm, dues hores; ADR 0103) i els
        # mesurats, a les mateixes hores (18-10-2026).
        self.assertEqual(e["1"]["mm"], {"previst": 0.1, "mesurat": 0.0, "hores": 2})
        f = next(x for x in self.dies if x["dia"] == "2026-10-16")["hores"][9]
        self.assertEqual(f["prev"]["2"][2], 1.0)
        self.assertEqual(e["2"]["temperatura"]["hores"], 2)
        i = H.index(self.dies, dt.date(2026, 10, 17))
        self.assertEqual(i["encert"]["2"]["darrers"]["temperatura"]["hores"], 2)
        self.assertEqual(i["encert"]["2"]["darrers"]["mm"]["hores"], 2)
        self.assertEqual(list(i["encert"]["2"]["mesos"]), ["2026-10"])
        self.assertIn("2026-10-17", i["dies"])
        self.assertEqual(sorted(map(int, i["encert"])), list(range(1, 24)))

    def test_el_format_nou_es_refa_per_tandes(self):
        # 18-10-2026: tots els dies de cop eren 22 arxius i IONOS en vol 12 com a
        # molt. Cada passada, els 2 de sempre i 3 dels vells, fins que hi són tots.
        with tempfile.TemporaryDirectory() as reg, tempfile.TemporaryDirectory() as sortida:
            for f in os.listdir(self.dir.name):
                shutil.copy(os.path.join(self.dir.name, f), reg)
            avui = dt.date(2026, 10, 17)
            tandes = []
            while True:
                noms = H.fes(sortida, 2, avui, reg)
                tandes.append([n for n in noms if n != "historial.json"])
                if open(os.path.join(reg, "historial-format")).read() == str(H.FORMAT):
                    break
            dies = (avui - H.PRIMER_DIA).days + 1
            self.assertTrue(all(len(t) <= 5 for t in tandes))
            self.assertEqual(len({n for t in tandes for n in t}), dies)
            self.assertEqual(H.fes(sortida, 2, avui, reg), ["historial.json", "historial-2026-10-16.json",
                                                            "historial-2026-10-17.json"])

    def test_el_dia_del_canvi_d_hora_te_25_hores(self):
        self.assertEqual(len(H.hores_del_dia(dt.date(2026, 10, 25))), 25)
        self.assertEqual(len(H.hores_del_dia(dt.date(2027, 3, 28))), 23)

    def test_el_sol_no_compta_per_a_la_temperatura(self):
        # Amb 6 h d'antelació, la de les 6:03 dona el tram de 12 a 13 i la de les
        # 7:03 el de 13 a 14, tots dos tocats pel sol: cap compta. Amb 5 h, el d'11
        # a 12 sí i el de 12 a 13 no; amb 4 h, els dos.
        e = next(x for x in self.dies if x["dia"] == "2026-10-16")["encert"]
        self.assertEqual(e["6"]["temperatura"]["hores"], 0)
        self.assertEqual(e["5"]["temperatura"]["hores"], 1)
        self.assertEqual(e["4"]["temperatura"]["hores"], 2)

    def test_la_pluja_per_franges(self):
        # Per a cada franja de probabilitat anunciada: hores, en quantes va ploure
        # i la suma del que deia (auditoria del 18-10-2026: de 11 hores amb 70 % o
        # més, va ploure en 6). Es conserven «plou» i «sec» dels fitxers d'abans.
        def fila(p, mm):
            return {"temperatura": None, "pluja_mm": mm, "prev": {"1": [None, p, None]}}
        files = [fila(0.05, 0), fila(0.1, 0.5), fila(0.2, 0), fila(0.3, 0), fila(0.5, 1.0), fila(0.9, 1.0),
                 fila(0.7, 0), fila(0.95, 0.2), fila(None, 1.0), fila(0.5, None)]
        e = H.encert(files, 1)
        self.assertEqual(e["pluja"]["franges"], {"0": [2, 1, 0.15], "20": [2, 0, 0.5], "50": [1, 1, 0.5],
                                                 "70": [3, 2, 2.55]})
        self.assertEqual(e["pluja"]["plou"], [3, 4])
        self.assertEqual(e["pluja"]["sec"], [1, 2])
        self.assertEqual(H.franja(0.199), 0)
        self.assertEqual(H.franja(0.7), 70)
        s = H.suma([e, e])
        self.assertEqual(s["pluja"]["franges"]["70"], [6, 4, 5.1])
        # Un dia guardat sense franges (format 2) se suma igual.
        vell = {"temperatura": {"error": None, "hores": 0}, "pluja": {"plou": [0, 0], "sec": [0, 0]},
                "mm": {"previst": 0, "mesurat": 0, "hores": 0}}
        self.assertEqual(H.suma([e, vell])["pluja"]["franges"]["0"], [2, 1, 0.15])
        i = H.index(self.dies, dt.date(2026, 10, 17))
        self.assertEqual(i["franges"], [0, 20, 50, 70])

