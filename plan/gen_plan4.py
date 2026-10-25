"""Verdrahtungsplan v4 (final): Pi 3A+ auf Akku-Board UPS HAT (D), Klemmen-Aufsatz, MAX98357A, Kopfhörer an der Pi-Klinke.
Erzeugt verdrahtungsplan.html"""
import html, re

def esc(s): return html.escape(s, quote=True)

COL = {"v5": "--w5v", "v33": "--w33", "gnd": "--wgnd", "i2s": "--wi2s", "spi": "--wspi", "gpio": "--wgpio",
       "aud": "--waud", "i2c": "--wi2c", "bat": "--wbat", "pwrsig": "--wps"}
NET = {"5V": ("5 V", "v5"), "3V3": ("3,3 V", "v33"), "SCL": ("SCL", "i2c"), "GNDA": ("GND A", "gnd"), "GNDB": ("GND B", "gnd")}

# ---------------- Module: (Pin am Modul, Pi-Pin oder Netz, Art, Funktionstext) ----------------
LEFT = [
    ("RC522 NFC-Leser", "SPI · nur 3,3 V · IRQ frei lassen", [
        ("SDA", 24, "spi", "GPIO 8 · CE0"), ("SCK", 23, "spi", "GPIO 11 · SCLK"), ("MOSI", 19, "spi", "GPIO 10 · MOSI"),
        ("MISO", 21, "spi", "GPIO 9 · MISO"), ("RST", 22, "spi", "GPIO 25"), ("3.3V", "3V3", "v33", ""), ("GND", "GNDB", "gnd", "")]),
    ("MPR121 Touch", "I2C-Adresse 0x5A · ADDR frei lassen", [
        ("SDA", 3, "i2c", "GPIO 2 · SDA"), ("IRQ", 29, "gpio", "GPIO 5"), ("SCL", "SCL", "i2c", ""),
        ("VIN", "3V3", "v33", ""), ("GND", "GNDB", "gnd", "")]),
    ("Drehgeber STEC11B03", "Lautstärke", [
        ("A", 11, "gpio", "GPIO 17"), ("B", 13, "gpio", "GPIO 27"), ("C (Mitte)", "GNDA", "gnd", "")]),
    ("Ein-Taste DTS-24R", "zwei diagonale Beinchen", [
        ("Bein 1", "SCL", "i2c", ""), ("Bein 2", "GNDB", "gnd", "")]),
]
MAXP = [("BCLK", 12, "i2s", "GPIO 18 · BCLK"), ("LRC", 35, "i2s", "GPIO 19 · LRCLK"), ("DIN", 40, "i2s", "GPIO 21 · DOUT"),
        ("SD", 36, "gpio", "GPIO 16 · stumm"), ("VIN", "5V", "v5", ""), ("GND", "GNDA", "gnd", "")]
JACKP = [("Öffner L", 37, "gpio", "GPIO 26 · erkennt Stecker")]
POWER_CLAMPS = [(2, "5V", "5V"), (1, "3V3", "3V3"), (5, "GPIO 3 · SCL", "SCL"), (6, "GND", "GNDA"), (9, "GND", "GNDB")]

W, H = 1210, 1010
SX0, SX1 = 470, 720          # Pi-Stapel
LX0, LX1 = 40, 300           # linke Module
RX0, RX1 = 860, 1060         # rechte Module
DY = 26
svg = []
def add(s): svg.append(s)
def wire(points, kind, width=2.6, dash=False):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)
    extra = ' stroke-dasharray="7 5"' if dash else ""
    add(f'<path d="{d}" class="wire" style="stroke:var({COL[kind]})" stroke-width="{width}"{extra}/>')
