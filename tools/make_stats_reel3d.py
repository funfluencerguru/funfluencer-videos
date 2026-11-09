"""FunFluencer TRUE-3D stats reel (9:16): pillars stand in a diagonal row that recedes to the right (a staircase in depth),
info card printed on each pillar's FRONT FACE near the top, camera glides forward along the row at the height of the
current pillar's top, then pulls back and up to show all pillars. Same spec format as tools/make_stats_reel.py.
Usage:  python3 tools/make_stats_reel3d.py spec.json [--preview t1 t2 ...]"""
import sys, os, math, runpy, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = sys.argv[1]
PREVIEW = sys.argv[sys.argv.index("--preview") + 1:] if "--preview" in sys.argv else None
sys.argv = ["x", SPEC_PATH, "--lib"]
E = runpy.run_path(os.path.join(HERE, "make_stats_reel.py"), run_name="lib")   # reuse spec, themes, icons, audio, brand
SPEC, P, N, W, H, FPS = E["SPEC"], E["P"], E["N"], E["W"], E["H"], E["FPS"]
font, fit, text, ease, ease_io, ease_io5, lerp = E["font"], E["fit"], E["text"], E["ease"], E["ease_io"], E["ease_io5"], E["lerp"]
BADGES, MAT, MCOL, LOGO, LOGO_X, LOGO_Y = E["BADGES"], E["MAT"], E["MCOL"], E["LOGO"], E["LOGO_X"], E["LOGO_Y"]
COUNT_FMT = E["COUNT_FMT"]

# ---------------- world ----------------
PW, PD = 1.0, 1.0                     # pedestal width / depth (world units)
LAYOUT = SPEC.get("layout", "line")     # line = pillars side by side in one straight row (approved positions); diagonal = staircase in depth
PEDH = 1.05 if LAYOUT == "diagonal" else 260 / 240   # ivory pedestal height (same proportion as the approved 2D reel)
INS = 0.07                             # metal pillar inset on the pedestal
LABH = 1.9                             # world height reserved above a pillar for value + badge + names
if LAYOUT == "diagonal": HMIN, HMAX = 1.2, 9.0
else: HMIN, HMAX = 60 / 240, 1100 / 240          # exactly the approved 2D scale (floor 60, max 1100 on a 240-wide pillar)
VMAX = max(p[3] for p in P)
def hgt(i): return HMIN + (HMAX - HMIN) * P[i][3] / VMAX
def pos(i): return (i * 1.30, 0.0, i * 1.95) if LAYOUT == "diagonal" else (i * 330 / 240, 0.0, 0.0)   # line: approved 330/240 pitch
VIEW_DIR = np.array([0.0, 0.0, 1.0]) if LAYOUT == "diagonal" else np.array([0.62, 0.0, 0.78])     # line: look along the row at an angle so it recedes to the right
CARD_H = 1.25                          # card height on the front face (world units, card width = PW)

T_INTRO, STEP, GROW0, GROW = 2.2, 2.2, 0.15, 1.05
T_STEPS_END = T_INTRO + N * STEP
PULL, HOLD = 2.8, 3.4
TOTAL = T_STEPS_END + PULL + HOLD
def t_start(i): return T_INTRO + i * STEP
def t_land(i): return t_start(i) + GROW0 + GROW
def growth(i, t): return ease(max(0.0, min(1.0, (t - t_start(i) - GROW0) / GROW)))

# ---------------- camera ----------------
FOC = 2.45 * W   # longer lens (telephoto) like the reference: flatter depth, foreground pillars stay small
def look_basis(eye, target):
    f = np.array(target, float) - np.array(eye, float); f /= np.linalg.norm(f)
    r = np.cross(np.array([0, 1.0, 0]), f); r /= np.linalg.norm(r)
    u = np.cross(f, r)
    return np.array(eye, float), r, u, f
