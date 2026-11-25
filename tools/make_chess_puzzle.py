#!/usr/bin/env python3
"""Weekly "Chess Puzzle" reel (Mate in 2 / Mate in 3), 1080x1920, 18 s.

    python3 tools/make_chess_puzzle.py --fen "<FEN>" --n 2 --date 2026-11-25 --slug mate2-white-01 [--verify-only]

1. Verifies the puzzle with an exact full-width brute-force solver (python-chess, no engine):
   legal position, game not over, no shorter mate, forced mate in exactly N, UNIQUE key move.
   Aborts (exit 2) if any check fails. Prints the main line in SAN.
2. Renders frames with Playwright (1080x1920, dsf 1): title card 2 s, puzzle frame with countdown 12..0 (13 s),
   end card 3 s. Side to move is always at the bottom. Logo assets/logo.png at logo_box(190, 30).
   Pieces: python-chess built-in SVG pieces; green/cream board. Never shows the solution.
3. Soft ticking audio made with numpy, encodes H.264/AAC 30 fps, burns the Like/Share/Follow tag
   (tools/brand.py add-cta, last 4 s, y 1455) and writes videos/<date>-chess-<slug>.mp4 +
   images/<date>-chess-<slug>-cover.jpg. Prints a JSON summary (solution etc.) at the end.
Log each run in tools/chess-log.csv (date,fen,side,mate_in,solution,slug).
"""
import argparse, base64, glob, json, os, subprocess, sys, tempfile, wave
import chess, chess.svg

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
from brand import logo_box, add_cta  # noqa: E402

W, H, FPS = 1080, 1920, 30
CTA_Y = 1455


# ---------------------------------------------------------------- solver
def can_mate(b, n):
    """Side to move can force mate within n of its own moves."""
    if n <= 0:
        return False
    for m in list(b.legal_moves):
        b.push(m)
        ok = forced(b, n)
        b.pop()
        if ok:
            return True
    return False


def forced(b, n):
    """Attacker just moved (n counts that move); every defence loses to mate within the remaining n-1 moves."""
    if b.is_checkmate():
        return True
    if n <= 1 or b.is_game_over():
        return False
    for r in list(b.legal_moves):
        b.push(r)
        ok = can_mate(b, n - 1)
        b.pop()
        if not ok:
            return False
    return True


def mate_len(b, maxn):
    for k in range(1, maxn + 1):
        if can_mate(b, k):
            return k
    return None


def verify(fen, n):
    b = chess.Board(fen)
    rep = {"fen": fen, "n": n, "side": "white" if b.turn else "black"}
    errs = []
    if not b.is_valid():
        errs.append(f"illegal position ({b.status()})")
    if b.is_game_over():
        errs.append("game already over")
    if not errs:
        for k in range(1, n):
            if can_mate(b, k):
                errs.append(f"shorter mate in {k} exists")
                break
        keys = []
        for m in list(b.legal_moves):
            b.push(m)
            ok = forced(b, n)
            b.pop()
            if ok:
                keys.append(m)
        rep["keys"] = [b.san(m) for m in keys]
        if not keys:
            errs.append(f"no forced mate in {n}")
        elif len(keys) > 1:
            errs.append(f"key not unique: {rep['keys']}")
        else:
            rep["solution"], rep["main_defence"] = main_line(b, keys[0], n)
    rep["errors"] = errs
    rep["ok"] = not errs
    return rep


def main_line(b, key, n):
    """Main line in SAN: key, then the toughest defence (longest resistance; captures/checks first), etc."""
    b = b.copy()
    defences = []
    mv, left = key, n
    while True:
        b.push(mv)
        if b.is_checkmate() or left <= 1:
            break
        best, bestscore = None, None
        for r in list(b.legal_moves):
            b.push(r)
            k = mate_len(b, left - 1) or 99
            b.pop()
            score = (k, b.is_capture(r), b.gives_check(r))
            if bestscore is None or score > bestscore:
                best, bestscore = r, score
        defences.append(b.san(best))
        b.push(best)
        left -= 1
        mv = next(m for m in list(b.legal_moves) if _mates_in(b, m, left))
    return _fmt(b), defences


def _mates_in(b, m, left):
    b.push(m)
    ok = forced(b, left)
    b.pop()
    return ok


def _fmt(end_board):
    """Re-print the played line from the final board's move stack in standard SAN numbering."""
    stack = end_board.move_stack
    b = end_board.root()
    out = []
    for i, m in enumerate(stack):
        san = b.san(m)
        if b.turn == chess.WHITE:
            out.append(f"{b.fullmove_number}. {san}")
        elif i == 0:
            out.append(f"{b.fullmove_number}... {san}")
        else:
            out.append(san)
        b.push(m)
    return " ".join(out)


