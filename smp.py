#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Los avisos de peligro de Meteocat (SMP) para el Vallès Occidental (ADR 0067).

Los planes de Protección Civil se activan para Cataluña o para unas comarcas,
según cada comunicado, y los datos abiertos no dicen cuáles (ADR 0066). Junto
a un plan activo se dice si Meteocat tiene un aviso de peligro para la
comarca del barrio, que es lo que le importa al vecino (Juanjo, 10-10-2026).

La API de Meteocat prohíbe difundir sus datos a terceros; las páginas
públicas de meteo.cat llevan los mismos avisos dentro, en la llamada
«Meteocat.avisosSMP({… avisos: [...] …})», y su aviso legal permite
reutilizar lo que publica en abierto sin alterarlo, citando la fuente y la
fecha (Llei 37/2007, la misma base que el radar, ADR 0019). Desde el
11-10-2026 se lee en cada pasada: sus avisos avisan como los de AEMET y van a
la página «Perill», también sin plan (ADR 0071).

Los avisos son episodios con la estructura de /smp/episodis-oberts de la API:
cada episodio, un meteoro; cada aviso, sus evoluciones por día, con las
franjas («00-06», «06-12», «12-18», «18-00») y las comarcas afectadas
(idComarca) y su grado de peligro. Como el mapa de meteo.cat, cuentan los
avisos vigentes que no son preavisos, y el grado de 1 a 6: 1-2 moderado,
3-4 alto, 5-6 muy alto (script.min.js de meteo.cat, _crearAvisosCombinatsLayer).
"""
import datetime as dt
import json
import re

import config as C

URL = "https://www.meteo.cat/prediccio/general"
DIES = {"ca": ("dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge"),
        "es": ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")}
GRAU = {"ca": {"mig": "moderat", "alt": "alt", "maxim": "molt alt"},
        "es": {"mig": "moderado", "alt": "alto", "maxim": "muy alto"}}
# «avís de perill», «avís d'observació de perill»: el de observación dice que
# el fenómeno ya ocurre.
NOM_TIPUS = {"ca": {"previsio": "avís", "observacio": "avís d'observació", "temps_violent": "avís d'observació"},
             "es": {"previsio": "aviso", "observacio": "aviso de observación", "temps_violent": "aviso de observación"}}


def nivell(perill):
    """El grado de Meteocat (1-6) en la escala de la página."""
    return "mig" if perill <= 2 else "alt" if perill <= 4 else "maxim"


def episodis(pagina):
    """Los episodios de la lista «avisos» de la llamada Meteocat.avisosSMP de una
    página de meteo.cat. Con avisos, la lista llega agrupada en bloques que
    repiten los mismos episodios (visto el 16-10-2026: [[…], […]], y la
    lectura falló hasta la 3.87.0); se aplana y cada episodio va una vez."""
    i = pagina.find("Meteocat.avisosSMP(")
    if i < 0:
        raise ValueError("la pàgina de Meteocat no porta els avisos")
    m = re.compile(r"\n\s*avisos:\s*(\[)").search(pagina, i)
    if not m:
        raise ValueError("la pàgina de Meteocat no porta la llista d'avisos")
    llista, _ = json.JSONDecoder().raw_decode(pagina, m.start(1))
    res, vistos = [], set()
    for ep in llista:
        for e in (ep if isinstance(ep, list) else [ep]):
            if not isinstance(e, dict):
                raise ValueError("la llista d'avisos de Meteocat té una forma desconeguda")
            clau = json.dumps(e, sort_keys=True)
            if clau not in vistos:
                vistos.add(clau)
                res.append(e)
    return res


def franja(nom):
    """«18-00» → (18, 24)."""
    a, b = (int(x) for x in nom.split("-"))
    return a, (24 if b == 0 else b)


def de_la_comarca(llista, comarca=None):
    """Los avisos que afectan a la comarca: [{meteor, tipus, llindar, perill,
    emissio, dies: {AAAA-MM-DD: [(inici, fi), …]}}], uno por aviso.

    tipus: «previsio» (el aviso de siempre, por franjas de seis horas),
    «observacio» o «temps_violent» (los que Meteocat emite cuando el fenómeno
    ya ocurre: «Avís Vigilància» y «Avís Vigilància per Temps Violent» en sus
    datos, con su hora de inicio y de fin y las comarcas en el propio aviso;
    script.min.js de meteo.cat, _calcularAfectacionsDelDiaAvis)."""
    comarca = comarca or C.SMP_COMARCA
    res, vistos = [], set()
    for ep in llista or []:
        meteor = ((ep.get("meteor") or {}).get("nom") or "").strip()
        for av in ep.get("avisos") or []:
            tipus_mc = (av.get("tipus") or "").strip()
            if (av.get("estat") or "").lower() != "vigent" or tipus_mc.lower().startswith("preav"):
                continue
            tipus = TIPUS.get(tipus_mc.lower(), "previsio")
            dies, perill, llindar = {}, 0, None
            if tipus == "previsio":
                for ev in av.get("evolucions") or []:
                    for per in ev.get("periodes") or []:
                        for af in per.get("afectacions") or []:
                            if int(af.get("idComarca") or 0) != comarca:
                                continue
                            dia = (af.get("dia") or ev.get("dia") or "")[:10]
                            dies.setdefault(dia, set()).add(franja(per["nom"]))
                            perill = max(perill, int(af.get("perill") or 0))
                            llindar = llindar or af.get("llindar") or ev.get("llindar1")
                dies = {d: junta(sorted(f)) for d, f in sorted(dies.items())}
            else:
                afs = [af for af in av.get("afectacions") or [] if int(af.get("idComarca") or 0) == comarca]
                if afs and av.get("dataInici") and av.get("dataFi"):
                    perill = max(int(af.get("perill") or 0) for af in afs)
                    llindar = next((af.get("llindar") for af in afs if af.get("llindar")), None)
                    dies = hores(av["dataInici"], av["dataFi"])
            clau = (meteor, tipus, av.get("dataEmisio"))
            if dies and perill and clau not in vistos:
                vistos.add(clau)
                res.append({"meteor": meteor or "Temps violent", "tipus": tipus, "llindar": llindar,
                            "perill": perill, "emissio": av.get("dataEmisio"), "dies": dies})
    return res


# Los tipos de aviso de Meteocat (script.min.js: TIPUS_OBSERVACIO y
# TIPUS_TEMPS_VIOLENT; «Avís d'Observació» y «Avís temps violent», los nombres
# que también acepta su lista).
TIPUS = {"avís vigilància": "observacio", "avís d'observació": "observacio",
         "avís vigilància per temps violent": "temps_violent", "avís temps violent": "temps_violent"}


def hores(inici, fi):
    """Un aviso de observación, de «2026-10-17T13:20Z» a «…T15:00Z», en
    franjas de hora local: {"2026-10-17": [(15, 17)]} (la hora de inicio, por
    abajo; la de fin, por arriba)."""
    t0 = dt.datetime.fromisoformat(inici.replace("Z", "+00:00")).astimezone()
    t1 = dt.datetime.fromisoformat(fi.replace("Z", "+00:00")).astimezone()
    res = {}
    t = t0.replace(minute=0, second=0, microsecond=0)
    while t < t1:
        f = min(t1, (t + dt.timedelta(days=1)).replace(hour=0))
        fi_h = 24 if f.date() > t.date() else f.hour + (1 if f.minute or f.second else 0)
        res.setdefault(t.date().isoformat(), []).append((t.hour, fi_h))
        t = (t + dt.timedelta(days=1)).replace(hour=0)
    return res


def junta(franges):
    """Las franjas seguidas, juntas: [(12, 18), (18, 24)] → [(12, 24)]."""
    res = []
    for a, b in franges:
        if res and res[-1][1] == a:
            res[-1] = (res[-1][0], b)
        else:
            res.append((a, b))
    return res


def hora_local(iso):
    """«2026-10-10T08:09Z» → «10:09» (hora de Montflorit)."""
    if not iso:
        return None
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return t.astimezone().strftime("%H:%M")


def quan(dies, idioma):
    """«dissabte 10 de 12 a 24 h i diumenge 11 de 0 a 6 h»."""
    de, i = ("de", "y") if idioma == "es" else ("de", "i")
    peces = []
    for dia, franges in dies.items():
        d = dt.date.fromisoformat(dia)
        hores = f" {i} ".join(f"{de} {a} a {b} h" for a, b in franges)
        peces.append(f"{DIES[idioma][d.weekday()]} {d.day} {hores}")
    return f" {i} ".join(peces)


def textos(avisos, hora):
    """Una línea por aviso, en catalán y castellano, con el meteoro y el umbral
    tal como los publica Meteocat (sin traducir: ADR 0067); sin avisos, que no
    hay ninguno, con la hora de la lectura."""
    nom = C.SMP_COMARCA_NOM
    if not avisos:
        return [{"nivell": "nul",
                 "ca": f"Meteocat no té cap avís de perill per al {nom} (dades de les {hora}).",
                 "es": f"Meteocat no tiene ningún aviso de peligro para el {nom} (datos de las {hora})."}]
    res = []
    for a in avisos:
        n = nivell(a["perill"])
        llindar = f"{a['llindar']}; " if a.get("llindar") else ""
        emes = hora_local(a.get("emissio"))
        tipus = a.get("tipus", "previsio")
        res.append({"nivell": n,
                    "ca": (f"Meteocat: {NOM_TIPUS['ca'][tipus]} de perill {GRAU['ca'][n]} per «{a['meteor']}» al {nom}, "
                           f"{quan(a['dies'], 'ca')} ({llindar}emès a les {emes})."),
                    "es": (f"Meteocat: {NOM_TIPUS['es'][tipus]} de peligro {GRAU['es'][n]} por «{a['meteor']}» en el {nom}, "
                           f"{quan(a['dies'], 'es')} ({llindar}emitido a las {emes}).")})
    return res


# --- Meteocat o AEMET, per fenomen (ADR 0093) ---------------------------------
# Meteocat, el servei d'aquí, mana; l'AEMET surt per a tot el que Meteocat no
# cobreix: un fenomen o unes hores sense avís de Meteocat, o si no es pot
# llegir (Juanjo, 16-10-2026: «si meteocat no tiene aviso y aemet sí, debe
# salir aemet, prima la información y seguridad de los usuarios»).

FENOMENS = (("violent", "temps_violent"), ("pluja", "pluja"), ("neu", "neu"), ("vent", "vent"),
            ("calor", "calor"), ("fred", "fred"), ("mar", "mar"))
NOM_FENOMEN = {"ca": {"pluja": "pluja", "neu": "neu", "vent": "vent", "calor": "calor", "fred": "fred",
                      "mar": "l'estat de la mar", "temps_violent": "temps violent"},
               "es": {"pluja": "lluvia", "neu": "nieve", "vent": "viento", "calor": "calor", "fred": "frío",
                      "mar": "el estado del mar", "temps_violent": "tiempo violento"}}
# Els tipus de l'AEMET que Meteocat també avisa; les tempestes, la boira o la
# pols no tenen avís propi a Meteocat i surten sempre de l'AEMET.
FENOMEN_AEMET = {"pluja": "pluja", "vent": "vent", "calor": "calor", "fred": "fred", "neu": "neu"}
COLOR = {"mig": "groc", "alt": "taronja", "maxim": "vermell"}


def fenomen(meteor):
    """«Intensitat de pluja en 30 minuts» → «pluja»."""
    m = (meteor or "").lower()
    return next((f for clau, f in FENOMENS if clau in m), m)


def hores_avis(a):
    """Les hores que cobreix un avís de Meteocat: {"AAAA-MM-DD:H", …}, hora local."""
    return {f"{d}:{h}" for d, franges in a["dies"].items() for i, fi in franges for h in range(i, fi)}


def hores_aemet(a):
    """Les hores que cobreix un avís de l'AEMET, en hora local."""
    t = dt.datetime.fromisoformat(a["inicio"]).astimezone().replace(minute=0, second=0, microsecond=0)
    fi = dt.datetime.fromisoformat(a["fin"]).astimezone()
    res = set()
    while t < fi:
        res.add(f"{t.date().isoformat()}:{t.hour}")
        t += dt.timedelta(hours=1)
    return res


