# -*- coding: utf-8 -*-
"""
Brand applications for 圣合丰 SHENGHEFENG, built on logo/build_logo.py:

  * horizontal logo lockup (colour / black / white)
  * business card 90x54mm, front + back (print PDF with 3mm bleed, PNG preview)
  * carton shipping-mark label 100x150mm, single colour black for flexo printing
  * a design board that shows everything together

Units inside the print layouts are 0.1 mm (so 900 = 90 mm).
"""
import importlib.util, os, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(os.path.dirname(HERE), "logo")
spec = importlib.util.spec_from_file_location("bl", os.path.join(LOGO, "build_logo.py"))
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)

BROWN, WOOD, WOOD_HI, CREAM, INK = "#3F1A08", "#9C6733", "#AE7A44", "#F5EFE6", "#111111"
CJK = "WenQuanYi Zen Hei"
LAT = "Liberation Sans"
FONT_CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

# --------------------------------------------------------------- helpers
def place(inner, bbox, x, y, k):
    """Put artwork whose bbox (in its own space) is `bbox` at (x, y), scaled by k."""
    x0, y0 = bbox[0], bbox[1]
    return f'<g transform="translate({x - k*x0:.2f},{y - k*y0:.2f}) scale({k:.5f})">{inner}</g>'

def flatten(svg, w, h, fill, scale=4):
    """Render black-on-white artwork and re-trace it as one fill colour, so grain
    becomes a real hole. Returns a <g> in the artwork's own w x h space."""
    tmp = os.path.join(HERE, "_f")
    cairosvg.svg2png(bytestring=svg.encode(), write_to=tmp + ".png",
                     output_width=int(w*scale), output_height=int(h*scale))
    g = np.array(Image.open(tmp + ".png").convert("L"))
    Image.fromarray(np.where(g < 150, 0, 255).astype(np.uint8), "L").convert("1").save(tmp + ".pbm")
    subprocess.run(["potrace", "-s", "-o", tmp + ".svg", "--turdsize", "3",
                    "--alphamax", "1.0", "--opttolerance", "0.2", tmp + ".pbm"], check=True)
    paths = "\n".join(re.findall(r'<path d="[^"]*"\s*/>', open(tmp + ".svg").read()))
    for ext in (".png", ".pbm", ".svg"):
        os.remove(tmp + ext)
    return (f'<g transform="scale({1.0/scale})"><g transform="translate(0,{int(h*scale)}) '
            f'scale(0.1,-0.1)" fill="{fill}" stroke="none">{paths}</g></g>')

def svg_doc(body, w, h, defs="", mm=None):
    size = f' width="{mm[0]}mm" height="{mm[1]}mm"' if mm else f' width="{w}" height="{h}"'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"{size}>'
            f'<defs>{defs}</defs>{body}</svg>')

def write(name, svg, png_w=None, pdf=False):
    open(os.path.join(HERE, name + ".svg"), "w", encoding="utf-8").write(svg)
    if png_w:
        cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(HERE, name + ".png"),
                         output_width=png_w)
    if pdf:
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(HERE, name + ".pdf"))

def text(x, y, s, size, fill=INK, family=CJK, weight="normal", anchor="start", spacing=0):
    if any(ord(c) > 127 for c in s):   # cairo does no per-glyph fallback: CJK needs a CJK font
        family = CJK
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}, {CJK}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}>{s}</text>')

# ----------------------------------------------------------- logo pieces
MARK_BB = (355, 165, 645, 505)          # band + leg, in logo space
CN_BB = (337, 535, 647, 640)            # 圣合丰 after the logo's downward shift
TAG_BB = (372, 670, 621, 679)           # SOFA WOODEN LEGS
VERT_BB = (337, 165, 647, 679)          # vertical lockup without the footer line

LEG = bl.outline()
EDGE = f'<path d="{LEG}" fill="none" stroke="#44220E" stroke-width="2"/>'

def mark_colour():
    g = bl.grain_svg("#4A2610", 0.30, 1.8, bl.GRAINS_FULL, bl.RINGS_FULL,
                     ((392, 13, 306), (372, 8, 302)))
    return (bl.group(*bl.BAND, "band", BROWN)
            + f'<path d="{LEG}" fill="url(#wood)"/>{g}{EDGE}')

