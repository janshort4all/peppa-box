"""Verdrahtungsplan Peppa Box (Stand 08.11.2026) -> plan/verdrahtungsplan.html

Gliederung nach Baugruppen: Deckel (Module + WAGO am Deckel), Boden (WAGO am Boden, Verstärker),
Korpus (Wandteile). Alle Anschlüsse am Klemmen-Aufsatz mit dessen Aufdruck (BerryBase RPI-BKFHAT):
Federklemmen 1–8 / A–H / I–P, gelbe 40er-Stiftleiste mit P-Nummern.
Ansicht des Aufsatzes wie im Boden eingebaut: 40er-Stiftleiste vorne (im Bild unten),
also um 180° gedreht gegenüber dem Produktfoto.
"""
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = html.escape

# ---------------------------------------------------------------- Aufdruck des Aufsatzes
GRUPPE_18 = [("1", "3.3V"), ("2", "SDA1"), ("3", "SCL1"), ("4", "GND"), ("5", "GND"), ("6", "RX0"), ("7", "TX0"), ("8", "+5V")]
GRUPPE_AH = [("A", "3.3V"), ("B", "MOSI"), ("C", "MISO"), ("D", "SCLK"), ("E", "CE0"), ("F", "CE1"), ("G", "GND"), ("H", "+5V")]
GRUPPE_IP = [("I", "3.3V"), ("J", "PWM0"), ("K", "PWM1"), ("L", "PCMfs"), ("M", "PCMi"), ("N", "PCMo"), ("O", "GND"), ("P", "+5V")]
# 40er-Leiste, Pi-Pin 1..40 -> Aufdruck
LEISTE = {1: "3.3V", 2: "5V", 3: "SDA1", 4: "5V", 5: "SCL1", 6: "GND", 7: "P04", 8: "TX0", 9: "GND", 10: "RX0",
          11: "P17", 12: "P18", 13: "P27", 14: "GND", 15: "P22", 16: "P23", 17: "3.3V", 18: "P24", 19: "MOSI", 20: "GND",
          21: "MISO", 22: "P25", 23: "SCLK", 24: "CE0", 25: "GND", 26: "CE1", 27: "IDSD", 28: "IDSC", 29: "P05", 30: "GND",
          31: "P06", 32: "P12", 33: "P13", 34: "GND", 35: "P19", 36: "P16", 37: "P26", 38: "P20", 39: "GND", 40: "P21"}

# ---------------------------------------------------------------- Belegung
# Zone: deckel / boden / korpus
KLEMMEN = {  # Federklemme -> (Ader, Zone, Ziel kurz)
    "A": ("D1", "deckel", "WAGO 3,3 V"),
    "B": ("D6", "deckel", "RC522 MOSI"),
    "C": ("D7", "deckel", "RC522 MISO"),
    "D": ("D5", "deckel", "RC522 SCK"),
    "E": ("D4", "deckel", "RC522 SDA"),
    "G": ("D2", "deckel", "WAGO GND B"),
    "I": ("D8", "deckel", "RC522 RST"),
    "2": ("D9", "deckel", "MPR121 SDA"),
    "3": ("D3", "deckel", "WAGO SCL"),
    "4": ("B2", "boden", "WAGO GND A"),
    "8": ("B1", "boden", "WAGO 5 V"),
}
STIFTE = {  # Aufdruck gelber Stift -> (Ader, Zone, Ziel kurz)
    "P05": ("D10", "deckel", "MPR121 INT"),
    "P16": ("B6", "boden", "MAX SD"),
    "P18": ("B3", "boden", "MAX BCLK"),
    "P19": ("B4", "boden", "MAX LRC"),
    "P21": ("B5", "boden", "MAX DIN"),
    "P17": ("K1", "korpus", "Drehgeber A"),
    "P27": ("K2", "korpus", "Drehgeber B"),
    "P26": ("K5", "korpus", "Klinke Öffner"),
}
JUMPER = [k for k in ["1", "2", "3", "4", "5", "6", "7", "8", "A", "B", "C", "D", "E", "F", "G", "H",
                      "I", "J", "K", "L", "M", "N", "O", "P"] if k in KLEMMEN]