def cobreix(avisos_smp, a):
    """Si Meteocat té avís del mateix fenomen en alguna hora de l'avís de
    l'AEMET a: llavors mana el de Meteocat."""
    f = FENOMEN_AEMET.get(a.get("tipo"))
    if not f:
        return False
    hores = hores_aemet(a)
    return any(fenomen(m["meteor"]) == f and hores & hores_avis(m) for m in avisos_smp or [])


def marca_coberts(avisos, smp):
    """Marca «cobert» els avisos de l'AEMET que cobreix Meteocat. Sense lectura
    de Meteocat (smp None), cap: surten tots."""
    for a in avisos or []:
        a.pop("cobert", None)
        if smp is not None and cobreix(smp.get("avisos"), a):
            a["cobert"] = "meteocat"
    return avisos


def per_hora(ini, fin, smp):
    """Els avisos de Meteocat d'un tram, com els de l'AEMET a la taula:
    [{nivell (groc, taronja, vermell), tipus: [fenomen], font}]."""
    res = {}
    hores = set()
    t = ini.astimezone().replace(minute=0, second=0, microsecond=0)
    while t < fin:
        hores.add(f"{t.date().isoformat()}:{t.hour}")
        t += dt.timedelta(hours=1)
    for a in (smp or {}).get("avisos") or []:
        if hores & hores_avis(a):
            c = COLOR[nivell(a["perill"])]
            res.setdefault(c, set()).add(fenomen(a["meteor"]))
    return [{"nivell": n, "tipus": sorted(t), "font": "meteocat"} for n, t in res.items()]


