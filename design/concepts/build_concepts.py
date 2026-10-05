# -*- coding: utf-8 -*-
"""
Five alternative trademark directions for 圣合丰 SHENGHEFENG, all built on the
same turned wooden leg as the main logo, all black-and-white and traced to a
single-colour vector at the end.

  A 丰字木脚   the vertical stroke of 丰 is a turned wooden leg
  B 年轮印     end-grain growth rings around a leg silhouette
  C 沙发剪影   sofa silhouette carrying the name, standing on two wooden legs
  D 圆形徽章   export-style round badge with the name around the ring
  E 中古斜脚   mid-century splayed leg in a rounded square, wordmark beside it
"""
import importlib.util, io, math, os, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
spec = importlib.util.spec_from_file_location("bl", os.path.join(ROOT, "logo", "build_logo.py"))
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)

BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
FONT = ImageFont.truetype(BOLD, 1000)
_uid = [0]
def uid(p):
    _uid[0] += 1; return f"{p}{_uid[0]}"

def pts_path(pts, close=True):
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + (" Z" if close else "")

# --------------------------------------------------------- the turned leg
L_TOP, L_BOT = bl.TOP, bl.BOT          # local profile 228..505, centre bl.CX

def leg(cx, top, h, wscale=1.0, angle=0.0, fill="#000", ink="#fff", line=8.0,
        rim=10.0, halo=0.0, arches=5, profile=None):
    """Turned wooden leg, front view, solid with monoline grain + grooves."""
    hwf = profile or bl.hw
    s = h / (L_BOT - L_TOP); sx = s * wscale
    a = math.radians(angle); ca, sa = math.cos(a), math.sin(a)
    def T(x, y):
        X, Y = (x - bl.CX) * sx, (y - L_TOP) * s
        return cx + X * ca - Y * sa, top + X * sa + Y * ca
    ys = np.arange(L_TOP, L_BOT + 0.01, 0.5)
    outline = [T(bl.CX + hwf(y), y) for y in ys] + [T(bl.CX - hwf(y), y) for y in ys[::-1]]
    inset = [T(bl.CX + max(hwf(y) - rim / sx, 0), y) for y in ys] + \
            [T(bl.CX - max(hwf(y) - rim / sx, 0), y) for y in ys[::-1]]
    cid = uid("clip")
    out = [f'<defs><clipPath id="{cid}"><path d="{pts_path(inset)}"/></clipPath></defs>']
    if halo:
        out.append(f'<path d="{pts_path(outline)}" fill="none" stroke="{ink}" stroke-width="{halo}" stroke-linejoin="round"/>')
    out.append(f'<path d="{pts_path(outline)}" fill="{fill}"/>')
    g = [f'<g clip-path="url(#{cid})" fill="none" stroke="{ink}" stroke-width="{line}" stroke-linecap="round">']
    if profile is None:                                   # turned grooves
        for yr in (256.0, 272.0, 458.0, 480.0):
            g.append(f'<path d="{pts_path([T(bl.CX - 80, yr), T(bl.CX + 80, yr)], False)}"/>')
        y0, y1 = 280.0, 454.0
    else:
        y0, y1 = L_TOP + 10, L_BOT - 10
    span = y1 - y0
    # nested flame arches: the same wide, shallow arch shifted down the leg, so
    # the lines never cross; the sides run off into the rim like real grain
    gap = span / (arches + 0.6)
    for k in range(arches):
        ay = y0 + 0.35 * gap + k * gap
        off = 2.0 * math.sin(k * 1.9)
        p = []
        for t in np.linspace(-1.6, 1.6, 121):
            x = bl.CX + off + t * 30
            y = ay + 70 * abs(t) ** 1.9 + 1.5 * math.sin(t * 2.5 + k)
            p.append(T(x, y))
        g.append(f'<path d="{pts_path(p, False)}"/>')
    g.append("</g>")
    if profile is None:
        # clip the grain to the tapered body only
        body = [T(bl.CX + 90, y0 - 2), T(bl.CX + 90, y1 + 2), T(bl.CX - 90, y1 + 2), T(bl.CX - 90, y0 - 2)]
        bid = uid("body")
        out.append(f'<defs><clipPath id="{bid}"><path d="{pts_path(body)}"/></clipPath></defs>')
        grooves = g[1:5]
        arch_g = g[5:-1]
        out.append(f'<g clip-path="url(#{cid})" fill="none" stroke="{ink}" stroke-width="{line}" stroke-linecap="round">'
                   + "".join(grooves) + f'<g clip-path="url(#{bid})">' + "".join(arch_g) + "</g></g>")
    else:
        out.append("".join(g))
    return "".join(out)

