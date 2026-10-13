#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Si circulen els trens de prop de Montflorit (ADR 0029).

Les línies que paren al terme de Cerdanyola: R4, R7 i R8 de Rodalies i S2
d'FGC (Bellaterra i Universitat Autònoma). Per a cada una:

- **Avisos**: els de Rodalies, de l'API de la seva web
  (`serveisgrs.rodalies.gencat.cat`, la mateixa que fa servir
  rodalies.gencat.cat) i, si no respon, els de Renfe (GTFS-RT en JSON,
  `gtfsrt.renfe.com`), que el 12-10-2026 encara portava avisos del 6 i del 7
  que la web de Rodalies ja no tenia (ADR 0078); els d'FGC (GTFS-RT en
  protobuf, al portal de dades obertes). Un avís «propi» només parla d'aquella
  línia; un de «general», de moltes. Un avís que només diu que el servei és
  normal («Servei ferroviari a tot el recorregut») no és una incidència.
- **Trens que es mouen** a TRENS_RADI_KM o menys de l'estació de la línia a
  Cerdanyola. Un tren aturat també envia la seva posició (el 07-10-2026, amb
  tot Rodalies parat, dos de l'R7 apareixien «a l'estació»): per això es
  compara amb la posició de la passada anterior, si és prou recent; sense,
  compten els que no estan aturats. I només els de prop de l'estació: aquell
  dia l'R4 circulava pel tram sud, que no serveix a qui surt de Cerdanyola.
  Amb trens cada 15 o 30 minuts, en una passada pot no haver-n'hi cap a prop:
  la línia circula si se n'ha vist un en els últims TRENS_VIST_MIN minuts.

L'estat: «bus» si l'avís propi més recent que parla del servei diu que va per
carretera (el 07-10-2026 l'R8 tenia alhora un avís vell de «servei per
carretera» i un de nou de «circulació ferroviària»: mana el nou, auditoria
del 07-10-2026); «incidencies» si circula i hi ha algun avís; «circula» si
circula sense avisos; «sense_trens» si dins de l'horari no se n'ha vist cap, i
«fora_horari» abans del primer tren de la línia a Cerdanyola (i mitja hora
més) o després de l'últim (config.TRENS_HORARI_LINIA). Els avisos es mostren
del més nou al més vell.
Els textos dels avisos no es tradueixen mai: es mostren en l'idioma en què
els publica l'operador. Si n'hi ha en català i en castellà, cada versió de la
pàgina mostra el seu (Renfe els marca tots dos com a castellà: es distingeixen
pel contingut); si només n'hi ha un, totes dues mostren aquell.
Llegeix la xarxa a cada passada de la pàgina de casa, sense IA.

Ús:
  python3 trens.py          l'estat ara (amb xarxa)
