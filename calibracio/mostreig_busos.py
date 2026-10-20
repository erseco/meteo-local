#!/usr/bin/env python3
"""¿És de fiar el temps real dels busos urbans de Cerdanyola (CV) de l'AMB?

Mostreig temporal abans de decidir si «Si surts» porta els propers busos de
Montflorit. El 14-10-2026 a les 04:49 les CV van aparèixer per primer cop al
temps real de l'AMB (GTFS-RT, https://www.ambmobilitat.cat/transit/trips-updates/trips.bin);
fins llavors no hi eren. Una sola mostra no diu si hi seran cada dia ni si
les hores que dona encerten: això ho mesura aquest mostreig.

    mostreig_busos.py mostra    una lectura (la llança cada 2 minuts un
                                temporitzador del NAS); desa les CV en
                                $ESTAT_DIR/busos-cv/AAAA-MM-DD.jsonl
    mostreig_busos.py resum     què diu el mostreig, comparat amb l'horari
                                oficial (GTFS de l'AMB)

Sense dependències: el contenidor del NAS no té la biblioteca de protobuf
(el lector mínim és el de trens.py).
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from trens import camps  # noqa: E402

TEMPS_REAL = "https://www.ambmobilitat.cat/transit/trips-updates/trips.bin"
HORARI = "https://www.ambmobilitat.cat/OpenData/google_transit.zip"
LINIES = {"508": "CV1", "509": "CV2", "510": "CV3", "511": "CV4", "512": "CV5"}
# Parades de la CV1 dins del barri o a tocar (Zona Esportiva Montflorit i
# l'avinguda Flor de Maig fins a Sant Jeroni).
PARADES_BARRI = {"200061", "200062", "201464", "201465", "201463", "200075"}
DIR = Path(os.environ.get("ESTAT_DIR", "/estat")) / "busos-cv"


def baixa(url: str, segons: int = 30) -> bytes:
    peticio = urllib.request.Request(url, headers={"User-Agent": "meteo-local (mostreig busos CV)"})
    with urllib.request.urlopen(peticio, timeout=segons) as r:
        return r.read()


def llegeix(feed: bytes) -> tuple[int, int, list[dict]]:
    """(hora de la capçalera, viatges en total, viatges de les CV amb les parades)."""
    capcalera, total, cv = 0, 0, []
    for num, v in camps(feed):
        if num == 1:  # FeedHeader
            capcalera = dict(camps(v)).get(3, 0)
        elif num == 2:  # FeedEntity
            tu = dict(camps(v)).get(3)
            if tu is None:
                continue
            total += 1
            camps_tu = camps(tu)
            trip = dict(camps(dict(camps_tu)[1])) if any(n == 1 for n, _ in camps_tu) else {}
            viatge = trip.get(1, b"").decode()
            if viatge.split(".")[0] not in LINIES:
                continue
            parades = {}
            for n, stu in camps_tu:
                if n != 2:
                    continue
                c = dict(camps(stu))
                hora = None
                for camp in (2, 3):  # arrival, departure
                    if camp in c:
                        hora = dict(camps(c[camp])).get(2) or hora
                        if hora:
                            break
                parada = c.get(4, b"").decode()
                if parada and hora:
                    parades[parada] = hora
            cv.append({"v": viatge, "p": parades})
    return capcalera, total, cv


def mostra() -> int:
    DIR.mkdir(parents=True, exist_ok=True)
    ara = int(time.time())
    fila = {"t": ara}
    try:
        capcalera, total, cv = llegeix(baixa(TEMPS_REAL))
        fila.update(cap=capcalera, total=total, cv=cv)
    except Exception as error:  # cal anotar qualsevol fallada: és part del que es mesura
        fila["error"] = f"{type(error).__name__}: {error}"[:200]
    with open(DIR / f"{datetime.fromtimestamp(ara):%Y-%m-%d}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, separators=(",", ":")) + "\n")
    # Una línia al registre: és el rastre que mira el panell del NAS.
    print(f"{datetime.fromtimestamp(ara):%Y-%m-%d %H:%M} "
          + (fila["error"] if "error" in fila else f"{fila['total']} viatges, {len(fila['cv'])} de les CV"))
    return 0


def horari(dies: list[date]) -> dict[date, dict[str, dict]]:
    """Viatges de les CV que l'horari oficial preveu cada dia: {dia: {viatge: {inici, fi, parades}}}."""
    z = zipfile.ZipFile(io.BytesIO(baixa(HORARI, 120)))
    llegir = lambda nom: csv.DictReader(io.TextIOWrapper(z.open(nom), "utf-8-sig"))  # noqa: E731
    calendari = {r["service_id"]: r for r in llegir("calendar.txt") if r["service_id"].split(".")[0] in LINIES}
    excepcions = defaultdict(dict)
    for r in llegir("calendar_dates.txt"):
        if r["service_id"] in calendari:
            excepcions[r["service_id"]][r["date"]] = r["exception_type"]
    viatges = {r["trip_id"]: r["service_id"] for r in llegir("trips.txt") if r["route_id"] in LINIES}
    hores = defaultdict(dict)
    for r in llegir("stop_times.txt"):
        if r["trip_id"] in viatges:
            h, m, s = map(int, r["arrival_time"].split(":"))
            hores[r["trip_id"]][r["stop_id"]] = h * 3600 + m * 60 + s
    noms_dia = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    res = {}
    for dia in dies:
        clau = f"{dia:%Y%m%d}"
        mitjanit = datetime.combine(dia, datetime.min.time()).timestamp()
        res[dia] = {}
        for viatge, servei in viatges.items():
            c = calendari.get(servei)
            actiu = bool(c) and c["start_date"] <= clau <= c["end_date"] and c[noms_dia[dia.weekday()]] == "1"
            exc = excepcions[servei].get(clau)
            actiu = (actiu or exc == "1") and exc != "2"
            if actiu and hores[viatge]:
                p = {s: mitjanit + seg for s, seg in hores[viatge].items()}
                res[dia][viatge] = {"inici": min(p.values()), "fi": max(p.values()), "p": p}
    return res


