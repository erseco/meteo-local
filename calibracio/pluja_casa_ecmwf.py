#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""El modelo del archivo con ECMWF IFS (9 km) como un modelo más (ADR 0086).

Como pluja_casa.py (ADR 0021): regresión logística con las previsiones
archivadas en casa y la lluvia medida en Sabadell y Sant Cugat, cada estación
una muestra. Rasgos: los del archivo y los de ECMWF
(aprenentatge.RASGOS_ARXIU_ECMWF). Solo entran las horas con ECMWF: a corto
plazo, todo el archivo; con un día de antelación, desde octubre de 2025,
cuando ECMWF abrió los datos de 9 km (ecmwf_prova.py). Se valida contra el
modelo sin ECMWF con las mismas muestras, en grupos de semanas, por
antelación. Escribe pluja_casa_ecmwf.json, que la página usa si la pasada
tiene ECMWF (aprenentatge.prob_pluja).

Necesita descarrega.py y ecmwf_descarrega.py.
Uso: python3 calibracio/pluja_casa_ecmwf.py
"""
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aprenentatge as A  # noqa: E402
import config as C  # noqa: E402
from calibracio.analitza import leer_obs, leer_prev  # noqa: E402
from calibracio.ecmwf_prova import leer_ecmwf  # noqa: E402
from calibracio.pluja_casa import creuada, fiabilitat  # noqa: E402

LOCAL = ZoneInfo("Europe/Madrid")
SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pluja_casa_ecmwf.json")


def muestras():
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
                d = {"fins": fins, "antelacio_h": horas,
                     f"pluja_{C.MODEL_ECMWF}": e.get(f"precipitation{plazo}_{C.MODEL_ECMWF}")}
                d.update({f"pluja_{m}": p.get(f"precipitation{plazo}_{m}") for m in C.MODELOS_FINOS})
                xe = A.rasgos(d, A.RASGOS_ARXIU_ECMWF)
                if xe is not None:
                    res.append((t, horas, xe, float(a + b >= C.UMBRAL_MM)))
    return res


def main():
    ms = muestras()
    t = np.array([m[0] for m in ms])
    horas = np.array([m[1] for m in ms])
    xe = np.array([m[2] for m in ms])
    x = xe[:, :len(A.RASGOS_ARXIU)]
    y = np.array([m[3] for m in ms])
    grup = np.array([(ti.isocalendar()[0] * 53 + ti.isocalendar()[1]) % A.SETMANES_VALIDACIO for ti in t])
    p_ec, p_base = creuada(xe, y, grup), creuada(x, y, grup)

    def brier(p, s):
        return round(float(np.mean((p[s] - y[s]) ** 2)), 5)

    validacio = {"metode": f"validació creuada en {A.SETMANES_VALIDACIO} grups de setmanes, "
                           "les mateixes mostres amb ECMWF i sense"}
    for nom, h in (("curt_termini", 0), ("un_dia_abans", 24)):
        s = horas == h
        b0, b1 = brier(p_base, s), brier(p_ec, s)
        validacio[nom] = {
            "des_de": t[s].min().astimezone(LOCAL).date().isoformat(),
            "mostres": int(s.sum()), "hores_pluja": int(y[s].sum()),
            "error_sense_ecmwf": b0, "error": b1, "millora_pct": round(100 * (b0 - b1) / b0, 1),
            "fiabilitat": fiabilitat(p_ec[s], y[s])}
        per_grup = []
        for g in sorted(set(grup)):
            sg = s & (grup == g)
            a, b = brier(p_base, sg), brier(p_ec, sg)
            per_grup.append(round(100 * (a - b) / a, 1))
        validacio[nom]["millora_per_grup_pct"] = per_grup
    resultado = {
        "origen": "arxiu", "ecmwf": True,
        "des_de": t.min().astimezone(LOCAL).date().isoformat(),
        "fins": t.max().astimezone(LOCAL).date().isoformat(),
        "rasgos": A.RASGOS_ARXIU_ECMWF, "w": [round(v, 5) for v in A.ajustar(xe, y).tolist()],
        "mostres": int(len(y)), "hores_pluja": int(y.sum()),
        "validacio": validacio,
    }
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1)
    for nom in ("curt_termini", "un_dia_abans"):
        v = validacio[nom]
        print(f"{nom} (des del {v['des_de']}): {v['mostres']} mostres, {v['hores_pluja']} amb pluja. "
              f"Error sense ECMWF {v['error_sense_ecmwf']}, amb ECMWF {v['error']} ({v['millora_pct']:+} %); "
              f"per grups {v['millora_per_grup_pct']}")
        print("  fiabilitat", " ".join(f"{100 * f['donada']:.0f}→{100 * f['va_ploure']:.0f} ({f['hores']})"
                                       for f in v["fiabilitat"]))


if __name__ == "__main__":
    main()
