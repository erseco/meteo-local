#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Los avisos públicos para el bot y el canal de Telegram (ADR 0034).

Tras cada cálculo (en el NAS o en la reserva de IONOS), mira los datos de casa
y decide qué avisos tocan para los vecinos, con su propio estado: el de los
avisos de Juanjo es otro. Los deja en avisos.json, que se sube a IONOS con
montflorit.json; allí el bot (bot/bot.py) los reparte a quien los haya elegido
y publica en el canal los importantes. Cada aviso lleva un identificador:
el bot no manda dos veces el mismo.

Tipos:
- pluja: llueve en Montflorit en unos 15 minutos, según el radar (la lógica
  de pluja_arriba.py, ADR 0022), un aviso por episodio de lluvia.
- perill: lo medido o previsto llega a los umbrales de aviso de AEMET (la de
  riscos.py, ADR 0018), al aparecer o subir de nivel; y, desde el 08-10-2026,
  un incendio forestal en curso que interesa al barrio (Bombers; desde el
  11-10-2026, en Collserola, en Cerdanyola o a 3 km en otro municipio del
  parque) al empezar y al dejar de constar (entorn.py, ADR 0046 y 0071).
- riera: riesgo de desbordamiento de la riera de Sant Cugat (la de riera.py,
  ADR 0027), atención y peligro, siempre con el aviso de que es orientativo.
- perill, también, desde el 09-10-2026: los avisos oficiales nuevos (ADR 0055).
  Un aviso de AEMET para el Prelitoral de Barcelona al aparecer o subir de
  nivel, y un plan de Protección Civil al pasar a alerta o a emergencia y
  cuando sale de ellas. La prealerta no avisa (ADR 0051).

- llum, desde el 11-10-2026: un corte de luz de e-distribución en el barrio
  (llum.py, ADR 0072), al aparecer y al dejar de constar, con la calle
  probable, que es una estimación. Sin nivel: 🔌. No es peligro: no va a
  «Perill».

Cada aviso de peligro y de la riera es parte de un episodio (episodi): el
historial de los últimos HISTORIAL_DIES días, con su comienzo y su final, va
en avisos.json para la página «Perill» de la web (ADR 0071).

Los trenes y el tráfico no avisan desde el 09-10-2026: se consultan en «Si
surts» y con /trens y /transit del bot (ADR 0053).

Uso: python3 avisos_bot.py CASA.json AVISOS.json [ANTERIOR]
     ANTERIOR: el avisos.json publicado (ruta o https), para unir su historial.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import unicodedata
import urllib.request

import config as C
import pluja_arriba as PA
import smp as SMP
import riera as RI
import riscos as RS

ESTAT = os.path.join(os.path.dirname(os.environ.get("REGISTRE_DIR", "/estat/registre")), "bot-avisos.json")
CONSERVA_H = 24          # avisos que se guardan en avisos.json
HISTORIAL_DIES = 366     # episodios de peligro de la página «Perill»: un año (ADR 0071)
# Más información de cada tipo de aviso, si su texto no lleva ya un enlace
# (ADR 0071).
BOMBERS = {"ca": "https://interior.gencat.cat/ca/arees_dactuacio/bombers/actuacions-de-bombers/",
           "es": "https://interior.gencat.cat/es/arees_dactuacio/bombers/actuacions-de-bombers/"}
PROTECCIO_CIVIL = {"ca": "https://interior.gencat.cat/ca/arees_dactuacio/proteccio_civil/",
                   "es": "https://interior.gencat.cat/es/arees_dactuacio/proteccio_civil/"}
AEMET = {"ca": "https://www.aemet.es/ca/eltiempo/prediccion/avisos?w=hoy&k=cat",
         "es": "https://www.aemet.es/es/eltiempo/prediccion/avisos?w=hoy&k=cat"}
METEOCAT = {"ca": "https://www.meteo.cat/prediccio/general", "es": "https://www.meteo.cat/prediccio/general"}
# El mapa de talls d'e-distribució centrat al barri (el mateix que /llum).
MAPA_LLUM = ("https://dpa-portalgis.enel.com/portal/apps/instant/basic/index.html"
             "?appid=21f5d825ceeb48dba6ef6ee97f840168&center=2.133,41.481&level=15&locale={}")
# Un tall d'una o dues cases no s'anuncia a tothom: es veu a «Llum» (ADR 0072).
LLUM_AVIS_CLIENTS_MIN = 3
# Los avisos que calcula la web, a su explicación con palabras corrientes en
# «Com funciona», en la lengua de quien lo lee; la metodología técnica se
# enlaza desde allí (Juanjo, 12-10-2026; ADR 0076).
ENLLAC_RIERA = {"ca": "https://meteo-montflorit.github.io/com-funciona.html#riera",
                "es": "https://meteo-montflorit.github.io/es/com-funciona.html#riera"}
ENLLAC_PROPI = {"ca": "https://meteo-montflorit.github.io/com-funciona.html#temps-extrem",
                "es": "https://meteo-montflorit.github.io/es/com-funciona.html#temps-extrem"}
WEB = "https://meteo-montflorit.github.io/"
# Corto: se lee en plena alerta; lo demás, en la explicación de «Com funciona»
# (Juanjo, 12-10-2026: «el texto de la alerta en sí ahora veo que es
# demasiado, condénsalo también»; ADR 0076).
ORIENTATIU = {
    "ca": "Avís en proves, orientatiu i no oficial.",
    "es": "Aviso en pruebas, orientativo y no oficial.",
}
NIVELLS_ES = {"groc": "amarillo", "taronja": "naranja", "vermell": "rojo"}
RISCOS_ES = {
    "pluja_1h": ("Lluvia muy fuerte prevista: hasta {v} mm en una hora, {q}.",
                 "Ahora llueve muy fuerte: {v} mm en la última hora."),
    "pluja_12h": ("Mucha lluvia prevista: {v} mm en 12 horas, {q}.",
                  "Ha llovido mucho: {v} mm en las últimas 12 horas."),
    "ratxa": ("Viento muy fuerte previsto: rachas de hasta {v} km/h, {q}.", None),
    "calor": ("Calor extremo previsto: hasta {v} °C, {q}.", "Ahora hace calor extremo: {v} °C."),
    "fred": ("Frío intenso previsto: hasta {v} °C, {q}.", "Ahora hace frío intenso: {v} °C."),
    "neu_24h": ("Nieve prevista: {v} cm en las próximas 24 horas.", None),
}


