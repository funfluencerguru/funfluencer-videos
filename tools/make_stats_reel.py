"""FunFluencer cinematic STATS PILLAR reel (9:16, 1080x1920, 30 fps) from one JSON spec.
Usage:  python3 tools/make_stats_reel.py spec.json            -> renders video + cover + audio
        python3 tools/make_stats_reel.py spec.json --preview 1.6 10.5 24   -> PNG frames only
See tools/README.md (section "Stats pillar reel") for the spec format."""
import subprocess, sys, math, os, random
from PIL import Image, ImageDraw, ImageFilter
from PIL import ImageFont
import json

W, H, FPS = 1080, 1920, 30
SCR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCR)
SPEC = json.load(open(sys.argv[1]))
FONT_DIRS = [os.path.join(REPO, "assets/fonts"), "/usr/share/fonts/opentype/inter"]
_fc = {}
def font(w, s):
    k = (w, int(s))
    if k not in _fc:
        for fd in FONT_DIRS:
            p = os.path.join(fd, f"Inter-{w}.otf")
            if os.path.exists(p): _fc[k] = ImageFont.truetype(p, int(s)); break
        else: _fc[k] = ImageFont.truetype(os.path.join(FONT_DIRS[0], "Inter-ExtraBold.otf"), int(s))
    return _fc[k]

# items low -> high: small, BIG, sub, value, icon, [3 pedestal lines], vertical name, final value label
P = [(it.get("small", ""), it["big"], it.get("sub", ""), float(it["value"]), it.get("icon", "glyph:" + it["big"][:3]), "coin",
      (it.get("lines", []) + ["", "", ""])[:3], it.get("vname", it["big"])[:10].upper(), it.get("value_text", ""))
     for it in SPEC["items"]]
