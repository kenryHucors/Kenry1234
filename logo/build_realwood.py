# -*- coding: utf-8 -*-
"""
Realistic wood-grain version of the SHENGHEFENG logo.

The wooden leg is rendered as a physically plausible turned leg rather than
drawn grain lines:

  * a straight wood blank with growth rings around a pith that sits off the
    blank and runs slightly out of parallel - turning the taper through those
    rings produces the cathedral / flame figure you see on real turned legs
  * earlywood / latewood ring profile, fbm turbulence, fine pore streaks and
    slow colour variation (walnut tones)
  * the texture is sampled in 3D on the surface of revolution, so grain
    compresses toward the silhouette like on a real cylinder
  * lighting from the actual profile normal: beads, chamfers and the foot
    catch light and shadow, plus a soft satin-lacquer highlight

Everything else in the logo stays vector. Output goes to logo/realwood/.
Procedural - no stock photography, so there is no image licence to worry about.
"""
import base64, importlib.util, io, os, sys
import numpy as np
from PIL import Image
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "realwood")
os.makedirs(OUT, exist_ok=True)
spec = importlib.util.spec_from_file_location("bl", os.path.join(HERE, "build_logo.py"))
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)

S = 6                                   # pixels per logo unit (logo 1000 -> 6000 px)
RNG = np.random.default_rng(20260925)
EARLY = np.array([168, 110, 64], float)     # earlywood, medium walnut
LATE = np.array([98, 56, 30], float)        # latewood, dark band
SHEEN = np.array([255, 236, 205], float)

# ----------------------------------------------------------------- noise
def noise(h, w, cell_y, cell_x):
    gh, gw = max(2, int(h / cell_y) + 3), max(2, int(w / cell_x) + 3)
    g = Image.fromarray(RNG.random((gh, gw)).astype(np.float32), "F")
    return np.asarray(g.resize((w, h), Image.BICUBIC), dtype=np.float32) - 0.5

def fbm(h, w, cell_y, cell_x, octaves=4):
    out, amp, tot = np.zeros((h, w), np.float32), 1.0, 0.0
    for o in range(octaves):
        out += amp * noise(h, w, cell_y / 2**o, cell_x / 2**o)
        tot += amp; amp *= 0.5
    return out / tot

def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- the leg
FIELDS = {}                             # ring phase, lighting etc. for the B&W builds