def coma(x):
    return f"{x:.0f}" if x >= 10 else f"{x:.1f}".replace(".", ",")


# --- Textos ------------------------------------------------------------------

# Cada aviso empieza por lo que pasa, en negrita (HTML de Telegram), y lo explica
# en palabras llanas para quien no conoce la web (Juanjo, 07-10-2026).
# Delante, el nivel con un círculo de color, la misma escala que el bot
# (bot/bot.py, CERCLE): se ve la gravedad antes de leer, también en la
# notificación del móvil (Juanjo, 10-10-2026; ADR 0065). El final, en verde.
# Lo que no tiene nivel lleva su propio símbolo, no un círculo: el incendio,
# 🔥 (Juanjo, 11-10-2026: «dejar los círculos para este tipo de niveles»; ADR 0071).
CERCLE = {"groc": "🟡", "taronja": "🟠", "vermell": "🔴", "atencio": "🟠", "perill": "🔴", "incendi": "🔥",
          "alerta": "🟠", "emergència": "🔴", "fi": "🟢", "llum": "🔌", "nul": "⚪", "mig": "🟡", "alt": "🟠", "maxim": "🔴"}


def negreta(text, nivell=None):
    cercle = CERCLE.get(nivell)
    return (f"{cercle} " if cercle else "") + f"<b>{html.escape(text, quote=False)}</b>"


def text_pluja(salida, ahora):
    r = salida["radar"]
    falta = round(PA.falta_min(salida, ahora))
    mm = r.get("arriba_mm_h")
    forca = {"ca": "", "es": ""}
    if mm is not None:
        forca = ({"ca": " Pot ser forta.", "es": " Puede ser fuerte."} if mm >= 4 else
                 {"ca": " Serà moderada.", "es": " Será moderada."} if mm >= 1 else
                 {"ca": " Serà feble.", "es": " Será débil."})
    if falta <= 2:
        ca = (negreta("Pluja imminent a Montflorit") + "\nEl radar ja veu pluja a sobre del barri: pot "
              "començar en qualsevol moment." + forca["ca"])
        es = (negreta("Lluvia inminente en Montflorit") + "\nEl radar ya ve lluvia encima del barrio: puede "
              "empezar en cualquier momento." + forca["es"])
    else:
        hora = dt.datetime.fromisoformat(r["arriba"]).strftime("%H:%M")
        ca = negreta(f"Pluja d'aquí a uns {falta} minuts") + (f"\nSegons el radar, començarà a ploure a "
                                                              f"Montflorit cap a les {hora}.") + forca["ca"]
        es = negreta(f"Lluvia dentro de unos {falta} minutos") + (f"\nSegún el radar, empezará a llover en "
                                                                 f"Montflorit hacia las {hora}.") + forca["es"]
    return amb_radar(ca, es, r)


def amb_radar(ca, es, r):
    """El radar en directe, el mateix que ha donat l'avís (Juanjo, 08-10-2026):
    a Telegram, un enllaç a l'última línia; a la notificació, que no admet
    enllaços al text, en tocar-la (bot/push.py llegeix «url» i «push»)."""
    font = "rainviewer" if r.get("imatge") == "rainviewer" else "meteocat"
    url = C.RADAR_EN_DIRECTE[font]
    nom = {"rainviewer": "RainViewer", "meteocat": "Meteocat"}[font]
    enllac = f'<a href="{html.escape(url)}">{nom}</a>'
    return {"ca": f"{ca}\nRadar en directe: {enllac}", "es": f"{es}\nRadar en directo: {enllac}", "url": url,
            "push": {"ca": f"{ca} Toca per veure el radar.", "es": f"{es} Toca para ver el radar."}}


def quan_es(r, ahora):
    ini, fin = dt.datetime.fromisoformat(r["des_de"]), dt.datetime.fromisoformat(r["fins"])
    dia = ("hoy" if ini.date() == ahora.date() else
           "mañana" if ini.date() == ahora.date() + dt.timedelta(days=1) else ini.strftime("%d/%m"))
    return f"{dia} de {ini.hour} a {fin.hour} h"


QUE_CA = {"pluja_1h": "pluja molt forta", "pluja_12h": "molta pluja", "ratxa": "vent molt fort",
          "calor": "calor extrema", "fred": "fred intens", "neu_24h": "neu"}
QUE_ES = {"pluja_1h": "lluvia muy fuerte", "pluja_12h": "mucha lluvia", "ratxa": "viento muy fuerte",
          "calor": "calor extremo", "fred": "frío intenso", "neu_24h": "nieve"}


def linia_risc_es(r, ahora):
    """El text d'un risc en castellà (el català ja ve fet a les dades)."""
    previst, mesura = RISCOS_ES[r["tipus"]]
    plantilla = previst if r["origen"] == "previsio" else mesura
    if not plantilla:
        return r["text"]
    return plantilla.format(v=RS.num(r["valor"]), q=quan_es(r, ahora) if r.get("des_de") else "")