def resum() -> int:
    fitxers = sorted(DIR.glob("*.jsonl"))
    if not fitxers:
        print("Encara no hi ha mostres.")
        return 0
    dies = [date.fromisoformat(f.stem) for f in fitxers]
    previst = horari(dies)
    print("Temps real de les CV de l'AMB, comparat amb l'horari oficial\n")
    for f, dia in zip(fitxers, dies):
        files = [json.loads(l) for l in f.open(encoding="utf-8")]
        errors = sum("error" in r for r in files)
        antigues = sum("cap" in r and r["t"] - r["cap"] > 300 for r in files)
        sense_cv = sum("cv" in r and not r["cv"] for r in files)
        vist = defaultdict(list)  # viatge → [(hora de la mostra, parades)]
        for r in files:
            for v in r.get("cv", []):
                vist[v["v"]].append((r["t"], v["p"]))
        primer, darrer = files[0]["t"], files[-1]["t"]
        print(f"{dia} ({len(files)} mostres, {datetime.fromtimestamp(primer):%H:%M}–{datetime.fromtimestamp(darrer):%H:%M})")
        print(f"  sense resposta: {errors}; dades de fa més de 5 min: {antigues}; sense cap CV: {sense_cv}")
        for ruta, nom in LINIES.items():
            # Només els viatges que van passar sencers mentre es mostrejava.
            esperats = {v: d for v, d in previst[dia].items()
                        if v.startswith(ruta + ".") and d["inici"] >= primer and d["fi"] <= darrer}
            if not esperats:
                continue
            trobats = [v for v in esperats if v in vist]
            # Abans de sortir: el viatge ha de sortir al temps real abans de la primera parada.
            avancats = [v for v in trobats if min(t for t, _ in vist[v]) <= esperats[v]["inici"]]
            print(f"  {nom}: {len(trobats)} de {len(esperats)} viatges previstos al temps real; "
                  f"{len(avancats)} ja abans de sortir")
            if ruta == "508":
                encert(esperats, vist)
        estranys = [v for v in vist if v not in previst[dia]]
        if estranys:
            print(f"  viatges al temps real que l'horari no preveu: {len(estranys)}")
        print()
    return 0


def encert(esperats: dict, vist: dict) -> None:
    """CV1 a les parades del barri: quant s'equivoca l'hora del temps real, 5-15 min abans de passar.

    L'hora «bona» és la darrera que dona el temps real per a la parada (la més
    propera al pas real que hi ha); es compara amb la que donava entre 5 i 15
    minuts abans, que és quan algú la miraria per sortir de casa."""
    errors = []
    for v in esperats:
        for parada in PARADES_BARRI:
            punts = [(t, p[parada]) for t, p in vist.get(v, []) if parada in p]
            if len(punts) < 2:
                continue
            final = punts[-1][1]
            if punts[-1][0] < final - 300:  # el viatge va deixar de sortir massa d'hora
                continue
            for t, hora in punts:
                if 300 <= final - t <= 900:
                    errors.append(abs(hora - final) / 60)
    if errors:
        errors.sort()
        mitjana = errors[len(errors) // 2]
        dins_2 = sum(e <= 2 for e in errors) / len(errors)
        print(f"    a les parades del barri, 5-15 min abans: error típic {mitjana:.1f} min; "
              f"{dins_2:.0%} amb menys de 2 min ({len(errors)} lectures)")


if __name__ == "__main__":
    ordre = sys.argv[1] if len(sys.argv) > 1 else ""
    if ordre == "mostra":
        raise SystemExit(mostra())
    if ordre == "resum":
        raise SystemExit(resum())
    print(__doc__)
    raise SystemExit(2)