def render_leg():
    """Returns (RGBA image, x0, y0) with x0/y0 in logo units."""
    x0u, x1u = bl.CX - 56, bl.CX + 56
    y0u, y1u = bl.TOP, bl.BOT + 1
    W, H = int((x1u - x0u) * S), int((y1u - y0u) * S)
    xs = x0u + (np.arange(W) + 0.5) / S
    ys = y0u + (np.arange(H) + 0.5) / S
    X, Y = np.meshgrid(xs, ys)

    r = np.array([bl.hw(y) for y in ys])                  # radius per row
    dr = np.gradient(r, ys)                               # profile slope
    R = r[:, None].repeat(W, 1)
    DR = dr[:, None].repeat(W, 1)
    dx = X - bl.CX
    n = np.clip(dx / np.maximum(R, 1e-3), -1, 1)          # sin(theta)
    cz = np.sqrt(1 - n * n)                               # cos(theta)
    Z = R * cz                                            # depth of the surface point

    # --- growth rings: pith behind the blank, drifting so rings break the surface
    # turbulence is long and gentle: real grain flows, it does not jitter
    turb = fbm(H, W, 160 * S, 26 * S, 3) + 0.25 * fbm(H, W, 40 * S, 6 * S, 2)
    px = 6.0 + 4.0 * np.sin((Y - bl.TOP) / 150.0)
    pz = -170.0 + 0.11 * (Y - bl.TOP)                     # slight run-out -> a few arches
    dist = np.sqrt((dx - px) ** 2 + (Z - pz) ** 2) + 2.4 * turb
    spacing = 3.6 + 0.8 * fbm(H, W, 200 * S, 60 * S, 2)  # rings vary in width
    t = np.mod(dist / spacing, 1.0)
    late = sstep(0.30, 0.88, t) * (1 - sstep(0.93, 1.0, t))   # soft rise, abrupt end
    late = late ** 1.2

    # --- pores and fine streaks along the grain (vertical)
    pores = fbm(H, W, 26 * S, 0.55 * S, 2)
    pores = np.clip(-pores * 2.6, 0, 1) ** 1.3
    streak = fbm(H, W, 60 * S, 3.5 * S, 3)
    tone = 1.0 + 0.16 * fbm(H, W, 140 * S, 40 * S, 3) + 0.07 * streak

    base = EARLY[None, None] * (1 - late[..., None] * 0.62) + LATE[None, None] * (late[..., None] * 0.62)
    base *= tone[..., None]
    base *= (1 - 0.28 * pores[..., None])

    # --- lighting from the real surface-of-revolution normal
    N = np.stack([n, -DR, cz], -1)
    N /= np.linalg.norm(N, axis=-1, keepdims=True)
    L = np.array([-0.42, -0.40, 0.81]); L /= np.linalg.norm(L)
    V = np.array([0.0, 0.0, 1.0])
    Hh = (L + V) / np.linalg.norm(L + V)
    diff = np.clip((N * L).sum(-1), 0, 1)
    spec_ = np.clip((N * Hh).sum(-1), 0, 1) ** 38
    shade = 0.30 + 0.86 * diff
    # crisp turned grooves where the profile creases
    groove = np.zeros_like(Y)
    for yr in bl.RINGS_FULL:
        groove += np.exp(-((Y - yr) / 0.75) ** 2)
    shade *= 1 - 0.38 * np.clip(groove, 0, 1)
    col = base * shade[..., None] + SHEEN[None, None] * (0.30 * spec_[..., None])
    # rim darkening keeps the silhouette crisp at logo sizes
    inside = R * S - np.abs(dx) * S
    rim = np.clip(1 - inside / (1.6 * S), 0, 1) ** 1.5
    col *= (1 - 0.45 * rim)[..., None]
    col = np.clip(col, 0, 255)

    # --- anti-aliased mask
    a = np.clip(inside + 0.5, 0, 1)
    a *= np.clip((bl.BOT - Y) * S + 0.5, 0, 1)
    a *= np.clip((Y - bl.TOP) * S + 0.5, 0, 1)
    FIELDS.update(t=t, spacing=spacing, shade=shade, groove=groove, inside=inside, a=a, Y=Y, cz=cz)
    rgba = np.dstack([col, a * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA"), x0u, y0u

LEG_IMG, LEG_X0, LEG_Y0 = render_leg()

def leg_data_uri(scale_to=None):
    im = LEG_IMG
    if scale_to:
        im = im.resize((int(im.width * scale_to), int(im.height * scale_to)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# ------------------------------------------------------------ compositing
def composite(svg_wo_leg, vb, px_per_unit, offset=(0.0, 0.0)):
    """Render the vector part, then lay the leg over it.
    vb = (x, y, w, h) viewBox; offset maps logo units into this document."""
    vx, vy, vw, vh = vb
    W, H = int(vw * px_per_unit), int(vh * px_per_unit)
    png = cairosvg.svg2png(bytestring=svg_wo_leg.encode(), output_width=W, output_height=H)
    base = Image.open(io.BytesIO(png)).convert("RGBA")
    k = px_per_unit / S
    leg = LEG_IMG if abs(k - 1) < 1e-6 else LEG_IMG.resize(
        (round(LEG_IMG.width * k), round(LEG_IMG.height * k)), Image.LANCZOS)
    x = round((LEG_X0 + offset[0] - vx) * px_per_unit)
    y = round((LEG_Y0 + offset[1] - vy) * px_per_unit)
    base.alpha_composite(leg, (x, y))
    return base

def leg_svg_image(offset=(0.0, 0.0)):
    w, h = LEG_IMG.width / S, LEG_IMG.height / S
    uri = leg_data_uri(0.5)
    return (f'<image x="{LEG_X0 + offset[0]:.3f}" y="{LEG_Y0 + offset[1]:.3f}" '
            f'width="{w:.3f}" height="{h:.3f}" xlink:href="{uri}" href="{uri}" '
            f'preserveAspectRatio="none"/>')

def doc(body, vb, bg):
    rect = (f'<rect x="{vb[0]-10}" y="{vb[1]-10}" width="{vb[2]+20}" height="{vb[3]+20}" '
            f'fill="#FFFFFF"/>' if bg else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" '
            f'width="{vb[2]}" height="{vb[3]}">{rect}{body}</svg>')

def trim(im, pad=0.03, max_side=3000):
    bb = im.split()[3].getbbox()
    p = int(max(im.size) * pad)
    im = im.crop((max(0, bb[0]-p), max(0, bb[1]-p), min(im.width, bb[2]+p), min(im.height, bb[3]+p)))
    k = max_side / max(im.size)
    return im.resize((round(im.width*k), round(im.height*k)), Image.LANCZOS)

# ------------------------------------------------------------------- main
if __name__ == "__main__":
    band = bl.group(*bl.BAND, "band", bl.DARK)
    cn = bl.group(*bl.CN, "cn", "#111111", bl.SHIFT)
    tag = bl.group(*bl.TAG, "tag", "#111111", bl.SHIFT)
    foot = bl.group(*bl.FOOT, "foot", "#111111")
    FULL = (0, 0, 1000, 1000)
    MARK = (332, 146, 336, 375)

    # full lockup, white and transparent
    full_vec = band + cn + tag + foot
    im = composite(doc(full_vec, FULL, True), FULL, 3.0)
    im.convert("RGB").save(os.path.join(OUT, "shenghefeng-logo-realwood.png"))
    im = composite(doc(full_vec, FULL, False), FULL, S)
    trim(im).save(os.path.join(OUT, "shenghefeng-logo-realwood-transparent.png"))
    # compact (no CHINA / WORLDWIDE SUPPLY line) - the one to use in Canva
    im = composite(doc(band + cn + tag, FULL, False), FULL, S)
    trim(im).save(os.path.join(OUT, "shenghefeng-logo-realwood-compact.png"))
    # mark only
    im = composite(doc(band, MARK, False), MARK, S)
    trim(im, max_side=2400).save(os.path.join(OUT, "shenghefeng-mark-realwood.png"))
    # SVGs: everything vector except the leg, which is an embedded image (no clipPath)
    open(os.path.join(OUT, "shenghefeng-logo-realwood.svg"), "w").write(
        doc(band + leg_svg_image() + cn + tag + foot, FULL, True))
    open(os.path.join(OUT, "shenghefeng-mark-realwood.svg"), "w").write(
        doc(band + leg_svg_image(), MARK, False))

    # horizontal lockup, reusing the layout from design/build_designs.py
    sys.argv = [sys.argv[0]]
    dspec = importlib.util.spec_from_file_location(
        "bd", os.path.join(os.path.dirname(HERE), "design", "build_designs.py"))
    bd = importlib.util.module_from_spec(dspec); dspec.loader.exec_module(bd)
    bd.mark_colour = lambda: band
    HB = (0, 0, bd.H_W, bd.H_H)
    off = (-bd.MARK_BB[0], -bd.MARK_BB[1])
    im = composite(doc(bd.horizontal(True), HB, False), HB, S, off)
    trim(im).save(os.path.join(OUT, "shenghefeng-horizontal-realwood.png"))
    print("\n".join(sorted(os.listdir(OUT))))