def text_perill(nous, ahora):
    pitjor = max(nous, key=lambda r: RS.NIVELLS.index(r["nivell"]))["nivell"]
    tipus = list(dict.fromkeys(r["tipus"] for r in nous))
    ca = [negreta(f"Avís de perill a Montflorit ({pitjor}): " + " i ".join(QUE_CA[t] for t in tipus), pitjor)]
    ca += [html.escape(r["text"], quote=False) for r in nous]
    ca.append("Calculat per aquesta web, no oficial.")
    es = [negreta(f"Aviso de peligro en Montflorit ({NIVELLS_ES[pitjor]}): " + " y ".join(QUE_ES[t] for t in tipus), pitjor)]
    es += [html.escape(linia_risc_es(r, ahora), quote=False) for r in nous]
    es.append("Calculado por esta web, no oficial.")
    return {"ca": "\n".join(ca), "es": "\n".join(es)}, pitjor


def text_perill_fi():
    """Ja no queda cap risc: el mateix que rebia abans només Juanjo (Juanjo,
    08-10-2026), perquè qui ha rebut l'avís sàpiga que ha passat."""
    h = C.RISC_FI_H
    ca = (negreta("Ja no hi ha cap situació de perill a Montflorit", "fi") +
          f"\nFa {h} hores que no se'n mesura ni se'n preveu cap. Si n'hi torna a haver, hi haurà un avís nou.")
    es = (negreta("Ya no hay ninguna situación de peligro en Montflorit", "fi") +
          f"\nHace {h} horas que no se mide ni se prevé ninguna. Si vuelve a haberla, habrá un aviso nuevo.")
    return {"ca": ca, "es": es}


def text_riera(riera, nivell):
    """Primer què cal fer; després, la pluja de Sant Cugat i si el radar en veu
    venir més (ADR 0076). El detall, a la fitxa i a «Com funciona»."""
    hora = dt.datetime.fromisoformat(riera["fins"]).strftime("%H:%M")
    mm3 = coma(riera["mm_3h"])
    radar = riera.get("radar_1h")
    mes_ca = " i el radar en veu venir més" if radar and radar >= 1 else ""
    mes_es = " y el radar ve venir más" if radar and radar >= 1 else ""
    if nivell == "perill":
        ca = (negreta("Perill de desbordament de la riera de Sant Cugat a Montflorit", nivell) +
              f"\nNo t'acostis a la riera.\n{mm3} mm en 3 hores a Sant Cugat (a les {hora}){mes_ca}: "
              "amb aquesta pluja ja s'ha desbordat altres vegades.")
        es = (negreta("Peligro de desbordamiento de la riera de Sant Cugat en Montflorit", nivell) +
              f"\nNo te acerques a la riera.\n{mm3} mm en 3 horas en Sant Cugat (a las {hora}){mes_es}: "
              "con esta lluvia ya se ha desbordado otras veces.")
    else:
        ca = (negreta("Atenció: possible desbordament de la riera de Sant Cugat", nivell) +
              f"\nNo t'acostis a la riera.\n{mm3} mm en 3 hores a Sant Cugat (a les {hora}){mes_ca}: "
              "si continua plovent fort, es pot desbordar.")
        es = (negreta("Atención: posible desbordamiento de la riera de Sant Cugat", nivell) +
              f"\nNo te acerques a la riera.\n{mm3} mm en 3 horas en Sant Cugat (a las {hora}){mes_es}: "
              "si sigue lloviendo fuerte, se puede desbordar.")
    if riera.get("incomplet"):
        ca += " A l'estació li falten mesures: pot haver plogut més."
        es += " A la estación le faltan medidas: puede haber llovido más."
    return {"ca": f"{ca}\n{ORIENTATIU['ca']}", "es": f"{es}\n{ORIENTATIU['es']}"}


def text_riera_fi(riera, episodi):
    """Final d'un episodi amb avís (Juanjo, 08-10-2026): un sol missatge, i
    només després de RIERA_FI_H hores per sota del registre. Curt (ADR 0076)."""
    h = C.RIERA_FI_H
    perill = bool(episodi["avisos"].get("perill"))
    ca = (negreta("Riera de Sant Cugat: " + ("ha passat el perill de desbordament" if perill else "ja no hi ha risc de desbordament"), "fi")
          + f"\nFa {h} hores que no plou fort a Sant Cugat. Si hi torna, tornarà l'avís.")
    es = (negreta("Riera de Sant Cugat: " + ("ha pasado el peligro de desbordamiento" if perill else "ya no hay riesgo de desbordamiento"), "fi")
          + f"\nLleva {h} horas sin llover fuerte en Sant Cugat. Si vuelve, volverá el aviso.")
    return {"ca": ca, "es": es}


# --- Incendios cerca (ADR 0046) ---------------------------------------------------
# Van con los de peligro («Situacions de perill»): son datos oficiales de
# Bombers, y se dice de dónde salen.

def hhmm(iso):
    return dt.datetime.fromisoformat(iso).strftime("%H:%M") if iso else "?"


def lloc_incendi(i, idioma):
    """Dónde es, para quien no conoce la web (ADR 0066 y 0071): dentro del
    parque de Collserola o el municipio, y siempre a qué distancia de
    Montflorit (Juanjo, 11-10-2026: «tiene que poner la distancia a
    Montflorit, siempre»)."""
    m = i.get("municipi") or "?"
    ca = idioma == "ca"
    if i.get("collserola"):
        on = f"dins del Parc de Collserola ({m})" if ca else f"dentro del Parque de Collserola ({m})"
    else:
        on = f"a {m}" if ca else f"en {m}"
    if i.get("km") is not None:
        on += f", a {coma(i['km'])} km de Montflorit"
    return on


def enllac_bombers(idioma):
    text = "Mapa d'actuacions de Bombers" if idioma == "ca" else "Mapa de actuaciones de Bombers"
    return f'<a href="{BOMBERS[idioma]}">{text}</a>'


