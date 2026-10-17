# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pruebas de la imagen de la gráfica (grafica_imatge.py, ADR 0098), sin Chromium."""
import os
import sys
import unittest

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ARREL)
import grafica_imatge as G  # noqa: E402


class Credits(unittest.TestCase):
    def test_que_es_de_quan_i_que_mana_l_oficial(self):
        ca, avis = G.credits({"generat": "2026-10-17T07:21+02:00"}, "ca")
        self.assertEqual(ca, "Temps a Montflorit (Cerdanyola del Vallès) · previsió de dissabte 17 d’octubre, 07:21"
                             " · meteo-montflorit.github.io")
        self.assertIn("mana el seu", avis)
        self.assertIn("previsión del lunes 2 de noviembre, 07:00", G.credits({"generat": "2026-11-02T07:00+01:00"}, "es")[0])
        self.assertIn("de novembre", G.credits({"generat": "2026-11-02T07:00+01:00"}, "ca")[0])

    def test_la_pagina_porta_els_credits_i_les_icones(self):
        p = G.pagina({"generat": "2026-10-17T07:21+02:00", "hores": []}, "avui", "ca")
        self.assertIn("meteo-montflorit.github.io", p)
        self.assertIn('<symbol id="i-cloud"', p)
        # Sense el botó de la càmera, que a la imatge no fa res.
        self.assertIn("fig._botoImatge = false", p)
