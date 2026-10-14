#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""¿Acierta más el modelo aprendido (ADR 0012) con la hora solar (tiempo
universal) que con la del reloj? (ADR 0089, 14-10-2026)

Con los datos de los dos primeros modelos (un año de la estación de casa,
estacio_casa.py, y el archivo de lluvia de 2024-2026, pluja_casa.py): las
mismas muestras y los mismos grupos de semanas no vistas; solo cambia la hora
de hora_sin y hora_cos. La diferencia de error, emparejada, con su intervalo
de confianza del 95 % por bootstrap de días (cada día, un bloque). Necesita
los datos de calibracio/dades/.

Uso: python3 calibracio/hora_solar.py
"""
import datetime as dt
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aprenentatge as A  # noqa: E402
from calibracio import estacio_casa as EC, pluja_casa as PC  # noqa: E402

UTC = dt.timezone.utc
rng = np.random.default_rng(1)

def hora_utc(fins):
    t = dt.datetime.fromisoformat(fins)
    if t.tzinfo is None:
        t = t.replace(tzinfo=EC.LOCAL)
    return t.astimezone(UTC).hour

def amb_utc(x, noms, fins):
    x = list(x); h = 2 * math.pi * hora_utc(fins) / 24
    x[noms.index("hora_sin")] = math.sin(h); x[noms.index("hora_cos")] = math.cos(h)
    return x

def boot(dif, dies, n=5000):
    u = sorted(set(dies)); idx = {d: i for i, d in enumerate(u)}
    di = np.array([idx[d] for d in dies])
    s = np.bincount(di, weights=dif, minlength=len(u)); c = np.bincount(di, minlength=len(u))
    mos = rng.integers(0, len(u), (n, len(u)))
    m = s[mos].sum(1) / c[mos].sum(1)
    return float(dif.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), len(u)

def cv_ridge(x, y, g):
    p = np.zeros(len(y))
    for k in set(g):
        e = g != k; p[~e] = x[~e] @ A.ajustar_ridge(x[e], y[e])
    return p

def cv_logit(x, y, g):
    p = np.zeros(len(y))
    for k in set(g):
        e = g != k; p[~e] = A.predecir(A.ajustar(x[e], y[e]), x[~e])
    return p


def main():
    res = {}
    # Temperatura (temperatura_casa.json: un año de la estación de casa)
    _, lect = EC.estacion()
    with open(EC.PREV_TEMP, encoding="utf-8") as f:
        prev = json.load(f)
    ms = EC.muestras_temperatura(lect, prev)
    for noms, nom in ((A.RASGOS_TEMPERATURA, "temperatura"), (A.RASGOS_TEMPERATURA_SENSE_ESTACIO, "temperatura_sense_estacio")):
        sel = [m for m in ms if A.rasgos(m, noms) is not None]
        xl = np.array([A.rasgos(m, noms) for m in sel])
        xu = np.array([amb_utc(A.rasgos(m, noms), noms, m["fins"]) for m in sel])
        err = np.array([m["temperature_2m"] - m["obs"] for m in sel])
        g = np.array([EC.grupo(m["t"]) for m in sel])
        dies = [m["fins"][:10] for m in sel]
        el = np.abs(err - cv_ridge(xl, err, g)); eu = np.abs(err - cv_ridge(xu, err, g))
        d, lo, hi, nd = boot(eu - el, dies)
        # Solo en los meses de horario de invierno, donde las dos difieren de verdad
        hiv = np.array([dt.datetime.fromisoformat(m["fins"]).replace(tzinfo=EC.LOCAL).utcoffset() == dt.timedelta(hours=1) for m in sel])
        dh = boot((eu - el)[hiv], [x for x, b in zip(dies, hiv) if b])
        res[nom] = {"mostres": len(sel), "dies": nd, "error_rellotge": round(float(el.mean()), 4),
                    "error_solar": round(float(eu.mean()), 4), "dif": [round(v, 4) for v in (d, lo, hi)],
                    "dif_hivern": [round(v, 4) for v in dh[:3]], "dies_hivern": dh[3]}
    # Lluvia (pluja_casa.json: 2024-2026, Sabadell y Sant Cugat)
    mp = PC.muestras()
    noms = A.RASGOS_ARXIU
    xl = np.array([m[2] for m in mp])
    xu = np.array([amb_utc(m[2], noms, m[0].astimezone(EC.LOCAL).strftime("%Y-%m-%dT%H:%M")) for m in mp])
    y = np.array([m[3] for m in mp])
    g = np.array([EC.grupo(m[0]) for m in mp])
    dies = [m[0].astimezone(EC.LOCAL).date().isoformat() for m in mp]
    bl = (cv_logit(xl, y, g) - y) ** 2; bu = (cv_logit(xu, y, g) - y) ** 2
    d, lo, hi, nd = boot(bu - bl, dies)
    res["pluja"] = {"mostres": len(y), "dies": nd, "brier_rellotge": round(float(bl.mean()), 5),
                    "brier_solar": round(float(bu.mean()), 5), "dif": [round(v, 6) for v in (d, lo, hi)],
                    "dif_relativa_%": round(100 * d / bl.mean(), 2)}
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
