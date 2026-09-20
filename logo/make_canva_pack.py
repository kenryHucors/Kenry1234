# -*- coding: utf-8 -*-
"""
Build a Canva-ready pack from build_logo.py.

Canva's SVG importer is unreliable with clipPath/mask, and Canva can only
recolour a shape that is genuinely one fill colour. So this script emits:

  * SVGs with no clipPath and an explicit width/height
  * a flattened single-colour SVG (grain is a real hole, not a white stroke)
    so Canva's colour picker recolours the whole logo in one click
  * trimmed transparent PNGs - no dead canvas to fight with when placing
"""
import importlib.util, os, re, subprocess
import numpy as np
from PIL import Image
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "canva")
os.makedirs(PACK, exist_ok=True)

spec = importlib.util.spec_from_file_location("bl", os.path.join(HERE, "build_logo.py"))
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)

def png(svg, path, width, height=None):
    cairosvg.svg2png(bytestring=svg.encode(), write_to=path,
                     output_width=width, output_height=height or width)

def trim(path, pad_frac=0.03, max_side=3000):
    """Crop away empty canvas, keep transparency, cap the longest side."""
    im = Image.open(path).convert("RGBA")
    bbox = im.split()[3].getbbox()
    if bbox:
        pad = int(max(im.width, im.height) * pad_frac)
        im = im.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                      min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad)))
    if max_side and max(im.size) != max_side:
        k = max_side / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    im.save(path)
    return im.size

def flatten_one_colour(colour="#3F1A08", scale=4, footer=True):
    """Render the 1-colour lockup, then re-trace it so grain becomes a real
    hole in a single-colour shape - this is what Canva can recolour."""
    svg = bl.build(colour=False, background=True, canva=True, footer=footer)
    tmp = os.path.join(PACK, "_flat.png")
    png(svg, tmp, 1000 * scale)
    g = np.array(Image.open(tmp).convert("L"))
    pbm, out = os.path.join(PACK, "_flat.pbm"), os.path.join(PACK, "_flat.svg")
    Image.fromarray(np.where(g < 150, 0, 255).astype(np.uint8), "L").convert("1").save(pbm)
    subprocess.run(["potrace", "-s", "-o", out, "--turdsize", "3",
                    "--alphamax", "1.0", "--opttolerance", "0.2", pbm], check=True)
    paths = "\n".join(re.findall(r'<path d="[^"]*"\s*/>', open(out).read()))
    for f in (tmp, pbm, out):
        os.remove(f)
    n = 1000 * scale
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" '
            f'width="1000" height="1000">\n'
            f'<g transform="scale({1.0/scale})">'
            f'<g transform="translate(0,{n}) scale(0.1,-0.1)" fill="{colour}" stroke="none">\n'
            f'{paths}\n</g></g>\n</svg>\n')

JOBS = [
    # full lockup, exactly as designed
    ("logo-wood-colour",         dict(colour=True,  background=False, canva=True), 4000, False),
    ("logo-wood-colour-whitebg", dict(colour=True,  background=True,  canva=True), 3000, False),
    ("logo-wood-1colour",        dict(colour=False, background=False, canva=True), 4000, False),
    # compact: drops the CHINA / WORLDWIDE SUPPLY strapline that sits far below,
    # so there is no dead space to fight with when placing it in a Canva design
    ("logo-wood-colour-compact", dict(colour=True,  background=False, canva=True, footer=False), 4000, False),
    ("logo-wood-1colour-compact",dict(colour=False, background=False, canva=True, footer=False), 4000, False),
    # symbol only
    ("mark-wood-colour",         dict(colour=True,  background=False, canva=True, mark_only=True), 2200, True),
]

if __name__ == "__main__":
    for name, kw, w, is_mark in JOBS:
        svg = bl.build(**kw)
        open(os.path.join(PACK, name + ".svg"), "w").write(svg)
        h = round(w * 375 / 336) if is_mark else w
        p = os.path.join(PACK, name + ".png")
        png(svg, p, w, h)
        size = trim(p) if not kw["background"] else Image.open(p).size
        print(f"{name:28s} svg + png {size[0]}x{size[1]}")

    MONO = [
        ("logo-1colour-recolourable",         "#3F1A08", True),
        ("logo-1colour-recolourable-compact", "#3F1A08", False),
        # true black and white - the grain is a real hole, so the wooden leg
        # still reads with no colour at all
        ("logo-black",                        "#000000", True),
        ("logo-black-compact",                "#000000", False),
        ("logo-white-for-dark-bg",            "#FFFFFF", True),
        ("logo-white-for-dark-bg-compact",    "#FFFFFF", False),
    ]
    for nm, col, ft in MONO:
        flat = flatten_one_colour(colour=col, footer=ft)
        open(os.path.join(PACK, nm + ".svg"), "w").write(flat)
        p = os.path.join(PACK, nm + ".png")
        png(flat, p, 4000)
        print(f"{nm:34s} svg + png", trim(p))
