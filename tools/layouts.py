"""Extra reel layouts for make_reel.py. Each returns SVG for a 1000x800 canvas
(placed at left 40, top 200 of the 1080x1920 frame). Ink colour comes from the background theme."""

THEMES = {
    # name: (css background, ink colour, extra decoration html, panel fill)
    "notebook": ("background-color:#f5f2e9;background-image:repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0px,rgba(0,0,0,0) 63px,#b9c8e6 63px,#b9c8e6 65px)", "#1c2aa8",
                 '<div style="position:absolute;left:118px;top:0;width:3px;height:1920px;background:#e4806f"></div><div style="position:absolute;left:128px;top:0;width:3px;height:1920px;background:#e4806f"></div>', "#ffffff"),
    "blackboard": ("background-color:#1f3d2f;background-image:radial-gradient(rgba(255,255,255,.06) 1px,transparent 1px);background-size:18px 18px", "#f3f1e4", "", "#2a4d3b"),
    "sticky": ("background-color:#ffe97a;background-image:linear-gradient(to bottom,rgba(255,255,255,.35),rgba(255,255,255,0) 20%)", "#3b2a8c", "", "#fff6b8"),
    "graph": ("background-color:#f7f9fb;background-image:linear-gradient(#cfe0f1 2px,transparent 2px),linear-gradient(90deg,#cfe0f1 2px,transparent 2px);background-size:54px 54px", "#14307a", "", "#ffffff"),
}


def tx(x, y, text, size=40, anchor="middle", weight=500, fill=None, lh=1.15):
    """Text; '|' makes a new line."""
    f = f' fill="{fill}"' if fill else ""
    out = f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" stroke="none"{f}>'
    for i, ln in enumerate(str(text).split("|")):
        out += f'<tspan x="{x}" dy="{0 if i == 0 else int(size * lh)}">{ln}</tspan>'
    return out + "</text>"


def face(mood, ink):
    if mood == "sleepy":
        return ('<path d="M-36 -4 Q-22 8 -8 -4 M14 -4 Q28 8 42 -4" stroke-width="4"/>'
                '<path d="M-20 44 Q0 52 22 44" stroke-width="4"/>'
                f'<text x="70" y="-40" font-size="44" stroke="none" fill="{ink}">z</text><text x="102" y="-72" font-size="34" stroke="none" fill="{ink}">z</text>')
    if mood == "angry":
        return (f'<circle cx="-24" cy="0" r="6" fill="{ink}"/><circle cx="26" cy="-2" r="6" fill="{ink}"/>'
                '<path d="M-48 -26 L-10 -18 M12 -20 L50 -28 M-22 50 Q2 38 28 50" stroke-width="4"/>')
    if mood == "shock":
        return (f'<circle cx="-24" cy="-4" r="9"/><circle cx="26" cy="-4" r="9"/><circle cx="-24" cy="-4" r="3" fill="{ink}"/><circle cx="26" cy="-4" r="3" fill="{ink}"/>'
                '<ellipse cx="2" cy="46" rx="12" ry="16"/>')
    # happy
    return (f'<circle cx="-24" cy="-2" r="6" fill="{ink}"/><circle cx="26" cy="-2" r="6" fill="{ink}"/>'
            '<path d="M-28 34 Q0 62 32 34" stroke-width="4"/>')