# ----------------------------------------------------------- typography
def text(x, y, s, size, fill="#000", anchor="middle", spacing=0.0, weight="bold", stroke=0.0):
    st = f' stroke="{fill}" stroke-width="{stroke}" stroke-linejoin="round"' if stroke else ""
    return (f'<text x="{x}" y="{y}" font-family="Liberation Sans" font-weight="{weight}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}"{st}>{s}</text>')

def advance(ch, size):
    return FONT.getlength(ch) * size / 1000

def arc_text(s, cx, cy, r, size, top=True, spacing=0.0, fill="#000"):
    """Glyph-by-glyph text on a circle. Top arc reads outward, bottom arc inward."""
    adv = [advance(c, size) + spacing for c in s]
    total = sum(adv) - spacing
    out, cum = [], 0.0
    for c, a in zip(s, adv):
        mid = cum + (a - spacing) / 2
        if top:
            th = -math.pi / 2 - total / 2 / r + mid / r
            rot = math.degrees(th) + 90
        else:
            th = math.pi / 2 + total / 2 / r - mid / r
            rot = math.degrees(th) - 90
        x, y = cx + r * math.cos(th), cy + r * math.sin(th)
        if c != " ":
            out.append(f'<text x="0" y="0" font-family="Liberation Sans" font-weight="bold" font-size="{size}" '
                       f'fill="{fill}" text-anchor="middle" transform="translate({x:.2f},{y:.2f}) rotate({rot:.2f})">{c}</text>')
        cum += a
    return "".join(out)

CN_BB = (337, 535, 647, 640)                 # 圣合丰 calligraphy in logo space
def calligraphy(x, y, width, fill="#000"):
    k = width / (CN_BB[2] - CN_BB[0])
    return (f'<g transform="translate({x - CN_BB[0]*k:.2f},{y - CN_BB[1]*k:.2f}) scale({k:.5f})">'
            + bl.group(*bl.CN, "cn", fill, bl.SHIFT) + "</g>")

# --------------------------------------------------------------- concepts
def concept_A():
    W, H = 1000, 1000
    bars = [(300, 400), (425, 320), (590, 560)]          # 丰: y-centre, width
    b = "".join(f'<rect x="{500 - w/2}" y="{y - 27}" width="{w}" height="54" rx="27" fill="#000"/>' for y, w in bars)
    body = b + leg(500, 140, 650, wscale=0.52, line=9, rim=11, arches=5)
    body += text(500, 905, "SHENGHEFENG", 58, spacing=14)
    return W, H, body

def concept_B():
    W, H = 1000, 1000
    cx, cy, R = 500, 430, 300
    cid = uid("disc")
    rings = [f'<defs><clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{R - 16}"/></clipPath></defs>',
             f'<g clip-path="url(#{cid})" fill="none" stroke="#000" stroke-width="7">']
    px, py = cx + 18, cy + 22                            # pith slightly off centre, like a real log
    for k in range(1, 16):
        rk = 21 * k
        pts = []
        for th in np.linspace(0, 2 * math.pi, 241):
            r = rk * (1 + 0.045 * math.sin(3 * th + 0.7 * k) + 0.025 * math.sin(7 * th + k))
            pts.append((px + r * math.cos(th), py + r * math.sin(th)))
        rings.append(f'<path d="{pts_path(pts)}"/>')
    rings.append("</g>")
    body = "".join(rings) + f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#000" stroke-width="18"/>'
    body += leg(cx, 165, 500, wscale=0.95, line=9, rim=11, halo=34)
    body += calligraphy(500 - 170, 770, 340)
    body += text(500, 950, "SHENGHEFENG", 40, spacing=12)
    return W, H, body

