"""Cut an illustrated icon sheet (cols x rows grid on a plain light background) into transparent square PNG icons.
Usage: [CIRCLE=1] python3 tools/cut_icon_sheet.py sheet.png 6 3 name1,name2,... [outdir=assets/icons]
Names are in reading order (left to right, top to bottom). Writes <outdir>/<name>.png (480x480 circle; CIRCLE=1 for scene tiles, otherwise objects are framed with their cream background)
and <outdir>/_contact_<first-name>.jpg for a quick visual check."""
import sys, os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage

src, cols, rows, names = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4].split(",")
out = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets/icons")
os.makedirs(out, exist_ok=True)
im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(float)
border = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
bg = np.median(border, 0)
dist = np.sqrt(((a - bg) ** 2).sum(2))
mask = dist > 22
mask = ndimage.binary_closing(mask, iterations=3); mask = ndimage.binary_fill_holes(mask); mask = ndimage.binary_opening(mask, iterations=2)
H, W = mask.shape; cw, ch = W / cols, H / rows
tiles = []
for k, name in enumerate(names):
    r, c = divmod(k, cols)
    x0, y0, x1, y1 = int(c * cw), int(r * ch), int((c + 1) * cw), int((r + 1) * ch)
    sub = mask[y0:y1, x0:x1].copy()
    lab, n = ndimage.label(sub)
    if n == 0: print("EMPTY cell", k, name); continue
    hh, ww = sub.shape; keep = np.zeros_like(sub)
    sizes = ndimage.sum(sub, lab, range(1, n + 1)); big = sizes.max()
    for i in range(1, n + 1):
        ys_, xs_ = np.where(lab == i)
        touches = xs_.min() <= 1 or xs_.max() >= ww - 2 or ys_.min() <= 1 or ys_.max() >= hh - 2
        if sizes[i - 1] > 0.04 * big and not (touches and sizes[i - 1] < 0.5 * big): keep |= lab == i
    ys, xs = np.where(keep)
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    circ = bool(os.environ.get("CIRCLE"))
    side = int(max(bx1 - bx0, by1 - by0) * (1.08 if circ else 1.32)) + 8
    cx, cy = x0 + (bx0 + bx1) / 2, y0 + (by0 + by1) / 2
    L, T = int(cx - side / 2), int(cy - side / 2)
    crop = im.crop((L, T, L + side, T + side))
    cm = Image.new("L", (side, side), 0); inset = 0.06 if circ else 0.01
    ImageDraw.Draw(cm).ellipse([side * inset, side * inset, side * (1 - inset), side * (1 - inset)], fill=255)
    alpha = cm.filter(ImageFilter.GaussianBlur(1.5))
    ic = crop.convert("RGBA"); ic.putalpha(alpha)
    ic = ic.resize((480, 480), Image.LANCZOS); ic.save(os.path.join(out, name + ".png")); tiles.append((name, ic))
sheet = Image.new("RGB", (cols * 200, rows * 230), (70, 50, 30)); d = ImageDraw.Draw(sheet)
for k, (name, ic) in enumerate(tiles):
    r, c = divmod(k, cols); t = ic.resize((180, 180)); sheet.paste(t, (c * 200 + 10, r * 230 + 10), t); d.text((c * 200 + 10, r * 230 + 198), name, fill=(255, 230, 160))
sheet.save(os.path.join(out, f"_contact_{names[0]}.jpg"), quality=85)
print("cut", len(tiles), "icons ->", out)