def extras(kind, ink):
    if kind == "girl":
        return ('<path d="M-70 -30 Q-110 -10 -96 30 M70 -30 Q110 -10 96 30" stroke-width="5"/>'
                '<circle cx="-98" cy="38" r="9"/><circle cx="98" cy="38" r="9"/><path d="M-30 -70 Q0 -90 30 -70" stroke-width="4"/>'
                '<path d="M-40 -10 L-48 -16 M36 -12 L44 -18" stroke-width="3"/>')
    if kind == "uncle":
        return ('<path d="M-34 30 Q0 18 36 30" stroke-width="7"/><circle cx="-24" cy="-2" r="17"/><circle cx="26" cy="-2" r="17"/><path d="M-7 -2 L9 -2" stroke-width="3"/>'
                '<path d="M-20 -78 Q0 -92 22 -78" stroke-width="4"/>')
    if kind == "aunty":
        return ('<circle cx="0" cy="-98" r="26"/><circle cx="0" cy="-22" r="4" fill="%s"/>' % ink +
                '<path d="M-72 -20 Q-70 -70 0 -76 Q70 -70 72 -20" stroke-width="4"/>')
    if kind == "kid":
        return '<path d="M-40 -66 Q0 -110 40 -66 Z" stroke-width="4"/><path d="M-4 -92 L-4 -104 M8 -90 L16 -102" stroke-width="3"/>'
    return '<path d="M-14 -74 Q-4 -96 6 -78 M6 -78 Q18 -92 24 -70" stroke-width="4"/>'  # boy tuft


def figure(cx, feet_y, kind="boy", mood="happy", scale=1.0, ink="#1c2aa8", arm="wave"):
    """Stick person. Local coords: head centre (0,-470), feet at y=0."""
    arms = {"wave": "M0 -395 L-80 -330 L-110 -400 M0 -395 L85 -320 L130 -280",
            "point": "M0 -395 L-85 -320 L-100 -260 M0 -395 L100 -380 L190 -400",
            "shrug": "M0 -395 L-90 -340 L-130 -380 M0 -395 L90 -340 L130 -380",
            "down": "M0 -395 L-70 -300 L-80 -230 M0 -395 L70 -300 L80 -230"}[arm]
    body = '<path d="M0 -395 L0 -200 M0 -200 L-62 0 M0 -200 L72 0"/>'
    if kind == "aunty":
        body = '<path d="M0 -395 L0 -230 M-55 0 L0 -250 L58 0 M-55 0 L58 0"/>'
    if kind == "uncle":
        body += '<path d="M0 -330 Q60 -290 0 -230" stroke-width="4"/>'
    return (f'<g transform="translate({cx},{feet_y}) scale({scale})" fill="none" stroke="{ink}" stroke-width="{5 / scale if scale < 1 else 5}" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="0" cy="-470" r="75"/><g transform="translate(0,-470)">{face(mood, ink)}{extras(kind, ink)}</g>'
            f'{body}<path d="{arms}"/></g>')


def bubble(x, y, w, h, text, tail_x, size=38, ink="#1c2aa8", fill="none"):
    """Speech bubble (x,y top-left); tail points down at tail_x."""
    r = 40
    path = (f'<path d="M{x + r} {y} H{x + w - r} Q{x + w} {y} {x + w} {y + r} V{y + h - r} Q{x + w} {y + h} {x + w - r} {y + h} '
            f'H{tail_x + 28} L{tail_x} {y + h + 62} L{tail_x - 8} {y + h} H{x + r} Q{x} {y + h} {x} {y + h - r} V{y + r} Q{x} {y} {x + r} {y} Z" '
            f'fill="{fill}" stroke-width="4"/>')
    lines = str(text).split("|")
    ty = y + h / 2 - (len(lines) - 1) * size * 0.58 + size * 0.34
    return path + tx(x + w / 2, int(ty), text, size, fill=ink)


def duo(d, ink, panel, k1, k2, m1, m2):
    return ('<path d="M40 730 L960 734" stroke-width="5"/>' +
            figure(250, 730, k1, m1, 0.82, ink, "wave") + figure(750, 730, k2, m2, 0.82, ink, "point") +
            bubble(30, 30, 460, 180, d.get("a", "..."), 250, 44, ink, panel) +
            bubble(510, 30, 460, 180, d.get("b", "..."), 750, 44, ink, panel))


