#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""El mapa de los límites de Montflorit para la web (ADR 0072).

Dibuja web/img/montflorit-limits.svg: el contorno de montflorit-limits.geojson
sobre las calles, la riera y el verde de OpenStreetMap, con unos pocos nombres
para orientarse. Es una imagen propia, sin pedir nada a servidores de fuera al
abrir la página. Hay que rehacerla cuando cambien los límites:

    curl -o zona.osm "https://api.openstreetmap.org/api/0.6/map?bbox=2.1225,41.4745,2.1445,41.4880"
    python3 eines/mapa_barri.py zona.osm

Los datos de OpenStreetMap (© col·laboradors d'OpenStreetMap, ODbL) no se
guardan: solo el dibujo, que lleva la atribución.
"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMITS = os.path.join(ARREL, "montflorit-limits.geojson")
SORTIDA = os.path.join(ARREL, "web", "img", "montflorit-limits.svg")

MARGE_M = 230          # al voltant del barri
PX_M = 0.55            # píxels per metre
LAT0 = 41.481
KX = math.cos(math.radians(LAT0)) * 111320
KY = 110540

VIES = {"primary": 7, "secondary": 7, "tertiary": 6, "unclassified": 4.5, "residential": 4.5,
        "living_street": 4.5, "pedestrian": 4, "service": 2.5}
VERD = {("landuse", "forest"), ("natural", "wood"), ("natural", "scrub"), ("leisure", "park"),
        ("landuse", "meadow"), ("landuse", "grass"), ("natural", "grassland")}
# Noms per orientar-se: el barri i els veïns (lon, lat, text, mida, cursiva).
NOMS = [(2.1322, 41.4797, "Montflorit", 30, False),
        (2.1265, 41.4842, "Parc Tecnològic", 15, False),
        (2.1335, 41.4874, "Sant Ramon", 15, False),
        (2.1378, 41.4846, "Guiera", 15, False),
        (2.1377, 41.4772, "Collserola", 15, False),
        (2.1351, 41.48075, "Ca n'Oliver", 13, False),
        (2.1272, 41.4820, "Riera de Sant Cugat", 13, True)]


def llegeix_osm(ruta):
    arrel = ET.parse(ruta).getroot()
    nodes = {n.get("id"): (float(n.get("lon")), float(n.get("lat"))) for n in arrel.iter("node")}
    vies = []
    for w in arrel.iter("way"):
        tags = {t.get("k"): t.get("v") for t in w.iter("tag")}
        punts = [nodes[nd.get("ref")] for nd in w.iter("nd") if nd.get("ref") in nodes]
        if len(punts) > 1:
            vies.append((tags, punts))
    return vies


def main(osm):
    anell = json.load(open(LIMITS, encoding="utf-8"))["features"][0]["geometry"]["coordinates"][0]
    xs = [(lon - 2.13) * KX for lon, _ in anell]
    ys = [(lat - LAT0) * KY for _, lat in anell]
    x0, x1 = min(xs) - MARGE_M, max(xs) + MARGE_M
    y0, y1 = min(ys) - MARGE_M, max(ys) + MARGE_M
    W, H = round((x1 - x0) * PX_M), round((y1 - y0) * PX_M)

    def px(lon, lat):
        return round(((lon - 2.13) * KX - x0) * PX_M), round((y1 - (lat - LAT0) * KY) * PX_M)

    def cami(punts, tancat=False):
        p = [px(*q) for q in punts]
        p = [q for i, q in enumerate(p) if i == 0 or q != p[i - 1]]
        d = "M" + " ".join(f"{x:g} {y:g}" for x, y in p)
        return d + ("Z" if tancat else "")

    verd, aigua, carrers = [], [], {}
    for tags, punts in llegeix_osm(osm):
        if punts[0] == punts[-1] and any((k, tags.get(k)) in VERD for k, _ in VERD):
            verd.append(cami(punts, True))
        elif tags.get("waterway") in ("stream", "river"):
            aigua.append(cami(punts))
        elif tags.get("highway") in VIES:
            carrers.setdefault(VIES[tags["highway"]], []).append(cami(punts))

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         'font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif">',
         "<!-- Límits de Montflorit (montflorit-limits.geojson, ADR 0072). Fons: © col·laboradors "
         "d'OpenStreetMap, ODbL. Fet amb eines/mapa_barri.py. -->",
         f'<rect width="{W}" height="{H}" fill="#f4f1ea"/>',
         f'<path fill="#d8e8c8" d="{" ".join(verd)}"/>',
         f'<path fill="none" stroke="#5b9bd5" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" '
         f'd="{" ".join(aigua)}"/>']
    for amplada in sorted(carrers):
        s.append(f'<path fill="none" stroke="#c9c2b5" stroke-width="{amplada + 2}" stroke-linecap="round" '
                 f'stroke-linejoin="round" d="{" ".join(carrers[amplada])}"/>')
    for amplada in sorted(carrers):
        s.append(f'<path fill="none" stroke="#fff" stroke-width="{amplada}" stroke-linecap="round" '
                 f'stroke-linejoin="round" d="{" ".join(carrers[amplada])}"/>')
    s.append(f'<path fill="#1d4ed8" fill-opacity=".13" stroke="#1d4ed8" stroke-width="3.5" '
             f'stroke-linejoin="round" d="{cami(anell, True)}"/>')
    for lon, lat, text, mida, cursiva in NOMS:
        x, y = px(lon, lat)
        color = "#1e3a8a" if text == "Montflorit" else ("#2f6aa3" if cursiva else "#4a4a4a")
        estil = ' font-style="italic"' if cursiva else ""
        pes = "700" if text == "Montflorit" else "600"
        s.append(f'<text x="{x:g}" y="{y:g}" font-size="{mida}" font-weight="{pes}"{estil} text-anchor="middle" '
                 f'fill="{color}" stroke="#f4f1ea" stroke-width="4" paint-order="stroke">{text}</text>')
    # Escala de 200 m i nord, a baix a l'esquerra.
    llarg = 200 * PX_M
    s.append(f'<g transform="translate(18 {H - 22})" font-size="12" fill="#333">'
             f'<path d="M0 0h{llarg:g}M0 -5v5M{llarg:g} -5v5" stroke="#333" stroke-width="2" fill="none"/>'
             f'<text x="{llarg / 2:g}" y="-8" text-anchor="middle">200 m</text></g>')
    s.append(f'<g transform="translate({W - 26} 34)"><path d="M0 -20 7 0H-7Z" fill="#333"/>'
             '<text y="16" font-size="13" font-weight="700" text-anchor="middle" fill="#333">N</text></g>')
    s.append(f'<text x="{W - 8}" y="{H - 8}" font-size="11" text-anchor="end" fill="#555" '
             'stroke="#f4f1ea" stroke-width="3" paint-order="stroke">© OpenStreetMap</text>')
    s.append("</svg>")
    with open(SORTIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(s) + "\n")
    print(f"{SORTIDA}: {W}×{H} px, {os.path.getsize(SORTIDA) // 1024} KB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
