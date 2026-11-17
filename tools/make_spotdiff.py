#!/usr/bin/env python3
"""Weekly "Spot the Difference" reel (1080x1920, 18 s, H.264/AAC, 30 fps).

Usage: python3 tools/make_spotdiff.py --scene-module shaadi_stage --date 2026-11-17 --slug shaadi-stage [--outdir videos]
       [--sub "Sirf 1% log saare dhoondh paate hain!"] [--check-only]

A scene module lives in tools/spotdiff_scenes/<name>.py and defines:
    SCENE = "Shaadi stage"
    DIFFS = {"key": "Hinglish answer line", ...}     # exactly 5 keys
    def draw(changes: set) -> str                    # SVG, viewBox 0 0 500 900
Picture A = draw(set()), picture B = draw(all keys). The script renders both, then VERIFIES by pixels that
each change alone alters the picture and that B differs from A only where the 5 changes are (no accidental diffs).
Outputs (in --outdir): <date>-spotdiff-<slug>.mp4, plus PNGs in WORK dir (A.png, B.png, main.png, end.png, diffmap.png).
Timeline: 0-2 s title card, 2-14 s side-by-side with countdown 12..0 + ticks, 14-18 s end card. Answers are NOT shown.
Brand finish (owner rule 2026-11-09): logo assets/logo.png 209 px at logo_box(190, 30) and the Like/Share/Follow
tag (tools/brand.py add_cta) for the last 4 s, placed on the end card (cta_y 1300) so it hides nothing.
Needs python3, numpy, Pillow, playwright (chromium; CHROMIUM_PATH overrides), ffmpeg.
"""
import argparse, base64, glob, importlib, json, os, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
from brand import logo_box, add_cta  # noqa: E402

SR = 44100
TITLE, COUNT, END = 2, 12, 4
CTA_Y = 1300

CSS = '''*{box-sizing:border-box;margin:0}
body{width:1080px;height:1920px;position:relative;overflow:hidden;font-family:"Comic Sans MS","Segoe UI",Arial,"Noto Color Emoji",sans-serif;
background-color:#fdf6e3;background-image:repeating-linear-gradient(to bottom,transparent 0,transparent 71px,#bfdcf2 71px,#bfdcf2 74px)}
.margin{position:absolute;left:90px;top:0;bottom:0;width:4px;background:#f2a0b5}
.head{position:absolute;top:70px;left:0;right:0;text-align:center}
.head span{display:inline-block;background:#ffe14d;border:7px solid #111;border-radius:18px;box-shadow:10px 10px 0 #111;
padding:10px 40px;font-size:84px;font-weight:900;color:#111}
.sub{position:absolute;top:255px;left:40px;right:40px;text-align:center;font-size:46px;font-weight:800;color:#1b5fd1}
.pic{position:absolute;top:350px;width:500px;height:900px;border:9px solid #111;border-radius:30px;overflow:hidden;background:#fff;
box-shadow:8px 8px 0 #111}
.pic img{width:100%;height:100%;display:block}
.pa{left:27px}.pb{left:553px}
.badge{position:absolute;top:-6px;width:84px;height:84px;border-radius:50%;background:#111;color:#fff;font-size:54px;font-weight:900;
display:flex;align-items:center;justify-content:center;border:5px solid #fff}
.ba{left:14px;top:336px}.bb{left:540px;top:336px}
.cd{position:absolute;top:1300px;left:300px;width:230px;height:230px;border-radius:50%;background:#fff;border:20px solid #e5322d;
box-shadow:8px 8px 0 #111;display:flex;align-items:center;justify-content:center;font-size:118px;font-weight:900;color:#111}
.cta{position:absolute;top:1580px;left:30px;width:770px;text-align:center;font-size:44px;white-space:nowrap;font-weight:900;color:#111}
.cta span{background:#fff;border:6px solid #111;border-radius:60px;padding:8px 30px;box-shadow:7px 7px 0 #111}
.card{position:absolute;left:90px;right:90px;background:#fff;border:9px solid #111;border-radius:40px;box-shadow:16px 16px 0 #111;
text-align:center;font-weight:900;color:#111}
.ai{position:absolute;left:120px;bottom:40px;font-size:30px;font-weight:700;color:#777}
.logo{position:absolute}
'''