def project(cam, p):
    eye, r, u, f = cam; d = np.array(p, float) - eye
    z = d @ f
    if z < 0.05: return None
    return (W / 2 + FOC * (d @ r) / z, H * 0.46 - FOC * (d @ u) / z, z)

def cam_for(s, t):
    """camera centred on fractional pillar index s"""
    i0 = int(math.floor(max(0, min(N - 1, s)))); i1 = min(N - 1, i0 + 1); k = ease_io(max(0.0, min(1.0, s - i0)))
    p = [lerp(pos(i0)[j], pos(i1)[j], k) for j in range(3)]
    h0 = hgt(i0) * growth(i0, t); h1 = max(h0, hgt(i1) * growth(i1, t))   # never dip toward an unborn pillar
    top = PEDH + max(lerp(h0, h1, k), 0.3)
    if LAYOUT == "diagonal":
        eye = (p[0] - 1.7, top + 1.55, p[2] - 10.5)
        tgt = (p[0] + 0.55, top + 0.15, p[2] + 0.5)
    else:
        c = np.array([p[0] + 0.5, 0, p[2] + 0.5]); D = 11.0
        eye = (c[0] - VIEW_DIR[0] * D - 0.6, top + 1.45, c[2] - VIEW_DIR[2] * D)
        tgt = (c[0] + 0.35, top + 0.20, c[2])
    return eye, tgt

def camera(t):
    if t < T_INTRO:  # fly in from far left / low, landing on pillar 0
        k = ease_io5(t / T_INTRO)
        e1, g1 = cam_for(0, T_INTRO)
        e0 = (e1[0] - 6.0, e1[1] + 2.5, e1[2] - 6.0)
        eye = tuple(lerp(e0[j], e1[j], k) for j in range(3)); tgt = tuple(lerp(g1[j] + (2.0 if j == 0 else 0), g1[j], k) for j in range(3))
        return look_basis(eye, tgt)
    if t < T_STEPS_END:
        s = (t - T_INTRO - 0.9) / STEP
        eye, tgt = cam_for(max(0.0, s), t)
        return look_basis(eye, tgt)
    k = ease_io5((t - T_STEPS_END) / PULL)
    e1, g1 = cam_for(N - 1, t)
    eo, go = OVERVIEW
    eye = tuple(lerp(e1[j], eo[j], k) for j in range(3)); tgt = tuple(lerp(g1[j], go[j], k) for j in range(3))
    if t > T_STEPS_END + PULL:  # gentle drift on hold
        h = (t - T_STEPS_END - PULL) / HOLD; eye = (eye[0] - 0.3 * h, eye[1], eye[2] - 0.3 * h)
    return look_basis(eye, tgt)

def fit_overview():
    """look at the whole row from the front-right at ~45 degrees to it, as close as possible while everything fits"""
    cx = (pos(0)[0] + pos(N - 1)[0]) / 2 + 0.5; cz = (pos(0)[2] + pos(N - 1)[2]) / 2 + 0.5
    v = np.array([-0.20, 0.0, 0.98]) if LAYOUT == "diagonal" else np.array([0.50, 0.0, 0.87]); v /= np.linalg.norm(v)
    best = None
    for back in np.arange(6, 80, 0.5):
      for dyt in np.arange(0.0, 9.0, 0.5):   # aim higher -> content moves down into the free band 670..1470
        eye = (cx - v[0] * back, HMAX * 0.62 + back * 0.10, cz - v[2] * back)
        tgt = (cx, HMAX * 0.50 + dyt, cz)
        cam = look_basis(eye, tgt); ok = True
        for i in range(N):
            x, y, z = pos(i)
            for c in [(x, 0, z), (x + PW, 0, z), (x + 0.5, PEDH + hgt(i) + LABH * 0.55, z), (x + PW, 0, z + PD)]:
                q = project(cam, c)
                if q is None or not (50 < q[0] < W - 50 and 670 < q[1] < 1470): ok = False; break
            if not ok: break
        if ok: return eye, tgt
    return eye, tgt
OVERVIEW = fit_overview()