def text_incendi(i, acabat=False):
    """La distancia va en el título, que es lo que se ve en la notificación y
    en la ficha plegada de «Perill»; el texto ya no la repite."""
    lloc = i.get("municipi") or "?"
    parc_ca = ", dins del Parc Natural de Collserola" if i.get("collserola") else ""
    parc_es = ", dentro del Parque Natural de Collserola" if i.get("collserola") else ""
    if acabat:
        dist = f", a {coma(i['km'])} km de Montflorit" if i.get("km") is not None else ""
        on_ca = (f"al Parc de Collserola ({lloc})" if i.get("collserola") else f"a {lloc}") + dist
        on_es = (f"en el Parque de Collserola ({lloc})" if i.get("collserola") else f"en {lloc}") + dist
        return {"ca": negreta(f"Incendi {on_ca}: ja no consta com a actiu", "fi")
                      + "\nBombers de la Generalitat ja no el tenen entre les actuacions en curs.",
                "es": negreta(f"Incendio {on_es}: ya no consta como activo", "fi")
                      + "\nBombers de la Generalitat ya no lo tienen entre las actuaciones en curso."}
    return {"ca": negreta(f"Incendi forestal {lloc_incendi(i, 'ca')}", "incendi")
                  + f"\nBombers de la Generalitat treballen en un incendi de vegetació forestal a {lloc}{parc_ca}, "
                  f"des de les {hhmm(i.get('inici'))}. Segueix les indicacions de Bombers i de Protecció Civil."
                  + "\n" + enllac_bombers("ca"),
            "es": negreta(f"Incendio forestal {lloc_incendi(i, 'es')}", "incendi")
                  + f"\nBombers de la Generalitat trabajan en un incendio de vegetación forestal en {lloc}{parc_es}, "
                  f"desde las {hhmm(i.get('inici'))}. Sigue las indicaciones de Bombers y de Protección Civil."
                  + "\n" + enllac_bombers("es")}


# --- Cortes de luz (ADR 0072) ----------------------------------------------------

def on_llum(t, idioma):
    """«Carrer de Sant Jeroni o Carrer de Casanovas (carrers probables)», o
    «al barri» si no hay calle cerca."""
    es = idioma == "es"
    c = t.get("carrers") or []
    if not c:
        return "en el barrio" if es else "al barri"
    cap = (("calle probable" if es else "carrer probable") if len(c) == 1
           else ("calles probables" if es else "carrers probables"))
    return f"{' o '.join(c)} ({cap})"


def text_llum(t, ahora, acabat=False):
    nota = {"ca": "Els carrers són una estimació a partir del punt aproximat del mapa: e-distribució no diu quins "
                  "carrers queden sense llum.",
            "es": "Las calles son una estimación a partir del punto aproximado del mapa: e-distribución no dice qué "
                  "calles se quedan sin luz."}
    if acabat:
        return {"ca": negreta(f"Tall de llum a Montflorit, {on_llum(t, 'ca')}: ja no consta", "fi")
                      + "\ne-distribució ja no el té entre els talls en curs.",
                "es": negreta(f"Corte de luz en Montflorit, {on_llum(t, 'es')}: ya no consta", "fi")
                      + "\ne-distribución ya no lo tiene entre los cortes en curso."}
    n = t.get("clients")
    res = {}
    for idioma in ("ca", "es"):
        es = idioma == "es"
        que = (("Trabajos programados" if es else "Treballs programats") if t.get("programat")
               else ("Avería" if es else "Avaria"))
        qui = "" if n is None else (f": {n} clientes sin luz" if es else f": {n} clients sense llum") if n != 1 \
            else (": 1 cliente sin luz" if es else ": 1 client sense llum")
        quan = ""
        if t.get("fins"):
            h = dt.datetime.fromisoformat(t["fins"]).astimezone(ahora.tzinfo).strftime("%H:%M")
            quan = f"; previsto hasta las {h}" if es else f"; previst fins a les {h}"
        mapa = ("Mapa de e-distribución" if es else "Mapa d'e-distribució")
        res[idioma] = (negreta(f"{'Corte de luz en Montflorit' if es else 'Tall de llum a Montflorit'}: "
                               f"{on_llum(t, idioma)}", "llum")
                       + f"\n{que} de e-distribución{qui}{quan}." if es else
                       negreta(f"Tall de llum a Montflorit: {on_llum(t, idioma)}", "llum")
                       + f"\n{que} d'e-distribució{qui}{quan}.")
        res[idioma] += f"\n<i>{nota[idioma]}</i>\n" + f'<a href="{html.escape(MAPA_LLUM.format(idioma))}">{mapa}</a>'
    return res


# --- Avisos oficiales nuevos (ADR 0055) -------------------------------------------
# Van con los de peligro: llegan al canal y a quien tiene «Situacions de perill».

