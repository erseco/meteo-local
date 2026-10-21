# SPDX-License-Identifier: AGPL-3.0-or-later
"""Collect local data into the upstream web contract, without local training.

All forecast timestamps come from Unix time, avoiding Open-Meteo's fixed-offset
local timestamp ambiguity at DST changes. No publishing or messaging side effects.
"""
import argparse
import concurrent.futures
import datetime as dt
import json
import os
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import aire
import prevision

from . import observations
from . import profile as P

FORECAST = "https://api.open-meteo.com/v1/forecast"
AIR = "https://air-quality-api.open-meteo.com/v1/air-quality"
MARINE = "https://marine-api.open-meteo.com/v1/marine"
ALERTS = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-spain"
HOURLY = ("temperature_2m", "precipitation", "precipitation_probability", "weather_code",
          "cloud_cover", "wind_speed_10m", "wind_gusts_10m", "snowfall", "uv_index",
          "wind_direction_10m", "relative_humidity_2m", "is_day")
CURRENT = ("temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m",
           "wind_direction_10m", "weather_code", "apparent_temperature", "is_day")
DAILY = ('temperature_2m_max','temperature_2m_min','precipitation_sum',
         'precipitation_probability_max','weather_code','wind_speed_10m_max',
         'wind_gusts_10m_max','wind_direction_10m_dominant')
# Saharan dust (calima) from CAMS global; indicative levels for surface dust in µg/m³.
DUST = ("dust", "aerosol_optical_depth", "pm10")
DUST_LEVELS = ((20, "none"), (50, "light"), (100, "moderate"), (200, "intense"))
# Offshore grid point in front of the city: the coastal cell has no sea data.
MARINE_POINT = (28.15, -15.40)
MARINE_FIELDS = ("wave_height", "wave_direction", "wave_period", "sea_surface_temperature")