# ---------------- textures ----------------
def persp_coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def warp(canvas, tex, quad):
    """paste RGBA texture onto screen quad (tl, tr, br, bl)"""
    xs = [q[0] for q in quad]; ys = [q[1] for q in quad]
    x0, y0, x1, y1 = int(max(0, min(xs))), int(max(0, min(ys))), int(min(W, max(xs)) + 1), int(min(H, max(ys)) + 1)
    if x1 - x0 < 2 or y1 - y0 < 2: return
    tw, th = tex.size
    dst = [(q[0] - x0, q[1] - y0) for q in quad]
    co = persp_coeffs(dst, [(0, 0), (tw, 0), (tw, th), (0, th)])
    out = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, co, Image.BILINEAR)
    canvas.alpha_composite(out, (x0, y0))

CW, CHT = 600, 750
def card_texture(i, g):
    small, big, grp, worth, slug, ic, lines, vname, vlab = P[i]
    base = MCOL[MAT[i]][1]
    im = Image.new("RGBA", (CW, CHT), base + (255,)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([22, 22, CW - 22, CHT - 22], 26, fill=(255, 253, 248, 255), outline=MCOL[MAT[i]][4] + (255,), width=6)
    b = BADGES[i].resize((250, 250), Image.LANCZOS); im.alpha_composite(b, (CW // 2 - 125, 44))
    d.text((CW / 2, 322), big, font=fit(big, 52, CW - 80), fill=(40, 26, 12), anchor="mm")
    if small or grp:
        sub = (small + " · " + grp).strip(" ·"); d.text((CW / 2, 368), sub, font=fit(sub, 26, CW - 80, "Bold"), fill=(150, 90, 10), anchor="mm")
    val = worth * g
    vs = vlab if (g > 0.995 and vlab) else COUNT_FMT.format(val)
    d.text((CW / 2, 448), vs, font=fit(vs, 96, CW - 70), fill=(200, 120, 0), anchor="mm", stroke_width=2, stroke_fill=(120, 60, 0))
    cap = SPEC.get("value_caption", "")
    if cap:
        d.rounded_rectangle([CW / 2 - 150, 508, CW / 2 + 150, 548], 10, fill=(40, 26, 12)); d.text((CW / 2, 528), cap, font=fit(cap, 24, 280, "Bold"), fill=(255, 230, 160), anchor="mm")
    cols = [(110, 58, 12), (0, 98, 140), (176, 110, 0)]
    for k, ln in enumerate([l for l in lines if l][:3]):
        d.text((CW / 2, 590 + k * 46), ln, font=fit(ln, 34 if k < 2 else 26, CW - 80), fill=cols[k], anchor="mm")
    return im

STATIC_CARDS = {}
def get_card(i, g):
    if g >= 0.999:
        if i not in STATIC_CARDS: STATIC_CARDS[i] = card_texture(i, 1.0)
        return STATIC_CARDS[i]
    return card_texture(i, g)

# background: theme backdrop (photo or drawn) used as a distant panorama
BG = E["bg_big"] if "bg_big" in E else Image.open(E["BG_PATH"]).convert("RGB")
def backdrop(cam):
    eye, r, u, f = cam
    yaw = math.atan2(f[0], f[2]); pitch = math.asin(max(-1, min(1, f[1])))
    sc = (H * 1.18) / BG.height
    bw = int(BG.width * sc); bh = int(H * 1.18)
    big = BG.resize((bw, bh), Image.BILINEAR) if not hasattr(backdrop, "c") else backdrop.c
    backdrop.c = big
    x = int((bw - W) / 2 + yaw * 900 + eye[0] * 25); x = max(0, min(bw - W, x))
    y = int((bh - H) / 2 - pitch * 900); y = max(0, min(bh - H, y))
    return big.crop((x, y, x + W, y + H)).convert("RGBA")

def floor(im, cam):
    d = ImageDraw.Draw(im, "RGBA")
    eye = cam[0]
    # soft floor tint below the horizon, then a perspective grid
    gx0, gx1 = -12, pos(N - 1)[0] + 14; gz0, gz1 = -12, pos(N - 1)[2] + 20
    corners = [project(cam, (gx0, 0, gz1)), project(cam, (gx1, 0, gz1))]
    hy = min([c[1] for c in corners if c] + [H]) if any(corners) else H * 0.46
    for k in range(40):
        y = hy + (H - hy) * k / 40
        d.rectangle([0, y, W, y + (H - hy) / 40 + 1], fill=(20, 16, 12, int(40 + 120 * k / 40)))
    for gx in np.arange(math.floor(gx0), gx1, 1.0):
        a = project(cam, (gx, 0, max(gz0, eye[2] + 0.6))); b = project(cam, (gx, 0, gz1))
        if a and b: d.line([a[:2], b[:2]], fill=(255, 235, 200, 40), width=2)
    for gz in np.arange(math.ceil(max(gz0, eye[2] + 0.6)), gz1, 1.0):
        a = project(cam, (gx0, 0, gz)); b = project(cam, (gx1, 0, gz))
        if a and b: d.line([a[:2], b[:2]], fill=(255, 235, 200, 40), width=2)

def tint(c, f): return tuple(int(max(0, min(255, v * f))) for v in c)
ICONS3 = E["ICONS"]
PED_TOP, PED_BOT = (34, 21, 13), (14, 8, 5)                   # very dark chocolate pedestal
PED_SIDE, PED_CAP = (9, 5, 3), (96, 66, 30)
PED_TEXT = [(255, 246, 225), (190, 244, 255), (255, 226, 120)]  # very light, bright text: ivory, ice blue, bright gold
VNAMES = [E["vlabel"](p[7], (255, 238, 170, 255)) for p in P]

def ped_texture(i, overview=False):
    """ivory pedestal front: rank + 3 text lines (or the vertical name in the overview), dark readable text"""
    tw, th = 480, int(480 * PEDH / PW)
    im = Image.new("RGBA", (tw, th)); d = ImageDraw.Draw(im)
    for yy in range(th):
        k = yy / th; d.line([(0, yy), (tw, yy)], fill=tuple(int(a + (b - a) * k) for a, b in zip(PED_TOP, PED_BOT)) + (255,))
    d.rectangle([0, 0, tw, 12], fill=(232, 180, 70, 255)); d.rectangle([16, 28, tw - 16, th - 18], outline=(200, 150, 60, 255), width=4)
    d.text((tw / 2, 82), f"#{N - i}", font=font("ExtraBold", 72), fill=(255, 232, 130), anchor="mm")
    if overview:
        vn = VNAMES[i]; sc_ = min((th - 150) / vn.height, (tw - 40) / vn.width, 2.2)
        vv = vn.resize((max(1, int(vn.width * sc_)), max(1, int(vn.height * sc_))), Image.LANCZOS)
        im.alpha_composite(vv, (int(tw / 2 - vv.width / 2), 130))
    else:
        lines = [l for l in P[i][6] if l][:3]
        for k, ln in enumerate(lines):
            f = fit(ln, 54 if k < 2 else 38, tw - 50); d.text((tw / 2, 170 + k * 78), ln, font=f, fill=PED_TEXT[k], anchor="mm")
    return im
PED_TEX = [ped_texture(i) for i in range(N)]; PED_TEX_O = [ped_texture(i, True) for i in range(N)]

def rot(px, pz, a, c):
    dx, dz = px - c[0], pz - c[1]
    return (c[0] + dx * math.cos(a) - dz * math.sin(a), c[1] + dx * math.sin(a) + dz * math.cos(a))

def box(im, cam, x0, x1, y0, y1, z0, z1, front_col, side_col, top_col, front_tex=None, ang=0.0, piv=None):
    """3D block rotated by ang around the vertical axis through piv=(x,z); visible faces drawn far to near, front face textured"""
    piv = piv or ((x0 + x1) / 2, (z0 + z1) / 2)
    def P3(x, y, z):
        rx, rz = rot(x, z, ang, piv); return (rx, y, rz)
    W3 = {"fbl": P3(x0, y0, z0), "fbr": P3(x1, y0, z0), "ftl": P3(x0, y1, z0), "ftr": P3(x1, y1, z0),
          "bbl": P3(x0, y0, z1), "bbr": P3(x1, y0, z1), "btl": P3(x0, y1, z1), "btr": P3(x1, y1, z1)}
    pts = {}
    for nm, c in W3.items():
        q = project(cam, c)
        if q is None: return False
        pts[nm] = q[:2]
    eye = cam[0]; d = ImageDraw.Draw(im, "RGBA")
    faces = {"front": ["ftl", "ftr", "fbr", "fbl"], "right": ["ftr", "btr", "bbr", "fbr"], "left": ["btl", "ftl", "fbl", "bbl"], "back": ["btr", "btl", "bbl", "bbr"]}
    vis = []
    for nm, ks in faces.items():
        c3 = np.mean([W3[k] for k in ks], axis=0)
        a3, b3, c_ = np.array(W3[ks[0]]), np.array(W3[ks[1]]), np.array(W3[ks[2]])
        n = np.cross(b3 - a3, c_ - b3)
        if n @ (np.array(eye) - c3) > 0: vis.append((np.linalg.norm(np.array(eye) - c3), nm, ks))
    for _, nm, ks in sorted(vis, reverse=True):
        if nm == "front":
            if front_tex is not None: warp(im, front_tex, [pts[k] for k in ks])
            else: d.polygon([pts[k] for k in ks], fill=front_col + (255,))
        else:
            d.polygon([pts[k] for k in ks], fill=(side_col if nm != "left" else tint(side_col, 1.05)) + (255,))
    if eye[1] > y1: d.polygon([pts["ftl"], pts["ftr"], pts["btr"], pts["btl"]], fill=top_col + (255,))
    pts["_P3"] = P3
    return pts

METAL_TEX = {}
def metal_front(mat, wpx, hpx):
    key = (mat, wpx // 8, hpx // 16)
    if key not in METAL_TEX:
        dk, base, hi = MCOL[mat][0], MCOL[mat][1], MCOL[mat][2]
        xs = np.linspace(0, 1, max(2, wpx))
        prof = 0.5 + 0.5 * np.cos((xs - 0.32) * math.pi * 1.6)      # soft vertical highlight band
        row = np.array(base)[None, :] * (1 - 0.25 * prof[:, None]) + np.array(hi)[None, :] * (0.25 * prof[:, None])
        arr = np.repeat(row[None, :, :], max(2, hpx), axis=0).clip(0, 255).astype("uint8")
        METAL_TEX[key] = Image.fromarray(arr, "RGB").convert("RGBA")
    return METAL_TEX[key]

FACE_VIEWER = SPEC.get("face_viewer", LAYOUT == "line")
TURN = -math.atan2(VIEW_DIR[0], VIEW_DIR[2])      # angle that makes a pillar's front face look at the camera
def turn(i, t):
    if not FACE_VIEWER: return 0.0
    # grows in the row like normal; when the NEXT pillar starts growing it turns to face the viewer and stays that way
    start = t_start(i + 1) if i < N - 1 else T_STEPS_END - 0.3
    return TURN * ease_io((t - start) / 0.8)

def ring_orbit(im, cx, cy, r, w, ang, col, alpha=1.0):
    """animated outer ring: a bright comet-like arc circles the badge, led by a shiny glowing dot"""
    if r < 6 or alpha <= 0.02: return
    alpha = min(1.0, alpha)
    pad = int(w * 5 + 8); size = int(2 * (r + pad))
    lay = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    c0 = size / 2
    d.ellipse([c0 - r, c0 - r, c0 + r, c0 + r], outline=col + (int(120 * alpha),), width=max(1, int(w * 0.45)))
    seg = 60; span = math.radians(220)
    for pass_w, pass_a in ((w * 2.4, 0.30), (w, 1.0)):          # soft glow pass, then the bright core
        for k in range(seg):
            f = (k + 1) / seg
            a0 = ang - span * (1 - k / seg); a1 = ang - span * (1 - f)
            p0 = (c0 + r * math.cos(a0), c0 + r * math.sin(a0)); p1 = (c0 + r * math.cos(a1), c0 + r * math.sin(a1))
            cc = tuple(int(c + (255 - c) * f * 0.7) for c in col)
            d.line([p0, p1], fill=cc + (int(255 * alpha * pass_a * (0.15 + 0.85 * f ** 1.3)),), width=max(1, int(pass_w)))
    hx, hy = c0 + r * math.cos(ang), c0 + r * math.sin(ang)
    for gr, ga in ((w * 1.6, 70), (w * 1.0, 160), (w * 0.6, 255)):   # small shiny head dot
        d.ellipse([hx - gr, hy - gr, hx + gr, hy + gr], fill=(255, 250, 225, int(ga * alpha)))
    im.alpha_composite(lay, (int(cx - c0), int(cy - c0)))

def draw_pillar(im, cam, i, t, overview_k):
    g = growth(i, t)
    if t < t_start(i) - 0.05: return
    x, _, z = pos(i); h = max(0.02, hgt(i) * g)
    eye = cam[0]; ang = turn(i, t); piv = (x + PW / 2, z + PD / 2)
    # ground shadow
    sh = [project(cam, (lambda r: (r[0], 0, r[1]))(rot(px, pz, ang, piv))) for px, pz in [(x - 0.15, z - 0.1), (x + PW + 0.25, z - 0.1), (x + PW + 0.35, z + PD + 0.2), (x - 0.05, z + PD + 0.2)]]
    if all(sh): ImageDraw.Draw(im, "RGBA").polygon([q[:2] for q in sh], fill=(0, 0, 0, 110))
    # pedestal (ivory) with text
    ptex = PED_TEX_O[i] if overview_k > 0.5 else PED_TEX[i]
    if not box(im, cam, x, x + PW, 0, PEDH, z, z + PD, None, PED_SIDE, PED_CAP, front_tex=ptex, ang=ang, piv=piv): return
    # metal pillar (lightest pastel)
    mat = MAT[i]; dk, base, hi = MCOL[mat][0], MCOL[mat][1], MCOL[mat][2]
    x0, x1, z0, z1 = x + INS, x + PW - INS, z + INS, z + PD - INS
    def RP(px, py, pz):
        r = rot(px, pz, ang, piv); return project(cam, (r[0], py, r[1]))
    ql = RP(x0, PEDH, z0); qr = RP(x1, PEDH, z0); qt = RP(x0, PEDH + h, z0)
    if not (ql and qr and qt): return
    wpx = int(max(4, abs(qr[0] - ql[0]))); hpx = int(max(4, abs(ql[1] - qt[1])))
    pts = box(im, cam, x0, x1, PEDH, PEDH + h, z0, z1, None, tint(dk, 0.88), hi, front_tex=metal_front(mat, min(wpx, 600), min(hpx, 1600)), ang=ang, piv=piv)
    if not pts: return
    d = ImageDraw.Draw(im, "RGBA"); d.line([pts["ftl"], pts["ftr"]], fill=(255, 255, 255, 220), width=3)
    # coin icon near the top of the metal face
    isz = min(0.62, h * 0.8)
    if isz > 0.12 and E["PILLAR_ICON"] != "none":
        cxw = (x0 + x1) / 2; ytop = PEDH + h - 0.12
        q = [RP(cxw - isz / 2, ytop, z0 - 0.002), RP(cxw + isz / 2, ytop, z0 - 0.002),
             RP(cxw + isz / 2, ytop - isz, z0 - 0.002), RP(cxw - isz / 2, ytop - isz, z0 - 0.002)]
        if all(q): warp(im, ICONS3[i], [p[:2] for p in q])
    if mat == "diamond":
        for k in range(10):
            a = (t * 1.7 + k * 0.37) % 1.0; yy = lerp(pts["fbl"][1], pts["ftl"][1], (k * 0.137) % 1); xx = lerp(pts["ftl"][0], pts["ftr"][0], (k * 0.61) % 1)
            r = 4 + 6 * math.sin(math.pi * a); d.line([(xx - r, yy), (xx + r, yy)], fill=(255, 255, 255, 200), width=2); d.line([(xx, yy - r), (xx, yy + r)], fill=(255, 255, 255, 200), width=2)
    # billboard labels above the pillar (value + round badge + names), same design as our approved 2D reels
    top = project(cam, (x + PW / 2, PEDH + h, z))
    if not top: return
    if top[2] < 2.5: return            # pillar right at the lens: no floating labels
    sc = min(2.2, (FOC * PW / top[2]) / 240.0)
    small, big, grp, worth, slug, ic, lines, vname, vlab = P[i]
    lab = sc > 0.55
    nsz = max(18, int(64 * sc)); yv = top[1] - nsz * (1.0 if lab else 0.75) - 8 * sc
    val = worth * g; vs = vlab if (g > 0.995 and vlab) else COUNT_FMT.format(val)
    va = 255 * ease(g / 0.15)
    if va > 1: text(d, (top[0], yv), vs, font("ExtraBold", nsz), (255, 255, 255), va, 4 if lab else 2)
    if lab and SPEC.get("value_caption"):
        text(d, (top[0], top[1] - 18 * sc), SPEC["value_caption"], font("Bold", max(12, int(20 * sc))), (255, 215, 120), 230 * ease(g / 0.15), 2)
    b = E["back"]((t - t_start(i) - 0.1) / 0.6)
    dia0 = max(40, int(200 * sc)); dia = dia0 * b
    yb = yv - nsz * 0.7
    if dia > 4:
        bx, by = int(top[0] - dia / 2), int(yb - dia0 / 2 - dia / 2 - 6)
        im.alpha_composite(BADGES[i].resize((int(dia), int(dia)), Image.BILINEAR), (bx, by))
        ring_orbit(im, top[0], by + dia / 2, dia / 2 + max(5, 12 * sc), max(3, 7 * sc), t * 4.2 + i * 0.9, (255, 200, 70), b)
    if lab and overview_k < 0.5:
        la = 255 * ease((t - t_start(i) - 0.2) / 0.5) * (1 - overview_k * 2)
        yn = yb - dia0 - 18
        gc = MCOL[MAT[i]][4]
        text(d, (top[0], yn - 8 * sc), grp, font("ExtraBold", max(12, int(22 * sc))), gc, la, 2)
        text(d, (top[0], yn - 46 * sc), big, font("ExtraBold", max(14, int((44 if len(big) < 9 else 36) * sc))), (255, 255, 255), la, 3)
        if small: text(d, (top[0], yn - 82 * sc), small, font("Medium", max(12, int(26 * sc))), (240, 230, 210), la, 2)

def frame(t):
    cam = camera(t)
    im = backdrop(cam)
    ok_ = ease_io((t - T_STEPS_END) / PULL) if t > T_STEPS_END else 0.0
    order = sorted(range(N), key=lambda i: -np.linalg.norm(np.array(pos(i)) + [0.5, 0.5, 0.5] - cam[0]))
    for i in order: draw_pillar(im, cam, i, t, ok_)
    d = ImageDraw.Draw(im, "RGBA")
    # intro title
    if t < T_INTRO + 0.6:
        a = 255 * (1 - ease_io((t - T_INTRO + 0.2) / 0.8)) * ease_io(t / 0.4)
        it = SPEC["intro"]
        text(d, (W / 2, 470), it[0], fit(it[0], 110, 980), (255, 214, 100), a, 6)
        text(d, (W / 2, 590), it[1], fit(it[1], 84, 980), (255, 255, 255), a, 6)
        text(d, (W / 2, 676), it[2], fit(it[2], 32, 980, "SemiBold"), (236, 222, 196), a, 3)
    # header pill during the race
    ha = ease_io((t - T_INTRO + 0.2) / 0.5) * (1 - ease_io((t - T_STEPS_END) / 0.5))
    if ha > 0.01:
        hd = SPEC["header"]; f = fit(hd, 34, 560); w2 = f.getlength(hd) / 2 + 34
        d.rounded_rectangle([W / 2 - w2, 212, W / 2 + w2, 288], 38, fill=(20, 10, 2, int(200 * ha)), outline=(255, 214, 100, int(255 * ha)), width=2)
        text(d, (W / 2, 250), hd, f, (255, 240, 200), 255 * ha, 0)
    # outro
    if t > T_STEPS_END + 0.8:
        oa = ease_io((t - T_STEPS_END - 0.8) / 0.8)
        o = SPEC["outro"]
        text(d, (W / 2, 290), o[0], fit(o[0], 84, 1000), (255, 255, 255), 255 * oa, 4)
        text(d, (W / 2, 368), o[1], fit(o[1], 42, 1000), (255, 214, 100), 255 * oa, 3)
        text(d, (W / 2, 446), SPEC["question"], fit(SPEC["question"], 44, 1000), (150, 230, 255), 255 * oa, 4)
    if t > T_STEPS_END + PULL - 0.4:
        ca = ease_io((t - T_STEPS_END - PULL + 0.4) / 0.6)
        d.rounded_rectangle([60, 1500, W - 60, 1598], 20, fill=(20, 10, 2, int(232 * ca)), outline=(170, 230, 255, int(255 * ca)), width=2)
        tw = SPEC["twist"]
        text(d, (W / 2, 1532), tw[0], fit(tw[0], 40, 920), (255, 255, 255), 255 * ca, 0)
        text(d, (W / 2, 1574), tw[1], fit(tw[1], 25, 920, "Medium"), (236, 222, 196), 255 * ca, 0)
        text(d, (W / 2, 1626), SPEC["sources"], fit(SPEC["sources"], 19, 1000, "Medium"), (200, 190, 170), 255 * ca, 0)
    im.alpha_composite(LOGO, (LOGO_X, LOGO_Y))
    out = im.convert("RGB")
    fade = min(1, t / 0.3, (TOTAL - t) / 0.5)
    if fade < 1: out = Image.blend(Image.new("RGB", (W, H)), out, max(0, fade))
    return out

# re-time the audio engine to this timeline (its functions read these names from their globals)
G_ = E["make_audio"].__globals__   # runpy returns a copy; patch the real module globals
G_["t_land"], G_["t_start"], G_["TOTAL"], G_["T_STEPS_END"] = t_land, t_start, TOTAL, T_STEPS_END

if __name__ == "__main__":
    WORK = SPEC.get("workdir", "/tmp/statsreel3d"); os.makedirs(WORK, exist_ok=True)
    if PREVIEW:
        for tt in PREVIEW:
            p = os.path.join(WORK, f"frame3d_{tt}.png"); frame(float(tt)).save(p); print(p)
        sys.exit(0)
    out, cover = SPEC["out"], SPEC["cover_out"]
    print("TOTAL", round(TOTAL, 2), "s, items", N)
    silent = os.path.join(WORK, "silent3d.mp4"); wav = os.path.join(WORK, "mix3d.wav")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent], stdin=subprocess.PIPE)
    for k in range(int(TOTAL * FPS)): ff.stdin.write(frame(k / FPS).tobytes())
    ff.stdin.close(); assert ff.wait() == 0
    E["make_audio"](wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "volume=-1.5dB",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    E["add_cta"](out, out, y=SPEC.get("cta_y", 520), width=SPEC.get("cta_width", 1000), x=SPEC.get("cta_x"))
    E["make_cover"](cover)
    print("OK", out, cover)
