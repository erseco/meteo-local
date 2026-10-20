# SPDX-License-Identifier: AGPL-3.0-or-later
"""Display AEMET's actual Canary reflectivity scans; never infer surface rain.

The public viewer supplies PNGs and WGS84 bounds, rendered on its Web Mercator
canvas. We use that same projection for the image, coastline and city marker.
No colour-to-rain-rate conversion or arrival-time extrapolation is performed.
"""
import base64
import concurrent.futures
import datetime as dt
import io
import json
import math
from pathlib import Path
import re
import urllib.request

from PIL import Image, ImageDraw, ImageFont

BASE = 'https://www.aemet.es/es/api-eltiempo/radar/'
SOURCE = 'https://www.aemet.es/es/eltiempo/observacion/radar?w=1'
MAX_AGE = 45
VIEW = (-18.5, 26.9, -13.0, 29.7)
SIZE = (1000, 580)


def read(url):
    request = urllib.request.Request(url, headers={'User-Agent':'meteo-local-lpa/0.4'})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(8_000_001)
    if len(raw) > 8_000_000:
        raise ValueError('Radar response too large')
    return raw


def mercator(latitude):
    return math.log(math.tan(math.pi / 4 + math.radians(latitude) / 2))


def scans(payload, now):
    """Whitelist the exact LPA product and cross-check offset dates against UTC names."""
    rows = {}
    for group in payload:
        if group.get('Producto') != 'PPI.Z_005_240':
            continue
        for item in group.get('Elementos', []):
            filename = item.get('Nombre fichero', '')
            match = re.fullmatch(r'LPA(\d{12})\.PPI\.Z_005_240\.png', filename)
            if item.get('Nombre radar') != 'LPA' or not match:
                continue
            stamp = dt.datetime.strptime(match[1], '%y%m%d%H%M%S').replace(tzinfo=dt.timezone.utc)
            declared = dt.datetime.fromisoformat(item['Fecha'])
            if declared.tzinfo is None or declared != stamp:
                continue
            age = (now - stamp).total_seconds() / 60
            if -5 <= age <= 120:
                rows[stamp] = {'observed_at':stamp.isoformat(), 'file':filename}
    # Bounded downloads; retain a useful recent sequence, not every archive scan.
    return [rows[t] for t in sorted(rows)[-6:]]


def render(raw, bounds):
    """Project the source raster and reviewed AEMET coastline into one map."""
    points = bounds[0] if isinstance(bounds[0][0], list) else bounds
    west, east = min(p[0] for p in points), max(p[0] for p in points)
    south, north = min(p[1] for p in points), max(p[1] for p in points)
    if not (-30 < west < VIEW[0] < VIEW[2] < east < 0 and 10 < south < VIEW[1] < VIEW[3] < north < 45):
        raise ValueError('Unexpected Canary radar bounds')
    image = Image.open(io.BytesIO(raw))
    if image.format != 'PNG' or not (500 <= image.width <= 5000 and 500 <= image.height <= 5000):
        raise ValueError('Unexpected radar raster')
    def source_pixel(lon, lat):
        return ((lon-west)/(east-west)*image.width,
                (mercator(north)-mercator(lat))/(mercator(north)-mercator(south))*image.height)
    left, top = source_pixel(VIEW[0], VIEW[3])
    right, bottom = source_pixel(VIEW[2], VIEW[1])
    layer = image.convert('RGBA').resize(SIZE, Image.Resampling.NEAREST, box=(left,top,right,bottom))
    canvas = Image.new('RGBA', SIZE, '#e5f1f7')
    def pixel(lon, lat):
        return ((lon-VIEW[0])/(VIEW[2]-VIEW[0])*SIZE[0],
                (mercator(VIEW[3])-mercator(lat))/(mercator(VIEW[3])-mercator(VIEW[1]))*SIZE[1])
    coast = json.loads((Path(__file__).parent/'assets/canarias-coast.json').read_text())['rings']
    draw = ImageDraw.Draw(canvas)
    for ring in coast:
        draw.polygon([pixel(*p) for p in ring], fill='#e1e5df')
    canvas = Image.alpha_composite(canvas, layer)
    draw = ImageDraw.Draw(canvas)
    for ring in coast:
        draw.line([pixel(*p) for p in ring], fill='#344b56', width=1)
    font = ImageFont.load_default(size=17)
    for lon, lat, name in [(-17.9,28.9,'La Palma'),(-18.3,27.65,'El Hierro'),
                           (-17.3,28.3,'La Gomera'),(-16.8,28.7,'Tenerife'),
                           (-15.7,27.65,'Gran Canaria'),(-14.3,28.8,'Fuerteventura'),
                           (-13.85,29.5,'Lanzarote')]:
        draw.text(pixel(lon,lat), name, font=font, fill='#172b36', stroke_width=2, stroke_fill='#ffffff')
    x,y = pixel(-15.436,28.124)
    draw.ellipse((x-5,y-5,x+5,y+5),fill='#ffffff',outline='#142f41',width=2)
    draw.text((x+9,y-12),'Las Palmas',font=font,fill='#142f41',stroke_width=2,stroke_fill='#ffffff')
    output = io.BytesIO()
    canvas.convert('RGB').save(output,format='PNG',optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')


def collect(now, reader=read):
    result = {'status':'unavailable','provider':'AEMET','url':SOURCE,
              'max_age_minutes':MAX_AGE,'frames':[], 'legend':[],
              'detail':'Reflectividad en dBZ. No equivale a lluvia medida en el suelo ni permite asegurar cuándo llegará. El área gris puede carecer de cobertura.'}
    try:
        rows = scans(json.loads(reader(BASE+'timeline/PPI/CAN')), now)
        if not rows:
            raise ValueError('No recent LPA scans')
        legend = json.loads(reader(BASE+'leyenda-radar/PPI'))
        if legend['Producto'] != 'PPI':
            raise ValueError('Radar legend changed')
        for entry in legend['Lista RGBA']:
            rgb = [int(c) for c in entry['RGBA'][:3]]
            values = entry['Valores']
            if len(rgb) != 3 or any(c<0 or c>255 for c in rgb) or len(values) != 2:
                raise ValueError('Invalid reflectivity legend')
            result['legend'].append({'color':'#'+''.join(f'{c:02x}' for c in rgb),
                'label':f'{values[0]}–{values[1]} dBZ' if values[1] != '' else f'≥{values[0]} dBZ'})
        def frame(row):
            try:
                bounds = json.loads(reader(BASE+'bounds-radar/PPI/'+row['file']))
                raw = reader(BASE+'imagen-radar/PPI/'+row['file'])
                return {'observed_at':row['observed_at'],'image':render(raw,bounds)}
            except Exception:
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            result['frames'] = [f for f in pool.map(frame,rows) if f]
        if not result['frames']:
            raise ValueError('No usable LPA rasters')
        result['observed_at'] = result['frames'][-1]['observed_at']
        age = (now-dt.datetime.fromisoformat(result['observed_at'])).total_seconds()/60
        result['status'] = 'ok' if age <= MAX_AGE else 'stale'
    except Exception as error:
        result['detail'] += ' No se pudo completar la consulta: '+type(error).__name__+'.'
    return result
