#!/usr/bin/env python3
"""Chess puzzle reel (1080x1920, 20 s, no clock): "Mate in N" on a green/cream online-chess style board.

Usage:
    python3 tools/make_chess.py tools/chess-specs/<date>-<slug>.json            # video + answer card
    python3 tools/make_chess.py spec.json --preview 3 16                         # PNG frames only

Spec (JSON):
  {"date": "2026-11-25", "slug": "smothered-queen-sac",
   "fen": "<FEN>",                 # side to move is read from the FEN
   "mate_in": 2,
   "last_move": "d8b6",            # optional: opponent's previous move, highlighted like an online board
   "solution": ["Qg8+", "Rxg8", "Nf7#"],   # main line in SAN, checked against the position
   "answer_note": "Smothered mate!",       # short line for the answer card
   "names": {"white": "White", "black": "Black"}}

Rules this tool enforces (owner request, 2026-11-25):
  * The board is 2D and the SIDE TO MOVE IS ALWAYS AT THE BOTTOM (Black to move -> board flipped).
  * A big "WHITE TO MOVE" / "BLACK TO MOVE" chip is always on screen.
  * No clock / countdown / time-up overlay: the board stays fully visible for all 20 s (owner, 2026-11-25).
  * The answer is NOT shown in the reel; it goes in the comments. The tool writes an answer card
    (images/<date>-chess-<slug>-answer.jpg) and the answer text (printed + saved next to it as .txt).
  * The puzzle is verified by brute force before rendering: the first move of `solution` must be the ONLY
    move that forces mate in `mate_in`, and the line must end in checkmate. Rendering stops otherwise.
No site logos or brand names: the look is just the common green/cream board colours.
Pieces: python-chess built-in SVG set. Needs python `chess` (pure python; if pip cannot build it on 3.11, run
`pip install chess` and add its site-packages folder to PYTHONPATH), playwright, numpy, Pillow, ffmpeg.
"""
import argparse, base64, glob, json, os, subprocess, sys, tempfile, wave
import numpy as np
import chess, chess.svg
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand import logo_box, add_cta  # noqa: E402

SR = 44100
FPS = 10
TOTAL = 20.0               # owner rule 2026-11-25: 20 s, NO clock/timer, board never covered
LIGHT, DARK = "#ebecd0", "#739552"
HL_LIGHT, HL_DARK = "#f5f682", "#b9ca43"


# ---------------------------------------------------------------- puzzle check
def _forced(b, n):
    if b.is_checkmate():
        return True
    if n == 0 or b.is_game_over():
        return False
    for r in list(b.legal_moves):
        b.push(r)
        ok = any(_mates(b, m, n) for m in list(b.legal_moves))
        b.pop()
        if not ok:
            return False
    return True


def _mates(b, m, n):
    b.push(m); ok = _forced(b, n - 1); b.pop()
    return ok


def verify(spec):
    b = chess.Board(spec["fen"])
    n = spec["mate_in"]
    for k in range(1, n):
        quick = [b.san(m) for m in b.legal_moves if _mates(b, m, k)]
        if quick:
            sys.exit(f"puzzle is already mate in {k}: {quick}")
    keys = [b.san(m) for m in b.legal_moves if _mates(b, m, n)]
    if keys != [spec["solution"][0]]:
        sys.exit(f"key moves for mate in {n}: {keys} (spec says {spec['solution'][0]}); need exactly one")
    line = b.copy()
    for san in spec["solution"]:
        line.push_san(san)
    if not line.is_checkmate():
        sys.exit("solution line does not end in checkmate")
    print("verified: unique key", keys[0], "| line", " ".join(spec["solution"]))
    return b


def answer_text(spec, b):
    parts, t = [], b.copy()
    for i, san in enumerate(spec["solution"]):
        if t.turn == chess.WHITE:
            parts.append(f"{t.fullmove_number}. {san}")
        else:
            parts.append(f"{t.fullmove_number}... {san}" if i == 0 else san)
        t.push_san(san)
    return " ".join(parts)