# ---------------------------------------------------------------- rendering
def _chromium(p):
    exe = os.environ.get("CHROMIUM_PATH") or next(iter(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")), None)
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(executable_path=exe)


def _b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def board_svg(fen, size=936):
    b = chess.Board(fen)
    colors = {"square light": "#EEEED2", "square dark": "#769656", "margin": "#262421", "coord": "#EEEED2"}
    return chess.svg.board(b, size=size, orientation=b.turn, coordinates=True, colors=colors)


CSS = """
@font-face{font-family:Inter;src:url('file://%(repo)s/assets/fonts/Inter-ExtraBold.otf');font-weight:800}
@font-face{font-family:Inter;src:url('file://%(repo)s/assets/fonts/Inter-Bold.otf');font-weight:700}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;font-family:Inter,'Noto Color Emoji',sans-serif;color:#fff;
 background:radial-gradient(ellipse at 50%% 35%%,#4a3424 0%%,#2c1f16 45%%,#17110d 100%%)}
.grain{position:absolute;inset:0;opacity:.18;background:repeating-linear-gradient(92deg,rgba(0,0,0,.35) 0 3px,rgba(255,255,255,.03) 3px 9px,rgba(0,0,0,.2) 9px 14px)}
.abs{position:absolute}
.hl{left:0;right:0;top:46px;text-align:center}
.hl span{display:inline-block;background:#FFE14D;color:#151515;font-weight:800;font-size:64px;padding:10px 32px 14px;border-radius:14px;
 transform:rotate(-1.2deg);box-shadow:0 8px 0 rgba(0,0,0,.35)}
.sub{left:0;right:0;top:186px;text-align:center;font-weight:700;font-size:42px;color:#FFF3D6}
.board{left:%(bx)dpx;top:%(by)dpx;width:%(bw)dpx;height:%(bw)dpx;border:12px solid #7a5230;border-radius:26px;overflow:hidden;
 box-shadow:0 0 0 4px #c89a5b,0 24px 50px rgba(0,0,0,.6)}
.board svg{display:block}
.pill{height:104px;border-radius:52px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:46px;letter-spacing:.5px;
 box-shadow:0 8px 0 rgba(0,0,0,.35)}
.pw{background:#fff;color:#111;border:5px solid #111}
.pb{background:#111;color:#fff;border:5px solid #fff}
.ring{width:150px;height:150px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:68px;color:#fff}
.ans{left:0;right:0;text-align:center;font-weight:800;font-size:50px;color:#FFE14D}
.logo{left:%(lx)dpx;top:%(ly)dpx;width:%(ls)dpx;height:%(ls)dpx}
.big{left:40px;right:40px;text-align:center;font-weight:800}
"""


def page(body, ctx):
    logo = f'<img class="abs logo" src="data:image/png;base64,{ctx["logo64"]}">'
    return f"<html><head><meta charset='utf-8'><style>{CSS % ctx}</style></head><body><div class='grain'></div>{body}{logo}</body></html>"


def pill_html(side, n, left, top, width):
    cls = "pw" if side == "white" else "pb"
    return f'<div class="abs pill {cls}" style="left:{left}px;top:{top}px;width:{width}px">{side.upper()} TO MOVE - Mate in {n}</div>'


def ring_html(sec, total, left, top):
    frac = sec / total
    deg = int(360 * frac)
    return (f'<div class="abs ring" style="left:{left}px;top:{top}px;'
            f'background:radial-gradient(circle,#1b1b1b 0 57%,transparent 58%),conic-gradient(#ff3b3b 0 {deg}deg,#4a2a2a {deg}deg 360deg);'
            f'box-shadow:0 0 0 5px #ff3b3b,0 8px 20px rgba(0,0,0,.5)">{sec}</div>')


def puzzle_body(ctx, sec):
    n, side = ctx["n"], ctx["side"]
    by, bw = ctx["by"], ctx["bw"]
    row = by + bw + 30
    return (f'<div class="abs hl"><span>Chess Puzzle ♟️ Mate in {n}!</span></div>'
            f'<div class="abs sub">{ctx["hook"]}</div>'
            f'<div class="abs board">{ctx["svg"]}</div>'
            + pill_html(side, n, 50, row + 10, 790)
            + ring_html(sec, 12, 875, row - 13)
            + f'<div class="abs ans" style="top:{row + 126}px">Answer comment mein! 👇</div>')


def title_body(ctx):
    n, side = ctx["n"], ctx["side"]
    return (f'<div class="abs big" style="top:430px;font-size:140px;line-height:1.1">Chess<br>Puzzle! ♟️</div>'
            f'<div class="abs big" style="top:800px"><span style="display:inline-block;background:#FFE14D;color:#151515;font-size:80px;white-space:nowrap;'
            f'padding:14px 36px 20px;border-radius:18px;transform:rotate(-2deg);box-shadow:0 10px 0 rgba(0,0,0,.35)">Mate in {n} dhoondo 👀</span></div>'
            f'<div class="abs big" style="top:1030px;font-size:46px;color:#FFF3D6;font-weight:700">Timer 12 second ka hai... ready? ⏱️</div>'
            + pill_html(side, n, 145, 1180, 790))


def end_body(ctx):
    return ('<div class="abs big" style="top:420px;font-size:120px;line-height:1.12">Mila<br>checkmate? 🤔</div>'
            '<div class="abs big" style="top:800px"><span style="display:inline-block;background:#FFE14D;color:#151515;font-size:84px;'
            'padding:14px 40px 20px;border-radius:18px;transform:rotate(-1.5deg);box-shadow:0 10px 0 rgba(0,0,0,.35)">Comment karo! 👇</span></div>'
            '<div class="abs big" style="top:1010px;font-size:62px;color:#FFF3D6">Answer first comment mein 💬</div>'
            '<div class="abs big" style="top:1150px;font-size:44px;color:#d9c7a8;font-weight:700">Save karo, dost ko challenge karo! ♟️</div>')


def render(fen, n, work, hook):
    from playwright.sync_api import sync_playwright
    b = chess.Board(fen)
    lx, ly, ls = logo_box(190, 30)
    bw = 960
    ctx = {"repo": REPO, "n": n, "side": "white" if b.turn else "black", "hook": hook,
           "bx": (W - bw) // 2, "by": 262, "bw": bw, "lx": lx, "ly": ly, "ls": ls,
           "svg": board_svg(fen, bw - 24), "logo64": _b64(os.path.join(REPO, "assets", "logo.png"))}
    shots = {}
    with sync_playwright() as p:
        br = _chromium(p)
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        def shot(name, body):
            path = os.path.join(work, name + ".png")
            pg.set_content(page(body, ctx))
            pg.wait_for_timeout(250)
            pg.screenshot(path=path)
            shots[name] = path
        shot("title", title_body(ctx))
        for s in range(12, -1, -1):
            shot(f"puzzle_{s:02d}", puzzle_body(ctx, s))
        shot("end", end_body(ctx))
        br.close()
    return shots


# ---------------------------------------------------------------- audio + encode
def make_audio(path, total):
    import numpy as np
    sr = 44100
    t_all = np.zeros(int(sr * total))
    def add(t0, sig):
        i = int(t0 * sr); t_all[i:i + len(sig)] += sig[:len(t_all) - i]
    def tone(f, dur, amp, decay):
        t = np.arange(int(sr * dur)) / sr
        return amp * np.sin(2 * np.pi * f * t) * np.exp(-t * decay)
    # intro shimmer
    for k, f in enumerate([523.25, 659.25, 783.99]):
        add(0.15 + 0.12 * k, tone(f, 0.6, 0.18, 6))
    # soft ticks 2..15 s (tick / tock), last 3 slightly louder
    for i in range(13):
        t0 = 2.0 + i
        f = 1800 if i % 2 == 0 else 1400
        amp = 0.16 if i < 10 else 0.24
        click = tone(f, 0.06, amp, 70) + tone(f * 0.5, 0.06, amp * 0.5, 90)
        add(t0, click)
    # end chime
    for k, f in enumerate([783.99, 987.77, 1174.66]):
        add(15.05 + 0.1 * k, tone(f, 1.2, 0.16, 3))
    t_all = np.clip(t_all, -0.9, 0.9)
    data = (t_all * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())


def encode(shots, work, out):
    seq = [("title", 2.0)] + [(f"puzzle_{s:02d}", 1.0) for s in range(12, -1, -1)] + [("end", 3.0)]
    total = sum(d for _, d in seq)
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for name, d in seq:
            f.write(f"file '{shots[name]}'\nduration {d}\n")
        f.write(f"file '{shots[seq[-1][0]]}'\n")
    wav = os.path.join(work, "tick.wav")
    make_audio(wav, total)
    raw = os.path.join(work, "raw.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-vf", "fps=30,tpad=stop_mode=clone:stop_duration=4,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
                    "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                    "-t", f"{total:.2f}", "-movflags", "+faststart", raw], check=True)
    add_cta(raw, out, y=CTA_Y, dur=4.0)
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--fen", required=True); a.add_argument("--n", type=int, required=True)
    a.add_argument("--date"); a.add_argument("--slug")
    a.add_argument("--hook", default="Sirf 1% log 12 second mein solve karte hain!")
    a.add_argument("--verify-only", action="store_true")
    g = a.parse_args()
    rep = verify(g.fen, g.n)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if not rep["ok"]:
        sys.exit(2)
    if g.verify_only:
        return
    work = tempfile.mkdtemp(prefix="chesspz_")
    shots = render(g.fen, g.n, work, g.hook)
    out = os.path.join(REPO, "videos", f"{g.date}-chess-{g.slug}.mp4")
    cover = os.path.join(REPO, "images", f"{g.date}-chess-{g.slug}-cover.jpg")
    os.makedirs(os.path.dirname(cover), exist_ok=True)
    from PIL import Image
    Image.open(shots["puzzle_12"]).convert("RGB").save(cover, quality=90)
    encode(shots, work, out)
    print(json.dumps({"video": out, "cover": cover, "work": work, "puzzle_png": shots["puzzle_12"],
                      "solution": rep["solution"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