def mark_mono_source():
    g = bl.grain_svg("#FFFFFF", 1.0, 3.2, bl.GRAINS_FLAT, bl.RINGS_FLAT, ())
    return bl.group(*bl.BAND, "band", "#000") + f'<path d="{LEG}" fill="#000"/>{g}'

def cn(fill):  return bl.group(*bl.CN, "cn", fill, bl.SHIFT)
def tag(fill): return bl.group(*bl.TAG, "tag", fill, bl.SHIFT)

WHITE_1000 = '<rect x="-10" y="-10" width="1100" height="1100" fill="#fff"/>'
_mono_mark = flatten(svg_doc(WHITE_1000 + mark_mono_source(), 1000, 1000), 1000, 1000, "#000")
def mark_mono(fill):
    return _mono_mark.replace('fill="#000"', f'fill="{fill}"')

def vertical_mono(fill):
    return mark_mono(fill) + cn(fill) + tag(fill)

# ---------------------------------------------------- horizontal lockup
# mark on the left, 圣合丰 + SOFA WOODEN LEGS on the right
H_W, H_H = 770, 340
def horizontal(colour=True, fill=INK):
    mk = mark_colour() if colour else mark_mono(fill)
    kc = 1.30
    cw, ch = (CN_BB[2]-CN_BB[0])*kc, (CN_BB[3]-CN_BB[1])*kc
    tw, th = (TAG_BB[2]-TAG_BB[0])*kc, (TAG_BB[3]-TAG_BB[1])*kc
    gap, tx = 34, 290 + 72
    top = (H_H - (ch + gap + th)) / 2
    txt_fill = INK if colour else fill
    return (place(mk, MARK_BB, 0, 0, 1.0)
            + place(cn(txt_fill), CN_BB, tx, top, kc)
            + place(tag(txt_fill), TAG_BB, tx + (cw - tw)/2, top + ch + gap, kc))

# ------------------------------------------------------- business card
BLEED = 30                        # 3 mm
CW, CH = 900 + 2*BLEED, 540 + 2*BLEED
def card_front():
    import math
    grain = []
    for i, (y, ph, a) in enumerate(((70, 0.3, 7), (150, 1.9, 9), (235, 3.4, 6), (330, 0.8, 10),
                                    (410, 2.6, 7), (495, 4.4, 8), (560, 1.2, 6))):
        pts = " L ".join(f"{x} {y + a*math.sin(x/150 + ph) + 3*math.sin(x/47 + ph*2):.1f}"
                         for x in range(-10, CW + 11, 10))
        grain.append(f'<path d="M {pts}" fill="none" stroke="#6B3517" stroke-opacity="0.45" '
                     f'stroke-width="1.6"/>')
    k = 340 / (VERT_BB[3] - VERT_BB[1])
    w = (VERT_BB[2] - VERT_BB[0]) * k
    return (f'<rect width="{CW}" height="{CH}" fill="{BROWN}"/>' + "".join(grain)
            + place(vertical_mono(CREAM), VERT_BB, CW/2 - w/2, CH/2 - 170, k))

def card_back(with_text=True):
    k = 0.80
    mh = (MARK_BB[3]-MARK_BB[1]) * k
    x0 = BLEED + 62
    body = [f'<rect width="{CW}" height="{CH}" fill="#F7F2EA"/>',
            place(mark_colour(), MARK_BB, x0, CH/2 - mh/2, k),
            f'<rect x="{x0 + 232 + 50}" y="{CH/2 - 150}" width="3" height="300" fill="{WOOD}"/>']
    if with_text:
        tx = x0 + 232 + 50 + 38
        body += [
            text(tx, 212, "姓名 NAME", 44, BROWN, CJK, "bold"),
            text(tx, 252, "职位 TITLE", 22, WOOD, CJK, spacing=2),
        ]
        rows = (("T", "+86 138 0000 0000"), ("E", "you@example.com"),
                ("W", "www.example.com"), ("A", "公司地址 ADDRESS"))
        for i, (lab, val) in enumerate(rows):
            y = 322 + i*40
            body += [text(tx, y, lab, 22, WOOD_HI, LAT, "bold"),
                     text(tx + 34, y, val, 23, "#2A2A2A", LAT)]
    return "".join(body)

