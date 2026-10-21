# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serve the upstream UI and refresh local data every 15 minutes."""
import argparse
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .build import build
from .collect import collect, finalize, publish


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.split('?', 1)[0].endswith('.json'):
            self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def refresh(destination, stop, state_dir):
    while not stop.is_set():
        try:
            data = finalize(collect(), state_dir)
            publish(destination, data)
            print('LPA update:', data['generat'], data['errors'], flush=True)
        except Exception as error:
            print('LPA update failed:', error, flush=True)
        stop.wait(900)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', default='/tmp/meteo-lpa')
    parser.add_argument('--state-dir', default=str(Path.home() / '.local/share/meteo-local/lpa'))
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--bind', default='127.0.0.1')
    args = parser.parse_args()
    destination = build(args.directory)
    stop = threading.Event()
    updater = threading.Thread(target=refresh, args=(Path(destination) / 'montflorit.json', stop, args.state_dir), daemon=True)
    updater.start()
    server = ThreadingHTTPServer((args.bind, args.port), partial(Handler, directory=str(destination)))
    try:
        server.serve_forever()
    finally:
        stop.set()
        server.server_close()
        updater.join(timeout=35)


if __name__ == '__main__':
    main()