# ---------------------------------------------------------------- drawing
def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def piece_uri(p):
    svg = chess.svg.piece(p, size=45)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def board_html(b, size, flip, highlight=(), arrows=()):
    """Plain HTML/SVG board. flip=True puts Black at the bottom."""
    sq = size / 8
    cells, labels, pieces = [], [], []
    for s in chess.SQUARES:
        f, r = chess.square_file(s), chess.square_rank(s)
        col, row = (7 - f, r) if flip else (f, 7 - r)
        light = (f + r) % 2 == 1
        fill = (HL_LIGHT if light else HL_DARK) if s in highlight else (LIGHT if light else DARK)
        x, y = col * sq, row * sq
        cells.append(f'<rect x="{x}" y="{y}" width="{sq}" height="{sq}" fill="{fill}"/>')
        tc = DARK if light else LIGHT
        if col == 0:
            labels.append(f'<text x="{x + sq * .05:.0f}" y="{y + sq * .24:.0f}" fill="{tc}" font-size="{sq * .21:.0f}" font-weight="800">{r + 1}</text>')
        if row == 7:
            labels.append(f'<text x="{x + sq * .82:.0f}" y="{y + sq * .93:.0f}" fill="{tc}" font-size="{sq * .21:.0f}" font-weight="800">{"abcdefgh"[f]}</text>')
        p = b.piece_at(s)
        if p:
            pieces.append(f'<image href="{piece_uri(p)}" x="{x}" y="{y}" width="{sq}" height="{sq}"/>')
    arr = []
    for i, (a, c) in enumerate(arrows):
        def centre(s):
            f, r = chess.square_file(s), chess.square_rank(s)
            col, row = (7 - f, r) if flip else (f, 7 - r)
            return (col + .5) * sq, (row + .5) * sq
        (x1, y1), (x2, y2) = centre(a), centre(c)
        d = np.hypot(x2 - x1, y2 - y1); ux, uy = (x2 - x1) / d, (y2 - y1) / d
        x2s, y2s = x2 - ux * sq * .32, y2 - uy * sq * .32
        arr.append(f'<line x1="{x1}" y1="{y1}" x2="{x2s}" y2="{y2s}" stroke="#ff9f1a" stroke-opacity=".9" '
                   f'stroke-width="{sq * .2}" marker-end="url(#ah)" stroke-linecap="round"/>')
        arr.append(f'<circle cx="{(x1 + x2) / 2}" cy="{(y1 + y2) / 2}" r="{sq * .24}" fill="#1f1d1b" stroke="#ff9f1a" stroke-width="5"/>'
                   f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 + sq * .1:.0f}" text-anchor="middle" font-size="{sq * .3:.0f}" font-weight="900" fill="#fff">{i + 1}</text>')
    defs = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="3" refY="5" markerWidth="2.6" markerHeight="2.6" orient="auto">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#ff9f1a" fill-opacity=".9"/></marker></defs>')
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
            f'style="font-family:Inter">{defs}{"".join(cells)}{"".join(labels)}{"".join(pieces)}{"".join(arr)}</svg>')


def fonts_css():
    css = ""
    for w, f in ((500, "Inter-Medium"), (700, "Inter-Bold"), (800, "Inter-ExtraBold"), (900, "Inter-ExtraBold")):
        css += (f'@font-face{{font-family:Inter;font-weight:{w};src:url(data:font/otf;base64,'
                f'{b64(os.path.join(ROOT, "assets/fonts", f + ".otf"))})}}')
    return css


def player_bar(name, colour):
    icon = f'<img src="{piece_uri(chess.Piece(chess.KING, colour == "white"))}">'
    return (f'<div class="bar"><div class="av {colour}">{icon}</div><div class="nm">{name}</div>'
            '</div>')


