# SPDX-License-Identifier: AGPL-3.0-or-later
"""Los avisos de peligro de Meteocat de la comarca, junto a los planes (ADR 0067), sin red."""
import datetime as dt
import json
import os
import sys
import tempfile
import unittest

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ARREL)
sys.path.insert(0, os.path.join(ARREL, "bot"))
import avisos_bot as AB  # noqa: E402
import bot as B  # noqa: E402
import smp  # noqa: E402

AHORA = dt.datetime(2026, 10, 10, 19, 0).astimezone()


def afectacio(comarca, perill, dia="2026-10-10T00:00Z"):
    return {"dia": dia, "llindar": "Intensitat > 20 mm / 30 minuts", "auxiliar": False, "perill": perill,
            "idComarca": comarca, "nivell": 1}


# Com l'exemple de /smp/episodis-oberts de la documentació de l'API de Meteocat.
EPISODIS = [{
    "estat": {"nom": "Obert", "data": None}, "meteor": {"nom": "Intensitat de pluja"},
    "avisos": [{
        "tipus": "Avís", "dataEmisio": "2026-10-10T08:09Z", "dataInici": "2026-10-10T12:00Z",
        "dataFi": "2026-10-11T05:59Z", "estat": "Vigent",
        "evolucions": [
            {"dia": "2026-10-10T00:00Z", "llindar1": "Intensitat > 20 mm / 30 minuts", "periodes": [
                {"nom": "00-06", "afectacions": None}, {"nom": "06-12", "afectacions": None},
                {"nom": "12-18", "afectacions": [afectacio(40, 3), afectacio(41, 2)]},
                {"nom": "18-00", "afectacions": [afectacio(40, 2)]}]},
            {"dia": "2026-10-11T00:00Z", "llindar1": "Intensitat > 20 mm / 30 minuts", "periodes": [
                {"nom": "00-06", "afectacions": [afectacio(40, 1, "2026-10-11T00:00Z")]}]}]},
        {"tipus": "Preavís", "estat": "Vigent", "evolucions": [{"dia": "2026-10-12T00:00Z", "periodes": [
            {"nom": "00-06", "afectacions": [afectacio(40, 5, "2026-10-12T00:00Z")]}]}]}]},
    {"estat": {"nom": "Obert"}, "meteor": {"nom": "Acumulació de pluja"}, "avisos": [{
        "tipus": "Avís", "estat": "Vigent", "dataEmisio": "2026-10-10T08:09Z",
        "evolucions": [{"dia": "2026-10-10T00:00Z", "periodes": [
            {"nom": "12-18", "afectacions": [afectacio(31, 4)]}]}]}]},
]


def pagina(episodis):
    return ("<script>\n            Meteocat.avisosSMP({\n                dom: 'mapaAvisos',\n"
            "                prediccions: [{\"general\":{}}],\n"
            "                episodisPreavisos: [{\"avisos\": [{\"tipus\": \"Preavís\"}]}],\n"
            f"                avisos: {json.dumps(episodis)},\n                cataleg: []\n            }});\n</script>")


