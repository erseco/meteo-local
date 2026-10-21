# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect the official API contract from the deployment network."""
import json
import os
import urllib.request

base = 'https://sensores.grafcan.es/api/v1.0/'
key = os.environ.get('GRAFCAN_API_KEY', '').strip()
if not key:
    raise SystemExit('GRAFCAN_API_KEY is not configured')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
for path in ('?format=openapi', 'things/14/'):
    request = urllib.request.Request(base + path, headers={
        'Accept': 'application/json', 'Authorization': 'Api-Key ' + key})
    try:
        with opener.open(request, timeout=30) as response:
            value = json.loads(response.read(2000000))
        if 'paths' in value:
            value = {'paths': value['paths'], 'definitions': value.get('definitions', {}),
                     'components': value.get('components', {})}
        print(path, json.dumps(value, ensure_ascii=False)[:80000])
    except Exception as error:
        print(path, type(error).__name__, getattr(error, 'code', 'request failed'))