def per_fenomen(avisos):
    """Un element per fenomen, el resum que surt a la previsió del dia (ADR
    0093): {fenomen, nivell (el més alt), dies (totes les franges), ca, es}."""
    grups = {}
    for a in avisos:
        g = grups.setdefault(fenomen(a["meteor"]), {"perill": 0, "dies": {}})
        g["perill"] = max(g["perill"], a["perill"])
        for d, franges in a["dies"].items():
            g["dies"].setdefault(d, set()).update(tuple(f) for f in franges)
    nom = C.SMP_COMARCA_NOM
    res = []
    for f, g in sorted(grups.items(), key=lambda x: -x[1]["perill"]):
        n = nivell(g["perill"])
        nca, nes = NOM_FENOMEN["ca"].get(f, f), NOM_FENOMEN["es"].get(f, f)
        res.append({"fenomen": f, "nivell": n,
                    "dies": {d: [list(x) for x in junta(sorted(fr))] for d, fr in sorted(g["dies"].items())},
                    "ca": f"Avís de perill {GRAU['ca'][n]} de Meteocat per {nca} al {nom}",
                    "es": f"Aviso de peligro {GRAU['es'][n]} de Meteocat por {nes} en el {nom}"})
    return res


def llegeix(get, ahora):
    """Lo que se publica: {hora, avisos (los de la comarca), linies (los textos),
    fenomens (el resumen por fenómeno)}."""
    avisos = de_la_comarca(episodis(get(URL)))
    hora = ahora.strftime("%H:%M")
    return {"hora": ahora.isoformat(timespec="minutes"), "avisos": avisos, "linies": textos(avisos, hora),
            "fenomens": per_fenomen(avisos)}