def concept_C():
    W, H = 1000, 1000
    sofa = ('<rect x="210" y="240" width="580" height="210" rx="52" fill="#000"/>'
            '<rect x="165" y="360" width="140" height="240" rx="48" fill="#000"/>'
            '<rect x="695" y="360" width="140" height="240" rx="48" fill="#000"/>'
            '<rect x="270" y="430" width="460" height="170" rx="24" fill="#000"/>'
            '<rect x="300" y="458" width="400" height="9" rx="4.5" fill="#fff"/>')   # cushion seam
    name = text(500, 375, "SHENGHEFENG", 54, fill="#fff", spacing=7)
    legs = leg(300, 608, 230, wscale=0.95, line=7, rim=8) + leg(700, 608, 230, wscale=0.95, line=7, rim=8)
    body = sofa + name + legs + calligraphy(500 - 150, 878, 300)
    return W, H, body

def concept_D():
    W, H = 1000, 1000
    cx, cy = 500, 500
    body = (f'<circle cx="{cx}" cy="{cy}" r="410" fill="none" stroke="#000" stroke-width="20"/>'
            f'<circle cx="{cx}" cy="{cy}" r="300" fill="none" stroke="#000" stroke-width="8"/>')
    body += arc_text("SHENGHEFENG", cx, cy, 326, 60, top=True, spacing=6)
    body += arc_text("SOFA WOODEN LEGS", cx, cy, 384, 44, top=False, spacing=5)
    for sx in (-1, 1):
        body += f'<circle cx="{cx + sx*355}" cy="{cy}" r="11" fill="#000"/>'
    body += '<rect x="370" y="236" width="260" height="22" rx="4" fill="#000"/>'   # sofa frame rail
    body += leg(cx, 268, 470, wscale=0.95, line=9, rim=11)
    return W, H, body

def mid_century(y):
    """Straight mid-century cone: wide at the plate, slim at the floor."""
    t = (y - L_TOP) / (L_BOT - L_TOP)
    hw = 46 - 27 * t
    if y > L_BOT - 6:                                     # eased flat foot
        hw *= math.sqrt(max(0.0, 1 - ((y - (L_BOT - 6)) / 6) ** 2)) * 0.25 + 0.75
    return hw

def concept_E():
    W, H = 1500, 760
    body = ('<rect x="80" y="130" width="500" height="500" rx="70" fill="#000"/>'
            '<rect x="130" y="230" width="400" height="34" rx="6" fill="#fff"/>')   # sofa base rail
    body += leg(300, 270, 310, wscale=1.0, angle=10, fill="#fff", ink="#000", line=9, rim=10,
                arches=4, profile=mid_century)
    body += text(640, 360, "SHENGHEFENG", 86, anchor="start", spacing=4)
    body += calligraphy(642, 420, 300)
    body += text(642, 590, "SOFA WOODEN LEGS", 34, anchor="start", spacing=10)
    return W, H, body

# --------------------------------------------------------------- export
def render(W, H, body, scale=3):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
           f'<rect width="{W}" height="{H}" fill="#fff"/>{body}</svg>')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=W*scale, output_height=H*scale)
    return np.asarray(Image.open(io.BytesIO(png)).convert("L")) < 128

