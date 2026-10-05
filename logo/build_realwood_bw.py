# -*- coding: utf-8 -*-
"""
Black-and-white versions of the realistic wood-grain logo.

  * GRAY  - the photographic leg desaturated, like a black-and-white photo.
            For black-and-white printing, newspapers, single-ink catalogues.
  * BW    - pure 1-bit, woodcut / engraving style. The white grain lines follow
            the SAME growth-ring field as the colour version, and their width
            follows the lighting (wide on the lit side, thin in shadow), so the
            leg keeps its turned 3D form with only black and white.
            Traced to a single-colour vector: screen print, hot-foil, laser
            engraving, stamps, carton printing, and one-click recolour in Canva.
"""
import importlib.util, io, os, re, subprocess, sys
import numpy as np
from PIL import Image
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "realwood")

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

rw = load("rw", os.path.join(HERE, "build_realwood.py"))
bl, S, F = rw.bl, rw.S, rw.FIELDS
COLOUR_LEG = rw.LEG_IMG

# ------------------------------------------------------------ grayscale leg
def gray_leg():
    a = np.asarray(COLOUR_LEG).astype(np.float32)
    g = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    g = np.clip((g - 18) * 1.30, 0, 255)                 # wood is mid-dark: open it up
    out = np.dstack([g, g, g, a[..., 3]]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")

# ------------------------------------------------------ 1-bit engraving leg
def engraved_leg():
    t, spacing, shade, groove, inside, a, Y, cz = (
        F[k] for k in ("t", "spacing", "shade", "groove", "inside", "a", "Y", "cz"))
    b = np.clip((shade - 0.30) / 0.80, 0, 1)            # 0 = shadow, 1 = highlight
    # woodcut: mostly black, thin white grain lines that widen in the light and
    # fade out toward the sides, so the sides go solid black like a shaded cylinder
    width = (0.05 + 0.24 * b) * np.clip(cz * 1.25, 0, 1) ** 1.6
    width = np.where(width * spacing < 0.40, 0, width)   # drop lines too thin to print
    grain = t < width
    # turned details (chamfer + collar bead, foot) carry a clean highlight, not rings
    detail = ((Y > 247) & (Y < 273)) | ((Y > 457) & (Y < 481))
    highlight = (b > 0.93) & (cz > 0.45)                 # a thin glint, like a lacquered ring
    white = np.where(detail, highlight, grain)
    white &= inside > 1.6 * S                            # solid black rim keeps the silhouette
    white &= (bl.BOT - Y) > 1.6                          # ... and along the flat foot
    white &= groove < 0.30                               # turned grooves stay black
    ink = (a > 0.5) & ~white
    out = np.zeros(ink.shape + (4,), np.uint8)
    out[..., 3] = np.where(ink, 255, 0)
    return Image.fromarray(out, "RGBA")

# ------------------------------------------------------------------ helpers
def composite(leg, svg, vb, offset=(0.0, 0.0), ppu=S):
    rw.LEG_IMG = leg
    try:
        return rw.composite(svg, vb, ppu, offset)
    finally:
        rw.LEG_IMG = COLOUR_LEG

def vectorize(im, vb, fill):
    """1-bit trace of black-on-white artwork -> single-colour SVG in vb units."""
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255)); flat.alpha_composite(im)
    g = np.asarray(flat.convert("L"))
    tmp = os.path.join(OUT, "_bw")
    Image.fromarray(np.where(g < 128, 0, 255).astype(np.uint8), "L").convert("1").save(tmp + ".pbm")
    subprocess.run(["potrace", "-s", "-o", tmp + ".svg", "--turdsize", "6",
                    "--alphamax", "1.0", "--opttolerance", "0.2", tmp + ".pbm"], check=True)
    paths = "\n".join(re.findall(r'<path d="[^"]*"\s*/>', open(tmp + ".svg").read()))
    os.remove(tmp + ".pbm"); os.remove(tmp + ".svg")
    vx, vy, vw, vh = vb
    k = vw / im.width
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx} {vy} {vw} {vh}" '
            f'width="{vw}" height="{vh}"><g transform="translate({vx},{vy}) scale({k:.6f})">'
            f'<g transform="translate(0,{im.height}) scale(0.1,-0.1)" fill="{fill}" stroke="none">'
            f'{paths}</g></g></svg>')

def save_svg_png(name, svg, max_side=3000):
    open(os.path.join(OUT, name + ".svg"), "w").write(svg)
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    k = 4000 / max(vb[2], vb[3])
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=int(vb[2]*k), output_height=int(vb[3]*k))
    rw.trim(Image.open(io.BytesIO(png)).convert("RGBA"), max_side=max_side).save(
        os.path.join(OUT, name + ".png"))

# -------------------------------------------------------------------- main
if __name__ == "__main__":
    BLACK = "#000000"
    band = bl.group(*bl.BAND, "band", BLACK)
    cn = bl.group(*bl.CN, "cn", BLACK, bl.SHIFT)
    tag = bl.group(*bl.TAG, "tag", BLACK, bl.SHIFT)
    foot = bl.group(*bl.FOOT, "foot", BLACK)
    FULL, MARK = (0, 0, 1000, 1000), (332, 146, 336, 375)

    sys.argv = [sys.argv[0]]
    bd = load("bd", os.path.join(os.path.dirname(HERE), "design", "build_designs.py"))
    bd.mark_mono = lambda fill: band
    HB = (0, 0, bd.H_W, bd.H_H)
    HOFF = (-bd.MARK_BB[0], -bd.MARK_BB[1])
    horiz = bd.horizontal(False, BLACK)

    gl, el = gray_leg(), engraved_leg()

    # grayscale (photographic)
    composite(gl, rw.doc(band + cn + tag + foot, FULL, True), FULL, ppu=3.0).convert("L").save(
        os.path.join(OUT, "shenghefeng-logo-realwood-gray.png"))
    rw.trim(composite(gl, rw.doc(band + cn + tag, FULL, False), FULL)).save(
        os.path.join(OUT, "shenghefeng-logo-realwood-gray-compact.png"))
    rw.trim(composite(gl, rw.doc(horiz, HB, False), HB, HOFF)).save(
        os.path.join(OUT, "shenghefeng-horizontal-realwood-gray.png"))

    # pure black & white (engraved), vector
    jobs = [("shenghefeng-logo-realwood-bw-compact", band + cn + tag, FULL, (0, 0), True),
            ("shenghefeng-logo-realwood-bw", band + cn + tag + foot, FULL, (0, 0), True),
            ("shenghefeng-mark-realwood-bw", band, MARK, (0, 0), False),
            ("shenghefeng-horizontal-realwood-bw", horiz, HB, HOFF, True)]
    for name, body, vb, off, white_too in jobs:
        art = composite(el, rw.doc(body, vb, True), vb, off)
        svg = vectorize(art, vb, BLACK)
        save_svg_png(name, svg)
        if white_too:
            save_svg_png(name + "-white", svg.replace(f'fill="{BLACK}"', 'fill="#FFFFFF"'))
    print("\n".join(sorted(n for n in os.listdir(OUT) if "gray" in n or "-bw" in n)))
