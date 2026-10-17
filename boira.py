#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""¿Acierta ICON la niebla en Montflorit? Vigilancia de un mes antes de usarlo
(ADR 0100; Juanjo, 17-10-2026: «investiga por qué ahora hay niebla y la
predicción del tiempo no dice nada»).

El tipo de tiempo de cada hora sale de AROME, que en Open-Meteo no da
visibilidad ni niebla. El 17-10-2026, con niebla cerrada en Sabadell desde las
6:30, ICON daba el código de niebla de 4 a 9 h (visibilidad de 720 m a las
9); ECMWF y GFS, no. Antes de usar ICON se mide:

- `apunta` (cada hora, desde reloj.sh): lo que dice ICON para las próximas
  12 horas (código y visibilidad), en registre/boira-icon.csv.
- `resum`: para cada hora observada, lo que decía ICON con 1 a 6 horas de
  antelación contra dos cosas: la niebla de Sabadell (METAR de
  nuvols-sabadell.csv) con la estación de casa saturada (C.HUMITAT_BOIRA),
  como en la hora en curso de la web; y la estación de casa saturada y sin
  lluvia, que es lo que se tiene de la niebla de la riera, que muchas veces
  no llega a Sabadell (Juanjo, 17-10-2026) y que nada mide en el barrio.
  Aciertos, fallos y falsas alarmas.

  python3 boira.py apunta | resum
"""
import csv
import datetime as dt
import json
import os
import sys

import config as C
import nuvols as NV
import prevision as P

REGISTRE = os.environ.get("REGISTRE_DIR", "/estat/registre")
FITXER = os.path.join(REGISTRE, "boira-icon.csv")
CAMPS = ["emes", "fins", "antelacio_h", "codi", "visibilitat"]
HORES = 12
CADA_MIN = 50
URL = ("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
       "&hourly=weather_code,visibility&models=icon_seamless&timezone=Europe%2FMadrid&forecast_hours=13")
CODIS_BOIRA = (45, 48)


def apunta(ara=None, get=None):
    """Lo que dice ICON para las próximas horas; una vez por hora como mucho."""
    ara = ara or dt.datetime.now(P.ZONA)
    if os.path.exists(FITXER):
        with open(FITXER, encoding="utf-8") as f:
            ultima = list(csv.DictReader(f))[-1:] or [None]
        if ultima[0] and ara - dt.datetime.fromisoformat(ultima[0]["emes"]) < dt.timedelta(minutes=CADA_MIN):
            return 0
    lat, lon = C.CASA
    h = json.loads((get or P.get)(URL.format(lat=lat, lon=lon)))["hourly"]
    files = []
    for t, codi, vis in zip(h["time"], h["weather_code"], h["visibility"]):
        fins = dt.datetime.fromisoformat(t).replace(tzinfo=P.ZONA)
        antelacio = (fins - ara).total_seconds() / 3600
        if 0 < antelacio <= HORES:
            files.append({"emes": ara.isoformat(timespec="minutes"), "fins": P.clau_hora(fins),
                          "antelacio_h": round(antelacio, 2), "codi": codi, "visibilitat": vis})
    nou = not os.path.exists(FITXER)
    with open(FITXER, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, CAMPS)
        if nou:
            w.writeheader()
        w.writerows(files)
    return len(files)


def observada(metars, humitat):
    """Niebla en Montflorit: el METAR de Sabadell la ve y casa está saturada."""
    return NV.te_boira(metars) and humitat is not None and humitat >= C.HUMITAT_BOIRA


def resum():
    def llegeix(nom):
        ruta = os.path.join(REGISTRE, nom)
        return list(csv.DictReader(open(ruta, encoding="utf-8"))) if os.path.exists(ruta) else []
    obs = {r["fins"]: r["metars"] for r in llegeix("nuvols-sabadell.csv")}
    casa = {r["fins"]: r for r in llegeix("estacio-casa.csv")}
    # Para cada hora, la previsión de ICON más reciente con 1 a 6 h de antelación.
    prev = {}
    for r in llegeix("boira-icon.csv"):
        if 1 <= float(r["antelacio_h"]) <= 6:
            prev[r["fins"]] = r
    def saturada(r):
        try:
            return (float(r["humitat"]) >= 98 and float(r["temperatura"]) - float(r["rosada"]) <= 0.5
                    and float(r["pluja_mm"] or 0) < C.UMBRAL_MM)
        except (TypeError, ValueError, KeyError):
            return None
    res = {}
    for nom, que in (("Boira a Sabadell i casa saturada", lambda f: f in obs and observada(
                          obs[f], float(casa[f]["humitat"]) if casa[f].get("humitat") else None)),
                     ("Casa saturada i sense pluja (la riera)", lambda f: saturada(casa[f]))):
        taula = {"encert": 0, "fallada": 0, "falsa_alarma": 0, "sense_boira": 0}
        for fins, p in prev.items():
            if fins not in casa or (nom.startswith("Boira") and fins not in obs):
                continue
            hi_ha = que(fins)
            if hi_ha is None:
                continue
            diu = int(float(p["codi"])) in CODIS_BOIRA
            taula[("encert" if diu else "fallada") if hi_ha else ("falsa_alarma" if diu else "sense_boira")] += 1
        pod = taula["encert"] / max(1, taula["encert"] + taula["fallada"])
        far = taula["falsa_alarma"] / max(1, taula["encert"] + taula["falsa_alarma"])
        print(f"{nom}: {sum(taula.values())} hores, {taula['encert'] + taula['fallada']} amb boira. "
              f"ICON l'encerta {taula['encert']}, no la veu {taula['fallada']}, en diu de més {taula['falsa_alarma']}. "
              f"Detecció {pod:.0%}, falses alarmes {far:.0%}.")
        res[nom] = taula
    return res


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("apunta", "resum"):
        sys.exit(__doc__)
    if sys.argv[1] == "apunta":
        apunta()
    else:
        resum()