# Deckel-Strang: Ader, Ende am Deckel, Ende am Aufsatz
STRANG_DECKEL = [
    ("D1", "WAGO 3,3 V (Deckel)", "Klemme A · 3.3V"),
    ("D2", "WAGO GND B (Deckel)", "Klemme G · GND"),
    ("D3", "WAGO SCL (Deckel)", "Klemme 3 · SCL1"),
    ("D4", "RC522 SDA", "Klemme E · CE0"),
    ("D5", "RC522 SCK", "Klemme D · SCLK"),
    ("D6", "RC522 MOSI", "Klemme B · MOSI"),
    ("D7", "RC522 MISO", "Klemme C · MISO"),
    ("D8", "RC522 RST", "Klemme I · 3.3V"),
    ("D9", "MPR121 SDA", "Klemme 2 · SDA1"),
    ("D10", "MPR121 INT", "gelber Stift P05 (Steckkabel-Buchse)"),
]

WAGO_DECKEL = [
    ("WAGO 3,3 V", "3-fach", "w33", ["D1 von Klemme A (3.3V)", "RC522 3.3V", "MPR121 VIN"]),
    ("WAGO SCL", "3-fach", "wscl", ["D3 von Klemme 3 (SCL1)", "MPR121 SCL", "Ein-Taste, Ader 1"]),
    ("WAGO GND B", "5-fach", "wgnd", ["D2 von Klemme G (GND)", "RC522 GND", "MPR121 GND", "Ein-Taste, Ader 2", "frei"]),
]
WAGO_BODEN = [
    ("WAGO 5 V", "3-fach", "w5v", ["B1 von Klemme 8 (+5V)", "MAX VIN", "Elko + (langes Bein)"]),
    ("WAGO GND A", "5-fach", "wgnd", ["B2 von Klemme 4 (GND)", "MAX GND", "MAX GAIN", "Elko − (Streifen)", "K3 Drehgeber C (Mitte)"]),
]

MODULE_DECKEL = [
    ("RC522 NFC-Leser", "in den Schienen hinter dem Kartenfach · Stiftleiste zur rechten Wand", [
        ("SDA", "D4 → Klemme E (CE0)"),
        ("SCK", "D5 → Klemme D (SCLK)"),
        ("MOSI", "D6 → Klemme B (MOSI)"),
        ("MISO", "D7 → Klemme C (MISO)"),
        ("IRQ", "frei"),
        ("GND", "WAGO GND B"),
        ("RST", "D8 → Klemme I (3.3V) · Reset macht die Software"),
        ("3.3V", "WAGO 3,3 V"),
    ]),
    ("MPR121 Touch (Adafruit 1982)", "Mulde unter der Verteiler-Brücke · Adern direkt in die Lötaugen", [
        ("VIN", "WAGO 3,3 V"),
        ("GND", "WAGO GND B"),
        ("SCL", "WAGO SCL"),
        ("SDA", "D9 → Klemme 2 (SDA1)"),
        ("INT", "D10 → gelber Stift P05"),
        ("E0 … E3", "Kupferfelder (Vorschlag: E0 zurück, E1 Play, E2 vor, E3 Schlaf)"),
        ("3Vo, ADDR, E4–E11", "frei"),
    ]),
    ("Ein-Taste (KHT1212PV73)", "im Tasterhalter des Deckelrahmens", [
        ("Beinchen unten rechts", "WAGO SCL"),
        ("Beinchen unten links", "WAGO GND B"),
        ("übrige 2 Beinchen", "frei · Paar gemessen 08.11.: nur gedrückt Durchgang"),
    ]),
]

BODEN_ADERN = [
    ("B1", "Klemme 8 · +5V", "WAGO 5 V"),
    ("B2", "Klemme 4 · GND", "WAGO GND A"),
    ("B3", "gelber Stift P18", "MAX BCLK"),
    ("B4", "gelber Stift P19", "MAX LRC"),
    ("B5", "gelber Stift P21", "MAX DIN"),
    ("B6", "gelber Stift P16", "MAX SD"),
    ("–", "MAX VIN · GND · GAIN", "WAGO 5 V · WAGO GND A · WAGO GND A"),
    ("–", "Elko + / − (Streifen)", "WAGO 5 V / WAGO GND A · Beinchen ca. 11 mm"),
]

KORPUS_ADERN = [
    ("K1", "Drehgeber A", "gelber Stift P17"),
    ("K2", "Drehgeber B", "gelber Stift P27"),
    ("K3", "Drehgeber C (Mitte)", "WAGO GND A"),
    ("–", "Drehgeber-Taster (2 Beinchen)", "Reserve: anlöten, Enden isolieren, nicht anschließen"),
    ("K4", "Lautsprecher + / −", "MAX-Klemme + / − (nie an GND)"),
    ("K5", "Klinke Fahne C (Öffner L)", "gelber Stift P26 (hat keine Federklemme)"),
    ("–", "Klinke Fahne A / B / E", "Goobay Geflecht / weiß / rot · Fahne D frei, nicht abschneiden"),
    ("K6", "Goobay-Winkelstecker", "Klinke des Pi"),
    ("K7", "USB-C-Platine VBUS / GND", "rote / schwarze Ader, 90°-Stecker in USB-C am Akku-Board · CC1, CC2 je 5,1 kΩ nach GND"),
]

