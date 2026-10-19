#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Una sola regla per decidir si un mètode nou substitueix el que hi ha (ADR
0105): el nou guanya si s'equivoca menys en almenys SEGURETAT dels
REMOSTREJOS remostrejos per blocs (bootstrap), no per un marge fix del 5 %.

Els blocs són dies o episodis, perquè les hores d'un mateix dia o d'un
mateix episodi de pluja s'assemblen i no són casos independents: remostrejar
hora a hora faria creure que hi ha més dades de les que hi ha. La fan servir
la probabilitat de pluja i la temperatura (aprenentatge.py), el radar
(radar_fonts.py), el final de la pluja (fi_pluja.py), l'aire (aire.py), el
cel (nuvols.py) i la variant de l'arxiu amb avisos
(calibracio/pluja_casa_avisos.py). Juanjo, 14-10-2026: «para ser coherentes y
evitar problemas en el futuro no habría que hacerlo todo…?».
"""
import numpy as np

REMOSTREJOS = 2000       # remostrejos per blocs
SEGURETAT = 0.95         # proporció de remostrejos en què el nou ha de guanyar


def seguretat(errors_nou, errors_actual, blocs, llavor=0):
    """Proporció de remostrejos per blocs (amb reposició) en què la suma
    d'errors del nou és menor que la de l'actual, amb els mateixos casos.
    errors_*: l'error de cada cas (quadràtic, absolut, minuts…); blocs: el
    dia o l'episodi de cada cas. None amb menys de dos blocs."""
    e_nou, e_actual = np.asarray(errors_nou, dtype=float), np.asarray(errors_actual, dtype=float)
    unics, idx = np.unique(np.asarray(blocs), return_inverse=True)
    if len(unics) < 2 or len(e_nou) != len(e_actual) or len(e_nou) != len(idx):
        return None
    per_bloc_nou = np.bincount(idx, e_nou, len(unics))
    per_bloc_actual = np.bincount(idx, e_actual, len(unics))
    tria = np.random.default_rng(llavor).integers(0, len(unics), (REMOSTREJOS, len(unics)))
    return round(float(np.mean(per_bloc_nou[tria].sum(axis=1) < per_bloc_actual[tria].sum(axis=1))), 3)


def guanya(s):
    """Si amb aquesta seguretat el nou substitueix l'actual."""
    return s is not None and s >= SEGURETAT