def versus(d, ink, panel, k1, k2, m1, m2):
    out = ""
    for i, (x, title, text, kind, mood) in enumerate([
            (30, d.get("left_title", "Expectation"), d.get("left_text", ""), k1, m1),
            (510, d.get("right_title", "Reality"), d.get("right_text", ""), k2, m2)]):
        out += f'<path d="M{x} 30 H{x + 460} V760 H{x} Z" fill="{panel}" stroke-width="5"/>'
        out += tx(x + 230, 100, title, 52, weight=700, fill=ink)
        out += f'<path d="M{x + 60} 122 Q{x + 230} 108 {x + 400} 122" stroke-width="4"/>'
        out += tx(x + 230, 200, text, 44, fill=ink)
        out += figure(x + 230, 735, kind, mood, 0.55, ink, "shrug" if i else "wave")
    out += (f'<circle cx="500" cy="395" r="42" fill="{panel}" stroke-width="5"/>' + tx(500, 410, "VS", 36, weight=700, fill=ink))
    return out


def chat(d, ink, panel):
    msgs = d.get("msgs", [["them", "Kahan hai?"], ["me", "Bas 5 min mein aaya"]])[:4]
    out = f'<path d="M110 20 H890 V780 H110 Z" fill="{panel}" stroke-width="5"/><path d="M110 120 H890" stroke-width="4"/>'
    out += f'<circle cx="170" cy="70" r="30"/>' + tx(225, 82, d.get("name", "Dost"), 44, "start", 700, ink)
    y = 150
    for who, text in msgs:
        lines = str(text).split("|")
        h = 40 + 54 * len(lines)
        w = min(680, 70 + 27 * max(len(l) for l in lines))
        if who == "me":
            x = 870 - w
            out += f'<path d="M{x} {y} H{x + w} V{y + h} H{x} Z" fill="{ink}" fill-opacity=".14" stroke-width="4"/>'
        else:
            x = 130
            out += f'<path d="M{x} {y} H{x + w} V{y + h} H{x} Z" fill="none" stroke-width="4"/>'
        out += tx(x + w / 2, y + 56, text, 46, fill=ink)
        y += h + 24
    return out


def toplist(d, ink, panel):
    out = tx(500, 90, d.get("title", "Top 3"), 64, weight=700, fill=ink)
    out += f'<path d="M180 120 Q500 100 820 124" stroke-width="5"/>'
    for i, item in enumerate(d.get("items", ["", "", ""])[:3]):
        y = 250 + i * 190
        out += f'<circle cx="150" cy="{y}" r="58" fill="{panel}" stroke-width="5"/>' + tx(150, y + 24, str(i + 1), 70, weight=700, fill=ink)
        out += f'<path d="M240 {y - 62} H900 V{y + 62} H240 Z" fill="{panel}" stroke-width="4"/>'
        out += tx(570, y - 4 if "|" in item else y + 16, item, 50, fill=ink)
    return out


def vote(d, ink, panel):
    out = ""
    for x, letter, text in [(30, "A", d.get("a", "")), (530, "B", d.get("b", ""))]:
        out += f'<path d="M{x} 110 H{x + 440} V680 H{x} Z" fill="{panel}" stroke-width="5"/>'
        out += f'<circle cx="{x + 220}" cy="210" r="70"/>' + tx(x + 220, 238, letter, 84, weight=700, fill=ink)
        out += tx(x + 220, 430, text, 62, weight=700, fill=ink)
    out += f'<circle cx="500" cy="395" r="50" fill="{panel}" stroke-width="5"/>' + tx(500, 412, "ya", 46, weight=700, fill=ink)
    out += tx(500, 750, d.get("hint", "Comment mein A ya B batao!"), 40, fill=ink)
    return out


def scene(layout, d, theme, k1="boy", k2="uncle", m1="happy", m2="shock"):
    ink, panel = THEMES[theme][1], THEMES[theme][3]
    inner = {"duo": lambda: duo(d, ink, panel, k1, k2, m1, m2),
             "versus": lambda: versus(d, ink, panel, k1, k2, m1, m2),
             "chat": lambda: chat(d, ink, panel),
             "list": lambda: toplist(d, ink, panel),
             "vote": lambda: vote(d, ink, panel)}[layout]()
    return f'<g fill="none" stroke="{ink}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" font-family="Carlito, DejaVu Sans, sans-serif">{inner}</g>'