ZONE_NAME = {"deckel": "Deckel", "boden": "Boden", "korpus": "Korpus"}


# ---------------------------------------------------------------- SVG Aufsatz
def svg_aufsatz():
    W, H = 1000, 700
    o = []
    a = o.append
    a(f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Klemmen-Aufsatz von oben, 40er-Stiftleiste vorne: '
      f'benutzte Federklemmen und gelbe Stifte farbig nach Baugruppe, mit Adernummer und Ziel">')
    a('<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
      '<line x1="0" y1="0" x2="0" y2="6" class="hatch"/></pattern></defs>')
    # Platine
    a('<rect x="40" y="56" width="920" height="532" rx="18" class="pcb"/>')
    a('<text x="500" y="44" class="cap" text-anchor="middle">HINTEN (Anschlusskante USB-C, Pi-Klinke)</text>')
    a('<text x="500" y="690" class="cap" text-anchor="middle">VORNE (zur Lautsprecherkammer)</text>')

    ROW0, RH = 132, 40          # Reihen der drei Gruppen, von oben nach unten

    def zone_of(key):
        return KLEMMEN.get(key, (None, None, None))

    # seitliche Klemmenleisten
    def bar_vertical(x, keys):
        a(f'<rect x="{x}" y="{ROW0 - 4}" width="40" height="{8 * RH + 8}" rx="6" class="bar"/>')
        for i, k in enumerate(keys):
            y = ROW0 + i * RH
            ad, zn, _ = zone_of(k)
            cls = f"tcell {zn}" if zn else "tcell"
            a(f'<rect x="{x + 5}" y="{y + 4}" width="30" height="{RH - 8}" rx="4" class="{cls}"/>')
            a(f'<text x="{x + 20}" y="{y + RH / 2 + 5}" text-anchor="middle" class="tkey{" on" if zn else ""}">{k}</text>')

    # Gruppen um 180° gedreht: oberste Reihe ist P / H / 8
    ip = list(reversed(GRUPPE_IP))
    ah = list(reversed(GRUPPE_AH))
    g18 = list(reversed(GRUPPE_18))
    bar_vertical(48, [k for k, _ in ip])
    bar_vertical(912, [k for k, _ in g18])
    # obere Leiste A–H (gedreht: H links … A rechts)
    tx0, tw = 420, 40
    a(f'<rect x="{tx0 - 6}" y="62" width="{8 * tw + 12}" height="44" rx="6" class="bar"/>')
    for i, (k, _) in enumerate(ah):
        x = tx0 + i * tw
        ad, zn, _ = zone_of(k)
        cls = f"tcell {zn}" if zn else "tcell"
        a(f'<rect x="{x + 4}" y="68" width="{tw - 8}" height="32" rx="4" class="{cls}"/>')
        a(f'<text x="{x + tw / 2}" y="89" text-anchor="middle" class="tkey{" on" if zn else ""}">{k}</text>')
    a(f'<text x="68" y="{ROW0 + 8 * RH + 22}" text-anchor="middle" class="small">I–P</text>')
    a(f'<text x="932" y="{ROW0 + 8 * RH + 22}" text-anchor="middle" class="small">1–8</text>')

    # Gruppenfelder mit Aufdruck, Jumper, Ziel
    def panel(x0, w, rows, title):
        a(f'<rect x="{x0}" y="{ROW0 - 4}" width="{w}" height="{8 * RH + 8}" rx="8" class="panel"/>')
        for i, (k, lab) in enumerate(rows):
            y = ROW0 + i * RH
            ad, zn, ziel = zone_of(k)
            if i:
                a(f'<line x1="{x0 + 8}" y1="{y}" x2="{x0 + w - 8}" y2="{y}" class="sep"/>')
            # Aufdruck
            a(f'<text x="{x0 + 12}" y="{y + RH / 2 + 5}" class="print{" on" if zn else ""}">{E(lab)}</text>')
            # zwei Stifte + Jumper
            px = x0 + 66
            if zn:
                a(f'<rect x="{px - 3}" y="{y + 11}" width="30" height="18" rx="4" class="jumper"/>')
            for dx in (0, 16):
                a(f'<rect x="{px + dx + 2}" y="{y + 16}" width="8" height="8" rx="1.5" class="pin{" covered" if zn else ""}"/>')
            # Buchstabe/Zahl
            a(f'<rect x="{x0 + 100}" y="{y + 9}" width="24" height="22" rx="4" class="keybox"/>')
            a(f'<text x="{x0 + 112}" y="{y + RH / 2 + 5}" text-anchor="middle" class="key">{k}</text>')
            # Ziel
            if zn:
                bw = w - 140
                a(f'<rect x="{x0 + 132}" y="{y + 7}" width="{bw}" height="26" rx="13" class="tag {zn}"/>')
                a(f'<text x="{x0 + 142}" y="{y + RH / 2 + 5}" class="tagt"><tspan class="tagid">{ad}</tspan> {E(ziel)}</text>')
        a(f'<text x="{x0 + w / 2}" y="{ROW0 - 12}" text-anchor="middle" class="small">{title}</text>')

    panel(100, 262, ip, "Gruppe I–P")
    panel(372, 262, ah, "Gruppe A–H")
    panel(644, 262, g18, "Gruppe 1–8")

    # 40er-Leiste, gedreht: links Pi-Pin 39/40 … rechts 1/2
    LX0, CW = 100, 40
    YO, YE, YS = 486, 512, 536            # obere Beschriftungsreihe (ungerade Pins), untere (gerade), Stifte
    a(f'<rect x="{LX0 - 8}" y="{YO - 16}" width="{20 * CW + 16}" height="104" rx="8" class="panel"/>')
    a(f'<rect x="{LX0}" y="{YS}" width="{20 * CW}" height="42" rx="4" class="header"/>')
    ins = len(o)                       # Führungslinien hier einfügen (hinter den Beschriftungen)
    callouts = []
    for i in range(20):
        po = 39 - 2 * i
        pe = 40 - 2 * i
        x = LX0 + i * CW
        for pin, y in ((po, YO), (pe, YE)):
            lab = LEISTE[pin]
            ad, zn, ziel = STIFTE.get(lab, (None, None, None))
            if zn:
                a(f'<rect x="{x + 2}" y="{y - 13}" width="{CW - 4}" height="18" rx="4" class="lcell {zn}"/>')
                callouts.append((x + CW / 2 + (-6 if y == YO else 6), y, ad, zn, lab, ziel))
            a(f'<text x="{x + CW / 2}" y="{y}" text-anchor="middle" class="lab{" on" if zn else ""}">{E(lab)}</text>')
        for row in range(2):
            a(f'<rect x="{x + 15}" y="{YS + 8 + row * 18}" width="10" height="10" rx="2" class="ypin"/>')
    a(f'<text x="{LX0 + 10 * CW}" y="{YO - 22}" text-anchor="middle" class="small">gelbe 40er-Stiftleiste (Aufdruck in zwei Reihen) · Steckkabel mit Buchse, unter dem Niederhalter</text>')

    # Hinweisschilder unter der Platine
    callouts.sort(key=lambda c: (c[0], c[1]))
    n = len(callouts)
    span = 900
    lines = []
    for j, (cx, cy, ad, zn, lab, ziel) in enumerate(callouts):
        tx = 50 + span * (j + 0.5) / n
        ty = 610
        lines.append(f'<polyline points="{cx},{cy + 6} {cx},{YS + 48} {tx},{ty - 6}" class="lead {zn}"/>')
        a(f'<rect x="{tx - 54}" y="{ty - 6}" width="108" height="46" rx="8" class="tag {zn}"/>')
        a(f'<text x="{tx}" y="{ty + 12}" text-anchor="middle" class="tagt"><tspan class="tagid">{ad}</tspan> {lab}</text>')
        a(f'<text x="{tx}" y="{ty + 30}" text-anchor="middle" class="tagt">{E(ziel)}</text>')
    o[ins:ins] = lines
    a('</svg>')
    return "".join(o)


