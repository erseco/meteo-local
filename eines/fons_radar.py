#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""El fons del mapa del radar (ADR 0019): web/img/radar-fons.webp.

El quadrat de 2 × nowcast.MAPA_KM km al voltant de casa, en la mateixa
projecció que les imatges del radar (Web Mercator), tret del Mapa base
estàndard gris de l'ICGC (© ICGC, CC BY) al nivell 10. És una imatge pròpia:
la web no demana res a cap servidor de mapes en obrir-la. Cal refer-la si
canvia MAPA_KM o la ubicació de casa:

    python3 eines/fons_radar.py
"""
import io
import math
import os
import sys
import urllib.request

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ARREL)
import config as C  # noqa: E402
import nowcast as N  # noqa: E402

SORTIDA = os.path.join(ARREL, "web", "img", "radar-fons.webp")
CAPA = "estandard-gris"
NIVELL = 10
TESSELA = "https://geoserveis.icgc.cat/servei/catalunya/mapa-base/wmts/{capa}/MON3857NW/{z}/{x}/{y}.png"


def main():
    from PIL import Image
    lat, lon = C.CASA
    n = 2 ** NIVELL * 256
    x0 = (lon + 180) / 360 * n
    y0 = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    # Els mateixos km per píxel que el radar (nowcast.km_px), al nivell del fons.
    mig = N.MAPA_KM / N.km_px(lat) * 2 ** (NIVELL - N.Z)
    e, d, s, i = x0 - mig, y0 - mig, x0 + mig, y0 + mig
    tx0, ty0, tx1, ty1 = int(e // 256), int(d // 256), int(s // 256), int(i // 256)
    mosaic = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            url = TESSELA.format(capa=CAPA, z=NIVELL, x=tx, y=ty)
            req = urllib.request.Request(url, headers={"User-Agent": "meteo-local (fons del mapa del radar)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                mosaic.paste(Image.open(io.BytesIO(r.read())).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
    fons = mosaic.crop((round(e - tx0 * 256), round(d - ty0 * 256), round(s - tx0 * 256), round(i - ty0 * 256)))
    fons.save(SORTIDA, "WEBP", quality=80, method=6)
    print(SORTIDA, fons.size, os.path.getsize(SORTIDA) // 1024, "KB")


if __name__ == "__main__":
    main()