def b64(data):
    return base64.b64encode(data).decode()


def page(body, logo):
    x, y, s = logo_box(190, 30)
    return (f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="margin"></div>{body}'
            f'<div class="ai">AI-generated</div>'
            f'<img class="logo" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px" src="data:image/png;base64,{logo}">'
            '</body></html>')


def title_body(scene):
    return (f'<div class="card" style="top:430px;padding:70px 40px">'
            f'<div style="font-size:72px;background:#ffe14d;display:inline-block;padding:6px 26px;border-radius:14px">Spot the Difference</div>'
            f'<div style="font-size:110px;margin-top:50px;line-height:1.1">5 differences<br>dhoondo! 👀</div>'
            f'<div style="font-size:56px;margin-top:50px;color:#d6246e">Sirf 1% log<br>kar paate hain!</div>'
            f'<div style="font-size:44px;margin-top:40px;color:#1b5fd1">Scene: {scene}</div></div>')


def main_body(a_uri, b_uri, sub, n):
    return (f'<div class="head"><span>Find 5 differences 👀</span></div><div class="sub">{sub}</div>'
            f'<div class="pic pa"><img src="{a_uri}"></div><div class="pic pb"><img src="{b_uri}"></div>'
            f'<div class="badge ba">A</div><div class="badge bb">B</div>'
            f'<div class="cd">{n}</div><div class="cta"><span>Kitne mile? Comment karo! 👇</span></div>')


def end_body():
    return ('<div class="card" style="top:380px;padding:80px 40px">'
            '<div style="font-size:120px;line-height:1.1">Kitne<br>mile? 🤔</div>'
            '<div style="font-size:76px;margin-top:50px;line-height:1.2">Comment karo! 👇</div>'
            '<div style="font-size:56px;margin-top:50px;color:#d6246e;background:#ffe14d;display:inline-block;padding:10px 28px;border-radius:16px">'
            'Answers first<br>comment mein ✅</div></div>')


