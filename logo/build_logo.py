# -*- coding: utf-8 -*-
"""
SHENGHEFENG / 圣合丰  ——  logo rebuild.

The original mark read as a METAL sofa leg: near-black colour, a thin flat
mounting plate and a long needle-thin parallel shaft with extruded slots.

This script keeps the SHENGHEFENG lettering exactly as drawn and replaces
everything below it with a turned/tapered WOODEN sofa leg:

  * warm walnut-oak colour instead of near-black
  * longitudinal wood grain plus a cathedral (flat-sawn) figure
  * a top block, a turned collar bead and a turned foot
  * a 2.4:1 taper with a flat foot instead of a needle point

Requires: pillow, numpy, cairosvg, potrace
"""
import math, os, re, subprocess
from PIL import Image
import numpy as np
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("LOGO_SRC", os.path.join(HERE, "source-original.png"))
OUT = HERE
UP = 3                                   # supersample factor for tracing

GRAY = np.array(Image.open(SRC).convert("L")).astype(np.float32)

# --------------------------------------------------------------- vectorise
_cache = {}
def trace(y0, y1, name):
    """Vectorise rows y0..y1 of the source artwork; returns SVG path data."""
    if name in _cache:
        return _cache[name]
    sub = np.full_like(GRAY, 255.0)
    sub[y0:y1 + 1] = GRAY[y0:y1 + 1]
    img = Image.fromarray(sub.astype(np.uint8), "L").resize((1000 * UP, 1000 * UP), Image.LANCZOS)
    pbm, svg = os.path.join(HERE, "_" + name + ".pbm"), os.path.join(HERE, "_" + name + ".svg")
    img.point(lambda v: 0 if v < 160 else 255).convert("1").save(pbm)
    subprocess.run(["potrace", "-s", "-o", svg, "--turdsize", "4",
                    "--alphamax", "1.0", "--opttolerance", "0.2", pbm], check=True)
    _cache[name] = "\n".join(re.findall(r'<path d="[^"]*"\s*/>', open(svg).read()))
    os.remove(pbm); os.remove(svg)
    return _cache[name]

def group(y0, y1, name, fill, dy=0.0):
    return (f'<g transform="translate(0,{dy}) scale({1.0 / UP})">'
            f'<g transform="translate(0,{1000 * UP}) scale(0.1,-0.1)" fill="{fill}" stroke="none">'
            f'{trace(y0, y1, name)}</g></g>')

# ---------------------------------------------------------- leg geometry
CX, TOP, BOT = 499.5, 228.0, 505.0       # joins the lettering where it is 104 wide

def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def hw(y):
    """Half-width of the wooden leg at height y."""
    if y < TOP or y > BOT:
        return 0.0
    if y <= 248:                                            # top block, meets the frame
        return 52 - 2 * sm((y - TOP) / 20)
    if y <= 256:                                            # chamfer under the block
        return 50 - 5 * sm((y - 248) / 8)
    if y <= 272:                                            # turned collar bead
        t = (y - 256) / 16
        return 45 - t + 5 * math.sin(math.pi * t)
    if y <= 458:                                            # tapered body, faint entasis
        t = (y - 272) / 186
        return 44 + (22.5 - 44) * t + 1.5 * math.sin(math.pi * t)
    if y <= 468:                                            # foot flare
        return 22.5 + 4 * sm((y - 458) / 10)
    if y <= 480:                                            # under-bead of the foot
        return 26.5 - 3.5 * sm((y - 468) / 12)
    if y <= 497:                                            # toe
        return 23 - 2.5 * sm((y - 480) / 17)
    r = 8.0                                                 # flat foot, eased corners
    return 12.5 + r * math.sqrt(max(0.0, 1 - ((y - 497) / r) ** 2))

def outline():
    ys = [TOP + i * 0.5 for i in range(int((BOT - TOP) / 0.5) + 1)]
    pts = [(CX + hw(y), y) for y in ys] + [(CX - hw(y), y) for y in reversed(ys)]
    return ("M {:.2f} {:.2f} ".format(*pts[0])
            + " ".join(f"L {x:.2f} {y:.2f}" for x, y in pts[1:]) + " Z")

# ------------------------------------------------------------- wood grain
def grain(p, phase, freq, amp, y0=None, y1=None):
    y0 = TOP + 4 if y0 is None else y0
    y1 = BOT - 5 if y1 is None else y1
    pts, y = [], y0
    while y <= y1:
        w = hw(y)
        x = CX + p * w + amp * math.sin(freq * (y - y0) / 100.0 * math.pi * 2 + phase) * (w / 52.0)
        pts.append((x, y))
        y += 2.0
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)

def cathedral(cx, y_apex, y_base, spread):
    l, r = cx - spread, cx + spread
    h = y_base - y_apex
    return (f"M {l:.2f} {y_base:.2f} C {l + spread*0.3:.2f} {y_base - h*0.55:.2f} "
            f"{cx - spread*0.28:.2f} {y_apex + h*0.2:.2f} {cx:.2f} {y_apex:.2f} "
            f"C {cx + spread*0.28:.2f} {y_apex + h*0.2:.2f} "
            f"{r - spread*0.3:.2f} {y_base - h*0.55:.2f} {r:.2f} {y_base:.2f}")

GRAINS_FULL = [(-0.70, 0.5, 1.2, 1.8), (-0.38, 2.3, 0.9, 2.2), (-0.08, 4.1, 1.4, 1.5),
               (0.26, 1.1, 1.0, 2.0), (0.58, 3.4, 1.3, 1.7), (0.82, 5.2, 0.8, 1.3)]
