#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Editor de los límites de Montflorit (ADR 0072).

Abre en el navegador un mapa con los límites del barrio, para retocarlos a
mano: se arrastran los puntos, los pequeños del medio de cada lado añaden uno
y el botón derecho quita uno. «Desa» guarda en eines/limits-esborrany.geojson,
un borrador que la web no usa. Cuando el borrador esté bien, «aplica» lo copia
a montflorit-limits.geojson, el que usan «Llum» y lo que venga (Juanjo,
11-10-2026: «este mapa guárdalo para cuando te lo pida»).

    python3 eines/limits.py            abre el editor (http://127.0.0.1:8766/)
    python3 eines/limits.py aplica     el borrador pasa a ser el límite de la web

El mapa de fondo es de OpenStreetMap y el editor usa Leaflet y Leaflet-Geoman
desde unpkg.com: hace falta conexión.
"""
import http.server
import json
import os
import socket
import sys
import webbrowser

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLICAT = os.path.join(ARREL, "montflorit-limits.geojson")
ESBORRANY = os.path.join(ARREL, "eines", "limits-esborrany.geojson")
PORT = 8766

PAGINA = """<!doctype html><html lang="ca"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Límits de Montflorit</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@2.17.0/dist/leaflet-geoman.css">
<script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@2.17.0/dist/leaflet-geoman.js"></script>
<style>html,body,#m{height:100%;margin:0}.l{background:#fff;padding:8px 12px;font:15px sans-serif;line-height:1.5;
max-width:360px;box-shadow:0 1px 6px #0004;border-radius:6px}.l button{font:inherit;font-weight:600;padding:6px 14px;
margin-top:6px;border:0;border-radius:999px;background:#1d4ed8;color:#fff;cursor:pointer}#e{color:#15803d;font-weight:600}</style>
</head><body><div id="m"></div><script>
const DADES = __DADES__;
const COLORS = ['#c00', '#7c3aed', '#0a7d2c', '#b45309'];
const m = L.map('m').setView([41.4815, 2.1330], 16);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '© OpenStreetMap', maxZoom: 19}).addTo(m);
const capes = DADES.features.map((f, i) => {
  const c = L.polygon(f.geometry.coordinates[0].slice(0, -1).map(([x, y]) => [y, x]),
    {color: COLORS[i % COLORS.length], weight: 3, fillOpacity: .1}).addTo(m);
  c.bindTooltip(f.properties.nom || '');
  c.pm.enable({allowSelfIntersection: false});
  return c;
});
const lg = L.control({position: 'topright'});
lg.onAdd = () => {
  const d = L.DomUtil.create('div', 'l');
  L.DomEvent.disableClickPropagation(d);
  d.innerHTML = '<b>Límits de Montflorit</b> (' + __QUIN__ + ')<br>Arrossega els punts per moure el contorn; els petits '
    + 'del mig afegeixen un punt; clic dret damunt d\\'un punt per treure\\'l.<br><button id="d">Desa</button> <span id="e"></span>';
  return d;
};
lg.addTo(m);
document.getElementById('d').onclick = () => {
  const fc = {type: 'FeatureCollection', features: capes.map((c, i) => ({...c.toGeoJSON(), properties: DADES.features[i].properties}))};
  fetch('/desa', {method: 'POST', body: JSON.stringify(fc)}).then((r) => {
    document.getElementById('e').textContent = r.ok ? 'Desat a l\\'esborrany.' : 'No s\\'ha pogut desar';
  });
};
</script></body></html>"""


def llegeix(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def desa_esborrany(fc):
    base = llegeix(ESBORRANY) if os.path.exists(ESBORRANY) else llegeix(PUBLICAT)
    for f in fc["features"]:
        f["geometry"]["coordinates"] = [[[round(x, 5), round(y, 5)] for x, y in f["geometry"]["coordinates"][0]]]
    base["features"] = fc["features"]
    base["nom"] = "Esborrany dels límits de Montflorit (no publicat)"
    with open(ESBORRANY, "w", encoding="utf-8") as f:
        f.write(json.dumps(base, ensure_ascii=False, indent=1) + "\n")


class Editor(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        esborrany = os.path.exists(ESBORRANY)
        dades = llegeix(ESBORRANY if esborrany else PUBLICAT)
        cos = (PAGINA.replace("__DADES__", json.dumps(dades, ensure_ascii=False))
               .replace("__QUIN__", json.dumps("esborrany" if esborrany else "el publicat"))).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(cos)

    def do_POST(self):
        if self.path != "/desa":
            self.send_error(404)
            return
        desa_esborrany(json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)))))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *a):
        pass


def aplica():
    if not os.path.exists(ESBORRANY):
        sys.exit("No hi ha cap esborrany.")
    pub, esb = llegeix(PUBLICAT), llegeix(ESBORRANY)
    pub["features"] = esb["features"]
    with open(PUBLICAT, "w", encoding="utf-8") as f:
        f.write(json.dumps(pub, ensure_ascii=False, indent=1) + "\n")
    os.remove(ESBORRANY)
    print("Fet: montflorit-limits.geojson és ara l'esborrany. Revisa la «font» i publica.")


if __name__ == "__main__":
    if sys.argv[1:] == ["aplica"]:
        aplica()
    elif not sys.argv[1:]:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                sys.exit(f"El port {PORT} ja és ocupat.")
        url = f"http://127.0.0.1:{PORT}/"
        print(f"Editor a {url} (Ctrl+C per aturar-lo)")
        webbrowser.open(url)
        http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Editor).serve_forever()
    else:
        sys.exit(__doc__)
