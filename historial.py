#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""El historial de la gráfica y el acierto de la previsión (ADR 0099; Juanjo,
17-10-2026: «que se pueda ir hacia atrás sin límite» y «algún índice o
indicador de lo buena que es la predicción… con el tiempo debería mejorar»).

Para cada día, hora a hora, lo medido en Montflorit y lo que decía la
previsión de las 7 de ese día (la del resumen de la mañana):

- Lo medido: la temperatura de la estación de casa (estacio-casa.csv) y la
  lluvia de la hora como la cuenta el aprendizaje (aprenentatge.observada:
  casa, las vecinas que cuentan y, para las horas secas, Meteocat). Si no se
  sabe si llovió, None.
- Lo previsto: lo que mostraba la web (`mostrat` de casa-AAAA-MM.jsonl, que
  apunta cada hora la previsión publicada) en la primera publicación de las
  7 de ese día; si falta, la última desde las 5. Cubre de las 7 a medianoche.

El acierto, sobre las horas con las dos cosas:
- Temperatura: el error medio absoluto (°C).
- Lluvia: de las horas en que decía 50 % o más, en cuántas llovió; de las
  que decía menos del 20 %, en cuántas no llovió. Es la comprobación de
  calibración de una probabilidad, contada en casos.
Los últimos 30 días, los 30 anteriores (para ver si mejora) y por meses.

Archivos para la web (los sube publica.sh a IONOS):
  historial.json              los días que hay y el acierto
  historial-AAAA-MM-DD.json   cada día, hora a hora

  python3 historial.py fes CARPETA [DIES]   escribe el índice y los días (DIES: solo los últimos)
