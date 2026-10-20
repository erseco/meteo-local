# SPDX-License-Identifier: AGPL-3.0-or-later
"""La regla común de mejora (remostreig, ADR 0105)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import remostreig as R  # noqa: E402


class Avanc(unittest.TestCase):
    def test_entrena_amb_els_dies_anteriors(self):
        dies = [f"2026-10-{d:02d}" for d in range(1, 11) for _ in range(3)]
        passos = list(R.avanc(dies))
        # Els set primers dies només entrenen; s'avaluen el 8, el 9 i el 10.
        self.assertEqual(len(passos), 3)
        ent, aval = passos[0]
        self.assertEqual(sorted(set(np.array(dies)[aval])), ["2026-10-08"])
        self.assertEqual(sorted(set(np.array(dies)[ent])), [f"2026-10-{d:02d}" for d in range(1, 8)])
        # Mai res posterior al dia avaluat.
        for ent, aval in passos:
            self.assertLess(max(np.array(dies)[ent]), min(np.array(dies)[aval]))
        self.assertEqual(list(R.avanc(dies[:9])), [])

    def test_un_episodi_que_creua_la_mitjanit_no_entrena_el_dia_que_l_avalua(self):
        moments = [f"2026-10-{d:02d}T{h:02d}:00" for d in range(1, 10) for h in (6, 12, 18, 23)] + ["2026-10-09T00:00"]
        moments.sort()
        plou = [m in ("2026-10-08T23:00", "2026-10-09T00:00", "2026-10-03T12:00") for m in moments]
        ep = R.episodis(moments, plou)
        self.assertEqual(sorted(set(ep)), [0, 1, 2])
        self.assertEqual(ep[moments.index("2026-10-08T23:00")], ep[moments.index("2026-10-09T00:00")])
        self.assertNotEqual(ep[moments.index("2026-10-03T12:00")], ep[moments.index("2026-10-09T00:00")])
        dies = [m[:10] for m in moments]
        ent, aval = [p for p in R.avanc(dies, ep) if "2026-10-09" in set(np.array(dies)[p[1]])][0]
        # L'hora de les 23 del dia 8, del mateix episodi, queda fora de l'entrenament del dia 9.
        self.assertFalse(ent[moments.index("2026-10-08T23:00")])
        self.assertTrue(ent[moments.index("2026-10-08T18:00")])
        self.assertTrue(ent[moments.index("2026-10-03T12:00")])


class Seguretat(unittest.TestCase):
    def test_guanya_sempre_i_mai(self):
        dies = [f"2026-10-{d:02d}" for d in range(1, 11) for _ in range(24)]
        self.assertEqual(R.seguretat([1.0] * 240, [2.0] * 240, dies), 1.0)
        self.assertEqual(R.seguretat([2.0] * 240, [1.0] * 240, dies), 0.0)
        self.assertTrue(R.guanya(1.0))
        self.assertFalse(R.guanya(0.949))
        self.assertFalse(R.guanya(None))

    def test_un_sol_dia_bo_no_es_segur(self):
        # Gana mucho un día y pierde poco los demás: la media dice que gana,
        # pero no es seguro, porque depende de un solo día.
        rng = np.random.default_rng(1)
        dies = [f"2026-10-{d:02d}" for d in range(1, 11) for _ in range(24)]
        actual = np.full(240, 1.0)
        nou = np.full(240, 1.05)
        nou[:24] = 0.1
        self.assertLess(np.mean(nou), np.mean(actual))
        self.assertLess(R.seguretat(nou, actual, dies), 0.95)
        # Hora a hora sí ganaría casi siempre: por eso los bloques son días.
        self.assertGreater(R.seguretat(nou, actual, list(range(240))), 0.95)
        # Un gana constante en todos los días, aunque pequeño, es seguro.
        nou2 = actual - 0.01 + rng.normal(0, 0.001, 240)
        self.assertGreaterEqual(R.seguretat(nou2, actual, dies), 0.95)

    def test_sense_dos_blocs_no_hi_ha_seguretat(self):
        self.assertIsNone(R.seguretat([1.0, 2.0], [2.0, 3.0], ["a", "a"]))
        self.assertIsNone(R.seguretat([1.0], [2.0, 3.0], ["a", "b"]))


    def test_periodes_amb_casos_diferents(self):
        # ADR 0110: ara (1 °C de mitjana per hora) contra abans (2 °C), amb
        # dies de casos diferents; amb soroll, el que es compara és la mitjana per cas.
        rng = np.random.default_rng(3)
        abans_n = rng.integers(10, 24, 28)
        ara_n = rng.integers(10, 24, 28)
        abans = abans_n * (2.0 + rng.normal(0, 0.3, 28))
        ara = ara_n * (1.0 + rng.normal(0, 0.3, 28))
        self.assertGreaterEqual(R.seguretat_periodes(abans, abans_n, ara, ara_n), 0.95)
        self.assertLessEqual(R.seguretat_periodes(ara, ara_n, abans, abans_n), 0.05)
        # Iguals, a l'atzar: ni una cosa ni l'altra.
        s = R.seguretat_periodes(abans, abans_n, abans[::-1], abans_n[::-1])
        self.assertTrue(0.05 < s < 0.95)
        self.assertIsNone(R.seguretat_periodes([1.0], [3], [1.0, 2.0], [3, 3]))


if __name__ == "__main__":
    unittest.main()