def reel_page(spec, b, logo):
    flip = b.turn == chess.BLACK
    side = "WHITE" if b.turn == chess.WHITE else "BLACK"
    names = spec.get("names", {"white": "White", "black": "Black"})
    hl = ()
    if spec.get("last_move"):
        m = chess.Move.from_uci(spec["last_move"]); hl = (m.from_square, m.to_square)
    top_col, bot_col = ("white", "black") if flip else ("black", "white")
    lx, ly, ls = logo_box(209, 30)
    chip_bg, chip_fg = ("#ffffff", "#1f1d1b") if side == "WHITE" else ("#1f1d1b", "#ffffff")
    return f'''<html><head><meta charset="utf-8"><style>{fonts_css()}
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;font-family:Inter,sans-serif;color:#fff;
background:radial-gradient(ellipse at 50% 35%,#3c3936 0%,#2b2926 55%,#1f1d1b 100%)}}
.head{{position:absolute;top:70px;left:0;right:0;text-align:center}}
.head .t{{display:inline-block;background:#81b64c;border-bottom:10px solid #45753c;border-radius:26px;padding:10px 54px 6px;
font-size:104px;font-weight:900;letter-spacing:2px;color:#fff;text-shadow:0 5px 0 rgba(0,0,0,.25)}}
.side{{position:absolute;top:250px;left:0;right:0;text-align:center}}
.side span{{display:inline-flex;align-items:center;gap:22px;background:{chip_bg};color:{chip_fg};border:5px solid #81b64c;
border-radius:60px;padding:10px 44px;font-size:56px;font-weight:900}}
.side img{{width:72px;height:72px}}
.bar{{position:absolute;left:40px;right:40px;height:78px;display:flex;align-items:center;gap:18px}}
.bar.top{{top:356px}}.bar.bot{{top:1452px}}
.av{{width:70px;height:70px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:56px}}
.av img{{width:60px;height:60px}}.av.white{{background:#e8e6e3}}.av.black{{background:#9e9b98}}
.nm{{font-size:40px;font-weight:800;flex:1;color:#e8e6e3}}
.board{{position:absolute;top:442px;left:40px;width:1000px;height:1000px;border-radius:8px;overflow:hidden;
box-shadow:0 18px 50px rgba(0,0,0,.55)}}
.hint{{position:absolute;top:1560px;left:40px;right:270px;font-size:46px;font-weight:800;line-height:1.25;color:#e8e6e3}}
.hint b{{color:#81b64c}}
.logo{{position:absolute;left:{lx}px;top:{ly}px;width:{ls}px;height:{ls}px}}
</style></head><body>
<div class="head"><span class="t" id="head">MATE IN {spec["mate_in"]}</span></div>
<div class="side"><span><img src="{piece_uri(chess.Piece(chess.KING, side == "WHITE"))}">{side} TO MOVE</span></div>
<div class="bar top">{player_bar(names[top_col], top_col)}</div>
<div class="board" id="board">{board_html(b, 1000, flip, hl)}</div>
<div class="bar bot">{player_bar(names[bot_col], bot_col)}</div>
<div class="hint" id="hint">Find the <b>checkmate in {spec["mate_in"]}</b>!<br>Answer in the comments &#128071;</div>
<img class="logo" src="data:image/png;base64,{logo}">
<script>
function setT(t){{
  const ip=Math.min(1,t/0.6), e=1-Math.pow(1-ip,3);
  document.getElementById('board').style.transform='scale('+(0.92+0.08*e)+')';
  document.getElementById('board').style.opacity=e;
  const hp=Math.min(1,Math.max(0,(t-0.2)/0.5));
  document.getElementById('head').style.transform='scale('+(hp<1?0.6+0.4*hp+0.12*Math.sin(hp*Math.PI):1)+')';
}}
</script></body></html>'''


