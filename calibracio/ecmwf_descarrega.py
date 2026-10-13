#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descarga las previsiones archivadas de ECMWF IFS en casa, para probar si
mejoran la probabilidad de lluvia (calibracio/ecmwf_prova.py).

Como descarrega.py: la Previous Runs API de Open-Meteo, «day0» (primeras horas
de cada pasada, unidas) y «day1» (la previsión hecha un día antes). Dos
versiones de ECMWF: la de 9 km (ecmwf_ifs) y la de 0,25° (ecmwf_ifs025), para
saber de cuál salen los datos de antes de que la de 9 km fuera abierta.

Los datos van a calibracio/dades/ecmwf/, que no se sube al repositorio.
Uso: python3 calibracio/ecmwf_descarrega.py [inicio] [fin]
"""
import csv
import datetime as dt
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
from calibracio.descarrega import PREVIAS, get_json  # noqa: E402

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dades", "ecmwf")
MODELOS = ["ecmwf_ifs", "ecmwf_ifs025"]
VARIABLES = ["precipitation", "precipitation_previous_day1"]


def previsiones(inicio, fin):
    lat, lon = C.CASA
    tramos = []
    a, final = dt.date.fromisoformat(inicio), dt.date.fromisoformat(fin)
    while a < final:
        b = min(a + dt.timedelta(days=180), final - dt.timedelta(days=1))
        q = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon, "hourly": ",".join(VARIABLES),
            "models": ",".join(MODELOS), "timezone": "UTC",
            "start_date": a.isoformat(), "end_date": b.isoformat()})
        tramos.append(get_json(f"{PREVIAS}?{q}")["hourly"])
        a = b + dt.timedelta(days=1)
    claves = [k for k in tramos[0] if k != "time"]
    ruta = os.path.join(DIR, "prev_casa_ecmwf.csv")
    with open(ruta, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hora_utc"] + claves)
        for t in tramos:
            for i, hora in enumerate(t["time"]):
                w.writerow([hora] + [t[k][i] for k in claves])
    print(f"{sum(len(t['time']) for t in tramos)} horas -> {ruta}")


if __name__ == "__main__":
    args = sys.argv[1:]
    os.makedirs(DIR, exist_ok=True)
    previsiones(args[0] if args else "2024-01-01", args[1] if len(args) > 1 else dt.date.today().isoformat())