"""
import datetime as dt
import json
import math
import os
import re
import urllib.request

import config as C

RENFE = "https://gtfsrt.renfe.com/"
# Els avisos de la web de Rodalies (ADR 0078): no és un servei documentat, i
# es vigila cada dia (comprova).
RODALIES = "https://serveisgrs.rodalies.gencat.cat/api/notices?limit=500&sort=date,desc&sort=time,desc"
FGC = "https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets/"
UA = {"User-Agent": "meteo-local/" + C.VERSION}
ESTAT = os.path.join(os.environ.get("TRENS_DIR", "/estat"), "trens-posicions.json")
# Moure's més que això entre dues passades és circular (el GPS balla uns metres).
MOGUT_M = 300
POSICIONS_MAX_MIN = 40      # posicions més velles: no es comparen
POSICIONS_VELLES_MIN = 10   # feed de posicions més vell: sense dades


def get(url, binari=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        dades = r.read()
    return dades if binari else json.loads(dades)


# --- Protobuf mínim ------------------------------------------------------------
# Prou per llegir els avisos GTFS-RT sense dependències: el contenidor del NAS
# no té la biblioteca de protobuf.

def _varint(b, i):
    n = desp = 0
    while True:
        c = b[i]
        i += 1
        n |= (c & 0x7F) << desp
        if c < 0x80:
            return n, i
        desp += 7


def camps(b):
    """Els camps d'un missatge: llista de (número, valor). Els de longitud
    variable surten com a bytes; els enters, com a int."""
    res, i = [], 0
    while i < len(b):
        clau, i = _varint(b, i)
        num, tipus = clau >> 3, clau & 7
        if tipus == 0:
            v, i = _varint(b, i)
        elif tipus == 2:
            n, i = _varint(b, i)
            v, i = b[i:i + n], i + n
        elif tipus == 1:
            v, i = b[i:i + 8], i + 8
        elif tipus == 5:
            v, i = b[i:i + 4], i + 4
        else:
            raise ValueError(f"tipus de camp desconegut: {tipus}")
        res.append((num, v))
    return res


def _text(traduit):
    """TranslatedString: {idioma: text}."""
    res = {}
    for num, t in camps(traduit):
        if num == 1:
            c = dict(camps(t))
            res[c.get(2, b"").decode()] = c.get(1, b"").decode()
    return res


def iso(segons):
    """Segons des de 1970 (GTFS-RT) → ISO local amb minuts, o None."""
    try:
        return dt.datetime.fromtimestamp(int(segons), dt.timezone.utc).astimezone().isoformat(timespec="minutes")
    except (TypeError, ValueError, OverflowError):
        return None


def avisos_pb(b):
    """Els avisos d'un FeedMessage GTFS-RT: [{rutes, text, inici}]. inici és
    el començament del primer període actiu de l'avís (ISO), o None."""
    res = []
    for num, entitat in camps(b):
        if num != 2:
            continue
        for n2, alerta in camps(entitat):
            if n2 != 5:
                continue
            rutes, textos, inicis, fins = [], {}, [], []
            for n3, v in camps(alerta):
                if n3 == 1:
                    inicis += [t for n4, t in camps(v) if n4 == 1]
                    fins += [t for n4, t in camps(v) if n4 == 2]
                elif n3 == 5:
                    rutes += [r.decode() for n4, r in camps(v) if n4 == 2]
                elif n3 in (10, 11):
                    for idioma, t in _text(v).items():
                        textos.setdefault(idioma, "")
                        textos[idioma] = (textos[idioma] + " " + t).strip()
            res.append({"rutes": rutes, "text": textos, "inici": iso(min(inicis)) if inicis else None,
                        "fi": iso(max(fins)) if fins and len(fins) == len(inicis) else None})
    return res


# --- Rodalies i FGC -------------------------------------------------------------

def linia_renfe(ruta):
    """«51T0037R7» → «R7» (les rutes de Rodalies comencen per 51)."""
    m = re.match(r"51T\d+((?:R|RG|RL|RT)\d+[NS]?)$", ruta or "")
    return m and m.group(1)


CATALA = re.compile(r"\b(servei|per causes|no es pot|recorregut|usuaris|demanem|els|amb|estació|línia)\b", re.I)
CASTELLA = re.compile(r"\b(servicio|por causas|no se puede|recorrido|usuarios|pedimos|los|con|estación|línea)\b", re.I)


def idiomes(textos):
    """{"ca": …, "es": …} a partir de textos amb idioma o sense: cada text va
    a l'idioma que diu el seu contingut."""
    res = {}
    for t in textos:
        t = " ".join(t.split())
        if t:
            idioma = "ca" if len(CATALA.findall(t)) > len(CASTELLA.findall(t)) else "es"
            res.setdefault(idioma, t)
    if res:
        res.setdefault("ca", res.get("es"))
        res.setdefault("es", res.get("ca"))
    return res


def avisos_renfe(dades=None):
    """[{linies, text, inici}] dels avisos de Renfe (alerts.json, o dades ja
    llegides)."""
    res = []
    for e in (dades or get(RENFE + "alerts.json")).get("entity", []):
        a = e.get("alert", {})
        linies = {linia_renfe(i.get("routeId")) for i in a.get("informedEntity", [])} - {None}
        textos = idiomes(t.get("text", "") for t in a.get("descriptionText", {}).get("translation", []))
        periodes = a.get("activePeriod") or []
        inicis = [p.get("start") for p in periodes if p.get("start")]
        fins = [p.get("end") for p in periodes if p.get("end")]
        if linies and textos:
            # Sense final en algun període, l'avís no acaba (GTFS-RT: end absent = obert).
            res.append({"linies": linies, "text": textos, "inici": iso(min(inicis, key=int)) if inicis else None,
                        "fi": iso(max(fins, key=int)) if fins and len(fins) == len(periodes) else None})
    return res


