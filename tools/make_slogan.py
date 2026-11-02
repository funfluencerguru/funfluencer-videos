#!/usr/bin/env python3
"""Slogan reel: 1080x1920, 15 s, notebook brand look, mood-matched music made with numpy.

Usage: python3 tools/make_slogan.py spec.json
spec.json:
{
  "tag": "Motivation ✨",
  "lines": ["Dheere chalo,", "par ruko mat."],     # 2-4 lines, wrap a key word in *stars* to highlight it
  "cta": "Save karo & us dost ko bhejo 💌",
  "mood": "uplifting",          # uplifting | emotional | warm | energetic | calm
  "doodle": "sprout",           # sprout | heart | sun | star | hands | none
  "out": "videos/2026-11-07-slogan-dheere-chalo.mp4",
  "seed": 7                     # optional, varies the melody
}
"""
import base64, json, os, re, shutil, subprocess, sys, tempfile, wave
import numpy as np

W, H, FPS, DUR, SR = 1080, 1920, 30, 15.0, 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ACCENT = {  # card glow / tag block / marker highlight / ink accent
    "uplifting": ("#ffe3b3", "#ffd54a", "#ffe066", "#e07a1f"),
    "energetic": ("#d8f5c9", "#9be15d", "#c9f27a", "#2f8f2f"),
    "emotional": ("#e3ddff", "#c9b8ff", "#d9ccff", "#5b4bb7"),
    "warm":      ("#ffd9e3", "#ff9fb8", "#ffc2d1", "#d6336c"),
    "calm":      ("#d6eefc", "#9fd6f5", "#bfe6fb", "#1f78b4"),
}