# short, staggered strokes - a 1-colour mark needs a hint of grain, not a bundle of sticks
GRAINS_FLAT = [(-0.50, 2.3, 0.7, 1.6, 292, 392), (0.06, 4.1, 0.9, 1.2, 320, 436),
               (0.54, 1.1, 0.8, 1.5, 284, 372)]
RINGS_FULL = [248.0, 256.0, 272.0, 458.0, 468.0, 480.0]
RINGS_FLAT = [250.0, 272.0, 464.0, 478.0]

def grain_svg(colour, opacity, width, lines, rings, figures):
    s = [f'<g fill="none" stroke="{colour}" stroke-opacity="{opacity}" '
         f'stroke-width="{width}" stroke-linecap="round">']
    for ln in lines:
        s.append(f'<path d="{grain(*ln)}"/>')
    s.append("</g>")
    if figures:
        s.append(f'<g fill="none" stroke="{colour}" stroke-opacity="{opacity*0.7:.2f}" '
                 f'stroke-width="{width*0.9:.2f}" stroke-linecap="round">')
        for yb, sp, ya in figures:
            s.append(f'<path d="{cathedral(CX - 4, ya, yb, sp)}"/>')
        s.append("</g>")
    s.append(f'<g fill="none" stroke="{colour}" stroke-opacity="{min(1.0, opacity*1.6):.2f}" '
             f'stroke-width="{width*1.2:.2f}" stroke-linecap="round">')
    for y in rings:
        s.append(f'<path d="M {CX-hw(y)+2.5:.2f} {y:.2f} L {CX+hw(y)-2.5:.2f} {y:.2f}"/>')
    s.append("</g>")
    return "\n".join(s)

# -------------------------------------------------------------- composition
BAND = (158, 230)        # SHENGHEFENG lettering - untouched
CN = (430, 548)          # 圣合丰 calligraphy
TAG = (563, 588)         # SOFA WOODEN LEGS
FOOT = (890, 910)        # CHINA / WORLDWIDE SUPPLY
SHIFT = 99.0             # the leg is longer, so the lower text moves down
DARK = "#3F1A08"         # existing brand brown, kept for the lettering

WOOD_GRADIENT = '''<linearGradient id="wood" x1="447" y1="0" x2="553" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="0.00" stop-color="#53300F"/><stop offset="0.14" stop-color="#7C4C1F"/>
  <stop offset="0.34" stop-color="#9C6733"/><stop offset="0.50" stop-color="#AE7A44"/>
  <stop offset="0.68" stop-color="#8E5C29"/><stop offset="0.87" stop-color="#673C16"/>
  <stop offset="1.00" stop-color="#452409"/>
 </linearGradient>'''

def build(colour=True, background=True, mark_only=False, canva=False, footer=True):
    d = outline()
    if colour:
        leg_fill = "url(#wood)"
        g = grain_svg("#4A2610", 0.30, 1.8, GRAINS_FULL, RINGS_FULL, ((392, 13, 306), (372, 8, 302)))
        edge = f'<path d="{d}" fill="none" stroke="#44220E" stroke-width="2"/>'
    else:
        leg_fill = DARK
        g = grain_svg("#FFFFFF", 0.95, 3.2, GRAINS_FLAT, RINGS_FLAT, ())
        edge = ""

    wrap = '<g>' if canva else '<g clip-path="url(#lc)">'
    body = (f'{group(*BAND, "band", DARK)}\n'
            f'<g><path d="{d}" fill="{leg_fill}"/>'
            f'{wrap}{g}</g>{edge}</g>')
    if not mark_only:
        body += (f'\n{group(*CN, "cn", "#111111", SHIFT)}'
                 f'\n{group(*TAG, "tag", "#111111", SHIFT)}')
        if footer:
            body += f'\n{group(*FOOT, "foot", "#111111")}'

    vb = "332 146 336 375" if mark_only else "0 0 1000 1000"
    _, _, vw, vh = (float(v) for v in vb.split())
    bg = ('<rect x="-10" y="-10" width="1100" height="1100" fill="#FFFFFF"/>'
          if background else "")
    clip = "" if canva else f'\n <clipPath id="lc"><path d="{d}"/></clipPath>'
    size = f' width="{vw:g}" height="{vh:g}"'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"{size}>\n'
            f'<defs>\n {WOOD_GRADIENT}{clip}\n</defs>\n'
            f'{bg}\n{body}\n</svg>\n')

# ------------------------------------------------------------------ outputs
VARIANTS = [
    ("shenghefeng-logo-wood",              dict(colour=True,  background=True),  1000),
    ("shenghefeng-logo-wood-transparent",  dict(colour=True,  background=False), 1000),
    ("shenghefeng-logo-wood-1color",       dict(colour=False, background=True),  1000),
    ("shenghefeng-mark-wood",              dict(colour=True,  background=False, mark_only=True), 700),
]

if __name__ == "__main__":
    for name, kw, w in VARIANTS:
        svg = build(**kw)
        open(os.path.join(OUT, name + ".svg"), "w").write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, name + ".png"),
                         output_width=w, output_height=int(w * (375 / 336) if kw.get("mark_only") else w))
        cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, name + "@2x.png"),
                         output_width=w * 2, output_height=int(w * 2 * (375 / 336) if kw.get("mark_only") else w * 2))
        print("wrote", name)
