#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""¿Mejora ECMWF IFS (9 km) la probabilidad de lluvia de casa?

La misma prueba que pluja_casa.py (ADR 0021): regresión logística con las
previsiones archivadas en casa y la lluvia medida en Sabadell y Sant Cugat,
cada estación una muestra, validación cruzada por grupos de semanas. Se
comparan, sobre las mismas muestras:

- «base»: los rasgos del modelo del archivo (aprenentatge.RASGOS_ARXIU);
- «+ ECMWF»: los mismos y los de ECMWF como un modelo más (ln(1 + mm), si da
  lluvia, su relación con la antelación, si la dan los cuatro y si solo la da
  ECMWF).

A corto plazo («day0») hay ECMWF de 9 km en todo el archivo; con un día de
antelación («day1»), solo desde octubre de 2025. Se mira también el subgrupo
en que AROME (cualquiera de los dos) e ICON-EU no coinciden, y la lluvia de
Montflorit medida por la estación de casa (casa_30min.csv, de octubre de 2025
a julio de 2026, cuando su pluviómetro era fiable).

Necesita descarrega.py y ecmwf_descarrega.py. Escribe dades/ecmwf/prova.json.
Uso: python3 calibracio/ecmwf_prova.py
"""
import csv
import datetime as dt
import json
import math
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aprenentatge as A  # noqa: E402
import config as C  # noqa: E402
from calibracio.analitza import leer_obs, leer_prev  # noqa: E402
from calibracio.pluja_casa import creuada  # noqa: E402

LOCAL = ZoneInfo("Europe/Madrid")
UTC = dt.timezone.utc
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dades")
SALIDA = os.path.join(DIR, "ecmwf", "prova.json")


def leer_ecmwf():
    res = {}
    with open(os.path.join(DIR, "ecmwf", "prev_casa_ecmwf.csv")) as f:
        for fila in csv.DictReader(f):
            t = dt.datetime.fromisoformat(fila["hora_utc"]).replace(tzinfo=UTC)
            res[t] = {k: (float(v) if v not in ("", "None") else None) for k, v in fila.items() if k != "hora_utc"}
    return res


def rasgos_ecmwf(mm, antelacio_h, d):
    """Los rasgos de ECMWF, como los de los otros modelos (aprenentatge.rasgos)."""
    ant = min(max(antelacio_h, 0) / 24, 1.0)
    plou = float(mm >= A.MM_MODEL_PLOU - 1e-9)
    altres = [d[f"pluja_{m}"] >= A.MM_MODEL_PLOU - 1e-9 for m in C.MODELOS_FINOS]
    return [math.log1p(max(mm, 0)), plou, math.log1p(max(mm, 0)) * ant,
            float(plou and all(altres)), float(plou and not any(altres))]


def desacord(d):
    """AROME (alguno de los dos) e ICON-EU no coinciden en si llueve."""
    arome = any(d[f"pluja_{m}"] >= A.MM_MODEL_PLOU - 1e-9 for m in C.MODELOS_FINOS[:2])
    icon = d["pluja_icon_eu"] >= A.MM_MODEL_PLOU - 1e-9
    return arome != icon


def muestras_archivo():
    obs, prev, ec = leer_obs(), leer_prev(), leer_ecmwf()
    res = []
    for t, puntos in prev.items():
        p, e = puntos.get("casa"), ec.get(t)
        if not p or not e:
            continue
        fins = t.astimezone(LOCAL).strftime("%Y-%m-%dT%H:%M")
        for serie in obs.values():
            a, b = serie.get(t - dt.timedelta(minutes=60)), serie.get(t - dt.timedelta(minutes=30))
            if a is None or b is None:
                continue
            for plazo, horas in (("", 0), ("_previous_day1", 24)):
                mm = e.get(f"precipitation{plazo}_ecmwf_ifs")
                d = {"fins": fins, "antelacio_h": horas}
                d.update({f"pluja_{m}": p.get(f"precipitation{plazo}_{m}") for m in C.MODELOS_FINOS})
                x = A.rasgos(d, A.RASGOS_ARXIU)
                if x is None or mm is None:
                    continue
                res.append((t, horas, x, rasgos_ecmwf(mm, horas, d), desacord(d), float(a + b >= C.UMBRAL_MM)))
    return res


def lluvia_casa():
    """{fin de hora UTC: mm} de la estación de casa, con la lluvia del día acumulada."""
    filas = []
    with open(os.path.join(DIR, "casa_30min.csv")) as f:
        for r in csv.DictReader(f):
            if r["pluja_avui"] not in ("", "None"):
                filas.append((dt.datetime.fromisoformat(r["t"]).astimezone(UTC), float(r["pluja_avui"])))
    acum = dict(filas)
    res = {}
    for t, _ in filas:
        if t.minute:
            continue
        ant = t - dt.timedelta(hours=1)
        if ant in acum and t in acum:
            # Al pasar la medianoche local el acumulado vuelve a cero.
            mm = acum[t] - acum[ant] if acum[t] >= acum[ant] else acum[t]
            res[t] = mm
    return res


def muestras_casa():
    prev, ec, casa = leer_prev(), leer_ecmwf(), lluvia_casa()
    res = []
    for t, mm_obs in casa.items():
        if t.astimezone(LOCAL).date().isoformat() > C.PLUVIOMETRE_CASA_FIABLE_FINS:
            continue
        p, e = (prev.get(t) or {}).get("casa"), ec.get(t)
        if not p or not e:
            continue
        fins = t.astimezone(LOCAL).strftime("%Y-%m-%dT%H:%M")
        for plazo, horas in (("", 0), ("_previous_day1", 24)):
            mm = e.get(f"precipitation{plazo}_ecmwf_ifs")
            d = {"fins": fins, "antelacio_h": horas}
            d.update({f"pluja_{m}": p.get(f"precipitation{plazo}_{m}") for m in C.MODELOS_FINOS})
            x = A.rasgos(d, A.RASGOS_ARXIU)
            if x is None or mm is None:
                continue
            res.append((t, horas, x, rasgos_ecmwf(mm, horas, d), desacord(d), float(mm_obs >= C.UMBRAL_MM)))
    return res


def compara(ms, nom):
    t = np.array([m[0] for m in ms])
    horas = np.array([m[1] for m in ms])
    x = np.array([m[2] for m in ms])
    xe = np.hstack([x, np.array([m[3] for m in ms])])
    des = np.array([m[4] for m in ms])
    y = np.array([m[5] for m in ms])
    grup = np.array([(ti.isocalendar()[0] * 53 + ti.isocalendar()[1]) % A.SETMANES_VALIDACIO for ti in t])
    res = {}
    for plazo, h in (("curt_termini", 0), ("un_dia_abans", 24)):
        s = horas == h
        if s.sum() < 500 or y[s].sum() < 20:
            continue
        # Cada antelación se ajusta y se comprueba con sus propias muestras, en el
        # mismo periodo para los dos modelos.
        pb, pe = creuada(x[s], y[s], grup[s]), creuada(xe[s], y[s], grup[s])
        ys, ds = y[s], des[s]

        def brier(p, sel):
            return float(np.mean((p[sel] - ys[sel]) ** 2))
        tot = np.ones(len(ys), bool)
        fila = {"des_de": t[s].min().astimezone(LOCAL).date().isoformat(),
                "fins": t[s].max().astimezone(LOCAL).date().isoformat(),
                "mostres": int(s.sum()), "hores_pluja": int(ys.sum())}
        for sub, sel in (("tot", tot), ("desacord_arome_icon", ds)):
            b0, b1 = brier(pb, sel), brier(pe, sel)
            fila[sub] = {"mostres": int(sel.sum()), "hores_pluja": int(ys[sel].sum()),
                         "brier_base": round(b0, 5), "brier_ecmwf": round(b1, 5),
                         "millora_pct": round(100 * (b0 - b1) / b0, 1)}
        res[plazo] = fila
        for sub in ("tot", "desacord_arome_icon"):
            v = fila[sub]
            print(f"{nom} {plazo} {sub}: {v['mostres']} mostres, {v['hores_pluja']} amb pluja; "
                  f"Brier base {v['brier_base']}, + ECMWF {v['brier_ecmwf']} ({v['millora_pct']:+} %)")
    return res


def main():
    resultado = {"arxiu_sabadell_sant_cugat": compara(muestras_archivo(), "arxiu"),
                 "montflorit_casa": compara(muestras_casa(), "casa")}
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