class Smp(unittest.TestCase):
    def test_llegeix_els_avisos_de_la_pagina(self):
        self.assertEqual(smp.episodis(pagina(EPISODIS)), EPISODIS)
        self.assertEqual(smp.episodis(pagina([])), [])
        with self.assertRaises(ValueError):
            smp.episodis("<html>sense avisos</html>")

    def test_nomes_els_vigents_de_la_comarca(self):
        a = smp.de_la_comarca(EPISODIS, 40)
        # El preavís i l'avís d'una altra comarca no hi són; les franges seguides, juntes.
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]["meteor"], "Intensitat de pluja")
        self.assertEqual(a[0]["perill"], 3)
        self.assertEqual(a[0]["dies"], {"2026-10-10": [(12, 24)], "2026-10-11": [(0, 6)]})
        self.assertEqual(smp.de_la_comarca(EPISODIS, 99), [])

    def test_grau_com_el_mapa_de_meteocat(self):
        self.assertEqual([smp.nivell(p) for p in range(1, 7)], ["mig", "mig", "alt", "alt", "maxim", "maxim"])

    def test_textos(self):
        r = smp.llegeix(lambda url: pagina(EPISODIS), AHORA)
        l = r["linies"][0]
        self.assertEqual(l["nivell"], "alt")
        hora = smp.hora_local("2026-10-10T08:09Z")
        self.assertEqual(l["ca"], "Meteocat: avís de perill alt per «Intensitat de pluja» al Vallès Occidental, "
                                  "dissabte 10 de 12 a 24 h i diumenge 11 de 0 a 6 h "
                                  f"(Intensitat > 20 mm / 30 minuts; emès a les {hora}).")
        self.assertTrue(l["es"].startswith("Meteocat: aviso de peligro alto por «Intensitat de pluja» en el Vallès "
                                           "Occidental, sábado 10 de 12 a 24 h y domingo 11 de 0 a 6 h"))
        cap = smp.llegeix(lambda url: pagina([]), AHORA)["linies"]
        self.assertEqual(cap, [{"nivell": "nul",
                                "ca": "Meteocat no té cap avís de perill per al Vallès Occidental (dades de les 19:00).",
                                "es": "Meteocat no tiene ningún aviso de peligro para el Vallès Occidental "
                                      "(datos de las 19:00)."}])

    def test_al_costat_del_pla(self):
        s = smp.llegeix(lambda url: pagina(EPISODIS), AHORA)
        pla = {"pla": "INUNCAT", "nom": "d'inundacions", "fase": "alerta"}
        d = {"generat": AHORA.isoformat(), "plans": [pla], "smp": s}
        r = B.text_avisos_actius(d, "ca", AHORA)
        self.assertIn("🟠 Pla d'inundacions (INUNCAT) en fase d'alerta.\n🟠 Meteocat: avís de perill alt", r)
        # A l'avís del pla nou, també.
        t = AB.text_pla(pla, smp=s)
        self.assertIn("\n🟠 Meteocat: avís de perill alt per «Intensitat de pluja»", t["ca"])
        self.assertIn("\n🟠 Meteocat: aviso de peligro alto", t["es"])
        # Sense lectura de Meteocat, res.
        self.assertNotIn("Meteocat", AB.text_pla(pla)["ca"])
        self.assertNotIn("Meteocat", B.text_avisos_actius({**d, "smp": None}, "ca", AHORA))

    def test_sense_pla_surt_sol(self):
        # ADR 0071: sense pla, als avisos actius amb el nom de Meteocat; el
        # «no hi ha cap avís», no.
        s = smp.llegeix(lambda url: pagina(EPISODIS), AHORA)
        r = B.text_avisos_actius({"generat": AHORA.isoformat(), "plans": [], "smp": s}, "ca", AHORA)
        self.assertIn("<b>Meteocat</b>\n🟠 Meteocat: avís de perill alt", r)
        buit = smp.llegeix(lambda url: pagina([]), AHORA)
        self.assertNotIn("Meteocat", B.text_avisos_actius({"generat": AHORA.isoformat(), "smp": buit}, "ca", AHORA))

    def test_la_llista_agrupada_de_meteo_cat(self):
        # El 16-10-2026 la pàgina portava els episodis en dos blocs repetits
        # ([[…], […]]) i la lectura fallava: ara s'aplana i cada un va una vegada.
        self.assertEqual(smp.episodis(pagina([EPISODIS, EPISODIS])), EPISODIS)
        self.assertEqual(len(smp.de_la_comarca(smp.episodis(pagina([EPISODIS, EPISODIS])), 40)), 1)
        with self.assertRaises(ValueError):
            smp.episodis(pagina([["no és un episodi"]]))

    def test_avisos_d_observacio_i_temps_violent(self):
        # «Avís Vigilància» i «… per Temps Violent»: hora d'inici i de fi i les
        # comarques a l'avís mateix (script.min.js de meteo.cat).
        obs = [{"meteor": {"nom": "Intensitat de pluja"}, "avisos": [{
                    "tipus": "Avís Vigilància", "estat": "Vigent", "dataEmisio": "2026-10-17T13:10Z",
                    "dataInici": "2026-10-17T13:20Z", "dataFi": "2026-10-17T15:00Z",
                    "afectacions": [afectacio(40, 3), afectacio(41, 4)]}]},
               {"meteor": {"nom": "Temps violent"}, "avisos": [{
                    "tipus": "Avís Vigilància per Temps Violent", "estat": "Vigent", "dataEmisio": "2026-10-17T13:30Z",
                    "dataInici": "2026-10-17T13:30Z", "dataFi": "2026-10-17T14:30Z",
                    "afectacions": [afectacio(41, 5)]}]}]
        a = smp.de_la_comarca(obs, 40)
        self.assertEqual(len(a), 1)                                  # el de temps violent és d'una altra comarca
        self.assertEqual((a[0]["tipus"], a[0]["perill"]), ("observacio", 3))
        inici = dt.datetime.fromisoformat("2026-10-17T13:20+00:00").astimezone()
        self.assertEqual(a[0]["dies"], {inici.date().isoformat(): [(inici.hour, inici.hour + 2)]})
        self.assertTrue(smp.textos(a, "15:30")[0]["ca"].startswith(
            "Meteocat: avís d'observació de perill alt per «Intensitat de pluja» al Vallès Occidental"))
        self.assertEqual(smp.de_la_comarca(obs, 41)[1]["tipus"], "temps_violent")

    def test_la_pagina_real_del_16_d_octubre(self):
        # Retallada de la pàgina real: dos blocs repetits, cada avís amb la
        # versió «Ampliat» (l'anterior) i la «Vigent».
        def av(estat, emissio, perill):
            return {"tipus": "Avís", "estat": estat, "dataEmisio": emissio, "evolucions": [{
                "dia": "2026-10-17T00:00Z", "llindar1": "Intensitat > 20 mm / 30 minuts", "periodes": [
                    {"nom": "06-12", "afectacions": None},
                    {"nom": "12-18", "afectacions": [afectacio(40.0, perill, "2026-10-17T00:00Z")]},
                    {"nom": "18-00", "afectacions": [afectacio(40.0, perill, "2026-10-17T00:00Z")]}]}]}
        ep = {"id": None, "estat": {"nom": "Obert", "data": None},
              "meteor": {"idMeteor": None, "nom": "Intensitat de pluja en 30 minuts"},
              "avisos": [av("Ampliat", "2026-10-15T07:28Z", 2.0), av("Vigent", "2026-10-15T16:20Z", 3.0)]}
        a = smp.de_la_comarca(smp.episodis(pagina([[ep], [ep]])))
        self.assertEqual([(x["perill"], x["dies"]) for x in a], [(3, {"2026-10-17": [(12, 24)]})])

    def test_meteocat_avisa_per_fenomen(self):
        # ADR 0092: el primer, si puja de nivell, un fenomen nou i hores noves;
        # no una nova emissió igual, una baixada ni un avís menor del mateix fenomen.
        estat = {}

        def passa(avisos, minuts):
            s = {"avisos": avisos, "linies": []}
            return [a for a in AB.decideix(estat, {"smp": s}, AHORA + dt.timedelta(minutes=minuts))
                    if a["tipus"] == "perill"]

        def av(meteor, perill, dies, tipus="previsio"):
            return {"meteor": meteor, "tipus": tipus, "llindar": "Intensitat > 20 mm / 30 minuts",
                    "perill": perill, "emissio": "2026-10-16T16:20Z", "dies": dies}
        dissabte = {"2026-10-17": [(12, 24)]}
        p30 = av("Intensitat de pluja en 30 minuts", 3, dissabte)
        p3h = av("Intensitat de pluja en 3 hores", 2, dissabte)
        self.assertEqual(passa([], 0), [])                                   # la primera vegada, s'apunta
        nous = passa([p30, p3h], 6)
        self.assertEqual(len(nous), 1)                                       # els dos de pluja, un sol avís
        self.assertEqual(nous[0]["ca"].splitlines()[0],
                         "🟠 <b>Meteocat: avís de perill alt per pluja al Vallès Occidental</b>")
        self.assertIn("\n🟠 Perill alt per «Intensitat de pluja en 30 minuts»: dissabte 17 de 12 a 24 h "
                      "(Intensitat > 20 mm / 30 minuts).", nous[0]["ca"])
        self.assertIn("\n🟡 Perill moderat per «Intensitat de pluja en 3 hores»", nous[0]["ca"])
        self.assertEqual(nous[0]["nivell"], "alt")
        episodi = nous[0]["episodi"]
        self.assertEqual(passa([dict(p30, emissio="2026-10-17T07:00Z"), p3h], 12), [])   # nova emissió igual
        self.assertEqual(passa([dict(p30, perill=4), p3h], 18), [])           # 4 és «alt», com el 3
        self.assertEqual(passa([dict(p30, perill=2), p3h], 24), [])           # baixa: res
        puja = passa([dict(p30, perill=5), p3h], 30)
        self.assertEqual(puja[0]["ca"].splitlines()[0],
                         "🔴 <b>Meteocat: actualització, puja a perill molt alt per pluja al Vallès Occidental</b>")
        self.assertEqual(puja[0]["episodi"], episodi)                         # la mateixa fitxa a «Perill»
        amplia = passa([dict(p30, perill=5, dies={**dissabte, "2026-10-18": [(0, 6)]})], 36)
        self.assertIn("Meteocat: actualització, amplia l'avís de perill molt alt per pluja", amplia[0]["ca"])
        vent = passa([dict(p30, perill=5, dies={**dissabte, "2026-10-18": [(0, 6)]}),
                      av("Ratxa màxima de vent", 1, dissabte)], 42)
        self.assertIn("Meteocat: actualització, avisa també de perill moderat per vent", vent[0]["ca"])
        self.assertEqual(vent[0]["nivell"], "maxim")                          # el color, el pitjor dels vigents
        obs = passa([dict(p30, perill=5, dies={**dissabte, "2026-10-18": [(0, 6)]}), av("Ratxa màxima de vent", 1, dissabte),
                     av("Intensitat de pluja", 3, {"2026-10-17": [(15, 17)]}, "observacio")], 48)
        self.assertIn("Meteocat: s'observa perill alt per pluja al Vallès Occidental", obs[0]["ca"])
        self.assertIn("Observat ara, perill alt per «Intensitat de pluja»", obs[0]["ca"])
        # Si no hi ha lectura, res; quan ja no en queda cap (passada la mitja hora), el final.
        self.assertEqual(AB.decideix(estat, {"smp": None}, AHORA + dt.timedelta(minutes=54)), [])
        self.assertEqual(passa([], 60), [])
        fi = passa([], 90)
        self.assertEqual(fi[0]["ca"], "🟢 <b>Meteocat: ja no hi ha cap avís de perill per al Vallès Occidental</b>")
        self.assertEqual((fi[0]["nivell"], fi[0]["episodi"]), ("fi", episodi))
        self.assertEqual(passa([], 96), [])
        # Un de nou després, un episodi nou.
        torna = passa([p3h], 102)
        self.assertTrue(torna[0]["ca"].startswith("🟡 <b>Meteocat: avís de perill moderat per pluja"))
        self.assertNotEqual(torna[0]["episodi"], episodi)

    def test_l_estat_d_abans_avisa_el_que_hi_ha(self):
        # Fins a la 3.86.3 l'estat era {clau: grau} i, com que la lectura fallava,
        # buit: el que hi ha ara s'avisa una vegada.
        estat = {"oficials": {"aemet": {}, "plans": {}, "smp": {}}}
        s = smp.llegeix(lambda url: pagina(EPISODIS), AHORA)
        self.assertEqual(len(AB.decideix(estat, {"smp": s}, AHORA)), 1)
        self.assertEqual(AB.decideix(estat, {"smp": s}, AHORA + dt.timedelta(minutes=6)), [])

    def test_l_aemet_per_al_que_meteocat_no_cobreix(self):
        # ADR 0093: per fenomen i hores, mana Meteocat; l'AEMET avisa del que
        # Meteocat no cobreix (Juanjo, 16-10-2026: «si meteocat no tiene aviso
        # y aemet sí, debe salir aemet»). Les tempestes, sempre de l'AEMET.
        pluja = {"zona": "Prelitoral de Barcelona", "tipo": "pluja", "nivel": "groc",
                 "inicio": "2026-10-17T12:00:00+02:00", "fin": "2026-10-17T23:59:59+02:00"}
        tempestes = dict(pluja, tipo="tempestes")
        mc = {"meteor": "Intensitat de pluja en 30 minuts", "tipus": "previsio", "llindar": None, "perill": 3,
              "emissio": "2026-10-16T16:20Z", "dies": {"2026-10-17": [(12, 24)]}}
        amb = {"avisos": [mc], "linies": []}
        self.assertTrue(smp.cobreix([mc], pluja))
        self.assertFalse(smp.cobreix([mc], tempestes))
        self.assertFalse(smp.cobreix([mc], dict(pluja, inicio="2026-10-18T12:00:00+02:00",
                                                 fin="2026-10-18T23:59:59+02:00")))      # un altre dia
        self.assertFalse(smp.cobreix([dict(mc, meteor="Ratxa màxima de vent")], pluja))   # un altre fenomen
        estat = {}

        def perill(sal, m):
            sal = {**sal, "avisos": [dict(a) for a in sal["avisos"]]}
            smp.marca_coberts(sal["avisos"], sal["smp"])
            return [a for a in AB.decideix(estat, sal, AHORA + dt.timedelta(minutes=m)) if a["tipus"] == "perill"]
        self.assertEqual(perill({"avisos": [], "smp": amb}, 0), [])                     # s'apunta
        nous = perill({"avisos": [pluja, tempestes], "smp": amb}, 6)
        self.assertEqual([a["id"].split(":")[2] for a in nous], ["tempestes"])          # la pluja la cobreix Meteocat
        self.assertEqual(estat["aemet_coberts"], ["aemet:pluja:2026-10-17T12:00:00+02:00"])
        # Si Meteocat la deixa de cobrir (o no es pot llegir), surt la de l'AEMET.
        nous = perill({"avisos": [pluja, tempestes], "smp": None}, 12)
        self.assertEqual([a["id"].split(":")[2] for a in nous], ["pluja"])
        self.assertEqual(perill({"avisos": [pluja, tempestes], "smp": None}, 18), [])

    def test_la_fitxa_de_l_aemet_es_tanca_si_la_cobreix_meteocat(self):
        estat = {"aemet_coberts": ["aemet:pluja:x"]}
        h = AB.historial(estat, [{"id": "perill:aemet:pluja:x:groc", "tipus": "perill", "nivell": "groc",
                                  "hora": AHORA.isoformat(timespec="minutes"), "ca": "a", "es": "a",
                                  "episodi": "aemet:pluja:x"}], AHORA)
        self.assertEqual(h[0]["fi_ca"], "Meteocat en té avís per al Vallès Occidental: ara es mostra el seu.")
        # Amb la fitxa de Meteocat que la substitueix, perquè «Perill» no la doni per acabada.
        mc = {"id": "perill:meteocat:x", "tipus": "perill", "nivell": "alt", "hora": AHORA.isoformat(timespec="minutes"),
              "ca": "b", "es": "b", "episodi": "meteocat:x"}
        estat["oficials"] = {"smp": {"episodi": "meteocat:x"}}
        h = AB.historial(estat, [mc], AHORA)
        self.assertEqual(h[0]["substituit_per"], {"clau": "meteocat:x", "inici": AHORA.isoformat(timespec="minutes")})

    def test_avis_a_juanjo_en_el_moment(self):
        # Si la passada no ha pogut llegir Meteocat, una vegada; i quan torna.
        from unittest import mock
        with tempfile.TemporaryDirectory() as dir:
            casa, sortida = os.path.join(dir, "casa.json"), os.path.join(dir, "avisos.json")
            marca = os.path.join(dir, "aprenentatge", "smp-falla")

            def passa(salida):
                with open(casa, "w", encoding="utf-8") as f:
                    json.dump(salida, f)
                with mock.patch.object(AB, "ESTAT", os.path.join(dir, "estat.json")), \
                        mock.patch.object(AB, "MARCA_SMP", marca), \
                        mock.patch("avis_privat.envia") as envia:
                    AB.actualitza(casa, sortida, ahora=AHORA)
                return [c.args[0] for c in envia.call_args_list]
            falla = passa({"smp": None, "errors": ["smp: 'list' object has no attribute 'get'"]})
            self.assertEqual(len(falla), 1)
            self.assertIn("no es poden llegir els avisos de perill de Meteocat ('list' object", falla[0])
            self.assertIn("els veïns reben els avisos de l'AEMET", falla[0])
            self.assertEqual(passa({"smp": None, "errors": []}), [])
            self.assertEqual(passa({"smp": {"avisos": [], "linies": []}}),
                             ["Temps a Montflorit: els avisos de perill de Meteocat es tornen a llegir."])
            self.assertEqual(passa({"smp": {"avisos": [], "linies": []}}), [])
            self.assertEqual(passa({}), [])                                    # sense la clau, res

    def test_prova_diaria(self):
        with tempfile.TemporaryDirectory() as dir:
            marca = os.path.join(dir, "smp-falla")
            self.assertIsNotNone(smp.comprova(lambda url: "<html></html>", marca, avisa=False))
            self.assertTrue(os.path.exists(marca))
            self.assertIsNone(smp.comprova(lambda url: pagina([]), marca, avisa=False))
            self.assertFalse(os.path.exists(marca))
            # Una forma que no se sap llegir també és una fallada (el 16-10-2026
            # la prova diària només mirava que hi hagués la llista).
            self.assertIsNotNone(smp.comprova(lambda url: pagina([[{"avisos": [{"estat": "Vigent", "evolucions": [
                {"periodes": [{"nom": "x", "afectacions": [afectacio(40, 3)]}]}]}]}]]), marca, avisa=False))


if __name__ == "__main__":
    unittest.main()
