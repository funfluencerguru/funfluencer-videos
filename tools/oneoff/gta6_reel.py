"""GTA VI launch reel (25 s, 9:16, animated). One-off, 2026-11-23.
Synthwave neon look (generic: sunset, grid, palms; no game art, logos or characters).
Usage: python3 tools/oneoff/gta6_reel.py videos/<date>-gta6-animated.mp4
Facts (sources: PlayStation India listing via Business Today 4 Nov 2026, Analytics Insight):
  launch 19 Nov 2026, PS5 + Xbox Series X|S, game Rs 5,999, game + new PS5 about Rs 70,989, no PC version yet.
"""
import base64, os, shutil, subprocess, sys, tempfile, wave
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from brand import add_cta, logo_box
W, H, FPS, DUR = 1080, 1920, 30, 25.0
SR = 44100
LX, LY, LS = logo_box(190, 30)


def b64(p): return base64.b64encode(open(p, "rb").read()).decode()


def page():
    logo = b64(os.path.join(ROOT, "assets/logo.png"))
    fb = b64(os.path.join(ROOT, "assets/fonts/Inter-ExtraBold.otf"))
    palm = ('<path d="M60 900 C70 700 80 500 120 330" stroke="#14061f" stroke-width="26" fill="none"/>'
            '<g fill="#14061f"><path d="M120 330 C40 280 -40 300 -90 360 C0 320 60 330 120 340Z"/>'
            '<path d="M120 330 C180 250 280 250 330 300 C250 290 180 310 120 345Z"/>'
            '<path d="M120 330 C90 230 20 190 -40 200 C40 230 80 280 115 340Z"/>'
            '<path d="M120 330 C170 220 250 190 300 210 C230 230 170 280 125 345Z"/>'
            '<path d="M120 330 C60 340 0 400 -20 460 C40 400 80 370 125 345Z"/>'
            '<path d="M120 330 C190 350 250 410 260 470 C200 410 160 380 118 348Z"/></g>')
    sky = "".join(f'<rect x="{x}" y="{1210 - h}" width="{w}" height="{h}" fill="#1b0930"/>' for x, w, h in
                  [(0, 90, 160), (85, 70, 260), (150, 110, 200), (255, 60, 330), (310, 120, 230), (425, 80, 380), (500, 100, 260),
                   (595, 70, 300), (660, 130, 210), (785, 70, 350), (850, 110, 240), (955, 125, 290)])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:XB;src:url(data:font/otf;base64,{fb})}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;overflow:hidden;background:#12051f;font-family:XB,Poppins,'Noto Color Emoji',sans-serif;color:#fff}}
