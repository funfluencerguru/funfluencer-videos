#!/usr/bin/env python3
"""Slogan reel: 1080x1920, 15 s. A 90s Indian village scene (doodle style, thick outlines, nostalgic grain)
behind the slogan card, with original village-folk music made with numpy (bansuri-style flute, tanpura drone,
dholak beats and bird chirps, all synthesised, no samples).

Usage: python3 tools/make_slogan.py spec.json
spec.json:
{
  "tag": "Motivation ✨",
  "lines": ["Dheere chalo,", "par *ruko mat.*"],   # 2-4 lines, *stars* = highlighted key word(s)
  "cta": "Save karo & us dost ko bhejo 💌",          # keep under about 32 characters
  "mood": "uplifting",          # uplifting | emotional | warm | energetic | calm (sets sky colour + music)
  "doodle": "sprout",           # sprout | heart | sun | star | hands | none
  "bg_image": "path/to/background.png",  # optional painted 9:16 background (new one every reel); omit = doodle village
  "text_in_image": true,        # optional: the message is already painted into bg_image -> no tag/card, only CTA + logo
  "out": "videos/2026-11-07-slogan-dheere-chalo.mp4",
  "seed": 7                     # optional, varies the melody
}
Also writes <out>-frame.png (final frame) and <out>.wav next to the video; do not commit those two.
"""
import base64, json, os, re, shutil, subprocess, sys, tempfile, wave
# OWNER RULE 2026-11-09 (overrides older task instructions that say 190 px / 25 px from the bottom):
# logo 209 px, 130 px above the bottom, plus the Like/Share/Follow tag from tools/brand.py. Do not revert.
import numpy as np
from scipy.signal import butter, lfilter

W, H, FPS, DUR, SR = 1080, 1920, 30, 15.0, 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#            sky top,   sky bottom, tag block, marker,    ink accent
MOODS = {
    "uplifting": ("#ffb547", "#ffe9b5", "#ffd54a", "#ffe066", "#d9661a"),
    "energetic": ("#6fc3f0", "#dff3ff", "#ffd54a", "#c9f27a", "#2f8f2f"),
    "emotional": ("#8b82c4", "#f7c4a8", "#c9b8ff", "#d9ccff", "#5b4bb7"),
    "warm":      ("#ff8a5c", "#ffd8a3", "#ff9fb8", "#ffc2d1", "#d6336c"),
    "calm":      ("#97c4e6", "#f4e7d2", "#9fd6f5", "#bfe6fb", "#1f78b4"),
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


def village_svg(sky_top, sky_bot):
    """Full-frame 90s village: sky, sun, clouds, kite, birds, hills, mustard field, dirt path, neem tree,
    electric pole, mud hut with thatched roof and old TV antenna, bicycle, hand pump with matkas, bullock cart."""
    spokes = ''.join(f'<line x1="560" y1="1772" x2="{560+68*np.cos(a):.0f}" y2="{1772+68*np.sin(a):.0f}" stroke-width="5"/>'
                     for a in np.linspace(0, 2*np.pi, 9)[:-1])
    bike_spokes = lambda cx: ''.join(f'<line x1="{cx}" y1="1592" x2="{cx+30*np.cos(a):.0f}" y2="{1592+30*np.sin(a):.0f}" stroke-width="2"/>'
                                     for a in np.linspace(0, 2*np.pi, 7)[:-1])
    furrows = ''.join(f'<path d="M{x} 1920 L{540+(x-540)*0.12:.0f} 1345" stroke="#7fa84f" stroke-width="4" fill="none"/>'
                      for x in range(-700, 1900, 130) if not 380 < x < 820)
    mustard = ''.join(f'<circle cx="{x}" cy="{y}" r="7" fill="#ffe14d" stroke="none"/>'
                      for x, y in [(30+i*47 % 470, 1370+(i*29) % 80) for i in range(60)])
    sun_rays = ''.join(f'<line x1="{120*np.cos(a):.0f}" y1="{120*np.sin(a):.0f}" x2="{150*np.cos(a):.0f}" y2="{150*np.sin(a):.0f}"/>'
                       for a in np.linspace(0, 2*np.pi, 13)[:-1])
    cloud = '<path d="M0 60 C-10 20 40 0 60 25 C75 -5 130 -5 140 30 C175 25 185 70 150 75 L10 75 C-10 75 -10 62 0 60Z" fill="#fffaf0"/>'
    bird = '<path d="M0 0 q12 -12 24 0 q12 -12 24 0" fill="none" stroke-width="4"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920"
 stroke="#111" stroke-width="5" stroke-linejoin="round" stroke-linecap="round">
<defs>
 <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky_top}"/><stop offset="1" stop-color="{sky_bot}"/></linearGradient>
 <linearGradient id="grd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a9cf6e"/><stop offset="1" stop-color="#8dbb55"/></linearGradient>
