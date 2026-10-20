# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate deterministic network-free browser data at the current clock."""
import datetime as dt
import json
import sys

from lpa.collect import collect, write_json, FORECAST, AIR
from lpa.tests.test_lpa import forecast, feed
import aire


def create(destination):
    now = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
    def reader(url, params):
        if url == FORECAST:
            return json.dumps(forecast(now))
        if url == AIR:
            h = {key: [10] * 24 for key in aire.CONTAMINANTS}
            h['time'] = forecast(now)['hourly']['time'][:24]
            return json.dumps({'hourly': h})
        return feed(updated=now.isoformat())
    data = collect(now, reader)
    write_json(destination, data)


if __name__ == '__main__': create(sys.argv[1])
