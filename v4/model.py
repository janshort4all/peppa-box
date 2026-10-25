"""Musikbox v4 – parametrisches Druckmodell (PETG, Elegoo Centauri Carbon 2).

Koordinaten im Einbauzustand: x links→rechts, y vorne(0)→hinten, z hoch, alles in mm.
Jeder Wert steht in P mit Status:
  belegt      – aus Datenblatt/Herstellerangabe (Konzeptprüfung Kapitel 12)
  festgelegt  – unsere Gestaltungsentscheidung
  vorläufig   – Platzhalter, muss am echten Teil gemessen werden
  Probedruck  – wird mit einem Coupon auf deinem Drucker eingestellt
"""
import math
import numpy as np
import manifold3d as m3
from manifold3d import Manifold, CrossSection, JoinType

SEG = 72
m3.set_circular_segments(SEG)
P = {}


def par(name, v, s, q=""):
    P[name] = dict(v=v, s=s, q=q)
    return v


# =====================================================================================
# Parameter
# =====================================================================================
W = par("W", 140.0, "festgelegt", "Außenmaß Breite = Tiefe")
HB = par("HB", 140.0, "festgelegt", "Höhe Korpus. Echter Würfel; 124 mm reichen für Akku-Stapel + Kartenfach nicht")
R = par("R", 16.0, "festgelegt", "Eckradius außen")
WALL = par("WALL", 3.0, "festgelegt", "Wandstärke (7 Linien à 0,42)")
BASE_T = par("BASE_T", 4.0, "festgelegt", "Bodenplatte, abnehmbar, trägt die Elektronik; Korpus steht darauf")
CH_FLOOR = par("CH_FLOOR", 2.4, "festgelegt", "eigener Boden der Lautsprecherkammer im Korpus (Kammer bleibt dicht)")
SHADOW = par("SHADOW", 0.0, "festgelegt", "Bodenplatte außen exakt so groß wie der Korpus (bündig)")
EDGE_V = par("EDGE_V", 0.8, "festgelegt", "Fase 45° an Korpus-Unterkante und Boden-Oberkante: bilden zusammen eine V-Fuge, kaschiert kleinen Versatz")
BASE_CHAMF = par("BASE_CHAMF", 0.8, "festgelegt", "Fase an der Boden-Unterkante (Standkante, gegen Elefantenfuß)")
LIP_CLR = par("LIP_CLR", 0.2, "Probedruck", "Spiel Zentrierkragen zur Innenwand je Seite (Coupon C8)")
FLOOR = BASE_T
CHAMF = par("CHAMF", 0.5, "festgelegt", "Fase Unterkante gegen Elefantenfuß (D2)")
LID_T = par("LID_T", 6.0, "festgelegt", "Deckelstärke (Schrauben von unten brauchen Fleisch)")
LID_SINK = par("LID_SINK", 1.2, "festgelegt", "Deckel liegt so tief unter der Kante")
LEDGE = par("LEDGE", 2.5, "festgelegt", "Auflage-Schräge 45° innen")
GAP_LID = par("GAP_LID", 0.4, "Probedruck", "Spalt Deckel–Wand je Seite")
SKIN = par("SKIN", 0.7, "festgelegt", "beige Deckschicht über orangem Kern (D1)")
CLR = par("CLR", 0.3, "Probedruck", "Spiel für Passungen")
PILOT = par("PILOT", 2.5, "Probedruck", "Kernloch für 3-mm-Kunststoffschraube in PETG")
HOLE3 = par("HOLE3", 3.4, "festgelegt", "Durchgangsloch 3-mm-Schraube")
BOSS_D = par("BOSS_D", 9.0, "festgelegt", "Dom-Ø, groß genug für spätere M3-Einsätze")
PILOT25 = par("PILOT25", 2.1, "Probedruck", "Kernloch M2,5 (Akku-Board)")

LID_TOP = HB - LID_SINK
LID_BOT = LID_TOP - LID_T
RING_T = 3.0
RING_Z0 = LID_BOT - RING_T
RING_OFF = LEDGE + GAP_LID + 0.5
RING_W = 8.0

# Front, Stoff, Lautsprecher
SEAT = par("SEAT", (12.0, 128.0, 12.0, 128.0), "festgelegt", "Stoffrahmen-Vertiefung x0,x1,z0,z1")
SEAT_R = 9.0
SEAT_D = par("SEAT_D", 3.8, "festgelegt", "Tiefe Stoffrahmen-Sitz")
FRONT_D = SEAT_D + 4.2
FAB_T = par("FAB_T", 0.6, "vorläufig", "Stoffdicke, Stoff noch nicht gekauft")
FR_T = par("FR_T", 3.0, "festgelegt", "Stoffrahmen-Dicke")
FR_BORDER = par("FR_BORDER", 6.0, "festgelegt", "Rahmenrand")
PIN_D = par("PIN_D", 4.0, "festgelegt", "Stift am Stoffrahmen")
PIN_HOLE = par("PIN_HOLE", 4.1, "Probedruck", "Loch für Rahmenstift (Coupon C4: 4,0 / 4,1 / 4,2)")
SPK_X = par("SPK_X", 70.0, "festgelegt", "Lautsprecher Mitte x")
SPK_Z = par("SPK_Z", 70.0, "festgelegt", "Lautsprecher Mitte z")
SPK_CUT = par("SPK_CUT", 73.0, "belegt", "Einbauausschnitt Visaton FRS 8")
SPK_FRAME = par("SPK_FRAME", 78.0, "belegt", "Außenmaß Korb (Kante)")
SPK_FRAME_R = par("SPK_FRAME_R", 21.0, "vorläufig", "Eckradius Korb, aus 93 mm Diagonale abgeleitet")
SPK_FLANGE = par("SPK_FLANGE", 4.5, "belegt", "Frontflansch")
SPK_DEPTH = par("SPK_DEPTH", 40.0, "belegt", "Gesamttiefe")
SPK_MAG = par("SPK_MAG", 60.0, "belegt", "Magnet-Ø")
SPK_PITCH = par("SPK_PITCH", 58.5, "vorläufig", "Lochabstand (Zeichnungswert ohne Beschriftung)")
BAY_D = par("BAY_D", 9.6, "festgelegt", "Tiefe Lautsprecher-Mulde ab Front")
DIV_Y = par("DIV_Y", 48.0, "festgelegt", "Vorderkante Trennwand Lautsprecherkammer")
CH_Z = par("CH_Z", 122.0, "festgelegt", "Unterkante Kammerdecke")

# Deckel-Bedienung (aus v3)
PADS = par("PADS", {"zurück": (30, 30, 22), "play": (70, 30, 30), "vor": (110, 30, 22), "schlaf": (70, 64, 18)},
           "festgelegt", "Touch-Felder x, y, Ø")
PAD_POCKET = par("PAD_POCKET", 2.0, "Probedruck", "Tasche unter dem Feld → 3,3 mm Kunststoff über dem Kupfer")

