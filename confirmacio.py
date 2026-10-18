#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Les preguntes a Juanjo per Telegram, amb botons, del que només ell pot veure
des de casa (la boira, ADR 0100; el plugim, ADR 0019), i les seves respostes.

Fa servir el bot dels agents (avisar-juanjo) i llegeix les respostes sense
marcar-les com a llegides (getUpdates sense offset), per no treure res a qui
llegeixi el xat. Cada pregunta té el seu prefix als botons («boira:si»), el
seu fitxer de preguntes i el de respostes, al registre.
"""
import csv
import datetime as dt
import json
import os
import urllib.parse
import urllib.request

CONFIG_BOT = os.path.expanduser("~/.config/avisar-juanjo/config.json")


def telegram(metode, config=None, **params):
    c = json.load(open(config or CONFIG_BOT, encoding="utf-8"))
    dades = urllib.parse.urlencode({k: json.dumps(v) if isinstance(v, (dict, list)) else v
                                    for k, v in params.items()}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{c['token']}/{metode}", dades, timeout=30) as r:
        return json.load(r).get("result"), c


def files(ruta):
    return list(csv.DictReader(open(ruta, encoding="utf-8"))) if os.path.exists(ruta) else []


def afegeix(ruta, camps, fila):
    nou = not os.path.exists(ruta)
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, camps)
        if nou:
            w.writeheader()
        w.writerow(fila)


def respostes(prefix, preguntes, confirmacions, textos, camps, telegram, ara):
    """Les respostes als botons d'una pregunta, una vegada cadascuna, a
    confirmacions, amb els camps de la pregunta que diu camps. Només consulta
    Telegram si n'hi ha alguna de les darreres 24 hores sense resposta: el
    rellotge ho mira cada minut, perquè la confirmació arribi de seguida."""
    pendents = {int(p["missatge"]): p for p in files(preguntes)}
    fetes = {int(r["missatge"]) for r in files(confirmacions)}
    if not any(m not in fetes and ara - dt.datetime.fromisoformat(p["t"]) < dt.timedelta(hours=24)
               for m, p in pendents.items()):
        return 0
    updates, cfg = telegram("getUpdates", allowed_updates=["callback_query"])
    n = 0
    for u in updates or []:
        q = u.get("callback_query") or {}
        m = (q.get("message") or {}).get("message_id")
        dada = q.get("data") or ""
        if not dada.startswith(prefix + ":") or m not in pendents or m in fetes \
                or str((q.get("from") or {}).get("id")) != str(cfg["chat_id"]):
            continue
        clau = dada.split(":", 1)[1]
        p = pendents[m]
        afegeix(confirmacions, ["missatge", "pregunta", "resposta"] + camps,
                {"missatge": m, "pregunta": p["t"], "resposta": clau, **{k: p.get(k) for k in camps}})
        fetes.add(m)
        n += 1
        # Primer, el missatge diu què s'ha apuntat: és la confirmació que es
        # veu. Després, el toc; si ha passat massa estona, Telegram ja no
        # l'accepta, i abans això deixava el missatge sense canviar (17-10-2026).
        try:
            telegram("editMessageReplyMarkup", chat_id=cfg["chat_id"], message_id=m,
                     reply_markup={"inline_keyboard": [[{"text": f"Apuntado: {textos.get(clau, clau)}",
                                                         "callback_data": f"{prefix}:fet"}]]})
        except Exception:
            pass
        try:
            telegram("answerCallbackQuery", callback_query_id=q["id"], text="Apuntado, gracias")
        except Exception:
            pass
    return n