def dot(x, y, kind, r=3.6): add(f'<circle cx="{x}" cy="{y}" r="{r}" style="fill:var({COL[kind]})"/>')
def text(x, y, s, cls="lbl", anchor="start"): add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{esc(s)}</text>')
def box(x0, y0, x1, y1, cls="mod", rx=8): add(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="{rx}" class="{cls}"/>')
def tag(x, y, net, anchor="start"):
    lab, kind = NET[net]
    w = 12 + 7.4 * len(lab)
    x0 = x if anchor == "start" else x - w
    add(f'<rect x="{x0:.1f}" y="{y-10}" width="{w:.1f}" height="20" rx="10" class="net" style="stroke:var({COL[kind]})"/>')
    add(f'<text x="{x0 + w/2:.1f}" y="{y+4}" class="nettxt" text-anchor="middle" style="fill:var({COL[kind]})">{esc(lab)}</text>')

clamp_left, clamp_right = [], []
# ---------- linke Module ----------
y = 70
for title, sub, pins in LEFT:
    top = y
    py = top + 62
    for i, (mp, tgt, kind, fn) in enumerate(pins):
        yy = py + i * DY
        text(LX1 - 10, yy + 4, mp, "pin", "end")
        if isinstance(tgt, int):
            wire([(LX1, yy), (SX0, yy)], kind); dot(LX1, yy, kind); dot(SX0, yy, kind)
            clamp_left.append((yy, tgt, fn, kind))
        else:
            wire([(LX1, yy), (LX1 + 26, yy)], kind); dot(LX1, yy, kind)
            tag(LX1 + 30, yy, tgt)
    bottom = py + (len(pins) - 1) * DY + 20
    if title.startswith("MPR"):
        bottom += 26
        text(LX0 + 14, bottom - 10, "E0–E3 → 4 Kupferfelder im Deckel", "msub")
    box(LX0, top, LX1, bottom)
    text(LX0 + 14, top + 24, title, "mtitle"); text(LX0 + 14, top + 42, sub, "msub")
    y = bottom + 24
LEFT_END = y

# ---------- rechte Module ----------
# MAX98357A
top = 70; py = top + 62
for i, (mp, tgt, kind, fn) in enumerate(MAXP):
    yy = py + i * DY
    text(RX0 + 10, yy + 4, mp, "pin")
    if isinstance(tgt, int):
        wire([(SX1, yy), (RX0, yy)], kind); dot(SX1, yy, kind); dot(RX0, yy, kind)
        clamp_right.append((yy, tgt, fn, kind))
    else:
        wire([(RX0 - 26, yy), (RX0, yy)], kind); dot(RX0, yy, kind); tag(RX0 - 30, yy, tgt, "end")
mb = py + 5 * DY + 20
box(RX0, top, RX1, mb)
text(RX0 + 14, top + 24, "MAX98357A Verstärker", "mtitle"); text(RX0 + 14, top + 42, "GAIN frei lassen (9 dB)", "msub")
# Lautsprecher
spy = (top + mb) / 2
wire([(RX1, spy - 10), (1100, spy - 10)], "aud"); wire([(RX1, spy + 10), (1100, spy + 10)], "aud")
text(RX1 - 8, spy - 6, "+", "pin", "end"); text(RX1 - 8, spy + 14, "−", "pin", "end")
add(f'<g class="spk"><rect x="1100" y="{spy-18}" width="16" height="36" rx="2"/><path d="M1116,{spy-18} L1146,{spy-40} L1146,{spy+40} L1116,{spy+18} Z"/></g>')
text(1123, spy + 62, "Lautsprecher", "msub", "middle"); text(1123, spy + 78, "FRS 8 · 4 Ω", "msub", "middle")

# Kopfhörerbuchse
jt = 360; jpy = jt + 62
for i, (mp, tgt, kind, fn) in enumerate(JACKP):
    yy = jpy + i * DY
    text(RX0 + 10, yy + 4, mp, "pin")
    if isinstance(tgt, int):
        wire([(SX1, yy), (RX0, yy)], kind); dot(SX1, yy, kind); dot(RX0, yy, kind)
        clamp_right.append((yy, tgt, fn, kind))
    else:
        wire([(RX0 - 26, yy), (RX0, yy)], kind); dot(RX0, yy, kind); tag(RX0 - 30, yy, tgt, "end")
aud_y = [jpy + 2 * DY + 8 + i * DY for i in range(3)]
for lab, yy in zip(["L (Spitze)", "R (Ring)", "GND (Hülse)"], aud_y):
    text(RX1 - 10, yy + 4, lab, "pin", "end")
jb = aud_y[-1] + 22
box(RX0, jt, RX1, jb)
text(RX0 + 14, jt + 24, "Kopfhörerbuchse 1503-09", "mtitle"); text(RX0 + 14, jt + 42, "in der Gehäusewand", "msub")

# Klinke des Pi -> Klinkenkabel (gewinkelt) -> Buchse; Leitungen werden unten beim Pi gezeichnet
DAC_Y0 = 40
cx = [1172, 1186, 1200]

# Elko
et = jb + 40
box(RX0, et, RX1, et + 96)
text(RX0 + 14, et + 24, "Elko 1000 µF / 10 V", "mtitle"); text(RX0 + 14, et + 42, "Beinchen in die Hebelklemmen", "msub")
for i, (lab, net) in enumerate([("+ (langes Bein)", "5V"), ("− (Streifen)", "GNDA")]):
    yy = et + 62 + i * DY
    text(RX0 + 10, yy + 4, lab, "pin"); wire([(RX0 - 26, yy), (RX0, yy)], NET[net][1]); dot(RX0, yy, NET[net][1]); tag(RX0 - 30, yy, net, "end")

# Modul-Boxen hinter Linien und Texte legen
rects = [x for x in svg if x.startswith('<rect') and 'class="mod"' in x]
others = [x for x in svg if not (x.startswith('<rect') and 'class="mod"' in x)]
svg[:] = rects + others
# ---------- Pi-Stapel ----------
S_Y1 = max(LEFT_END - 24, et + 96)
PI_Y0 = S_Y1 - 112
add(f'<rect x="{SX0}" y="{DAC_Y0}" width="{SX1-SX0}" height="{S_Y1-DAC_Y0}" rx="12" class="stack"/>')
box(SX0 + 8, DAC_Y0 + 6, SX1 - 8, PI_Y0 - 4, "pi", 6)
for i, (yy, kind) in enumerate(zip(aud_y, ["aud", "aud", "gnd"])):
    x = cx[i]
    yb = PI_Y0 + 12 + i * 10
    wire([(SX1 - 8, yb), (x, yb), (x, yy), (RX1, yy)], kind, 2.2)
    dot(SX1 - 8, yb, kind); dot(RX1, yy, kind)
text(SX1 + 14, PI_Y0 + 4, "Klinkenkabel, Stecker gewinkelt: Spitze = L, Ring = R, Hülse = GND", "tiny")
text((SX0 + SX1) / 2, 318, "Klemmen-Aufsatz", "ptitle", "middle")
text((SX0 + SX1) / 2, 338, "auf dem Pi · Leiste wird durchgeschleift", "psub", "middle")
for (yy, pin, fn, kind) in clamp_left:
    text(SX0 + 12, yy - 4, f"Pin {pin}", "pnum"); text(SX0 + 12, yy + 10, fn, "tagfn")
for (yy, pin, fn, kind) in clamp_right:
    text(SX1 - 12, yy - 4, f"Pin {pin}", "pnum", "end"); text(SX1 - 12, yy + 10, fn, "tagfn", "end")
# Stromklemmen unten im Aufsatz
pc_y0 = 512
text((SX0 + SX1) / 2, pc_y0 - 22, "Strom-Klemmen → Hebelklemmen", "stitle", "middle")
for i, (pin, fn, net) in enumerate(POWER_CLAMPS):
    yy = pc_y0 + i * 22
    kind = NET[net][1]
    text(SX0 + 20, yy + 4, f"Pin {pin}", "pnum"); text(SX0 + 70, yy + 4, fn, "pin")
    wire([(SX1 - 70, yy), (SX1 - 40, yy)], kind); tag(SX1 - 36, yy, net)
box(SX0 + 8, PI_Y0, SX1 - 8, PI_Y0 + 44, "pilayer", 6)
text((SX0 + SX1) / 2, PI_Y0 + 22, "Raspberry Pi 3 Model A+", "mtitle", "middle")
text((SX0 + SX1) / 2, PI_Y0 + 37, "Klinke 3,5 mm → Kopfhörer", "msub", "middle")
box(SX0 + 8, PI_Y0 + 50, SX1 - 8, S_Y1 - 6, "ups", 6)
text((SX0 + SX1) / 2, PI_Y0 + 73, "Akku-Board UPS HAT (D)", "mtitle", "middle")
text((SX0 + SX1) / 2, PI_Y0 + 90, "2 × 21700 · USB-C zum Laden", "msub", "middle")

# ---------- Hebelklemmen unten ----------
WAGOS = [
    ("5V", "3-fach · Boden", ["Aufsatz Pin 2 (5 V)", "MAX VIN", "Elko +"]),
    ("GNDA", "5-fach · Boden", ["Aufsatz Pin 6 (GND)", "MAX GND", "Elko −", "Drehgeber C", "frei"]),
    ("3V3", "3-fach · Deckel", ["Aufsatz Pin 1 (3,3 V)", "RC522 3.3V", "MPR121 VIN"]),
    ("SCL", "3-fach · Deckel", ["Aufsatz Pin 5 (SCL)", "MPR121 SCL", "Ein-Taste Bein 1"]),
    ("GNDB", "5-fach · Deckel", ["Aufsatz Pin 9 (GND)", "RC522 GND", "MPR121 GND", "Ein-Taste Bein 2", "frei"]),
]
wy = S_Y1 + 50
text(40, wy - 16, "Hebelklemmen: jede Zeile ist ein Hebel · 2 auf dem Boden, 3 unter dem Deckel", "stitle")
gap = 16; bw = (W - 80 - gap * 4) / 5
for i, (net, typ, members) in enumerate(WAGOS):
    x0 = 40 + i * (bw + gap)
    lab, kind = NET[net]
    add(f'<rect x="{x0:.1f}" y="{wy}" width="{bw:.1f}" height="{44 + 22 * len(members)}" rx="8" class="wago" style="stroke:var({COL[kind]})"/>')
    tag(x0 + 12, wy + 20, net)
    text(x0 + bw - 12, wy + 24, typ, "tiny", "end")
    for j, m in enumerate(members):
        yy = wy + 52 + j * 22
        add(f'<rect x="{x0+12:.1f}" y="{yy-9}" width="14" height="14" rx="3" class="lever" style="fill:var({COL[kind]})"/>')
        text(x0 + 34, yy + 3, m, "pin" if m != "frei" else "msub")
H = wy + 44 + 22 * 5 + 20
svg_code = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Schaltplan der Musikbox">' + "".join(svg) + "</svg>")

# ---------------- Kabelliste ----------------
CABLES = [
    ("Aufsatz → Hebelklemmen", "Steckkabel-Hälfte, beide Enden abisoliert", [
        ("p2", "Aufsatz Pin 2 (5 V)", "Hebelklemme 5 V"),
        ("p1", "Aufsatz Pin 1 (3,3 V)", "Hebelklemme 3,3 V"),
        ("p5", "Aufsatz Pin 5 (SCL)", "Hebelklemme SCL"),
        ("p6", "Aufsatz Pin 6 (GND)", "Hebelklemme GND A"),
        ("p9", "Aufsatz Pin 9 (GND)", "Hebelklemme GND B"),
    ]),
    ("RC522 NFC-Leser", "Steckkabel-Hälfte: Buchse auf den Modul-Stift, abisoliertes Ende in die Klemme", [
        ("rc1", "RC522 SDA", "Aufsatz Pin 24 (GPIO 8)"), ("rc2", "RC522 SCK", "Aufsatz Pin 23 (GPIO 11)"),
        ("rc3", "RC522 MOSI", "Aufsatz Pin 19 (GPIO 10)"), ("rc4", "RC522 MISO", "Aufsatz Pin 21 (GPIO 9)"),
        ("rc5", "RC522 RST", "Aufsatz Pin 22 (GPIO 25)"), ("rc6", "RC522 3.3V", "Hebelklemme 3,3 V"),
        ("rc7", "RC522 GND", "Hebelklemme GND B"),
    ]),
    ("MPR121 Touch", "Steckkabel-Hälften wie beim RC522", [
        ("mp1", "MPR121 SDA", "Aufsatz Pin 3 (GPIO 2)"), ("mp2", "MPR121 IRQ", "Aufsatz Pin 29 (GPIO 5)"),
        ("mp3", "MPR121 SCL", "Hebelklemme SCL"), ("mp4", "MPR121 VIN", "Hebelklemme 3,3 V"),
        ("mp5", "MPR121 GND", "Hebelklemme GND B"),
        ("mp6", "MPR121 E0–E3 (4 Kabel)", "Kupferfelder 1–4 unter dem Deckel"),
    ]),
    ("Verstärker und Lautsprecher", "Steckkabel-Hälften; Lautsprecher mit zwei Adern", [
        ("mx1", "MAX BCLK", "Aufsatz Pin 12 (GPIO 18)"), ("mx2", "MAX LRC", "Aufsatz Pin 35 (GPIO 19)"),
        ("mx3", "MAX DIN", "Aufsatz Pin 40 (GPIO 21)"), ("mx4", "MAX SD", "Aufsatz Pin 36 (GPIO 16)"),
        ("mx5", "MAX VIN", "Hebelklemme 5 V"), ("mx6", "MAX GND", "Hebelklemme GND A"),
        ("mx7", "MAX Klemme + und −", "Lautsprecher + und − (Lötfahnen)"),
    ]),
    ("Bedienteile", "Ader an das Bauteil gelötet, anderes Ende abisoliert", [
        ("en1", "Drehgeber A", "Aufsatz Pin 11 (GPIO 17)"), ("en2", "Drehgeber B", "Aufsatz Pin 13 (GPIO 27)"),
        ("en3", "Drehgeber C (Mitte)", "Hebelklemme GND A"),
        ("bt1", "Ein-Taste Bein 1", "Hebelklemme SCL"), ("bt2", "Ein-Taste Bein 2 (diagonal)", "Hebelklemme GND B"),
    ]),
    ("Kopfhörer", "Klinkenkabel halbieren, Hälfte mit dem gewinkelten Stecker nehmen. Welche Ader an Spitze, Ring und Hülse geht, vorher mit dem Multimeter am Stecker prüfen", [
        ("ci1", "Gewinkelter Stecker", "Klinke des Pi"),
        ("ci2", "Ader von der Spitze (L)", "Buchse L (Spitze)"), ("ci3", "Ader vom Ring (R)", "Buchse R (Ring)"),
        ("ci4", "Ader bzw. Schirm von der Hülse", "Buchse GND (Hülse)"),
        ("jd1", "Buchse Öffner L (siehe Hinweis)", "Aufsatz Pin 37 (GPIO 26)"),
    ]),
    ("Elko", "Beinchen auf ca. 11 mm kürzen, direkt einstecken", [
        ("el1", "Elko + (langes Bein)", "Hebelklemme 5 V"), ("el2", "Elko − (Streifen-Seite)", "Hebelklemme GND A"),
    ]),
]
ncab = sum(len(c) for _, _, c in CABLES)
cab_html = ""
for title, how, rows in CABLES:
    trs = "".join(f'<tr><td class="ck"><input type="checkbox" data-k="k-{k}" aria-label="{esc(a)} verbunden"></td>'
                  f'<td>{esc(a)}</td><td class="arr">→</td><td>{esc(b)}</td></tr>' for k, a, b in rows)
    cab_html += f'<div class="cgroup"><h3>{esc(title)}</h3><p class="how">{esc(how)}</p><table class="ctab"><tbody>{trs}</tbody></table></div>'

# ---------------- Teile ----------------
PARTS = [
    ("Raspberry Pi 3 Model A+", "Gehirn: Spotify, Karten, Tasten", "Amazon", "nein"),
    ("microSD SanDisk Ultra 32 GB", "Betriebssystem", "Reichelt", "nein"),
    ("Waveshare UPS HAT (D) + 2 × BAK 21700", "Akku, Laden über USB-C, Akkustand", "BerryBase", "nein"),
    ("GPIO Breakout HAT mit Federkraftklemmen", "Klemmen statt Löten am Pi", "BerryBase", "nein"),
    ("MAX98357A (2 Stück)", "Verstärker für den Lautsprecher, einer Reserve", "Amazon", "ja"),
    ("Visaton FRS 8, 4 Ω", "Lautsprecher", "Reichelt", "ja"),
    ("Lumberg 1503-09", "Kopfhörerbuchse mit 2 Öffnern", "Reichelt", "ja"),
    ("Klinkenkabel 3,5 mm, ein Stecker 90° (Goobay 67782)", "Pi-Klinke zur Buchse, wird halbiert – noch offen", "BerryBase", "nein"),
    ("MPR121", "die 4 Touch-Tasten", "Reichelt", "ja"),
    ("Kupferband 5 mm", "Touchfelder unter dem Deckel", "BerryBase", "nein"),
    ("RC522 (3 Stück)", "NFC-Leser, zwei Reserve", "Amazon", "ja"),
    ("NTAG215-Aufkleber, 20 Stück", "in die Karten", "BerryBase", "nein"),
    ("ALPS STEC11B03", "Lautstärkeknopf", "Reichelt", "ja"),
    ("Kurzhubtaster DTS-24R (2 Stück)", "unter der gedruckten Ein-Taste", "Reichelt", "ja"),
    ("WAGO 221-425 × 4, 221-423 × 3", "Hebelklemmen für Strom und SCL", "Reichelt", "nein"),
    ("Elko 1000 µF / 10 V", "puffert Stromspitzen des Verstärkers", "Reichelt", "nein"),
    ("Steckkabel Buchse–Buchse 50 cm, 40 Stück", "alle Verbindungen, halbiert", "BerryBase", "nein"),
    ("Schrumpfschlauch-Sortiment", "isoliert die Lötstellen", "Reichelt", "–"),
]
parts_rows = "".join(
    f'<tr class="done"><td class="num">{i}</td><td><b>{esc(n)}</b></td><td>{esc(w)}</td><td class="shop">{esc(s)}</td><td class="sold">{esc(l)}</td></tr>'
    for i, (n, w, s, l) in enumerate(PARTS, 1))

# ---------------- Lötliste ----------------
SOLDER = [
    ("Stiftleisten an die Module", [
        ("max", "MAX98357A: Stiftleiste (7) und grüne Lautsprecherklemme (2)", 9),
        ("mpr", "MPR121: Stifte für VIN, GND, SCL, SDA, IRQ und E0–E3 (9)", 9),
        ("rc", "RC522: Stiftleiste (8)", 8),
    ]),
    ("Adern an Bauteile", [
        ("spk", "Lautsprecher: 2 Adern an die Lötfahnen", 2),
        ("jack", "Kopfhörerbuchse: L, R, GND, Öffner L (4)", 4),
        ("enc", "Drehgeber: A, B, C (3)", 3),
        ("btn", "Ein-Taste: 2 diagonale Beinchen", 2),
    ]),
]
total = sum(n for _, items in SOLDER for *_, n in items)
solder_html = ""
for title, items in SOLDER:
    lis = "".join(f'<li><label><input type="checkbox" data-k="s-{k}"> <span>{esc(t)}</span></label></li>' for k, t, _ in items)
    solder_html += f'<div class="sgroup"><h3>{esc(title)}</h3><ul class="checks">{lis}</ul></div>'

# ---------------- Pin-Tabelle ----------------
PINS = [
    (1, "3,3 V", "Hebelklemme 3,3 V (Deckel)", "RC522, MPR121", "v33"),
    (2, "5 V", "Hebelklemme 5 V (Boden)", "MAX98357A, Elko", "v5"),
    (3, "GPIO 2 · SDA", "MPR121", "SDA (Akku-Board liest mit)", "i2c"),
    (5, "GPIO 3 · SCL", "Hebelklemme SCL (Deckel)", "MPR121 SCL, Ein-Taste", "i2c"),
    (6, "GND", "Hebelklemme GND A (Boden)", "", "gnd"),
    (9, "GND", "Hebelklemme GND B (Deckel)", "", "gnd"),
    (11, "GPIO 17", "Drehgeber", "A", "gpio"),
    (12, "GPIO 18 · BCLK", "MAX98357A", "BCLK", "i2s"),
    (13, "GPIO 27", "Drehgeber", "B", "gpio"),
    (19, "GPIO 10 · MOSI", "RC522", "MOSI", "spi"),
    (21, "GPIO 9 · MISO", "RC522", "MISO", "spi"),
    (22, "GPIO 25", "RC522", "RST", "spi"),
    (23, "GPIO 11 · SCLK", "RC522", "SCK", "spi"),
    (24, "GPIO 8 · CE0", "RC522", "SDA", "spi"),
    (29, "GPIO 5", "MPR121", "IRQ", "gpio"),
    (35, "GPIO 19 · LRCLK", "MAX98357A", "LRC", "i2s"),
    (36, "GPIO 16", "MAX98357A", "SD (stumm schalten)", "gpio"),
    (37, "GPIO 26", "Kopfhörerbuchse", "Öffner L", "gpio"),
    (40, "GPIO 21 · DOUT", "MAX98357A", "DIN", "i2s"),
]
KL = {"v5": "5 V", "v33": "3,3 V", "gnd": "Masse", "i2s": "I2S Ton", "spi": "SPI", "gpio": "Signal", "i2c": "I2C"}
rows_html = "".join(
    f'<tr><td class="num">{p}</td><td class="mono">{esc(n)}</td><td>{esc(m)}</td><td>{esc(mp)}</td>'
    f'<td><span class="chip" style="--c:var({COL[k]})">{KL[k]}</span></td></tr>' for (p, n, m, mp, k) in PINS)

css = open(__import__("os").path.join(__import__("os").path.dirname(__file__), "css_part.txt")).read()
css = css.split("<style>", 1)[1].rsplit("</style>", 1)[0]
css += """
.stack {{ fill: none; stroke: var(--line); stroke-width: 1.5; stroke-dasharray: 5 5 }}
.dac {{ fill: var(--panel); stroke: var(--waud); stroke-width: 1.5 }}
.pilayer {{ fill: var(--pcb); stroke: var(--pcb-edge); stroke-width: 1.5 }}
.ups {{ fill: var(--panel); stroke: var(--wbat); stroke-width: 1.5 }}
.net {{ fill: var(--panel); stroke-width: 1.6 }}
.nettxt {{ font-family: var(--f-mono); font-size: 11.5px; font-weight: 600 }}
.wago {{ fill: var(--panel); stroke-width: 1.6 }}
.lever {{ opacity: .85 }}
.cgrid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 18px }}
.cgroup {{ display: grid; gap: 4px; align-content: start }}
.cgroup .how {{ color: var(--muted); font-size: .88rem }}
.ctab td {{ padding: 5px 6px }}
.ctab td.ck {{ width: 28px }}
.ctab td.arr {{ color: var(--muted); width: 18px; padding-inline: 2px }}
.ctab input, .checks input {{ width: 18px; height: 18px; accent-color: var(--accent) }}
.ctab tr:has(input:checked) td {{ color: var(--muted); text-decoration: line-through }}
ol.steps2 {{ margin: 0; padding-left: 1.3em; display: grid; gap: 8px }}
.callout {{ background: var(--openbg); border-radius: 12px; padding: 12px 16px }}
""".replace("{{", "{").replace("}}", "}")
css = css.replace("{{", "{").replace("}}", "}")

page = f'''<title>Verdrahtungsplan Musikbox</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=Source+Sans+3:wght@400;600&display=swap">
<style>{css}</style>
<div class="wrap">
<header>
  <h1>Verdrahtungsplan Musikbox</h1>
  <p class="lead">Stand 24.10.2026. Der Pi sitzt auf dem Akku-Board, obendrauf der Klemmen-Aufsatz. Die Kopfhörer bekommen den Ton aus der Klinke des Pi, ein kurzes Kabel führt sie zur Buchse in der Wand. Zwei Hebelklemmen sitzen auf dem Boden, drei unter dem Deckel. Gelötet wird nur an den Modulen und Bedienteilen.</p>
</header>

<section>
  <h2>So hängt alles zusammen</h2>
  <div class="steps">
    <div class="step"><b>Strom</b><span>2 Akkuzellen im Akku-Board unter dem Pi. Es lädt über USB-C und versorgt den Pi über Federkontakte. 5 V und 3,3 V gehen von den Klemmen am Aufsatz in Hebelklemmen und von dort zu den Modulen.</span></div>
    <div class="step"><b>Ton</b><span>Lautsprecher: digital über Pin 12, 35, 40 an den Verstärker. Kopfhörer: aus der Klinke des Pi. Steckt ein Kopfhörer, meldet die Buchse das an Pin 37. Das Programm schaltet den Lautsprecher stumm, stellt Spotify auf die Klinke um und begrenzt die Lautstärke (3–5 s Pause).</span></div>
    <div class="step"><b>Bedienen</b><span>NFC-Leser erkennt die Karte, MPR121 die 4 Touch-Tasten, der Drehgeber die Lautstärke. Die Ein-Taste weckt den Pi.</span></div>
    <div class="step"><b>Stapel</b><span>Von unten: Akku-Board, Pi, Klemmen-Aufsatz. Der Boden mit allem darauf wird am Tisch verdrahtet und dann von unten in die Box geschoben.</span></div>
  </div>
</section>

<section>
  <h2>Schaltplan</h2>
  <div class="legend" aria-label="Legende Leitungsarten">
    <span><i style="--c:var(--w5v)"></i>5 V</span><span><i style="--c:var(--w33)"></i>3,3 V</span><span><i style="--c:var(--wgnd)"></i>Masse (GND)</span>
    <span><i style="--c:var(--wi2s)"></i>Ton digital (I2S)</span><span><i style="--c:var(--waud)"></i>Ton analog</span>
    <span><i style="--c:var(--wspi)"></i>NFC (SPI)</span><span><i style="--c:var(--wi2c)"></i>I2C</span><span><i style="--c:var(--wgpio)"></i>Signal</span>
  </div>
  <div class="diagram">{svg_code}</div>
  <p class="lead">Die runden Schilder (5 V, 3,3 V, SCL, GND A, GND B) bedeuten: Dieses Kabel geht in die gleichnamige Hebelklemme. 5 V und GND A liegen auf dem Boden, 3,3 V, SCL und GND B unter dem Deckel bei Touch-Modul, NFC-Leser und Ein-Taste. „Pin“ ist immer die Nummer auf der 40-Pin-Leiste; der Aufsatz hat die Funktion neben jede Klemme gedruckt.</p>
</section>

<section class="card">
  <div class="callout"><b>Klemmen-Nummern folgen:</b> Wie die Steckbrücken auf dem BerryBase-Aufsatz genau den Klemmen zugeordnet werden, steht nirgends im Datenblatt. Schick mir ein Foto der Oberseite, sobald er da ist. Dann trage ich zu jedem Pin die exakte Klemme und Brücke ein. Gebraucht werden 19 der 24 Brücken.</div>
</section>

<section>
  <h2>Kabelliste <span class="progress" id="prog-k"></span></h2>
  <p class="lead">{ncab} Verbindungen. Abisolieren: für die Hebelklemmen 11 mm, für die Federklemmen am Aufsatz so tief, wie die Klemme ist (meist 6–8 mm). Dünne Litze vorher fest verdrillen und mit leichtem Zug prüfen. Häkchen bleiben in diesem Browser gespeichert.</p>
  <div class="card cgrid">{cab_html}</div>
</section>

<section>
  <h2>Lötliste <span class="progress" id="prog-s"></span></h2>
  <p class="lead">{total} Lötstellen, alle von der einfachen Sorte. Vorher eine Stunde mit dem Übungsset üben. Akkuzellen werden nie gelötet; die Touchfelder auch nicht: Das abisolierte Kabelende kommt unter das Kupferband und wird mit einem zweiten Streifen überklebt.</p>
  <div class="card sgrid">{solder_html}</div>
</section>

<section>
  <h2>Was verbaut wird</h2>
  <p class="lead">Alles bestellt bis auf das Klinkenkabel mit gewinkeltem Stecker.</p>
  <div class="card tablewrap"><table>
    <thead><tr><th>Nr</th><th>Bauteil</th><th>Wofür</th><th>Shop</th><th>Löten</th></tr></thead>
    <tbody>{parts_rows}</tbody>
  </table></div>
</section>

<div class="cols">
  <section class="card">
    <h2>Pin-Belegung am Pi</h2>
    <div class="tablewrap"><table>
      <thead><tr><th>Pin</th><th>Funktion</th><th>geht an</th><th>Modul-Pin</th><th>Art</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>
    <p class="lead" style="margin-top:10px">Das Akku-Board speist 5 V und GND von unten ein und liest seine Werte über Pin 3 und 5 (Adressen 0x43 und 0x2D).</p>
  </section>
  <section class="card">
    <h2>Worauf du achten musst</h2>
    <ul class="notes">
      <li class="warn"><b>Zellen:</b> Polung nach dem Aufdruck im Halter, beide Zellen gleich. Der kleine Schiebeschalter am Akku-Board bleibt auf ON.</li>
      <li class="warn"><b>Elko:</b> Der Streifen markiert Minus und kommt in GND A. Falsch herum kann er platzen.</li>
      <li class="warn"><b>Nie 5 V an einen Pin</b> außer Pin 2/4. RC522 und MPR121 nur an 3,3 V.</li>
      <li><b>Laden</b> über die USB-C-Buchse am Akku-Board, nicht über den Micro-USB des Pi. Am Pi selbst wird nichts eingesteckt.</li>
      <li><b>Lautsprecher stumm:</b> Pin 36 LOW schaltet aus. Zum Einschalten wird der Pin auf Eingang gestellt, nicht auf HIGH, sonst spielt der Verstärker nur den linken Kanal.</li>
      <li><b>Ein-Taste an SCL:</b> Kurz drücken weckt den Pi. Im Betrieb erkennt die Software 3 Sekunden Halten und fährt herunter. Touch und Akku-Abfrage stocken währenddessen kurz, das ist normal.</li>
      <li><b>Kopfhörerbuchse:</b> Sie hat laut Datenblatt zwei Öffner: Ohne Stecker ist je eine Lötöse mit dem L- bzw. R-Kontakt verbunden, beim Einstecken trennt sie. Vor dem Löten mit dem Multimeter herausfinden, welche Öse der Öffner von L ist. Sie geht an Pin 37, der Öffner von R bleibt frei. Ob die Erkennung zuverlässig schaltet, prüfen wir im Tischtest.</li>
      <li><b>Kopfhörer-Lautstärke</b> wird nur per Software begrenzt, der Lautsprecher bleibt laut.</li>
    </ul>
    <h2 style="margin-top:18px">Einstellungen in config.txt</h2>
    <pre>dtparam=spi=on
dtparam=i2c_arm=on
dtparam=audio=on
# I2S-Ausgang für den Verstärker MAX98357A
dtoverlay=hifiberry-dac</pre>
  </section>
</div>

<section class="card">
  <h2>Reihenfolge beim Tischaufbau</h2>
  <ol class="steps2">
    <li><b>Vor dem ersten Strom:</b> Mit dem Multimeter zwischen 5 V und GND sowie 3,3 V und GND messen. Es darf kein Durchgang (Piepen) sein. Bei den genutzten Klemmen Durchgang zum jeweiligen Pin prüfen.</li>
    <li><b>Grundsystem:</b> Zellen ins Akku-Board, Pi drauf, SD-Karte rein. Startet der Pi? Zeigt <code>i2cdetect -y 1</code> die Adressen 0x2D und 0x43? Wenn der Pi nicht startet, Plan B: USB-A-Ausgang des Akku-Boards per Kabel an den Micro-USB des Pi.</li>
    <li><b>Aufsatz und Kopfhörer:</b> Steckbrücken setzen. Kopfhörer zuerst direkt in die Klinke des Pi, dann über das gelötete Kabel und die Buchse testen.</li>
    <li><b>Lautsprecher:</b> MAX98357A anschließen, Elko in die Hebelklemmen, laut testen.</li>
    <li><b>Bedienung:</b> MPR121 mit Kupferfeldern, Drehgeber, Ein-Taste (Herunterfahren und Aufwecken).</li>
    <li><b>NFC:</b> RC522 anschließen, erst mit der Testkarte aus dem Set, dann mit einem beschriebenen NTAG215.</li>
    <li><b>Messen für das Gehäuse:</b> Stromaufnahme nach dem Herunterfahren, WLAN-Empfang mit Zellen unter dem Pi, Lautstärke am Kinderkopfhörer, Touch durch 3 mm Kunststoff, Höhe des Stapels.</li>
  </ol>
</section>
</div>
<script>
(function () {{
  var KEY = 'musikbox-verdrahtung-v4';
  var state = {{}};
  try {{ state = JSON.parse(localStorage.getItem(KEY) || '{{}}') || {{}}; }} catch (e) {{ state = {{}}; }}
  var boxes = Array.prototype.slice.call(document.querySelectorAll('input[data-k]'));
  function count(prefix, el) {{
    var b = boxes.filter(function (x) {{ return x.dataset.k.indexOf(prefix) === 0; }});
    var n = b.filter(function (x) {{ return x.checked; }}).length;
    document.getElementById(el).textContent = n + ' / ' + b.length;
  }}
  function render() {{ count('k-', 'prog-k'); count('s-', 'prog-s'); }}
  boxes.forEach(function (b) {{
    b.checked = !!state[b.dataset.k];
    b.addEventListener('change', function () {{
      state[b.dataset.k] = b.checked;
      try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}}
      render();
    }});
  }});
  render();
}})();
</script>'''
open("/home/claude/musikbox/plan/verdrahtungsplan.html", "w").write(page)
print("ok", len(page), "H", H, "total", total, "cables", ncab)