def avisos_rodalies(dades=None):
    """[{linies, text, inici}] dels avisos de la web de Rodalies: els vigents,
    amb la data i l'hora en què es van publicar (hora local)."""
    d = dades or get(RODALIES)
    res = []
    for n in d["included"]:
        linies = {l.get("id") for l in n.get("lines") or []} - {None}
        text = n.get("description") or n.get("title") or {}
        textos = {k: " ".join((text.get(k) or "").split()) for k in ("ca", "es") if text.get(k)}
        if not linies or not textos:
            continue
        textos.setdefault("ca", textos.get("es"))
        textos.setdefault("es", textos.get("ca"))
        inici = None
        if n.get("date"):
            inici = dt.datetime.fromisoformat(f"{n['date']}T{(n.get('time') or '00:00:00')[:5]}").astimezone() \
                .isoformat(timespec="minutes")
        res.append({"linies": linies, "text": textos, "inici": inici, "fi": None, "font": "rodalies"})
    return res


def avisos_rodalies_o_renfe(errors):
    """Els de Rodalies; si la seva API no respon, els de Renfe, i es diu."""
    try:
        return avisos_rodalies()
    except Exception as ex:
        errors.append(f"avisos de Rodalies: {ex}")
        return avisos_renfe()


def prova(get_json=None):
    """Si l'API d'avisos de Rodalies respon amb el que cal. None si va bé; si no, per què."""
    try:
        d = (get_json or get)(RODALIES)
        if not isinstance(d.get("included"), list):
            return "no porta la llista d'avisos («included»)"
        for n in d["included"][:3]:
            if not {"date", "lines"} <= set(n) or not (n.get("description") or n.get("title")):
                return "els avisos no porten data, línies o text"
    except Exception as ex:
        return f"no respon: {ex}"
    return None


def comprova(marca, avisa=True, get_json=None):
    """La prova diària (aprenentatge.diari), com la dels talls de llum (ADR
    0072): l'API no és un servei documentat; si deixa de respondre o canvia, es
    diu un cop a Juanjo, i un altre quan torna (marca rodalies-falla).
    Mentrestant, la pàgina fa servir els avisos de Renfe."""
    import subprocess
    error = prova(get_json)
    text = None
    if error and not os.path.exists(marca):
        open(marca, "w").close()
        text = (f"Temps a Montflorit: l'API d'avisos de Rodalies ha deixat de funcionar ({error}). "
                "Mentrestant, els trens fan servir els avisos de Renfe, que poden anar endarrerits: mira trens.py.")
    elif not error and os.path.exists(marca):
        os.remove(marca)
        text = "Temps a Montflorit: l'API d'avisos de Rodalies torna a funcionar."
    if text:
        print(text)
        if avisa:
            subprocess.run(["avisar-juanjo", "--asunto", "meteo-local", text], check=False)
    return error


def trens_renfe(dades=None, ara=None):
    """Posicions dels trens de Renfe. Si el feed és de fa més de
    POSICIONS_VELLES_MIN minuts, no serveix: una resposta correcta no vol dir
    que sigui actual (auditoria del 08-10-2026)."""
    dades = dades or get(RENFE + "vehicle_positions.json")
    marca = (dades.get("header") or {}).get("timestamp")
    if marca:
        edat = ((ara or dt.datetime.now().astimezone()) - dt.datetime.fromtimestamp(int(marca), dt.timezone.utc))
        if edat > dt.timedelta(minutes=POSICIONS_VELLES_MIN):
            raise ValueError(f"posicions de fa {int(edat.total_seconds() // 60)} min")
    res = []
    for e in dades.get("entity", []):
        v = e.get("vehicle", {})
        linia = (v.get("vehicle", {}).get("label") or "").split("-")[0]
        p = v.get("position") or {}
        if linia and "latitude" in p:
            res.append({"id": "renfe-" + str(v.get("vehicle", {}).get("id")), "linia": linia,
                        "lat": p["latitude"], "lon": p["longitude"],
                        "aturat": v.get("currentStatus") == "STOPPED_AT"})
    return res