# ---------------------------------------------------------------- HTML-Bausteine
def chk(key):
    return f'<input type="checkbox" data-k="{E(key)}" aria-label="erledigt">'


def wago_card(name, typ, cls, members, zone):
    li = "".join(
        f'<li><span class="lever {cls}"></span><span class="{"muted" if m == "frei" else ""}">{E(m)}</span></li>'
        for m in members)
    return (f'<div class="wago {zone}"><div class="whead"><b>{E(name)}</b><span>{E(typ)}</span></div>'
            f'<ol class="levers">{li}</ol></div>')


def mod_card(name, where, rows, zone):
    tr = "".join(f'<tr><td>{chk(zone + name + p)}</td><td class="mono">{E(p)}</td><td>{E(z)}</td></tr>' for p, z in rows)
    return (f'<div class="card"><h4>{E(name)}</h4><p class="where">{E(where)}</p>'
            f'<table class="t"><thead><tr><th></th><th>Pin</th><th>geht an</th></tr></thead><tbody>{tr}</tbody></table></div>')


def adern_table(rows, zone, kopf):
    tr = "".join(
        f'<tr><td>{chk(zone + ad + a_)}</td><td><span class="id {zone}">{E(ad)}</span></td><td>{E(a_)}</td><td>{E(b)}</td></tr>'
        for ad, a_, b in rows)
    return (f'<table class="t"><thead><tr><th></th><th>Ader</th><th>{E(kopf[0])}</th><th>{E(kopf[1])}</th></tr></thead>'
            f'<tbody>{tr}</tbody></table>')