def card(name, body):
    defs = bl.WOOD_GRADIENT
    full = svg_doc(body, CW, CH, defs, mm=(96, 60))
    write(name + "-print-bleed", full, pdf=True)
    os.remove(os.path.join(HERE, name + "-print-bleed.svg"))
    trim = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{BLEED} {BLEED} 900 540" '
            f'width="90mm" height="54mm"><defs>{defs}</defs>{body}</svg>')
    write(name, trim, png_w=2126)          # 90 mm at 600 dpi

# ------------------------------------------------------ carton label
def up_arrows(ox, oy):
    out = []
    for cx in (ox + 58, ox + 122):
        out.append(f'<rect x="{cx-9}" y="{oy+62}" width="18" height="92" fill="#000"/>')
        out.append(f'<path d="M {cx-34} {oy+72} L {cx} {oy+14} L {cx+34} {oy+72} Z" fill="#000"/>')
    out.append(f'<rect x="{ox+22}" y="{oy+162}" width="136" height="14" fill="#000"/>')
    return "".join(out)

def umbrella(ox, oy):
    cx, base = ox + 90, oy + 112
    canopy = (f'M {cx-78} {base} A 78 78 0 0 1 {cx+78} {base} '
              f'A 26 17 0 0 0 {cx+26} {base} A 26 17 0 0 0 {cx-26} {base} '
              f'A 26 17 0 0 0 {cx-78} {base} Z')
    drops = "".join(f'<path d="M {x} {oy+2} L {x-7} {oy+24}" stroke="#000" stroke-width="8" '
                    f'stroke-linecap="round"/>' for x in (cx-52, cx+4, cx+60))
    return (f'<path d="{canopy}" fill="#000"/>'
            f'<path d="M {cx} {base-4} L {cx} {oy+160} A 15 15 0 0 1 {cx-30} {oy+160}" '
            f'fill="none" stroke="#000" stroke-width="10" stroke-linecap="round"/>' + drops)

def carton_label():
    W, H = 1000, 1500
    b = [f'<rect width="{W}" height="{H}" fill="#fff"/>',
         f'<rect x="22" y="22" width="{W-44}" height="{H-44}" fill="none" stroke="#000" stroke-width="6"/>']
    k = 780 / H_W
    b.append(place(horizontal(colour=False, fill="#000"), (0, 0), (W - H_W*k)/2, 70, k))
    b.append(f'<rect x="22" y="440" width="{W-44}" height="5" fill="#000"/>')
    rows = [("品名", "PRODUCT", "沙发木脚 SOFA WOODEN LEGS", ""),
            ("型号", "MODEL NO.", "", ""), ("木种", "WOOD", "", ""),
            ("尺寸", "SIZE", "", "mm"), ("颜色", "FINISH", "", ""),
            ("数量", "QUANTITY", "", "PCS"), ("毛重", "G.W.", "", "KG"),
            ("净重", "N.W.", "", "KG"), ("箱号", "CTN NO.", "/", "")]
    y0, rh = 462, 78
    for i, (zh, en, val, unit) in enumerate(rows):
        y = y0 + i*rh
        b.append(text(60, y + 40, zh, 32, "#000", CJK, "bold"))
        b.append(text(60, y + 66, en, 17, "#000", LAT, spacing=1))
        b.append(f'<rect x="300" y="{y + 60}" width="640" height="2.5" fill="#000"/>')
        if val == "/":
            b.append(text(620, y + 52, "/", 34, "#000", LAT, anchor="middle"))
        elif val:
            b.append(text(312, y + 50, val, 30, "#000", CJK, "bold"))
        if unit:
            b.append(text(940, y + 50, unit, 22, "#000", LAT, "bold", anchor="end"))
    b.append(f'<rect x="22" y="1180" width="{W-44}" height="5" fill="#000"/>')
    b.append(up_arrows(70, 1215))
    b.append(umbrella(290, 1215))
    b.append(text(160, 1440, "向上 THIS SIDE UP", 20, "#000", CJK, anchor="middle"))
    b.append(text(380, 1440, "怕湿 KEEP DRY", 20, "#000", CJK, anchor="middle"))
    b.append(text(935, 1300, "MADE IN CHINA", 46, "#000", LAT, "bold", anchor="end"))
    b.append(text(935, 1365, "中国制造", 40, "#000", CJK, "bold", anchor="end", spacing=6))
    b.append(text(935, 1425, "CHINA / WORLDWIDE SUPPLY", 18, "#000", LAT, "bold",
                  anchor="end", spacing=2))
    svg = svg_doc("".join(b), W, H, mm=(100, 150))
    write("carton-label-100x150", svg, png_w=2362, pdf=True)   # 600 dpi