#world{{position:absolute;inset:0;transform-origin:50% 45%}}
#sky{{position:absolute;inset:0;background:linear-gradient(#12051f 0%,#3a0d5e 28%,#a3227a 50%,#ff6a3d 62%,#ffb347 66%,#2a0a3f 66.2%,#12051f 100%)}}
#sun{{position:absolute;left:290px;top:820px;width:500px;height:500px;border-radius:50%;
 background:linear-gradient(#ffe36b,#ff8a3d 55%,#ff3d8b);
 -webkit-mask:linear-gradient(#000 52%,transparent 52%,transparent 56%,#000 56%,#000 64%,transparent 64%,transparent 69%,#000 69%,#000 76%,transparent 76%,transparent 82%,#000 82%,#000 88%,transparent 88%);
 filter:drop-shadow(0 0 60px #ff4f9a)}}
#skyline{{position:absolute;left:0;top:0}}
#grid{{position:absolute;left:0;top:1268px}}
.palm{{position:absolute;top:350px;width:340px;height:950px}}
.star{{position:absolute;width:6px;height:6px;border-radius:50%;background:#fff}}
.sc{{position:absolute;inset:0;opacity:0}}
.hd{{position:absolute;left:60px;right:60px;top:250px;text-align:center;font-size:62px;line-height:1.12;text-shadow:0 0 18px #ff2fd0,0 6px 0 #3a0a55}}
.cap{{position:absolute;left:90px;right:90px;top:1150px;text-align:center;font-size:54px;line-height:1.15;padding:18px 20px;border-radius:30px;background:rgba(18,4,30,.72);text-shadow:0 4px 0 #2a0640}}
.big{{position:absolute;left:0;right:0;text-align:center}}
.em{{position:absolute;font-family:'Noto Color Emoji';line-height:1}}
.card{{position:absolute;left:110px;right:110px;top:560px;height:420px;border-radius:44px;background:rgba(20,6,40,.82);
 border:6px solid #2ff3ff;box-shadow:0 0 40px #2ff3ff,inset 0 0 30px rgba(47,243,255,.35)}}
.price{{position:absolute;left:0;right:0;top:640px;text-align:center;font-size:150px;letter-spacing:2px}}
.pill{{display:inline-block;padding:14px 38px;border-radius:999px;font-size:44px}}
.stamp{{position:absolute;left:90px;right:90px;top:820px;text-align:center;font-size:76px;color:#ff2a4f;border:12px solid #ff2a4f;border-radius:28px;
 padding:18px 10px;background:rgba(18,4,30,.85);box-shadow:0 0 40px #ff2a4f}}
.bub{{position:absolute;left:360px;top:560px;width:640px;padding:36px 40px;border-radius:40px;background:#fff;color:#1a0830;font-size:60px;line-height:1.15;text-align:center;
 box-shadow:10px 10px 0 #ff2fd0}}
.bub:after{{content:"";position:absolute;left:-46px;top:120px;border:28px solid transparent;border-right:46px solid #fff}}
#flash{{position:absolute;inset:0;background:#fff;opacity:0}}
#logo{{position:absolute;left:{LX}px;top:{LY}px;width:{LS}px;height:{LS}px}}
</style></head><body>
<div id="world">
 <div id="sky"></div>
 <div id="stars"></div>
 <div id="sun"></div>
 <svg id="skyline" width="{W}" height="{H}">{sky}</svg>
 <svg id="grid" width="{W}" height="652"><g id="gl" stroke="#ff3fd0" stroke-width="3" opacity=".85"></g></svg>
 <svg class="palm" id="pl" viewBox="-100 150 450 760" style="left:-80px">{palm}</svg>
 <svg class="palm" id="pr" viewBox="-100 150 450 760" style="right:-60px;transform:scaleX(-1)">{palm}</svg>

 <div class="sc" id="s1">
  <div class="big" id="title" style="top:450px;font-size:215px;letter-spacing:4px">
   <span class="L">G</span><span class="L">T</span><span class="L">A</span>&nbsp;<span class="L" style="color:#ffe36b">V</span><span class="L" style="color:#ffe36b">I</span></div>
  <div class="big" id="t2" style="top:760px;font-size:110px;color:#2ff3ff;text-shadow:0 0 26px #2ff3ff,0 8px 0 #3a0a55">AA GAYA! 🔥</div>
  <div class="big" id="t3" style="top:960px"><span class="pill" style="background:#ff2fd0;box-shadow:0 0 30px #ff2fd0">19 Nov 2026 · PS5 &amp; Xbox</span></div>
  <div class="cap" id="t4">Gamers ki Diwali 🎆</div>
 </div>

 <div class="sc" id="s2">
  <div class="hd">Step 1:<br>Game kharido 🛒</div>
  <div class="card"></div>
  <div class="em" id="pad" style="left:430px;top:450px;font-size:220px">🎮</div>
  <div class="price" id="p2" style="color:#7dffb0;text-shadow:0 0 30px #33ff8a">₹0</div>
  <div class="big" id="ok" style="top:850px"><span class="pill" style="background:#20c46a;font-size:56px">✅ DONE!</span></div>
  <div class="cap" id="c2">"Itna toh manage<br>ho jayega" 😎</div>
 </div>

 <div class="sc" id="s3">
  <div class="hd">Step 2:<br>PS5 bhi chahiye... 🤔</div>
  <div class="card" id="card3" style="border-color:#ff2a4f;box-shadow:0 0 40px #ff2a4f"></div>
  <div class="em" id="wal" style="left:440px;top:470px;font-size:200px">👛</div>
  <div id="cash"></div>
  <div class="price" id="p3" style="color:#ff5470;text-shadow:0 0 30px #ff2a4f">₹5,999</div>
  <div class="big" id="tot" style="top:850px;font-size:62px;color:#ffe36b">TOTAL (game + PS5)</div>
  <div class="em" id="shock" style="left:390px;top:1040px;font-size:300px">😱</div>
 </div>

 <div class="sc" id="s4">
  <div class="hd">"Koi na,<br>PC pe khel lenge!" 💻</div>
  <div class="em" id="pc" style="left:380px;top:520px;font-size:320px">🖥️</div>
  <div class="stamp" id="stamp">PC VERSION:<br>ABHI NAHI ❌</div>
  <div class="cap" id="c4">PC wale: 💀💀💀</div>
 </div>

 <div class="sc" id="s5">
  <div class="hd">Phir Papa se<br>paise maange... 🙏</div>
  <div class="em" id="dad" style="left:70px;top:560px;font-size:270px">👨</div>
  <div class="bub" id="bub">"Pehle report card<br>dikhao!" 📚</div>
  <div class="em" id="chap" style="left:-260px;top:930px;font-size:190px">🩴</div>
  <div class="em" id="kid" style="left:700px;top:960px;font-size:230px">😵</div>
 </div>

 <div class="sc" id="s6">
  <div class="hd" id="h6">Final plan: 😂</div>
  <div class="em" id="phone" style="left:380px;top:430px;font-size:330px">📱</div>
  <div class="big" id="yt" style="top:820px;font-size:76px;line-height:1.15;text-shadow:0 0 20px #ff2fd0,0 6px 0 #3a0a55">YouTube pe gameplay<br>dekh lenge! 🍿</div>
  <div class="cap" id="c6" style="color:#2ff3ff">Tumhara plan kya hai?<br>Comment karo 👇</div>
 </div>
</div>
<div id="flash"></div>
<img id="logo" src="data:image/png;base64,{logo}">
<script>
const $=id=>document.getElementById(id);
const cl=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const eo=x=>{{x=cl(x);return 1-Math.pow(1-x,3)}};
const back=x=>{{x=cl(x);const c=1.9;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
function env(t,a,b,fi=.35,fo=.3){{return cl(Math.min((t-a)/fi,(b-t)/fo))}}
function pop(el,t,t0,base=''){{const p=back((t-t0)/.45);el.style.opacity=cl((t-t0)/.15);el.style.transform=base+` scale(${{Math.max(0,p)}})`}}
const rupee=n=>'₹'+Math.round(n).toLocaleString('en-IN');
// stars + grid
let s='';for(let i=0;i<70;i++){{s+=`<div class="star" style="left:${{Math.floor(Math.abs(Math.sin(i*12.9898)*43758.5)%1080)}}px;top:${{Math.floor(Math.abs(Math.sin(i*78.233)*12345.6)%720)+30}}px"></div>`}}$('stars').innerHTML=s;
let g='';for(let i=-12;i<=12;i++){{g+=`<line x1="${{540+i*30}}" y1="0" x2="${{540+i*260}}" y2="652"/>`}}
for(let k=0;k<12;k++)g+=`<line class="hz" x1="0" x2="1080" y1="0" y2="0"/>`;$('gl').innerHTML=g;
const hz=[...document.querySelectorAll('.hz')], stars=[...document.querySelectorAll('.star')], L=[...document.querySelectorAll('.L')];
let c='';for(let i=0;i<14;i++)c+=`<div class="em cash" style="font-size:90px;left:0;top:0;opacity:0">💸</div>`;$('cash').innerHTML=c;
const cash=[...document.querySelectorAll('.cash')];
function render(t){{
  // background motion
  hz.forEach((h,k)=>{{const f=((k+ (t*0.9)%1)/12);const y=652*Math.pow(f,2.2);h.setAttribute('y1',y);h.setAttribute('y2',y);h.setAttribute('opacity',f)}});
  stars.forEach((st,i)=>st.style.opacity=.25+.6*Math.abs(Math.sin(t*1.7+i)));
  $('sun').style.transform=`translateY(${{-t*3}}px)`;
  $('pl').style.transform=`rotate(${{Math.sin(t*1.2)*1.5}}deg)`;$('pr').style.transform=`scaleX(-1) rotate(${{Math.sin(t*1.2+1)*1.5}}deg)`;
  let shake=0, zoom=1+t*0.004;
  const S=[['s1',0,4.6],['s2',4.6,9.2],['s3',9.2,14.2],['s4',14.2,18.4],['s5',18.4,22.0],['s6',22.0,25.2]];
  for(const [id,a,b] of S){{const e=env(t,a,b);const el=$(id);el.style.opacity=e;el.style.transform=`translateX(${{(1-eo((t-a)/.35))*120 - (t>b-.3? eo((t-b+.3)/.3)*120:0)}}px)`}}
  // S1 title
  L.forEach((l,i)=>{{const t0=.25+i*.14;const p=cl((t-t0)/.35);l.style.display='inline-block';l.style.opacity=cl((t-t0)/.1);
    l.style.transform=`translateY(${{(1-back(p))*-500}}px)`;l.style.textShadow=`0 0 ${{20+14*Math.sin(t*6+i)}}px #ff2fd0,0 0 60px #ff2fd0,0 12px 0 #3a0a55`}});
  if(t>1.05&&t<1.45) shake=18*(1.45-t)/.4;
  pop($('t2'),t,1.5);pop($('t3'),t,2.1);$('t4').style.opacity=cl((t-2.8)/.3);$('t4').style.transform=`translateY(${{(1-eo((t-2.8)/.4))*40}}px)`;
  // S2 game price
  $('pad').style.transform=`translateY(${{Math.sin(t*5)*14}}px) rotate(${{Math.sin(t*3)*6}}deg)`;
  $('p2').textContent=rupee(5999*eo((t-5.3)/1.3));
  pop($('ok'),t,6.9);$('ok').style.top='870px';
  $('c2').style.opacity=cl((t-7.4)/.3);
  // S3 total
  const k3=eo((t-9.9)/1.8);$('p3').textContent=rupee(5999+(70989-5999)*k3);
  const jit=t>9.9&&t<12.2? (k3*10):0;$('p3').style.transform=`translate(${{Math.sin(t*70)*jit}}px,${{Math.cos(t*60)*jit}}px) scale(${{1+ (t>11.7?0.12*Math.abs(Math.sin((t-11.7)*8)):0)}})`;
  $('tot').style.opacity=cl((t-11.7)/.2);
  cash.forEach((cs,i)=>{{const t0=9.9+i*0.14;const p=(t-t0)/1.4;if(p<0||p>1){{cs.style.opacity=0;return}}
    cs.style.opacity=1-p;cs.style.left=(520+Math.sin(i*2.1)*260*p)+'px';cs.style.top=(600-300*p+150*p*p)+'px';cs.style.transform=`rotate(${{(i%2?1:-1)*p*200}}deg)`}});
  $('wal').style.transform=`rotate(${{t>9.9&&t<11.8?Math.sin(t*40)*8:0}}deg)`;
  pop($('shock'),t,11.9);
  if(t>11.85&&t<12.15) shake=Math.max(shake,14);
  // S4 PC
  $('pc').style.transform=`translateY(${{(1-eo((t-14.4)/.5))*-300}}px)`;
  {{const p=cl((t-15.5)/.25);$('stamp').style.opacity=p;$('stamp').style.transform=`rotate(-8deg) scale(${{2.4-1.4*eo(p)}})`;}}
  if(t>15.72&&t<16.0) shake=Math.max(shake,16);
  $('c4').style.opacity=cl((t-16.4)/.3);
  // S5 Papa + chappal
  $('dad').style.transform=`translateY(${{Math.sin(t*4)*8}}px)`;pop($('bub'),t,18.9);
  {{const p=cl((t-19.9)/.7);$('chap').style.left=(-260+1100*p)+'px';$('chap').style.top=(930-140*Math.sin(p*Math.PI))+'px';$('chap').style.transform=`rotate(${{p*900}}deg)`;$('chap').style.opacity=p>0&&p<1?1:0;}}
  {{const hit=t>20.55&&t<21.0;$('kid').style.transform=hit?`translate(${{Math.sin(t*90)*18}}px,0) rotate(${{Math.sin(t*50)*14}}deg)`:'none';$('kid').style.opacity=cl((t-18.7)/.3)}}
  if(t>20.55&&t<20.8) shake=Math.max(shake,12);
  // S6 final
  $('phone').style.transform=`translateY(${{(1-back((t-22.1)/.5))*400}}px) rotate(${{Math.sin(t*3)*4}}deg)`;
  pop($('yt'),t,22.6);$('c6').style.opacity=cl((t-23.2)/.3);
  // camera
  $('world').style.transform=`translate(${{(Math.random()-.5)*shake}}px,${{(Math.random()-.5)*shake}}px) scale(${{zoom}})`;
  const fl=[1.05,4.6,9.2,11.9,14.2,15.6,18.4,22.0].map(x=>cl(1-Math.abs(t-x)/.12)*(x==1.05||x==11.9||x==15.6?.55:.25));
  $('flash').style.opacity=Math.max(...fl);
  document.body.style.opacity=Math.min(1,t/0.25+0.15);
}}
render(0);
</script></body></html>"""


def tone(f, d, a=1.0, dec=6):
    t = np.arange(int(d * SR)) / SR; return a * np.sin(2 * np.pi * f * t) * np.exp(-t * dec)


def noise(d, lo, hi, dec=10):
    n = int(d * SR); t = np.arange(n) / SR
    x = sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), np.random.default_rng(3).standard_normal(n))
    return x / (np.max(np.abs(x)) + 1e-9) * np.exp(-t * dec)


def audio(path):
    n = int(DUR * SR); out = np.zeros((n, 2))
    sr, m = wavfile.read(os.path.join(ROOT, "assets/music/future_bass.wav")); m = m.astype(np.float64) / 32768
    m = m[:n]; env = np.ones(len(m)); fo = int(1.8 * SR); env[-fo:] = np.linspace(1, 0.15, fo)
    out[:len(m)] += m * env[:, None] * 0.55

    def add(x, t, g=1.0):
        if x.ndim == 1: x = np.stack([x, x], 1)
        i = int(t * SR); e = min(n, i + len(x)); out[i:e] += x[:e - i] * g

    def whoosh(d=0.6):
        k = np.linspace(0, 1, int(d * SR)); x = noise(d, 400, 5000, 0) * np.sin(np.pi * k) ** 2; return x

    def boom():
        t = np.arange(int(1.0 * SR)) / SR; f = 110 * np.exp(-t * 3) + 40
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4) + 0.5 * noise(1.0, 60, 400, 9)

    def ching(f=2400):
        return sum(tone(f * r, 0.5, a, 6 + 3 * j) for j, (r, a) in enumerate([(1, 1), (2.76, .5), (5.4, .25)]))

    for ts in (4.6, 9.2, 14.2, 18.4, 22.0): add(whoosh(), ts - 0.25, 0.35)
    add(boom(), 1.05, 0.9)
    for i in range(5): add(tone(900 + i * 120, 0.12, 1, 25), 0.25 + i * 0.14, 0.25)   # letter drops
    add(ching(2600), 1.5, 0.35); add(ching(3100), 2.1, 0.25)
    for k in range(12): add(ching(2000 + k * 120) * 0.6, 5.3 + k * 0.1, 0.18)        # coin counter
    for k, f in enumerate([784, 988, 1319]): add(tone(f, 0.5, 1, 5), 6.9 + k * 0.09, 0.3)  # success
    for k in range(18): add(tone(600 + k * 70, 0.08, 1, 30), 9.9 + k * 0.1, 0.22)    # rising register beeps
    t_al = np.arange(int(0.7 * SR)) / SR; alarm = np.sign(np.sin(2 * np.pi * 440 * t_al)) * (np.sin(2 * np.pi * 6 * t_al) > 0) * 0.5
    add(sosfilt(butter(2, 3000, fs=SR, output="sos"), alarm), 11.8, 0.35); add(boom(), 11.9, 0.6)
    add(boom(), 15.65, 0.9); add(noise(0.25, 200, 2500, 18), 15.65, 0.5)               # stamp thud
    add(tone(196, 0.9, 1, 3) + tone(185, 0.9, 1, 3), 16.4, 0.25)                        # sad trombone-ish
    add(tone(1200, 0.15, 1, 20), 18.9, 0.3)                                            # bubble pop
    add(whoosh(0.7), 19.9, 0.6); add(noise(0.18, 800, 6000, 25), 20.58, 1.0); add(boom(), 20.58, 0.35)  # chappal thwack
    for k, f in enumerate([523, 659, 784, 1047]): add(tone(f, 0.35, 1, 7), 22.6 + k * 0.08, 0.25)
    out = out / max(1.0, np.max(np.abs(out)) / 0.95)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype("<i2").tobytes())


def main(out, preview=None):
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(); open(f"{tmp}/p.html", "w").write(page())
    exe = os.environ.get("CHROMIUM_PATH") or None
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe); pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(f"file://{tmp}/p.html"); pg.wait_for_timeout(800)
        if preview:
            for t in preview:
                pg.evaluate(f"render({t})"); pg.screenshot(path=f"/tmp/gta_prev_{t}.png"); print(f"/tmp/gta_prev_{t}.png")
            b.close(); return
        for i in range(int(DUR * FPS)):
            pg.evaluate(f"render({i / FPS})"); pg.screenshot(path=f"{tmp}/f{i:04d}.jpg", type="jpeg", quality=90)
        b.close()
    audio(f"{tmp}/a.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.jpg", "-i", f"{tmp}/a.wav",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    add_cta(out, out, y=1350)
    shutil.rmtree(tmp); print(out)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        main(None, [float(x) for x in sys.argv[sys.argv.index("--preview") + 1:]])
    else:
        main(sys.argv[1])