CSS = r"""
/* Layout: Aufsatz-Bild oben (was kommt wohin), darunter drei Spalten Deckel / Boden / Korpus */
:root {
  --bg: #f3f4f1; --panel: #ffffff; --fg: #1b1f1d; --muted: #5f6762; --line: #d8dcd6;
  --pcb: #1f4f7a; --pcbtext: #dfe9f2; --bar: #c9ccc8; --cell: #e7e9e6;
  --deckel: #d9731f; --deckel-bg: #fbeadb; --boden: #2c66b8; --boden-bg: #e0eaf8; --korpus: #7a4fc2; --korpus-bg: #ece4f8;
  --jumper: #2f9a64; --yellow: #f0b429;
  --w5v: #d23b2e; --w33: #e08a12; --wgnd: #3c4440; --wscl: #0f8a8a;
  --f-display: "IBM Plex Sans Condensed", "Arial Narrow", sans-serif;
  --f-body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #121513; --panel: #1b1f1d; --fg: #e6ebe7; --muted: #9ba59f; --line: #2f3632;
  --pcb: #17364f; --pcbtext: #c9d9e6; --bar: #4a4f4c; --cell: #2a2f2c;
  --deckel: #f39a4c; --deckel-bg: #3a2717; --boden: #6f9ff0; --boden-bg: #1a2a42; --korpus: #b18cf0; --korpus-bg: #2c2240;
  --jumper: #4fcf8c; --yellow: #f0c050; --w5v: #ff6b5c; --w33: #ffb347; --wgnd: #b9c3bd; --wscl: #4fd0d0; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #121513; --panel: #1b1f1d; --fg: #e6ebe7; --muted: #9ba59f; --line: #2f3632;
  --pcb: #17364f; --pcbtext: #c9d9e6; --bar: #4a4f4c; --cell: #2a2f2c;
  --deckel: #f39a4c; --deckel-bg: #3a2717; --boden: #6f9ff0; --boden-bg: #1a2a42; --korpus: #b18cf0; --korpus-bg: #2c2240;
  --jumper: #4fcf8c; --yellow: #f0c050; --w5v: #ff6b5c; --w33: #ffb347; --wgnd: #b9c3bd; --wscl: #4fd0d0; color-scheme: dark }
* { box-sizing: border-box }
html { background: var(--bg) }
body { background: var(--bg); color: var(--fg); font-family: var(--f-body); font-size: 16px; line-height: 1.5; margin: 0;
  padding: 28px max(16px, env(safe-area-inset-right, 0px)) 56px max(16px, env(safe-area-inset-left, 0px)) }
.wrap { max-width: 1320px; margin: 0 auto; display: grid; gap: 30px }
header { display: grid; gap: 8px }
h1 { font-family: var(--f-display); font-weight: 700; font-size: clamp(1.7rem, 3.2vw, 2.4rem); margin: 0; text-wrap: balance }
h2 { font-family: var(--f-display); font-weight: 700; font-size: 1.45rem; margin: 0; text-wrap: balance; display: flex; gap: 10px; align-items: center }
h3 { font-family: var(--f-display); font-weight: 600; font-size: .95rem; margin: 6px 0 0; color: var(--muted); letter-spacing: .06em; text-transform: uppercase }
h4 { font-family: var(--f-display); font-weight: 600; font-size: 1.08rem; margin: 0 }
p { margin: 0 }
.lead { color: var(--muted); max-width: 80ch }
.legend { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; font-size: .95rem }
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 99px; font-weight: 600; font-size: .9rem }
.chip.deckel { background: var(--deckel-bg); color: var(--deckel) } .chip.boden { background: var(--boden-bg); color: var(--boden) }
.chip.korpus { background: var(--korpus-bg); color: var(--korpus) } .chip.jump { background: transparent; border: 2px solid var(--jumper); color: var(--jumper) }
.figwrap { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 12px; overflow-x: auto }
.figwrap svg { display: block; width: 100%; min-width: 760px; height: auto }
figure { margin: 0; display: grid; gap: 10px }
figcaption { color: var(--muted); font-size: .95rem; max-width: 90ch }
.jlist { display: flex; flex-wrap: wrap; gap: 6px; align-items: center }
.jl { font-family: var(--f-mono); font-weight: 600; min-width: 30px; text-align: center; padding: 2px 6px; border-radius: 6px; border: 2px solid var(--jumper); color: var(--jumper) }
.zones { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(440px, 100%), 1fr)); gap: 20px; align-items: start }
.zone { display: grid; gap: 14px; background: var(--panel); border: 1px solid var(--line); border-top: 6px solid; border-radius: 14px; padding: 16px 18px 20px; min-width: 0 }
.zone.deckel { border-top-color: var(--deckel) } .zone.boden { border-top-color: var(--boden) } .zone.korpus { border-top-color: var(--korpus) }
.zone > p { color: var(--muted); font-size: .95rem }
.zone.deckel { grid-column: 1 / -1 }
.mods { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr)); gap: 12px; align-items: start }
.two { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(340px, 100%), 1fr)); gap: 18px; align-items: start }
.col { display: grid; gap: 10px; min-width: 0 }
.col p { font-size: .95rem }
.card { display: grid; gap: 6px; border: 1px solid var(--line); border-radius: 10px; padding: 12px 12px 8px }
.where { color: var(--muted); font-size: .9rem }
.wagos { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; align-items: start }
.wago { border-radius: 10px; padding: 10px 12px; display: grid; gap: 6px; border: 2px solid }
.wago.deckel { border-color: var(--deckel); background: var(--deckel-bg) } .wago.boden { border-color: var(--boden); background: var(--boden-bg) }
.whead { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; align-items: baseline }
.whead b { font-family: var(--f-display); font-size: 1.05rem } .whead span { color: var(--muted); font-size: .85rem }
.levers { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; font-size: .93rem }
.levers li { display: flex; gap: 8px; align-items: center }
.lever { flex: none; width: 14px; height: 14px; border-radius: 3px }
.lever.w5v { background: var(--w5v) } .lever.w33 { background: var(--w33) } .lever.wgnd { background: var(--wgnd) } .lever.wscl { background: var(--wscl) }
.muted { color: var(--muted) }
.tw { overflow-x: auto }
table.t { width: 100%; border-collapse: collapse; font-size: .93rem }
.t th { text-align: left; font-weight: 600; color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; padding: 4px 6px; border-bottom: 1px solid var(--line) }
.t td { padding: 6px; border-bottom: 1px solid var(--line); vertical-align: top }
.t tr:last-child td { border-bottom: 0 }
.t td:first-child { width: 26px }
.mono { font-family: var(--f-mono); font-size: .88rem; white-space: nowrap }
.id { font-family: var(--f-mono); font-weight: 600; font-size: .85rem; padding: 1px 7px; border-radius: 6px; white-space: nowrap }
.id.deckel { background: var(--deckel-bg); color: var(--deckel) } .id.boden { background: var(--boden-bg); color: var(--boden) } .id.korpus { background: var(--korpus-bg); color: var(--korpus) }
input[type=checkbox] { width: 18px; height: 18px; accent-color: var(--jumper); margin: 1px 0 0 }
input[type=checkbox]:focus-visible { outline: 2px solid var(--boden); outline-offset: 2px }
tr:has(input:checked) td:not(:first-child) { color: var(--muted); text-decoration: line-through; text-decoration-color: var(--muted) }
.notes { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr)); gap: 10px; padding: 0; margin: 0; list-style: none }
.notes li { background: var(--panel); border: 1px solid var(--line); border-left: 4px solid var(--muted); border-radius: 8px; padding: 10px 12px; font-size: .95rem }
.notes li.warn { border-left-color: var(--w5v) }
.progress { font-family: var(--f-mono); font-size: .9rem; color: var(--muted) }
/* SVG */
svg text { font-family: var(--f-body) }
svg .pcb { fill: var(--pcb) }
svg .cap { fill: var(--muted); font-family: var(--f-display); font-weight: 600; font-size: 14px; letter-spacing: .06em }
svg .small { fill: var(--pcbtext); font-size: 12.5px; opacity: .85 }
svg .bar { fill: var(--bar) }
svg .tcell { fill: var(--cell) }
svg .tcell.deckel { fill: var(--deckel) } svg .tcell.boden { fill: var(--boden) } svg .tcell.korpus { fill: var(--korpus) }
svg .tkey { font-family: var(--f-mono); font-size: 15px; font-weight: 600; fill: var(--muted) }
svg .tkey.on { fill: #fff }
svg .panel { fill: rgba(255,255,255,.06); stroke: rgba(255,255,255,.18) }
svg .sep { stroke: rgba(255,255,255,.12) }
svg .print { font-family: var(--f-mono); font-size: 14px; fill: var(--pcbtext); opacity: .55 }
svg .print.on { opacity: 1; font-weight: 600 }
svg .pin { fill: var(--yellow) } svg .pin.covered { fill: #fff; opacity: .85 }
svg .jumper { fill: var(--jumper) }
svg .keybox { fill: none; stroke: var(--pcbtext); opacity: .7 }
svg .key { font-family: var(--f-mono); font-size: 14px; font-weight: 600; fill: var(--pcbtext) }
svg .tag.deckel { fill: var(--deckel) } svg .tag.boden { fill: var(--boden) } svg .tag.korpus { fill: var(--korpus) }
svg .tagt { fill: #fff; font-size: 13px; font-weight: 600 }
svg .tagid { font-family: var(--f-mono); font-weight: 700 }
svg .header { fill: rgba(0,0,0,.25) }
svg .ypin { fill: var(--yellow) }
svg .lab { font-family: var(--f-mono); font-size: 11.5px; fill: var(--pcbtext); opacity: .6 }
svg .lab.on { fill: #fff; opacity: 1; font-weight: 600 }
svg .lcell.deckel { fill: var(--deckel) } svg .lcell.boden { fill: var(--boden) } svg .lcell.korpus { fill: var(--korpus) }
svg .lead { fill: none; stroke-width: 1.6 }
svg .lead.deckel { stroke: var(--deckel) } svg .lead.boden { stroke: var(--boden) } svg .lead.korpus { stroke: var(--korpus) }
svg .hatch { stroke: rgba(255,255,255,.2) }
"""