# ------------------------------------------------------------ board
def shadowed(board, im, xy, r=18, off=(0, 14), alpha=70):
    sh = Image.new("RGBA", (im.width + 4*r, im.height + 4*r), (0, 0, 0, 0))
    a = im.split()[3] if im.mode == "RGBA" else Image.new("L", im.size, 255)
    sh.paste(Image.new("RGBA", im.size, (40, 25, 15, alpha)), (2*r, 2*r), a)
    sh = sh.filter(ImageFilter.GaussianBlur(r))
    board.alpha_composite(sh, (xy[0] - 2*r + off[0], xy[1] - 2*r + off[1]))
    board.alpha_composite(im.convert("RGBA"), xy)

def design_board():
    load = lambda n: Image.open(os.path.join(HERE, n)).convert("RGBA")
    f = lambda s: ImageFont.truetype(FONT_CJK, s)
    front = load("business-card-front.png").resize((840, 504), Image.LANCZOS)
    back = load("business-card-back.png").resize((840, 504), Image.LANCZOS)
    label = load("carton-label-100x150.png"); label = label.resize((700, 1050), Image.LANCZOS)
    B = Image.new("RGBA", (1960, 1850), (236, 232, 226, 255)); d = ImageDraw.Draw(B)
    d.text((100, 60), "圣合丰 SHENGHEFENG  品牌应用", font=f(44), fill=(63, 26, 8))
    d.text((100, 124), "名片 · 纸箱唛头 · 横版组合", font=f(24), fill=(120, 95, 70))
    shadowed(B, front, (100, 210)); d.text((100, 734), "名片正面  90×54mm", font=f(22), fill=(90, 80, 70))
    shadowed(B, back, (100, 800));  d.text((100, 1324), "名片背面", font=f(22), fill=(90, 80, 70))
    shadowed(B, label, (1100, 210)); d.text((1100, 1284), "纸箱唛头标签  100×150mm  单色黑", font=f(22), fill=(90, 80, 70))
    tiles = [("logo-horizontal-colour.png", (247, 242, 234)), ("logo-horizontal-black.png", (255, 255, 255)),
             ("logo-horizontal-white.png", (63, 26, 8))]
    tw, th, y = 540, 300, 1440
    for i, (n, bg) in enumerate(tiles):
        x = 100 + i*(tw + 40)
        tile = Image.new("RGBA", (tw, th), bg + (255,))
        lg = load(n); k = min((tw - 90)/lg.width, (th - 90)/lg.height)
        lg = lg.resize((int(lg.width*k), int(lg.height*k)), Image.LANCZOS)
        tile.alpha_composite(lg, ((tw - lg.width)//2, (th - lg.height)//2))
        shadowed(B, tile, (x, y), r=12, off=(0, 8), alpha=45)
    d.text((100, 1770), "横版组合  全彩 · 纯黑 · 反白", font=f(22), fill=(90, 80, 70))
    B.convert("RGB").save(os.path.join(HERE, "design-board.png"))

# ------------------------------------------------------------- main
if __name__ == "__main__":
    wood = bl.WOOD_GRADIENT
    write("logo-horizontal-colour", svg_doc(horizontal(True), H_W, H_H, wood), png_w=2400)
    src = svg_doc(f'<rect width="{H_W}" height="{H_H}" fill="#fff"/>'
                  + horizontal(False, "#000"), H_W, H_H)
    flat = flatten(src, H_W, H_H, "#000")
    write("logo-horizontal-black", svg_doc(flat, H_W, H_H), png_w=2400)
    write("logo-horizontal-white", svg_doc(flat.replace('fill="#000"', 'fill="#FFFFFF"'), H_W, H_H),
          png_w=2400)
    card("business-card-front", card_front())
    card("business-card-back", card_back(True))
    card("business-card-back-blank", card_back(False))
    carton_label()
    design_board()
    print("\n".join(sorted(n for n in os.listdir(HERE) if not n.endswith(".py"))))