def avisos_fgc():
    fitxer = get(FGC + "alerts-gtfs_realtime/records?limit=1")["results"][0]["file"]["url"]
    res = []
    for a in avisos_pb(get(fitxer, binari=True)):
        # Els textos, mai traduïts: en català i castellà si n'hi ha; si no, el
        # que hi hagi, tal qual.
        textos = (idiomes(t for idioma, t in a["text"].items() if idioma in ("ca", "es", ""))
                  or idiomes(a["text"].values()))
        if a["rutes"] and textos:
            res.append({"linies": set(a["rutes"]), "text": textos, "inici": a.get("inici"), "fi": a.get("fi")})
    return res


def trens_fgc(linies):
    q = "lin in (" + ",".join(f"'{x}'" for x in linies) + ")"
    url = FGC + "posicionament-dels-trens/records?limit=100&where=" + urllib.request.quote(q)
    # «en_hora» (text «True» o «False»): si el tren va puntual (ADR 0079).
    en_hora = lambda v: None if v in (None, "") else str(v).lower() == "true"
    return [{"id": "fgc-" + r["id"], "linia": r["lin"], "lat": r["geo_point_2d"]["lat"],
             "lon": r["geo_point_2d"]["lon"], "aturat": bool(r.get("estacionat_a")), "en_hora": en_hora(r.get("en_hora"))}
            for r in get(url)["results"] if r.get("geo_point_2d")]


# Retards (ADR 0079): les dades d'FGC diuen si cada tren va en hora. Una
# línia surt «amb retard» si, dels trens vistos a prop de l'estació en els
# últims RETARD_MIN minuts, van tard com a mínim RETARD_TRENS_MIN i més que
# els puntuals: un sol tren no ho decideix (Juanjo, 12-10-2026). Renfe no ho
# dona: només les línies d'FGC.
RETARD_MIN = 30
RETARD_TRENS_MIN = 2


def puntualitat(registre, trens, ara):
    """Afegeix al registre {linia: {id: [hora, en_hora]}} els trens que diuen
    si van en hora i són a prop de l'estació de la seva línia, i treu els de fa
    més de RETARD_MIN minuts. Torna el registre nou."""
    nou = {l: {i: v for i, v in d.items()
               if ara - dt.datetime.fromisoformat(v[0]) <= dt.timedelta(minutes=RETARD_MIN)}
           for l, d in (registre or {}).items()}
    for t in trens:
        est = C.TRENS_ESTACIONS.get(t["linia"])
        if t.get("en_hora") is None or not est or km((t["lat"], t["lon"]), est) > C.TRENS_RADI_KM:
            continue
        nou.setdefault(t["linia"], {})[t["id"]] = [ara.isoformat(timespec="minutes"), t["en_hora"]]
    return {l: d for l, d in nou.items() if d}


def amb_retard(registre_linia):
    """Quants trens van tard, si la línia ha de sortir «amb retard»; si no, 0."""
    tard = sum(1 for _, en_hora in (registre_linia or {}).values() if en_hora is False)
    puntuals = sum(1 for _, en_hora in (registre_linia or {}).values() if en_hora is True)
    return tard if tard >= RETARD_TRENS_MIN and tard > puntuals else 0


def km(a, b):
    lat = math.radians((a[0] + b[0]) / 2)
    return 111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(lat))


def km_al_tram(p, a, b):
    """Distància (km) del punt p al tram recte entre a i b."""
    lat = math.radians(p[0])
    xy = lambda q: (111.2 * (q[1] - p[1]) * math.cos(lat), 111.2 * (q[0] - p[0]))
    (ax, ay), (bx, by) = xy(a), xy(b)
    dx, dy = bx - ax, by - ay
    f = max(0, min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy))) if dx or dy else 0
    return math.hypot(ax + f * dx, ay + f * dy)


def es_mouen(trens, abans, ara):
    """Els trens que es mouen a prop de l'estació de la seva línia: comparats
    amb la passada anterior si és recent; si no, els que no estan aturats.
    També els que hi han passat entre les dues passades: l'R8 fa un tren per
    hora i sentit, i cadascun és uns 12 minuts dins del radi; amb passades
    cada 15 minuts, un retard de pocs minuts el deixava sense veure i la
    línia sortia «Sense trens» amb l'avís «Circulació normalitzada» (Juanjo,
    13-10-2026)."""
    estacions = {linia: coord for linia, coord in C.TRENS_ESTACIONS.items()}
    recent = abans and ara - dt.datetime.fromisoformat(abans["hora"]) <= dt.timedelta(minutes=POSICIONS_MAX_MIN)
    res = []
    for t in trens:
        if t["linia"] not in estacions:
            continue
        ara_es, estacio = (t["lat"], t["lon"]), estacions[t["linia"]]
        antiga = recent and abans["posicions"].get(t["id"])
        if antiga:
            if (km(antiga, ara_es) * 1000 >= MOGUT_M
                    and km_al_tram(estacio, antiga, ara_es) <= C.TRENS_RADI_KM):
                res.append(t)
        elif not t["aturat"] and km(ara_es, estacio) <= C.TRENS_RADI_KM:
            res.append(t)
    return res


