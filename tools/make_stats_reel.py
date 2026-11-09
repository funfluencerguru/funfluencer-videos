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
    "bronze": ((226, 186, 150), (248, 222, 196), (255, 244, 232), (40, 18, 4), (230, 140, 70)),
    "silver": ((216, 222, 232), (242, 245, 250), (255, 255, 255), (26, 30, 40), (210, 220, 240)),
    "gold": ((240, 214, 140), (253, 240, 190), (255, 252, 232), (52, 32, 0), (255, 205, 70)),
    "diamond": ((210, 236, 252), (236, 249, 255), (255, 255, 255), (12, 34, 66), (170, 230, 255)),
}

PITCH, PWW, HMAX, PED = 330, 240, 1100, 260   # tall scale so differences read clearly
FLOOR = 60
VMAX = max(p[3] for p in P)
def hof(v): return FLOOR + (HMAX - FLOOR) * v / VMAX
def wx(i): return i * PITCH
T_INTRO, STEP, PAN, RISE0, GROW, EXTRA, ZOOM, HOLD = 2.6, 2.3, 0.55, 0.45, 1.0, 0.8, 2.4, 3.4
T_STEPS_END = T_INTRO + N * STEP + EXTRA
T_ZOOM_END = T_STEPS_END + ZOOM
TOTAL = T_ZOOM_END + HOLD
def t_start(i): return T_INTRO + i * STEP
def t_land(i): return t_start(i) + RISE0 + GROW
SPAN = wx(N - 1) + PWW
LAB = 400            # world space reserved for labels above a pillar (value + badge + names)
ZX_O = 1000 / SPAN
ZY_O = min(0.62, 1000 / (PED + HMAX + 170)); BASE_O = 1480

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def ease_io(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def ease_io5(t): t = max(0.0, min(1.0, t)); return t*t*t*(t*(6*t-15)+10)
def back(t):
    t = max(0, min(1, t)); c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k

# ---- drone camera: shots are (cx, z, base); z = zoom, base = screen y of the ground line ----
def shot_close(i):          # low and close at the foot of the pillar, a little to its right (approach from the left)
    return (wx(i) + PWW * 0.5 + 40, 1.24, 1580.0)
def shot_crane(i, g):       # follows the growing top upward
    top = PED + hof(P[i][3]) * g
    return (wx(i) + PWW * 0.5 + 20, lerp(1.24, 1.06, g), max(1580.0, 640 + (top + LAB * 0.55) * 1.06 * 0.92))
def shot_wide(i):           # pull back and up: this pillar and the previous one fully in frame
    j = max(0, i - 1)
    cx = (wx(j) + wx(i) + PWW) / 2 + (40 if i == 0 else 0)
    hh = PED + hof(P[i][3]) + LAB
    z = min(0.95, 1080 / hh, W * 0.80 / (wx(i) + PWW - wx(j) + 60))
    return (cx, z, min(1620.0, 470 + hh * z))
def blend(a, b, k):
    return (lerp(a[0], b[0], k), math.exp(lerp(math.log(a[1]), math.log(b[1]), k)), lerp(a[2], b[2], k))

CAM_MODE = SPEC.get("camera", "orbit")   # DEFAULT orbit (owner-approved 9 Nov 2026). Others: drone | track | lowangle | flyover
VIEW = {"dx": 0.16, "dy": -0.10, "key": 0.0}   # 3D depth direction (x pillar width) + keystone (+ low angle, - looking down)
MODE_Z = {"track": 0.80, "lowangle": 0.95, "orbit": 1.05, "flyover": 0.72}
def cam_modes(t):
    z0 = MODE_Z[CAM_MODE]
    if t < T_INTRO:
        k = ease_io5((t - 0.6) / (T_INTRO - 0.6)); cx = lerp(-900, PWW / 2 + 60, k)
        return cx, z0, z0, lerp(2300, 1560, k), 0, 0, 0.0, 1 - k
    i = min(N - 1, int((t - T_INTRO) // STEP)); lt = t - t_start(i)
    g = ease((lt - RISE0) / GROW) if lt > RISE0 else 0.0
    hcur = PED + hof(P[i][3]) * g; hprev = PED + hof(P[i - 1][3]) if i > 0 else 0
    tall = max(hcur, hprev) + LAB
    z = z0 * (1 + 0.015 * math.sin(t * 1.1))
    if CAM_MODE == "orbit":
        TR = SPEC.get("transition", "glide")             # DEFAULT glide (owner-approved). Others: whip | lift : how the camera travels between pillars
        PT = {"glide": 0.85, "whip": 0.30, "lift": 0.85}[TR]
        kr = min(1.0, lt / PT)
        k = ease_io5(kr) if TR != "whip" else (1 - (1 - kr) ** 4)
        prevc = wx(i - 1) + PWW / 2 if i > 0 else PWW / 2
        th = lerp(0.9, -0.9, ease_io(lt / STEP))
        th_prev = -0.9
        thc = lerp(th_prev, th, ease_io(kr)) if i > 0 else th
        VIEW["dx"], VIEW["dy"] = 0.30 * math.sin(thc), -0.10
        cx = lerp(prevc + 120 * 0.78, wx(i) + PWW / 2 - 120 * math.sin(th), k) if i > 0 else wx(i) + PWW / 2 - 120 * math.sin(th)
        z = z0 * (1 + 0.06 * math.cos(thc))
        base = max(1560.0, 500 + tall * z * 0.9)
        VIEW["blur"] = 0.0
        if i > 0 and kr < 1:
            if TR == "lift":   # rise up and look down a little, fly across, drop in
                up = math.sin(math.pi * kr)
                z *= 1 - 0.28 * up; base += 260 * up; VIEW["dy"] = -0.10 - 0.25 * up
            elif TR == "whip":  # fast pan with motion blur
                VIEW["blur"] = 90 * math.sin(math.pi * kr) ** 2
    else:
        cx = PWW / 2 + (t - T_INTRO - STEP * 0.35) / STEP * PITCH + (60 if CAM_MODE == "track" else 0)
        base = max(1500.0 if CAM_MODE != "lowangle" else 1760.0, 480 + tall * z)
        if CAM_MODE == "lowangle": VIEW["dx"], VIEW["dy"], VIEW["key"] = 0.16, -0.02, 0.20
        elif CAM_MODE == "flyover": VIEW["dx"], VIEW["dy"], VIEW["key"] = 0.08, -0.42, -0.17; base = max(1450.0, 600 + tall * z)
        else: VIEW["dx"], VIEW["dy"] = 0.16, -0.10
    sh = t - t_land(i); dx = dy = 0
    if 0 < sh < 0.35:
        a = 12 * math.exp(-sh * 11); dx, dy = a * math.sin(sh * 90), a * math.cos(sh * 70)
    return cx, z, z, base, dx, dy, 0.0, 0.0

def camera(t):
    if CAM_MODE != "drone" and t < T_STEPS_END: return cam_modes(t)
    if t < T_INTRO:   # drone flies in from far left and low
        k = ease_io5((t - 0.6) / (T_INTRO - 0.6))
        c0 = shot_close(0); cx = lerp(-900, c0[0], k)
        z = lerp(1.05, c0[1], k)
        return cx, z, z, lerp(2300, c0[2], k), 0, 0, 0.0, 1 - k
    if t < T_STEPS_END:
        i = min(N - 1, int((t - T_INTRO) // STEP))
        lt = t - t_start(i)
        prev = shot_wide(i - 1) if i > 0 else shot_close(0)
        if lt < PAN:                                   # swoop from the previous wide shot down to the next pillar
            k = ease_io5(lt / PAN); c = blend(prev, shot_close(i), k)
            arc = 0.10 * math.sin(math.pi * k) if i > 0 else 0   # drone lifts slightly mid-swoop
            cx, z, base = c[0], c[1] * (1 - arc), c[2] + 120 * math.sin(math.pi * k) * (i > 0)
        elif lt < RISE0 + GROW:                         # crane up with the pillar
            g = ease((lt - RISE0) / GROW) if lt > RISE0 else 0.0
            c = blend(shot_close(i), shot_crane(i, g), ease_io(min(1, (lt - PAN) / (RISE0 + GROW - PAN))))
            cx, z, base = c
        else:                                           # pull back and up to compare with the previous pillar
            k = ease_io5((lt - RISE0 - GROW) / (STEP - RISE0 - GROW))
            c = blend(shot_crane(i, 1.0), shot_wide(i), k); cx, z, base = c
        z *= 1 + 0.01 * math.sin(t * 1.3)
        sh = t - t_land(i); dx = dy = 0
        if 0 < sh < 0.35:
            a = (12 if i < N - 2 else 20) * math.exp(-sh * 11)
            dx, dy = a * math.sin(sh * 90), a * math.cos(sh * 70)
        return cx, z, z, base, dx, dy, 0.0, 0.0
    if CAM_MODE != "drone":   # start the final pull-out exactly where the step camera ended
        c_ = cam_modes(T_STEPS_END - 1e-3); last = (c_[0], c_[1], c_[3]); dx_end = VIEW["dx"]
    else:
        last = shot_wide(N - 1); dx_end = VIEW["dx"]
    lt = t - T_STEPS_END
    k = ease_io5(lt / ZOOM)
    VIEW["dx"], VIEW["dy"], VIEW["blur"] = lerp(dx_end, 0.16, k), -0.10, 0.0
    cx = lerp(last[0], SPAN / 2, k)
    zx = math.exp(lerp(math.log(last[1]), math.log(ZX_O), k))
    zy = math.exp(lerp(math.log(last[1]), math.log(ZY_O), k))
    base = lerp(last[2], BASE_O, k) - 160 * math.sin(math.pi * k)   # rises up while pulling out
    if t > T_ZOOM_END:
        h = (t - T_ZOOM_END) / HOLD
        zx *= 1 + 0.015 * h; zy *= 1 + 0.015 * h
    return cx, zx, zy, base, 0, 0, k, 0.0

# ---------- assets ----------
# Theme presets: background + default music per topic category. Spec "theme" picks one; "bg"/"music" in the spec override.
THEMES = {
    "money":    {"bg": {"style": "drawn", "scene": "money", "motif": "₹", "left_color": [128, 78, 36], "right_color": [26, 84, 104]}, "music": "retro_bollywood"},
    "cricket":  {"bg": {"style": "photo", "file": "cricket_stadium.png"}, "music": "stadium_anthem"},
    "sports":   {"bg": {"style": "photo", "file": "cricket_stadium.png"}, "music": "stadium_anthem_alt"},
    "bollywood":{"bg": {"style": "photo", "file": "cinema_stage.png"}, "music": "retro_bollywood"},
    "tech":     {"bg": {"style": "drawn", "scene": "tech", "motif": "●", "left_color": [20, 30, 70], "right_color": [70, 20, 90]}, "music": "future_bass"},
    "space":    {"bg": {"style": "drawn", "scene": "space", "motif": "✦", "left_color": [8, 12, 40], "right_color": [40, 10, 60]}, "music": "future_bass"},
    "city":     {"bg": {"style": "drawn", "scene": "city", "motif": "●", "left_color": [30, 20, 70], "right_color": [120, 50, 70]}, "music": "future_bass"},
    "geo":      {"bg": {"style": "drawn", "scene": "geo", "motif": "▲", "left_color": [30, 90, 110], "right_color": [140, 100, 40]}, "music": "retro_bollywood"},
    "world":    {"bg": {"style": "drawn", "scene": "world", "motif": "●", "left_color": [14, 50, 90], "right_color": [20, 90, 80]}, "music": "stadium_anthem_alt"},
    "food":     {"bg": {"style": "drawn", "scene": "money", "motif": "●", "left_color": [140, 70, 20], "right_color": [150, 40, 40]}, "music": "retro_bollywood"},
}
TH = THEMES.get(SPEC.get("theme", "money"), THEMES["money"])
BGSPEC = dict(TH["bg"]); BGSPEC.update(SPEC.get("bg", {}))
MUSIC_NAME = SPEC.get("music") or TH["music"]

def scene_art(d, scene, BW, BH, rr):
    """Topic scenery drawn on the RGBA overlay (low alpha, sits behind everything)."""
    if scene == "tech":  # circuit grid
        for x in range(0, BW, 120): d.line([(x, 0), (x, BH)], fill=(120, 200, 255, 48), width=2)
        for y in range(0, BH, 120): d.line([(0, y), (BW, y)], fill=(120, 200, 255, 48), width=2)
        for _ in range(70):
            x, y = rr.randrange(0, BW, 120), rr.randrange(0, BH, 120); L_ = rr.choice([240, 360, 480])
            d.line([(x, y), (x + L_, y), (x + L_, y + 120)], fill=(120, 230, 255, 154), width=5); d.ellipse([x + L_ - 10, y + 110, x + L_ + 10, y + 130], fill=(120, 230, 255, 230))
    elif scene == "space":
        for _ in range(900):
            x, y, r = rr.uniform(0, BW), rr.uniform(0, BH), rr.choice([1, 1, 2, 3]); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rr.randint(120, 255)))
        for (x, y, r, c) in ((520, 1500, 260, (230, 140, 80)), (3150, 1350, 190, (120, 170, 255)), (1900, 260, 90, (240, 220, 200))):
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (90,)); d.ellipse([x - r * 1.6, y - r * 0.25, x + r * 1.6, y + r * 0.25], outline=c + (70,), width=8)
    elif scene == "city":
        x = 0
        while x < BW:
            w_ = rr.randint(120, 260); h_ = rr.randint(500, 1300); top = 2000 - h_
            d.rectangle([x, top, x + w_, 2300], fill=(10, 8, 30, 230))
            for yy in range(top + 30, 1980, 60):
                for xx in range(x + 20, x + w_ - 30, 50):
                    if rr.random() < 0.45: d.rectangle([xx, yy, xx + 22, yy + 30], fill=(255, 220, 140, 198))
            x += w_ + rr.randint(10, 40)
    elif scene == "geo":
        pts = [(0, 1500)] + [(x, 1500 - rr.randint(200, 700) * (0.5 + 0.5 * math.sin(x / 400))) for x in range(0, BW + 300, 300)] + [(BW, 2300), (0, 2300)]
        d.polygon(pts, fill=(20, 40, 50, 230))
        for (x, y) in pts[1:-2]:
            if y < 1050: d.polygon([(x - 90, y + 130), (x, y), (x + 90, y + 130)], fill=(240, 245, 255, 230))
        d.line([(x, 1700 + 120 * math.sin(x / 300)) for x in range(0, BW, 40)], fill=(120, 200, 255, 230), width=40)
        d.ellipse([2700, 250, 3050, 600], fill=(255, 210, 120, 176))
    elif scene == "world":
        cx, cy, R = BW / 2, 1250, 900
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(150, 230, 255, 154), width=8)
        for k in range(1, 6): rx = R * k / 6; d.ellipse([cx - rx, cy - R, cx + rx, cy + R], outline=(150, 230, 255, 88), width=4)
        for k in range(-4, 5): y = cy + R * k / 5; w_ = R * math.sqrt(max(0, 1 - (k / 5) ** 2)); d.line([(cx - w_, y), (cx + w_, y)], fill=(150, 230, 255, 88), width=4)

def make_bg(path):
    """Drawn backdrop (0 credits): two-colour gradient, sunburst, two big faded words, scattered motifs."""
    import numpy as np
    b = BGSPEC
    BW, BH = 3600, 2300; rr = random.Random(b.get("seed", 5))
    if b.get("style") == "photo":
        ph = Image.open(os.path.join(REPO, "assets/backgrounds", b["file"])).convert("RGB")
        ph = ph.resize((int(ph.width * BH / ph.height), BH), Image.LANCZOS).filter(ImageFilter.GaussianBlur(b.get("blur", 3)))
        Image.blend(ph, Image.new("RGB", ph.size), b.get("darken", 0.30)).save(path); return
    cl, cr = b.get("left_color", [128, 78, 36]), b.get("right_color", [26, 84, 104])
    xs = np.linspace(0, 1, BW)[None, :, None]; ys = np.linspace(0, 1, BH)[:, None, None]
    a = (np.array(cl) * (1 - xs) + np.array(cr) * xs) * (1.05 - 0.45 * ys)
    im = Image.fromarray(np.clip(a, 0, 255).astype("uint8")).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    cx, cy = BW / 2, BH * 0.42
    for k in (range(48) if b.get("scene", "money") == "money" else []):
        a0 = k * 2 * math.pi / 48; a1 = a0 + math.pi / 48
        d.polygon([(cx, cy), (cx + 4000 * math.cos(a0), cy + 4000 * math.sin(a0)), (cx + 4000 * math.cos(a1), cy + 4000 * math.sin(a1))], fill=(255, 230, 180, 22))
    if b.get("scene", "money") != "money": scene_art(d, b["scene"], BW, BH, rr)
    lw, rw = b.get("left_word", ""), b.get("right_word", "")
    for word, x, col in ((lw, 620, (255, 210, 140, 70)), (rw, BW - 620, (140, 230, 255, 70))):
        if word:
            fs = 520
            while fs > 120 and font("ExtraBold", fs).getlength(word) > 1150: fs -= 20
            d.text((x, 560), word, font=font("ExtraBold", fs), fill=col, anchor="mm")
    motif = b.get("motif", "₹")
    for _ in range(90 if b.get("scene", "money") in ("money",) else 30):
        x, y = rr.uniform(0, BW), rr.uniform(900, BH); k = x / BW
        col = tuple(int(c) for c in (255 * (1 - k) + 150 * k, 214 * (1 - k) + 230 * k, 140 * (1 - k) + 255 * k))
        sz = rr.uniform(40, 120); al = rr.randint(35, 80)
        if rr.random() < 0.5:
            d.text((x, y), motif, font=font("ExtraBold", int(sz * 1.2)), fill=col + (al,), anchor="mm")
        else:
            d.ellipse([x - sz / 2, y - sz / 2, x + sz / 2, y + sz / 2], outline=col + (al + 10,), width=6)
    if b.get("scene", "money") == "money":
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

def _star(d, cx, cy, r, col):
    pts = [(cx + (r if k % 2 == 0 else r * 0.42) * math.cos(-math.pi / 2 + k * math.pi / 5), cy + (r if k % 2 == 0 else r * 0.42) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    d.polygon(pts, fill=col)

def draw_flag(im, code, Z):
    """Simple drawn national flags, shown as a waving-free rectangle in the badge. Codes: ISO-3 / cricket short names."""
    fw, fh = int(Z * 0.86), int(Z * 0.58); f = Image.new("RGB", (fw, fh), (255, 255, 255)); d = ImageDraw.Draw(f)
    def H(cols):
        for k, c in enumerate(cols): d.rectangle([0, fh * k / len(cols), fw, fh * (k + 1) / len(cols)], fill=c)
    def V(cols):
        for k, c in enumerate(cols): d.rectangle([fw * k / len(cols), 0, fw * (k + 1) / len(cols), fh], fill=c)
    R, Wt, G, B, Y, K = (220, 40, 50), (255, 255, 255), (0, 130, 70), (20, 50, 140), (250, 200, 30), (20, 20, 20)
    c = code
    if c in ("IND", "INDIA"):
        H([(255, 153, 51), Wt, (19, 136, 8)]); r = fh / 7; d.ellipse([fw / 2 - r, fh / 2 - r, fw / 2 + r, fh / 2 + r], outline=(0, 0, 128), width=max(2, int(r / 4)))
        for k in range(12): a_ = k * math.pi / 6; d.line([(fw / 2, fh / 2), (fw / 2 + r * math.cos(a_), fh / 2 + r * math.sin(a_))], fill=(0, 0, 128), width=1)
    elif c in ("AUS", "NZ", "NZL"):
        f.paste((0, 36, 125), [0, 0, fw, fh]); d.rectangle([0, 0, fw / 2, fh / 2], fill=(0, 36, 125))
        d.line([(0, 0), (fw / 2, fh / 2)], fill=Wt, width=int(fh / 12)); d.line([(fw / 2, 0), (0, fh / 2)], fill=Wt, width=int(fh / 12))
        d.rectangle([fw / 4 - fh / 24, 0, fw / 4 + fh / 24, fh / 2], fill=R); d.rectangle([0, fh / 4 - fh / 24, fw / 2, fh / 4 + fh / 24], fill=R)
        col = Wt if c == "AUS" else R
        for (x, y) in ((0.75, 0.25), (0.68, 0.55), (0.85, 0.45), (0.75, 0.8)): _star(d, fw * x, fh * y, fh / 12, col)
        if c == "AUS": _star(d, fw * 0.25, fh * 0.75, fh / 9, Wt)
    elif c in ("ENG",):
        d.rectangle([fw / 2 - fh / 10, 0, fw / 2 + fh / 10, fh], fill=R); d.rectangle([0, fh / 2 - fh / 10, fw, fh / 2 + fh / 10], fill=R)
    elif c in ("UK", "GBR"):
        f.paste((1, 33, 105), [0, 0, fw, fh])
        for (p1, p2) in (((0, 0), (fw, fh)), ((fw, 0), (0, fh))): d.line([p1, p2], fill=Wt, width=int(fh / 6)); d.line([p1, p2], fill=R, width=int(fh / 16))
        d.rectangle([fw / 2 - fh / 6, 0, fw / 2 + fh / 6, fh], fill=Wt); d.rectangle([0, fh / 2 - fh / 6, fw, fh / 2 + fh / 6], fill=Wt)
        d.rectangle([fw / 2 - fh / 10, 0, fw / 2 + fh / 10, fh], fill=R); d.rectangle([0, fh / 2 - fh / 10, fw, fh / 2 + fh / 10], fill=R)
    elif c in ("PAK",):
        f.paste((1, 65, 28), [0, 0, fw, fh]); d.rectangle([0, 0, fw / 4, fh], fill=Wt)
        cx, cy, r = fw * 0.62, fh / 2, fh * 0.3; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=Wt); d.ellipse([cx - r * 0.75, cy - r * 1.05, cx + r * 1.1, cy + r * 0.7], fill=(1, 65, 28))
        _star(d, cx + r * 0.55, cy - r * 0.35, r * 0.28, Wt)
    elif c in ("SA", "RSA", "ZAF"):
        H([R, Wt, B]); d.polygon([(0, 0), (fw * 0.45, fh / 2), (0, fh)], fill=G)
        d.polygon([(0, fh * 0.12), (fw * 0.33, fh / 2), (0, fh * 0.88)], fill=Y); d.polygon([(0, fh * 0.22), (fw * 0.27, fh / 2), (0, fh * 0.78)], fill=K)
        d.rectangle([fw * 0.42, fh * 0.4, fw, fh * 0.6], fill=G)
    elif c in ("SL", "SRI", "LKA"):
        f.paste(Y, [0, 0, fw, fh]); d.rectangle([fw * 0.05, fh * 0.08, fw * 0.12, fh * 0.92], fill=(0, 114, 74)); d.rectangle([fw * 0.13, fh * 0.08, fw * 0.2, fh * 0.92], fill=(255, 130, 0))
        d.rectangle([fw * 0.24, fh * 0.08, fw * 0.95, fh * 0.92], fill=(141, 21, 58)); d.ellipse([fw * 0.48, fh * 0.3, fw * 0.72, fh * 0.7], fill=Y)
    elif c in ("WI",):
        f.paste((120, 20, 40), [0, 0, fw, fh]); d.ellipse([fw * 0.35, fh * 0.15, fw * 0.65, fh * 0.85], fill=Y)
    elif c in ("BAN", "BGD"):
        f.paste((0, 106, 78), [0, 0, fw, fh]); r = fh * 0.3; d.ellipse([fw * 0.45 - r, fh / 2 - r, fw * 0.45 + r, fh / 2 + r], fill=(244, 42, 65))
    elif c in ("AFG",): V([K, (190, 0, 0), (0, 122, 54)])
    elif c in ("ZIM", "ZWE"): H([G, Y, R, K, R, Y, G])
    elif c in ("IRE", "IRL"): V([(22, 155, 98), Wt, (255, 136, 62)])
    elif c in ("NED", "NLD"): H([(174, 28, 40), Wt, (33, 70, 139)])
    elif c in ("USA",):
        for k in range(13): d.rectangle([0, fh * k / 13, fw, fh * (k + 1) / 13], fill=R if k % 2 == 0 else Wt)
        d.rectangle([0, 0, fw * 0.4, fh * 7 / 13], fill=(60, 59, 110))
        for yy in range(5):
            for xx in range(6): d.ellipse([fw * 0.03 + xx * fw * 0.062, fh * 0.05 + yy * fh * 0.1, fw * 0.03 + xx * fw * 0.062 + 4, fh * 0.05 + yy * fh * 0.1 + 4], fill=Wt)
    elif c in ("CHN",):
        f.paste((222, 41, 16), [0, 0, fw, fh]); _star(d, fw * 0.17, fh * 0.3, fh * 0.15, (255, 222, 0))
        for (x, y) in ((0.32, 0.12), (0.38, 0.25), (0.38, 0.42), (0.32, 0.55)): _star(d, fw * x, fh * y, fh * 0.05, (255, 222, 0))
    elif c in ("JPN",):
        r = fh * 0.3; d.ellipse([fw / 2 - r, fh / 2 - r, fw / 2 + r, fh / 2 + r], fill=(188, 0, 45))
    elif c in ("GER", "DEU"): H([K, (221, 0, 0), (255, 206, 0)])
    elif c in ("FRA",): V([(0, 85, 164), Wt, (239, 65, 53)])
    elif c in ("ITA",): V([(0, 146, 70), Wt, (206, 43, 55)])
    elif c in ("RUS",): H([Wt, (0, 57, 166), (213, 43, 30)])
    elif c in ("IDN", "INA"): H([(206, 17, 38), Wt])
    elif c in ("BRA",):
        f.paste((0, 156, 59), [0, 0, fw, fh]); d.polygon([(fw * 0.08, fh / 2), (fw / 2, fh * 0.08), (fw * 0.92, fh / 2), (fw / 2, fh * 0.92)], fill=(255, 223, 0))
        r = fh * 0.24; d.ellipse([fw / 2 - r, fh / 2 - r, fw / 2 + r, fh / 2 + r], fill=(0, 39, 118))
    elif c in ("CAN",):
        V([(216, 6, 33), Wt, Wt, (216, 6, 33)]); _star(d, fw / 2, fh / 2, fh * 0.28, (216, 6, 33))
    elif c in ("KOR",):
        r = fh * 0.22; d.pieslice([fw / 2 - r, fh / 2 - r, fw / 2 + r, fh / 2 + r], 180, 360, fill=(205, 46, 58)); d.pieslice([fw / 2 - r, fh / 2 - r, fw / 2 + r, fh / 2 + r], 0, 180, fill=(0, 71, 160))
    elif c in ("UAE", "ARE"):
        H([(0, 115, 47), Wt, K]); d.rectangle([0, 0, fw / 4, fh], fill=(255, 0, 0))
    elif c in ("SAU", "KSA"):
        f.paste((0, 108, 53), [0, 0, fw, fh]); d.line([(fw * 0.25, fh * 0.65), (fw * 0.75, fh * 0.65)], fill=Wt, width=max(2, int(fh / 20)))
    elif c in ("NEP", "NPL"):
        f.paste(Wt, [0, 0, fw, fh]); d.polygon([(fw * 0.25, 0), (fw * 0.7, fh * 0.45), (fw * 0.4, fh * 0.45), (fw * 0.75, fh), (fw * 0.25, fh)], fill=(220, 20, 60), outline=(0, 56, 147))
    elif c in ("KEN",): H([K, R, G])
    elif c in ("MEX",): V([(0, 104, 71), Wt, (206, 17, 38)])
    elif c in ("ESP",): H([(170, 21, 27), (241, 191, 0), (241, 191, 0), (170, 21, 27)])
    else:
        f.paste((70, 80, 100), [0, 0, fw, fh]); d.text((fw / 2, fh / 2), c[:3], font=font("ExtraBold", int(fh * 0.45)), fill=Wt, anchor="mm")
    m = Image.new("L", (fw, fh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, fw - 1, fh - 1], int(fh * 0.12), fill=255)
    im.paste(f, ((Z - fw) // 2, (Z - fh) // 2), m)
    ImageDraw.Draw(im).rounded_rectangle([(Z - fw) // 2, (Z - fh) // 2, (Z + fw) // 2 - 1, (Z + fh) // 2 - 1], int(fh * 0.12), outline=(60, 40, 20), width=max(2, Z // 80))

def item_art(slug, Z):
    """Drawn icon library. 'glyph:TEXT' draws short text (e.g. glyph:4G, glyph:₹). Add new icons here as new elif branches."""
    im = Image.new("RGBA", (Z, Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im); u = Z / 100
    def B(*p): return [v * u for v in p]
    if slug.startswith("img:"):  # illustrated icon from assets/icons/<name>.png (India icon pack)
        ip = os.path.join(REPO, "assets/icons", slug[4:] + ".png")
        if os.path.exists(ip):
            ic = Image.open(ip).convert("RGBA").resize((int(Z * 1.12), int(Z * 1.12)), Image.LANCZOS)
            im.alpha_composite(ic, (int(-Z * 0.06), int(-Z * 0.06))); return im
        slug = "glyph:" + slug[4:7].upper()
    if slug.startswith("flag:"):
        draw_flag(im, slug[5:].upper(), Z); return im
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
VNAMES = [vlabel(p[7], (110, 58, 12, 255)) for i, p in enumerate(P)]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import logo_box, add_cta
LOGO_X, LOGO_Y, LOGO_S = logo_box(104, 36)  # owner rule 2026-11-09: 10% bigger, lifted from the bottom
LOGO = Image.open(os.path.join(REPO, "assets/logo.png")).convert("RGBA").resize((LOGO_S, LOGO_S), Image.LANCZOS)
rnd = random.Random(11)
PARTS = [(rnd.random(), rnd.random(), rnd.uniform(2, 6), rnd.uniform(0.3, 1.0), rnd.uniform(0, 6.28)) for _ in range(80)]

def fit(s_, size, maxw, w="ExtraBold"):
    size = int(size)
    while size > 12 and font(w, size).getlength(s_) > maxw: size -= 1
    return font(w, size)
def wa(c, a): return tuple(c[:3]) + (int(max(0, min(255, a))),)
def text(d, xy, s, f, fill, a=255, stroke=3, sc=(8, 4, 0)):
    d.text(xy, s, font=f, fill=wa(fill, a), anchor="mm", stroke_width=stroke, stroke_fill=wa(sc, a * 0.85))

PED_FRONT_TOP, PED_FRONT_BOT = (255, 253, 248), (238, 230, 214)   # light ivory pedestal
PED_TEXT = [(120, 62, 14), (0, 98, 140), (176, 110, 0)]           # 1st line, 2nd line, note
def tint(c, f): return tuple(int(max(0, min(255, v * f))) for v in c)
def box3d(im, d, x0, x1, ytop, ybot, front, side_col, top_col, dep):
    """Front face image + right side face + top face, giving a 3D block. dep = (dx, dy) depth vector (dy negative = up)."""
    dx, dy = dep
    if side_col and abs(dx) > 0.5:
        n = 12; xe = x1 if dx > 0 else x0
        for k in range(n):  # side face with vertical gradient
            y0_ = ytop + (ybot - ytop) * k / n; y1_ = ytop + (ybot - ytop) * (k + 1) / n
            c = tint(side_col, 1.0 - 0.18 * k / n)
            d.polygon([(xe, y0_), (xe + dx, y0_ + dy), (xe + dx, y1_ + dy + 1), (xe, y1_ + 1)], fill=c + (255,))
    if front is not None: im.paste(front, (int(x0), int(ytop)))
    if top_col:
        d.polygon([(x0, ytop), (x0 + dx, ytop + dy), (x1 + dx, ytop + dy), (x1, ytop)], fill=top_col + (255,))

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
            ped = Image.new("RGB", (max(2, int(pw)), max(2, int(pedh))), PED_FRONT_TOP); pdd = ImageDraw.Draw(ped)
            for yy in range(ped.height):
                k = yy / max(1, ped.height); pdd.line([(0, yy), (ped.width, yy)], fill=tuple(int(PED_FRONT_TOP[j] + (PED_FRONT_BOT[j] - PED_FRONT_TOP[j]) * k) for j in range(3)))
            pdd.rectangle([0, 0, ped.width, max(2, int(6 * zy))], fill=(214, 160, 60))
            pdd.rectangle([int(8 * zx), int(14 * zy), ped.width - int(8 * zx), ped.height - int(10 * zy)], outline=(200, 160, 90), width=max(1, int(2 * zx)))
            dep = (pw * VIEW['dx'], pw * VIEW['dy'])
            box3d(im, ImageDraw.Draw(im, "RGBA"), x0, x1, pt, gy, ped, (200, 186, 160), (240, 210, 140), dep)
            rs = max(20, int(44 * zx))
            text(d, (xc, pt + rs * 0.95), f"#{N - i}", font("ExtraBold", rs), (150, 84, 10), 255 * pg, 0)
            if names_a > 0.01 and zx > 0.6 and pedh - rs * 1.9 - 16 * zy > 30:
                ba = 255 * names_a * ease((t - t_start(i) - 0.3) / 0.5)
                n_ = len(brands); avail = pedh - rs * 1.9 - 16 * zy
                lh = min(50 * zy, avail / max(1, n_)); yb = pt + rs * 1.9
                for bi, bname in enumerate(brands):
                    fs = int(min((30 if bi < 2 else 22) * zx, lh * 0.66))
                    while fs > 12 and font("ExtraBold", fs).getlength(bname) > pw - 26 * zx: fs -= 1
                    text(d, (xc, yb + lh / 2), bname, font("ExtraBold", fs), PED_TEXT[bi], ba, 0)
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
            box3d(im, ImageDraw.Draw(im, "RGBA"), mx0, mx1, top, mgy, tex, tint(dk, 0.88), tint(hi, 1.0), (mw * VIEW['dx'] * 1.06, mw * VIEW['dy'] * 1.1))
            d.line([(mx0, top), (mx1, top)], fill=wa((255, 255, 255), 200), width=max(1, int(2 * zx)))
            isz0 = max(40, 108 * zx); isz = int(min(isz0, mw - 8, ph - 12))
            if isz > 24 and PILLAR_ICON != "none":
                over.alpha_composite(ICONS[i].resize((isz, isz), Image.BILINEAR), (int(xc - isz / 2), int(top + min(14 * max(zx, .42), (ph - isz) / 2))))
            if mat == "diamond":
                sparkle.append((mx0, mx1, top, mgy))
        # value + photo + names above the pillar
        lab = zx > 0.6
        nsz = max(26, int(64 * zx))
        liftv = mw * min(0.0, VIEW["dy"]) * 1.1 if ph > 2 else 0.0
        y = top + liftv - nsz * (1.05 if lab else 0.75)
        val = worth * g
        vs = vlab if (g > 0.995 and vlab) else COUNT_FMT.format(val)
        va = 255 * ease(g / 0.15)
        if va > 1: text(d, (xc, y), vs, font("ExtraBold", nsz), (255, 255, 255), va, 4 if lab else 3)
        if lab:
            text(d, (xc, top + liftv - 22), SPEC.get("value_caption", ""), font("Bold", 20), (255, 215, 120), 230 * names_a * ease(g / 0.15), 2)
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
    ha = ease_io((t - 2.3) / 0.5) * (1 - ease_io((t - t_start(min(2, N - 1)) + 0.1) / 0.4))
    if ha > 0.01:
        d.rounded_rectangle([W / 2 - 300, 212, W / 2 + 300, 288], 38, fill=(20, 10, 2, int(205 * ha)), outline=(255, 205, 70, int(220 * ha)), width=2)
        text(d, (W / 2, 250), SPEC["header"], fit(SPEC["header"], 34, 560), (255, 255, 255), 255 * ha, 0)
    oa = ease_io((t - T_STEPS_END - 1.4) / 0.8)
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
    bl = int(VIEW.get("blur", 0.0))
    if bl > 3:   # horizontal motion blur for whip pans
        import numpy as _np
        arr = _np.asarray(im.convert("RGB"), dtype=_np.float32); acc = _np.zeros_like(arr); n_ = 8
        for k_ in range(n_):
            sft = int(bl * (k_ / (n_ - 1) - 0.5)); acc += _np.roll(arr, sft, axis=1)
        im = Image.fromarray((acc / n_).astype("uint8")).convert("RGBA")
    kk = VIEW.get("key", 0.0) * (1 - ok) if CAM_MODE in ("lowangle", "flyover") else 0.0
    if abs(kk) > 0.002:   # perspective tilt: + low angle (ground near, bigger), - looking down (tops near)
        if kk > 0: quad = (0, 0, kk * W, H, (1 - kk) * W, H, W, 0)
        else: quad = (-kk * W, 0, 0, H, W, H, (1 + kk) * W, 0)
        im = im.transform((W, H), Image.QUAD, quad, Image.BILINEAR)
    im.alpha_composite(LOGO, (LOGO_X, LOGO_Y))
    out = im.convert("RGB")
    fade = min(1, t / 0.35, (TOTAL - t) / 0.5)
    if fade < 1: out = Image.blend(Image.new("RGB", (W, H)), out, max(0, fade))
    return out

# ---------------- audio (numpy, 0 credits: reuses owned music in assets/music) ----------------
MUSIC = {"retro_bollywood": ("retro_bollywood.wav", 28.7), "future_bass": ("future_bass.wav", 30.8),
         "stadium_anthem": ("stadium_anthem.wav", 27.3), "stadium_anthem_alt": ("stadium_anthem_alt.wav", 27.3)}
def make_audio(path):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, sosfilt
    SR = 44100; NS = int(SR * TOTAL); rng = np.random.default_rng(7)
    def load(f): sr, x = wavfile.read(os.path.join(REPO, "assets/music", f)); return x.astype(np.float64) / 32768
    mf, hit = MUSIC[MUSIC_NAME]
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
    logo = Image.open(os.path.join(REPO, "assets/logo.png")).convert("RGBA").resize((143, 143), Image.LANCZOS); im.paste(logo, (754, 1379), logo)
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
    add_cta(out, out, y=SPEC.get("cta_y", 520))  # Like / Share / Follow reminder over the final overview
    make_cover(cover)
    for tt in (round(t_land(N // 2) + 0.4, 1), round(TOTAL - 1.0, 1)):
        frame(tt).save(os.path.join(WORK, f"check_{tt}.png"))
    print("OK", out, cover, "check frames in", WORK)