def page():
    jl = "".join(f'<span class="jl">{k}</span>' for k in JUMPER)
    deckel_mod = "".join(mod_card(n, w, r, "deckel") for n, w, r in MODULE_DECKEL)
    wd = "".join(wago_card(*w, "deckel") for w in WAGO_DECKEL)
    wb = "".join(wago_card(*w, "boden") for w in WAGO_BODEN)
    parts = [
        '<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>Verdrahtungsplan Peppa Box</title>',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700'
        '&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=Source+Sans+3:wght@400;600&display=swap">',
        f'<style>{CSS}</style></head><body><div class="wrap">',
        '<header><h1>Verdrahtungsplan Peppa Box</h1>',
        '<p class="lead">Stand 08.11.2026. Alle Anschlüsse am Klemmen-Aufsatz mit seinem Aufdruck: Federklemmen 1–8, A–H, I–P '
        'und die gelbe 40er-Stiftleiste (P05, P16 …). Jede Ader hat eine Nummer für das Fähnchen: D = Deckel-Strang, '
        'B = Boden, K = Korpus.</p>',
        '<div class="legend"><span class="chip deckel">Deckel</span><span class="chip boden">Boden</span>'
        '<span class="chip korpus">Korpus (Wände)</span><span class="chip jump">Jumper setzen</span>'
        '<span class="progress" id="prog"></span></div></header>',
        '<section><figure><div class="figwrap">', svg_aufsatz(), '</div>',
        '<figcaption>Klemmen-Aufsatz von oben, so wie er im Boden sitzt: gelbe 40er-Stiftleiste vorne (im Bild unten), '
        'also um 180° gedreht gegenüber dem Produktfoto. Hältst du ihn anders herum, gelten trotzdem die Aufdrucke. '
        'Grüner Balken = Jumper stecken; ohne Jumper ist die Federklemme tot. Aufdrucke abgelesen am Produktfoto '
        'BerryBase RPI-BKFHAT.</figcaption></figure>',
        f'<div class="jlist"><b>Jumper setzen (11):</b> {jl} <span class="muted">· alle anderen Reihen ohne Jumper</span></div></section>',
        '<div class="zones">',
        # Deckel
        '<section class="zone deckel"><h2><span class="chip deckel">Deckel</span>Was an den Deckel kommt</h2>',
        '<p>Alles hängt kopfüber unter dem Deckel. Kurze Adern von den Modulen in die drei WAGO; nur der '
        'Deckel-Strang (10 Adern, D1–D10) geht hinunter zum Aufsatz.</p>',
        '<h3>Module am Deckel</h3>', f'<div class="mods">{deckel_mod}</div>',
        '<div class="two"><div class="col"><h3>WAGO am Deckel (unter der Verteiler-Brücke)</h3>', f'<div class="wagos">{wd}</div></div>',
        '<div class="col"><h3>Deckel-Strang: 10 Adern zum Aufsatz</h3>',
        '<div class="tw">', adern_table(STRANG_DECKEL, "deckel", ("Ende am Deckel", "Ende am Aufsatz")), '</div>',
        '<p class="muted">Gebündelt rechts herausführen, so lang, dass der Deckel umgedreht neben der Box liegen kann (mit Schnur abmessen). '
        'Reserve rechts hinten auf dem Boden ablegen, Zugentlastung an einer Stelle.</p></div></div>',
        '</section>',
        # Boden
        '<section class="zone boden"><h2><span class="chip boden">Boden</span>Was auf den Boden kommt</h2>',
        '<p>Stapel (Akku-Board, Pi, Aufsatz), Verstärker MAX98357A, Elko und zwei WAGO in ihren Mulden hinten. '
        'Signaladern zum MAX höchstens 15 cm.</p>',
        '<h3>WAGO am Boden</h3>', f'<div class="wagos">{wb}</div>',
        '<h3>Adern am Boden</h3>',
        '<div class="tw">', adern_table(BODEN_ADERN, "boden", ("Aufsatz / Bauteil", "geht an")), '</div>',
        '<p>Steckkabel auf P16, P18, P19, P21 (und P05, P17, P27, P26) direkt über dem Stecker zur Seite knicken, '
        'dann den Niederhalter aufschrauben.</p>',
        '</section>',
        # Korpus
        '<section class="zone korpus"><h2><span class="chip korpus">Korpus</span>Was in den Wänden sitzt</h2>',
        '<p>Drehgeber und Klinke rechts, Lautsprecher vorne, USB-C hinten. Vor dem Einsetzen löten; '
        'angeschlossen wird von oben, wenn der Boden drin ist.</p>',
        '<div class="tw">', adern_table(KORPUS_ADERN, "korpus", ("Bauteil", "geht an")), '</div>',
        '</section>',
        '</div>',
        '<section><h2>Bevor Strom drauf kommt</h2><ul class="notes">',
        '<li class="warn">Kabel nur ohne Strom umstecken: <code>sudo poweroff</code>, dann Schalter am Akku-Board auf OFF.</li>',
        '<li class="warn">Multimeter auf Durchgang: zwischen +5V und GND sowie 3.3V und GND darf es <b>nicht</b> piepen.</li>',
        '<li class="warn">Elko: Streifen = Minus, kommt in WAGO GND A.</li>',
        '<li class="warn">RC522 und MPR121 nur an 3,3 V. Lautsprecher-Ausgänge des MAX nie mit GND verbinden.</li>',
        '<li>Litze für Federklemmen und WAGO: 11 mm abisolieren, verzinnen, bei offenem Hebel bis Anschlag, Zugtest.</li>',
        '<li>Ein-Taste: Beinchen unten rechts und unten links (am 08.11. gemessen: Durchgang nur gedrückt). Welche Ader in SCL, welche in GND, ist egal.</li>',
        '<li>Drehgeber-Taster bleibt Reserve. Später möglich: ein Bein an Klemme 5 (GND), das andere an einen freien gelben Stift, z. B. P06.</li>',
        '<li>Alternative für den MAX: Klemmen J (PWM0 = P18), L (PCMfs = P19), N (PCMo = P21). Die Steckkabel auf den gelben Stiften laufen; nicht umbauen.</li>',
        '</ul></section>',
        '</div>',
        r"""<script>
(function () {
  var KEY = 'peppa-verdrahtung-v5', state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { state = {}; }
  var boxes = Array.prototype.slice.call(document.querySelectorAll('input[data-k]'));
  var prog = document.getElementById('prog');
  function render() {
    var n = boxes.filter(function (b) { return b.checked; }).length;
    prog.textContent = n + ' von ' + boxes.length + ' Anschlüssen abgehakt';
  }
  boxes.forEach(function (b) {
    b.checked = !!state[b.dataset.k];
    b.addEventListener('change', function () {
      state[b.dataset.k] = b.checked;
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
      render();
    });
  });
  render();
})();
</script></body></html>""",
    ]
    return "".join(parts)


if __name__ == "__main__":
    out = os.path.join(ROOT, "plan", "verdrahtungsplan.html")
    s = page()
    with open(out, "w", encoding="utf-8") as f:
        f.write(s)
    print("ok", out, len(s), "Jumper", " ".join(JUMPER))