# Avisos que diuen com va el servei: per carretera o amb trens. Entre els
# propis d'una línia, mana el més recent d'aquests.
SERVEI = re.compile(r"carretera|circulaci[oó]n? (ferrovi|normali)|servei ferrovi|servicio ferrovi", re.I)
# Un avís que només diu que el servei és normal a tota la línia (Rodalies el
# publica quan es recupera): no és una incidència (ADR 0078). També
# «Circulació normalitzada» (13-10-2026, R8).
NORMAL = re.compile(r"^\s*((servei|circulaci[oó]n?|servicio) ferrovi\w* (a|en) (tot|todo) (el|su) (seu )?(recorregut|recorrido)"
                    r"|circulaci[oó]n? normali(tz|z)ada)\.?\s*$", re.I)


def vigent(a, ara):
    """Si l'avís és d'ara: ha començat (o no té data) i no ha acabat."""
    ara = ara.isoformat(timespec="minutes") if ara.tzinfo else ara.astimezone().isoformat(timespec="minutes")
    comparable = lambda t: dt.datetime.fromisoformat(t).astimezone().isoformat(timespec="minutes")
    return (not a.get("inici") or comparable(a["inici"]) <= ara) and (not a.get("fi") or comparable(a["fi"]) > ara)


def mes_nous_primer(avisos):
    """Del més recent al més vell; sense data, els últims."""
    return sorted(avisos, key=lambda a: a.get("inici") or "", reverse=True)


def dins_horari(linia, ara):
    """Si a aquesta hora la línia hauria de circular per Cerdanyola: des de
    TRENS_MARGE_INICI_MIN minuts després del seu primer tren fins a l'últim
    (config.TRENS_HORARI_LINIA). Abans o després, no veure'n cap és normal."""
    ini, fi = getattr(C, "TRENS_HORARI_LINIA", {}).get(linia, C.TRENS_HORARI)
    h, m = map(int, ini.split(":"))
    inici = f"{(h * 60 + m + C.TRENS_MARGE_INICI_MIN) // 60:02d}:{(h * 60 + m + C.TRENS_MARGE_INICI_MIN) % 60:02d}"
    return inici <= ara.strftime("%H:%M") < fi


