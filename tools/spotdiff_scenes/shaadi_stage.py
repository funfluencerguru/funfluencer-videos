"""Spot-the-difference scene: shaadi stage (wedding season). draw(changes) -> SVG 500x900.
Picture A = draw(set()), picture B = draw(set(DIFFS)). Each key in DIFFS is one deliberate change."""

SCENE = "Shaadi stage"
# key -> Hinglish answer line (in the order they appear top to bottom)
DIFFS = {
    "strand": "Upar genda phool ki ek ladi gayab hai (right side)",
    "turban": "Dulhe ki pagdi ka rang orange se green ho gaya",
    "sofa": "Sofa ki back pe polka dots ki jagah stripes",
    "gift": "Left gift ke dher pe ek extra pink gift box",
    "balloon": "Bachche ka laal balloon bada ho gaya",
}

S = 'stroke="#111" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"'


def draw(ch=frozenset()):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 900" width="500" height="900">',
         '<rect width="500" height="900" fill="#ffeef3"/>']
    # backdrop arch
    o.append(f'<path d="M30 650 L30 250 Q30 110 250 110 Q470 110 470 250 L470 650 Z" fill="#c2185b" {S}/>')
    o.append(f'<path d="M70 650 L70 270 Q70 155 250 155 Q430 155 430 270 L430 650 Z" fill="#ffd1dc" {S}/>')
    # canopy
    o.append(f'<rect x="-10" y="-10" width="520" height="80" fill="#ff9f1c" {S}/>')
    for i in range(10):
        x = i * 50 + 25
        o.append(f'<path d="M{x-25} 70 Q{x} 105 {x+25} 70" fill="#ff9f1c" {S}/>')
    # marigold strands
    for k, x in enumerate([45, 120, 195, 305, 380, 455]):
        if x == 380 and "strand" in ch:
            continue
        o.append(f'<line x1="{x}" y1="70" x2="{x}" y2="262" stroke="#2e7d32" stroke-width="4"/>')
        for j in range(8):
            col = "#ff8c00" if (j + k) % 2 == 0 else "#ffd23f"
            o.append(f'<circle cx="{x}" cy="{88 + j * 24}" r="12" fill="{col}" stroke="#111" stroke-width="4"/>')
    # sofa back
    o.append('<clipPath id="sb"><rect x="112" y="322" width="276" height="236" rx="60"/></clipPath>')
    o.append(f'<rect x="112" y="322" width="276" height="236" rx="60" fill="#ffcf33" {S}/>')
    o.append('<g clip-path="url(#sb)">')
    if "sofa" in ch:
        for y in range(345, 560, 34):
            o.append(f'<rect x="100" y="{y}" width="300" height="14" fill="#e0a100"/>')
    else:
        for r_, y in enumerate(range(345, 560, 38)):
            for x in range(130 + (r_ % 2) * 22, 390, 44):
                o.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#e0a100"/>')
    o.append('</g>')
    o.append(f'<rect x="112" y="322" width="276" height="236" rx="60" fill="none" {S}/>')
    # sofa seat + arms
    o.append(f'<rect x="92" y="540" width="316" height="70" rx="20" fill="#e53950" {S}/>')
    o.append(f'<circle cx="98" cy="535" r="30" fill="#e53950" {S}/><circle cx="402" cy="535" r="30" fill="#e53950" {S}/>')
    # stage platform + skirt
    o.append(f'<rect x="-10" y="640" width="520" height="40" fill="#7b1fa2" {S}/>')
    o.append(f'<rect x="-10" y="680" width="520" height="90" fill="#9c27b0" {S}/>')
    for i in range(10):
        x = i * 50
        o.append(f'<path d="M{x} 680 L{x+25} 720 L{x+50} 680 Z" fill="#ffd23f" stroke="#111" stroke-width="4"/>')
    # red carpet floor
    o.append(f'<rect x="-10" y="770" width="520" height="140" fill="#ffe0b2" {S}/>')
    o.append(f'<path d="M170 770 L330 770 L380 910 L120 910 Z" fill="#d32f2f" {S}/>')
    # juttis (shoes) on the carpet
    for x in (215, 285):
        o.append(f'<path d="M{x-28} 845 Q{x-30} 820 {x} 822 Q{x+28} 822 {x+34} 806 Q{x+36} 846 {x} 850 Z" fill="#ffc107" {S}/>')
    # flower pots
    for x in (55, 445):
        o.append(f'<path d="M{x-30} 820 L{x+30} 820 L{x+22} 880 L{x-22} 880 Z" fill="#8d6e63" {S}/>')
        o.append(f'<circle cx="{x}" cy="800" r="26" fill="#43a047" {S}/>')
        o.append(f'<circle cx="{x-12}" cy="792" r="9" fill="#ff4081" stroke="#111" stroke-width="3"/>')
        o.append(f'<circle cx="{x+12}" cy="806" r="9" fill="#ff4081" stroke="#111" stroke-width="3"/>')
    # gift stack (left, on stage)
    o.append(f'<rect x="14" y="575" width="80" height="65" fill="#29b6f6" {S}/>')
    o.append('<rect x="48" y="575" width="12" height="65" fill="#ffd23f" stroke="#111" stroke-width="3"/>')
    o.append(f'<rect x="28" y="528" width="52" height="47" fill="#66bb6a" {S}/>')
    o.append('<rect x="49" y="528" width="10" height="47" fill="#fff" stroke="#111" stroke-width="3"/>')
    if "gift" in ch:
        o.append(f'<rect x="38" y="492" width="34" height="36" fill="#ff6fb5" {S}/>')
        o.append('<rect x="51" y="492" width="8" height="36" fill="#fff" stroke="#111" stroke-width="3"/>')
    # groom
    gx = 195
    o.append(f'<line x1="{gx-15}" y1="560" x2="{gx-22}" y2="640" {S}/><line x1="{gx+15}" y1="560" x2="{gx+22}" y2="640" {S}/>')
    o.append(f'<path d="M{gx-32} 432 L{gx+32} 432 L{gx+40} 575 L{gx-40} 575 Z" fill="#fff4d6" {S}/>')
    o.append(f'<line x1="{gx-30}" y1="450" x2="{gx-55}" y2="530" {S}/><line x1="{gx+30}" y1="450" x2="{gx+50}" y2="525" {S}/>')
    o.append(f'<circle cx="{gx}" cy="392" r="38" fill="#ffd7b0" {S}/>')
    tc = "#2ecc71" if "turban" in ch else "#ff7a00"
    o.append(f'<path d="M{gx-40} 385 Q{gx-44} 336 {gx} 334 Q{gx+44} 336 {gx+40} 385 Q{gx} 368 {gx-40} 385 Z" fill="{tc}" {S}/>')
    o.append(f'<circle cx="{gx+6}" cy="352" r="7" fill="#fff" stroke="#111" stroke-width="3"/>')
    o.append(f'<circle cx="{gx-12}" cy="400" r="4" fill="#111"/><circle cx="{gx+12}" cy="400" r="4" fill="#111"/>')
    o.append(f'<path d="M{gx-12} 412 Q{gx} 424 {gx+12} 412" fill="none" stroke="#111" stroke-width="4" stroke-linecap="round"/>')
    # bride
    bx = 305
    o.append(f'<path d="M{bx-24} 432 L{bx+24} 432 L{bx+58} 615 L{bx-58} 615 Z" fill="#e3242b" {S}/>')
    o.append(f'<path d="M{bx-52} 585 L{bx+52} 585 L{bx+58} 615 L{bx-58} 615 Z" fill="#ffd23f" {S}/>')
    o.append(f'<line x1="{bx-24}" y1="450" x2="{bx-48}" y2="525" {S}/><line x1="{bx+24}" y1="450" x2="{bx+50}" y2="528" {S}/>')
    o.append(f'<circle cx="{bx}" cy="392" r="36" fill="#ffd7b0" {S}/>')
    o.append(f'<path d="M{bx-44} 420 Q{bx-50} 340 {bx} 344 Q{bx+50} 340 {bx+44} 420 Q{bx+34} 372 {bx} 370 Q{bx-34} 372 {bx-44} 420 Z" fill="#e3242b" {S}/>')
    o.append(f'<circle cx="{bx-12}" cy="398" r="4" fill="#111"/><circle cx="{bx+12}" cy="398" r="4" fill="#111"/>')
    o.append(f'<path d="M{bx-11} 410 Q{bx} 421 {bx+11} 410" fill="none" stroke="#111" stroke-width="4" stroke-linecap="round"/>')
    # varmala garlands on both
    for x in (gx, bx):
        for j, a in enumerate(range(0, 9)):
            import math
            t = math.pi * (0.1 + 0.8 * a / 8)
            cx = x - math.cos(t) * 30
            cy = 436 + math.sin(t) * 48
            col = "#ff4d4d" if j % 2 else "#fff176"
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="8" fill="{col}" stroke="#111" stroke-width="3"/>')
    # kid with balloon (right)
    kx = 455
    br = 40 if "balloon" in ch else 28
    o.append(f'<path d="M{kx+12} 560 Q{kx+20} 520 {kx+5} 504" fill="none" stroke="#111" stroke-width="3"/>')
    o.append(f'<ellipse cx="{kx+5}" cy="{470 - (br - 28)}" rx="{br}" ry="{br + 6}" fill="#f44336" {S}/>')
    o.append(f'<line x1="{kx}" y1="590" x2="{kx-10}" y2="640" {S}/><line x1="{kx}" y1="590" x2="{kx+10}" y2="640" {S}/>')
    o.append(f'<line x1="{kx}" y1="560" x2="{kx}" y2="595" {S}/>')
    o.append(f'<line x1="{kx}" y1="572" x2="{kx+14}" y2="560" {S}/><line x1="{kx}" y1="572" x2="{kx-16}" y2="585" {S}/>')
    o.append(f'<circle cx="{kx}" cy="540" r="20" fill="#ffd7b0" {S}/>')
    o.append(f'<circle cx="{kx-7}" cy="538" r="3" fill="#111"/><circle cx="{kx+7}" cy="538" r="3" fill="#111"/>')
    o.append('</svg>')
    return "\n".join(o)
