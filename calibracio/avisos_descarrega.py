#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""El histórico de avisos oficiales del barrio, para aprender cuánto pesan en
la probabilidad de lluvia (ADR 0097).

- AEMET: el archivo de avisos CAP de AEMET OpenData (desde el 18-06-2018),
  por meses. Se queda con los del Prelitoral de Barcelona (C.ZONA_AVISOS).
- Meteocat: los episodios de la Situació Meteorològica de Perill de cada día
  (API v2, /smp/episodis-oberts?data=…), los del Vallès Occidental, leídos
  con smp.de_la_comarca, igual que en la página.

Cada aviso se guarda con su hora de emisión, para usar al ajustar solo los
que ya se conocían cuando se hizo la previsión. Las claves no van en el
repositorio: AEMET_API_KEY y METEOCAT_API_KEY, o los archivos aemet.key y
meteocat.key de ~/.config/meteo-montflorit/. Los datos van a calibracio/dades/,
que no se publica: las condiciones de la API de Meteocat no permiten
difundirlos (solo se publican los pesos que salen de ellos).

Uso: python3 calibracio/avisos_descarrega.py aemet|meteocat [DES_DE [FINS]]
     (fechas AAAA-MM-DD; por defecto, el archivo de pluja_casa.py)
"""
import datetime as dt
import io
import json
import os
import re
import sys
import tarfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
import smp as SMP  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
DADES = os.path.join(AQUI, "dades")
SORTIDA_AEMET = os.path.join(DADES, "avisos_aemet.json")
DIR_METEOCAT = os.path.join(DADES, "smp")
DES_DE, FINS = "2024-01-01", "2026-10-04"


def clau(nom):
    v = os.environ.get(f"{nom.upper()}_API_KEY")
    if v:
        return v.strip()
    with open(os.path.expanduser(f"~/.config/meteo-montflorit/{nom}.key")) as f:
        return f.read().strip()


def baixa(url, capcaleres, intents=4):
    for i in range(intents):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "meteo-local", **capcaleres})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as ex:
            if ex.code == 404:
                raise
            if i == intents - 1:
                raise
            time.sleep(20 * (i + 1) if ex.code == 429 else 5)
        except OSError:
            if i == intents - 1:
                raise
            time.sleep(5)


# --- AEMET ------------------------------------------------------------------------------

def xmls(contingut):
    """Los XML de un archivo de AEMET: un tar (a veces comprimido) que puede
    llevar otros tar dentro."""
    try:
        tf = tarfile.open(fileobj=io.BytesIO(contingut))
    except tarfile.TarError:
        yield contingut
        return
    for m in tf.getmembers():
        if not m.isfile():
            continue
        dins = tf.extractfile(m).read()
        if m.name.endswith(".xml"):
            yield dins
        else:
            yield from xmls(dins)


def camp(xml, nom):
    m = re.search(rf"<{nom}>(.*?)</{nom}>", xml, re.S)
    return m.group(1).strip() if m else ""


def parametre(info, nom, etiqueta="parameter"):
    for p in re.findall(rf"<{etiqueta}>(.*?)</{etiqueta}>", info, re.S):
        if camp(p, "valueName") == nom:
            return camp(p, "value")
    return ""


def avisos_cap(xml):
    """Los avisos de un mensaje CAP de AEMET para la zona: en castellano, con
    su emisión, tipo de mensaje, fenómeno, nivel y horas."""
    s = xml.decode("utf-8", "replace")
    res = []
    for info in re.findall(r"<info>(.*?)</info>", s, re.S):
        if not camp(info, "language").startswith("es"):
            continue
        zones = [camp(a, "areaDesc") for a in re.findall(r"<area>(.*?)</area>", info, re.S)]
        if C.ZONA_AVISOS not in zones:
            continue
        res.append({"id": camp(s, "identifier"), "emes": camp(s, "sent"), "tipus_missatge": camp(s, "msgType"),
                    "referencies": camp(s, "references"), "fenomen": parametre(info, "AEMET-Meteoalerta fenomeno", "eventCode"),
                    "nivell": parametre(info, "AEMET-Meteoalerta nivel"), "event": camp(info, "event"),
                    "inici": camp(info, "onset") or camp(info, "effective"), "fi": camp(info, "expires")})
    return res


def tram_aemet(d, fi, k):
    """Los avisos de la zona de un tramo de 2 días del archivo."""
    url = ("https://opendata.aemet.es/opendata/api/avisos_cap/archivo/"
           f"fechaini/{d.isoformat()}T00:00:00UTC/fechafin/{fi.isoformat()}T23:59:59UTC")
    meta = json.loads(baixa(url, {"api_key": k}).decode("latin-1"))
    if meta.get("estado") == 404:
        return d, []
    if meta.get("estado") != 200 or not meta.get("datos"):
        raise RuntimeError(f"{d}: {meta.get('descripcion')}")
    return d, [a for x in xmls(baixa(meta["datos"], {"api_key": k})) for a in avisos_cap(x)]


def aemet(des_de, fins, processos=4):
    """Por tramos de 2 días, lo máximo que admite el archivo, en varios
    procesos (AEMET tarda unos 7 s en servir cada uno). Se puede
    interrumpir: los tramos hechos quedan apuntados y no se repiten."""
    from concurrent.futures import ProcessPoolExecutor, as_completed
    k = clau("aemet")
    vistos, fets = {}, set()
    if os.path.exists(SORTIDA_AEMET):
        with open(SORTIDA_AEMET) as f:
            vistos = {(a["id"], a["fenomen"], a["inici"]): a for a in json.load(f)}
    ruta_fets = SORTIDA_AEMET + ".fets"
    if os.path.exists(ruta_fets):
        with open(ruta_fets) as f:
            fets = set(f.read().split())

    def desa():
        os.makedirs(DADES, exist_ok=True)
        with open(SORTIDA_AEMET, "w", encoding="utf-8") as f:
            json.dump(sorted(vistos.values(), key=lambda a: (a["emes"], a["id"])), f, ensure_ascii=False)
        with open(ruta_fets, "w") as f:
            f.write("\n".join(sorted(fets)))

    d, final, trams = dt.date.fromisoformat(des_de), dt.date.fromisoformat(fins), []
    while d <= final:
        fi = min(d + dt.timedelta(days=1), final)
        if d.isoformat() not in fets:
            trams.append((d, fi))
        d = fi + dt.timedelta(days=1)
    with ProcessPoolExecutor(processos) as ex:
        for n, fut in enumerate(as_completed([ex.submit(tram_aemet, a, b, k) for a, b in trams]), 1):
            dia, avisos = fut.result()
            for a in avisos:
                vistos[(a["id"], a["fenomen"], a["inici"])] = a
            fets.add(dia.isoformat())
            print(dia, len(avisos), "avisos del", C.ZONA_AVISOS, f"({n}/{len(trams)})", flush=True)
            if n % 10 == 0:
                desa()
    desa()


# --- Meteocat ---------------------------------------------------------------------------

def meteocat(des_de, fins):
    """Un archivo por día, con los episodios en bruto (para no repetir
    consultas si cambia la lectura) y los avisos de la comarca."""
    k = clau("meteocat")
    os.makedirs(DIR_METEOCAT, exist_ok=True)
    d, final = dt.date.fromisoformat(des_de), dt.date.fromisoformat(fins)
    while d <= final:
        ruta = os.path.join(DIR_METEOCAT, f"{d.isoformat()}.json")
        if not os.path.exists(ruta):
            url = f"https://api.meteo.cat/pronostic/v2/smp/episodis-oberts?data={d.isoformat()}Z"
            try:
                episodis = json.loads(baixa(url, {"X-Api-Key": k}))
            except urllib.error.HTTPError as ex:
                if ex.code == 429:
                    print("Quota de Meteocat exhaurida; es continuarà el mes vinent.")
                    return
                raise
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump({"episodis": episodis, "avisos": SMP.de_la_comarca(episodis)}, f, ensure_ascii=False)
            print(d, len(SMP.de_la_comarca(episodis)), "avisos del Vallès Occidental")
            time.sleep(1)
        d += dt.timedelta(days=1)


if __name__ == "__main__":
    font = sys.argv[1] if len(sys.argv) > 1 else ""
    args = sys.argv[2:4] + [DES_DE, FINS][len(sys.argv[2:4]):]
    {"aemet": aemet, "meteocat": meteocat}[font](*args)