def comprova(get, marca, avisa=True):
    """La prueba diaria (aprenentatge.diari): como la página no es una API, si
    deja de traer los avisos, o trae algo que no se sabe leer, se le dice una
    vez a Juanjo, y otra cuando vuelve. Desde la 3.87.0 lo mismo se mira en
    cada pasada (avisos_bot.py), con la misma marca, y se le dice en el momento."""
    try:
        de_la_comarca(episodis(get(URL)))
        error = None
    except Exception as ex:
        error = str(ex) or type(ex).__name__
    marca_falla(marca, error, avisa)
    return error


def marca_falla(marca, error, avisa=True):
    """Apunta si la lectura falla y se lo dice a Juanjo al empezar y al acabar
    el fallo, una sola vez cada cosa. Mientras falla, avisan los de AEMET
    (ADR 0092). Devuelve el texto enviado, o None."""
    import os
    text = None
    if error and not os.path.exists(marca):
        os.makedirs(os.path.dirname(marca) or ".", exist_ok=True)
        open(marca, "w").close()
        text = (f"Temps a Montflorit: no es poden llegir els avisos de perill de Meteocat ({error}). "
                "Mentrestant, els veïns reben els avisos de l'AEMET. Mira smp.py.")
    elif not error and os.path.exists(marca):
        os.remove(marca)
        text = "Temps a Montflorit: els avisos de perill de Meteocat es tornen a llegir."
    if text:
        print(text)
        if avisa:
            import avis_privat
            avis_privat.envia(text)
    return text
