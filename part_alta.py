#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""La parte alta del barrio, más cálida que la riera (ADR 0087).

La estación de casa está junto a la riera (carrer Canaletes), en la zona más
fría del barrio, como ICERDA6; ICERDA18, ICERDA28 e ICERDA48 están en la
parte alta (config.VEINES, «alta»). Juanjo, 13-10-2026: las temperaturas son
las de la riera, y para el resto hay que sumar «1, 2... grados, dependiendo
del momento y del frío, porque a veces no habrá diferencias, pero otras sí».

- **Ahora** (`ara`): la mediana de las vecinas de arriba leídas en la última
  media hora menos la temperatura de «Ara». Es una medida.
- **Previsión** (`per_hores`): para cada hora del día, la mediana de (parte
  alta − casa) en los últimos DIES días del registro, sin las horas con sol
  directo sobre el termómetro (ADR 0081). Si una hora tiene menos de
  MIN_MOSTRES, la de partida, calculada con el verano y el otoño de 2026
  (calibracio/part_alta.json). Así sigue la época del año sola.

Las horas del día son las del tiempo universal (`hora_solar`), no las del
reloj: la diferencia la marcan el sol y el aire que se calienta, que no
cambian con la hora oficial. Con las del reloj, el mes siguiente a cada
cambio de hora (ADR 0089) se mezclaban dos horas de sol distintas.
"""
import datetime as dt
import json
import os
import statistics
from zoneinfo import ZoneInfo

import config as C
import sol_estacio as SE

DIR = os.environ.get("REGISTRE_DIR", "/estat/registre")
INICIAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibracio", "part_alta.json")
ALTES = [e for e, v in C.VEINES.items() if v.get("alta")]
DIES = 30
MIN_MOSTRES = 10
ALTES_MIN = 2           # vecinas de arriba con dato para dar la diferencia
FRESCA_MIN = 30
ZONA = ZoneInfo("Europe/Madrid")


def hora_solar(t):
    """La hora en tiempo universal (0-23) de una clave de hora del programa
    («…T15:00», hora de Madrid, o «…T02:00+01:00» la que se repite en
    octubre) o de un datetime con zona."""
    if isinstance(t, str):
        t = dt.datetime.fromisoformat(t)
    if t.tzinfo is None:
        t = t.replace(tzinfo=ZONA)
    return t.astimezone(dt.timezone.utc).hour


def mediana_alta(temperatures):
    ts = [t for t in temperatures if t is not None]
    return statistics.median(ts) if len(ts) >= ALTES_MIN else None


def ara(temperatura, veines, ahora):
    """Grados que tiene de más la parte alta ahora mismo (o None)."""
    if temperatura is None:
        return None
    fresques = [v.get("temperatura") for v in veines or [] if v.get("estacio") in ALTES and v.get("hora")
                and ahora - dt.datetime.fromisoformat(v["hora"]) <= dt.timedelta(minutes=FRESCA_MIN)]
    m = mediana_alta(fresques)
    return None if m is None else round(m - temperatura, 1)


def inicial():
    try:
        with open(INICIAL, encoding="utf-8") as f:
            return {int(h): v for h, v in json.load(f)["per_hora_utc"].items()}
    except (OSError, ValueError, KeyError):
        return {}


def per_hores(ahora, casa_hores=None, veines_hores=None, eps=None):
    """{hora del día en tiempo universal: grados que tiene de más la parte alta}."""
    if casa_hores is None:
        casa_hores = SE._llegeix_hores(os.path.join(DIR, "estacio-casa.csv"))
    if veines_hores is None:
        veines_hores = {e: SE._llegeix_hores(os.path.join(DIR, f"veina-{e}.csv")) for e in ALTES}
    desde = (ahora - dt.timedelta(days=DIES)).strftime("%Y-%m-%dT%H:%M")
    claus = [c for c in casa_hores if c >= desde and casa_hores[c] is not None]
    fora = SE.hores_tocades(claus, eps)
    mostres = {}
    for c in claus:
        if c in fora:
            continue
        m = mediana_alta([veines_hores.get(e, {}).get(c) for e in ALTES])
        if m is not None:
            mostres.setdefault(hora_solar(c), []).append(m - casa_hores[c])
    res = inicial()
    for h, ds in mostres.items():
        if len(ds) >= MIN_MOSTRES:
            res[h] = round(statistics.median(ds), 1)
    return res


def a_les_hores(hores, taula):
    """Pone a cada fila de la previsión «dif_alta»: la de su hora (la
    temperatura de la fila es la media de sus dos extremos)."""
    for f in hores or []:
        a = taula.get(hora_solar(f["hora"]))
        b = taula.get(hora_solar(f["fins"]))
        vals = [x for x in (a, b) if x is not None]
        f["dif_alta"] = round(sum(vals) / len(vals), 1) if vals else None
    return hores