</defs>
<rect width="1080" height="1360" fill="url(#sky)" stroke="none"/>
<g id="sun" transform="translate(940,120)"><g id="rays" stroke="#e8a317" stroke-width="7">{sun_rays}</g>
 <circle r="95" fill="#ffd54a" stroke-width="6"/></g>
<g id="c1" transform="translate(40,40) scale(1.2)">{cloud}</g>
<g id="c2" transform="translate(620,380) scale(0.9)">{cloud}</g>
<g id="c3" transform="translate(-60,410) scale(0.8)">{cloud}</g>
<g id="birds">
 <g transform="translate(300,400)">{bird}</g><g transform="translate(370,375) scale(.8)">{bird}</g><g transform="translate(430,410) scale(.7)">{bird}</g></g>
<path d="M1000 610 C 700 720, 300 720, -20 640" fill="none" stroke-width="3"/>
<path d="M1000 640 C 700 760, 300 760, -20 690" fill="none" stroke-width="3"/>
<g id="kite" transform="translate(110,170)">
 <path d="M0 0 C -40 120, -60 260, -150 420" fill="none" stroke-width="2"/>
 <path d="M0 -70 L50 0 L0 80 L-50 0Z" fill="#ff5a5f"/><path d="M0 -70 V80 M-50 0 H50" stroke-width="3"/>
 <path d="M0 80 l-12 18 l18 6 l-12 18" fill="none" stroke-width="3"/></g>
<path d="M0 1350 Q 160 1255 360 1335 Q 560 1240 780 1325 Q 940 1265 1080 1320 L1080 1400 L0 1400Z" fill="#7fae5b"/>
<rect y="1345" width="1080" height="575" fill="url(#grd)" stroke="none"/>
<line x1="0" y1="1345" x2="1080" y2="1345"/>
{furrows}
<path d="M0 1355 H500 L470 1470 H0Z" fill="#f2c72f"/>{mustard}
<path d="M380 1920 C 450 1720, 560 1520, 590 1347 L 625 1347 C 625 1520, 730 1720, 820 1920 Z" fill="#d9a86c"/>
<g id="tree">
 <path d="M30 1560 C 55 1350, 50 1150, 70 980 L 110 980 C 110 1150, 120 1350, 150 1560Z" fill="#8a5a32"/>
 <circle cx="20" cy="900" r="150" fill="#4f9440"/><circle cx="170" cy="820" r="130" fill="#5ea84c"/>
 <circle cx="60" cy="760" r="120" fill="#6bb85a"/><circle cx="200" cy="960" r="110" fill="#4f9440"/></g>
<g id="pole"><rect x="1022" y="560" width="22" height="900" fill="#8d8d8d"/><rect x="985" y="600" width="95" height="16" fill="#8d8d8d"/></g>
<g id="hut">
 <rect x="790" y="1470" width="230" height="135" fill="#d4874a"/>
 <path d="M800 1560 h210" stroke="#fff6e0" stroke-width="4" stroke-dasharray="6 14"/>
 <rect x="870" y="1510" width="60" height="95" fill="#6b3f1f"/>
 <rect x="950" y="1500" width="45" height="40" fill="#ffe9a8"/><path d="M972 1500 V1540 M950 1520 H995" stroke-width="3"/>
 <path d="M765 1478 L1045 1478 L985 1385 L825 1385Z" fill="#c9a24a"/>
 <path d="M800 1478 L840 1390 M840 1478 L870 1390 M880 1478 L900 1390 M925 1478 L935 1390 M970 1478 L960 1390 M1010 1478 L985 1390" stroke-width="3"/>
 <line x1="960" y1="1388" x2="960" y2="1270" stroke-width="5"/>
 <path d="M915 1285 H1005 M925 1305 H995 M935 1325 H985 M945 1345 H975" stroke-width="4"/></g>