# Karte und Kartenfach
CARD_W = par("CARD_W", 70.0, "festgelegt", "Karte Breite")
CARD_H = par("CARD_H", 112.0, "festgelegt", "Karte Höhe (70 sichtbar + 42 im Fach)")
CARD_T = par("CARD_T", 4.0, "festgelegt", "Karte Dicke")
CARD_IN = par("CARD_IN", 42.0, "festgelegt", "Einstecktiefe")
SLOT_Y = par("SLOT_Y", 116.0, "festgelegt", "Schlitzmitte auf dem Deckel")
TILT = par("TILT", 8.0, "festgelegt", "Neigung der Karte nach hinten")
NFC_D = par("NFC_D", 25.0, "belegt", "NFC-Aufkleber Ø")
NFC_T = par("NFC_T", 0.4, "vorläufig", "NFC-Aufkleber Dicke")
RC_L = par("RC_L", 60.0, "vorläufig", "RC522 Platine Länge")
RC_B = par("RC_B", 40.0, "vorläufig", "RC522 Platine Breite")
RC_T = par("RC_T", 1.6, "vorläufig", "RC522 Platinendicke")
RC_ANT = par("RC_ANT", 20.0, "vorläufig", "Antennenmitte ab Platinenende")
RC_COMP = par("RC_COMP", 3.0, "vorläufig", "Bauteilhöhe auf der Rückseite")

# Ein-Taste
BTN_X = par("BTN_X", 124.5, "festgelegt", "Ein-Taste x (hinten rechts)")
BTN_Y = par("BTN_Y", 108.0, "festgelegt", "Ein-Taste y")
BTN_D = par("BTN_D", 12.0, "festgelegt", "Tastenkopf-Ø")
DISH_D = par("DISH_D", 20.0, "festgelegt", "Mulde um die Taste")
DISH_DEPTH = par("DISH_DEPTH", 1.5, "festgelegt", "Taste liegt so tief (gegen versehentliches Drücken)")
SW = par("SW", 12.0, "belegt", "Kurzhubtaster 12 × 12")
SW_H = par("SW_H", 7.3, "vorläufig", "Tasterhöhe gesamt (Quellen: 7,3 bzw. 6,5)")

# Rechts: Drehgeber, Klinke
ENC_Y = par("ENC_Y", 84.0, "festgelegt", "Drehgeber y")
ENC_Z = par("ENC_Z", 60.0, "festgelegt", "Drehgeber z")
ENC_HOLE = par("ENC_HOLE", 7.4, "Probedruck", "Loch für M7-Gewinde")
ENC_WALL = par("ENC_WALL", 2.0, "vorläufig", "Wand am Drehgeber (Gewindelänge unbekannt)")
ENC_OUT = par("ENC_OUT", 14.0, "vorläufig", "Achse ragt so weit aus der Wand")
ENC_SLOT = par("ENC_SLOT", 1.0, "vorläufig", "Schlitzbreite Achse")
KNOB_D = par("KNOB_D", 34.0, "festgelegt", "Knopf-Ø")
KNOB_L = par("KNOB_L", 16.0, "festgelegt", "Knopflänge")
NUT_REC = par("NUT_REC", (14.0, 3.0), "vorläufig", "Aussparung für Mutter+Scheibe im Knopf Ø, Tiefe")
JK_Y = par("JK_Y", 84.0, "festgelegt", "Klinke y")
JK_Z = par("JK_Z", 24.0, "festgelegt", "Klinke z")
JK_HOLE = par("JK_HOLE", 6.2, "vorläufig", "Loch für Klinkengewinde (Gewinde unbekannt)")
JK_WALL = par("JK_WALL", 2.0, "vorläufig", "Wand an der Klinke")

# Links: Riemen, USB-C
STRAP_Y = par("STRAP_Y", 104.0, "festgelegt", "Riemenpunkt y")
STRAP_Z = par("STRAP_Z", 118.0, "festgelegt", "Riemenpunkt z")
STRAP_HOLE = par("STRAP_HOLE", 5.2, "vorläufig", "Buchschraube noch nicht gekauft")

# Boden (abnehmbar) – Schrauben von unten in Dome im Korpus
BASE_BOSSES = par("BASE_BOSSES", [(8.6, 8.6), (131.4, 8.6), (7.7, 47.0), (132.3, 47.0), (8.6, 131.4), (131.4, 131.4)],
                  "festgelegt", "Bodenschrauben: 4 Ecken + 2 an der Kammerwand (vordere Dome stehen dicht in der Kammer)")
BOSS_H = par("BOSS_H", 14.0, "festgelegt", "Höhe der Bodendome im Korpus; Kernloch 12 tief")
CSK = par("CSK", (6.2, 3.4), "festgelegt", "Senkung für Kunststoffschraube 3,0 × 14 Senkkopf (Ø Kopf, Ø Loch)")
LIP = par("LIP", (1.6, 3.0), "festgelegt", "Zentrierkragen der Bodenplatte im hinteren Teil (Breite, Höhe)")

# Elektronik-Stapel: Acrylplatte → Zellen → Akku-Board → Pi → Klemmen-Aufsatz
UPS = par("UPS", (85.0, 56.0), "belegt", "Akku-Board Grundriss")
ACRYL = par("ACRYL", (85.0, 55.0), "gemessen", "Acrylplatte unter dem Stapel (von dir gemessen)")
STACK_H = par("STACK_H", 70.0, "gemessen", "Acrylplatte bis Oberkante graue Klemmen, ohne Kabel")
PINS_H = par("PINS_H", 60.0, "gemessen", "Acrylplatte bis Spitzen der gelben Stifte")
STACK_PAT = par("STACK_PAT", (58.0, 49.0), "gemessen", "Lochbild der Bolzen unter der Acrylplatte")
PAT_END = par("PAT_END", 3.5, "vorläufig", "Lochmitte bis Pi-Ende des Stapels (Pi-Norm); ±3 mm deckt der Freiraum ab")
OVERHANG = par("OVERHANG", 20.0, "belegt", "Akku-Board steht so weit über den Pi hinaus (85 − 65), BOOT-Taste dort")
UPS_LEVEL = par("UPS_LEVEL", 35.0, "vorläufig", "Acrylplatte bis Oberkante Akku-Board (Zellen + Board)")
CLAMP_Z = par("CLAMP_Z", 52.0, "vorläufig", "Unterkante der Klemmblöcke über der Acrylplatte")
STACK_X0 = par("STACK_X0", 9.0, "festgelegt", "Stapel links; Überhang mit BOOT-Taste zeigt nach links")
STACK_Y0 = par("STACK_Y0", 55.5, "festgelegt", "Stapel vorne = Kante mit den gelben Stiften; Anschlusskante (USB-C, Schalter) zeigt nach hinten")
PAD_H = par("PAD_H", 3.5, "festgelegt", "Auflagen unter der Acrylplatte")
PAD_REC = par("PAD_REC", (7.0, 2.4), "festgelegt", "Mulde in jeder Auflage (Ø, Tiefe): vorhandene Schraubenköpfe oder Muttern passen hinein")
HOLE25 = par("HOLE25", 2.9, "festgelegt", "Durchgang M2,5")
CB25 = par("CB25", (6.4, 2.2), "festgelegt", "Senkbohrung von unten für Kopf/Mutter M2,5 (Ø, Tiefe)")
WIRE_CLR = par("WIRE_CLR", 15.0, "festgelegt", "Platz für die Kabel an jeder Klemmreihe")
STACK_CLR = par("STACK_CLR", 3.0, "festgelegt", "Luft rings um den Stapel")
USB_PLUG = par("USB_PLUG", 20.0, "festgelegt", "Platz hinter der Anschlusskante: Stecker am Akku-Board gewinkelt oder höchstens 20 mm lang")
USB_PANEL = par("USB_PANEL", {"x": 114.0, "z": 60.0, "loch": 16.4, "mutter": 24.0, "tiefe": 20.0}, "vorläufig",
                "USB-C-Einbaubuchse in der Rückwand (rund M16 angenommen, Produkt noch offen)")