def fetch(url, params=None):
    """Read one bounded public request; failures are reported per source."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": f"meteo-local-lpa/{P.VERSION}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(4_000_000).decode("utf-8")


def parameters():
    return {"latitude": P.COORDINATES[0], "longitude": P.COORDINATES[1],
            "timezone": P.TIMEZONE, "timeformat": "unixtime", "forecast_days": 7}


def local(timestamp):
    return dt.datetime.fromtimestamp(timestamp, dt.UTC).astimezone(P.ZONE)


def day_of(timestamp, offset):
    """Daily Unix times are midnights at the fixed offset of the request, also after a DST change."""
    return dt.datetime.fromtimestamp(timestamp + offset, dt.UTC).date().isoformat()


def forecast_rows(data, now):
    """Hourly precipitation is accumulated up to the end of the shown interval."""
    h = data["hourly"]
    times = h["time"]
    if not times or any(b - a != 3600 for a, b in zip(times, times[1:])):
        raise ValueError("Invalid hourly timeline")
    for field in HOURLY:
        if len(h.get(field, [])) != len(times):
            raise ValueError(f"Incomplete forecast: {field}")
    if not any(v is not None for v in h["temperature_2m"]):
        raise ValueError("Forecast has no temperatures for Las Palmas")
    rows = []
    for i, timestamp in enumerate(times):
        end = local(timestamp)
        if end.timestamp() <= now.timestamp():
            continue
        start = local(timestamp - 3600)
        value = lambda key, i=i: h[key][i]
        probability = value("precipitation_probability")
        rows.append({"hora": start.isoformat(timespec="minutes"), "fins": end.isoformat(timespec="minutes"),
                     "temperatura": value("temperature_2m"), "pluja_mm": value("precipitation"),
                     "probabilitat": None if probability is None else probability / 100,
                     "codi": value("weather_code"), "nuvols": value("cloud_cover"),
                     "vent": value("wind_speed_10m"), "ratxa": value("wind_gusts_10m"),
                     "neu": value("snowfall"), "uv": value("uv_index"),
                     "direccio": value("wind_direction_10m"), "humitat": value("relative_humidity_2m"),
                     "es_dia": value("is_day"),
                     "plou_ara": None, "segons_estacio": False, "segons_radar": False,
                     "radar": None, "avisos": [], "ratxes_models": {}})
    if len(rows) < 24:
        raise ValueError("Less than 24 hours of fresh forecast")
    return rows


def dust_level(value):
    """Indicative calima level for a surface dust concentration; None stays unknown."""
    if value is None:
        return None
    return next((level for limit, level in DUST_LEVELS if value < limit), "very_intense")


def hourly_series(payload, fields, now, hours):
    """Future hourly rows from an Open-Meteo Unix-time response, in Canary time."""
    h = payload["hourly"]
    rows = []
    for i, timestamp in enumerate(h["time"]):
        if timestamp + 3600 <= now.timestamp():
            continue
        rows.append({"hora": local(timestamp).isoformat(timespec="minutes"),
                     **{field: h.get(field, [None] * len(h["time"]))[i] for field in fields}})
    return rows[:hours]


def parse_calima(payload, now):
    rows = hourly_series(payload, DUST, now, 96)
    if not rows or not any(r["dust"] is not None for r in rows):
        raise ValueError("No dust forecast")
    for row in rows:
        row["nivel"] = dust_level(row["dust"])
    peak = max((r for r in rows if r["dust"] is not None), key=lambda r: r["dust"])
    return {"source": "CAMS global · Open-Meteo", "unit": "µg/m³", "now": rows[0],
            "peak": peak, "hours": rows}


def parse_marine(payload, now):
    rows = hourly_series(payload, MARINE_FIELDS, now, 72)
    if not rows or rows[0]["wave_height"] is None:
        raise ValueError("No marine forecast for the offshore point")
    return {"source": "Open-Meteo Marine", "point": list(MARINE_POINT),
            "now": rows[0], "hours": rows}


def parse_alerts(xml, now):
    """A successful national feed with no matching entries means no local warning.

    A failed/malformed feed remains None in the public document, never [].
    """
    root = ET.fromstring(xml)
    atom = "{http://www.w3.org/2005/Atom}"
    cap = "{urn:oasis:names:tc:emergency:cap:1.2}"
    if root.tag != atom + "feed":
        raise ValueError("Expected Meteoalarm Atom feed")
    updated = root.findtext(atom + "updated")
    if not updated:
        raise ValueError("Feed has no freshness timestamp")
    age = now - dt.datetime.fromisoformat(updated.replace("Z", "+00:00"))
    if age > dt.timedelta(hours=24) or age < -dt.timedelta(minutes=10):
        raise ValueError("Meteoalarm feed is stale or future dated")
    result = {}
    for entry in root.findall(atom + "entry"):
        text = lambda key, entry=entry: entry.findtext(cap + key, "")
        if text("areaDesc") != P.ALERT_AREA:
            continue
        start = dt.datetime.fromisoformat(text("onset").replace("Z", "+00:00"))
        end = dt.datetime.fromisoformat(text("expires").replace("Z", "+00:00"))
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("Alert timestamps need offsets")
        if end <= now:
            continue
        event = text("event")
        level = {"Moderate": "groc", "Severe": "taronja", "Extreme": "vermell"}.get(event.split()[0])
        if level is None:
            raise ValueError("Unknown local warning severity")
        row = {"zona": P.ALERT_AREA, "tipo": prevision.tipus_aemet(event), "nivel": level,
               "inicio": start.astimezone(P.ZONE).isoformat(), "fin": end.astimezone(P.ZONE).isoformat(),
               "descripcio": text("headline") or event, "url": P.AEMET_ALERTS}
        result[(row["tipo"], row["inicio"], row["fin"], level)] = row
    return list(result.values())


def collect(now=None, reader=fetch, include_observations=True):
    """Collect independent sources concurrently; retain explicit failure state."""
    now = (now or dt.datetime.now(dt.UTC)).astimezone(P.ZONE)
    params = parameters()
    requests = {
        "previsió": (FORECAST, {**params, "hourly": ",".join(HOURLY), "current": ",".join(CURRENT),
                                "daily": ",".join(('sunrise','sunset','uv_index_max')+DAILY), "models": "best_match"}),
        "aire": (AIR, {**params, "forecast_days": 1, "domains": "cams_global",
                       "hourly": ",".join(aire.CONTAMINANTS)}),
        "avisos": (ALERTS, None),
        "calima": (AIR, {**params, "forecast_days": 4, "domains": "cams_global",
                         "hourly": ",".join(DUST)}),
        "mar": (MARINE, {**params, "latitude": MARINE_POINT[0], "longitude": MARINE_POINT[1],
                         "forecast_days": 3, "hourly": ",".join(MARINE_FIELDS)}),
    }
    data = {"versio": f"lpa-{P.VERSION}", "generat": now.isoformat(timespec="minutes"),
            "errors": [], "hores": None, "avisos": None, "aire": None, "sol": None,
            "ara_casa": None, "vent": None, "veines": [], "models": None, "radar": None,
            "riera": None, "riera_previsio": None, "trens": None, "transit": None, "llum": None,
            "pollen": None, "plans": None, "plans_ocults": None, "smp": None, "entorn": None,
            "riscos": None, "plou_ara": None, "temperatura_mesurada": None,
            "pluja_ara": {"plou": None, "mesurada": None}, "aprenentatge": None,
            "sortir_llindars": {"curt": {"risc": 0.2, "pluja": 0.5}, "llarg": {"risc": 0.2, "pluja": 0.5}},
            "horari": {"trams": [["00:00", "23:45"]], "cada_min": 15, "normal_min": 15,
                       "avis_min": 15, "mode_avis": [], "desfase_min": 0},
            "lpa": {"nom": P.NAME, "timezone": P.TIMEZONE, "unavailable": P.UNAVAILABLE,
                    "current_model": None, "calima": None, "marine": None, "sources": {}}, "consultes": {"es": {}}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        obs_future = pool.submit(observations.collect, now) if include_observations else None
        from . import nature
        nature_future = pool.submit(nature.collect, now) if include_observations else None
        from . import radar
        radar_future = pool.submit(radar.collect, now) if include_observations else None
        futures = {pool.submit(reader, url, values): name for name, (url, values) in requests.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                raw = future.result()
                if name == "avisos":
                    data["avisos"] = parse_alerts(raw, now)
                elif name == "calima":
                    data["lpa"]["calima"] = parse_calima(json.loads(raw), now)
                elif name == "mar":
                    data["lpa"]["marine"] = parse_marine(json.loads(raw), now)
                elif name == "previsió":
                    forecast = json.loads(raw)
                    data["hores"] = forecast_rows(forecast, now)
                    current = forecast.get("current")
                    if current and abs(now.timestamp() - current["time"]) <= 7200:
                        data["lpa"]["current_model"] = current
                    daily = forecast["daily"]
                    offset = forecast.get("utc_offset_seconds", 0)
                    data['lpa']['daily_forecast'] = [
                        {'date':day_of(t, offset),
                         **{key:daily.get(key,[None]*len(daily['time']))[i] for key in DAILY}}
                        for i,t in enumerate(daily['time'])]
                    data["sol"] = [{"dia": day_of(t, offset),
                                    "sortida": local(s).isoformat(timespec="minutes"),
                                    "posta": local(p).isoformat(timespec="minutes"), "uv_max": u}
                                   for t, s, p, u in zip(daily["time"], daily["sunrise"], daily["sunset"], daily["uv_index_max"])]
                else:
                    forecast = json.loads(raw)
                    forecast["hourly"]["time"] = [local(t).strftime("%Y-%m-%dT%H:%M") for t in forecast["hourly"]["time"]]
                    data["aire"] = aire.llegeix(forecast, now, corr=None)
                    if data["aire"] is None:
                        raise ValueError("No fresh air-quality forecast")
                    for row in data["aire"]["hores"]:
                        row["hora"] = dt.datetime.fromisoformat(row["hora"]).replace(tzinfo=P.ZONE).isoformat()
                    for row in (data["aire"], data["aire"]["pitjor"]):
                        row["hora"] = dt.datetime.fromisoformat(row["hora"]).replace(tzinfo=P.ZONE).isoformat()
                data["lpa"]["sources"][name] = "ok"
            except Exception as error:
                data["errors"].append(f"{name}: {error}")
                data["lpa"]["sources"][name] = "unavailable"
        if obs_future is not None:
            try:
                data["lpa"]["observations"] = obs_future.result()
            except Exception:
                data["lpa"]["observations"] = {"stations": [], "providers": observations.institutional_sources()}
                data["errors"].append("observaciones: no se pudo completar la recogida")
        if nature_future is not None:
            data['lpa']['environment'] = nature_future.result()
        if radar_future is not None:
            data['lpa']['radar'] = radar_future.result()
    for row in data["hores"] or []:
        # The hourly graph uses a different upstream contract from the alert cards.
        row["avisos"] = [{"font": "aemet", "tipus": [a["tipo"]], "nivell": a["nivel"]}
                         for a in data["avisos"] or []
                         if dt.datetime.fromisoformat(a["inicio"]) < dt.datetime.fromisoformat(row["fins"])
                         and dt.datetime.fromisoformat(a["fin"]) > dt.datetime.fromisoformat(row["hora"])]
    for key, offset in (("avui", 0), ("dema", 1)):
        day = now.date() + dt.timedelta(days=offset)
        rows = [r for r in data["hores"] or [] if r["hora"][:10] == str(day)]
        temps = [r["temperatura"] for r in rows if r["temperatura"] is not None]
        if temps:
            data["consultes"]["es"][key] = (f"<b>{'Hoy' if not offset else 'Mañana'} en {P.NAME}</b>\n"
                f"Temperatura prevista entre {min(temps):.1f} y {max(temps):.1f} °C. "
                "Estimación de Open-Meteo, sin calibración local.")
    for key in ("pollen", "trens", "transit", "llum"):
        data["consultes"]["es"][key] = P.UNAVAILABLE[key]
    counts = data.get('lpa', {}).get('environment', {}).get('pollen', {})
    if counts.get('last_count'):
        day = counts['last_count']['date']
        state = 'Dato antiguo; no describe el polen actual.' if counts['status'] == 'stale' else 'Último recuento observado; no es un pronóstico.'
        data['consultes']['es']['pollen'] = f'Polen de Las Palmas · SEAIC. Último recuento: {day}. {state} Detalle en Estaciones e historial.'
    return data


def write_json(destination, data):
    """Atomically replace public data, never expose a partially written JSON."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
        temp = Path(output.name)
        try:
            json.dump(data, output, ensure_ascii=False, allow_nan=False)
            output.close()
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)


def finalize(data, state_dir=None):
    """Persist the verification history before producing a compact public payload."""
    if state_dir:
        from .history import update
        update(data, state_dir)
    else:
        (data.get("lpa", {}).get("observations") or {}).pop("_archive", None)
        data.get('lpa', {}).get('environment', {}).get('pollen', {}).pop('_archive', None)
    return data


def publish(destination, data):
    """Publish the application payload and its documented public data companions."""
    write_json(destination, data)
    from .public_data import export
    export(Path(destination).parent, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    parser.add_argument("--state-dir", default=os.environ.get("LPA_STATE_DIR"))
    args = parser.parse_args()
    data = finalize(collect(), args.state_dir)
    publish(args.destination, data)
    for message in data["errors"]:
        print(message)
    return 0 if data["hores"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