<g id="bike">
 <circle cx="690" cy="1592" r="30" fill="none" stroke-width="4"/><circle cx="770" cy="1592" r="30" fill="none" stroke-width="4"/>
 {bike_spokes(690)}{bike_spokes(770)}
 <path d="M690 1592 L722 1545 L760 1545 L770 1592 M722 1545 L740 1592 L760 1545 M760 1545 L765 1528 M752 1528 H778 M722 1545 L718 1532 M708 1530 H730" fill="none" stroke-width="5" stroke="#1f4fa0"/></g>
<g id="pump">
 <rect x="215" y="1640" width="90" height="22" fill="#9a9a9a"/>
 <rect x="243" y="1505" width="34" height="138" fill="#3d6fb5"/>
 <path d="M277 1540 H322 V1560" fill="none" stroke-width="10" stroke="#3d6fb5"/><path d="M277 1540 H322 V1560" fill="none" stroke-width="3"/>
 <path d="M246 1512 L178 1470" stroke-width="9"/><circle cx="260" cy="1500" r="12" fill="#3d6fb5"/>
 <ellipse cx="345" cy="1640" rx="34" ry="30" fill="#c0612b"/><ellipse cx="345" cy="1612" rx="16" ry="6" fill="#8a3f17"/>
 <path d="M392 1650 h30 l-4 -26 h-22z" fill="#c9c9c9"/></g>
<g id="cart">
 <path d="M440 1700 L180 1720" stroke-width="7" stroke="#6b3f1f"/>
 <path d="M440 1660 Q 560 1585 700 1660Z" fill="#e8c35a"/>
 <path d="M470 1630 l10 30 M540 1610 l5 45 M610 1612 l-5 45 M665 1635 l-8 25" stroke-width="3"/>
 <rect x="430" y="1660" width="280" height="38" rx="6" fill="#a8693a"/>
 <circle cx="560" cy="1772" r="74" fill="none" stroke="#6b3f1f" stroke-width="14"/><circle cx="560" cy="1772" r="81" fill="none" stroke-width="4"/>
 {spokes}<circle cx="560" cy="1772" r="14" fill="#6b3f1f"/></g>
<g id="bull">
 <path d="M190 1760 v80 M220 1765 v80 M300 1765 v80 M330 1760 v80" stroke-width="12"/>
 <ellipse cx="262" cy="1745" rx="95" ry="48" fill="#f1ece0"/>
 <path d="M175 1705 q 18 -40 50 -8" fill="#f1ece0"/>
 <path d="M356 1740 q 30 20 18 70" fill="none" stroke-width="4" id="tail"/>
 <ellipse cx="145" cy="1735" rx="38" ry="48" fill="#f1ece0" transform="rotate(20 145 1735)"/>
 <path d="M128 1700 q -18 -22 -6 -42" fill="none" stroke-width="9" stroke="#111"/><path d="M128 1700 q -18 -22 -6 -42" fill="none" stroke-width="5" stroke="#f4d7a6"/>
 <path d="M160 1704 q 16 -24 6 -44" fill="none" stroke-width="9" stroke="#111"/><path d="M160 1704 q 16 -24 6 -44" fill="none" stroke-width="5" stroke="#f4d7a6"/>
 <circle cx="133" cy="1728" r="5" fill="#111"/><ellipse cx="128" cy="1772" rx="16" ry="10" fill="#e9c6b5"/></g>
