# SPDX-License-Identifier: AGPL-3.0-or-later
"""Draw the social sharing card (Open Graph, 1200×630) committed in assets/.

The card is static: social networks cache it, so it shows no weather values.
Run `python3 -m lpa.og_image` after a design change and commit the PNG.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
OUTPUT = HERE / 'assets/og-image.png'
SIZE = (1200, 630)
SCALE = 3  # supersampling for smooth edges
FONTS = ('/usr/share/fonts/opentype/inter/Inter-{}.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf')
# Gran Canaria bounding box in the reviewed AEMET coastline.
ISLAND = (-15.85, 27.72, -15.35, 28.19)
CITY = (-15.436, 28.124)


def font(weight, size):
    """Inter when installed, DejaVu otherwise; the PIL default as a last resort."""
    for pattern, name in zip(FONTS, (weight, {'Bold': '-Bold', 'SemiBold': '-Bold'}.get(weight, ''))):
        path = Path(pattern.format(name))
        if path.exists():
            return ImageFont.truetype(str(path), size * SCALE)
    return ImageFont.load_default(size * SCALE)


def gradient(size, stops):
    """Vertical gradient through (position, colour) stops."""
    width, height = size
    column = Image.new('RGB', (1, height))
    for y in range(height):
        t = y / (height - 1)
        (p0, c0), (p1, c1) = next((a, b) for a, b in zip(stops, stops[1:]) if a[0] <= t <= b[0])
        f = (t - p0) / (p1 - p0) if p1 > p0 else 0
        column.putpixel((0, y), tuple(round(a + (b - a) * f) for a, b in zip(c0, c1)))
    return column.resize(size)


def s(*values):
    return [v * SCALE for v in values]


def island_rings():
    rings = json.loads((HERE / 'assets/canarias-coast.json').read_text())['rings']
    west, south, east, north = ISLAND
    return [ring for ring in rings if len(ring) > 20
            and all(west <= lon <= east and south <= lat <= north for lon, lat in ring)]


def draw():
    width, height = SIZE[0] * SCALE, SIZE[1] * SCALE
    hex_rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    card = gradient((width, height), [(0, hex_rgb('#0b3b66')), (.55, hex_rgb('#0e7fb8')), (1, hex_rgb('#38bdf8'))])

    # Sun with a soft glow, top right.
    glow = Image.new('RGBA', card.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(s(860, -40, 1180, 280), fill=(253, 224, 71, 150))
    card = Image.alpha_composite(card.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(60 * SCALE)))
    d = ImageDraw.Draw(card, 'RGBA')
    d.ellipse(s(945, 45, 1095, 195), fill='#fcd34d', outline='#f59e0b', width=5 * SCALE)
    cx, cy = 1020, 120
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        d.line(s(cx + math.cos(a) * 98, cy + math.sin(a) * 98, cx + math.cos(a) * 128, cy + math.sin(a) * 128),
               fill='#fcd34d', width=9 * SCALE)

    # A cloud passing in front of the sun.
    cloud = Image.new('RGBA', card.size, (0, 0, 0, 0))
    c = ImageDraw.Draw(cloud)
    for box in ((880, 170, 990, 270), (935, 130, 1065, 260), (1020, 175, 1120, 270)):
        c.ellipse(s(*box), fill=(255, 255, 255, 255))
    c.rounded_rectangle(s(880, 215, 1120, 270), radius=27 * SCALE, fill=(255, 255, 255, 255))
    shadow = cloud.filter(ImageFilter.GaussianBlur(8 * SCALE))
    card = Image.alpha_composite(card, Image.eval(shadow, lambda v: v // 4))
    card = Image.alpha_composite(card, cloud)

    # Ocean with gentle waves and Gran Canaria, Las Palmas marked.
    sea = Image.new('RGBA', card.size, (0, 0, 0, 0))
    w = ImageDraw.Draw(sea)
    top = 430
    for n, (alpha, offset) in enumerate(((120, 0), (160, 26), (210, 56))):
        points = [(x, top + offset + 9 * math.sin(x / 70 + n * 1.7)) for x in range(0, SIZE[0] + 10, 10)]
        w.polygon([(x * SCALE, y * SCALE) for x, y in points] + s(SIZE[0], SIZE[1], 0, SIZE[1]),
                  fill=(7, 54, 99, alpha))
    # RGB target so that translucent fills blend instead of replacing pixels.
    card = Image.alpha_composite(card, sea).convert('RGB')
    d = ImageDraw.Draw(card, 'RGBA')
    west, south, east, north = ISLAND
    ox, oy, scale = 850, 385, 460  # pixels per degree; latitude stretched for the local cosine
    k = math.cos(math.radians(28))
    project = lambda lon, lat: ((ox + (lon - west) * scale * k) * SCALE, (oy + (north - lat) * scale) * SCALE)
    for ring in island_rings():
        d.polygon([project(*p) for p in ring], fill='#f5e6c8', outline='#7c5c2e', width=2 * SCALE)
    x, y = project(*CITY)
    d.ellipse((x - 11 * SCALE, y - 11 * SCALE, x + 11 * SCALE, y + 11 * SCALE), fill='#ef4444', outline='white', width=4 * SCALE)
    d.text((x + 18 * SCALE, y - 34 * SCALE), 'Las Palmas', font=font('SemiBold', 24), fill='white',
           stroke_width=3 * SCALE, stroke_fill='#0b3b66')

    # Title and features.
    d.text(s(72, 70), 'Tiempo en', font=font('Medium', 40), fill='#e0f2fe')
    d.text(s(68, 112), 'Las Palmas', font=font('Bold', 104), fill='white')
    d.text(s(72, 240), 'de Gran Canaria', font=font('Medium', 44), fill='#e0f2fe')
    x = 72
    chip = font('SemiBold', 26)
    for label in ('7 días', 'Radar', 'Viento', 'Calima', 'Mar'):
        text_w = d.textlength(label, font=chip) / SCALE
        d.rounded_rectangle(s(x, 330, x + text_w + 40, 380), radius=25 * SCALE, fill=(255, 255, 255, 46),
                            outline=(255, 255, 255, 110), width=2 * SCALE)
        d.text(s(x + 20, 341), label, font=chip, fill='white')
        x += text_w + 54
    d.text(s(72, 560), 'erseco.github.io/meteo-local', font=font('Medium', 26), fill='#e0f2fe')
    return card.resize(SIZE, Image.Resampling.LANCZOS)


if __name__ == '__main__':
    draw().save(OUTPUT, optimize=True)
    print(OUTPUT)