def answer_page(spec, b, text):
    flip = b.turn == chess.BLACK
    side = "White" if b.turn == chess.WHITE else "Black"
    t, arrows = b.copy(), []
    for san in spec["solution"]:
        m = t.parse_san(san)
        if t.turn == b.turn:
            arrows.append((m.from_square, m.to_square))
        t.push(m)
    return f'''<html><head><meta charset="utf-8"><style>{fonts_css()}
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1350px;font-family:Inter,sans-serif;color:#fff;background:#262421;padding:44px 40px}}
h1{{font-size:64px;font-weight:900;color:#81b64c;text-align:center}}
.sub{{text-align:center;font-size:36px;font-weight:700;color:#cfcac4;margin:8px 0 26px}}
.main{{width:840px;height:840px;margin:0 auto;border-radius:8px;overflow:hidden}}
.line{{margin-top:28px;background:#1f1d1b;border:5px solid #81b64c;border-radius:24px;padding:26px 34px}}
.line .m{{font-size:58px;font-weight:900}}
.line .n{{font-size:38px;font-weight:700;color:#cfcac4;margin-top:12px;line-height:1.3}}
</style></head><body>
<h1>ANSWER: MATE IN {spec["mate_in"]}</h1>
<div class="sub">{side} to move &middot; {spec["date"]}</div>
<div class="main">{board_html(b, 840, flip, arrows=arrows)}</div>
<div class="line"><div class="m">{text}</div><div class="n">{spec.get("answer_note", "")}</div></div>
</body></html>'''


# ---------------------------------------------------------------- audio
def audio(path):
    n = int(SR * TOTAL); y = np.zeros(n)
    def add(at, sig):
        i = int(at * SR); y[i:i + len(sig)] += sig[:max(0, n - i)]
    m = np.arange(int(0.09 * SR)) / SR
    clack = 0.5 * np.sin(2 * np.pi * 900 * m) * np.exp(-m * 60) + 0.25 * np.random.default_rng(1).normal(size=len(m)) * np.exp(-m * 120)
    add(0.15, clack)
    pad = np.zeros(n); tt = np.arange(n) / SR
    for i, chord in enumerate([(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 293.66), (164.81, 207.65, 246.94)]):
        seg = (tt >= i * 5) & (tt < i * 5 + 5)           # 4 calm chords, 5 s each
        env = np.sin(np.pi * np.clip((tt - i * 5) / 5, 0, 1)) ** 0.6
        for f in chord:
            pad += np.where(seg, env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)), 0)
    y += 0.06 * pad * np.minimum(1, tt / 1.5) * np.minimum(1, (TOTAL - tt) / 1.5)
    y = np.clip(y, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype("<i2").tobytes())


def browser(p):
    exe = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")
    exe = os.environ.get("CHROMIUM_PATH") or (exe[0] if exe else None)
    return p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--preview", nargs="*", type=float)
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    b = verify(spec)
    text = answer_text(spec, b)
    slug = f'{spec["date"]}-chess-{spec["slug"]}'
    out = os.path.join(ROOT, "videos", slug + ".mp4")
    ans_img = os.path.join(ROOT, "images", slug + "-answer.jpg")
    tmp = tempfile.mkdtemp(prefix="chess_")
    logo = b64(os.path.join(ROOT, "assets", "logo.png"))
    with sync_playwright() as p:
        br = browser(p)
        pg = br.new_page(viewport={"width": 1080, "height": 1920})
        pg.set_content(reel_page(spec, b, logo))
        times = a.preview if a.preview is not None else [i / FPS for i in range(int(TOTAL * FPS))]
        for i, t in enumerate(times):
            pg.evaluate(f"setT({t})")
            pg.screenshot(path=f"{tmp}/{'p_%s' % t if a.preview is not None else 'f%04d' % i}.png")
        if a.preview is None:
            pa = br.new_page(viewport={"width": 1080, "height": 1350})
            pa.set_content(answer_page(spec, b, text))
            pa.screenshot(path=f"{tmp}/answer.png")
        br.close()
    if a.preview is not None:
        print("preview frames in", tmp); return
    from PIL import Image
    Image.open(f"{tmp}/answer.png").convert("RGB").save(ans_img, quality=92)
    with open(ans_img[:-4] + ".txt", "w") as f:
        f.write(f"Answer ({'White' if b.turn else 'Black'} to move, mate in {spec['mate_in']}): {text}\n{spec.get('answer_note', '')}\n")
    audio(f"{tmp}/a.wav")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                           "-i", f"{tmp}/a.wav", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "19", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out])
    add_cta(out, out, y=spec.get("cta_y", 1700), width=spec.get("cta_width", 760), x=spec.get("cta_x", 40))
    print("video:", out); print("answer card:", ans_img); print("answer:", text)


if __name__ == "__main__":
    main()
