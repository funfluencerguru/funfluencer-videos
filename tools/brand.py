"""funfluencer brand finish: logo placement + "Like / Share / Follow" reminder tag.

Owner rules (set 2026-11-09), apply to EVERY reel:
  * Logo (assets/logo.png) bottom-right, 10% bigger than before and lifted up from the very bottom:
    its bottom edge sits LOGO_LIFT px above the bottom of the 1080x1920 frame.
  * A reminder tag "LIKE . SHARE . FOLLOW / SUBSCRIBE" pops in near the end of every reel.

Use from Python:
    from brand import logo_box, add_cta
    x, y, s = logo_box(base=104, right=36)     # size and position for the logo
    add_cta("in.mp4", "out.mp4", y=1320)       # burns the reminder tag into the last ~4 s

Or from the shell, for any finished 1080x1920 reel:
    python3 tools/brand.py add-cta in.mp4 out.mp4 [--y 1320] [--dur 4] [--start 12.5]
    python3 tools/brand.py preview /tmp/cta.png          # just the tag, to look at
Pick --y so the tag (110 px tall) covers nothing important in the last seconds and stays
between y 300 and the top of the logo. Needs Pillow + ffmpeg.
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LOGO_PATH = os.path.join(REPO, "assets", "logo.png")
LOGO_SCALE = 1.10      # 10% bigger than each format's old logo size
LOGO_LIFT = 130        # px between the logo's bottom edge and the bottom of the frame
CTA_H = 110


def logo_box(base, right=36):
    """Return (x, y, size) of the logo for a format whose old logo was `base` px."""
    s = int(round(base * LOGO_SCALE))
    return W - right - s, H - LOGO_LIFT - s, s


def _font(size):
    for f in ("assets/fonts/Inter-ExtraBold.otf", "assets/fonts/Inter-Bold.otf"):
        p = os.path.join(REPO, f)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _icon(kind, size, col):
    u = size / 100; im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == "like":       # heart
        d.ellipse([8 * u, 14 * u, 52 * u, 58 * u], fill=col); d.ellipse([48 * u, 14 * u, 92 * u, 58 * u], fill=col)
        d.polygon([(10 * u, 44 * u), (90 * u, 44 * u), (50 * u, 90 * u)], fill=col)
    elif kind == "share":    # paper plane
        d.polygon([(6 * u, 46 * u), (94 * u, 10 * u), (62 * u, 92 * u), (46 * u, 58 * u)], fill=col)
        d.line([(46 * u, 58 * u), (94 * u, 10 * u)], fill=(0, 0, 0, 0), width=max(2, int(6 * u)))
    elif kind == "bell":     # bell
        d.pieslice([20 * u, 10 * u, 80 * u, 70 * u], 180, 360, fill=col)
        d.polygon([(20 * u, 40 * u), (80 * u, 40 * u), (90 * u, 76 * u), (10 * u, 76 * u)], fill=col)
        d.ellipse([40 * u, 76 * u, 60 * u, 94 * u], fill=col); d.ellipse([44 * u, 2 * u, 56 * u, 14 * u], fill=col)
    return im


def cta_image(width=1000):
    """Transparent PNG of the reminder tag: dark rounded bar with 3 chips."""
    S = 2; w, h = width * S, CTA_H * S
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, w - 4, h - 4], h // 2, fill=(18, 14, 30, 235), outline=(255, 214, 80, 255), width=5 * S)
    chips = [("like", "LIKE", (255, 72, 96)), ("share", "SHARE", (60, 210, 140)), ("bell", "FOLLOW / SUBSCRIBE", (255, 206, 60))]
    fs = 38 * S; f = _font(fs); ic = 44 * S; gap_i = 12 * S
    widths = [ic + gap_i + d.textlength(t, font=f) for _, t, _ in chips]
    gap = (w - 60 * S - sum(widths)) / (len(chips) - 1)
    x = 30 * S
    for (k, t, col), cw in zip(chips, widths):
        im.alpha_composite(_icon(k, ic, col), (int(x), (h - ic) // 2))
        d.text((x + ic + gap_i, h / 2), t, font=f, fill=(255, 255, 255), anchor="lm")
        x += cw + gap
    return im.resize((width, CTA_H), Image.LANCZOS)


def _duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).decode().strip())


def add_cta(src, dst, y=1320, dur=4.0, start=None):
    """Burn the reminder tag into a finished 1080x1920 reel (re-encodes video, copies audio).
    The tag slides up + fades in at `start` (default: `dur` seconds before the end) and stays to the end."""
    total = _duration(src)
    st = max(0.0, total - dur) if start is None else start
    tmp = tempfile.mkdtemp(); png = os.path.join(tmp, "cta.png")
    img = cta_image(); img.save(png)
    x = (W - img.width) // 2
    fc = (f"[1:v]format=rgba,fade=t=in:st={st:.2f}:d=0.35:alpha=1[c];"
          f"[0:v][c]overlay=x={x}:y='{y}+max(0,{st + 0.35:.2f}-t)*160':shortest=1:eof_action=pass,format=yuv420p[v]")
    same = os.path.abspath(src) == os.path.abspath(dst)
    out = os.path.join(tmp, "out.mp4") if same else dst
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-loop", "1", "-framerate", "30", "-t", f"{total:.2f}", "-i", png,
                    "-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                    "-r", "30", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
    if same:
        os.replace(out, dst)
    return dst


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = a.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("add-cta"); c.add_argument("src"); c.add_argument("dst")
    c.add_argument("--y", type=int, default=1320); c.add_argument("--dur", type=float, default=4.0); c.add_argument("--start", type=float)
    p = sp.add_parser("preview"); p.add_argument("out")
    g = a.parse_args()
    if g.cmd == "add-cta":
        print(add_cta(g.src, g.dst, g.y, g.dur, g.start))
    else:
        cta_image().save(g.out); print(g.out)
