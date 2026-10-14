#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""La diferencia de partida entre la parte alta del barrio y la estación de
casa, junto a la riera, hora a hora (ADR 0087).

Con el historial de la estación de casa cada 5 minutos (dades/casa_5min.csv)
y el de las vecinas de Weather Underground (dades/veines/), en las horas en
punto en que hay al menos dos vecinas de arriba (config.VEINES, «alta»): la
mediana de (parte alta − casa) de cada hora del día, en tiempo universal
(part_alta.hora_solar). Fuera las horas con sol
directo sobre el termómetro de casa: de 7 a 11 h, cuando casa está 1,5 °C o
más por encima de la mediana de todas las vecinas (el criterio de
sol_estacio, ADR 0081, que en verano no se apuntaba). part_alta.py la usa
mientras el registro no tenga bastantes horas.

Uso: python3 calibracio/part_alta.py
"""
import csv
import datetime as dt
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
import part_alta as PA  # noqa: E402

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dades")


def main():
    casa = {}
    with open(os.path.join(DIR, "casa_5min.csv")) as f:
        for r in csv.DictReader(f):
            t = dt.datetime.fromisoformat(r["t"])
            if t.minute == 0 and r["temperatura"] not in ("", "None"):
                casa[t] = float(r["temperatura"])
    veines = {}
    for ruta in glob.glob(os.path.join(DIR, "veines", "*.json")):
        est = os.path.basename(ruta).split("-")[0]
        with open(ruta) as f:
            for o in json.load(f):
                t = dt.datetime.fromisoformat(o["obsTimeUtc"].replace("Z", "+00:00")).astimezone(
                    dt.timezone(dt.timedelta(hours=2))).replace(second=0, microsecond=0)
                t = t - dt.timedelta(minutes=t.minute % 10)
                v = (o.get("metric") or {}).get("tempAvg")
                if v is not None and t.minute == 0:
                    veines.setdefault(est, {})[t] = v
    mostres, sol = {}, 0
    for t, c in casa.items():
        alta = PA.mediana_alta([veines.get(e, {}).get(t) for e in PA.ALTES])
        totes = [veines[e][t] for e in C.VEINES if t in veines.get(e, {})]
        if alta is None:
            continue
        if 7 <= t.hour <= 11 and len(totes) >= 2 and c - statistics.median(totes) >= 1.5:
            sol += 1
            continue
        mostres.setdefault(PA.hora_solar(t), []).append(alta - c)
    t0 = min(casa).date().isoformat()
    res = {"des_de": max(t0, "2026-07-27"), "fins": max(casa).date().isoformat(),
           "hores_sol_fora": sol,
           "per_hora_utc": {h: round(statistics.median(d), 1) for h, d in sorted(mostres.items())},
           "mostres": {h: len(d) for h, d in sorted(mostres.items())}}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "part_alta.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(res["per_hora_utc"], "sol fora:", sol)


if __name__ == "__main__":
    main()
