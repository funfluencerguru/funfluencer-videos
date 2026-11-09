#!/usr/bin/env python3
"""Weekly puzzle reel (1080x1920, 16s, one page only).

Usage: python3 tools/make_puzzle.py spec.json out.mp4
spec.json: {"sub": "blue hinglish line",
            "rows": ["{a} + {a} = 10", ...],      # {name} -> inline icon
            "last": "{b} + {a} × {c} = ?",    # last row, after dashed line
            "icons": {"a": "<svg ...>...</svg>"}} # optional inline SVGs (viewBox 0 0 100 100)
Logo: assets/logo.png embedded as base64. Static page; only the countdown number
changes (15..0, one second each). Audio: tick per second + 3-note chime at 0.
Run with a python that has numpy + playwright (CHROMIUM_PATH overrides browser).
"""
import base64, glob, json, os, subprocess, sys, tempfile, wave
# OWNER RULE 2026-11-09 (overrides older task instructions that say 190 px / 25 px from the bottom):
# logo 209 px, 130 px above the bottom, plus the Like/Share/Follow tag from tools/brand.py. Do not revert.
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100


def b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()


def icon(svg):
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()


def row_html(text, icons):
    out = text
    for k, svg in icons.items():
        out = out.replace('{%s}' % k, '<img class="ic" src="%s">' % icon(svg))
    return out.replace('×', '<span class="op">×</span>')


def page(spec, n, logo):
    icons = spec.get('icons', {})
    rows = ''.join('<div class="row">%s</div>' % row_html(r, icons) for r in spec['rows'])
    last = '<div class="row last">%s</div>' % row_html(spec['last'], icons)
    return f'''<html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;position:relative;overflow:hidden;font-family:"Comic Sans MS","Chalkboard SE","Segoe UI",Arial,sans-serif;
background-color:#fdf6e3;background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 71px,#bfdcf2 71px,#bfdcf2 74px)}}
.margin{{position:absolute;left:90px;top:0;bottom:0;width:4px;background:#f2a0b5}}
.head{{position:absolute;top:110px;left:0;right:0;text-align:center}}
.head span{{display:inline-block;background:#ffe14d;border:7px solid #111;border-radius:18px;box-shadow:12px 12px 0 #111;
padding:14px 44px;font-size:96px;font-weight:900;color:#111}}
.sub{{position:absolute;top:340px;left:60px;right:60px;text-align:center;font-size:48px;font-weight:800;color:#1b5fd1}}
.card{{position:absolute;top:470px;left:90px;right:90px;background:#fff;border:8px solid #111;border-radius:34px;
box-shadow:16px 16px 0 #111;padding:36px 30px}}
.row{{display:flex;align-items:center;justify-content:center;gap:14px;font-size:70px;font-weight:900;color:#111;height:112px;white-space:nowrap}}
.row.last{{border-top:6px dashed #888;margin-top:14px;padding-top:20px;height:138px;color:#d6246e}}
.ic{{width:92px;height:92px}}.op{{margin:0 4px}}
.cd{{position:absolute;top:1230px;left:50%;margin-left:-130px;width:260px;height:260px;border-radius:50%;background:#fff;border:20px solid #e5322d;
box-shadow:8px 8px 0 #111;display:flex;align-items:center;justify-content:center;font-size:130px;font-weight:900;color:#111}}
.cta{{position:absolute;top:1545px;left:0;right:230px;text-align:center;font-size:54px;white-space:nowrap;font-weight:900;color:#111}}
.cta span{{background:#fff;border:6px solid #111;border-radius:60px;padding:8px 36px;box-shadow:7px 7px 0 #111}}
.ai{{position:absolute;left:120px;bottom:40px;font-size:30px;font-weight:700;color:#777}}
.logo{{position:absolute;right:30px;bottom:130px;width:209px;height:209px}}
</style></head><body><div class="margin"></div>
<div class="head"><span>Solve karo! \U0001F9E0</span></div>
<div class="sub">{spec['sub']}</div>
<div class="card">{rows}{last}</div>
<div class="cd">{n}</div>
<div class="cta"><span>Answer comment karo! \U0001F447</span></div>
<div class="ai">AI-generated</div>
<img class="logo" src="data:image/png;base64,{logo}">
</body></html>'''


def audio(path, secs=16):
    t = np.arange(int(SR * secs)) / SR
    y = np.zeros_like(t)
    for s in range(15):  # ticks at 0..14
        i = int(s * SR)
        m = np.arange(int(0.06 * SR)) / SR
        y[i:i + len(m)] += 0.35 * np.sin(2 * np.pi * 1800 * m) * np.exp(-m * 70)
    for k, f in enumerate([523.25, 659.25, 783.99]):  # chime at 15s
        i = int((15 + k * 0.22) * SR)
        m = np.arange(min(int(0.6 * SR), len(y) - i)) / SR
        y[i:i + len(m)] += 0.4 * np.sin(2 * np.pi * f * m) * np.exp(-m * 5)
    y = np.clip(y, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype('<i2').tobytes())


def main(spec_path, out):
    spec = json.load(open(spec_path))
    logo = b64(os.path.join(ROOT, 'assets', 'logo.png'))
    tmp = tempfile.mkdtemp()
    exe = glob.glob('/opt/pw-browsers/chromium-*/chrome-linux*/chrome')
    exe = os.environ.get('CHROMIUM_PATH') or (exe[0] if exe else None)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        for i, n in enumerate(range(15, -1, -1)):
            pg.set_content(page(spec, n, logo))
            pg.screenshot(path=f'{tmp}/f{i:02d}.png')
        b.close()
    audio(f'{tmp}/a.wav')
    subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '1', '-i', f'{tmp}/f%02d.png',
                           '-i', f'{tmp}/a.wav', '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264',
                           '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', out])
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from brand import add_cta
    add_cta(out, out, y=spec.get('cta_y', 1080))  # Like / Share / Follow reminder, last 4 s
    print('frames in', tmp)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
