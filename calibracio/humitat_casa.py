#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""La corrección del punto de rocío del modelo, con el año de la estación de
casa (ADR 0114).

La humedad de la gráfica sale del rocío de AROME y de la temperatura de la
página (casa.humitat_hora). El 21-10-2026 a las 5 h el barrio medía un 93 % y
la gráfica daba un 82 %: el modelo veía el aire más seco. Aquí se ajusta la
corrección del rocío como la de la temperatura (ADR 0017): regresión ridge
del error del modelo (rocío previsto menos medido) según el propio rocío, la
temperatura, la humedad, las nubes, la radiación, la hora, el día del año,
la antelación y el error que tenía al prever.

La verdad es el rocío de la estación de casa: el del barrio (la mediana de
casa y las vecinas, el del recuadro «Ara») se diferencia de él en −0,07 °C de
media del 9 al 21-10-2026 (280 horas), porque el aire lleva la misma agua en
todo el barrio; la humedad cambia con la temperatura, no con el rocío. Las
vecinas solo están registradas desde el 9 de octubre: el aprendizaje diario
del NAS (aprenentatge.py) ya usa la mediana.

Comprobación con avance temporal (remostreig.avanc, ADR 0106): cada día se
corrige con lo ajustado con los días anteriores. Se adopta solo si gana al
modelo sin corregir en el 95 % de los remuestreos por días (ADR 0105).

Lee lo que ya descargó calibracio/estacio_casa.py (calibracio/dades/).
Escribe calibracio/humitat_casa.json.
Uso: python3 calibracio/humitat_casa.py
"""
import datetime as dt
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aprenentatge as A  # noqa: E402
import remostreig as R  # noqa: E402
import sol_estacio as SE  # noqa: E402
from calibracio.estacio_casa import ANTELACIONES, LOCAL, PREV_TEMP, UTC, VARIABLES, estacion  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "humitat_casa.json")


def muestras(lect, prev):
    """Una muestra por hora medida y antelación, con el rocío medido (obs) y
    la temperatura y la humedad medidas, para pasar el rocío a humedad."""
    idx = {dt.datetime.fromisoformat(t).replace(tzinfo=UTC): i for i, t in enumerate(prev["time"])}
    res = []
    for t, i in idx.items():
        f = lect.get(t)
        if not f or f["rosada"] is None or f["humitat"] is None:
            continue
        for horas, plazo in ANTELACIONES:
            emes = t - dt.timedelta(hours=horas)
            fe, ie = lect.get(emes), idx.get(emes)
            d = {"fins": t.astimezone(LOCAL).strftime("%Y-%m-%dT%H:%M"), "antelacio_h": horas,
                 **{v: prev[f"{v}{plazo}"][i] for v in VARIABLES}}
            if fe and fe["rosada"] is not None and ie is not None:
                r_emes = A.rosada_model({v: prev[v][ie] for v in VARIABLES})
                if r_emes is not None:
                    d["error_rosada_ara"] = r_emes - fe["rosada"]
            if A.rosada_model(d) is None:
                continue
            res.append({**d, "t": t, "obs": f["rosada"], "temp_obs": f["temperatura"], "hum_obs": f["humitat"]})
    return res


def ajusta(ms):
    """Pesos con y sin el error al prever, y su comprobación con avance
    temporal: el error del rocío (°C) y el de la humedad que sale de él con la
    temperatura medida (puntos de %), corregido y sin corregir."""
    resultado = {}
    for clave, noms in (("", A.RASGOS_ROSADA), ("_sense_estacio", A.RASGOS_ROSADA_SENSE_ESTACIO)):
        sel = [m for m in ms if A.rasgos(m, noms) is not None]
        x = np.array([A.rasgos(m, noms) for m in sel])
        model = np.array([A.rosada_model(m) for m in sel])
        obs = np.array([m["obs"] for m in sel])
        err = model - obs
        dies = np.array([m["fins"][:10] for m in sel])
        h = np.array([m["antelacio_h"] for m in sel])
        pred = np.full(len(err), np.nan)
        for ent, aval in R.avanc(dies):
            pred[aval] = x[aval] @ A.ajustar_ridge(x[ent], err[ent])
        s = ~np.isnan(pred)
        corr = model - pred
        tobs = np.array([m["temp_obs"] for m in sel])
        hobs = np.array([m["hum_obs"] for m in sel])

        def hum(r, t):
            return np.array([SE.humitat(min(a, b), b) for a, b in zip(r, t)])
        e_hum_model = np.abs(hum(model, tobs) - hobs)
        e_hum_corr = np.full(len(err), np.nan)
        e_hum_corr[s] = np.abs(hum(corr[s], tobs[s]) - hobs[s])
        resultado[f"rasgos{clave}"] = noms
        resultado[f"w{clave}"] = [round(v, 5) for v in A.ajustar_ridge(x, err).tolist()]
        resultado[f"validacio{clave}"] = {
            "mostres": int(len(err)), "dies": len(set(dies)), "avaluades": int(s.sum()),
            "dies_avaluats": len(set(dies[s])),
            "biaix_model": round(float(err[s].mean()), 2),
            "error_model": round(float(np.abs(err[s]).mean()), 3),
            "error_corregit": round(float(np.abs(err[s] - pred[s]).mean()), 3),
            "seguretat": R.seguretat(np.abs(err[s] - pred[s]), np.abs(err[s]), dies[s]),
            "humitat_error_model": round(float(e_hum_model[s].mean()), 2),
            "humitat_error_corregit": round(float(e_hum_corr[s].mean()), 2),
            "per_antelacio": {str(a): {"model": round(float(np.abs(err[s & (h == a)]).mean()), 2),
                                       "corregit": round(float(np.abs(err - pred)[s & (h == a)].mean()), 2),
                                       "humitat_model": round(float(e_hum_model[s & (h == a)].mean()), 1),
                                       "humitat_corregit": round(float(e_hum_corr[s & (h == a)].mean()), 1)}
                              for a, _ in ANTELACIONES}}
    return resultado


def main():
    _, lect = estacion()
    with open(PREV_TEMP, encoding="utf-8") as f:
        prev = json.load(f)
    ms = muestras(lect, prev)
    res = ajusta(ms)
    resultado = {"origen": "arxiu",
                 "des_de": min(m["t"] for m in ms).astimezone(LOCAL).date().isoformat(),
                 "fins": max(m["t"] for m in ms).astimezone(LOCAL).date().isoformat(),
                 # La web la usa solo si gana con seguridad (ADR 0105).
                 "adoptat": bool(R.guanya(res["validacio"]["seguretat"])), **res}
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in resultado.items() if k.startswith("validacio") or k == "adoptat"},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