COUNT_FMT = SPEC.get("count_fmt", "{:,.0f}")
N = len(P)
MAT = [["bronze", "silver", "gold"][min(2, i * 3 // max(1, N - 1))] for i in range(N - 1)] + ["diamond"]
MCOL = {  # dark, base, highlight, text-on-metal, glow
    "bronze": ((92, 48, 18), (184, 112, 52), (255, 206, 150), (40, 18, 4), (230, 140, 70)),
    "silver": ((96, 102, 114), (186, 190, 200), (255, 255, 255), (26, 30, 40), (210, 220, 240)),
    "gold": ((128, 86, 8), (226, 176, 40), (255, 243, 170), (52, 32, 0), (255, 205, 70)),
    "diamond": ((120, 170, 210), (196, 232, 255), (255, 255, 255), (12, 34, 66), (170, 230, 255)),
}

PITCH, PWW, HMAX, PED = 330, 240, 680, 260
FLOOR = 120
VMAX = max(p[3] for p in P)
def hof(v): return FLOOR + (HMAX - FLOOR) * v / VMAX
def wx(i): return i * PITCH
T_INTRO, STEP, PAN, RISE0, GROW, EXTRA, ZOOM, HOLD = 2.6, 2.0, 0.6, 0.4, 1.0, 1.0, 2.2, 3.6
T_STEPS_END = T_INTRO + N * STEP + EXTRA
T_ZOOM_END = T_STEPS_END + ZOOM
TOTAL = T_ZOOM_END + HOLD
def t_start(i): return T_INTRO + i * STEP
def t_land(i): return t_start(i) + RISE0 + GROW
SPAN = wx(N - 1) + PWW
ZX_O, ZY_O, BASE_O = 1000 / SPAN, 0.60, 1500

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def ease_io(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def ease_io5(t): t = max(0.0, min(1.0, t)); return t*t*t*(t*(6*t-15)+10)
def back(t):
    t = max(0, min(1, t)); c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k

def target(i):
    cx = wx(i) + PWW / 2 - 0.13 * W
    base = min(1700.0, max(1300.0, 640 + PED + hof(P[i][3])))
    return (cx, 1.0, base)

def camera(t):
    if t < T_INTRO:
        k = ease_io5((t - 0.6) / (T_INTRO - 0.6))
        b = target(0)
        cx = lerp(-700, b[0] - 140, k)
        z = lerp(1.15, 1.0, k)
        return cx, z, z, lerp(2300, b[2], k), 0, 0, 0.0, 1 - k
    if t < T_STEPS_END:
        i = min(N - 1, int((t - T_INTRO) // STEP))
        lt = t - t_start(i)
        prev = target(i - 1) if i > 0 else (target(0)[0] - 140, 1.0, target(0)[2])
        cur = target(i)
        k = ease_io5(lt / PAN)
        cx = lerp(prev[0], cur[0], k) + 26 * max(0, lt - PAN)
        base = lerp(prev[2], cur[2], k)
        dip = 0.05 * math.sin(math.pi * min(1, lt / PAN)) if i > 0 else 0
        z = 1.0 - dip + 0.012 * math.sin(t * 1.3)
        sh = t - t_land(i); dx = dy = 0
        if 0 < sh < 0.35:
            a = (12 if i < N - 2 else 20) * math.exp(-sh * 11)
            dx, dy = a * math.sin(sh * 90), a * math.cos(sh * 70)
        return cx, z, z, base, dx, dy, 0.0, 0.0
    last = target(N - 1)
    lt = t - T_STEPS_END
    cx_last = last[0] + 26 * (STEP + EXTRA - PAN)
    k = ease_io5(lt / ZOOM)
    cx = lerp(cx_last, SPAN / 2, k)
    zx = math.exp(lerp(0.0, math.log(ZX_O), k))
    zy = lerp(1.0, ZY_O, k)
    base = lerp(last[2], BASE_O, k)
    if t > T_ZOOM_END:
        h = (t - T_ZOOM_END) / HOLD
        zx *= 1 + 0.015 * h; zy *= 1 + 0.015 * h
    return cx, zx, zy, base, 0, 0, k, 0.0

# ---------- assets ----------
def make_bg(path):
    """Drawn backdrop (0 credits): two-colour gradient, sunburst, two big faded words, scattered motifs."""
    import numpy as np
    b = SPEC.get("bg", {})
    BW, BH = 3600, 2300; rr = random.Random(b.get("seed", 5))
    cl, cr = b.get("left_color", [128, 78, 36]), b.get("right_color", [26, 84, 104])
    xs = np.linspace(0, 1, BW)[None, :, None]; ys = np.linspace(0, 1, BH)[:, None, None]
    a = (np.array(cl) * (1 - xs) + np.array(cr) * xs) * (1.05 - 0.45 * ys)
    im = Image.fromarray(np.clip(a, 0, 255).astype("uint8")).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    cx, cy = BW / 2, BH * 0.42
    for k in range(48):
        a0 = k * 2 * math.pi / 48; a1 = a0 + math.pi / 48
        d.polygon([(cx, cy), (cx + 4000 * math.cos(a0), cy + 4000 * math.sin(a0)), (cx + 4000 * math.cos(a1), cy + 4000 * math.sin(a1))], fill=(255, 230, 180, 22))
    lw, rw = b.get("left_word", ""), b.get("right_word", "")
    for word, x, col in ((lw, 620, (255, 210, 140, 70)), (rw, BW - 620, (140, 230, 255, 70))):
        if word:
            fs = 520
            while fs > 120 and font("ExtraBold", fs).getlength(word) > 1150: fs -= 20
            d.text((x, 560), word, font=font("ExtraBold", fs), fill=col, anchor="mm")
    motif = b.get("motif", "₹")
    for _ in range(90):
        x, y = rr.uniform(0, BW), rr.uniform(900, BH); k = x / BW
        col = tuple(int(c) for c in (255 * (1 - k) + 150 * k, 214 * (1 - k) + 230 * k, 140 * (1 - k) + 255 * k))
        sz = rr.uniform(40, 120); al = rr.randint(35, 80)
        if rr.random() < 0.5:
            d.text((x, y), motif, font=font("ExtraBold", int(sz * 1.2)), fill=col + (al,), anchor="mm")
        else:
            d.ellipse([x - sz / 2, y - sz / 2, x + sz / 2, y + sz / 2], outline=col + (al + 10,), width=6)
    for y in (1150, 1550, 1950): d.rectangle([0, y, BW, y + 22], fill=(255, 220, 160, 26))
    im.alpha_composite(ov); im = im.convert("RGB").filter(ImageFilter.GaussianBlur(5))
    Image.blend(im, Image.new("RGB", im.size), 0.12).save(path)
WORK = SPEC.get("workdir", "/tmp/statsreel"); os.makedirs(WORK, exist_ok=True)
BG_PATH = os.path.join(WORK, "bg.png")
make_bg(BG_PATH)
bg_src = Image.open(BG_PATH).convert("RGB")
BGH = 2300
bg_big = bg_src.resize((int(bg_src.width * BGH / bg_src.height), BGH), Image.LANCZOS)
BGW = bg_big.width

shade = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(shade)
for y in range(H):
    v = 60
    if y < 300: v = int(60 + 110 * (1 - y / 300) ** 1.6)
    if y > 1450: v = int(60 + 150 * ((y - 1450) / 470) ** 1.2)
    sd.line([(0, y), (W, y)], fill=min(255, v))
vig = Image.new("L", (W, H), 0)
ImageDraw.Draw(vig).ellipse([-500, -300, W + 500, H + 300], fill=255)
shade = Image.composite(shade, Image.new("L", (W, H), 190), vig.filter(ImageFilter.GaussianBlur(160)))
SHADE_RGB = Image.new("RGB", (W, H), (10, 5, 2))

def metal_tex(name, w=PWW, h=600):
    dk, bs, hi, _, _ = MCOL[name]
    im = Image.new("RGB", (w, h)); px = im.load()
    rnd = random.Random(3)
    for x in range(w):
        k = x / (w - 1)
        s = 0.5 + 0.5 * math.cos((k - 0.32) * math.pi * 1.15)
        spec = math.exp(-((k - 0.26) / 0.05) ** 2)
        for y in range(h):
            v = s * (0.92 + 0.08 * (1 - y / h))
            c = [dk[j] + (bs[j] - dk[j]) * min(1, v * 1.25) for j in range(3)]
            if v > 0.8: c = [c[j] + (hi[j] - c[j]) * (v - 0.8) * 2.5 for j in range(3)]
            c = [c[j] + (hi[j] - c[j]) * spec * 0.85 for j in range(3)]
            px[x, y] = tuple(int(min(255, max(0, q))) for q in c)
    if name == "diamond":  # faceted overlay
        d = ImageDraw.Draw(im, "RGBA")
        for yy in range(-60, h + 60, 60):
            for xx in range(0, w + 60, 60):
                off = 30 if (yy // 60) % 2 else 0
                pts = [(xx + off, yy), (xx + off + 30, yy + 60), (xx + off - 30, yy + 60)]
                d.polygon(pts, fill=(255, 255, 255, rnd.randint(10, 70)))
                d.line(pts + [pts[0]], fill=(255, 255, 255, 90), width=1)
    return im
TEX = {m: metal_tex(m) for m in MCOL}

def icon(kind, S=120):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], 22, fill=(26, 16, 6, 235), outline=(255, 210, 90), width=4)
    g = (255, 214, 100); u = S / 120; L = lambda *p: [(x * u, y * u) for x, y in p]
    w = int(6 * u)
    if kind == "ship":
        d.polygon(L((22, 70), (98, 70), (86, 92), (34, 92)), fill=g)
        d.rectangle([40 * u, 48 * u, 80 * u, 70 * u], fill=g)
        for x in (46, 58, 70): d.rectangle([x * u, 54 * u, (x + 6) * u, 62 * u], fill=(26, 16, 6))
        d.rectangle([56 * u, 30 * u, 64 * u, 48 * u], fill=g)
        d.arc([20 * u, 92 * u, 50 * u, 104 * u], 180, 360, fill=g, width=w // 2)
        d.arc([70 * u, 92 * u, 100 * u, 104 * u], 180, 360, fill=g, width=w // 2)
    elif kind == "tower":
        d.line(L((60, 34), (40, 98)), fill=g, width=w); d.line(L((60, 34), (80, 98)), fill=g, width=w)
        d.line(L((48, 72), (72, 72)), fill=g, width=w)
        d.ellipse([54 * u, 28 * u, 66 * u, 40 * u], fill=g)
        for r in (16, 28):
            d.arc([(60 - r) * u, (34 - r) * u, (60 + r) * u, (34 + r) * u], 200, 250, fill=g, width=w // 2 + 1)
            d.arc([(60 - r) * u, (34 - r) * u, (60 + r) * u, (34 + r) * u], 290, 340, fill=g, width=w // 2 + 1)
    elif kind == "girder":
        d.rectangle([24 * u, 34 * u, 96 * u, 46 * u], fill=g); d.rectangle([24 * u, 82 * u, 96 * u, 94 * u], fill=g)
        d.rectangle([54 * u, 46 * u, 66 * u, 82 * u], fill=g)
    elif kind == "vial":
        d.rounded_rectangle([46 * u, 40 * u, 74 * u, 98 * u], 8 * u, fill=g)
        d.rectangle([42 * u, 26 * u, 78 * u, 40 * u], fill=g)
        d.rectangle([50 * u, 66 * u, 70 * u, 90 * u], fill=(26, 16, 6))
        d.rectangle([50 * u, 78 * u, 70 * u, 90 * u], fill=(255, 150, 90))
    elif kind == "laptop":
        d.rounded_rectangle([30 * u, 34 * u, 90 * u, 78 * u], 5 * u, outline=g, width=w)
        d.polygon(L((20, 84), (100, 84), (92, 94), (28, 94)), fill=g)
        d.text((60 * u, 56 * u), "</>", font=font("ExtraBold", int(22 * u)), fill=g, anchor="mm")
    elif kind == "capsule":
        im2 = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d2 = ImageDraw.Draw(im2)
        d2.rounded_rectangle([30 * u, 48 * u, 90 * u, 74 * u], 13 * u, fill=g)
        d2.rectangle([60 * u, 48 * u, 90 * u, 74 * u], fill=(255, 150, 90))
        d2.rounded_rectangle([30 * u, 48 * u, 90 * u, 74 * u], 13 * u, outline=g, width=3)
        im.alpha_composite(im2.rotate(35, resample=Image.BICUBIC))
    elif kind == "factory":
        d.polygon(L((22, 96), (22, 58), (44, 70), (44, 58), (66, 70), (66, 58), (88, 70), (98, 70), (98, 96)), fill=g)
        d.rectangle([80 * u, 30 * u, 90 * u, 64 * u], fill=g)
        d.ellipse([84 * u, 18 * u, 100 * u, 30 * u], fill=(255, 214, 100, 150))
    elif kind == "truck":
        d.rectangle([20 * u, 44 * u, 72 * u, 82 * u], fill=g)
        d.polygon(L((72, 56), (90, 56), (100, 70), (100, 82), (72, 82)), fill=g)
        d.rectangle([78 * u, 60 * u, 90 * u, 68 * u], fill=(26, 16, 6))
        for x in (36, 86): d.ellipse([(x - 9) * u, 76 * u, (x + 9) * u, 94 * u], fill=(26, 16, 6), outline=g, width=w // 2 + 1)
    elif kind == "play":
        d.ellipse([18 * u, 18 * u, 102 * u, 102 * u], outline=g, width=w)
        d.polygon(L((48, 38), (48, 82), (86, 60)), fill=g)
    elif kind == "coin":
        d.ellipse([18 * u, 18 * u, 102 * u, 102 * u], fill=g)
        d.ellipse([28 * u, 28 * u, 92 * u, 92 * u], outline=(150, 100, 20), width=w // 2 + 1)
        d.text((60 * u, 62 * u), "₹", font=font("ExtraBold", int(50 * u)), fill=(90, 56, 8), anchor="mm")
    elif kind == "star":
        pts = [(60 + (40 if k % 2 == 0 else 17) * math.cos(-math.pi / 2 + k * math.pi / 5), 62 + (40 if k % 2 == 0 else 17) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
        d.polygon(L(*pts), fill=g)
    elif kind == "drop":
        d.polygon(L((60, 24), (40, 62), (80, 62)), fill=g); d.ellipse([38 * u, 46 * u, 82 * u, 92 * u], fill=g)
        d.ellipse([48 * u, 62 * u, 58 * u, 76 * u], fill=(255, 245, 200))
    return im
PILLAR_ICON = SPEC.get("pillar_icon", "coin")  # coin | star | none
ICONS = [icon(PILLAR_ICON) for p in P]

def item_art(slug, Z):
    """Drawn icon library. 'glyph:TEXT' draws short text (e.g. glyph:4G, glyph:₹). Add new icons here as new elif branches."""
    im = Image.new("RGBA", (Z, Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im); u = Z / 100
    def B(*p): return [v * u for v in p]
    if slug.startswith("glyph:"):
        g = slug[6:]; fs = int(46 * u)
        while fs > 10 and font("ExtraBold", fs).getlength(g) > 70 * u: fs -= 2
        d.text((50 * u, 52 * u), g, font=font("ExtraBold", fs), fill=(60, 34, 10), anchor="mm")
    elif slug == "flag":  # generic tricolour-free plain flag on pole
        d.rectangle(B(26, 18, 30, 86), fill=(90, 70, 50)); d.polygon([(30 * u, 20 * u), (80 * u, 30 * u), (30 * u, 50 * u)], fill=(230, 80, 60))
    elif slug == "bat":
        d.polygon([(46 * u, 18 * u), (54 * u, 18 * u), (60 * u, 72 * u), (40 * u, 72 * u)], fill=(225, 190, 130), outline=(120, 80, 30))
        d.rectangle(B(47, 72, 53, 88), fill=(60, 60, 60)); d.ellipse(B(66, 64, 82, 80), fill=(210, 40, 40))
    elif slug == "trophy":
        d.pieslice(B(28, 14, 72, 64), 0, 180, fill=(240, 190, 50)); d.rectangle(B(28, 22, 72, 40), fill=(240, 190, 50))
        d.rectangle(B(46, 62, 54, 76), fill=(200, 150, 30)); d.rectangle(B(34, 76, 66, 86), fill=(120, 80, 30))
    elif slug == "phone":
        d.rounded_rectangle(B(32, 14, 68, 86), 6 * u, fill=(40, 40, 50)); d.rectangle(B(36, 22, 64, 74), fill=(120, 200, 255)); d.ellipse(B(47, 77, 53, 83), fill=(200, 200, 200))
    elif slug == "people":
        for x, s_ in ((32, 1.0), (50, 1.2), (68, 1.0)):
            d.ellipse(B(x - 7 * s_, 30 - 6 * s_, x + 7 * s_, 44 - 6 * s_ + 2), fill=(90, 60, 40)); d.pieslice(B(x - 13 * s_, 44, x + 13 * s_, 84), 180, 360, fill=(60, 120, 200))
    elif slug == "building":
        d.rectangle(B(30, 16, 70, 86), fill=(120, 140, 170))
        for yy in range(22, 80, 10):
            for xx in (36, 47, 58): d.rectangle(B(xx, yy, xx + 6, yy + 5), fill=(255, 230, 140))
    elif slug == "train":
        d.rounded_rectangle(B(20, 30, 80, 72), 8 * u, fill=(60, 100, 180)); d.rectangle(B(28, 38, 72, 52), fill=(200, 230, 255))
        for x in (34, 66): d.ellipse(B(x - 7, 66, x + 7, 80), fill=(40, 40, 40))
    elif slug == "plane":
        d.polygon([(14 * u, 50 * u), (86 * u, 44 * u), (90 * u, 50 * u), (86 * u, 56 * u)], fill=(220, 225, 235))
        d.polygon([(48 * u, 50 * u), (36 * u, 20 * u), (44 * u, 20 * u), (62 * u, 50 * u)], fill=(180, 190, 210)); d.polygon([(48 * u, 50 * u), (36 * u, 80 * u), (44 * u, 80 * u), (62 * u, 50 * u)], fill=(180, 190, 210))
    elif slug == "film":
        d.rectangle(B(18, 30, 82, 70), fill=(40, 40, 40))
        for x in range(22, 80, 10): d.rectangle(B(x, 33, x + 5, 38), fill=(240, 240, 240)); d.rectangle(B(x, 62, x + 5, 67), fill=(240, 240, 240))
        d.polygon([(44 * u, 42 * u), (44 * u, 58 * u), (58 * u, 50 * u)], fill=(255, 214, 100))
    elif slug == "food":
        d.pieslice(B(18, 30, 82, 86), 0, 180, fill=(200, 120, 60)); d.ellipse(B(18, 46, 82, 62), fill=(250, 220, 150)); d.line(B(70, 20, 50, 54), fill=(150, 150, 150), width=int(3 * u))
    elif slug == "house":
        d.polygon([(18 * u, 48 * u), (50 * u, 20 * u), (82 * u, 48 * u)], fill=(200, 70, 50)); d.rectangle(B(26, 48, 74, 84), fill=(240, 210, 160)); d.rectangle(B(44, 62, 56, 84), fill=(120, 80, 40))
    elif slug == "bolt":
        d.polygon([(56 * u, 12 * u), (28 * u, 54 * u), (48 * u, 54 * u), (40 * u, 88 * u), (72 * u, 42 * u), (52 * u, 42 * u)], fill=(255, 200, 40), outline=(150, 100, 0))
    elif slug == "car":
        d.rounded_rectangle(B(14, 50, 86, 70), 6 * u, fill=(230, 60, 50))
        d.polygon([(28 * u, 50 * u), (36 * u, 34 * u), (62 * u, 34 * u), (74 * u, 50 * u)], fill=(230, 60, 50))
        d.polygon([(33 * u, 49 * u), (39 * u, 38 * u), (48 * u, 38 * u), (48 * u, 49 * u)], fill=(170, 220, 255))
        d.polygon([(51 * u, 49 * u), (51 * u, 38 * u), (60 * u, 38 * u), (68 * u, 49 * u)], fill=(170, 220, 255))
        for x in (30, 70): d.ellipse(B(x - 9, 61, x + 9, 79), fill=(30, 30, 30)); d.ellipse(B(x - 4, 66, x + 4, 74), fill=(200, 200, 200))
        d.rectangle(B(80, 54, 86, 58), fill=(255, 230, 120))
    elif slug == "post":
        d.rectangle(B(14, 26, 86, 74), fill=(250, 214, 90)); d.rectangle(B(14, 26, 86, 74), outline=(150, 100, 20), width=int(2 * u))
        d.rectangle(B(66, 32, 80, 48), fill=(220, 70, 60)); d.line(B(50, 30, 50, 70), fill=(150, 100, 20), width=int(1.5 * u))
        for y in (54, 61, 68): d.line(B(55, y, 80, y), fill=(150, 100, 20), width=int(1.5 * u))
        for y in (38, 46, 54): d.line(B(20, y, 44, y), fill=(120, 90, 60), width=int(1.5 * u))
    elif slug == "dollar":
        d.rounded_rectangle(B(10, 30, 90, 70), 4 * u, fill=(110, 170, 100)); d.rounded_rectangle(B(15, 35, 85, 65), 3 * u, outline=(40, 90, 40), width=int(2 * u))
        d.ellipse(B(37, 37, 63, 63), fill=(70, 130, 70)); d.text((50 * u, 51 * u), "$", font=font("ExtraBold", int(26 * u)), fill=(235, 255, 225), anchor="mm")
    elif slug == "petrol":
        d.rounded_rectangle(B(26, 22, 62, 82), 4 * u, fill=(230, 60, 50)); d.rectangle(B(31, 28, 57, 46), fill=(230, 245, 255))
        d.text((44 * u, 37 * u), "₹", font=font("ExtraBold", int(14 * u)), fill=(30, 30, 30), anchor="mm")
        d.rectangle(B(22, 80, 66, 86), fill=(80, 80, 80))
        d.line(B(62, 36, 74, 42, 74, 66, 80, 70), fill=(40, 40, 40), width=int(4 * u), joint="curve")
        d.polygon([(76 * u, 62 * u), (84 * u, 62 * u), (82 * u, 74 * u), (78 * u, 74 * u)], fill=(40, 40, 40))
    elif slug == "income":
        d.rounded_rectangle(B(16, 32, 84, 76), 8 * u, fill=(140, 82, 40)); d.rounded_rectangle(B(56, 44, 90, 64), 5 * u, fill=(110, 60, 28))
        d.ellipse(B(64, 50, 72, 58), fill=(255, 214, 100))
        for k in range(3): d.rectangle(B(24 + k * 4, 22 - k * 2, 60 + k * 4, 34 - k * 2), fill=(120, 180, 110), outline=(60, 110, 60))
        d.text((36 * u, 56 * u), "₹", font=font("ExtraBold", int(24 * u)), fill=(255, 220, 140), anchor="mm")
    elif slug in ("silver", "gold"):
        c1, c2, c3 = ((200, 205, 215), (245, 248, 255), (130, 135, 150)) if slug == "silver" else ((230, 175, 40), (255, 236, 150), (150, 100, 10))
        for (x, y) in ((22, 58), (50, 58), (36, 36)):
            d.polygon([(x * u, (y + 18) * u), ((x + 6) * u, y * u), ((x + 26) * u, y * u), ((x + 32) * u, (y + 18) * u)], fill=c1, outline=c3)
            d.polygon([((x + 8) * u, (y + 3) * u), ((x + 24) * u, (y + 3) * u), ((x + 26) * u, (y + 8) * u), ((x + 6) * u, (y + 8) * u)], fill=c2)
    elif slug == "sensex":
        d.rectangle(B(14, 20, 86, 80), fill=(14, 30, 40)); 
        for y in (35, 50, 65): d.line(B(16, y, 84, y), fill=(40, 70, 80), width=1)
        pts = [(18, 74), (30, 68), (40, 70), (52, 56), (62, 58), (74, 38), (84, 26)]
        d.line([(x * u, y * u) for x, y in pts], fill=(80, 230, 120), width=int(4 * u), joint="curve")
        d.polygon([(84 * u, 22 * u), (88 * u, 34 * u), (76 * u, 30 * u)], fill=(80, 230, 120))
    return im

def badge_base(i, Z=380):
    slug = P[i][4]
    ring = MCOL[MAT[i]][4]
    out = Image.new("RGBA", (Z, Z), (0, 0, 0, 0))
    ImageDraw.Draw(out).ellipse([0, 0, Z - 1, Z - 1], fill=ring)
    r = int(Z * 0.07)
    inner = Image.new("RGB", (Z, Z)); idd = ImageDraw.Draw(inner)
    for y in range(Z):
        k = y / Z; idd.line([(0, y), (Z, y)], fill=(int(255 - 40 * k), int(244 - 50 * k), int(222 - 60 * k)))
    m = Image.new("L", (Z, Z), 0); ImageDraw.Draw(m).ellipse([r, r, Z - r, Z - r], fill=255)
    out.paste(inner, (0, 0), m)
    art = item_art(slug, int(Z * 0.78)); out.alpha_composite(art, (int(Z * 0.11), int(Z * 0.11)))
    ImageDraw.Draw(out).ellipse([r, r, Z - r, Z - r], outline=(255, 255, 255, 210), width=6)
    return out
BADGES = [badge_base(i) for i in range(N)]

def vlabel(text, col, size=28):
    f = font("ExtraBold", size); tw = int(f.getlength(text)) + 10
    im = Image.new("RGBA", (tw, size + 14), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((tw / 2, (size + 14) / 2), text, font=f, fill=col, anchor="mm")
    return im.rotate(90, expand=True)
VNAMES = [vlabel(p[7], (255, 220, 140, 255)) for i, p in enumerate(P)]
LOGO = Image.open(os.path.join(REPO, "assets/logo.png")).convert("RGBA").resize((104, 104), Image.LANCZOS)
rnd = random.Random(11)
PARTS = [(rnd.random(), rnd.random(), rnd.uniform(2, 6), rnd.uniform(0.3, 1.0), rnd.uniform(0, 6.28)) for _ in range(80)]

def fit(s_, size, maxw, w="ExtraBold"):
    size = int(size)
    while size > 12 and font(w, size).getlength(s_) > maxw: size -= 1
    return font(w, size)
def wa(c, a): return tuple(c[:3]) + (int(max(0, min(255, a))),)
def text(d, xy, s, f, fill, a=255, stroke=3, sc=(8, 4, 0)):
    d.text(xy, s, font=f, fill=wa(fill, a), anchor="mm", stroke_width=stroke, stroke_fill=wa(sc, a * 0.85))

def frame(t):
    cx, zx, zy, base, sdx, sdy, ok, intro = camera(t)
    kb = lerp(1.0, 0.9, ok) * (1 + 0.12 * intro)
    cw, ch = W / kb, H / kb
    bx = max(0, min(BGW - cw, BGW / 2 - cw / 2 + (cx - SPAN / 2) * 0.2 * (1 - intro)))
    by_track = (BGH - ch) * 0.6 + (base - 1500) * 0.2
    by = max(0, min(BGH - ch, lerp(by_track, 0, intro)))
    im = bg_big.crop((int(bx), int(by), int(bx + cw), int(by + ch))).resize((W, H), Image.BILINEAR)
    im.paste(SHADE_RGB, (0, 0), shade)

    def sx(w): return (w - cx) * zx + W / 2 + sdx
    def sy(h): return base - h * zy + sdy
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(over)
    glow = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(glow); glow_col = None
    gy = sy(0)
    if gy < H + 40:
        d.line([(0, gy), (W, gy)], fill=(255, 220, 150, 190), width=max(2, int(4 * zy)))
    final_hold = t > T_STEPS_END
    active = min(N - 1, int((t - T_INTRO) // STEP)) if t >= T_INTRO else -1
    names_a = 1 - ease_io(ok * 2.2)
    vnames_a = ease_io((ok - 0.55) / 0.45)
    sparkle = []

    for i, (small, big, grp, worth, slug, ic, brands, vname, vlab) in enumerate(P):
        if t < t_start(i): break
        mat = MAT[i]; dk, bs, hi, tc, gc = MCOL[mat]
        lt = t - (t_start(i) + RISE0)
        g = ease(lt / GROW) if lt > 0 else 0
        pg = ease((t - t_start(i) - 0.05) / 0.4)
        h = hof(worth) * g
        x0, x1 = sx(wx(i)), sx(wx(i) + PWW)
        if x1 < -260 or x0 > W + 260: continue
        pw = x1 - x0; xc = (x0 + x1) / 2
        # carved pedestal (same for everyone) carrying rank + brands
        pt = sy(PED * pg); pedh = gy - pt
        if pedh > 2:
            ped = Image.new("RGB", (max(2, int(pw)), max(2, int(pedh))), (46, 22, 10)); pdd = ImageDraw.Draw(ped)
            for yy in range(ped.height):
                k = yy / max(1, ped.height); pdd.line([(0, yy), (ped.width, yy)], fill=(int(70 - 30 * k), int(34 - 16 * k), int(14 - 6 * k)))
            pdd.rectangle([0, 0, ped.width, max(2, int(5 * zy))], fill=(232, 180, 70))
            pdd.rectangle([int(8 * zx), int(12 * zy), ped.width - int(8 * zx), ped.height - int(10 * zy)], outline=(190, 140, 50), width=max(1, int(2 * zx)))
            im.paste(ped, (int(x0), int(pt)))
            rs = max(20, int(44 * zx))
            text(d, (xc, pt + rs * 0.95), f"#{N - i}", font("ExtraBold", rs), (255, 214, 100), 255 * pg, 0)
            if names_a > 0.01 and zx > 0.6 and pedh - rs * 1.9 - 16 * zy > 30:
                ba = 255 * names_a * ease((t - t_start(i) - 0.3) / 0.5)
                n_ = len(brands); avail = pedh - rs * 1.9 - 16 * zy
                lh = min(50 * zy, avail / max(1, n_)); yb = pt + rs * 1.9
                for bi, bname in enumerate(brands):
                    fs = int(min((30 if bi < 2 else 22) * zx, lh * 0.66))
                    while fs > 12 and font("ExtraBold", fs).getlength(bname) > pw - 26 * zx: fs -= 1
                    text(d, (xc, yb + lh / 2), bname, font("ExtraBold", fs), [(255, 214, 150), (150, 230, 255), (255, 214, 100)][bi], ba, 0)
                    yb += lh
            if vnames_a > 0.01:
                vn = VNAMES[i]
                sc_ = min(1.0, (pedh - rs * 2.0) / vn.height, (pw - 6) / vn.width)
                if sc_ > 0.3:
                    vv = vn.resize((max(1, int(vn.width * sc_)), max(1, int(vn.height * sc_))), Image.BILINEAR)
                    vv.putalpha(vv.getchannel("A").point(lambda a: int(a * vnames_a)))
                    over.alpha_composite(vv, (int(xc - vv.width / 2), int(pt + rs * 1.7)))
        top = sy(PED * pg + h)
        mgy = pt  # metal stands on the pedestal
        if (i == active and not final_hold) or (final_hold and i == N - 1):
            pad = 30 * max(zx, .42)
            gd.rounded_rectangle([x0 - pad, top - 430 * max(zx, .42), x1 + pad, gy], int(40 * max(zx, .42)), fill=150 if i < N - 1 else 200)
            glow_col = gc
        d.ellipse([x0 - pw * 0.15, gy - 10 * zy, x1 + pw * 0.15, gy + 22 * zy], fill=(0, 0, 0, 120))
        ph = mgy - top
        if ph > 2:
            inset = pw * 0.06
            mx0, mx1 = x0 + inset, x1 - inset; mw = mx1 - mx0
            tex = TEX[mat].resize((max(2, int(mw)), max(2, int(ph))), Image.BILINEAR)
            m = Image.new("L", tex.size, 0)
            ImageDraw.Draw(m).rounded_rectangle([0, 0, tex.width - 1, tex.height + 30], int(min(18 * zx, tex.width / 3)) + 4, fill=255)
            im.paste(tex, (int(mx0), int(top)), m)
            d.line([(mx0 + 2, top + 3), (mx1 - 2, top + 3)], fill=wa(hi, 220), width=max(1, int(3 * zx)))
            isz0 = max(40, 108 * zx); isz = int(min(isz0, mw - 8, ph - 12))
            if isz > 24 and PILLAR_ICON != "none":
                over.alpha_composite(ICONS[i].resize((isz, isz), Image.BILINEAR), (int(xc - isz / 2), int(top + min(14 * max(zx, .42), (ph - isz) / 2))))
            if mat == "diamond":
                sparkle.append((mx0, mx1, top, mgy))
        # value + photo + names above the pillar
        lab = zx > 0.6
        nsz = max(26, int(64 * zx))
        y = top - nsz * (1.05 if lab else 0.75)
        val = worth * g
        vs = vlab if (g > 0.995 and vlab) else COUNT_FMT.format(val)
        va = 255 * ease(g / 0.15)
        if va > 1: text(d, (xc, y), vs, font("ExtraBold", nsz), (255, 255, 255), va, 4 if lab else 3)
        if lab:
            text(d, (xc, top - 22), SPEC.get("value_caption", ""), font("Bold", 20), (255, 215, 120), 230 * names_a * ease(g / 0.15), 2)
        y -= nsz * 0.7
        b = back((t - t_start(i) - 0.15) / 0.6)
        pk = (t - t_land(i)) / 0.45
        if final_hold and i == N - 1: pk = max(pk if pk < 1 else -1, (t - T_ZOOM_END + 0.2) / 0.45)
        if 0 < pk < 1: b *= 1 + 0.12 * math.sin(pk * math.pi)
        dia0 = max(64, int(200 * zx)); dia = dia0 * b
        if dia > 4:
            over.alpha_composite(BADGES[i].resize((int(dia), int(dia)), Image.BILINEAR), (int(xc - dia / 2), int(y - dia0 / 2 - dia / 2 - 6)))
        y -= dia0 + 18
        if names_a > 0.01:
            la = 255 * ease((t - t_start(i) - 0.2) / 0.5) * names_a
            text(d, (xc, y - 8), grp, font("ExtraBold", 22 if len(grp) < 17 else 19), gc, la, 2)
            text(d, (xc, y - 46), big, font("ExtraBold", 44 if len(big) < 9 else 36), (255, 255, 255), la, 3)
            text(d, (xc, y - 88), small, font("SemiBold", 30 if len(small) < 10 else 26), (236, 222, 196), la, 2)

    if glow_col:
        im.paste(glow_col, (0, 0), glow.filter(ImageFilter.GaussianBlur(34)).point(lambda v: int(v * 0.85)))
    pd = ImageDraw.Draw(over)
    for (x0, x1, top, gy_) in sparkle:  # twinkles on the diamond pillar
        for k in range(7):
            ph_ = (t * 1.7 + k * 0.37) % 1.0
            sxk = x0 + (x1 - x0) * ((k * 0.618) % 1); syk = top + (gy_ - top) * ((k * 0.381 + 0.13) % 1)
            r = 14 * max(zx, .45) * math.sin(ph_ * math.pi)
            if r > 1:
                pd.line([(sxk - r, syk), (sxk + r, syk)], fill=(255, 255, 255, 230), width=2)
                pd.line([(sxk, syk - r), (sxk, syk + r)], fill=(255, 255, 255, 230), width=2)
    for (px, py, r, depth, ph0) in PARTS:  # drifting gold dust
        X = (px * (W + 400) - cx * zx * 0.35 * depth) % (W + 400) - 200
        Y = (py * H + t * 26 * depth) % H
        a = int(85 * depth * (0.6 + 0.4 * math.sin(t * 2 + ph0)))
        pd.ellipse([X - r, Y - r, X + r, Y + r], fill=(255, 214, 120, a))

    # ---- screen-space titles
    if t < 2.8:
        k = ease((t - 0.3) / 0.9); a = 255 * k * (1 - ease_io((t - 2.1) / 0.6))
        sc = lerp(1.2, 1.0, k)
        text(d, (W / 2, 1150), SPEC["intro"][0], fit(SPEC["intro"][0], 110 * sc, 980), (255, 214, 100), a, 6)
        text(d, (W / 2, 1275), SPEC["intro"][1], fit(SPEC["intro"][1], 84 * sc, 980), (255, 255, 255), a, 6)
        text(d, (W / 2, 1365), SPEC["intro"][2], fit(SPEC["intro"][2], 32, 980, "SemiBold"), (236, 222, 196), a, 3)
    ha = ease_io((t - 2.3) / 0.5) * (1 - ease_io((t - t_start(4) + 0.1) / 0.4))
    if ha > 0.01:
        d.rounded_rectangle([W / 2 - 300, 212, W / 2 + 300, 288], 38, fill=(20, 10, 2, int(205 * ha)), outline=(255, 205, 70, int(220 * ha)), width=2)
        text(d, (W / 2, 250), SPEC["header"], fit(SPEC["header"], 34, 560), (255, 255, 255), 255 * ha, 0)
    oa = ease_io((t - T_STEPS_END - 0.9) / 0.9)
    if oa > 0.01:
        text(d, (W / 2, 290), SPEC["outro"][0], fit(SPEC["outro"][0], 84, 1000), (255, 255, 255), 255 * oa, 4)
        text(d, (W / 2, 368), SPEC["outro"][1], fit(SPEC["outro"][1], 42, 1000), (255, 214, 100), 255 * oa, 3)
        ca = ease_io((t - T_ZOOM_END + 0.3) / 0.7)
        if ca > 0.01:
            d.rounded_rectangle([60, 1500, W - 60, 1598], 20, fill=(20, 10, 2, int(232 * ca)), outline=(170, 230, 255, int(255 * ca)), width=2)
            text(d, (W / 2, 1532), SPEC["twist"][0], fit(SPEC["twist"][0], 40, 920), (255, 255, 255), 255 * ca, 0)
            text(d, (W / 2, 1574), SPEC["twist"][1], fit(SPEC["twist"][1], 25, 920, "Medium"), (236, 222, 196), 255 * ca, 0)
            text(d, (W / 2, 446), SPEC["question"], fit(SPEC["question"], 44, 1000), (150, 230, 255), 255 * ca, 4)
            text(d, (W / 2, 1626), SPEC["sources"], fit(SPEC["sources"], 19, 1000, "Medium"), (180, 168, 150), 255 * ca, 0)

    im = im.convert("RGBA"); im.alpha_composite(over)
    im.alpha_composite(LOGO, (W - 104 - 36, 1795))
    out = im.convert("RGB")
    fade = min(1, t / 0.35, (TOTAL - t) / 0.5)
    if fade < 1: out = Image.blend(Image.new("RGB", (W, H)), out, max(0, fade))
    return out

# ---------------- audio (numpy, 0 credits: reuses owned music in assets/music) ----------------
MUSIC = {"retro_bollywood": ("retro_bollywood.wav", 28.7), "future_bass": ("future_bass.wav", 30.8)}
def make_audio(path):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, sosfilt
    SR = 44100; NS = int(SR * TOTAL); rng = np.random.default_rng(7)
    def load(f): sr, x = wavfile.read(os.path.join(REPO, "assets/music", f)); return x.astype(np.float64) / 32768
    mf, hit = MUSIC[SPEC.get("music", "retro_bollywood")]
    m = load(mf); off = max(0, int((hit - TOTAL) * SR)); m = m[off:][:NS]
    out = np.zeros((NS, 2)); out[:len(m)] += m * 0.88
    def add(x, t, g):
        i = int(t * SR); e = min(NS, i + len(x))
        if i < NS: out[i:e] += x[:e - i] * g
    def whoosh(dd, lr=True):
        n = int(dd * SR); tt = np.arange(n) / SR; nz = rng.standard_normal(n)
        a = sosfilt(butter(2, [300, 2500], btype="band", fs=SR, output="sos"), nz); b = sosfilt(butter(2, [1500, 7000], btype="band", fs=SR, output="sos"), nz)
        k = tt / dd; x = (a * (1 - k) + b * k) * np.sin(np.pi * k) ** 2; x /= np.max(np.abs(x)); p = k if lr else 0.5 + 0 * k
        return np.stack([x * (1 - p * 0.7), x * (0.3 + p * 0.7)], 1)
    def ching(base=2093, dd=1.0, n=5):
        tt = np.arange(int(dd * SR)) / SR; x = np.zeros_like(tt)
        for k, (r, a) in enumerate([(1, 1), (2.76, .6), (5.4, .35), (8.9, .2), (1.5, .4)][:n]):
            x += a * np.sin(2 * np.pi * base * r * tt + rng.random() * 6) * np.exp(-tt * (3 + 2 * k))
        x *= np.minimum(1, tt / 0.002); x /= np.max(np.abs(x)); return np.stack([x, x], 1)
    def register():
        n = int(0.12 * SR); tt = np.arange(n) / SR
        clk = sosfilt(butter(2, [800, 5000], btype="band", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-tt * 70)
        o = np.zeros((int(1.2 * SR), 2)); o[:n, 0] += clk; o[:n, 1] += clk
        b = ching(2637, 1.0, 4); o[int(0.09 * SR):int(0.09 * SR) + len(b)] += b * 0.9; return o / np.max(np.abs(o))
    def coins(dd=1.0, cnt=14):
        o = np.zeros((int(dd * SR) + SR, 2))
        for _ in range(cnt):
            c = ching(rng.uniform(2600, 4200), 0.4, 3) * rng.uniform(.3, .8); i = int(rng.uniform(0, dd) * SR); pan = rng.uniform(.2, .8)
            o[i:i + len(c), 0] += c[:, 0] * (1 - pan); o[i:i + len(c), 1] += c[:, 1] * pan
        return o
    crowd = [load(f"crowd{k}.wav") for k in (1, 2, 3)]
    def fadeout(x): x = x.copy(); fo = min(len(x) // 3, int(0.35 * SR)); x[-fo:] *= np.linspace(1, 0, fo)[:, None]; return x
    lands = [t_land(i) for i in range(N)]
    add(whoosh(1.8), 0.9, 0.16)
    for i in range(1, N): add(whoosh(0.7), t_start(i) - 0.05, 0.13)
    for i, tl in enumerate(lands): add(register(), tl - 0.03, 0.20 + 0.012 * i); add(coins(0.5, 4 + i), tl + 0.05, 0.09)
    add(coins(1.6, 40), lands[-1] + 0.1, 0.15); add(fadeout(crowd[0]), lands[-1], 0.3); add(fadeout(crowd[1]), lands[-1] + 0.5, 0.22)
    add(whoosh(2.0, False), T_STEPS_END - 0.1, 0.22)
    for k, o_ in enumerate([1.9, 2.4, 2.9]): add(fadeout(crowd[(k + 1) % 3]), T_STEPS_END + o_, 0.28 * (1 - 0.2 * k))
    fl = int(0.5 * SR); out[-fl:] *= np.linspace(1, 0, fl)[:, None]
    pk = np.max(np.abs(out)); out = out / pk * 0.97 if pk > 0.97 else out
    out = np.tanh(out * 1.15) / np.tanh(1.15) * 0.9
    wavfile.write(path, SR, (out * 32767).astype(np.int16))

def make_cover(path):
    """Grid-safe cover: title, hero badge (spec 'cover_hero' item index), hook pill, row of all badges, question, logo."""
    c = SPEC.get("cover", {})
    im = bg_big.crop((int(BGW / 2 - W / 2), int((BGH - H) / 2), int(BGW / 2 + W / 2), int((BGH - H) / 2) + H)).convert("RGB")
    sh = Image.new("L", (W, H), 70); ImageDraw.Draw(sh).rectangle([0, 180, W, 720], fill=150)
    im.paste((8, 2, 4), (0, 0), sh.filter(ImageFilter.GaussianBlur(70)))
    d = ImageDraw.Draw(im)
    def T(xy, s_, f, fill, sw=6): d.text(xy, s_, font=f, fill=fill, anchor="mm", stroke_width=sw, stroke_fill=(8, 2, 4))
    t1, t2, t3 = (c.get("title", SPEC["intro"]) + ["", "", ""])[:3]
    T((W / 2, 330), t1, fit(t1, 130, 980), (255, 214, 100)); T((W / 2, 465), t2, fit(t2, 104, 980), "white"); T((W / 2, 570), t3, fit(t3, 46, 900), (150, 230, 255))
    hi = c.get("hero", N - 1)
    g = Image.new("L", (W, H), 0); ImageDraw.Draw(g).ellipse([W / 2 - 320, 640, W / 2 + 320, 1280], fill=170)
    im.paste(MCOL[MAT[hi]][4], (0, 0), g.filter(ImageFilter.GaussianBlur(85)))
    b = BADGES[hi].resize((460, 460), Image.LANCZOS); im.paste(b, (int(W / 2 - 230), 660), b)
    d = ImageDraw.Draw(im); pill = c.get("pill", "")
    if pill:
        f = fit(pill, 54, 700); pw_ = f.getlength(pill) / 2 + 40
        d.rounded_rectangle([W / 2 - pw_, 1110, W / 2 + pw_, 1200], 45, fill=(255, 214, 100)); d.text((W / 2, 1155), pill, font=f, fill=(40, 20, 0), anchor="mm")
    s_ = min(112, int((980 - (N - 1) * 12) / N))
    for k in range(N):
        x = int(W / 2 - (N * s_ + (N - 1) * 12) / 2 + k * (s_ + 12)); bb = BADGES[k].resize((s_, s_), Image.LANCZOS); im.paste(bb, (x, 1245), bb)
    q = c.get("question", "Guess No. 1?"); T((430, 1450), q, fit(q, 70, 560), "white")
    logo = Image.open(os.path.join(REPO, "assets/logo.png")).convert("RGBA").resize((130, 130), Image.LANCZOS); im.paste(logo, (760, 1385), logo)
    im.save(path, quality=92)

if __name__ == "__main__":
    if "--preview" in sys.argv:
        for tt in sys.argv[sys.argv.index("--preview") + 1:]:
            p = os.path.join(WORK, f"frame_{tt}.png"); frame(float(tt)).save(p); print(p)
        sys.exit(0)
    out = SPEC["out"]; cover = SPEC["cover_out"]; os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    print("TOTAL", round(TOTAL, 2), "s, items", N)
    silent = os.path.join(WORK, "silent.mp4"); wav = os.path.join(WORK, "mix.wav")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent], stdin=subprocess.PIPE)
    for k in range(int(TOTAL * FPS)): ff.stdin.write(frame(k / FPS).tobytes())
    ff.stdin.close(); assert ff.wait() == 0
    make_audio(wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", "volume=-1.5dB", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    make_cover(cover)
    for tt in (round(t_land(N // 2) + 0.4, 1), round(TOTAL - 1.0, 1)):
        frame(tt).save(os.path.join(WORK, f"check_{tt}.png"))
    print("OK", out, cover, "check frames in", WORK)