FASES_PLA = ("prealerta", "alerta", "emergència")
DIES = {"ca": ("dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge"),
        "es": ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")}
TIPUS_AEMET = {"ca": {"pluja": "pluja", "tempestes": "tempestes"}, "es": {"pluja": "lluvia", "tempestes": "tormentas"}}
NOM_PLA_ES = {"d'inundacions": "de inundaciones", "de vent": "de viento", "de neu": "de nieve",
              "per onada de calor": "por ola de calor", "per onada de fred": "por ola de frío",
              "per contaminació": "por contaminación", "per vent": "por viento"}
SENTIT_FASE = {
    "ca": {"alerta": "El pla està activat: es preveu un risc important a curt termini, o hi ha afectacions que no són greus.",
           "emergència": "El pla està activat per un risc greu per a la població: segueix les indicacions de Protecció Civil."},
    "es": {"alerta": "El plan está activado: se prevé un riesgo importante a corto plazo, o hay afectaciones que no son graves.",
           "emergència": "El plan está activado por un riesgo grave para la población: sigue las indicaciones de Protección Civil."}}


def moment(iso, ahora):
    """(dia, hora) d'un instant; les 23:59:59 compten com la mitjanit següent."""
    t = dt.datetime.fromisoformat(iso).astimezone(ahora.tzinfo)
    if t.second == 59:
        t += dt.timedelta(seconds=1)
    return t, (t.date() - ahora.date()).days


def nom_dia(t, dies, idioma):
    es = idioma == "es"
    return (("hoy" if es else "avui") if dies == 0 else ("mañana" if es else "demà") if dies == 1
            else DIES[idioma][t.weekday()])


def franja(inici, fi, ahora, idioma):
    """«Des d'avui a les 15 h fins a mitjanit.», «Desde mañana a las 6 h hasta el
    sábado a las 3 h.»"""
    es = idioma == "es"
    t0, d0 = moment(inici, ahora)
    t1, d1 = moment(fi, ahora)
    dia0 = nom_dia(t0, d0, idioma)
    if d1 == d0:                                     # el mateix dia
        return (f"{dia0.capitalize()}, de las {t0.hour} h a las {t1.hour} h." if es
                else f"{dia0.capitalize()}, de les {t0.hour} h a les {t1.hour} h.")
    if t1.hour == 0 and t1.minute == 0 and d1 == d0 + 1:
        fins = "hasta medianoche" if es else "fins a mitjanit"
    else:
        dia1 = nom_dia(t1, d1, idioma)
        fins = (f"hasta {'el ' if d1 > 1 else ''}{dia1} a las {t1.hour} h" if es
                else f"fins {dia1} a les {t1.hour} h")
    if es:
        return f"Desde {'el ' if d0 > 1 else ''}{dia0} a las {t0.hour} h {fins}."
    de = "d'" if dia0[:1] in "aeiouàèéíòóú" else "de "
    return f"Des {de}{dia0} a les {t0.hour} h {fins}."


def text_aemet(a, ahora):
    """Un aviso de AEMET: nivel, de qué, de cuándo a cuándo y su texto (en
    castellano, como lo publica AEMET: ADR 0033)."""
    nivell = a["nivel"]
    desc = f"\n«{html.escape(a['descripcio'], quote=False)}»" if a.get("descripcio") else ""
    ca = (negreta(f"Avís {nivell} de l'AEMET per {TIPUS_AEMET['ca'].get(a['tipo'], a['tipo'])} al Vallès", nivell)
          + "\n" + franja(a["inicio"], a["fin"], ahora, "ca") + desc
          + "\nÉs un avís oficial: segueix les indicacions de Protecció Civil.")
    es = (negreta(f"Aviso {NIVELLS_ES.get(nivell, nivell)} de la AEMET por {TIPUS_AEMET['es'].get(a['tipo'], a['tipo'])} "
                  f"en el Vallès", nivell)
          + "\n" + franja(a["inicio"], a["fin"], ahora, "es") + desc
          + "\nEs un aviso oficial: sigue las indicaciones de Protección Civil.")
    return {"ca": ca, "es": es}


def clau_smp(a):
    """Un aviso de Meteocat: el meteoro y su primer día (cada nueva emisión
    del mismo aviso no es un aviso nuevo)."""
    return f"{a['meteor']}:{min(a['dies'])}"


def fins_smp(a):
    """Hasta cuándo vale: el final de su última franja, en hora local."""
    dia = max(a["dies"])
    fi = a["dies"][dia][-1][1]
    t = dt.datetime.fromisoformat(dia) + dt.timedelta(hours=fi)
    return t.astimezone().isoformat(timespec="minutes")


def text_meteocat(a):
    """Un aviso de peligro de Meteocat para la comarca, sin plan de Protecció
    Civil (ADR 0071). El meteoro y el umbral, como los publica Meteocat (ADR 0067)."""
    n = SMP.nivell(a["perill"])
    nom = C.SMP_COMARCA_NOM
    llindar_ca = f" ({a['llindar']})" if a.get("llindar") else ""
    ca = (negreta(f"Avís de perill {SMP.GRAU['ca'][n]} de Meteocat per «{a['meteor']}» al {nom}", n)
          + f"\n{SMP.quan(a['dies'], 'ca').capitalize()}{llindar_ca}."
          + "\nÉs un avís oficial: segueix les indicacions de Protecció Civil.")
    es = (negreta(f"Aviso de peligro {SMP.GRAU['es'][n]} de Meteocat por «{a['meteor']}» en el {nom}", n)
          + f"\n{SMP.quan(a['dies'], 'es').capitalize()}{llindar_ca}."
          + "\nEs un aviso oficial: sigue las indicaciones de Protección Civil.")
    return {"ca": ca, "es": es}


def text_smp(smp, idioma):
    """Si Meteocat té avís de perill per a la comarca (smp.py, ADR 0067)."""
    return "".join(f"\n{CERCLE.get(l.get('nivell'), '')} {html.escape(l[idioma], quote=False)}".replace("\n ", "\n")
                   for l in (smp or {}).get("linies") or [])


def text_pla(p, acabat=False, smp=None):
    nom_ca, nom_es = p["nom"], NOM_PLA_ES.get(p["nom"], p["nom"])
    if acabat:
        return {"ca": negreta(f"Protecció Civil: el pla {nom_ca} ({p['pla']}) ja no està en alerta", "fi")
                      + "\nJa no consta en alerta ni en emergència.",
                "es": negreta(f"Protección Civil: el plan {nom_es} ({p['pla']}) ya no está en alerta", "fi")
                      + "\nYa no consta en alerta ni en emergencia."}
    de = "d'" if p["fase"][:1] in "aeiouàèéíòóú" else "de "
    fase_es = {"emergència": "emergencia"}.get(p["fase"], p["fase"])
    enllac_ca = f"\n<a href=\"{html.escape(p['comunicat'])}\">Comunicat (PDF)</a>" if p.get("comunicat") else ""
    enllac_es = enllac_ca.replace("Comunicat (PDF)", "Comunicado (PDF)")
    return {"ca": negreta(f"Protecció Civil: pla {nom_ca} ({p['pla']}) en fase {de}{p['fase']}", p["fase"])
                  + "\n" + SENTIT_FASE["ca"][p["fase"]] + text_smp(smp, "ca") + enllac_ca,
            "es": negreta(f"Protección Civil: plan {nom_es} ({p['pla']}) en fase de {fase_es}", p["fase"])
                  + "\n" + SENTIT_FASE["es"][p["fase"]] + text_smp(smp, "es") + enllac_es}


# --- Decidir -----------------------------------------------------------------

def decideix(estat, salida, ahora):
    """Pone al día el estado y devuelve los avisos nuevos:
    [{id, tipus, nivell, ca, es, hora}]."""
    nous = []
    hora = ahora.isoformat(timespec="minutes")

    def afegeix(tipus, clau, text, nivell=None, episodi=None, enllac=None, fins=None):
        # episodi: de qué suceso es parte, para el historial (ADR 0071); enllac,
        # más información si el texto no la enlaza; fins, cuándo acaba un
        # aviso que no tiene mensaje de final (los de AEMET).
        extra = {k: v for k, v in (("episodi", episodi), ("enllac", enllac), ("fins", fins)) if v}
        nous.append({"id": f"{tipus}:{clau}", "tipus": tipus, "nivell": nivell, "hora": hora, **text, **extra})

    # Lluvia en unos minutos: la lógica del aviso de Juanjo, con estado propio.
    try:
        avis, _ = PA.compara(estat.setdefault("pluja", {"episodi": None}), salida, ahora)
        if avis:
            afegeix("pluja", estat["pluja"]["episodi"]["inici"], text_pluja(salida, ahora))
    except Exception:
        pass
    # Peligro: al aparecer o subir de nivel.
    actius = estat.setdefault("perill", {})
    nous_perill = []
    for r in salida.get("riscos") or []:
        abans = actius.get(r["clau"])
        if not abans or RS.NIVELLS.index(r["nivell"]) > RS.NIVELLS.index(abans["nivell"]):
            nous_perill.append(r)
            actius[r["clau"]] = {"nivell": r["nivell"]}
        actius[r["clau"]]["vist"] = hora
    # Sin previsión o sin estación no se ha podido mirar: el riesgo no caduca,
    # para no repetirlo al canal cuando vuelvan los datos.
    sense = not salida.get("hores") or not salida.get("ara")
    acabats = []
    for clau, a in list(actius.items()):
        if not sense and ahora - dt.datetime.fromisoformat(a["vist"]) >= dt.timedelta(hours=C.RISC_FI_H):
            acabats.append(clau)
            del actius[clau]
    if nous_perill:
        text, pitjor = text_perill(nous_perill, ahora)
        afegeix("perill", hora + ":" + ",".join(r["clau"] for r in nous_perill), text, pitjor,
                episodi="propi", enllac=ENLLAC_PROPI)
    elif acabats and not actius:
        # Quan ja no en queda cap, es diu (abans, només a Juanjo).
        afegeix("perill", hora + ":fi", text_perill_fi(), "fi", episodi="propi")
    # Incendios forestales cerca (ADR 0046). La primera vez solo se apunta lo
    # que hay: lo que ya estaba no es una novedad.
    entorn = salida.get("entorn") or {}
    e = estat.get("entorn")
    if entorn.get("incendis") is not None:
        ara_ids = {i["id"]: i for i in entorn["incendis"]}
        if e is not None:
            for i in entorn["incendis"]:
                if i["id"] not in e["incendis"]:
                    afegeix("perill", f"incendi:{i['id']}", text_incendi(i), "incendi", episodi=f"incendi:{i['id']}")
            for iid, i in e["incendis"].items():
                if iid not in ara_ids:
                    afegeix("perill", f"incendi:{iid}:fi", text_incendi(i, acabat=True), "fi", episodi=f"incendi:{iid}")
        estat.setdefault("entorn", {"incendis": {}})["incendis"] = ara_ids
    # Cortes de luz del barrio (ADR 0072): al aparecer y al dejar de constar. La
    # primera vez solo se apunta lo que hay; si e-distribución no responde
    # (None), no se toca el estado.
    llum = salida.get("llum")
    if llum is not None:
        ara_talls = {t["id"]: t for t in llum.get("talls") or []
                     if (t.get("clients") or 0) >= LLUM_AVIS_CLIENTS_MIN}
        abans = estat.get("llum")
        if abans is not None:
            for k, t in ara_talls.items():
                if k not in abans:
                    afegeix("llum", k, text_llum(t, ahora), "llum")
            for k, t in abans.items():
                if k not in ara_talls:
                    afegeix("llum", f"{k}:fi", text_llum(t, ahora, acabat=True), "fi")
        estat["llum"] = ara_talls
    # Avisos oficiales nuevos (ADR 0055). La primera vez solo se apunta lo que
    # hay; si una fuente ha fallado (None), no se toca: no es que se acabe.
    of = estat.get("oficials")
    nou_of = {"aemet": dict((of or {}).get("aemet") or {}), "plans": dict((of or {}).get("plans") or {})}
    if of is not None and "smp" in of:
        nou_of["smp"] = dict(of["smp"])
    if salida.get("avisos") is not None:
        aemet = {f"{a['tipo']}:{a['inicio']}": a for a in salida["avisos"]
                 if a.get("zona", C.ZONA_AVISOS) == C.ZONA_AVISOS and a["nivel"] in RS.NIVELLS}
        if of is not None:
            for k, a in aemet.items():
                abans = of["aemet"].get(k)
                if abans is None or RS.NIVELLS.index(a["nivel"]) > RS.NIVELLS.index(abans):
                    afegeix("perill", f"aemet:{k}:{a['nivel']}", text_aemet(a, ahora), a["nivel"],
                            episodi=f"aemet:{k}", enllac=AEMET, fins=a.get("fin"))
        nou_of["aemet"] = {k: a["nivel"] for k, a in aemet.items()}
    # Los avisos de peligro de Meteocat para la comarca, como los de AEMET: al
    # aparecer o subir de grado (ADR 0071). La primera vez, solo se apuntan.
    if salida.get("smp") is not None:
        smp = {clau_smp(a): a for a in salida["smp"].get("avisos") or []}
        if of is not None and "smp" in of:
            for k, a in smp.items():
                abans = of["smp"].get(k)
                if abans is None or a["perill"] > abans:
                    afegeix("perill", f"meteocat:{k}:{a['perill']}", text_meteocat(a), SMP.nivell(a["perill"]),
                            episodi=f"meteocat:{k}", enllac=METEOCAT, fins=fins_smp(a))
        nou_of["smp"] = {k: a["perill"] for k, a in smp.items()}
    elif of is not None and "smp" in of:
        nou_of["smp"] = of["smp"]
    if salida.get("plans") is not None:
        actius = ("alerta", "emergència")
        plans = {p["pla"]: p for p in salida["plans"] if p.get("fase") in actius}
        # Los ocultos por no tener motivo meteorológico (ADR 0062) siguen
        # activos: ocultarlos no es un final, y si vuelven a mostrarse en la
        # misma fase no son nuevos. Al desactivarse uno oculto no se avisa:
        # ya no se estaba mostrando.
        ocults = {p["pla"]: p for p in salida.get("plans_ocults") or [] if p.get("fase") in actius}
        if of is not None:
            for k, p in plans.items():
                abans = (of["plans"].get(k) or {}).get("fase")
                if abans is None or FASES_PLA.index(p["fase"]) > FASES_PLA.index(abans):
                    afegeix("perill", f"pla:{k}:{p['fase']}:{hora}", text_pla(p, smp=salida.get("smp")), "pc",
                            episodi=f"pla:{k}", enllac=None if p.get("comunicat") else PROTECCIO_CIVIL)
            for k, p in of["plans"].items():
                if k not in plans and k not in ocults and not p.get("ocult"):
                    afegeix("perill", f"pla:{k}:fi:{hora}", text_pla({**p, "pla": k}, acabat=True), "fi",
                            episodi=f"pla:{k}")
        nou_of["plans"] = {k: {"fase": p["fase"], "nom": p["nom"], **({"ocult": True} if k in ocults else {})}
                           for k, p in {**ocults, **plans}.items()}
    estat["oficials"] = nou_of
    # Riera: atención y peligro, una vez cada nivel por episodio.
    riera = salida.get("riera")
    if riera:
        e = estat.setdefault("riera", {"episodi": None})
        episodi_abans = e.get("episodi")
        abans = set((episodi_abans or {}).get("avisos", {}))
        RI.compara(e, riera, ahora)
        despres = (e.get("episodi") or {}).get("avisos", {})
        for nivell in ("perill", "atencio"):
            if nivell in despres and nivell not in abans:
                afegeix("riera", f"{e['episodi']['inici']}:{nivell}", text_riera(riera, nivell), nivell,
                        episodi=f"riera:{e['episodi']['inici']}", enllac=ENLLAC_RIERA)
                break
        # L'episodi s'ha tancat (3 hores de calma) després d'un avís: es diu que ha passat.
        if episodi_abans and not e.get("episodi") and abans:
            afegeix("riera", f"{episodi_abans['inici']}:fi", text_riera_fi(riera, episodi_abans), "fi",
                    episodi=f"riera:{episodi_abans['inici']}")
    # Los avisos de trenes y de cortes ya no existen (ADR 0053): fuera su estado.
    estat.pop("trens", None)
    estat.pop("talls", None)
    return nous


# --- Historial (ADR 0071) -----------------------------------------------------
# Los avisos de peligro y de la riera agrupados por suceso: una entrada con
# su comienzo y, si ya ha acabado, su final. Para la página «Perill».

RANG = {"🟡": 1, "🟠": 2, "🔴": 3}


def rang(nivell):
    return RANG.get(CERCLE.get(nivell), 0)


def fusiona(propi, altre):
    """El historial propio con el último publicado (anterior): el NAS y la
    reserva de IONOS llevan estados distintos, y el que vuelve a publicar no
    puede borrar lo que el otro vio mientras tanto. Un suceso es el mismo si
    coinciden clave y comienzo; si uno de los dos ya lo da por acabado, vale ese."""
    res = [dict(e) for e in propi]
    for e in altre or []:
        igual = next((x for x in res if x["clau"] == e["clau"] and x["inici"] == e["inici"]), None)
        if igual is None:
            res.append(dict(e))
        elif e.get("fi") and not igual.get("fi"):
            igual.update({k: e[k] for k in ("fi", "fi_ca", "fi_es") if k in e})
    return sorted(res, key=lambda e: e["inici"])


def historial(estat, nous, ahora, anterior=None):
    h = estat["historial"] = fusiona(estat.get("historial") or [], anterior)
    for a in nous:
        ep = a.get("episodi")
        if not ep:
            continue
        obert = next((e for e in reversed(h) if e["clau"] == ep and not e.get("fi")), None)
        if a.get("nivell") == "fi":
            for e in h:
                if e["clau"] == ep and not e.get("fi"):
                    e.update(fi=a["hora"], fi_ca=a["ca"], fi_es=a["es"])
            continue
        if obert:
            # Sube de nivel o cambia: se queda el texto nuevo y el peor nivel.
            if rang(a.get("nivell")) >= rang(obert.get("nivell")):
                obert["nivell"] = a.get("nivell")
            obert.update(ca=a["ca"], es=a["es"], darrer=a["hora"],
                         **{k: a[k] for k in ("enllac", "fins") if a.get(k)})
        else:
            h.append({"clau": ep, "tipus": a["tipus"], "inici": a["hora"], "nivell": a.get("nivell"),
                      "ca": a["ca"], "es": a["es"], **{k: a[k] for k in ("enllac", "fins") if a.get(k)}})
    # Un plan que ya no se muestra (desactivado sin aviso, u oculto por no
    # tener motivo meteorológico: ADR 0062) ya no está activo en la página.
    plans = (estat.get("oficials") or {}).get("plans")
    if plans is not None:
        visibles = {k for k, p in plans.items() if not p.get("ocult")}
        for e in h:
            if e["clau"].startswith("pla:") and not e.get("fi") and e["clau"][4:] not in visibles:
                e["fi"] = ahora.isoformat(timespec="minutes")
    limit = ahora - dt.timedelta(days=HISTORIAL_DIES)
    estat["historial"] = [e for e in h if dt.datetime.fromisoformat(
        e.get("fi") or e.get("fins") or e.get("darrer") or e["inici"]) > limit]
    return estat["historial"]


def anterior_publicat(font):
    """El historial del último avisos.json publicado: una ruta (la reserva, en
    IONOS) o una dirección (el NAS). [] si no se puede leer."""
    if not font:
        return []
    try:
        if font.startswith("https://"):
            with urllib.request.urlopen(font, timeout=20) as r:
                return json.load(r).get("historial") or []
        with open(font, encoding="utf-8") as f:
            return json.load(f).get("historial") or []
    except (OSError, ValueError):
        return []


# --- Enlace a la web (ADR 0072) -----------------------------------------------------
# Todo aviso que se puede elegir lleva un enlace a su información en la web
# (Juanjo, 11-10-2026: «todos los avisos que tengan una alerta configurable …
# deben tener un enlace, como ya has hecho con la pestaña peligros»): peligro y
# riera, a su ficha de «Perill»; los cortes de luz, a «Llum»; la lluvia, a «El
# temps». La misma página abre la notificación del navegador (bot/push.py).

def id_fitxa(clau, inici):
    """El id de la ficha en «Perill», el mismo que idFitxa de web/perill.js."""
    t = unicodedata.normalize("NFD", f"{clau}-{inici}")
    t = "".join(c for c in t if not "\u0300" <= c <= "\u036f")
    return "a-" + re.sub(r"-+", "-", re.sub(r"[^A-Za-z0-9-]+", "-", t)).lower()


PAGINA = {"pluja": "./", "llum": "consultes.html#llum"}
MES_INFO = {"ca": "Més informació a Temps a Montflorit", "es": "Más información en Temps a Montflorit"}


def pagina(a, hist):
    """La página del aviso, relativa a la web (perill.html#a-…, consultes.html#llum…)."""
    ep = a.get("episodi")
    if ep:
        e = next((e for e in reversed(hist) if e["clau"] == ep), None)
        return f"perill.html#{id_fitxa(ep, e['inici'])}" if e else "perill.html"
    return PAGINA.get(a["tipus"], "./")


def amb_enllac(a, hist):
    """Pone a cada aviso nuevo su página y, al final del texto, el enlace."""
    a["pagina"] = pagina(a, hist)
    for idioma in ("ca", "es"):
        base = WEB if idioma == "ca" else WEB + "es/"
        url = base + ("" if a["pagina"] == "./" else a["pagina"])
        a[idioma] += f'\n<a href="{html.escape(url)}">{MES_INFO[idioma]}</a>'
    return a


def actualitza(casa_json, sortida, ahora=None, anterior=None):
    ahora = ahora or dt.datetime.now().astimezone()
    with open(casa_json, encoding="utf-8") as f:
        salida = json.load(f)
    try:
        with open(ESTAT, encoding="utf-8") as f:
            estat = json.load(f)
    except (OSError, ValueError):
        estat = {}
    nous = decideix(estat, salida, ahora)
    # Los avisos de las últimas CONSERVA_H horas: el bot reparte los que no ha
    # mandado aún.
    limit = ahora - dt.timedelta(hours=CONSERVA_H)
    llista = [a for a in estat.get("llista", []) if dt.datetime.fromisoformat(a["hora"]) > limit] + nous
    estat["llista"] = llista
    hist = historial(estat, nous, ahora, anterior_publicat(anterior))
    # El enlace va en el aviso, no en el historial: la ficha ya está en la web.
    for a in nous:
        amb_enllac(a, hist)
    with open(ESTAT + ".tmp", "w", encoding="utf-8") as f:
        json.dump(estat, f, ensure_ascii=False)
    os.replace(ESTAT + ".tmp", ESTAT)
    with open(sortida, "w", encoding="utf-8") as f:
        # El Pla Alfa de hoy y mañana, para «Ara» de «Perill», sin avisar ni
        # guardar historial: cambia cada día (ADR 0046 y 0071).
        alfa = (salida.get("entorn") or {}).get("pla_alfa")
        json.dump({"generat": ahora.isoformat(timespec="minutes"), "versio": C.VERSION, "avisos": llista,
                   "historial": hist, "pla_alfa": alfa}, f, ensure_ascii=False)
    return nous


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print(__doc__)
        sys.exit(1)
    for a in actualitza(sys.argv[1], sys.argv[2], anterior=sys.argv[3] if len(sys.argv) == 4 else None):
        print(a["id"], a["ca"].splitlines()[0])