DOODLES = {
 "sprout": '<path d="M100 190 V95" /><path d="M100 120 C60 115 40 85 45 55 C80 55 100 80 100 120Z" fill="#7bd36b"/>'
           '<path d="M100 105 C140 100 165 70 158 40 C122 42 100 65 100 105Z" fill="#9be15d"/>'
           '<path d="M55 190 H145 L135 150 H65 Z" fill="#e8955a"/>',
 "heart":  '<path d="M100 175 C30 125 25 70 60 55 C82 46 98 62 100 78 C102 62 118 46 140 55 C175 70 170 125 100 175Z" fill="#ff6b8b"/>',
 "sun":    '<circle cx="100" cy="100" r="42" fill="#ffd54a"/>' + ''.join(
           f'<line x1="{100+60*np.cos(a):.0f}" y1="{100+60*np.sin(a):.0f}" x2="{100+82*np.cos(a):.0f}" y2="{100+82*np.sin(a):.0f}"/>'
           for a in np.linspace(0, 2*np.pi, 9)[:-1]),
 "star":   '<path d="M100 25 L122 78 L178 82 L135 118 L148 172 L100 143 L52 172 L65 118 L22 82 L78 78Z" fill="#ffd54a"/>',
 "hands":  '<path d="M40 150 C40 110 70 95 95 105 L95 160 Z" fill="#ffcf9e"/><path d="M160 150 C160 110 130 95 105 105 L105 160Z" fill="#f2b27a"/>'
           '<path d="M85 70 C75 55 95 45 100 60 C105 45 125 55 115 70 L100 85Z" fill="#ff6b8b"/>',
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html(spec):
    glow, tagbg, marker, ink = ACCENT.get(spec["mood"], ACCENT["uplifting"])
    logo = base64.b64encode(open(os.path.join(ROOT, "assets/logo.png"), "rb").read()).decode()
    n = len(spec["lines"])
    size = 96 if n <= 3 else 84
    lines = []
    for i, ln in enumerate(spec["lines"]):
        t = re.sub(r"\*(.+?)\*", lambda m: f'<span class="mk">{m.group(1)}</span>', esc(ln))
        lines.append(f'<div class="ln" data-in="{1.6 + i*0.9:.2f}">{t}</div>')
    d = spec.get("doodle", "none")
    doodle = (f'<svg class="dd" data-in="{1.6 + n*0.9:.2f}" viewBox="0 0 200 200" width="200" height="200" '
              f'stroke="#111" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" fill="none">{DOODLES[d]}</svg>'
              if d in DOODLES else "")
    cta_in = max(1.6 + n*0.9 + 1.2, 6.5)
    return f"""<html><head><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;overflow:hidden;font-family:Poppins,'Noto Color Emoji',sans-serif}}
#bg{{position:absolute;inset:0;background-color:#f5f2e9;
 background-image:radial-gradient(circle at 50% 48%,{glow} 0,rgba(0,0,0,0) 640px),
 repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0,rgba(0,0,0,0) 63px,#b9c8e6 63px,#b9c8e6 65px)}}
#margin{{position:absolute;left:110px;top:0;bottom:0;width:4px;background:#f2a3b3}}
.tag{{position:absolute;top:210px;left:0;right:0;text-align:center}}
.tag span{{display:inline-block;background:{tagbg};border:6px solid #111;box-shadow:12px 12px 0 #111;
 padding:18px 44px;border-radius:18px;font-size:64px;font-weight:700;color:#111;transform:rotate(-2deg)}}
.card{{position:absolute;left:150px;right:90px;top:520px;min-height:820px;background:#fff;border:8px solid #111;
 border-radius:44px;box-shadow:18px 18px 0 #111;padding:70px 50px 60px;display:flex;flex-direction:column;
 justify-content:center;align-items:center;text-align:center}}
.ln{{font-size:{size}px;font-weight:700;line-height:1.18;color:#1c2aa8;margin:6px 0}}
.mk{{background:linear-gradient(transparent 52%,{marker} 52%,{marker} 92%,transparent 92%);color:{ink};padding:0 6px}}
.dd{{margin-top:34px}}
.quote{{position:absolute;left:180px;top:470px;font-size:230px;font-weight:700;color:{ink};line-height:1;font-family:Poppins}}
.cta{{position:absolute;left:130px;right:170px;top:1500px;text-align:center;font-size:44px;white-space:nowrap;font-weight:700;color:#111;
 background:#fff;border:5px solid #111;border-radius:999px;padding:22px 30px;box-shadow:8px 8px 0 #111}}
#logo{{position:absolute;right:30px;bottom:25px;width:190px;height:190px}}
</style></head><body>
<div id="bg"></div><div id="margin"></div>
<div class="tag" data-in="0.3"><span>{esc(spec['tag'])}</span></div>
<div class="card" data-in="0.9">{''.join(lines)}{doodle}</div>
<div class="quote" data-in="0.9">&ldquo;</div>
<div class="cta" data-in="{cta_in:.2f}" data-pop="1">{esc(spec['cta'])}</div>
<img id="logo" src="data:image/png;base64,{logo}">
<script>
const els=[...document.querySelectorAll('[data-in]')];
function ease(x){{x=Math.min(Math.max(x,0),1);return 1-Math.pow(1-x,3)}}
function render(t){{
  document.body.style.opacity=Math.min(1,t/0.4+0.15);
  for(const e of els){{
    const p=ease((t-parseFloat(e.dataset.in))/0.7);
    e.style.opacity=p;
    if(e.dataset.pop){{const s=p<1?0.6+0.5*p-0.1*Math.sin(p*Math.PI):1;e.style.transform=`scale(${{s}})`}}
    else e.style.transform=`translateY(${{(1-p)*50}}px)`;
  }}
}}
render(0);
</script></body></html>"""


# ---------------- music ----------------
def note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def adsr(n, a, d, s, r):
    env = np.ones(n) * s
    A, D, R = int(a*SR), int(d*SR), int(r*SR)
    A = min(A, n); env[:A] = np.linspace(0, 1, A, endpoint=False)
    D = min(D, n - A); env[A:A+D] = np.linspace(1, s, D, endpoint=False)
    if R and n > R: env[-R:] *= np.linspace(1, 0, R)
    return env


def tone(f, dur, kind, amp):
    n = int(dur*SR); t = np.arange(n) / SR
    if kind == "pad":
        y = sum((1/k) * np.sin(2*np.pi*f*k*t + k) for k in (1, 2, 3)) \
            + 0.6 * np.sin(2*np.pi*f*1.004*t) + 0.6 * np.sin(2*np.pi*f*0.996*t)
        y *= adsr(n, 0.6, 0.4, 0.8, 0.8)
    elif kind == "piano":
        y = sum(np.exp(-t*(2.5+k*1.5)) * np.sin(2*np.pi*f*k*t) / k**1.3 for k in (1, 2, 3, 4))
        y *= adsr(n, 0.004, 0.05, 1, 0.08)
    elif kind == "bell":
        y = np.exp(-t*3) * (np.sin(2*np.pi*f*t) + 0.4*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*5))
        y *= adsr(n, 0.003, 0, 1, 0.05)
    elif kind == "bass":
        y = (np.sin(2*np.pi*f*t) + 0.25*np.sin(4*np.pi*f*t)) * adsr(n, 0.02, 0.3, 0.7, 0.2)
    else:  # click
        y = np.random.default_rng(1).standard_normal(n) * np.exp(-t*90)
    return amp * y