AUDIO_PLUG = par("AUDIO_PLUG", 20.0, "vorläufig", "Platz hinter der Klinke des Pi: Klinkenstecker 90° gewinkelt (Goobay 67782)")
MAXB = par("MAXB", (19.0, 18.0, 8.0), "vorläufig", "Verstärker-Klon L, B, Höhe mit Klemme")
MPRB = par("MPRB", (25.0, 20.0, 4.0), "vorläufig", "MPR121-Modul L, B, Höhe")
WAGO5 = par("WAGO5", (30.0, 18.6, 8.4), "belegt", "WAGO 221-425 B, T, H")
WAGO3 = par("WAGO3", (18.6, 18.6, 8.4), "belegt", "WAGO 221-423 B, T, H")
REAR_Y = STACK_Y0 + UPS[1] + 1.0          # hinterer Streifen hinter der Anschlusskante
BRIDGE_Y = par("BRIDGE_Y", (74.0, 98.0), "festgelegt", "Verteiler-Brücke am Deckelrahmen: MPR121 + Klemmen für 3,3 V, SCL, GND B")

LS_X = par("LS_X", (24.0, 116.0), "festgelegt", "Deckelschrauben hinten x")
LS_Z = par("LS_Z", 124.0, "festgelegt", "Deckelschrauben hinten z")

# =====================================================================================
# Helfer
# =====================================================================================