def audio(path, total):
    t = np.zeros(int(SR * total))
    m = np.arange(int(0.05 * SR)) / SR
    for s in range(COUNT + 1):  # light tick each second of the countdown
        i = int((TITLE + s) * SR)
        f = 1500 if s % 2 == 0 else 1200
        t[i:i + len(m)] += 0.3 * np.sin(2 * np.pi * f * m) * np.exp(-m * 80)
    for k, f in enumerate([523.25, 659.25, 783.99, 1046.5]):  # small chime on the end card
        i = int((TITLE + COUNT + k * 0.15) * SR)
        mm = np.arange(int(0.7 * SR)) / SR
        t[i:i + len(mm)] += 0.25 * np.sin(2 * np.pi * f * mm) * np.exp(-mm * 5)
    t = np.clip(t, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((t * 32767).astype('<i2').tobytes())


def verify(pics, keys, work):
    """pics: dict name->PIL image. Each single change must alter pixels; B must equal union of single changes."""
    a = np.asarray(pics['A'].convert('RGB')).astype(int)
    union = np.zeros(a.shape[:2], bool)
    report = {}
    for k in keys:
        d = np.abs(np.asarray(pics[k].convert('RGB')).astype(int) - a).sum(2) > 30
        n = int(d.sum()); report[k] = n
        if n < 400:
            raise SystemExit(f'difference "{k}" too small/invisible: {n} px')
        if n > 40000:
            raise SystemExit(f'difference "{k}" too big: {n} px')
        union |= d
    db = np.abs(np.asarray(pics['B'].convert('RGB')).astype(int) - a).sum(2) > 30
    extra = int((db & ~union).sum())
    if extra > 50:
        raise SystemExit(f'accidental differences between A and B: {extra} px')
    vis = np.asarray(pics['A'].convert('RGB')).copy() // 3
    vis[db] = [255, 0, 0]
    Image.fromarray(vis.astype('uint8')).save(os.path.join(work, 'diffmap.png'))
    print('diff pixels per change:', report, '| accidental:', extra)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene-module', required=True); ap.add_argument('--date', required=True); ap.add_argument('--slug', required=True)
    ap.add_argument('--outdir', default=os.path.join(ROOT, 'videos'))
    ap.add_argument('--sub', default='Sirf 1% log saare dhoondh paate hain!')
    ap.add_argument('--check-only', action='store_true')
    g = ap.parse_args()
    mod = importlib.import_module('spotdiff_scenes.' + g.scene_module)
    keys = list(mod.DIFFS)
    assert len(keys) == 5, 'need exactly 5 differences'
    work = tempfile.mkdtemp(prefix='spotdiff_')
    logo = b64(open(os.path.join(ROOT, 'assets', 'logo.png'), 'rb').read())
    exe = glob.glob('/opt/pw-browsers/chromium-*/chrome-linux*/chrome')
    exe = os.environ.get('CHROMIUM_PATH') or (exe[0] if exe else None)
    svgs = {'A': mod.draw(set()), 'B': mod.draw(set(keys))}
    for k in keys:
        svgs[k] = mod.draw({k})
    uri = {n: 'data:image/svg+xml;base64,' + b64(s.encode()) for n, s in svgs.items()}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page(viewport={'width': 500, 'height': 900}, device_scale_factor=1)
        pics = {}
        for n, s in svgs.items():
            pg.set_content(f'<html><body style="margin:0">{s}</body></html>')
            path = os.path.join(work, f'{n}.png'); pg.screenshot(path=path); pics[n] = Image.open(path)
        verify(pics, keys, work)
        pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        frames = []
        pg.set_content(page(title_body(mod.SCENE), logo)); pg.wait_for_timeout(150)
        pg.screenshot(path=f'{work}/title.png'); frames.append(('title.png', TITLE))
        for i, n in enumerate(range(COUNT, -1, -1)):
            pg.set_content(page(main_body(uri['A'], uri['B'], g.sub, n), logo)); pg.wait_for_timeout(100)
            if i == 0:  # layout guard: nothing may touch the logo (keep left of x 820 or above y 1570)
                for sel in ('.cta span', '.cd'):
                    r = pg.eval_on_selector(sel, 'e=>{const r=e.getBoundingClientRect();return [r.right+8,r.bottom+8]}')
                    if r[0] > 820 and r[1] > 1570:
                        raise SystemExit(f'{sel} overlaps the logo zone: {r}')
            pg.screenshot(path=f'{work}/c{i:02d}.png')
            frames.append((f'c{i:02d}.png', COUNT / (COUNT + 1)))
        pg.set_content(page(end_body(), logo)); pg.wait_for_timeout(150)
        pg.screenshot(path=f'{work}/end.png'); frames.append(('end.png', END))
        b.close()
    Image.open(f'{work}/c00.png').save(f'{work}/main.png')
    print('work dir:', work)
    if g.check_only:
        return
    total = TITLE + COUNT + END
    with open(f'{work}/list.txt', 'w') as f:
        for name, d in frames:
            f.write(f"file '{work}/{name}'\nduration {d:.4f}\n")
        f.write(f"file '{work}/{frames[-1][0]}'\n")
    audio(f'{work}/a.wav', total)
    os.makedirs(g.outdir, exist_ok=True)
    out = os.path.join(g.outdir, f'{g.date}-spotdiff-{g.slug}.mp4')
    subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{work}/list.txt',
                           '-i', f'{work}/a.wav', '-vf',
                           'fps=30,tpad=stop_mode=clone:stop_duration=%d,' % END +  # concat drops the last still's duration: pad with it
                           'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
                           '-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '128k', '-t', str(total), '-movflags', '+faststart', out])
    add_cta(out, out, y=CTA_Y)  # Like / Share / Follow tag, last 4 s (end card only)
    json.dump({'scene': mod.SCENE, 'differences': list(mod.DIFFS.values())}, open(f'{work}/answers.json', 'w'), ensure_ascii=False)
    print(out)


if __name__ == '__main__':
    main()
