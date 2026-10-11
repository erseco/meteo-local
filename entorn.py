# SPDX-License-Identifier: AGPL-3.0-or-later
"""Lo que pasa alrededor de Montflorit y condiciona salir (ADR 0046):

- incendios forestales en curso de la capa pública de actuaciones urgentes de
  Bombers de la Generalitat (ArcGIS), solo los que interesan al barrio (ADR
  0071): dentro del Parc Natural de Collserola, a cualquier distancia (el
  límite oficial, de la capa del Consorci del parque); en Cerdanyola, en
  cualquier punto; y en los demás municipios del parque, como Montcada, a
  ENTORN_RADI_KM o menos. Ripollet, Sabadell o Barberà, que no tienen parque,
  no;
- el nivel del Pla Alfa de Cerdanyola hoy y mañana, y los cierres de espacios
  naturales que tocan Collserola, de las capas públicas de Agents Rurals
  (ArcGIS).

Las restricciones de acceso a Collserola por la peste porcina se leían de los
avisos de la web del parque; se quitaron el mismo día, por frágiles (dependían
de cómo y cuándo los redactaran: ADR 0046).

Las dos fuentes de ArcGIS son las que usan los visores oficiales, no conjuntos
de datos documentados: si una falla, su parte queda en None y se dice.

    python3 entorn.py        lo que hay ahora, en JSON
"""
import datetime as dt
import json
import math
import sys
import urllib.parse
import urllib.request

import config as C

ARCGIS = "https://services7.arcgis.com/ZCqVt1fRXwwK6GF4/arcgis/rest/services"
BOMBERS = ARCGIS + "/ACTUACIONS_URGENTS_online_PRO_AMB_FASE_VIEW/FeatureServer/0"
# El límite del Parc Natural de la Serra de Collserola, del Consorci del parque.
COLLSEROLA = ("https://services7.arcgis.com/z50OW9s1n52Z8H2C/arcgis/rest/services/"
              "L%C3%ADmit_Parc_de_Collserola/FeatureServer/0")
ALFA_MUNICIPAL = {"avui": ARCGIS + "/Pla_Alfa_Municipal_Avui_FL_2_view/FeatureServer/0",
                  "dema": ARCGIS + "/pla_alfa_municipal_dema_FL_VW/FeatureServer/5"}
ALFA_TANCAMENTS = {"avui": ARCGIS + "/tancaments_pla_alfa_avui_VW/FeatureServer/2",
                   "dema": ARCGIS + "/tancaments_pla_alfa_dema_VW/FeatureServer/2"}
UA = {"User-Agent": "Temps a Montflorit (https://meteo-montflorit.github.io/)"}

def get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    return 6371 * math.hypot((lo2 - lo1) * math.cos((la1 + la2) / 2), la2 - la1)


def hora_iso(ms):
    return dt.datetime.fromtimestamp(ms / 1000).astimezone().isoformat(timespec="minutes") if ms else None


def dins_collserola(y, x):
    """Si el punto cae dentro del parque, con COLLSEROLA_MARGE_KM de margen:
    la posición de una actuación es aproximada."""
    d = get(COLLSEROLA + "/query", {
        "geometry": f"{x},{y}", "geometryType": "esriGeometryPoint", "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects", "distance": C.COLLSEROLA_MARGE_KM,
        "units": "esriSRUnit_Kilometer", "returnCountOnly": "true", "f": "json"})
    if "error" in d:
        raise RuntimeError(d["error"].get("message"))
    return d.get("count", 0) > 0


def interessa(municipi, dist, collserola):
    """Si un incendio interesa al barrio (Juanjo, 11-10-2026): en Collserola,
    a cualquier distancia; en Cerdanyola, siempre; en los otros municipios del
    parque, solo cerca. Los demás, no, por cerca que estén."""
    nom = (municipi or "").strip().lower()
    if collserola or nom == C.MUNICIPI.lower():
        return True
    return nom in {m.lower() for m in C.MUNICIPIS_COLLSEROLA} and dist is not None and dist <= C.ENTORN_RADI_KM


