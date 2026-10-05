# -*- coding: utf-8 -*-
"""
Trademark-grade refinement of the flat black-and-white SHENGHEFENG mark.

What changes compared with logo/realwood/*-bw (the version approved as a base):

  * one stroke weight: every white line - grain and turned grooves - is the
    same width, and that width survives a 20 mm reproduction
  * grain redrawn as clean monoline cathedral arches (constant width via a
    signed distance to the ring isolines), fewer and bolder, no fragments
  * solid black rim around the leg so the silhouette never breaks up
  * the comb of descender stubs between SHENGHEFENG and the leg is closed into
    a solid neck, with one clean groove where the leg meets the frame
  * the thin bar over the lettering gets a wider gap, and the letter counters
    are opened slightly so the word does not clog when small
  * the tagline is reset in a real typeface instead of a trace of 9 px pixels

Outputs to trademark/: a filing version (mark + 圣合丰 only), a graphic-only
filing version, and usage lockups with the tagline.
"""
import importlib.util, io, os, re, subprocess
import numpy as np
from PIL import Image, ImageFont
from scipy import ndimage
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("bl", os.path.join(ROOT, "logo", "build_logo.py"))
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)

S = 8                                    # raster pixels per logo unit while building
LINE = 2.6                               # the one white stroke width, in logo units
RIM = 3.4                                # solid black margin inside the silhouette
RNG = np.random.default_rng(7)
LAT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# ---------------------------------------------------------------- helpers
def raster(svg_body, box, bg=True):
    """Render svg_body (logo units) over box=(x0,y0,x1,y1) at S px/unit -> bool ink mask."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {w} {h}">'
           f'<rect x="{x0-5}" y="{y0-5}" width="{w+10}" height="{h+10}" fill="#fff"/>{svg_body}</svg>')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=int(w*S), output_height=int(h*S))
    return np.asarray(Image.open(io.BytesIO(png)).convert("L")) < 128

def trace(mask, box, name):
    """1-bit mask over box -> SVG <g> of filled paths in logo units."""
    tmp = os.path.join(HERE, "_" + name)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").convert("1").save(tmp + ".pbm")
    subprocess.run(["potrace", "-s", "-o", tmp + ".svg", "--turdsize", "10",
                    "--alphamax", "1.0", "--opttolerance", "0.2", tmp + ".pbm"], check=True)
    paths = "\n".join(re.findall(r'<path d="[^"]*"\s*/>', open(tmp + ".svg").read()))
    os.remove(tmp + ".pbm"); os.remove(tmp + ".svg")
    h = mask.shape[0]
    return (f'<g transform="translate({box[0]},{box[1]}) scale({1/S})">'
            f'<g transform="translate(0,{h}) scale(0.1,-0.1)" fill="FILL" stroke="none">{paths}</g></g>')

def smooth_noise(h, w, cy, cx):
    g = RNG.random((max(2, int(h/cy)+3), max(2, int(w/cx)+3))).astype(np.float32)
    return np.asarray(Image.fromarray(g, "F").resize((w, h), Image.BICUBIC)) - 0.5

def drop_small(mask, min_area_units):
    lab, n = ndimage.label(mask)
    if n == 0:
        return mask
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool); keep[1:] = sizes >= min_area_units * S * S
    return keep[lab]

# ---------------------------------------------------------------- the mark
MARK_BOX = (340, 150, 660, 512)

def build_mark():
    x0, y0, x1, y1 = MARK_BOX
    H, W = int((y1-y0)*S), int((x1-x0)*S)
    xs = x0 + (np.arange(W) + 0.5) / S
    ys = y0 + (np.arange(H) + 0.5) / S
    X, Y = np.meshgrid(xs, ys)
    r = np.array([bl.hw(y) for y in ys])[:, None]
    dx = X - bl.CX
    inside = r - np.abs(dx)                               # distance to silhouette, units
    leg = (inside > 0) & (Y >= bl.TOP) & (Y <= bl.BOT)

    # --- band: original lettering, cleaned
    band = raster(bl.group(*bl.BAND, "band", "#000"), MARK_BOX)
    lab, n = ndimage.label(band)
    # the thin bar over the letters is the component that starts highest
    tops = ndimage.find_objects(lab)
    bar_id = 1 + int(np.argmin([sl[0].start for sl in tops]))
    bar = lab == bar_id
    band &= ~bar
    band |= np.roll(bar, -int(1.6 * S), axis=0)           # lift it: wider gap to the letters
    # open the letter counters a touch so the word does not clog when small
    letters = Y < 219
    thin = ndimage.binary_erosion(band, structure=np.ones((3, 3)), iterations=2)
    band = np.where(letters & ~np.roll(bar, -int(1.6 * S), axis=0), thin, band)
    # close the comb of descender stubs into a solid neck down to the leg
    for i in np.where((ys >= 218) & (ys <= 232))[0]:
        c = np.where(band[i])[0]
        if len(c):
            band[i, c.min():c.max() + 1] = True

    ink = band | leg

    # --- monoline cathedral grain on the tapered body
    # tight curvature -> nested flame arches whose sides run down the leg, like
    # flat-sawn wood; gentle drift and low-frequency wobble keep it organic
    D = 62.0 - 0.18 * (Y - bl.TOP)
    px = 4.0 + 6.0 * np.sin((Y - bl.TOP) / 70.0)
    f = np.sqrt((dx - px) ** 2 + D ** 2) + 3.6 * smooth_noise(H, W, 60 * S, 26 * S)
    gy, gx = np.gradient(f, 1.0 / S)
    grad = np.maximum(np.hypot(gx, gy), 1e-3)
    spacing = 8.0
    d_iso = np.abs(np.mod(f / spacing + 0.5, 1.0) - 0.5) * spacing
    grain = (d_iso / grad < LINE / 2) & leg & (inside > RIM) & (Y > 276) & (Y < 454)
    grain = drop_small(grain, 14)                          # no stubs at the rim

    # --- turned grooves and the frame/leg joint, same stroke width
    grooves = np.zeros_like(leg)
    for yr in (256.0, 272.0, 458.0, 480.0):
        grooves |= (np.abs(Y - yr) < LINE / 2) & (inside > RIM)
    joint = (np.abs(Y - 225.0) < LINE / 2) & ink
    jc = np.where(joint.any(0))[0]
    if len(jc):                                            # keep a black rim at the ends
        joint &= (X > xs[jc.min()] + RIM) & (X < xs[jc.max()] - RIM)

    return ink & ~grain & ~grooves & ~joint

# ---------------------------------------------------------------- tagline
TAG_BOX = (360, 664, 640, 686)
def build_tagline():
    s, target_w = "SOFA WOODEN LEGS", 249.0
    size = 12.6
    font = ImageFont.truetype(LAT_BOLD, 1000)
    w0 = font.getlength(s) * size / 1000
    spacing = (target_w - w0) / (len(s) - 1)
    body = (f'<text x="{372 - 0.0}" y="679.3" font-family="Liberation Sans" font-weight="bold" '
            f'font-size="{size}" letter-spacing="{spacing:.3f}" fill="#000" '
            f'stroke="#000" stroke-width="0.75" stroke-linejoin="round">{s}</text>')
    return raster(body, TAG_BOX)

# ---------------------------------------------------------------- layout
def place(group, fill, x=0.0, y=0.0, k=1.0):
    return f'<g transform="translate({x},{y}) scale({k})">{group.replace("FILL", fill)}</g>'

def doc(body, vb, bg=None):
    rect = (f'<rect x="{vb[0]-1}" y="{vb[1]-1}" width="{vb[2]+2}" height="{vb[3]+2}" fill="{bg}"/>'
            if bg else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" '
            f'width="{vb[2]}" height="{vb[3]}">{rect}{body}</svg>')

def square_vb(x0, y0, x1, y1, margin=0.12):
    w, h = x1 - x0, y1 - y0
    side = max(w, h) * (1 + 2 * margin)
    return (x0 + w/2 - side/2, y0 + h/2 - side/2, side, side)

def tight_vb(x0, y0, x1, y1, margin=0.04):
    m = max(x1 - x0, y1 - y0) * margin
    return (x0 - m, y0 - m, x1 - x0 + 2*m, y1 - y0 + 2*m)

def save(name, svg, png_px=3000, jpg=None, transparent=True):
    open(os.path.join(HERE, name + ".svg"), "w").write(svg)
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    k = png_px / max(vb[2], vb[3])
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=round(vb[2]*k), output_height=round(vb[3]*k))
    Image.open(io.BytesIO(png)).save(os.path.join(HERE, name + ".png"))
    if jpg:
        im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(),
                                                    output_width=jpg, output_height=jpg))).convert("L")
        out = os.path.join(HERE, name + ".jpg")
        for q in (92, 88, 84, 80, 75, 70):
            im.save(out, "JPEG", quality=q, optimize=True)
            if os.path.getsize(out) <= 195_000:
                break
        print(f"  {name}.jpg  {jpg}x{jpg}  {os.path.getsize(out)//1000} KB  q={q}")

if __name__ == "__main__":
    mark = trace(build_mark(), MARK_BOX, "mark")
    tag = trace(build_tagline(), TAG_BOX, "tag")
    cn = bl.group(*bl.CN, "cn", "FILL", bl.SHIFT)

    MK = (355, 160, 645, 505)                 # mark bounds after the bar lift
    CNB = (337, 535, 647, 640)
    B, W = "#000000", "#FFFFFF"

    # 1. filing version: mark + 圣合丰, no descriptive tagline, no country name
    body = place(mark, B) + place(cn, B)
    save("shenghefeng-trademark-filing", doc(body, square_vb(337, 160, 647, 640), "#fff"), jpg=1500)
    # 2. filing, graphic only (for a separate figurative application)
    save("shenghefeng-trademark-filing-graphic", doc(place(mark, B), square_vb(*MK), "#fff"), jpg=1500)
    # 3. usage lockups with the tagline, transparent
    usage = place(mark, "F") + place(cn, "F") + place(tag, "F")
    vb = tight_vb(337, 160, 647, 686)
    save("shenghefeng-logo-final", doc(usage.replace('"F"', f'"{B}"'), vb))
    save("shenghefeng-logo-final-white", doc(usage.replace('"F"', f'"{W}"'), vb))
    # 4. horizontal: mark left, 圣合丰 + tagline right
    kc = 1.30
    cw, ch = (CNB[2]-CNB[0]) * kc, (CNB[3]-CNB[1]) * kc
    tw, th = 249 * kc, 9 * kc
    mh = MK[3] - MK[1]
    gap, tx = 34, (MK[2] - MK[0]) + 72
    top = (mh - (ch + gap + th)) / 2
    hz = (place(mark, "F", -MK[0], -MK[1])
          + place(cn, "F", tx - CNB[0]*kc, top - CNB[1]*kc, kc)
          + place(tag, "F", tx + (cw - tw)/2 - 372*kc, top + ch + gap - 670*kc, kc))
    hvb = tight_vb(0, 0, tx + cw, mh)
    save("shenghefeng-logo-final-horizontal", doc(hz.replace('"F"', f'"{B}"'), hvb))
    save("shenghefeng-logo-final-horizontal-white", doc(hz.replace('"F"', f'"{W}"'), hvb))
    print("\n".join(sorted(f for f in os.listdir(HERE) if not f.endswith(".py"))))
