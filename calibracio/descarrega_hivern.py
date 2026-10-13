#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baja poco a poco los inviernos hora a hora de las vecinas de Weather
Underground, para ajustar la diferencia de la parte alta en las noches de
helada (ADR 0087).

De noviembre a marzo de los inviernos de INVIERNOS, el historial horario
(history/hourly: máxima, mínima y media de cada hora) de todas las vecinas
de config.VEINES. Cada consulta es una estación y un día, y la clave de
lectura da 1.500 al día que la web también usa (unas 400, hasta ~960 en modo
aviso): cada pasada baja como mucho --max días y deja el resto para la
siguiente. Lo hace el cron del NAS una vez al día, de madrugada, dentro del
contenedor; lo ya bajado no se repite. Cuando no queda nada escribe
«complet» en el directorio: es la señal para el análisis.

Se para sin gastar más si la API dice que se ha llegado al límite (429), si
la clave no vale o tras tres fallos seguidos.

Uso: python3 calibracio/descarrega_hivern.py [--dir DIR] [--max N]
(DIR por defecto, $ESTAT_DIR/hivern-wu o /estat/hivern-wu; N, 400)
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C  # noqa: E402
import wunderground as WU  # noqa: E402

# Primer año de cada invierno: el de 2024-2025 primero, el más frío.
INVIERNOS = (2024, 2023, 2025)
# La API admite 30 consultas por minuto.
PAUSA = 2.5


def dias(invierno):
    d, fin = dt.date(invierno, 11, 1), dt.date(invierno + 1, 3, 31)
    while d <= fin:
        yield d
        d += dt.timedelta(days=1)


def pendientes(directorio):
    for invierno in INVIERNOS:
        for d in dias(invierno):
            for est in C.VEINES:
                ruta = os.path.join(directorio, est, d.strftime("%Y%m%d") + ".json")
                if not os.path.exists(ruta):
                    yield est, d, ruta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.environ.get("ESTAT_DIR", "/estat"), "hivern-wu"))
    ap.add_argument("--max", type=int, default=400)
    a = ap.parse_args()
    marca = os.path.join(a.dir, "complet")
    if os.path.exists(marca):
        return 0
    hechas = fallos = 0
    for est, d, ruta in pendientes(a.dir):
        if hechas >= a.max:
            break
        try:
            obs = WU._consulta("history/hourly", {"stationId": est, "date": d.strftime("%Y%m%d")})
            fallos = 0
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                print(f"hivern-wu: límite de la API alcanzado tras {hechas} consultas")
                return 1
            fallos += 1
            obs = None
        except RuntimeError as ex:
            print(f"hivern-wu: {ex}")
            return 1
        except (urllib.error.URLError, OSError, ValueError):
            fallos += 1
            obs = None
        hechas += 1
        if obs is not None:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta + ".tmp", "w") as f:
                json.dump(obs, f)
            os.replace(ruta + ".tmp", ruta)
        elif fallos >= 3:
            print(f"hivern-wu: tres fallos seguidos ({est} {d}); se sigue mañana")
            return 1
        time.sleep(PAUSA)
    queden = sum(1 for _ in pendientes(a.dir))
    print(f"hivern-wu: {hechas} consultas; quedan {queden}")
    if queden == 0:
        with open(marca, "w") as f:
            f.write(dt.datetime.now().isoformat(timespec="minutes") + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