def incendis(dades=None, collserola=None):
    """Incendios de vegetación forestal en curso que interesan al barrio
    (interessa), del más cercano al más lejano."""
    xmin, ymin, xmax, ymax = C.INCENDIS_CAIXA
    d = dades or get(BOMBERS + "/query", {
        "where": "TAL_COD_ALARMA1='IV'", "geometry": f"{xmin},{ymin},{xmax},{ymax}",
        "geometryType": "esriGeometryEnvelope", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
        "outSR": 4326,
        "outFields": "GlobalID,TAL_DESC_ALARMA2,MUNICIPI_SIG,ACT_DAT_INICI,ACT_DAT_FI,ACT_NUM_VEH,COM_FASE",
        "returnGeometry": "true", "f": "json"})
    if "error" in d:
        raise RuntimeError(d["error"].get("message"))
    collserola = collserola or dins_collserola
    res = []
    for f in d.get("features", []):
        a, g = f["attributes"], f.get("geometry") or {}
        # Solo los forestales: los de solares urbanos son muchos y no limitan salir.
        if "forestal" not in (a.get("TAL_DESC_ALARMA2") or "").lower() or a.get("ACT_DAT_FI"):
            continue
        if "x" not in g:
            continue
        dist = km(C.CASA, (g["y"], g["x"]))
        municipi = a.get("MUNICIPI_SIG")
        al_parc = collserola(g["y"], g["x"])
        if not interessa(municipi, dist, al_parc):
            continue
        res.append({"id": a["GlobalID"], "municipi": municipi, "km": round(dist, 1),
                    "collserola": al_parc, "inici": hora_iso(a.get("ACT_DAT_INICI")),
                    "vehicles": a.get("ACT_NUM_VEH"), "fase": a.get("COM_FASE")})
    return sorted(res, key=lambda i: i["km"])


def actualitzada(url, ara, hores):
    """Si la capa se ha editado en las últimas `hores`: fuera de campaña, la
    del Pla Alfa municipal se queda con el último valor y no vale."""
    edit = ((get(url, {"f": "json"}).get("editingInfo") or {}).get("lastEditDate"))
    return bool(edit) and ara - dt.datetime.fromtimestamp(edit / 1000).astimezone() <= dt.timedelta(hours=hores)


def pla_alfa(ara):
    """Nivel del Pla Alfa de Cerdanyola hoy y mañana (None si la capa no está
    al día) y los cierres de espacios naturales que tocan Collserola."""
    res = {}
    for dia, url in ALFA_MUNICIPAL.items():
        nivell = None
        if actualitzada(url, ara, C.ALFA_ACTUAL_H):
            d = get(url + "/query", {"where": f"CODIMUNI='{C.ALFA_MUNICIPI}'", "outFields": "PERIL_M",
                                     "returnGeometry": "false", "f": "json"})
            files = d.get("features") or []
            nivell = files[0]["attributes"]["PERIL_M"] if files else None
        # La escala es 0-4; el 5 es «sin nivel» (gris claro en el mapa oficial).
        res[dia] = nivell if nivell in (0, 1, 2, 3, 4) else None
    tancaments = []
    for dia, url in ALFA_TANCAMENTS.items():
        d = get(url + "/query", {"where": "1=1", "outFields": "Espai_prot", "returnGeometry": "false", "f": "json"})
        for f in d.get("features") or []:
            nom = f["attributes"].get("Espai_prot") or ""
            if "collserola" in nom.lower():
                tancaments.append({"dia": dia, "espai": nom})
    res["tancaments"] = tancaments
    return res


def calcula(ara=None):
    """Para casa.json y los datos públicos. Cada parte, None si su fuente falla."""
    ara = ara or dt.datetime.now().astimezone()
    res = {"hora": ara.isoformat(timespec="minutes"), "errors": []}
    for clau, funcio in (("incendis", incendis), ("pla_alfa", lambda: pla_alfa(ara))):
        try:
            res[clau] = funcio()
        except Exception as ex:
            res[clau] = None
            res["errors"].append(f"{clau}: {ex}")
    return res


if __name__ == "__main__":
    print(json.dumps(calcula(), ensure_ascii=False, indent=1))