def rr(x0, y0, x1, y1, r):
    w, d = x1 - x0, y1 - y0
    r = max(min(r, w / 2 - 0.01, d / 2 - 0.01), 0.05)
    return CrossSection.square([w - 2 * r, d - 2 * r]).translate([x0 + r, y0 + r]).offset(r, JoinType.Round, circular_segments=SEG)


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def slab(cs, z0, z1):
    return Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def ext_xz(cs, y0, y1):          # Profil in (x, z), Extrusion entlang y
    return Manifold.extrude(cs, y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def ext_yz(cs, x0, x1):          # Profil in (y, z), Extrusion entlang x
    return Manifold.extrude(cs, x1 - x0).rotate([90, 0, 90]).translate([x0, 0, 0])


def cyl_z(x, y, z0, h, r, r2=None):
    return Manifold.cylinder(h, r, r if r2 is None else r2, SEG).translate([x, y, z0])


def cyl_x(x0, x1, y, z, r):
    return Manifold.cylinder(x1 - x0, r, r, SEG).rotate([0, 90, 0]).translate([x0, y, z])


def cyl_y(y0, y1, x, z, r):
    return Manifold.cylinder(y1 - y0, r, r, SEG).rotate([-90, 0, 0]).translate([x, y0, z])


def tear(r, a=0.0, b=0.0, cap=None):
    """Tropfenprofil (Spitze nach +2. Achse), druckbar ohne Stütze in senkrechten Wänden."""
    c = CrossSection.circle(r, SEG)
    t = CrossSection.hull(c + CrossSection([[(-r * 0.7071, r * 0.7071), (r * 0.7071, r * 0.7071), (0, r * 1.4142)]]))
    if cap is not None:
        t = t ^ CrossSection.square([4 * r, r + cap]).translate([-2 * r, -r])
    return t.translate([a, b])


def U(lst):
    lst = [m for m in lst if m is not None and not m.is_empty()]
    return Manifold.batch_boolean(lst, m3.OpType.Add) if lst else Manifold()


OUT = rr(0, 0, W, W, R)
INN = OUT.offset(-WALL, JoinType.Round, circular_segments=SEG)
INN_SLAB = lambda z0, z1: slab(INN, z0, z1)


# =====================================================================================
# Korpus
# =====================================================================================

def korpus():
    z0 = BASE_T
    body = Manifold.batch_hull([slab(OUT.offset(-EDGE_V, JoinType.Round), z0, z0 + 0.01), slab(OUT, z0 + EDGE_V, HB - 1.0),
                                slab(OUT.offset(-1.0, JoinType.Round), HB - 0.01, HB)])
    body = body - slab(INN, z0 - 1, HB + 1)                                  # unten offen
    add = []
    # eigener Boden der Lautsprecherkammer
    add.append(INN_SLAB(z0, z0 + CH_FLOOR) ^ box(0, 0, 0, W, DIV_Y + 3, HB))

    # --- Frontplatte (Stoffsitz) und Lautsprecher-Mulde ---
    sx0, sx1, sz0, sz1 = SEAT
    def seat_prof(dz):
        return rr(sx0, sz0, sx1, sz1 + dz, SEAT_R)
    plate_front = rr(sx0 - 3, FLOOR - 12.5, sx1 + 3, sz1 + 3, SEAT_R + 3)
    plate_back = rr(sx0 - 3, FLOOR - 12.5, sx1 + 3, sz1 + 3 - FRONT_D, SEAT_R + 3)
    add.append(Manifold.batch_hull([ext_xz(plate_front, 0, 0.01), ext_xz(plate_back, FRONT_D - 0.01, FRONT_D)]))
    bh = SPK_FRAME / 2 + 2
    bay_r = SPK_FRAME_R + 2
    bay_front = rr(SPK_X - bh, SPK_Z - bh, SPK_X + bh, SPK_Z + bh + BAY_D + 1, bay_r)
    bay_back = rr(SPK_X - bh, SPK_Z - bh, SPK_X + bh, SPK_Z + bh, bay_r)
    pw_front = rr(SPK_X - bh - 3, FLOOR - 27.0, SPK_X + bh + 3, SPK_Z + bh + BAY_D + 3, bay_r + 3)
    pw_back = rr(SPK_X - bh - 3, FLOOR - 27.0, SPK_X + bh + 3, SPK_Z + bh + 3 - 3, bay_r + 3)
    add.append(Manifold.batch_hull([ext_xz(pw_front, 0, 0.01), ext_xz(pw_back, BAY_D + 3 - 0.01, BAY_D + 3)]))

    # Lautsprecher-Dome hinter der Mulde (mit 45°-Stütze darunter)
    hp = SPK_PITCH / 2
    spk_holes = [(SPK_X + sx * hp, SPK_Z + sz * hp) for sx in (-1, 1) for sz in (-1, 1)]
    y0 = BAY_D + 3
    for (x, z) in spk_holes:
        add.append(ext_xz(tear(BOSS_D / 2).mirror([0, 1]).translate([x, z]), y0 - 0.5, y0 + 7))   # Tropfen nach unten: ohne Stütze

    # Trennwand, Kammerdecke
    add.append(INN_SLAB(FLOOR, CH_Z) ^ box(0, DIV_Y, 0, W, DIV_Y + 3, HB))
    add.append(INN_SLAB(CH_Z, CH_Z + 3) ^ box(0, 0, 0, W, DIV_Y + 3, HB))

    # Zungen-Aufnahmen vorne (für den Deckelrahmen)
    tongue_blocks = []
    for x in (40.0, 100.0):
        blk = box(x - 9, 7.4, CH_Z + 3, x + 9, 14.4, RING_Z0 - 0.5)
        tongue_blocks.append(blk)
    add += tongue_blocks

    # Deckelauflage 45°
    z0 = LID_BOT - LEDGE
    ledge = slab(INN.offset(0.6, JoinType.Round), z0, LID_BOT) - Manifold.batch_hull([slab(INN.offset(0.03, JoinType.Round), z0 - 0.03, z0), slab(INN.offset(-LEDGE - 1.0, JoinType.Round), LID_BOT + 0.99, LID_BOT + 1.0)])
    add.append(ledge)                                                          # ringsum geschlossen: Elektronik kommt von unten

    # Dome hinten für die Deckelschrauben
    for x in LS_X:
        add.append(Manifold.batch_hull([box(x - 7, W - WALL - 2.4, LS_Z - 7, x + 7, W - WALL + 0.1, RING_Z0 - 0.5),
                                        box(x - 7, W - WALL - 0.01, LS_Z - 7 - 2.4, x + 7, W - WALL + 0.1, RING_Z0 - 0.5)]))

    # Dome für die Bodenschrauben (stehen auf der Druckplatte, kein Überhang)
    for (x, y) in BASE_BOSSES:
        add.append(cyl_z(x, y, BASE_T, BOSS_H, BOSS_D / 2))

    body = U([body] + [a ^ slab(OUT, BASE_T, HB) for a in add])

    cut = []
    # Stoffsitz und Mulde (Decke 45°)
    cut.append(Manifold.batch_hull([ext_xz(seat_prof(1.0), -1, 0), ext_xz(seat_prof(-SEAT_D), SEAT_D - 0.01, SEAT_D)]))
    cut.append(Manifold.batch_hull([ext_xz(bay_front, -1, 0), ext_xz(bay_back, BAY_D - 0.01, BAY_D)]))
    cut.append(box(64, -1, sz0 - 0.01, 76, SEAT_D, sz0 + 2.0))                     # Hebelkerbe unten
    # Lautsprecherausschnitt (Tropfen, oben gekappt → dichtet unter dem Flansch)
    cut.append(ext_xz(tear(SPK_CUT / 2, SPK_X, SPK_Z, cap=SPK_CUT / 2 + 1.0), BAY_D - 1, BAY_D + 4))
    for (x, z) in spk_holes:
        cut.append(cyl_y(BAY_D - 1, y0 + 6, x, z, PILOT / 2))
    # Stiftlöcher für den Stoffrahmen
    for (x, z) in frame_pins():
        cut.append(cyl_y(SEAT_D - 0.5, SEAT_D + 2.8, x, z, PIN_HOLE / 2))
    # Kabeldurchführung Trennwand (mit Heißkleber abdichten)
    cut.append(ext_xz(tear(3.0, 118, 14), DIV_Y - 1, DIV_Y + 4))
    # Zungenschlitze
    for x in (40.0, 100.0):
        cut.append(box(x - 6.2, 9.2, CH_Z + 3.4, x + 6.2, 11.6, RING_Z0))
    # Deckelschrauben hinten: Loch + Senkung außen
    for x in LS_X:
        cut.append(ext_xz(tear(HOLE3 / 2, x, LS_Z), W - WALL - 3, W - 0.8))
        cut.append(Manifold.cylinder(2.9, 1.5, 4.4, 61).rotate([-90, 0, 0]).translate([x, W - 1.9, LS_Z]))
    # Rechts: Drehgeber und Klinke
    cut.append(ext_yz(tear(ENC_HOLE / 2, ENC_Y, ENC_Z), W - WALL - 1, W + 1))
    cut.append(cyl_x(W - WALL - 1, W - ENC_WALL, ENC_Y, ENC_Z, 11))
    cut.append(ext_yz(tear(JK_HOLE / 2, JK_Y, JK_Z), W - WALL - 1, W + 1))
    cut.append(cyl_x(W - WALL - 1, W - JK_WALL, JK_Y, JK_Z, 9))
    # Links: Riemen
    cut.append(ext_yz(tear(STRAP_HOLE / 2, STRAP_Y, STRAP_Z), -1, WALL + 1))
    # Hinten: USB-C-Einbaubuchse (Tropfenform, druckbar) und Lüftungsschlitze (G11, max. 2 mm)
    up = USB_PANEL
    cut.append(ext_xz(tear(up["loch"] / 2, up["x"], up["z"]), W - WALL - 1, W + 1))
    for i in range(6):
        cut.append(ext_xz(rr(30 + i * 6.4, 50, 32 + i * 6.4, 66, 1.0), W - WALL - 1, W + 1))
    # Kernlöcher der Bodendome (von unten, blind – Kammer bleibt dicht)
    for (x, y) in BASE_BOSSES:
        cut.append(cyl_z(x, y, BASE_T - 1, 1 + BOSS_H - 2, PILOT / 2))
    return body - U(cut)


def frame_pins():
    sx0, sx1, sz0, sz1 = SEAT
    m = FR_BORDER / 2 + FAB_T + CLR
    return [(sx0 + m, sz0 + 30), (sx0 + m, sz1 - 30), (sx1 - m, sz0 + 30), (sx1 - m, sz1 - 30),
            ((sx0 + sx1) / 2 - 30, sz0 + m), ((sx0 + sx1) / 2 + 30, sz0 + m)]


def usb_panel():
    up = USB_PANEL
    return up["x"], up["z"]


# =====================================================================================
# Deckel (zweifarbig) und Deckelrahmen
# =====================================================================================
LID_CS = INN.offset(-GAP_LID, JoinType.Round, circular_segments=SEG)
RING_SCREWS = [(22.0, 3 + RING_OFF + RING_W / 2), (118.0, 3 + RING_OFF + RING_W / 2),
               (3 + RING_OFF + RING_W / 2, 68.0), (W - 3 - RING_OFF - RING_W / 2, 70.0),
               (45.0, W - 3 - RING_OFF - RING_W / 2), (95.0, W - 3 - RING_OFF - RING_W / 2)]
POCKET_SCREWS = [(70 - 39.9, 116.0), (70 + 39.9, 116.0)]
POCKET_GRIP = 8.0      # so viel Kartenfach wird von der Schraube unter dem Deckel geklemmt


def tri(x0, y0, s, left):
    if left:
        return [(x0, y0), (x0 + s, y0 + s * 0.62), (x0 + s, y0 - s * 0.62)]
    return [(x0, y0 + s * 0.62), (x0, y0 - s * 0.62), (x0 + s, y0)]


def pad_symbols():
    def poly(p):
        a = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
        return CrossSection([p if a > 0 else p[::-1]])
    s = []
    px, py, _ = PADS["zurück"]; s += [poly(tri(px - 9, py, 8, True)), poly(tri(px + 0.5, py, 8, True))]
    px, py, _ = PADS["vor"]; s += [poly(tri(px - 8.5, py, 8, False)), poly(tri(px + 0.5, py, 8, False))]
    px, py, _ = PADS["play"]
    s += [poly(tri(px - 9, py, 9.5, False)), CrossSection.square([2.6, 11.5]).translate([px + 2.5, py - 5.75]),
          CrossSection.square([2.6, 11.5]).translate([px + 6.6, py - 5.75])]
    px, py, _ = PADS["schlaf"]
    s += [CrossSection.circle(5.2, SEG).translate([px - 0.6, py]) - CrossSection.circle(4.5, SEG).translate([px + 2.0, py + 1.8])]
    for (x, y, d) in PADS.values():
        s.append(CrossSection.circle(d / 2, SEG).translate([x, y]) - CrossSection.circle(d / 2 - 1.1, SEG).translate([x, y]))
    out = s[0]
    for t in s[1:]:
        out = out + t
    return out


def card_frame():
    """Matrix für Karten-Koordinaten (u quer, v nach unten entlang der Karte, w Dicke nach hinten)."""
    a = math.radians(TILT)
    ex = np.array([1.0, 0, 0])
    d = np.array([0, -math.sin(a), -math.cos(a)])
    n = np.array([0, math.cos(a), -math.sin(a)])
    o = np.array([70.0, SLOT_Y, LID_TOP])
    return np.column_stack([ex, d, n, o]).astype(np.float32)


def to_world(m):
    return m.transform(card_frame())


def slot_cut():
    c = CLR
    return to_world(box(-CARD_W / 2 - 0.75, -15, -CARD_T / 2 - 0.4, CARD_W / 2 + 0.75, 12, CARD_T / 2 + 0.4))


def deckel():
    core = slab(LID_CS, LID_BOT, LID_TOP - SKIN)
    skin = slab(LID_CS, LID_TOP - SKIN, LID_TOP)
    sym = pad_symbols()
    skin = skin - slab(sym, LID_TOP - SKIN - 0.05, LID_TOP + 1)
    cut = [slot_cut()]
    # Taste: Mulde und Bohrung
    cut.append(cyl_z(BTN_X, BTN_Y, LID_TOP - DISH_DEPTH, 5, DISH_D / 2))
    cut.append(cyl_z(BTN_X, BTN_Y, LID_BOT - 1, LID_T + 2, BTN_D / 2 + 0.25))
    # Taschen für Kupferband unter den Feldern (von unten)
    for (x, y, d) in PADS.values():
        cut.append(cyl_z(x, y, LID_BOT - 1, 1 + PAD_POCKET, d / 2 - 1.0))
    # Kernlöcher von unten
    for (x, y) in RING_SCREWS + POCKET_SCREWS:
        cut.append(cyl_z(x, y, LID_BOT - 1, 1 + 4.5, PILOT / 2))
    cu = U(cut)
    return core - cu, skin - cu


def deckelrahmen():
    ring = slab(INN.offset(-RING_OFF, JoinType.Round) - INN.offset(-RING_OFF - RING_W, JoinType.Round), RING_Z0, LID_BOT)
    parts = [ring]
    # Zungen vorne
    for x in (40.0, 100.0):
        parts.append(box(x - 6, 9.4, CH_Z + 3.8, x + 6, 11.4, RING_Z0 + 0.1))
    # Blöcke hinten mit waagerechtem Kernloch
    for x in LS_X:
        parts.append(box(x - 7, W - WALL - 2.4 - 0.4 - 10, LS_Z - 7, x + 7, W - WALL - 2.4 - 0.4, LID_BOT))
    # Steg zum Tasterhalter + Halter
    sw_bot = act_top() - SW_H
    hw = SW / 2 + 0.2 + 3.1
    parts.append(box(BTN_X - hw, BTN_Y - hw, sw_bot - 3, BTN_X + hw, BTN_Y + hw, RING_Z0 + 0.1))   # Boden 3 mm: trägt kräftiges Drücken
    parts.append(box(BTN_X - hw, BTN_Y - hw, RING_Z0, W - 3 - RING_OFF - 1, BTN_Y + hw, LID_BOT))
    # Verteiler-Brücke quer über den Rahmen: MPR121 und Klemmen hängen darunter (kurze Wege zu Touchfeldern, NFC, Taste)
    by0, by1 = BRIDGE_Y
    parts.append(slab(INN.offset(-RING_OFF - 0.5, JoinType.Round) ^ CrossSection.square([W, by1 - by0]).translate([0, by0]), RING_Z0, LID_BOT))
    for (name, x0, y0, w, d, h) in lid_layout():
        parts.append(pocket(x0, y0, w, d, RING_Z0, up=False))
    r = U(parts)
    cut = []
    for (x, y) in RING_SCREWS:
        cut.append(cyl_z(x, y, RING_Z0 - 1, RING_T + 2, HOLE3 / 2))
    for x in LS_X:
        cut.append(ext_xz(tear(PILOT / 2).mirror([0, 1]).translate([x, LS_Z]), W - WALL - 2.4 - 0.4 - 9, W))
    s = SW / 2 + 0.2
    cut.append(box(BTN_X - s, BTN_Y - s, sw_bot, BTN_X + s, BTN_Y + s, RING_Z0 + 0.01))
    cut.append(cyl_z(BTN_X, BTN_Y, RING_Z0 - 0.01, RING_T + 1, COLLAR[2] + 0.5))
    cut.append(cyl_z(BTN_X, BTN_Y, RING_Z0 - 2.9, 2.9, SW / 2 + 0.2, COLLAR[2] + 0.5))     # 45°-Trichter, druckbar kopfüber
    cut.append(box(BTN_X - 7, BTN_Y - 3.5, sw_bot - 4, BTN_X + 7, BTN_Y + 3.5, sw_bot + 0.01))   # Beinchen/Kabel
    cut.append(box(BTN_X - 3, BTN_Y - hw - 1, sw_bot, BTN_X + 3, BTN_Y - 5, sw_bot + 4))         # Kabelausgang
    return r - U(cut)


def lid_layout():
    """Module unter der Verteiler-Brücke: (Name, x0, y0, w, d, Höhe), Innenmaße der Mulden."""
    by0, by1 = BRIDGE_Y
    out, x = [], 15.0 + 1.2
    for name, (bw, bt, bh) in (("WAGO GND B", WAGO5), ("WAGO 3,3 V", WAGO3), ("WAGO SCL", WAGO3), ("Touch-Modul MPR121", MPRB)):
        w, d = bw + 2 * CLR, bt + 2 * CLR
        y0 = (by0 + by1) / 2 - d / 2
        out.append((name, x, y0, w, d, bh))
        x += w + 2 * 1.2 + 2.0
    return out


COLLAR = (2.5, 0.5, 8.5)          # Kegelhöhe, Zylinderhöhe, Radius
PLUNGER_L = 4.0


def act_top():
    return LID_BOT - COLLAR[0] - COLLAR[1] - PLUNGER_L - 0.05


def taste():
    """Kappe: Kopf in der Deckelbohrung, Kegelkragen als Anschlag unter dem Deckel, Stößel auf den Taster.
    Druck kopfüber: Kegel wächst unter 45° – keine Stütze."""
    ch, cy, cr = COLLAR
    head = Manifold.batch_hull([cyl_z(BTN_X, BTN_Y, LID_BOT, LID_T - DISH_DEPTH - 0.5, BTN_D / 2),
                                cyl_z(BTN_X, BTN_Y, LID_TOP - DISH_DEPTH - 0.01, 0.01, BTN_D / 2 - 0.5)])
    cone = cyl_z(BTN_X, BTN_Y, LID_BOT - ch, ch + 0.01, cr, BTN_D / 2)
    cylr = cyl_z(BTN_X, BTN_Y, LID_BOT - ch - cy, cy + 0.01, cr)
    plunger = cyl_z(BTN_X, BTN_Y, LID_BOT - ch - cy - PLUNGER_L, PLUNGER_L + 0.01, 2.5)
    return U([head, cone, cylr, plunger])


# =====================================================================================
# Kartenfach mit RC522-Schiene
# =====================================================================================
V_LID = (LID_TOP - LID_BOT) / math.cos(math.radians(TILT))
V_TAG = CARD_IN - 1.0 - NFC_D / 2


def rc_local():
    """RC522-Lage im Kartenrahmen: u0,u1,v0,v1,w0,w1 der Platine."""
    u0 = -RC_ANT
    v0 = V_TAG - RC_B / 2
    w0 = CARD_T / 2 + 0.4 + 1.2 + 0.6
    return (u0, u0 + RC_L, v0, v0 + RC_B, w0, w0 + RC_T)


def kartentasche():
    wi = CARD_W / 2 + 0.75
    ti = CARD_T / 2 + 0.4
    depth = CARD_IN + 0.5
    outer = box(-wi - 2, 0, -ti - 2, wi + 2, depth + 2, ti + 1.2)
    u0, u1, v0, v1, w0, w1 = rc_local()
    # Rückplatte bis unter die RC522-Platine, mit zwei Schienen (Platine wird seitlich eingeschoben)
    back = box(u0 - 3, V_LID, ti, u1 + 2, v1 + 3, ti + 1.2)
    rails = []
    for (va, vb, gv0, gv1) in ((v0 - 3, v0 + 1.5, v0 - 0.3, v0 + 1.5), (v1 - 1.5, v1 + 3, v1 - 1.5, v1 + 0.3)):
        rail = box(u0 - 3, va, ti + 1.2, u1 + 2, vb, w1 + 1.6)
        rail = rail - box(u0 - 1, gv0, w0 - 0.2, u1 + 3, gv1, w1 + 0.3)
        rails.append(rail)
    stop = box(-wi - 8.5, v0 - 3, ti + 1.2, u0 - 0.5, v1 + 3, w1 + 1.6)      # Anschlag an der Antennenseite, reicht bis zur Druckplatte
    # seitliche Wangen über die ganze Höhe: tragen die Schraublöcher und liegen beim Druck auf der Platte
    ears = [box(-wi - 8.5, V_LID - 4, -ti - 2, -wi, depth + 2, ti + 1.2), box(wi, V_LID - 4, -ti - 2, wi + 8.5, depth + 2, ti + 1.2)]
    local = U([outer, back, stop] + rails + ears)
    inner = box(-wi, -20, -ti, wi, depth, ti)
    # Federzunge in der Vorderwand (drückt die Karte zum Leser)
    tongue_cut = U([box(-11, 14, -ti - 3, -10.2, 34, -ti + 0.01), box(10.2, 14, -ti - 3, 11, 34, -ti + 0.01),
                    box(-11, 33.2, -ti - 3, 11, 34, -ti + 0.01)])
    thin = box(-10.2, 14, -ti - 3, 10.2, 33.2, -ti - 2 + 0.6)
    bump = Manifold.batch_hull([box(-8, 29.5, -ti - 0.05, 8, 30.5, -ti + 0.8), box(-8, 28, -ti - 0.05, 8, 32, -ti)])
    local = local - inner - tongue_cut - thin + bump
    world = to_world(local)
    world = world ^ box(-50, -50, -50, 200, 200, LID_BOT)
    # Flansch unter dem Deckel; vorne bündig mit der Vorderwand
    fl = box(70 - (CARD_W / 2 + 0.75 + 2 + 6.5), 104, RING_Z0, 70 + (CARD_W / 2 + 0.75 + 2 + 6.5), 124, LID_BOT)
    fl = fl ^ to_world(box(-100, -100, -ti - 2, 100, 100, 100))
    fl = fl - to_world(box(-wi, -20, -ti, wi, 12, ti))
    world = world + fl
    for (x, y) in POCKET_SCREWS:
        world = world - cyl_z(x, y, RING_Z0 - 40, 45, HOLE3 / 2)
        world = world - cyl_z(x, y, RING_Z0 - 40, 40 - (POCKET_GRIP - RING_T), 3.4)    # Senkung von unten: Schraube 3,0 × 12
    return world


def rc522_placeholder():
    u0, u1, v0, v1, w0, w1 = rc_local()
    return to_world(box(u0, v0, w0, u1, v1, w1) + box(u0 + 3, v0 + 2.5, w1, u1 - 3, v1 - 2.5, w1 + RC_COMP))


def karte_world():
    return to_world(box(-CARD_W / 2, -(CARD_H - CARD_IN), -CARD_T / 2 + 0.4, CARD_W / 2, CARD_IN, CARD_T / 2 + 0.4))   # von der Zunge an die Rückwand gedrückt


def karte_print():
    """Karte flach, Rückseite oben (NFC-Tasche von oben druckbar). Unten = Kartenunterkante bei y=0."""
    cs = rr(0, 0, CARD_W, CARD_H, 5.0)
    ch = CrossSection([[(CARD_W - 9, CARD_H + 1), (CARD_W + 1, CARD_H + 1), (CARD_W + 1, CARD_H - 9)]])
    cs = cs - ch                                          # Ecke schräg: oben rechts (von vorne gesehen)
    c = slab(cs, 0, CARD_T)
    c = c - cyl_z(CARD_W / 2, 1.0 + NFC_D / 2, CARD_T - NFC_T - 0.4, 2, NFC_D / 2 + 0.3)
    return c.mirror([1, 0, 0]).translate([CARD_W, 0, 0])


# =====================================================================================
# Bodenplatte = Elektronikträger (wird von unten eingesetzt und mit 6 Schrauben gehalten)
# =====================================================================================

def stack_holes():
    """Lochmitten der Bolzen unter der Acrylplatte (Pi-Ende rechts)."""
    px, py = STACK_PAT
    xr = STACK_X0 + UPS[0] - PAT_END
    yf = STACK_Y0 + (UPS[1] - py) / 2
    return [(xr - px, yf), (xr, yf), (xr - px, yf + py), (xr, yf + py)]


def pocket(x0, y0, w, d, z, up=True, rim=1.2, h=2.5):
    """Mulde mit Rand für ein Modul (Innenmaß w × d inkl. Spiel). up=True: Rand nach oben, sonst hängend."""
    za, zb = (z - 0.01, z + h) if up else (z - h, z + 0.01)
    outer = box(x0 - rim, y0 - rim, za, x0 + w + rim, y0 + d + rim, zb)
    inner = box(x0, y0, za - 1, x0 + w, y0 + d, zb + 1)
    return outer - inner


def rear_layout():
    """Hinterer Streifen: (Name, x0, y0, w, d, Höhe) – Innenmaße der Mulden inkl. Spiel."""
    y0 = REAR_Y + 1.2
    out, x = [], 14.0 + 1.2
    for name, (bw, bt, bh) in (("WAGO GND A", WAGO5), ("WAGO 5 V", WAGO3), ("Verstärker", (MAXB[0], MAXB[1], MAXB[2]))):
        w, d = bw + 2 * CLR, bt + 2 * CLR
        out.append((name, x, y0, w, d, bh))
        x += w + 2 * 1.2 + 2.5
    return out


def base_open():
    """Öffnung des Korpus im hinteren Teil (Innenkontur hinter der Kammerwand)."""
    return INN ^ CrossSection.square([W + 2, W]).translate([-1, DIV_Y + 3])


def boden():
    z = BASE_T
    plate = Manifold.batch_hull([slab(OUT.offset(-SHADOW - BASE_CHAMF, JoinType.Round), 0, 0.01),
                                 slab(OUT.offset(-SHADOW, JoinType.Round), BASE_CHAMF, z - EDGE_V),
                                 slab(OUT.offset(-SHADOW - EDGE_V, JoinType.Round), z - 0.01, z)])
    add, cut = [], []
    # Zentrierkragen in der hinteren Öffnung, an den Domen ausgespart
    lw, lh = LIP
    op = base_open()
    ring = op.offset(-LIP_CLR, JoinType.Round) - op.offset(-LIP_CLR - lw, JoinType.Round)
    lip = slab(ring, z - 0.01, z + lh)
    for (x, y) in BASE_BOSSES:
        lip = lip - cyl_z(x, y, z - 1, lh + 2, BOSS_D / 2 + 0.6)
    add.append(lip)
    # Auflagen für die Acrylplatte (Mulde für vorhandene Schraubenköpfe/Muttern)
    rd, rdep = PAD_REC
    for (x, y) in stack_holes():
        add.append(cyl_z(x, y, z - 0.01, PAD_H + 0.01, 5.5))
        cut.append(cyl_z(x, y, z + PAD_H - rdep, rdep + 1, rd / 2))
        cut.append(cyl_z(x, y, -1, 20, HOLE25 / 2))
        cut.append(cyl_z(x, y, -1, 1 + CB25[1], CB25[0] / 2))
    # Mulden im hinteren Streifen
    for (name, x0, y0, w, d, h) in rear_layout():
        add.append(pocket(x0, y0, w, d, z))
    # Senkschrauben in die Korpusdome
    hd, hl = CSK
    for (x, y) in BASE_BOSSES:
        cut.append(cyl_z(x, y, -1, z + 2, hl / 2))
        cut.append(cyl_z(x, y, -0.01, (hd - hl) / 2 + 0.01, hd / 2, hl / 2))
    return U([plate] + add) - U(cut)


# =====================================================================================
# Außenteile
# =====================================================================================

def stoffrahmen():
    sx0, sx1, sz0, sz1 = SEAT
    m = FAB_T + CLR
    x0, x1, z0, z1 = sx0 + m, sx1 - m, sz0 + m, sz1 - m
    outer = rr(x0, z0, x1, z1, SEAT_R - m)
    inner = rr(x0 + FR_BORDER, z0 + FR_BORDER, x1 - FR_BORDER, z1 - FR_BORDER, SEAT_R - m - FR_BORDER + 2)
    cs = outer - inner
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    for k in (-1, 1):                                    # Gittersteg (K5) gegen Verziehen
        cs = cs + CrossSection.square([x1 - x0, 2.0]).translate([x0, cz + k * 19 - 1]) ^ outer
        cs = cs + CrossSection.square([2.0, z1 - z0]).translate([cx + k * 19 - 1, z0]) ^ outer
    fr = ext_xz(cs, SEAT_D - FR_T, SEAT_D)
    # Oberkante hinten 45° wie der Sitz
    # Sitz fällt oben unter 45° nach hinten → Rahmen folgt der Sitzform, um Stoff + Spiel eingerückt
    env = Manifold.batch_hull([ext_xz(rr(x0 - 0.4, z0 - 0.4, x1 + 0.4, z1 + 1.0, SEAT_R - m), -1, 0),
                               ext_xz(rr(x0 - 0.4, z0 - 0.4, x1 + 0.4, z1 - SEAT_D - 2.5, SEAT_R - m), SEAT_D + 2.5 - 0.01, SEAT_D + 2.5)])
    fr = fr ^ env
    for (x, z) in frame_pins():
        fr = fr + cyl_y(SEAT_D - 0.1, SEAT_D + 2.4, x, z, PIN_D / 2 - 0.05)
    return fr


def drehknopf():
    x0 = W + 1.0
    k = Manifold.batch_hull([cyl_x(x0, x0 + KNOB_L - 2, ENC_Y, ENC_Z, KNOB_D / 2),
                             cyl_x(x0 + KNOB_L - 0.01, x0 + KNOB_L, ENC_Y, ENC_Z, KNOB_D / 2 - 2)])
    for i in range(24):
        a = 2 * math.pi * i / 24
        k = k - cyl_x(x0 + 1.5, x0 + KNOB_L - 3, ENC_Y + math.cos(a) * (KNOB_D / 2 + 0.6), ENC_Z + math.sin(a) * (KNOB_D / 2 + 0.6), 1.3)
    k = k - box(x0 + KNOB_L - 0.6, ENC_Y - 0.9, ENC_Z + 6, x0 + KNOB_L + 1, ENC_Y + 0.9, ENC_Z + 13)   # Markierung
    nd, nt = NUT_REC
    k = k - cyl_x(x0 - 1, x0 + nt, ENC_Y, ENC_Z, nd / 2)
    bore = min(12.0, ENC_OUT - 1.0 - 1.0)
    k = k - cyl_x(x0 + nt - 0.1, x0 + 1.0 + bore, ENC_Y, ENC_Z, 3.05 + 0.05)
    k = k + box(x0 + 1.0 + bore - 5, ENC_Y - 3.2, ENC_Z - ENC_SLOT / 2 + 0.1, x0 + 1.0 + bore, ENC_Y + 3.2, ENC_Z + ENC_SLOT / 2 - 0.1)
    return k


def gegenplatte():
    p = box(WALL, STRAP_Y - 12, STRAP_Z - 9, WALL + 4, STRAP_Y + 12, STRAP_Z + 9)
    return p - cyl_x(0, 10, STRAP_Y, STRAP_Z, STRAP_HOLE / 2)


# =====================================================================================
# Platzhalter (für den Kollisionscheck, nicht zum Drucken)
# =====================================================================================

def stack_parts():
    """Stapel als Hüllkörper (gemessene Höhen) und die Freiräume, die er braucht."""
    x0, y0 = STACK_X0, STACK_Y0
    L, B = UPS
    za = BASE_T + PAD_H                                    # Unterkante Acrylplatte
    xp = x0 + OVERHANG                                     # Pi und Aufsatz beginnen hier (Überhang links)
    s = {}
    s["Akku-Board mit Zellen"] = box(x0, y0, za, x0 + L, y0 + B, za + UPS_LEVEL)
    s["Pi + Klemmen-Aufsatz"] = box(xp, y0, za + UPS_LEVEL, x0 + L, y0 + B, za + STACK_H)
    hx0 = xp + 7.0                                         # 40-Pin-Leiste: 51 mm, mittig auf dem 65-mm-Pi
    zc0, zc1 = za + CLAMP_Z, za + STACK_H
    s["Kabel Klemmreihe links (Zone)"] = box(xp - WIRE_CLR, y0, zc0, xp, y0 + B, zc1)
    s["Kabel Klemmreihe rechts (Zone)"] = box(x0 + L, y0, zc0, x0 + L + WIRE_CLR, y0 + B, zc1)
    s["Kabel Klemmreihe hinten (Zone)"] = box(xp, y0 + B, zc0, x0 + L, y0 + B + WIRE_CLR, zc1)
    s["Klinkenstecker am Pi (Zone)"] = box(xp, y0 + B, za + UPS_LEVEL, x0 + L, y0 + B + AUDIO_PLUG, za + UPS_LEVEL + 14.0)
    s["USB-C-Stecker am Akku-Board (Zone)"] = box(x0 + 4.5, y0 + B, za + 15.0, x0 + L, y0 + B + USB_PLUG, za + UPS_LEVEL + 6.0)
    return s


def placeholders():
    ph = {}
    ph.update(stack_parts())
    z = BASE_T
    for (name, x0, y0, w, d, h) in rear_layout():
        ph[name] = box(x0 + CLR, y0 + CLR, z, x0 + w - CLR, y0 + d - CLR, z + h + (4 if name.startswith("WAGO") else 0))
    for (name, x0, y0, w, d, h) in lid_layout():
        ph[name] = box(x0 + CLR, y0 + CLR, RING_Z0 - h - (4 if name.startswith("WAGO") else 0), x0 + w - CLR, y0 + d - CLR, RING_Z0)
    up = USB_PANEL
    r = up["mutter"] / 2
    ph["USB-C-Einbaubuchse mit Kabel"] = cyl_y(W - WALL - up["tiefe"], W - WALL - 0.3, up["x"], up["z"], r)
    spk_front = BAY_D - SPK_FLANGE
    flange = ext_xz(rr(SPK_X - SPK_FRAME / 2, SPK_Z - SPK_FRAME / 2, SPK_X + SPK_FRAME / 2, SPK_Z + SPK_FRAME / 2, SPK_FRAME_R), spk_front, BAY_D)
    basket = cyl_y(BAY_D + 3, spk_front + SPK_DEPTH - 8, SPK_X, SPK_Z, 35.5)
    magnet = cyl_y(spk_front + SPK_DEPTH - 8, spk_front + SPK_DEPTH, SPK_X, SPK_Z, SPK_MAG / 2)
    ph["Lautsprecher"] = U([flange, basket, magnet])
    ph["Drehgeber"] = box(W - ENC_WALL - 16, ENC_Y - 6.5, ENC_Z - 6.5, W - ENC_WALL, ENC_Y + 6.5, ENC_Z + 6.5)
    ph["Klinkenbuchse"] = box(W - JK_WALL - 15, JK_Y - 6, JK_Z - 6, W - JK_WALL, JK_Y + 6, JK_Z + 6)
    ph["Kurzhubtaster"] = box(BTN_X - SW / 2, BTN_Y - SW / 2, act_top() - SW_H, BTN_X + SW / 2, BTN_Y + SW / 2, act_top())
    ph["RC522"] = rc522_placeholder()
    ph["Karte (gesteckt)"] = karte_world()
    return ph


# Gruppen für die Prüfungen
BASE_PH = ["Akku-Board mit Zellen", "Pi + Klemmen-Aufsatz", "Kabel Klemmreihe links (Zone)",
           "Kabel Klemmreihe rechts (Zone)", "Kabel Klemmreihe hinten (Zone)", "USB-C-Stecker am Akku-Board (Zone)",
           "Klinkenstecker am Pi (Zone)",
           "WAGO GND A", "WAGO 5 V", "Verstärker"]
LID_PH = ["RC522", "Kurzhubtaster", "Karte (gesteckt)", "WAGO GND B", "WAGO 3,3 V", "WAGO SCL", "Touch-Modul MPR121"]
WALL_PH = ["Lautsprecher", "Drehgeber", "Klinkenbuchse", "USB-C-Einbaubuchse mit Kabel"]


def build():
    lid_o, lid_b = deckel()
    parts = {
        "korpus": korpus(),
        "deckel_orange": lid_o,
        "deckel_beige": lid_b,
        "deckelrahmen": deckelrahmen(),
        "kartenfach": kartentasche(),
        "boden": boden(),
        "stoffrahmen": stoffrahmen(),
        "drehknopf": drehknopf(),
        "ein_taste": taste(),
        "riemen_gegenplatte": gegenplatte(),
    }
    return parts


if __name__ == "__main__":
    import time
    t = time.time()
    parts = build()
    for k, v in parts.items():
        print(f"{k:20s} vol={v.volume()/1000:8.1f} cm³ tris={v.num_tri():7d} genus={v.genus()} bbox={tuple(round(b,1) for b in v.bounding_box())}")
    print("t", round(time.time() - t, 1))