def estat_linia(linia, mouen, vist, avisos, ara):
    """vist: última vegada que s'ha vist un tren de la línia movent-se a prop
    de l'estació (ISO), o None."""
    nomes = mes_nous_primer([a for a in avisos if a["linies"] == {linia}])
    propis = [a["text"] for a in nomes]
    generals = [a["text"] for a in mes_nous_primer([a for a in avisos if linia in a["linies"] and len(a["linies"]) > 1])]
    n = sum(t["linia"] == linia for t in mouen)
    circula = n > 0 or bool(vist and ara - dt.datetime.fromisoformat(vist)
                            <= dt.timedelta(minutes=C.TRENS_VIST_MIN))
    de_dia = dins_horari(linia, ara)
    # Si l'avís més nou que parla del servei té data, decideix ell; sense
    # dates, qualsevol avís propi de carretera (com fins ara). Només els
    # vigents: un avís que encara no ha començat o que ja ha acabat es mostra,
    # però no decideix (auditoria del 08-10-2026).
    carretera = lambda a: bool(re.search(r"carretera", a["text"]["ca"] + a["text"]["es"], re.I))
    # Els generals de Rodalies també decideixen: la seva API només porta els
    # vigents i al dia; els de Renfe, no, que s'hi quedaven avisos vells (ADR 0078).
    al_dia = mes_nous_primer([a for a in avisos if linia in a["linies"] and (a["linies"] == {linia} or a.get("font") == "rodalies")])
    servei = [a for a in al_dia if SERVEI.search(a["text"]["ca"] + a["text"]["es"]) and vigent(a, ara)]
    bus = (carretera(servei[0]) if servei[0].get("inici") else any(carretera(a) for a in servei)) if servei else False
    # Si l'avís de servei més nou diu que hi ha circulació ferroviària, mana
    # ell encara que no s'hagi vist cap tren: no es diu «sense trens», sinó
    # que hi ha incidències, i es diu la contradicció (Juanjo, 09-10-2026: la
    # R8 sortia «Sense trens» amb l'avís «Circulació ferroviària a tot el
    # recorregut»).
    ferroviari = bool(servei) and servei[0].get("inici") and not carretera(servei[0])
    no_vist = False
    if bus:
        estat = "bus"
    elif circula:
        incidencies = [t for t in propis + generals if not (NORMAL.match(t.get("ca") or "") or NORMAL.match(t.get("es") or ""))]
        estat = "incidencies" if incidencies else "circula"
    elif de_dia and ferroviari:
        estat, no_vist = "incidencies", True
    else:
        estat = "sense_trens" if de_dia else "fora_horari"
    # Dels avisos de servei vigents, només el més nou: els anteriors ja no
    # valen i, mostrats, es contradeien amb ell (Juanjo, 09-10-2026).
    antics = {id(a) for a in servei[1:]} if servei and servei[0].get("inici") else set()
    propis = [a["text"] for a in nomes if id(a) not in antics]
    # Primer el que és només d'aquesta línia; sense repetir textos.
    textos = []
    for t in propis + generals:
        if t not in textos:
            textos.append(t)
    res = {"estat": estat, "trens": n, "vist": vist if not n else ara.isoformat(timespec="minutes"),
           "avisos": textos[:2]}
    if no_vist:
        res["no_vist"] = True
    return res


def calcula(ara=None):
    """L'estat de cada línia de C.TRENS, per a les dades públiques. Al NAS
    (amb /estat) desa les posicions i quan s'ha vist circular cada línia, per
    a la passada següent."""
    ara = ara or dt.datetime.now().astimezone()
    try:
        with open(ESTAT, encoding="utf-8") as f:
            abans = json.load(f)
    except (OSError, ValueError):
        abans = None
    vistos = dict((abans or {}).get("vist") or {})
    registre_puntualitat = (abans or {}).get("puntualitat") or {}
    res = {"hora": ara.isoformat(timespec="minutes"), "linies": [], "errors": []}
    trens = []
    for operador, llegeix_avisos, llegeix_trens in (
            ("rodalies", lambda: avisos_rodalies_o_renfe(res["errors"]), trens_renfe),
            ("fgc", avisos_fgc, lambda: trens_fgc([l for l, o, _ in C.TRENS if o == "fgc"]))):
        try:
            avisos, tr = llegeix_avisos(), llegeix_trens()
        except Exception as ex:
            res["errors"].append(f"{operador}: {ex}")
            avisos, tr = None, []
        mouen = es_mouen(tr, abans, ara)
        trens += tr
        if operador == "fgc":
            registre_puntualitat = puntualitat(registre_puntualitat, tr, ara)
        for linia, op, estacio in C.TRENS:
            if op != operador:
                continue
            fila = {"linia": linia, "operador": op, "estacio": estacio}
            if avisos is None:
                fila.update({"estat": "sense_dades", "trens": 0, "avisos": []})
            else:
                fila.update(estat_linia(linia, mouen, vistos.get(linia), avisos, ara))
                if fila["vist"]:
                    vistos[linia] = fila["vist"]
                # Circula, però els trens van tard: «amb retard» (ADR 0079).
                tard = amb_retard(registre_puntualitat.get(linia)) if op == "fgc" else 0
                if fila["estat"] == "circula" and tard:
                    fila.update(estat="retard", trens_tard=tard)
            fila.pop("vist", None)
            res["linies"].append(fila)
    posicions = {t["id"]: (round(t["lat"], 5), round(t["lon"], 5)) for t in trens}
    if os.path.isdir(os.path.dirname(ESTAT)) and posicions:
        with open(ESTAT + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"hora": res["hora"], "posicions": posicions, "vist": vistos,
                       "puntualitat": registre_puntualitat}, f)
        os.replace(ESTAT + ".tmp", ESTAT)
    return res


if __name__ == "__main__":
    print(json.dumps(calcula(), ensure_ascii=False, indent=1))