"""
import datetime as dt
import glob
import json
import os
import sys

import aprenentatge as A
import config as C
import prevision as P

REGISTRE = A.REGISTRE
PRIMER_DIA = dt.date(2026, 10, 4)       # el primero con la estación de casa en el registro
HORA_PREVISIO = 7
PROB_PLOU = 0.5                          # «plourà», como en la web (PROB_PLUJA)
PROB_SEC = 0.2                           # «no plourà», por debajo de «possible pluja»
DIES_FINESTRA = 30
MIN_HORES_TEMP = 48                      # para dar el error de la temperatura
MIN_CASOS_PLUJA = 20                     # para dar el acierto de la lluvia (en cada sentido)


def hores_del_dia(dia):
    """Las horas de un día local (23 o 25 el día del cambio de hora): [(hora, fins)]."""
    ini = dt.datetime.combine(dia, dt.time()).replace(tzinfo=P.ZONA)
    fi = dt.datetime.combine(dia + dt.timedelta(days=1), dt.time()).replace(tzinfo=P.ZONA)
    res, t = [], ini.astimezone(dt.timezone.utc)
    while t < fi.astimezone(dt.timezone.utc):
        res.append((P.clau_hora(t), P.clau_hora(t + dt.timedelta(hours=1))))
        t += dt.timedelta(hours=1)
    return res


def emissions(registre=None):
    """Las previsiones apuntadas, {emes: {fins: mostrat}}, de casa-*.jsonl."""
    res = {}
    for ruta in sorted(glob.glob(os.path.join(registre or REGISTRE, "casa-*.jsonl"))):
        with open(ruta, encoding="utf-8") as f:
            for linia in f:
                try:
                    e = json.loads(linia)
                except ValueError:
                    continue
                hores = {h["fins"]: h["mostrat"] for h in e.get("hores") or [] if h.get("mostrat")}
                if hores:
                    res[e["emes"]] = hores
    return res


def previsio_del_mati(dia, emes):
    """(emes, {fins: mostrat}) de la previsión de las 7 del día: la primera de
    las 7; si no hay, la última desde las 5. None si no hay ninguna."""
    del_dia = sorted(k for k in emes if dt.datetime.fromisoformat(k).date() == dia)
    hora = lambda k: dt.datetime.fromisoformat(k).hour
    de_les_7 = [k for k in del_dia if hora(k) == HORA_PREVISIO]
    abans = [k for k in del_dia if 5 <= hora(k) < HORA_PREVISIO]
    k = de_les_7[0] if de_les_7 else (abans[-1] if abans else None)
    return (k, emes[k]) if k else None


def un_dia(dia, casa, meteocat, veines, emes):
    """El día, para la web: {dia, previsio_de, hores: [...], encert}."""
    prev = previsio_del_mati(dia, emes)
    files = []
    for hora, fins in hores_del_dia(dia):
        t = A._num((casa.get(fins) or {}).get("temperatura"))
        mm = A.observada(casa, meteocat, veines, fins)
        f = {"hora": hora, "fins": fins, "mesura": True,
             "temperatura": None if t is None else round(t, 1),
             "pluja_mm": None if mm is None else round(mm, 1)}
        p = prev and prev[1].get(fins)
        if p:
            f["prev"] = {k: p.get(k) for k in ("temperatura", "probabilitat", "pluja_mm")}
        files.append(f)
    return {"dia": dia.isoformat(), "previsio_de": prev and prev[0], "hores": files, "encert": encert(files)}


def encert(files):
    """El acierto de unas horas: {temperatura: {error, hores}, pluja: {plou: [sí, de], sec: [sí, de]}}."""
    errors = [abs(f["temperatura"] - f["prev"]["temperatura"]) for f in files
              if f.get("prev") and f["temperatura"] is not None and f["prev"].get("temperatura") is not None]
    plou, sec = [0, 0], [0, 0]
    for f in files:
        p = (f.get("prev") or {}).get("probabilitat")
        if p is None or f["pluja_mm"] is None:
            continue
        mullat = f["pluja_mm"] >= C.UMBRAL_MM
        if p >= PROB_PLOU:
            plou = [plou[0] + mullat, plou[1] + 1]
        elif p < PROB_SEC:
            sec = [sec[0] + (not mullat), sec[1] + 1]
    return {"temperatura": {"error": round(sum(errors) / len(errors), 2) if errors else None, "hores": len(errors)},
            "pluja": {"plou": plou, "sec": sec}}


def suma(encerts):
    """El acierto de varios días juntos."""
    hores = sum(e["temperatura"]["hores"] for e in encerts)
    err = sum((e["temperatura"]["error"] or 0) * e["temperatura"]["hores"] for e in encerts)
    plou = [sum(e["pluja"]["plou"][i] for e in encerts) for i in (0, 1)]
    sec = [sum(e["pluja"]["sec"][i] for e in encerts) for i in (0, 1)]
    return {"temperatura": {"error": round(err / hores, 2) if hores else None, "hores": hores},
            "pluja": {"plou": plou, "sec": sec}}


def tots(avui=None, registre=None):
    """Todos los días del registro, del primero a hoy."""
    avui = avui or dt.date.today()
    if registre:
        A.REGISTRE = registre
    casa = A._llegeix("estacio-casa.csv")
    meteocat, veines = A._meteocat(), A._veines()
    emes = emissions(registre)
    dies, d = [], PRIMER_DIA
    while d <= avui:
        dies.append(un_dia(d, casa, meteocat, veines, emes))
        d += dt.timedelta(days=1)
    return dies


def index(dies, avui):
    """historial.json: los días que hay y el acierto de los últimos 30 días,
    de los 30 anteriores y de cada mes, con los mínimos para darlo."""
    complets = [d for d in dies if d["dia"] < avui.isoformat()]
    fi = avui
    finestra = lambda ini, fi_: [d["encert"] for d in complets if ini.isoformat() <= d["dia"] < fi_.isoformat()]
    mesos = {}
    for d in complets:
        mesos.setdefault(d["dia"][:7], []).append(d["encert"])
    return {"generat": dt.datetime.now(P.ZONA).isoformat(timespec="minutes"),
            "dies": [d["dia"] for d in dies],
            "minims": {"temperatura_hores": MIN_HORES_TEMP, "pluja_casos": MIN_CASOS_PLUJA},
            "encert": {"darrers": suma(finestra(fi - dt.timedelta(days=DIES_FINESTRA), fi)),
                       "anteriors": suma(finestra(fi - dt.timedelta(days=2 * DIES_FINESTRA),
                                                  fi - dt.timedelta(days=DIES_FINESTRA))),
                       "mesos": {m: suma(e) for m, e in sorted(mesos.items())}}}


def fes(carpeta, ultims=None, avui=None, registre=None):
    """Escribe historial.json y los días (todos o los `ultims`). Devuelve los nombres."""
    avui = avui or dt.date.today()
    dies = tots(avui, registre)
    os.makedirs(carpeta, exist_ok=True)
    noms = ["historial.json"]
    escriu = lambda nom, dades: json.dump(dades, open(os.path.join(carpeta, nom), "w", encoding="utf-8"),
                                          ensure_ascii=False, separators=(",", ":"))
    escriu("historial.json", index(dies, avui))
    for d in dies[-ultims:] if ultims else dies:
        nom = f"historial-{d['dia']}.json"
        escriu(nom, d)
        noms.append(nom)
    return noms


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4) or sys.argv[1] != "fes":
        sys.exit(__doc__)
    print(" ".join(fes(sys.argv[2], int(sys.argv[3]) if len(sys.argv) == 4 else None)))
