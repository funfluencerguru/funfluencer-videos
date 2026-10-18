import sys, numpy as np, wave, subprocess, os
sr=44100;TT=18.0
def audio(i,sfx,path):
    n=int(sr*TT);out=np.zeros(n);rng=np.random.default_rng(100+i)
    def add(s,st):
        a=int(st*sr);b=min(n,a+len(s));
        if a<n: out[a:b]+=s[:b-a]
    def tone(f,d,bass=False,amp=.22):
        t=np.arange(int(sr*d))/sr
        if bass: return .3*np.exp(-t*5)*(1-np.exp(-t*300))*(np.sin(2*np.pi*f*t)+.3*np.sin(4*np.pi*f*t))
        return amp*np.exp(-t*9)*(1-np.exp(-t*400))*(np.sin(2*np.pi*f*t)+.4*np.sin(4*np.pi*f*t)+.15*np.sin(6*np.pi*f*t))
    bpm=[112,120,128,136][i%4];step=60/bpm/2
    root=[1,1.122,1.26,1.189,1.335][i%5]
    scale=[f*root for f in [349.23,392,466.16,523.25,587.33,698.46]]
    pats=[[2,4,3,2,0,1,2,-1,3,5,4,3,1,2,3,-1],[0,2,4,2,0,2,5,-1,4,3,2,1,0,-1,2,-1],[4,4,2,3,5,3,1,-1,2,2,0,1,3,1,0,-1]]
    pat=pats[i%3];bass=[130.81*root,196*root,174.61*root,196*root]
    k=0;t0=0.0
    while t0<TT-.3:
        p=pat[k%len(pat)]
        if p>=0: add(tone(scale[p],.35),t0)
        if k%2==0: add(tone(bass[(k//2)%4],.5,True),t0)
        k+=1;t0+=step
    def beeps():
        P=[]
        for _ in range(3):
            t=np.arange(int(sr*.12))/sr
            P+= [.35*np.sign(np.sin(2*np.pi*1760*t))*np.minimum(1,(.12-t)/.02),np.zeros(int(sr*.1))]
        return np.concatenate(P)
    def growl(d):
        t=np.arange(int(sr*d))/sr;f=110-45*t/d;ph=2*np.pi*np.cumsum(f)/sr
        am=.55+.45*np.sin(2*np.pi*(9+6*t/d)*t)
        nz=np.convolve(rng.standard_normal(len(t)),np.ones(40)/40,mode="same")*1.5
        return .55*np.minimum(1,t/.08)*np.minimum(1,(d-t)/.25)*am*((np.sin(ph)+.6*np.sin(2*ph)+.5*np.sin(3*ph+1))*.7+nz*.5)
    def boing(d=.6):
        t=np.arange(int(sr*d))/sr;f=300+250*np.sin(2*np.pi*8*t)*np.exp(-t*4);ph=2*np.pi*np.cumsum(f)/sr
        return .45*np.exp(-t*4)*np.sin(ph)
    for st in (2.8,8.4):
        if sfx=="beeps": add(beeps(),st)
        elif sfx=="growl": add(growl(1.6),st)
        else: add(boing(),st);add(boing(),st+.7)
    def trom(f0,f1,d,vib=False):
        t=np.arange(int(sr*d))/sr;f=f0+(f1-f0)*t/d
        if vib: f=f*(1+.02*np.sin(2*np.pi*6*t))
        ph=2*np.pi*np.cumsum(f)/sr
        return .22*np.minimum(1,t/.05)*np.minimum(1,(d-t)/.08)*sum(np.sin(h*ph)/h for h in range(1,9))
    st=13.2
    for f,d in [(233,.5),(220,.5),(208,.5)]: add(trom(f,f*.985,d),st);st+=d+.03
    add(trom(196,150,1.7,True),st)
    out*=.9/np.max(np.abs(out));fd=int(sr*.8);out[-fd:]*=np.linspace(1,0,fd)
    with wave.open(path,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((out*32767).astype(np.int16).tobytes())
def html(i,t):
    slug,bub,prop,shape,head,cta,sfx=t
    mouth=["M238 292 Q262 280 288 292","M240 290 Q262 305 286 290","M242 292 L284 292"][i%3]
    shp=('<circle cx="760" cy="600" r="90"></circle>' if shape=="circle" else '<path d="M670 520 L850 520 L850 680 L670 680 Z"></path>')
    if SLEEPY:
        EYES='<path d="M224 246 Q238 258 252 246 M274 244 Q288 256 302 244" stroke-width="4"></path><text x="330" y="215" font-size="44" fill="#1c2aa8">z</text><text x="360" y="185" font-size="36" fill="#1c2aa8">z</text>'
        mouth="M242 296 Q262 302 284 296"
    else:
        EYES='<circle cx="238" cy="245" r="6" fill="#1c2aa8"></circle><circle cx="288" cy="243" r="6" fill="#1c2aa8"></circle><path d="M214 224 L252 230 M274 228 L312 222" stroke-width="4"></path>'
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0}}</style></head><body>
<div style="position:relative;width:1080px;height:1920px;overflow:hidden;background-color:#f5f2e9;background-image:repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0px,rgba(0,0,0,0) 63px,#b9c8e6 63px,#b9c8e6 65px);font-family:Carlito,'DejaVu Sans',sans-serif;color:#1c2aa8">
<div style="position:absolute;left:118px;top:0;width:3px;height:1920px;background:#e4806f"></div>
<div style="position:absolute;left:128px;top:0;width:3px;height:1920px;background:#e4806f"></div>
<svg style="position:absolute;left:40px;top:200px" viewBox="0 0 1000 800" width="1000" height="800">
<g fill="none" stroke="#1c2aa8" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">
<path d="M40 730 L960 734"></path>
<circle cx="260" cy="250" r="75"></circle>
{EYES}<path d="{mouth}" stroke-width="4"></path>
<path d="M260 325 L260 520 M260 520 L200 720 M260 520 L330 720"></path>
<path d="M260 370 L350 440 L520 560 M260 370 L180 450 L150 380"></path>
{shp}
<path d="M120 90 q0 -50 80 -50 h420 q80 0 80 50 q0 50 -80 50 h-420 q-80 0 -80 -50 Z" stroke-width="4"></path>
<circle cx="190" cy="165" r="10"></circle><circle cx="215" cy="200" r="6"></circle>
</g>
<g fill="#1c2aa8" font-family="Carlito, DejaVu Sans, sans-serif">
<text x="410" y="100" font-size="42" text-anchor="middle">{bub}</text>
<text x="760" y="610" font-size="40" text-anchor="middle">{prop}</text>
</g></svg>
<div style="position:absolute;left:170px;top:1055px;width:780px;font-size:62px;font-weight:700;line-height:1.12">{head}</div>
<div style="position:absolute;left:170px;top:1470px;width:520px;font-size:42px;line-height:1.2">{cta}</div>
<img src="{LOGO}" style="position:absolute;left:760px;top:1400px;width:210px;height:210px">
</div></body></html>'''

LOGO=""
SLEEPY=False
if __name__=="__main__":
    import argparse
    from playwright.sync_api import sync_playwright
    a=argparse.ArgumentParser(description="Make an 18s funfluencer doodle reel")
    a.add_argument("--slug",required=True);a.add_argument("--bubble",required=True)
    a.add_argument("--prop",required=True);a.add_argument("--shape",choices=["box","circle"],default="box")
    a.add_argument("--headline",required=True,help="use <br> for line breaks")
    a.add_argument("--cta",required=True);a.add_argument("--sfx",choices=["beeps","growl","boing"],default="boing")
    a.add_argument("--variant",type=int,default=0,help="any int; changes tune/face")
    a.add_argument("--sleepy",action="store_true",help="closed eyes + zzz");a.add_argument("--outdir",default="videos");a.add_argument("--date",required=True)
    g=a.parse_args();SLEEPY=g.sleepy
    here=os.path.dirname(os.path.abspath(__file__));logo=os.path.join(here,"..","assets","logo.png")
    LOGO="file://"+os.path.abspath(logo)
    os.makedirs(g.outdir,exist_ok=True);tmp="/tmp/reel_"+g.slug;os.makedirs(tmp,exist_ok=True)
    t=(g.slug,g.bubble,g.prop,g.shape,g.headline,g.cta,g.sfx)
    open(tmp+"/p.html","w").write(html(g.variant,t))
    with sync_playwright() as p:
        b=p.chromium.launch();pg=b.new_page(viewport={"width":1080,"height":1920})
        pg.goto("file://"+tmp+"/p.html");pg.screenshot(path=tmp+"/p.png");b.close()
    audio(g.variant,g.sfx,tmp+"/p.wav")
    out=f"{g.outdir}/{g.date}-{g.slug}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-framerate","30","-t","18","-i",tmp+"/p.png","-i",tmp+"/p.wav","-vf","format=yuv420p","-c:v","libx264","-tune","stillimage","-crf","20","-r","30","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",out],check=True)
    print(out)