def music(mood, seed=0):
    cfg = {  # bpm, key root (midi), progression (scale degrees as semitone offsets of chord roots), minor flags
        "uplifting": (94, 60, [0, 7, 9, 5], "piano"),
        "energetic": (106, 62, [0, 5, 9, 7], "piano"),
        "emotional": (70, 57, [9, 5, 0, 7], "piano"),
        "warm":      (80, 65, [0, 9, 5, 7], "bell"),
        "calm":      (64, 62, [0, 5, 0, 7], "bell"),
    }[mood]
    bpm, key, prog, lead = cfg
    rng = np.random.default_rng(seed)
    out = np.zeros(int((DUR + 2) * SR))
    beat = 60 / bpm; bar = 4 * beat

    def add(y, at):
        i = int(at * SR); out[i:i+len(y)] += y[:len(out)-i]

    def triad(r):
        minor = (r % 12) in (2, 4, 9)
        return [r, r + (3 if minor else 4), r + 7]

    t, k = 0.0, 0
    nbars = int(np.ceil(DUR / bar))
    for b in range(nbars):
        root = key + (prog[k % 4] if b < nbars - 1 else 0)   # last bar resolves home (hope)
        ch = triad(root)
        for m in ch: add(tone(note(m), bar + 0.8, "pad", 0.05), t)
        add(tone(note(root - 24), bar, "bass", 0.18), t)
        build = min(1, (b + 1) / 3)  # energy builds
        steps = 8 if mood in ("uplifting", "energetic") else 4
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12, ch[1] + 12, ch[2] + 12]
        if b > 0:
            for s in range(steps):
                m = arp[(s + int(rng.integers(0, 2))) % len(arp)] if mood != "energetic" else arp[s % 8] + (12 if s > 5 else 0)
                add(tone(note(m), bar / steps * 2.5, lead, 0.09 * build), t + s * bar / steps)
        if mood == "energetic" and b > 0:
            for s in range(8): add(tone(0, 0.08, "click", 0.05 if s % 2 else 0.09), t + s * beat / 2)
        t += bar; k += 1
    # echo
    d = int(beat * 0.75 * SR); y = out.copy()
    for i in range(1, 4): y[d*i:] += out[:-d*i] * (0.32 ** i)
    y = y[:int(DUR * SR)]
    # soft lowpass (one-pole)
    a = 0.35
    for _ in range(1):
        z = np.empty_like(y); acc = 0.0
        # vectorised enough for 15 s
        z = np.convolve(y, a * (1 - a) ** np.arange(64), mode="same")
        y = 0.5 * y + 0.5 * z
    n = len(y); fi, fo = int(1 * SR), int(2 * SR)
    y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo)
    y = y / (np.max(np.abs(y)) + 1e-9) * 10 ** (-3 / 20)
    return y


def main():
    spec = json.load(open(sys.argv[1]))
    out = os.path.join(ROOT, spec["out"]) if not os.path.isabs(spec["out"]) else spec["out"]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = tempfile.mkdtemp()
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_PATH") or None
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.set_content(html(spec)); pg.wait_for_timeout(400)
        frames = int(DUR * FPS)
        for i in range(frames):
            pg.evaluate(f"render({i / FPS})")
            pg.screenshot(path=f"{tmp}/f{i:04d}.jpg", type="jpeg", quality=92)
        pg.evaluate("render(99)"); pg.screenshot(path=out.replace(".mp4", "-frame.png"))
        b.close()
    audio = (music(spec["mood"], spec.get("seed", 0)) * 32767).astype(np.int16)
    with wave.open(f"{tmp}/a.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.jpg", "-i", f"{tmp}/a.wav",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", "-shortest", "-movflags", "+faststart", out], check=True)
    shutil.copy(f"{tmp}/a.wav", out.replace(".mp4", ".wav"))
    shutil.rmtree(tmp)
    print(out)


if __name__ == "__main__":
    main()