</svg>'''


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html(spec):
    sky_top, sky_bot, tagbg, marker, ink = MOODS.get(spec["mood"], MOODS["uplifting"])
    logo = base64.b64encode(open(os.path.join(ROOT, "assets/logo.png"), "rb").read()).decode()
    bg = spec.get("bg_image")
    if bg:   # painted background (new AI-made image every reel), slow Ken Burns push-in
        bgp = bg if os.path.isabs(bg) else os.path.join(ROOT, bg)
        mime = "image/png" if bgp.lower().endswith(".png") else "image/jpeg"
        scene_html = f'<img id="bgimg" src="data:{mime};base64,{base64.b64encode(open(bgp, "rb").read()).decode()}">'
        scene = ""
    else:    # fallback: hand-drawn doodle village
        scene_html = ""
        scene = base64.b64encode(village_svg(sky_top, sky_bot).encode()).decode()
    tint_op = ".10" if bg else ".22"
    zoom = "0.0035" if spec.get("text_in_image") else "0.006"
    card_min = "0px" if bg else "700px"
    n = len(spec["lines"])
    size = 92 if n <= 3 else 80
    lines = []
    for i, ln in enumerate(spec["lines"]):
        t = re.sub(r"\*(.+?)\*", lambda m: f'<span class="mk">{m.group(1)}</span>', esc(ln))
        lines.append(f'<div class="ln" data-in="{1.6 + i*0.9:.2f}">{t}</div>')
    d = spec.get("doodle", "none")
    doodle = (f'<svg class="dd" data-in="{1.6 + n*0.9:.2f}" viewBox="0 0 200 200" width="170" height="170" '
              f'stroke="#111" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" fill="none">{DOODLES[d]}</svg>'
              if d in DOODLES else "")
    cta_in = max(1.6 + n*0.9 + 1.2, 6.5)
    tii = bool(spec.get("text_in_image")) and bool(bg)   # message already painted into the picture
    if tii:
        overlay = ""
        cta_in = 9.0
        tint_op = ".06"
    else:
        overlay = (f'<div class="tag" data-in="0.3"><span>{esc(spec.get("tag", ""))}</span></div>'
                   f'<div class="card" data-in="0.9">{"".join(lines)}{doodle}</div>'
                   f'<div class="quote" data-in="0.9">&ldquo;</div>')
    cta_html = (f'<div class="cta{" small" if tii else ""}" data-in="{cta_in:.2f}" data-pop="1">{esc(spec["cta"])}</div>'
                if spec.get("cta") else "")
    # village scene is inlined so its parts (clouds, birds, kite, sun rays, tail) can move each frame
    return f"""<html><head><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;overflow:hidden;font-family:Poppins,'Liberation Sans',Arial,sans-serif,'Noto Color Emoji';background:#f5e6c8}}
#scene{{position:absolute;inset:0;overflow:hidden}}
#bgimg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform-origin:50% 70%}}
#tint{{position:absolute;inset:0;background:#f3d29b;mix-blend-mode:multiply;opacity:{tint_op}}}
#vig{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,rgba(0,0,0,0) 55%,rgba(70,40,10,.45) 100%)}}
#grain{{position:absolute;inset:0;opacity:.13;mix-blend-mode:multiply}}
.tag{{position:absolute;top:220px;left:0;right:0;text-align:center}}
.tag span{{display:inline-block;background:{tagbg};border:6px solid #111;box-shadow:12px 12px 0 #111;
 padding:16px 44px;border-radius:18px;font-size:62px;font-weight:700;color:#111;transform:rotate(-2deg)}}
.card{{position:absolute;left:140px;right:100px;top:480px;min-height:{card_min};background:rgba(255,250,236,.96);border:8px solid #111;
 border-radius:44px;box-shadow:18px 18px 0 #111;padding:56px 46px 46px;display:flex;flex-direction:column;
 justify-content:center;align-items:center;text-align:center}}
.ln{{font-size:{size}px;font-weight:700;line-height:1.18;color:#1c2aa8;margin:6px 0;white-space:nowrap}}
.mk{{background:linear-gradient(transparent 52%,{marker} 52%,{marker} 92%,transparent 92%);color:{ink};padding:0 6px}}
.dd{{margin-top:26px}}
.quote{{position:absolute;left:170px;top:450px;font-size:230px;font-weight:700;color:{ink};line-height:1;font-family:Poppins}}
.cta{{position:absolute;left:120px;right:180px;top:1268px;text-align:center;font-size:44px;white-space:nowrap;font-weight:700;color:#111;
 background:#fff;border:5px solid #111;border-radius:999px;padding:20px 30px;box-shadow:8px 8px 0 #111}}
.cta.small{{top:1585px;left:60px;right:270px;font-size:38px;padding:16px 24px;background:rgba(255,255,255,.94)}}
#logo{{position:absolute;right:30px;bottom:130px;width:209px;height:209px}}
</style></head><body>
<div id="scene">{scene_html}</div><div id="tint"></div><div id="vig"></div>
<svg id="grain" width="{W}" height="{H}"><filter id="n"><feTurbulence id="turb" type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="1"/>
 <feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>
{overlay}
{cta_html}
<img id="logo" src="data:image/png;base64,{logo}">
<script>
if('{scene}') document.getElementById('scene').innerHTML=atob('{scene}');
const els=[...document.querySelectorAll('[data-in]')];
function fit(){{
  const card=document.querySelector('.card'), lns=[...document.querySelectorAll('.ln')];
  const cta0=document.querySelector('.cta');
  if(!card){{ if(cta0) for(let c=38;c>=26;c-=1){{cta0.style.fontSize=c+'px'; if(cta0.scrollWidth<=cta0.clientWidth) break;}} return 0; }}
  const inner=card.clientWidth-92, cta=document.querySelector('.cta');
  for(let c=44;c>=30;c-=1){{cta.style.fontSize=c+'px'; if(cta.scrollWidth<=cta.clientWidth) break;}}
  for(let s={size};s>=48;s-=2){{
    lns.forEach(l=>l.style.fontSize=s+'px');
    if(lns.every(l=>l.scrollWidth<=inner) && card.offsetHeight<=740){{
      if(document.getElementById('bgimg')) cta.style.top=(480+card.offsetHeight+48)+'px';
      return s;
    }}
  }}
  return 48;
}}
const $=id=>document.getElementById(id);
function ease(x){{x=Math.min(Math.max(x,0),1);return 1-Math.pow(1-x,3)}}
function render(t){{
  document.body.style.opacity=Math.min(1,t/0.5+0.1);
  for(const e of els){{
    const p=ease((t-parseFloat(e.dataset.in))/0.7);
    e.style.opacity=p;
    if(e.dataset.pop){{const s=p<1?0.6+0.5*p-0.1*Math.sin(p*Math.PI):1;e.style.transform=`scale(${{s}})`}}
    else e.style.transform=`translateY(${{(1-p)*50}}px)`;
  }}
  if($('bgimg')){{ $('bgimg').style.transform=`scale(${{1.0+t*{zoom}}})`; }}
  else {{
  $('c1').setAttribute('transform',`translate(${{40+t*9}},40) scale(1.2)`);
  $('c2').setAttribute('transform',`translate(${{620+t*6}},380) scale(0.9)`);
  $('c3').setAttribute('transform',`translate(${{-60+t*7}},410) scale(0.8)`);
  $('birds').setAttribute('transform',`translate(${{-80+t*45}},${{Math.sin(t*1.3)*12}})`);
  $('kite').setAttribute('transform',`translate(${{110+Math.sin(t*1.1)*10}},${{170+Math.sin(t*1.7)*8}}) rotate(${{Math.sin(t*1.4)*9}})`);
  $('rays').setAttribute('transform',`rotate(${{t*8}})`);
  $('tail').setAttribute('transform',`rotate(${{Math.sin(t*3)*10}} 356 1740)`);
  }}
  $('turb').setAttribute('seed',String(Math.floor(t*12)%7+1));
}}
render(0);
</script></body></html>"""


# ---------------- village-folk music ----------------
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bandpass(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return lfilter(b, a, x)


def flute(notes, n):
    """Bansuri-style flute: smooth glides (meend), delayed vibrato, breath noise. notes = [(midi, start_s, dur_s)]."""
    f = np.zeros(n); amp = np.zeros(n); since = np.zeros(n)
    for m, st, du in notes:
        i0, i1 = int(st * SR), min(n, int((st + du) * SR))
        f[i0:i1] = np.log(mtof(m)); amp[i0:i1] = 1.0; since[i0:i1] = np.arange(i1 - i0) / SR
        r = min(int(0.07 * SR), i1 - i0)                    # small breath gap at the end of each note
        amp[i1 - r:i1] *= np.linspace(1, 0.35, r)
    # hold pitch through rests so glides start from the previous note
    last = np.log(mtof(notes[0][0]))
    idx = np.where(f == 0)[0]
    filled = f.copy()
    for i in range(n):
        if filled[i] == 0: filled[i] = last
        else: last = filled[i]
    a = np.exp(-1 / (0.045 * SR)); logf = lfilter([1 - a], [1, -a], filled, zi=[filled[0] * a])[0]
    b = np.exp(-1 / (0.05 * SR)); env = lfilter([1 - b], [1, -b], amp)
    vib = 1 + 0.006 * np.clip((since - 0.25) / 0.4, 0, 1) * np.sin(2 * np.pi * 5.3 * np.arange(n) / SR)
    ph = np.cumsum(np.exp(logf) * vib) * 2 * np.pi / SR
    tone = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    breath = bandpass(np.random.default_rng(5).standard_normal(n), 1200, 5000) * 0.10
    return (tone + breath) * env


def tanpura(sa, n, period=0.8):
    """Tanpura drone: Pa(low) - Sa - Sa - Sa(low), each pluck rich in buzzing harmonics."""
    out = np.zeros(n); seq = [sa - 5, sa, sa, sa - 12]
    L = int(3.2 * SR); t = np.arange(L) / SR
    k = 0; st = 0.0
    while st < n / SR:
        f = mtof(seq[k % 4]); y = np.zeros(L)
        for h in range(1, 13):
            if f * h > 6000: break
            buzz = 1 + 0.6 * np.sin(np.pi * np.clip(t / (0.6 + 0.12 * h), 0, 1))   # jawari swell of upper partials
            y += (1 / h ** 0.85) * np.exp(-t * (0.9 + 0.12 * h)) * np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h)) * (buzz if h > 2 else 1)
        y *= np.minimum(1, t / 0.004)
        i = int(st * SR); out[i:i + L] += y[:max(0, n - i)]
        st += period; k += 1
    return out


def dholak(bpm, n, start, dense=False):
    """Keherwa-style dholak: low 'dha' (pitch drop) and high 'na'/'ka' strokes on eighth notes."""
    out = np.zeros(n); e = 30 / bpm
    def low():
        L = int(0.35 * SR); t = np.arange(L) / SR
        f = 75 + 70 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    def high(p=520):
        L = int(0.16 * SR); t = np.arange(L) / SR
        return (np.sin(2 * np.pi * p * t) + 0.4 * np.sin(2 * np.pi * p * 2.3 * t)) * np.exp(-t * 30) \
            + np.random.default_rng(2).standard_normal(L) * np.exp(-t * 120) * 0.3
    pattern = ["L", "", "H", "h", "H", "L", "H", "h"]          # dha . na ti na dha na ka (8 eighths)
    lo, hi, hk = low(), high(), high(700)
    i = 0; st = start
    while st < n / SR - 0.3:
        p = pattern[i % 8]
        add = {"L": lo * 0.9, "H": hi * 0.5, "h": hk * 0.32}.get(p)
        if add is None and dense: add = hk * 0.18
        if add is not None:
            j = int(st * SR); out[j:j + len(add)] += add[:n - j]
        st += e; i += 1
    return out


def ghungroo(bpm, n, start):
    out = np.zeros(n); e = 30 / bpm; L = int(0.12 * SR); t = np.arange(L) / SR
    j = bandpass(np.random.default_rng(9).standard_normal(L), 5000, 12000) * np.exp(-t * 35)
    st = start
    while st < n / SR - 0.3:
        i = int(st * SR); out[i:i + L] += j[:n - i]; st += e
    return out


def birds(n, rng, count=5, until=5.0):
    out = np.zeros(n)
    for _ in range(count):
        st = rng.uniform(0.2, until); f0 = rng.uniform(3200, 4200)
        for r in range(int(rng.integers(2, 4))):
            L = int(0.07 * SR); t = np.arange(L) / SR
            f = f0 + 1600 * t / 0.07
            y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.07)
            i = int((st + r * 0.11) * SR); out[i:i + L] += y[:max(0, n - i)]
    return out


def melody(mood, bpm, sa, rng):
    """Original phrases on a folk pentatonic scale; final phrase always comes home to Sa (hopeful ending)."""
    major = [0, 2, 4, 7, 9]; minorish = [0, 2, 3, 7, 8]
    scale = minorish if mood == "emotional" else major
    beat = 60 / bpm
    rhythms = [[1, 1, 2, 1, 1, 2], [2, 1, 1, 2, 2], [1.5, 0.5, 1, 1, 2, 2], [1, 0.5, 0.5, 2, 1, 1, 2], [0.5, 0.5, 1, 2, 2, 2]]
    if mood in ("emotional", "calm"):
        rhythms = [[2, 2, 4], [3, 1, 2, 2], [2, 1, 1, 4]]
    def pitches(sc):
        return [sa + o * 12 + s for o in (0, 1) for s in sc] + [sa + 24]
    notes, t = [], 1.2                                 # flute enters after the tanpura and birds set the scene
    end = DUR - 1.6
    phrase_no = 0; motif = None
    while t < end - 1.0:
        last = t + 8 * beat >= end - 1.0
        sc = major if last else scale
        P = pitches(sc)
        if motif is None or phrase_no == 2:
            rh = rhythms[int(rng.integers(len(rhythms)))]
            idx = int(rng.integers(3, 7)); seq = []
            for d in rh:
                seq.append(idx); idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2]), 1, len(P) - 2))
            motif = (rh, seq)
        rh, seq = motif
        seq = list(seq)
        if phrase_no % 2 == 1:
            seq[-1] = 5 if seq[-1] != 5 else 7          # answer phrase: different cadence
        if last:
            seq[-1] = 5                                # upper Sa
        for d, ix in zip(rh, seq):
            if t >= end: break
            du = d * beat
            if last and ix == seq[-1] and d == rh[-1]: du = max(du, DUR - t - 0.3)
            notes.append((P[ix], t, min(du, DUR - t)))
            t += d * beat
        t += beat * (0.5 if phrase_no % 2 == 0 else 1)  # breath between phrases
        phrase_no += 1
    return notes


def music(mood, seed=0):
    bpm = {"uplifting": 96, "energetic": 108, "warm": 84, "emotional": 70, "calm": 64}[mood]
    rng = np.random.default_rng(seed)
    n = int(DUR * SR); sa = 62                            # Sa = D
    mix = 0.42 * flute(melody(mood, bpm, sa + 12, rng), n)
    mix += 0.16 * tanpura(sa - 12, n)
    beat = 60 / bpm
    if mood in ("uplifting", "warm", "energetic"):
        mix += 0.30 * dholak(bpm, n, start=round(2.0 / beat) * beat, dense=(mood == "energetic"))
    if mood == "energetic":
        mix += 0.05 * ghungroo(bpm, n, start=round(2.0 / beat) * beat)
    mix += 0.035 * birds(n, rng, count=6 if mood != "energetic" else 4)
    # small courtyard echo
    for d, g in ((0.17, 0.22), (0.29, 0.13), (0.43, 0.07)):
        k = int(d * SR); mix[k:] += g * mix[:-k].copy()
    fi, fo = int(1.0 * SR), int(2.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.4) / np.tanh(1.4)
    return mix * 10 ** (-3 / 20)


def main():
    spec = json.load(open(sys.argv[1]))
    out = spec["out"] if os.path.isabs(spec["out"]) else os.path.join(ROOT, spec["out"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = tempfile.mkdtemp()
    from playwright.sync_api import sync_playwright
    exe = os.environ.get("CHROMIUM_PATH") or None
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.set_content(html(spec)); pg.wait_for_timeout(500)
        print("slogan font px:", pg.evaluate("document.fonts.ready.then(()=>fit())"))
        for i in range(int(DUR * FPS)):
            pg.evaluate(f"render({i / FPS})")
            pg.screenshot(path=f"{tmp}/f{i:04d}.jpg", type="jpeg", quality=92)
        pg.evaluate("render(12)"); pg.screenshot(path=out.replace(".mp4", "-frame.png"))
        b.close()
    audio = (music(spec["mood"], spec.get("seed", 0)) * 32767).astype(np.int16)
    with wave.open(f"{tmp}/a.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.jpg", "-i", f"{tmp}/a.wav",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from brand import add_cta
    add_cta(out, out, y=spec.get("cta_y", 1420))  # Like / Share / Follow reminder, last 4 s
    shutil.copy(f"{tmp}/a.wav", out.replace(".mp4", ".wav"))
    shutil.rmtree(tmp)
    print(out)


if __name__ == "__main__":
    main()
