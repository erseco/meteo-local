# SPDX-License-Identifier: AGPL-3.0-or-later
"""La regla común de mejora (remostreig, ADR 0105)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import remostreig as R  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
