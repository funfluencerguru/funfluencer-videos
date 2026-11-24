"""Spot-the-difference scene: sardi ki subah, gully mein alaav (winter bonfire). draw(changes) -> SVG 500x900.
Picture A = draw(set()), picture B = draw(set(DIFFS)). Each key in DIFFS is one deliberate change."""

SCENE = "Sardi ki subah ka alaav"
# key -> Hinglish answer line (in the order they appear top to bottom)
DIFFS = {
    "sock": "Rassi pe latka laal moza gayab hai",
    "window": "Ghar ki khidki ka top seedha se gol (arch) ho gaya",
    "cap": "Uncle ki monkey cap ka rang laal se purple ho gaya",
    "stripes": "Bachche ke sweater pe 2 ki jagah 3 stripes",
    "log": "Aag ke right side ek extra lakdi aa gayi",
}

S = 'stroke="#111" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'
T = 'stroke="#111" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"'


def draw(ch=frozenset()):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 900" width="500" height="900">',
         '<rect width="500" height="900" fill="#dde8f3"/>']
    # pale winter sun
    o.append(f'<circle cx="150" cy="95" r="42" fill="#fff3b0" {S}/>')
    # house (right)
    o.append(f'<rect x="250" y="140" width="270" height="440" fill="#f4a261" {S}/>')
    o.append(f'<rect x="240" y="122" width="280" height="30" fill="#e76f51" {S}/>')
    for y in (210, 300, 390, 480):  # bricks hint
        o.append(f'<line x1="262" y1="{y}" x2="292" y2="{y}" stroke="#c9733e" stroke-width="5"/>')
    # window
    if "window" in ch:
        o.append(f'<path d="M300 330 L300 245 Q360 185 420 245 L420 330 Z" fill="#9fd3f5" {S}/>')
    else:
        o.append(f'<path d="M300 330 L300 215 L420 215 L420 330 Z" fill="#9fd3f5" {S}/>')
    arch = "window" in ch
    for x in (330, 360, 390):
        y1 = 225 if (arch and x != 360) else 218
        o.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="328" stroke="#111" stroke-width="4"/>')
    o.append(f'<rect x="290" y="330" width="140" height="16" fill="#ffd166" {S}/>')
    # door
    o.append(f'<rect x="440" y="400" width="70" height="180" fill="#2a9d8f" {S}/>')
    o.append('<circle cx="455" cy="495" r="6" fill="#ffd166" stroke="#111" stroke-width="3"/>')
    # clothesline (left) with pole
    o.append(f'<line x1="25" y1="180" x2="25" y2="580" {S}/>')
    o.append('<path d="M25 200 Q135 232 250 210" fill="none" stroke="#111" stroke-width="4"/>')
    # sweater (green)
    o.append(f'<path d="M50 212 L95 214 L112 236 L102 246 L95 240 L95 290 L52 290 L52 240 L44 246 L35 236 Z" fill="#43aa8b" {S}/>')
    # sock (red)
    if "sock" not in ch:
        o.append(f'<path d="M140 222 L162 223 L162 262 L178 270 Q182 284 168 284 L140 278 Z" fill="#e63946" {S}/>')
        o.append('<rect x="140" y="222" width="22" height="10" fill="#fff" stroke="#111" stroke-width="3"/>')
    # muffler (striped)
    o.append(f'<rect x="200" y="220" width="30" height="95" fill="#ffd166" {S}/>')
    for y in (240, 262, 284):
        o.append(f'<rect x="200" y="{y}" width="30" height="10" fill="#3a86ff"/>')
    o.append(f'<rect x="200" y="220" width="30" height="95" fill="none" {S}/>')
    # fog bands
    for y in (360, 420):
        o.append(f'<rect x="-10" y="{y}" width="520" height="26" rx="13" fill="#ffffff" opacity="0.45"/>')
    # ground (gully)
    o.append(f'<rect x="-10" y="580" width="520" height="330" fill="#d8c3a5" {S}/>')
    for x, y in ((40, 860), (450, 640), (470, 860), (60, 640)):
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="14" ry="8" fill="#a8977c" stroke="#111" stroke-width="3"/>')
    # uncle (left) in shawl + monkey cap, holding chai
    ux = 110
    o.append(f'<line x1="{ux-15}" y1="700" x2="{ux-22}" y2="790" {S}/><line x1="{ux+15}" y1="700" x2="{ux+22}" y2="790" {S}/>')
    o.append(f'<path d="M{ux-30} 560 L{ux+30} 560 L{ux+52} 710 L{ux-52} 710 Z" fill="#8d6e63" {S}/>')
    o.append(f'<path d="M{ux-45} 660 L{ux+48} 660" stroke="#5d4037" stroke-width="6"/>')
    o.append(f'<line x1="{ux+28}" y1="590" x2="{ux+66}" y2="630" {S}/>')
    o.append(f'<path d="M{ux+58} 612 L{ux+82} 612 L{ux+78} 640 L{ux+62} 640 Z" fill="#fff" {T}/>')
    o.append(f'<path d="M{ux+64} 600 q5 -8 0 -16 M{ux+75} 600 q5 -8 0 -16" fill="none" stroke="#888" stroke-width="3"/>')
    cc = "#7b2cbf" if "cap" in ch else "#d62828"
    o.append(f'<circle cx="{ux}" cy="520" r="42" fill="{cc}" {S}/>')
    o.append(f'<rect x="{ux-26}" y="505" width="52" height="34" rx="14" fill="#ffd7b0" {T}/>')
    o.append(f'<circle cx="{ux}" cy="474" r="9" fill="{cc}" {T}/>')
    o.append(f'<circle cx="{ux-10}" cy="518" r="4" fill="#111"/><circle cx="{ux+10}" cy="518" r="4" fill="#111"/>')
    o.append(f'<path d="M{ux-8} 530 Q{ux} 535 {ux+8} 530" fill="none" stroke="#111" stroke-width="3" stroke-linecap="round"/>')
    # kid (right) in striped sweater + muffler
    kx = 395
    o.append(f'<line x1="{kx-12}" y1="725" x2="{kx-18}" y2="800" {S}/><line x1="{kx+12}" y1="725" x2="{kx+18}" y2="800" {S}/>')
    o.append('<clipPath id="sw"><rect x="365" y="640" width="60" height="90" rx="12"/></clipPath>')
    o.append(f'<rect x="365" y="640" width="60" height="90" rx="12" fill="#3a86ff" {S}/>')
    o.append('<g clip-path="url(#sw)">')
    ys = (668, 696, 720) if "stripes" in ch else (675, 705)
    for y in ys:
        o.append(f'<rect x="360" y="{y}" width="70" height="11" fill="#ffffff"/>')
    o.append('</g>')
    o.append(f'<rect x="365" y="640" width="60" height="90" rx="12" fill="none" {S}/>')
    o.append(f'<line x1="{kx-28}" y1="660" x2="{kx-60}" y2="700" {S}/><line x1="{kx+28}" y1="660" x2="{kx+52}" y2="700" {S}/>')
    o.append(f'<circle cx="{kx}" cy="606" r="28" fill="#ffd7b0" {S}/>')
    o.append(f'<path d="M{kx-30} 600 Q{kx-30} 570 {kx} 570 Q{kx+30} 570 {kx+30} 600 Z" fill="#ffd166" {S}/>')
    o.append(f'<rect x="{kx-24}" y="632" width="48" height="14" rx="7" fill="#e63946" {T}/>')
    o.append(f'<circle cx="{kx-9}" cy="610" r="3.5" fill="#111"/><circle cx="{kx+9}" cy="610" r="3.5" fill="#111"/>')
    o.append(f'<ellipse cx="{kx}" cy="622" rx="5" ry="4" fill="#111"/>')
    # bonfire (centre bottom)
    fx = 250
    o.append(f'<ellipse cx="{fx}" cy="815" rx="95" ry="22" fill="#9e9e9e" {T}/>')
    o.append(f'<path d="M{fx} 820 Q{fx-70} 790 {fx-40} 720 Q{fx-30} 760 {fx-15} 750 Q{fx-20} 690 {fx+5} 650 Q{fx+15} 720 {fx+30} 715 Q{fx+40} 690 {fx+38} 680 Q{fx+80} 770 {fx} 820 Z" fill="#ff7b00" {S}/>')
    o.append(f'<path d="M{fx} 815 Q{fx-35} 795 {fx-15} 750 Q{fx} 775 {fx+5} 735 Q{fx+35} 780 {fx} 815 Z" fill="#ffd23f" {T}/>')
    o.append(f'<rect x="{fx-80}" y="800" width="160" height="22" rx="10" fill="#8b5a2b" {S} transform="rotate(-12 {fx} 811)"/>')
    o.append(f'<rect x="{fx-80}" y="800" width="160" height="22" rx="10" fill="#a0522d" {S} transform="rotate(12 {fx} 811)"/>')
    if "log" in ch:
        o.append(f'<rect x="{fx+70}" y="838" width="80" height="20" rx="9" fill="#8b5a2b" {S} transform="rotate(-8 {fx+110} 848)"/>')
    # sparks
    for x, y in ((fx-40, 630), (fx+45, 640), (fx+10, 605)):
        o.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#ffb703" stroke="#111" stroke-width="2"/>')
    o.append('</svg>')
    return "\n".join(o)