def trace(mask, W, H, name, fill="#000000"):
    tmp = os.path.join(HERE, "_" + name)
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), "L").convert("1").save(tmp + ".pbm")
    subprocess.run(["potrace", "-s", "-o", tmp + ".svg", "--turdsize", "8", "--alphamax", "1.0",
                    "--opttolerance", "0.2", tmp + ".pbm"], check=True)
    paths = "\n".join(re.findall(r'<path d="[^"]*"\s*/>', open(tmp + ".svg").read()))
    os.remove(tmp + ".pbm"); os.remove(tmp + ".svg")
    ys, xs = np.where(mask); k = W / mask.shape[1]
    m = 0.04 * max(W, H)
    x0, y0 = xs.min()*k - m, ys.min()*k - m
    w, h = (xs.max() - xs.min())*k + 2*m, (ys.max() - ys.min())*k + 2*m
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
            f'width="{w:.0f}" height="{h:.0f}"><g transform="scale({k:.6f})">'
            f'<g transform="translate(0,{mask.shape[0]}) scale(0.1,-0.1)" fill="{fill}" stroke="none">'
            f'{paths}</g></g></svg>')

CONCEPTS = [
    ("A", "丰字木脚", concept_A,
     "「丰」字的竖笔就是一根车削木脚，名字和产品合二为一。独特性最强，最好注册。"),
    ("B", "年轮印", concept_B,
     "原木截面的年轮包住木脚，「实木」一眼可见。圆形适合烙在木脚底部。"),
    ("C", "沙发剪影", concept_C,
     "名字写在沙发靠背上，下面两只木脚。品类最直观，外行一看就懂。"),
    ("D", "圆形徽章", concept_D,
     "经典外贸徽章，英文名和品类绕圈。适合吊牌、封口贴、展会。"),
    ("E", "中古斜脚", concept_E,
     "北欧中古外撇斜脚配方形底标，现代简洁。适合欧美客户和电商头像。"),
]

if __name__ == "__main__":
    tiles = []
    for key, name, fn, why in CONCEPTS:
        W, H, body = fn()
        svg = trace(render(W, H, body), W, H, key)
        base = os.path.join(HERE, f"concept-{key}")
        open(base + ".svg", "w").write(svg)
        vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
        k = 2400 / max(vb[2], vb[3])
        png = cairosvg.svg2png(bytestring=svg.encode(), output_width=round(vb[2]*k), output_height=round(vb[3]*k))
        Image.open(io.BytesIO(png)).save(base + ".png")
        tiles.append((key, name, why, Image.open(io.BytesIO(png)).convert("RGBA")))
        print("built", key, name)

    # design board
    TW, TH, CAP = 600, 600, 120
    cols = 3
    B = Image.new("RGB", (cols*TW + (cols+1)*40, 2*(TH+CAP) + 3*40 + 110), (244, 241, 236))
    d = ImageDraw.Draw(B)
    fT, fH, fB = ImageFont.truetype(CJK, 40), ImageFont.truetype(CJK, 30), ImageFont.truetype(CJK, 21)
    d.text((40, 34), "圣合丰 商标造型方向", font=fT, fill=(30, 30, 30))
    for i, (key, name, why, im) in enumerate(tiles):
        r, c = divmod(i, cols)
        if r == 1:
            c += 0.5                                       # centre the second row
        x = int(40 + c*(TW + 40)); y = 110 + r*(TH + CAP + 40)
        tile = Image.new("RGBA", (TW, TH), (255, 255, 255, 255))
        kk = min((TW - 80)/im.width, (TH - 80)/im.height)
        sm = im.resize((int(im.width*kk), int(im.height*kk)), Image.LANCZOS)
        tile.alpha_composite(sm, ((TW - sm.width)//2, (TH - sm.height)//2))
        B.paste(tile.convert("RGB"), (x, y))
        d.text((x, y + TH + 14), f"{key}  {name}", font=fH, fill=(30, 30, 30))
        lines, cur = [], ""
        for ch in why:
            if d.textlength(cur + ch, font=fB) > TW: lines.append(cur); cur = ch
            else: cur += ch
        lines.append(cur)
        for j, ln in enumerate(lines[:2]):
            d.text((x, y + TH + 56 + j*28), ln, font=fB, fill=(90, 90, 90))
    B.save(os.path.join(HERE, "concepts-board.png"))
    print("board saved")
