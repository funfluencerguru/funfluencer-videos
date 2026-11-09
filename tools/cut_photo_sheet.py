"""Cut a real-photo sheet (photo tiles separated by white gaps, optional title label on top) into round badge PNGs.
Usage: [TOP=name,...] python3 tools/cut_photo_sheet.py sheet.png name1,name2,... [outdir=assets/icons]
Tiles are found from the white gaps, read left to right, top to bottom. Each tile gives a centred square
(slightly above centre for tall tiles), cut to a 480x480 circle. Also writes <outdir>/_contact_<first-name>.jpg."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

src, names = sys.argv[1], sys.argv[2].split(",")
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets/icons")
os.makedirs(out, exist_ok=True)
im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(int)
white = (a.min(2) > 235)

def runs(frac):
    """Index ranges where the line is mostly NOT white (= tiles)."""
    on = frac < 0.6; res = []; s = None
    for i, v in enumerate(list(on) + [False]):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s > 40: res.append((s, i))
            s = None
    return res

cols = runs(white.mean(0))
rows = [r for r in runs(white[:, cols[0][0]:cols[-1][1]].mean(1)) if r[1] - r[0] > 0.6 * max(b - a_ for a_, b in runs(white[:, cols[0][0]:cols[-1][1]].mean(1)))]
print("grid", len(cols), "x", len(rows))
tiles = []
for k, name in enumerate(names):
    r, c = divmod(k, len(cols))
    (x0, x1), (y0, y1) = cols[c], rows[r]
    x0, y0, x1, y1 = x0 + 3, y0 + 3, x1 - 3, y1 - 3
    w, h = x1 - x0, y1 - y0; side = min(w, h)
    cx = x0 + w / 2; cy = y0 + h * (0.45 if h > w * 1.2 else 0.5)
    if name in os.environ.get("TOP", "").split(","): cy = y0 + side / 2 + h * 0.08  # tall subject: keep the top in
    L = int(cx - side / 2); T = int(max(y0, min(y1 - side, cy - side / 2)))
    crop = im.crop((L, T, L + side, T + side)).resize((480, 480), Image.LANCZOS)
    m = Image.new("L", (480, 480), 0); ImageDraw.Draw(m).ellipse([6, 6, 474, 474], fill=255)
    ic = crop.convert("RGBA"); ic.putalpha(m.filter(ImageFilter.GaussianBlur(1.5)))
    ic.save(os.path.join(out, name + ".png")); tiles.append((name, ic))
nc = len(cols); nr = (len(tiles) + nc - 1) // nc
sheet = Image.new("RGB", (nc * 200, nr * 230), (70, 50, 30)); d = ImageDraw.Draw(sheet)
for k, (name, ic) in enumerate(tiles):
    r, c = divmod(k, nc); t = ic.resize((180, 180)); sheet.paste(t, (c * 200 + 10, r * 230 + 10), t); d.text((c * 200 + 10, r * 230 + 198), name, fill=(255, 230, 160))
sheet.save(os.path.join(out, f"_contact_{names[0]}.jpg"), quality=85)
print("cut", len(tiles), "badges ->", out)
