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
from manifold3d import Manifold, CrossSection, JoinType, FillRule

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
SKIN = par("SKIN", 0.8, "festgelegt", "beige Deckschicht über orangem Kern (D1); 0,8 = 4 Schichten à 0,2 bzw. 5 à 0,16 (vorher 0,7, lag zwischen zwei Schichten)")
SYM_INLAY = par("SYM_INLAY", 0, "festgelegt", "Symbole und Ringe bündig in Orange eingelegt (CANVAS druckt in den 4 Haut-Schichten beide Farben), statt 0,8 mm vertieft. "
                "Grund (Druck 05.11.): Kopfüber werden die Vertiefungen in Schicht 5 überbrückt; der Slicer dehnt die Brücke auf den ganzen Kreis aus "
                "(1760 mm² Brücke für 597 mm² Vertiefung) – die runden orangen Brückenfäden scheinen durch die 0,8 mm beige Haut, Böden sehen wie Fäden aus, "
                "um jedes Loch 3 Wände, Fäden und Nahtpunkte an den Lochkanten. Eingelegt liegt die ganze Oberseite auf der Platte, ohne Loch und ohne Brücke. "
                "Nicht mehr ertastbar → von Jan am 05.11. abgelehnt (Tasten müssen ertastbar bleiben). 0 = Vertiefung (gilt)")
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
CH_Z = par("CH_Z", 122.0, "festgelegt", "Bezugshöhe vorne oben (Zungenschlitze, Zungen am Deckelrahmen); die Kammerdecke selbst ist seit 04.11. ein Satteldach (ROOF)")
ROOF = par("ROOF", (25.0, 126.5, 1.6, 0.04), "festgelegt",
           "Kammerdecke als 45°-Satteldach (First y, First-Unterkante z am rechten Ende, Dicke senkrecht zur Fläche, Neigung des "
           "Firsts entlang x). Ersetzt die flache Decke bei z 122–125: die war eine 40-mm-Brücke, Schichten bis 5½ min statt "
           "ca. 1 min (G-Code 04.11.), dort lag die stärkste Querlinie. 45° druckt ohne Brücke. Der First steigt nach rechts um "
           "0,04 mm/mm (5,4 mm über die Breite): First und Traufen beginnen und enden nicht in einer Schicht, sondern über "
           "ca. 27 Schichten – sonst gäbe es dort wieder einen Sprung der Schichtdauer. Abstände in check.py")

# Deckel-Bedienung (aus v3)
PADS = par("PADS", {"zurück": (30, 30, 22), "play": (70, 30, 30), "vor": (110, 30, 22), "schlaf": (70, 64, 18)},
           "festgelegt", "Touch-Felder x, y, Ø")
PAD_POCKET = par("PAD_POCKET", 2.0, "Probedruck", "Tasche unter dem Feld → 4 mm Kunststoff über dem Kupfer, unter den Symbolen 3,2 mm")
PAD_RING = par("PAD_RING", 1.1, "festgelegt", "Breite der Ringnut um jedes Touchfeld")
SYM_GAP = par("SYM_GAP", 1.8, "festgelegt", "Mindestabstand Symbol ↔ Ringnut (Probedruck 27.10.: Dreiecke lagen auf der Nut)")
SYM_MIN = par("SYM_MIN", 0.9, "festgelegt", "kleinste Breite in Symbolen (2 Linien bei Düse 0,4); dünnere Spitzen werden abgerundet")

# Karte und Kartenfach
CARD_W = par("CARD_W", 70.0, "festgelegt", "Karte Breite")
CARD_H = par("CARD_H", 112.0, "festgelegt", "Karte Höhe (70 sichtbar + 42 im Fach)")
CARD_T = par("CARD_T", 4.0, "festgelegt", "Karte Dicke")
CARD_IN = par("CARD_IN", 42.0, "festgelegt", "Einstecktiefe")
SLOT_Y = par("SLOT_Y", 116.0, "festgelegt", "Schlitzmitte auf dem Deckel")
TILT = par("TILT", 8.0, "festgelegt", "Neigung der Karte nach hinten")
# Einschubtasche für ein Papier-Cover (statt Aufkleber): von oben einschieben, Rahmen mit 45°-Lippen (Schwalbenschwanz)
INS_GAP = par("INS_GAP", 0.6, "Probedruck", "Tasche: Spalt an der Außenwand (Einleger laminiert ca. 0,25–0,35 mm)")
INS_LIP = par("INS_LIP", 1.5, "festgelegt", "Lippe überdeckt den Einleger je Seite und unten; Unterseite 45°, druckbar ohne Stütze")
INS_WALL = par("INS_WALL", 1.2, "festgelegt", "Außenwand neben der Tasche")
INS_FRONT = par("INS_FRONT", 0.6, "festgelegt", "Lippe an der Fensterkante mindestens so dick")
INS_Y0 = par("INS_Y0", 43.5, "festgelegt", "Taschenunterkante ab Kartenunterkante (1,5 mm über dem Deckel)")
INS_CLR = par("INS_CLR", 0.3, "festgelegt", "Spiel Einleger zur Tasche je Seite")
CARD_TOP_R = par("CARD_TOP_R", 1.5, "festgelegt", "Eckradius oben (Tasche ist oben offen und muss gerade bis zur Kante laufen)")
GRIP_R = par("GRIP_R", 7.0, "festgelegt", "Griffmulde oben Mitte in der Rückwand: Einleger von vorn und hinten greifbar")
NFC_D = par("NFC_D", 25.0, "belegt", "NFC-Aufkleber Ø")
NFC_T = par("NFC_T", 0.4, "vorläufig", "NFC-Aufkleber Dicke")
RC_L = par("RC_L", 60.0, "gemessen", "RC522 Platine Länge")
RC_B = par("RC_B", 40.0, "gemessen", "RC522 Platine Breite")
RC_T = par("RC_T", 1.6, "vorläufig", "RC522 Platinendicke")
RC_ANT = par("RC_ANT", 20.0, "gemessen", "Antennenmitte ab Platinenende (Antennenseite; 40 mm bis Lötlochende)")
RC_COMP = par("RC_COMP", 5.0, "gemessen", "Bauteilhöhe auf der Rückseite (Quarz, höchstes Bauteil)")
RC_PIN_OUT = par("RC_PIN_OUT", 6.0, "gemessen", "Überstand der 90°-Stifte über die Platinenkante")
RC_PLUG_OUT = par("RC_PLUG_OUT", 14.0, "gemessen", "Platinenkante bis Ende Steckkabel-Hülse (gesteckt, Buchse sitzt bis an die Leiste)")
RC_BEND = par("RC_BEND", 8.0, "vorläufig", "Platz für den Kabelbogen hinter den Buchsen")
RC_DROP = par("RC_DROP", 5.0, "festgelegt", "RC522 so viel tiefer (weg vom Deckel) als mittig hinter dem NFC-Aufkleber; Probedruck 27.10.: Steckkabel stießen an den Schraubblock des Deckelrahmens")
RC_HDR_OFF = par("RC_HDR_OFF", 0.0, "vorläufig", "Mitte der Stiftleiste gegenüber Platinenmitte, + = vom Deckel weg (nicht gemessen, mittig angenommen)")
RC_XTAL_FREE = par("RC_XTAL_FREE", 18.0, "festgelegt", "deckelseitige Schiene: Lippe auf so viel Länge vor dem Stiftleisten-Ende entfernt (Quarz; laut Foto ca. 12 mm lang)")

# Ein-Taste
BTN_X = par("BTN_X", 124.5, "festgelegt", "Ein-Taste x (hinten rechts)")
BTN_Y = par("BTN_Y", 108.0, "festgelegt", "Ein-Taste y")
BTN_D = par("BTN_D", 12.0, "festgelegt", "Tastenkopf-Ø")
BTN_GAP = par("BTN_GAP", 0.25, "Probedruck", "Luft je Seite zwischen Kappe und Deckelbohrung (Druck 02.11.: passt)")
BTN_FLUSH = par("BTN_FLUSH", 0.0, "festgelegt", "Kappe endet bündig mit der Deckeloberfläche, keine Mulde (Jan 02.11.: Mulde wirkt billig)")
BTN_TOP_CH = par("BTN_TOP_CH", 0.3, "festgelegt", "Fase an der Oberkante der Kappe (nimmt die Kante, kaum sichtbar)")
LID_EDGE_CH = par("LID_EDGE_CH", 0.5, "festgelegt", "Fase 45° an der Deckel-Oberkante (kopfüber: verdeckt den Elefantenfuß)")
SLOT_CH = par("SLOT_CH", 0.6, "festgelegt", "Einführfase am Kartenschlitz oben")
SW = par("SW", 12.0, "belegt", "Kurzhubtaster 12 × 12")
SW_H = par("SW_H", 7.3, "belegt", "Tasterhöhe gesamt, Gehäuseunterseite bis Stößeloberkante (Etikett BerryBase KHT1212PV73: H 7,30; nachmessen)")
SW_LEGS = par("SW_LEGS", 13.0, "gemessen", "Breite über die Beinchen (Außenkante zu Außenkante), Jan ca. 13 mm; Taster 12 mm, Beinchen stehen seitlich über")
SW_LEG_CLR = par("SW_LEG_CLR", 0.5, "festgelegt", "Luft je Seite im Beinchen-Kanal des Tasterhalters")

# Rechts: Drehgeber, Klinke
ENC_Y = par("ENC_Y", 84.0, "festgelegt", "Drehgeber y")
ENC_Z = par("ENC_Z", 60.0, "festgelegt", "Drehgeber z")
ENC_HOLE = par("ENC_HOLE", 7.4, "Probedruck", "Loch für M7-Gewinde")
ENC_WALL = par("ENC_WALL", 2.6, "festgelegt", "Wand unter der Drehgeber-Mutter = volle Wand 3,0 minus glatte Fläche 0,4 (vorher 2,0 mit Senkung innen). Gewinde 7 mm (Datenblatt STEC11B, M7×0,75); am Prototyp bei 2 mm Wand 2 mm Gewinde über der Mutter (Jan 03.11.) → bei 3 mm Wand noch ca. 1 mm, Mutter voll im Gewinde")
ENC_OUT = par("ENC_OUT", 21.8, "gemessen", "Achse ragt so weit über die Wand-Außenfläche. Achse wird NICHT gekürzt (Jan 05.11.). Gemessen am finalen Korpus: Achsende bis Mutterauflage (glatte Fläche, 0,4 unter der Wand) 22,2 → 21,8 über der Wand (Modell vorher 22,0)")
ENC_THREAD = par("ENC_THREAD", 7.0, "belegt", "Gewindelänge ab Gehäusefläche (Datenblatt STEC11B, M7 × 0,75)")
ENC_NUT = par("ENC_NUT", (2.5, 0.5, 12.0), "gemessen / vorläufig", "Mutter Höhe 2,5 und ca. 10 breit (Jan 03.11.); Scheibe 0,5 dick und Ø 12 angenommen (liegen bei). 05.11.: Achsende bis Mutter 20,2, bis Auflage 22,2 → über der Wand nur 2,0 (mit/ohne Scheibe offen). Für den Knopf ohne Einfluss: Aussparung reicht bis zum Gewindeende")
ENC_LUG = par("ENC_LUG", (2.5, 2.0, 1.5), "gemessen", "Nase am Drehgeber (Jan 03.11.): Gewinde-Außenkante bis Nase 2,5, Nase 2,0 breit, steht 1,5 vor. Einbau: Nase nach oben (zum Deckel)")
ENC_SLOT_D = par("ENC_SLOT_D", 11.3, "gemessen", "Schlitztiefe ab Achsende (Jan 05.11.: 11,3; Achse wird nicht gekürzt)")
ENC_PUSH = par("ENC_PUSH", 0.5, "belegt", "Hub des Drucktasters in der Achse (Datenblatt)")
ENC_SLOT = par("ENC_SLOT", 1.6, "gemessen", "Schlitzbreite Achse (Jan 03.11.: ca. 1,6, Schlitz 11 tief, Achse Ø 6)")
KNOB_D = par("KNOB_D", 34.0, "festgelegt", "Knopf-Ø")
KNOB_ROOF = par("KNOB_ROOF", 2.0, "festgelegt", "Knopf: Material vor dem Achsende")
NUT_REC_D = par("NUT_REC_D", 15.0, "festgelegt", "Aussparung im Knopf für Mutter (Eckmaß ca. 11,5) und Scheibe")
KNOB_GAP = par("KNOB_GAP", 1.0, "festgelegt", "Luft Knopf ↔ Wand (Fuzzy Skin ±0,25, Drucktaster 0,5 mm Hub)")
KNOB_BORE = par("KNOB_BORE", 6.1, "Probedruck", "Bohrung für die Schlitzachse Ø 6 (gedruckt meist 0,1–0,2 kleiner → Klemmsitz), nur im geschlitzten Teil der Achse (federt dort)")
KNOB_GUIDE = par("KNOB_GUIDE", 6.3, "Probedruck", "Bohrung im ungeschlitzten Teil der Achse (federt nicht): nur Führung, damit der lange Knopf nicht auf ganzer Länge klemmt")
KNOB_TIP = par("KNOB_TIP", 0.0, "festgelegt", "Luft Achsende ↔ Knopfboden: 0 = Knopf bis Anschlag aufschieben, Lage eindeutig (vorher 0,4, als die Achslänge noch nicht gemessen war). Ist die Achse länger (z. B. 22,2 ab Scheibe), sitzt der Knopf nur weiter außen")
KNOB_RIB = par("KNOB_RIB", 8.0, "festgelegt", "Länge des Stegs im Achsschlitz (Mitnahme), Schlitz 11,3 tief")
JK_Y = par("JK_Y", 84.0, "festgelegt", "Klinke y")
JK_Z = par("JK_Z", 24.0, "festgelegt", "Klinke z")
JK_HOLE = par("JK_HOLE", 6.2, "vorläufig", "Loch für Klinkengewinde (Gewinde unbekannt)")
JK_WALL = par("JK_WALL", 2.0, "gemessen", "Wand unter der Klinkenmutter (wie Prototyp, passt laut Jan; Gewinde ist knapp)")

# Links: Riemen, USB-C
STRAP_Y = par("STRAP_Y", 104.0, "festgelegt", "Riemenpunkt y")
STRAP_Z = par("STRAP_Z", 118.0, "festgelegt", "Riemenpunkt z")
STRAP_HOLE = par("STRAP_HOLE", 7.9, "gemessen", "Buchschraube: Schaft Ø 7,5 (Jan 03.11.) + 0,4 Spiel; Kopf liegt auf dem Riemen (Riemen ca. 3 mm dick)")

# Boden (abnehmbar) – Schrauben von unten in Dome im Korpus
BASE_BOSSES = par("BASE_BOSSES", [(8.6, 8.6), (131.4, 8.6), (7.7, 47.0), (132.3, 47.0), (8.6, 131.4), (131.4, 131.4)],
                  "festgelegt", "Bodenschrauben: 4 Ecken + 2 an der Kammerwand (vordere Dome stehen dicht in der Kammer)")
BOSS_H = par("BOSS_H", 14.0, "festgelegt", "Höhe der Bodendome im Korpus; Kernloch 12 tief")
CSK = par("CSK", (6.2, 3.4), "gemessen", "Senkung für Senkkopf 3,0 × 12 (Kopf Ø 6 gemessen + 0,2; Ø Loch)")
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
USBC = par("USBC", {"x": 112.0, "z": 60.0, "pcb": 22.0, "pcb_t": 1.6, "loch_abst": 16.0, "loch_rand": 3.0,
                    "buchse_b": 9.2, "buchse_h": 3.4, "spalt": 0.3, "dom_l": 12.0},
            "belegt / gemessen",
            "Soldered 333011 (V1.2.0) in der Rückwand, Bauteilseite oben, Buchsenmund bündig mit der Platinenkante. "
            "Belegt (KiCad-Datei V1.2.0): Platine 22 × 22 × 1,6, Löcher Ø 3,2 mit 16,0 Abstand, 3,0 von der Buchsenkante, "
            "Buchsenbreite ca. 9,2 (Bestückungsdruck). Gemessen (Jan 03.11.): Buchsenhöhe 3,4, Lochabstand 16. "
            "x 112 statt 114: 2 mm mehr Abstand zur Innenecke")
USBC_LEGS = par("USBC_LEGS", (4.31, 2.5, 6.7, 1.5), "belegt",
                "Lötfahnen der Buchse unter der Platine (KiCad): seitlich ±4,31, 2,5 und 6,7 von der Platinenkante; Aussparung 1,5 tief im Dom")
USBC_PLUG = par("USBC_PLUG", (10.8, 7.0, 2.0), "gemessen / festgelegt",
                "Öffnung in der Rückwand für den Steckerkörper (B, H, Eckradius). Steckergehäuse Jan 04.11.: 10 × 6 mm "
                "(vorher 13 × 7 nach USB-C-Höchstmaß 12,35 × 6,5). Breite +0,4 je Seite; Höhe +0,5 je Seite (Oberkante ist eine "
                "Brücke und hängt leicht durch). Eckradius 2 passt für Gehäuseecken ab ca. R 0,5. Das Gehäuse taucht ca. 2,9 mm in die "
                "Wand ein, bis zum Buchsenmund an der Innenseite; deshalb muss die Öffnung gehäusegroß sein und unter der Buchse "
                "bleibt die Platinenkante (1,6 mm) sichtbar")
USBC_CH = par("USBC_CH", 0.6, "festgelegt", "Fase außen an der USB-C-Öffnung")
SCREW_L = par("SCREW_L", 12.0, "gemessen", "Einzige vorhandene Schrauben: 3,0 × 12, Senk- und Flachkopf (Jan 03.11.). Alle Dome und Kernlöcher darauf ausgelegt")
SPK_DOME_L = par("SPK_DOME_L", 10.0, "festgelegt", "Lautsprecher-Dome hinter der Frontplatte (vorher 7): Schraube 3,0 × 12 durch den Korbflansch")
# Fuzzy Skin: glatte, leicht vertiefte Flächen an allem mit Passung (Entscheidung Jan 03.11.: Rückseite Variante B)
FUZZ_REC = par("FUZZ_REC", 0.4, "festgelegt", "Glatte Flächen (ohne Fuzzy Skin) liegen so tief unter der Außenfläche: saubere Kante, wirkt gewollt; Muttern liegen eben")
FUZZ_RIM = par("FUZZ_RIM", 0.3, "festgelegt", "Modifier „ohne Fuzzy“ reicht so weit über die glatte Fläche hinaus (Stufe selbst bleibt glatt)")
FUZZ_SHELL = par("FUZZ_SHELL", 1.0, "festgelegt",
                 "Modifier „Fuzzy Außenhaut“ (04.11.): Fuzzy nur in dieser Tiefe unter der Außenfläche. Enthält die Mitte der "
                 "Außenwand-Linie (0,21 mm), erreicht nie die Innenseite (Wand 2,0–3,0). Grund: Löcher durch die Wand schneiden den "
                 "Wandring auf, dann zählt der Slicer die Innenseite zur Kontur (Druck 04.11.: Fuzzy innen in Bändern)")
FUZZ_Z = par("FUZZ_Z", (BASE_T + EDGE_V, HB - 1.0), "festgelegt",
             "Fuzzy-Außenhaut von/bis z: Fase unten (V-Fuge) und Fase oben bleiben glatt und rahmen die Fläche")
BACK_PANEL = par("BACK_PANEL", (17.0, 46.5, 123.0, 69.5, 5.0), "festgelegt",
                 "Anschlussfeld hinten x0, z0, x1, z1, Eckradius: ein glattes Feld mit USB-C und Lüftung, mittig (x 70)")
VENTS = par("VENTS", (6, 2.0, 6.4, 50.0, 66.0), "festgelegt",
            "Lüftungsschlitze: Anzahl, Breite, Teilung, z unten, z oben; links im Anschlussfeld mit gleichem Rand wie USB-C rechts")
LS_SPOT = par("LS_SPOT", 10.0, "festgelegt", "glatte Fläche um die Deckelschrauben hinten (Ø)")
JK_NUT = par("JK_NUT", 8.0, "gemessen", "Mutter der Klinkenbuchse Ø (Jan 03.11.)")
JK_BODY = par("JK_BODY", (12.2, 12.8, 0.6), "gemessen / festgelegt",
              "Tasche innen gegen Mitdrehen der Klinkenbuchse (B × H × Tiefe): Körper 11,5 breit, 6,2 hoch, mit Lötfahne 9 (Jan 03.11.); Höhe symmetrisch, weil die Lage der Fahne zur Achse nicht gemessen ist. Wand unter der Mutter bleibt 2,0")
JK_SPOT = par("JK_SPOT", 10.0, "festgelegt", "glatte Fläche um die Klinke (Ø) = Mutter + 1 mm Rand")
ENC_SPOT = par("ENC_SPOT", 18.0, "festgelegt", "glatte Fläche um den Drehgeber (Ø), liegt unter dem Knopf (Ø 34)")
SEAT_CH = par("SEAT_CH", 0.6, "festgelegt", "Fase 45° an der Kante des Gitter-Sitzes vorne (glatt, rahmt das Gitter)")
AUDIO_PLUG = par("AUDIO_PLUG", 20.0, "vorläufig", "Platz hinter der Klinke des Pi: Klinkenstecker 90° gewinkelt (Goobay 67782)")
MAXB = par("MAXB", (19.0, 18.0, 8.0), "vorläufig", "Verstärker-Klon L, B, Höhe mit Klemme")
MPRB = par("MPRB", (34.0, 20.0, 5.0), "gemessen", "MPR121-Modul L, B, Höhe: Adafruit 1982 STEMMA-QT-Ausführung, L × B gemessen 03.11.; Höhe 5 mm festgelegt (inkl. Buchsen und Lötstellen)")
WAGO5 = par("WAGO5", (30.0, 18.6, 8.4), "belegt", "WAGO 221-425 B, T, H")
WAGO3 = par("WAGO3", (18.6, 18.6, 8.4), "belegt", "WAGO 221-423 B, T, H")
REAR_Y = STACK_Y0 + UPS[1] + 1.0          # hinterer Streifen hinter der Anschlusskante
BRIDGE_Y = par("BRIDGE_Y", (74.0, 98.0), "festgelegt", "Verteiler-Brücke am Deckelrahmen: MPR121 + Klemmen für 3,3 V, SCL, GND B")

LS_X = par("LS_X", (24.0, 116.0), "festgelegt", "Deckelschrauben hinten x")
LS_Z = par("LS_Z", 124.0, "festgelegt", "Deckelschrauben hinten z")
LS_BLOCK_Z0 = par("LS_BLOCK_Z0", 119.0, "festgelegt", "Unterkante der Schraubblöcke hinten am Deckelrahmen (vorher 117; 2 mm mehr Platz für die RC522-Stecker, 3,2 mm Wand unter dem Kernloch)")

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

def _roof_prof(dz=0.0, unten=None):
    """Profil (y, z) des Satteldachs am rechten Ende (x = W): Unterkante z_u(y) = First − |y − First_y| (45°), um dz angehoben.
    unten=None: Band zwischen Unterkante und Unterkante + Dicke; sonst Fläche von z=unten bis zur (angehobenen) Unterkante."""
    yr, zr, t, _ = ROOF
    tv = t * math.sqrt(2.0)
    y0, y1 = -2.0, DIV_Y + 5.0
    zu = lambda y: zr - abs(y - yr)
    if unten is None:
        pts = [(y0, zu(y0)), (yr, zr), (y1, zu(y1)), (y1, zu(y1) + tv), (yr, zr + tv), (y0, zu(y0) + tv)]
    else:
        pts = [(y0, unten), (y1, unten), (y1, zu(y1) + dz), (yr, zr + dz), (y0, zu(y0) + dz)]
    return CrossSection([pts]) if CrossSection([pts]).area() > 0 else CrossSection([pts[::-1]])


def _roof_shear(m):
    """First fällt nach links: z' = z − s·(W − x)."""
    s = ROOF[3]
    return m.transform(np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [s, 0, 1.0, -s * W]], dtype=np.float32))


def roof():
    """Satteldach als Körper (über die ganze Breite, wird mit der Kammer geschnitten)."""
    return _roof_shear(ext_yz(_roof_prof(), -1, W + 1))


def roof_unter(oberkante=False):
    """Raum unter dem Dach (Kammer-Luft) bzw. mit oberkante=True alles bis zur Dach-Oberkante."""
    tv = ROOF[2] * math.sqrt(2.0) if oberkante else 0.0
    return _roof_shear(ext_yz(_roof_prof(dz=tv, unten=-20.0), -1, W + 1))


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
        add.append(ext_xz(tear(BOSS_D / 2).mirror([0, 1]).translate([x, z]), y0 - 0.5, y0 + SPK_DOME_L))   # Tropfen nach unten: ohne Stütze

    # Trennwand bis unter das Dach, Kammerdecke als 45°-Satteldach
    kammer = INN_SLAB(0, HB) ^ box(0, 0, 0, W, DIV_Y + 3, HB)
    add.append((INN_SLAB(FLOOR, CH_Z) ^ box(0, DIV_Y, 0, W, DIV_Y + 3, HB)) ^ roof_unter(oberkante=True))
    add.append(roof() ^ kammer)

    # Zungen-Aufnahmen vorne (für den Deckelrahmen): stehen auf dem Dach
    tongue_blocks = []
    for x in (40.0, 100.0):
        blk = box(x - 9, 7.4, 95.0, x + 9, 14.4, RING_Z0 - 0.5) - roof_unter()
        tongue_blocks.append(blk)
    add += tongue_blocks

    # Deckelauflage 45°
    z0 = LID_BOT - LEDGE
    ledge = slab(INN.offset(0.6, JoinType.Round), z0, LID_BOT) - Manifold.batch_hull([slab(INN.offset(0.03, JoinType.Round), z0 - 0.03, z0), slab(INN.offset(-LEDGE - 1.0, JoinType.Round), LID_BOT + 0.99, LID_BOT + 1.0)])
    add.append(ledge)                                                          # ringsum geschlossen: Elektronik kommt von unten
    add.append(usbc_domes())                                                   # Halter USB-C-Platine

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
    c = SEAT_CH                                                                     # Fase an der Sitzkante
    cut.append(Manifold.batch_hull([ext_xz(rr(sx0 - c, sz0 - c, sx1 + c, sz1 + c, SEAT_R + c), -1, 0.0),
                                    ext_xz(rr(sx0, sz0, sx1, sz1, SEAT_R), c - 0.01, c)]))
    # Lautsprecherausschnitt (Tropfen, oben gekappt → dichtet unter dem Flansch)
    cut.append(ext_xz(tear(SPK_CUT / 2, SPK_X, SPK_Z, cap=SPK_CUT / 2 + 1.0), BAY_D - 1, BAY_D + 4))
    for (x, z) in spk_holes:
        cut.append(cyl_y(BAY_D - 1, y0 + SPK_DOME_L - 0.5, x, z, PILOT / 2))     # 12,4 tief ab Muldenboden
    # Stiftlöcher für den Stoffrahmen
    for (x, z) in frame_pins():
        cut.append(cyl_y(SEAT_D - 0.5, SEAT_D + 2.8, x, z, PIN_HOLE / 2))
    # Kabeldurchführung Trennwand (mit Heißkleber abdichten)
    cut.append(ext_xz(tear(3.0, 118, 14), DIV_Y - 1, DIV_Y + 4))
    # Mulden in der Kammerdecke unter den vorderen Ring-Domen (Deckelrahmen): 1,2 tief, Decke bleibt 1,8 dick
    for (x, y) in RING_SCREWS:
        if y < DIV_Y:
            cut.append(cyl_z(x, y, CH_Z + 3 - 1.2, 5, BOSS_D / 2 + 1.0))
    # Zungenschlitze
    for x in (40.0, 100.0):
        cut.append(box(x - 6.2, 9.2, CH_Z + 3.4, x + 6.2, 11.6, RING_Z0))
    # Deckelschrauben hinten: Loch + Senkung außen
    for x in LS_X:
        cut.append(ext_xz(tear(HOLE3 / 2, x, LS_Z), W - WALL - 3, W - 0.8))
        face = W - FUZZ_REC
        hd = CSK[0] + 0.2                                                       # Senkkopf bündig mit der glatten Fläche
        cut.append(Manifold.cylinder(hd / 2 + 0.6, 0.0, hd / 2 + 0.6, 61).rotate([-90, 0, 0]).translate([x, face - hd / 2, LS_Z]))
        cut.append(cyl_y(face, W + 1, x, LS_Z, LS_SPOT / 2))
    # Rechts: Drehgeber und Klinke
    cut.append(ext_yz(tear(ENC_HOLE / 2, ENC_Y, ENC_Z, cap=ENC_HOLE / 2), W - WALL - 1, W + 1))
    if ENC_WALL < WALL - FUZZ_REC:                                              # Senkung innen nur bei dünnerer Wand
        cut.append(cyl_x(W - WALL - 1, W - FUZZ_REC - ENC_WALL, ENC_Y, ENC_Z, 11))
    cut.append(cyl_x(W - FUZZ_REC, W + 1, ENC_Y, ENC_Z, ENC_SPOT / 2))
    g, lb, lh = ENC_LUG                                                         # Verdrehschutz: Tasche für die Nase (oben)
    r0 = 3.5 + g                                                                # Gewinde M7 → Außenradius 3,5
    cut.append(box(W - WALL - 1, ENC_Y - lb / 2 - 0.3, ENC_Z + r0 - 0.5, W - WALL + lh + 0.4, ENC_Y + lb / 2 + 0.3, ENC_Z + r0 + 1.4))
    cut.append(ext_yz(tear(JK_HOLE / 2, JK_Y, JK_Z, cap=JK_HOLE / 2), W - WALL - 1, W + 1))
    cut.append(cyl_x(W - FUZZ_REC, W + 1, JK_Y, JK_Z, JK_SPOT / 2))
    jb, jh, _ = JK_BODY                                                         # innen: Tasche gegen Mitdrehen, Wand unter der Mutter bleibt 2,0
    cut.append(box(W - WALL - 1, JK_Y - jb / 2, JK_Z - jh / 2, W - FUZZ_REC - JK_WALL, JK_Y + jb / 2, JK_Z + jh / 2))
    # Links: Riemen
    cut.append(ext_yz(tear(STRAP_HOLE / 2, STRAP_Y, STRAP_Z, cap=STRAP_HOLE / 2), -1, WALL + 1))
    # Hinten: Öffnung für den USB-C-Steckerkörper (Buchse sitzt innen an der Wand) und Lüftungsschlitze (G11, max. 2 mm)
    cut.append(usbc_cut())
    px0, pz0, px1, pz1, pr = BACK_PANEL
    cut.append(ext_xz(rr(px0, pz0, px1, pz1, pr), W - FUZZ_REC, W + 1))
    for (vx0, vz0, vx1, vz1) in vents():
        cut.append(ext_xz(rr(vx0, vz0, vx1, vz1, 1.0), W - WALL - 1, W + 1))
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
    return USBC["x"], USBC["z"]


def vents():
    """Lüftungsschlitze (x0, z0, x1, z1): links im Anschlussfeld, Rand links = Rand rechts neben der USB-C-Fase."""
    n, b, t, z0, z1 = VENTS
    px0, _, px1, _, _ = BACK_PANEL
    rand = px1 - (USBC["x"] + USBC_PLUG[0] / 2 + USBC_CH)
    x = px0 + rand
    return [(x + i * t, z0, x + i * t + b, z1) for i in range(n)]


def usbc_geo():
    """Lage der USB-C-Platine: Unterkante, Löcher (x, y)."""
    u = USBC
    pcb_top = u["z"] - u["buchse_h"] / 2
    pcb_bot = pcb_top - u["pcb_t"]
    y_edge = W - WALL - u["spalt"]                              # Platinenkante = Buchsenmund
    holes = [(u["x"] + s * u["loch_abst"] / 2, y_edge - u["loch_rand"]) for s in (-1, 1)]
    return pcb_bot, pcb_top, y_edge, holes


def usbc_cut():
    b, h, r = USBC_PLUG
    x, z = usb_panel()
    f = W - FUZZ_REC                                                    # Oberfläche des Anschlussfelds
    inner = ext_xz(rr(x - b / 2, z - h / 2, x + b / 2, z + h / 2, r), W - WALL - 1, f - USBC_CH + 0.01)
    c = USBC_CH
    fase = Manifold.batch_hull([ext_xz(rr(x - b / 2, z - h / 2, x + b / 2, z + h / 2, r), f - c, f - c + 0.01),
                                ext_xz(rr(x - b / 2 - c, z - h / 2 - c, x + b / 2 + c, z + h / 2 + c, r + c), f - 0.01, W + 1)])
    return inner + fase


def usbc_domes():
    """Zwei Dome unter der Platine, an die Rückwand angesetzt; unten 45°-Kegel in die Wand (ohne Stütze).
    Aussparung oben für die Lötfahnen der Buchse."""
    pcb_bot, _, y_edge, holes = usbc_geo()
    dl = USBC["dom_l"]
    r = BOSS_D / 2
    yw = W - WALL + 0.5                                         # bis in die Wand
    out = []
    for (x, y) in holes:
        col = cyl_z(x, y, pcb_bot - dl, dl, r) + box(x - r, y, pcb_bot - dl, x + r, yw, pcb_bot)
        # 45°-Übergang unten: Kegel von der Wand aus
        cone = Manifold.batch_hull([box(x - r, yw - 0.01, pcb_bot - dl - (yw - y + r), x + r, yw, pcb_bot - dl),
                                    cyl_z(x, y, pcb_bot - dl, 0.01, r)])
        out.append(col + cone)
    d = U(out)
    lat, a, b, depth = USBC_LEGS
    x0 = USBC["x"]
    d = d - box(x0 - lat - 0.9, y_edge - b - 1.0, pcb_bot - depth, x0 + lat + 0.9, W, pcb_bot + 1)   # Lötfahnen (a liegt näher an der Wand)
    for (x, y) in holes:
        d = d - cyl_z(x, y, pcb_bot - dl + 1.0, dl, PILOT / 2)
    return d ^ INN_SLAB(0, HB)


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


def _poly(p):
    a = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return CrossSection([p if a > 0 else p[::-1]])


def _cs_radius(cs, cx, cy):
    """größter Abstand eines Symbolpunkts von der Feldmitte"""
    r = 0.0
    for poly in cs.to_polygons():
        p = np.asarray(poly)
        if len(p):
            r = max(r, float(np.max(np.hypot(p[:, 0] - cx, p[:, 1] - cy))))
    return r


def _fit(cs, cx, cy, d):
    """Symbol um die Feldmitte so skalieren, dass SYM_GAP zur Ringnut bleibt (nur verkleinern)."""
    r_max = d / 2 - PAD_RING - SYM_GAP
    r = _cs_radius(cs, cx, cy)
    if r <= r_max:
        return cs
    k = r_max / r
    return cs.translate([-cx, -cy]).scale([k, k]).translate([cx, cy])


def _skip(cx, cy, d, right):
    """Doppeldreieck (vor/zurück), Dreiecke überlappen um 30 %: eine Fläche ohne dünne Stege."""
    a, h, ov = 1.0, 0.62, 0.3
    tot = 2 * a - ov * a
    x0 = -tot / 2
    t1 = [(x0, h), (x0, -h), (x0 + a, 0)]
    t2 = [(x0 + a - ov * a, h), (x0 + a - ov * a, -h), (x0 + tot, 0)]
    cs = _poly(t1) + _poly(t2)
    if not right:
        cs = cs.mirror([1, 0])
    cs = cs.scale([20, 20]).translate([cx, cy])       # erst groß, _fit verkleinert auf den erlaubten Radius
    return _fit(cs, cx, cy, d)


def _opening(cs, r):
    """entfernt alles, was schmaler als 2r ist (Spitzen werden mit Radius r abgerundet)"""
    return cs.offset(-r, JoinType.Round, circular_segments=SEG).offset(r, JoinType.Round, circular_segments=SEG).simplify(0.01)   # simplify: doppelte Punkte aus offset entfernen


def pad_symbols(rings=True):
    s = []
    px, py, d = PADS["zurück"]; s.append(_skip(px, py, d, right=False))
    px, py, d = PADS["vor"]; s.append(_skip(px, py, d, right=True))
    px, py, d = PADS["play"]
    s.append(_fit(_poly(tri(px - 9, py, 9.5, False)) + CrossSection.square([2.6, 11.5]).translate([px + 2.5, py - 5.75])
                  + CrossSection.square([2.6, 11.5]).translate([px + 6.6, py - 5.75]), px, py, d))
    px, py, d = PADS["schlaf"]
    s.append(_fit(CrossSection.circle(5.2, SEG).translate([px - 0.6, py]) - CrossSection.circle(4.5, SEG).translate([px + 2.0, py + 1.8]), px, py, d))
    out = s[0]
    for t in s[1:]:
        out = out + t
    out = _opening(out, SYM_MIN / 2)
    if rings:
        for (x, y, d) in PADS.values():
            out = out + (CrossSection.circle(d / 2, SEG).translate([x, y]) - CrossSection.circle(d / 2 - PAD_RING, SEG).translate([x, y]))
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


def lid_plate():
    """Deckelplatte mit 45°-Fase an der Oberkante."""
    ch = LID_EDGE_CH
    return Manifold.batch_hull([slab(LID_CS, LID_BOT, LID_TOP - ch),
                                slab(LID_CS.offset(-ch, JoinType.Round, circular_segments=SEG), LID_TOP - 0.01, LID_TOP)])


def slot_chamfer():
    """Einführfase am Kartenschlitz: Schlitzumriss auf der Oberseite, 45° nach innen."""
    top = (slot_cut() ^ slab(LID_CS, LID_TOP - 0.02, LID_TOP + 0.02)).project()
    return Manifold.batch_hull([slab(top.offset(SLOT_CH, JoinType.Miter), LID_TOP, LID_TOP + 1),
                                slab(top, LID_TOP - SLOT_CH, LID_TOP - SLOT_CH + 0.01)])


def deckel(einfarbig=False):
    """Deckel. Gedacht für den Druck kopfüber (Oberseite auf der Platte): Symbole, Ringnuten, Fasen druckbar ohne Stützen."""
    sym = pad_symbols()
    plate = lid_plate()
    if einfarbig:      # Prototyp: ein Körper, Symbole SKIN tief vertieft (ohne Vereinigung zweier Körper an einer gemeinsamen Fläche)
        core = plate - slab(sym, LID_TOP - SKIN, LID_TOP + 1)
        skin = None
    else:
        core = plate ^ box(-1, -1, LID_BOT - 1, W + 1, W + 1, LID_TOP - SKIN)
        skin = plate ^ box(-1, -1, LID_TOP - SKIN, W + 1, W + 1, LID_TOP + 1)
        if SYM_INLAY:   # Symbole/Ringe als oranger Einleger in der Haut: gehört zum orangen Teil (ein Körper mit dem Kern)
            core = core + (skin ^ slab(sym, LID_TOP - SKIN - 0.05, LID_TOP + 1))
        skin = skin - slab(sym, LID_TOP - SKIN - 0.05, LID_TOP + 1)
    cut = [slot_cut(), slot_chamfer()]
    # Taste: glatte Bohrung bis zur Oberfläche, keine Mulde. Kopfüber liegt die Öffnung auf der Platte → keine Brücke, keine Opferschicht
    cut.append(cyl_z(BTN_X, BTN_Y, LID_BOT - 1, LID_T + 2, BTN_D / 2 + BTN_GAP))
    # Taschen für Kupferband unter den Feldern (von unten)
    for (x, y, d) in PADS.values():
        cut.append(cyl_z(x, y, LID_BOT - 1, 1 + PAD_POCKET, d / 2 - 1.0))
    # Kernlöcher von unten
    for (x, y) in RING_SCREWS + POCKET_SCREWS:
        cut.append(cyl_z(x, y, LID_BOT - 1, 1 + 4.5, PILOT / 2))
    cu = U(cut)
    if einfarbig:
        return core - cu
    return core - cu, skin - cu


def deckel_opfer(sel=None):
    """Opfer-Einleger (PLA) genau in den Vertiefungen der Symbole und Ringe, SKIN hoch. Kopfüber gedruckt liegt er in Schicht 1–4
    in den Löchern der beigen Haut; die erste orange Schicht wird dann auf PLA gedruckt statt als Brücke über Luft (dicht, eben,
    gleiche Richtung in allen Symbolen). PETG haftet nicht an PLA: nach dem Druck mit einer Nadel heraushebeln."""
    sym = pad_symbols()
    m = lid_plate() ^ slab(sym, LID_TOP - SKIN, LID_TOP + 1)
    return m if sel is None else m ^ sel


def deckel_bruecken_modifier(sel=None, rand=0.4):
    """Modifier nur für die erste orange Schicht (kopfüber Schicht 5, Schnitt bei z 0,9): Fußabdruck der Vertiefungen + rand.
    Eigener Bereich → der Slicer kann die Brücke nicht mehr über den ganzen Kreis ausdehnen (Druck 05.11.: 1760 mm² Brücke für
    597 mm² Vertiefung); hinter dem Beige liegt sonst überall dichte Füllung. Dort „Externe Brücken Füllrichtung“ fest einstellen."""
    fp = pad_symbols().offset(rand, JoinType.Round, circular_segments=SEG).simplify(0.001)
    m = slab(fp, LID_TOP - SKIN - 0.18, LID_TOP - SKIN - 0.02)
    return m if sel is None else m ^ sel


def deckel_haut_modifier(sel=None):
    """Modifier für die 4 Haut-Schichten (kopfüber Schicht 1–4, nicht Schicht 5): dort „Wandschleifen 1“, damit hinter der
    durchscheinenden ersten Schicht überall gleich gerichtete Füllbahnen liegen statt 3 Ringen um jedes Symbol.
    Höhe bis 0,05 über der Haut (Schicht 5 wird bei 0,9 geschnitten), seitlich 1 mm über den Deckel hinaus."""
    m = slab(LID_CS.offset(1.0, JoinType.Round, circular_segments=SEG).simplify(0.001), LID_TOP - SKIN - 0.05, LID_TOP)
    return m if sel is None else m ^ sel


def deckel_kopfueber(m, bezug=None):
    """Deckel(-teil) für den Druck umdrehen: Oberseite auf die Platte. Drehung um y (keine Spiegelung): hinten bleibt hinten,
    Nahtposition „Rückseite“ landet an der Hinterkante des Deckels (bis 04.11. Drehung um x: Naht wäre vorne gelandet).
    bezug: gemeinsamer Körper aller Teile (02a + 02b), damit sie nach dem Verschieben deckungsgleich bleiben."""
    rot = lambda k: k.rotate([0, 180, 0])
    bb = rot(bezug if bezug is not None else m).bounding_box()
    return rot(m).translate([-bb[0], -bb[1], -bb[2]])


def deckelrahmen():
    ring = slab(INN.offset(-RING_OFF, JoinType.Round) - INN.offset(-RING_OFF - RING_W, JoinType.Round), RING_Z0, LID_BOT)
    parts = [ring]
    # Zungen vorne
    for x in (40.0, 100.0):
        parts.append(box(x - 6, 9.4, CH_Z + 3.8, x + 6, 11.4, RING_Z0 + 0.1))
    # Blöcke hinten mit waagerechtem Kernloch
    for x in LS_X:
        parts.append(box(x - 7, W - WALL - 2.4 - 0.4 - 10, LS_BLOCK_Z0, x + 7, W - WALL - 2.4 - 0.4, LID_BOT))
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
    zb = ring_boss_bottom()
    for (x, y) in RING_SCREWS:                                              # Dome für 3,0 × 12 Senkkopf (Kopf versenkt im Dom)
        parts.append(cyl_z(x, y, zb, RING_Z0 - zb + 0.01, BOSS_D / 2))
    r = U(parts)
    cut = []
    hd = CSK[0] + 0.2
    for (x, y) in RING_SCREWS:
        cut.append(cyl_z(x, y, zb - 1, LID_BOT - zb + 2, HOLE3 / 2))
        cut.append(cyl_z(x, y, zb - 0.6, hd / 2 + 0.6, hd / 2 + 0.6, 0.0))        # 90°-Senkung, Kopf bündig mit der Domunterseite
    for x in LS_X:
        cut.append(ext_xz(tear(PILOT / 2).mirror([0, 1]).translate([x, LS_Z]), W - WALL - 2.4 - 0.4 - 9, W))
    s = SW / 2 + 0.2
    cut.append(box(BTN_X - s, BTN_Y - s, sw_bot, BTN_X + s, BTN_Y + s, RING_Z0 + 0.01))
    cut.append(cyl_z(BTN_X, BTN_Y, RING_Z0 - 0.01, RING_T + 1, COLLAR[2] + 0.5))
    cut.append(cyl_z(BTN_X, BTN_Y, RING_Z0 - 2.9, 2.9, SW / 2 + 0.2, COLLAR[2] + 0.5))     # 45°-Trichter, druckbar kopfüber
    lx = SW_LEGS / 2 + SW_LEG_CLR
    cut.append(box(BTN_X - lx, BTN_Y - 3.5, sw_bot - 4, BTN_X + lx, BTN_Y + 3.5, RING_Z0 + 0.01))   # Beinchen-Kanal: Taster mit Beinchen von oben einsetzen, Beinchen/Kabel unten raus
    cut.append(box(BTN_X - 3, BTN_Y - hw - 1, sw_bot, BTN_X + 3, BTN_Y - 5, sw_bot + 4))         # Kabelausgang
    return r - U(cut)


def ring_boss_bottom():
    """Unterseite der Ring-Dome: Senkschraube 3,0 × 12 endet 0,2 vor dem Ende des 4,5 tiefen Kernlochs im Deckel."""
    return LID_BOT + 4.3 - SCREW_L


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
    top = LID_TOP - BTN_FLUSH
    head = Manifold.batch_hull([cyl_z(BTN_X, BTN_Y, LID_BOT, top - BTN_TOP_CH - LID_BOT, BTN_D / 2),
                                cyl_z(BTN_X, BTN_Y, top - 0.01, 0.01, BTN_D / 2 - BTN_TOP_CH)])
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
    v0 = V_TAG - RC_B / 2 + RC_DROP
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
    for i, (va, vb, gv0, gv1) in enumerate(((v0 - 3, v0 + 1.5, v0 - 0.3, v0 + 1.5), (v1 - 1.5, v1 + 3, v1 - 1.5, v1 + 0.3))):
        rail = box(u0 - 3, va, ti + 1.2, u1 + 2, vb, w1 + 1.6)
        rail = rail - box(u0 - 1, gv0, w0 - 0.2, u1 + 3, gv1, w1 + 0.3)
        if i == 0:      # deckelseitige Schiene: Lippe über dem Quarz weg (Platine liegt dort nur noch auf)
            rail = rail - box(u1 - RC_XTAL_FREE, va - 1, w1 + 0.3 - 0.01, u1 + 3, vb + 1, w1 + 2.0)
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


def rc522_stecker_zone():
    """90°-Stiftleiste mit 8 Steckkabeln am Lötlochende, flach in der Platinenebene, plus Kabelbogen."""
    u0, u1, v0, v1, w0, w1 = rc_local()
    vm = (v0 + v1) / 2 + RC_HDR_OFF
    return to_world(box(u1 - 2.5, vm - 11.5, w1 - 0.5, u1 + RC_PLUG_OUT + RC_BEND, vm + 11.5, w1 + 4.0))   # Buchse 2,54 mm um den Stift, Stiftmitte ca. 1,3 mm über der Platine


def _karte_nach_kartenrahmen(m):
    """Druckkoordinaten der Karte (x, y ab Unterkante, z ab Rückseite) → Kartenrahmen (u, v, w); Drehung 180° um x, keine Spiegelung."""
    return m.rotate([180, 0, 0]).translate([-CARD_W / 2, CARD_IN, CARD_T / 2 + 0.4])


def karte_world():
    """gesteckte Karte (von der Zunge an die Rückwand gedrückt) in Einbaulage"""
    return to_world(_karte_nach_kartenrahmen(karte_print()))


def einleger_world(t=0.3):
    """Papier-Cover in der Tasche (nur für Ansichten)"""
    w, h = einleger_mass()
    zf = CARD_T - INS_FRONT - INS_LIP - INS_GAP
    e = box(CARD_W / 2 - w / 2, INS_Y0 + INS_CLR, zf, CARD_W / 2 + w / 2, INS_Y0 + INS_CLR + h, zf + t)
    return to_world(_karte_nach_kartenrahmen(e))


def einleger_mass():
    """Einleger (Papier-Cover) Breite × Höhe in mm."""
    w = CARD_W - 2 * INS_WALL - 2 * INS_CLR
    h = CARD_H - INS_Y0 - 0.5            # 0,5 mm unter der Oberkante
    return w, h


def karte_fenster():
    """sichtbares Fenster (x0, y0, x1, y1) in Kartenkoordinaten von vorne gesehen, y ab Kartenunterkante"""
    x0 = INS_WALL + INS_LIP
    return x0, INS_Y0 + INS_LIP, CARD_W - x0, CARD_H


def karte_print():
    """Karte flach, Rückseite unten (NFC-Tasche an der Platte, Decke Ø 25 mm als Brücke), Vorderseite mit Einschubtasche oben.
    Koordinaten wie von vorne gesehen: x nach rechts, y = 0 Kartenunterkante (steckt im Fach), z = 0 Rückseite.
    Tasche: Boden auf zf, Spalt INS_GAP an der Außenwand, darüber Lippen mit 45°-Unterseite, oben offen."""
    T = CARD_T
    R0 = 5.0
    out = rr(0, 0, CARD_W, CARD_H, R0) ^ CrossSection.square([CARD_W, CARD_H - 10]) 
    out = out + rr(0, CARD_H - 20, CARD_W, CARD_H, CARD_TOP_R)
    c = slab(out, 0, T)
    zf = T - INS_FRONT - INS_LIP - INS_GAP
    a, l = INS_WALL, INS_LIP
    top = CARD_H + 1
    gap = box(a, INS_Y0, zf, CARD_W - a, top, zf + INS_GAP)
    wedge = Manifold.batch_hull([box(a, INS_Y0, zf + INS_GAP - 0.01, CARD_W - a, top, zf + INS_GAP),
                                 box(a + l, INS_Y0 + l, zf + INS_GAP + l - 0.01, CARD_W - a - l, top, zf + INS_GAP + l)])
    window = box(a + l, INS_Y0 + l, zf + INS_GAP + l - 0.01, CARD_W - a - l, top, T + 1)
    c = c - U([gap, wedge, window])
    c = c - cyl_z(CARD_W / 2, CARD_H, -1, zf + 1.01, GRIP_R)                         # Griffmulde hinten oben
    c = c - cyl_z(CARD_W / 2, 1.0 + NFC_D / 2, -1, 1 + NFC_T + 0.4, NFC_D / 2 + 0.3)   # NFC-Tasche hinten unten
    return c


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
    """Überholt 05.11.2026: ersetzt durch das gedruckte Gitter `gitter()`; nicht mehr in build()."""
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


# --- Gitter vorne mit Logo (ersetzt Stoff + Stoffrahmen, Nachtrag 05.11.2026 (6)) ---
GR_T = par("GR_T", 3.6, "festgelegt", "Gitterdicke (18 Schichten); liegt hinten auf der Sitzfläche (y = SEAT_D), Vorderfläche 0,2 hinter der Korpusfront")
GR_HOLE = par("GR_HOLE", (3.3, 4.2), "festgelegt", "Löcher Ø und Teilung im Wabenraster, mittig zu (70, 70); Steg 0,9 = 2 Linien")
GR_RIM = par("GR_RIM", 4.5, "festgelegt", "geschlossener Rand außen (an der Vorderfläche)")
GR_RIM_BACK = par("GR_RIM_BACK", 1.2, "festgelegt", "Mindeststeg Loch ↔ schräge Oberkante hinten (Sitz fällt oben nach hinten ab)")
GR_LOGO = par("GR_LOGO", (100.0, 70.0, 76.0), "festgelegt", "Logo Breite, Mitte x, Mitte z (Vorlage Jan 05.11., gitter/peppa_box_logo.png)")
GR_LETTER_T = par("GR_LETTER_T", 1.2, "festgelegt",
                  "Logo-Buchstaben als eigene orange Teile, 1,2 dick, aufgeklebt auf die glatte Gitterfläche (stehen 1,0 vor der Korpusfront; 3D-Effekt, Entscheidung Jan 06.11.)")
GR_PEG = par("GR_PEG", (2.0, 1.0, 0.2), "Probedruck",
             "Stifte hinten an den Buchstaben: Ø (bei schmalen Teilen kleiner), Länge, Spiel je Seite im Sackloch des Gitters (Loch 0,3 tiefer). Mit C14 prüfen")
GR_KEEP = par("GR_KEEP", 1.2, "festgelegt", "geschlossener beiger Rand um das Logo bis zum ersten Loch")
GR_PLENUM = par("GR_PLENUM", 1.2, "festgelegt",
                "Luftraum: Gitter hinten über der Lautsprecher-Mulde 1,2 dünner (2,4 statt 3,6), damit der Schall hinter dem Logo zu den Löchern kommt. "
                "Lautsprecherrahmen ca. 1,3 hinter der Sitzfläche, Schraubenköpfe liegen dahinter (Jan 05.11.) → 2,5 mm Luft")
GR_EDGE_CH = par("GR_EDGE_CH", 0.4, "festgelegt", "Fase 45° an der Vorderkante außen")
GR_PIN_D = par("GR_PIN_D", 3.9, "Probedruck", "Stift Ø (Loch im Korpus PIN_HOLE 4,1; mit C14 am Korpus prüfen)")
GR_PIN_L = par("GR_PIN_L", 2.4, "festgelegt", "Stiftlänge hinter der Sitzfläche (Loch 2,8 tief), Spitze 0,4 gefast")


def _seat_top(y):
    """Oberkante des Gitter-Sitzes im Korpus bei Tiefe y (Hülle wie im Korpus: z = SEAT[3] + 1 bei y = 0, SEAT[3] − SEAT_D bei y = SEAT_D)."""
    y = min(max(y, 0.0), SEAT_D)
    return SEAT[3] + 1.0 - (SEAT_D + 1.0) * y / (SEAT_D - 0.01)


def gitter_env():
    """Raum für das Gitter: Sitz im Korpus, ringsum CLR kleiner; an der schrägen Oberkante CLR senkrecht zur Fläche."""
    sx0, sx1, sz0, sz1 = SEAT
    c = CLR
    ct = CLR / math.cos(math.atan((SEAT_D + 1.0) / SEAT_D))          # senkrecht zur Schräge gemessen
    prof = lambda top: rr(sx0 + c, sz0 + c, sx1 - c, top - ct, SEAT_R - c)
    return Manifold.batch_hull([ext_xz(prof(sz1 + 1.0), -1, 0), ext_xz(prof(sz1 - SEAT_D), SEAT_D - 0.01, SEAT_D)])


def gitter_logo_cs():
    import os, sys
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gitter")
    if d not in sys.path:
        sys.path.insert(0, d)
    from logo import logo_cs
    w, x, z = GR_LOGO
    return logo_cs(w).translate([x, z])


def gitter_bay_cs():
    """Öffnung der Lautsprecher-Mulde auf Höhe der Sitzfläche (y = SEAT_D), wie im Korpus (Oberkante 45° nach vorn erweitert)."""
    bh = SPK_FRAME / 2 + 2
    top = SPK_Z + bh + (BAY_D + 1) * (1 - SEAT_D / BAY_D)
    return rr(SPK_X - bh, SPK_Z - bh, SPK_X + bh, top, SPK_FRAME_R + 2)


def gitter_holes(logo=None):
    """Lochmitten im Wabenraster, mittig zu (70, 70). Ganze Löcher entfallen, wo sie Rand, Logo-Rand oder Stifte schneiden."""
    sx0, sx1, sz0, sz1 = SEAT
    m = CLR
    x0, x1, z0, z1 = sx0 + m, sx1 - m, sz0 + m, sz1 - m
    d, p = GR_HOLE
    inner = rr(x0 + GR_RIM, z0 + GR_RIM, x1 - GR_RIM, z1 - GR_RIM, SEAT_R - m - GR_RIM)
    ct = CLR / math.cos(math.atan((SEAT_D + 1.0) / SEAT_D))
    z_max = _seat_top(SEAT_D) - ct - GR_RIM_BACK - d / 2              # schräge Oberkante hinten
    logo = gitter_logo_cs() if logo is None else logo
    keep = logo.offset(GR_KEEP, JoinType.Round)
    for (px, pz) in frame_pins():
        keep = keep + CrossSection.circle(GR_PIN_D / 2 + 0.9, SEG).translate([px, pz])
    out = []
    dz = p * math.sqrt(3) / 2
    for k in range(-40, 41):
        z = 70.0 + k * dz
        if z > z_max or z < z0:
            continue
        off = p / 2 if k % 2 else 0.0
        for j in range(-40, 41):
            x = 70.0 + off + j * p
            if not (x0 < x < x1):
                continue
            c = _hole_cs(x, z)
            if (c - inner).area() > 1e-6 or (c ^ keep).area() > 1e-6:
                continue
            out.append((x, z))
    return out


def _hole_cs(x, z):
    """Loch als 32-Eck, um eine halbe Teilung gedreht: keine Ecke liegt auf den Rasterrichtungen 0°/60°/120°
    (dort läuft der Rand des Luftraums durch die Lochmitte – sonst fielen Ecken zusammen)."""
    r = GR_HOLE[0] / 2
    return CrossSection([[(x + r * math.cos((k + 0.5) * math.pi / 16), z + r * math.sin((k + 0.5) * math.pi / 16)) for k in range(32)]])


def gitter_lattice():
    """Wabenraster: Zeilen k mit Punkten (x, z), mittig zu (70, 70)."""
    _, p = GR_HOLE
    dz = p * math.sqrt(3) / 2
    rows = {}
    for k in range(-16, 17):
        off = p / 2 if k % 2 else 0.0
        rows[k] = [(70.0 + off + j * p, 70.0 + k * dz) for j in range(-16, 17)]
    return rows


def gitter_plenum_cs():
    """Luftraum hinten (Grundriss): alle Dreiecke des Lochrasters, deren Mitte in der Mulden-Öffnung (0,5 kleiner) liegt.
    Der Rand läuft so immer durch Lochmitten: Er schneidet die Löcher senkrecht, es bleiben keine Sicheln oder Spitzen
    zwischen Luftraum und Loch (Schichtanalyse 05.11.), und die STL bleibt sauber geschlossen."""
    rec = gitter_bay_cs().offset(-0.5, JoinType.Round)
    rows = gitter_lattice()
    tris = []
    for k in sorted(rows)[:-1]:
        A, B = rows[k], rows[k + 1]
        up = B[0][0] > A[0][0]                      # obere Zeile um eine halbe Teilung nach rechts versetzt
        for j in range(len(A) - 1):
            if up:
                cand = [(A[j], A[j + 1], B[j]), (B[j], B[j + 1], A[j + 1])]
            else:
                cand = [(A[j], A[j + 1], B[j + 1]), (B[j], B[j + 1], A[j])]
            for t in cand:
                cx, cz = sum(q[0] for q in t) / 3, sum(q[1] for q in t) / 3
                if (CrossSection.circle(0.05, 8).translate([cx, cz]) - rec).area() < 1e-9:
                    tris.append(CrossSection([[t[0], t[1], t[2]]], FillRule.Positive) if _ccw(t) else CrossSection([[t[0], t[2], t[1]]], FillRule.Positive))
    return CrossSection.batch_boolean(tris, m3.OpType.Add).offset(0.001).offset(-0.001)


def _ccw(t):
    (ax, ay), (bx, by), (cx, cy) = t
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) > 0


def gitter_buchstaben_cs():
    """Die 11 Teile des Logos (5 Buchstaben oben, 3 Strahlen, B, O, X) als einzelne Querschnitte, sortiert oben links → unten rechts."""
    parts = gitter_logo_cs().decompose()
    cz = lambda c: (c.bounds()[1] + c.bounds()[3]) / 2
    cx = lambda c: (c.bounds()[0] + c.bounds()[2]) / 2
    zmid = GR_LOGO[2]
    top = sorted([c for c in parts if cz(c) > zmid - 3], key=cx)
    bot = sorted([c for c in parts if cz(c) <= zmid - 3], key=cx)
    return top + bot


def gitter_stifte(cs):
    """Stift-Querschnitte unter einem Logo-Teil. Buchstaben: zwei runde Stifte möglichst weit auseinander (verdrehsicher), dort,
    wo der Buchstabe am breitesten ist. Schmale Teile (Strahlen), in die nur ein runder Stift passt: ein Stift in der Form des
    Teils, 0,7 mm kleiner (verdrehsicher). Das Sackloch im Gitter (Stift + Spiel) bleibt mindestens 0,4 mm unter dem Rand verdeckt."""
    import cv2
    import numpy as np
    R = 20.0                                                        # px je mm
    x0, y0, x1, y1 = cs.bounds()
    pad = 2.0
    w, h = int((x1 - x0 + 2 * pad) * R), int((y1 - y0 + 2 * pad) * R)
    img = np.zeros((h, w), np.uint8)
    for poly in cs.to_polygons():
        t = np.zeros_like(img)
        pts = np.round(np.c_[(np.array(poly)[:, 0] - x0 + pad) * R, (y1 + pad - np.array(poly)[:, 1]) * R]).astype(np.int32)
        cv2.fillPoly(t, [pts], 1)
        img ^= t
    dist = cv2.distanceTransform(img, cv2.DIST_L2, 5) / R          # Abstand zum Rand in mm
    dmax, (lx, ly) = dist.max(), np.unravel_index(dist.argmax(), dist.shape)[::-1]
    d_max, L, clr = GR_PEG
    d = min(d_max, 2 * (dmax - clr - 0.4))
    to_mm = lambda q: (q[1] / R + x0 - pad, y1 + pad - q[0] / R)
    if d >= 1.8:
        need = d / 2 + clr + 0.4 + 0.15                             # + 0,15 Reserve für das Raster
        ok = np.argwhere(dist >= need)                              # (Zeile, Spalte)
        p1 = np.array([ly, lx])
        far = ok[np.argmax(((ok - p1) ** 2).sum(axis=1))] if len(ok) else p1
        if np.hypot(*(far - p1)) / R >= 2.0 * d:
            return [CrossSection.circle(d / 2, SEG).translate(list(to_mm(q))) for q in (p1, far)]
    return [cs.offset(-(clr + 0.5), JoinType.Round).simplify(0.005)]


def _konvex(cs):
    return abs(CrossSection.hull(cs).area() - cs.area()) < 1e-3 * max(cs.area(), 1e-9)


def gitter():
    """Gedrucktes Frontgitter mit Logo (Stand 06.11.2026). Rückgabe (beige, buchstaben_orange) im Einbauzustand.
    Das Gitter ist einfarbig beige (Vorderfläche auf der texturierten PEI-Platte, kein Farbwechsel). Die Buchstaben sind eigene
    orange Teile, 1,2 mm dick, Sichtseite ebenfalls auf der PEI-Platte gedruckt, mit Stiften in Sacklöchern des Gitters, aufgeklebt."""
    yf = SEAT_D - GR_T
    env = gitter_env()
    sx0, sx1, sz0, sz1 = SEAT
    c = CLR
    face = rr(sx0 + c, sz0 + c, sx1 - c, _seat_top(yf) - 0.5, SEAT_R - c)    # Umriss vorne (für die Fase)
    e = GR_EDGE_CH
    ch = Manifold.batch_hull([ext_xz(face.offset(-e, JoinType.Round), yf, yf + 0.01),
                              ext_xz(face.offset(10 - e, JoinType.Round), yf + 10, yf + 10.01)])
    logo = gitter_logo_cs()
    holes = CrossSection.batch_boolean([_hole_cs(x, z) for (x, z) in gitter_holes(logo)], m3.OpType.Add)
    big = CrossSection.square([200, 200]).translate([-30, -30])
    yb = SEAT_D - GR_PLENUM
    plate = (ext_xz(big - holes, yf, SEAT_D) ^ env ^ ch) - ext_xz(gitter_plenum_cs(), yb, SEAT_D + 1)
    _, L, clr = GR_PEG
    letters, sacks = [], []
    for cs in gitter_buchstaben_cs():
        body = [ext_xz(cs, yf - GR_LETTER_T, yf)]
        for pc in gitter_stifte(cs):
            # (Offsets mit simplify: sonst entstehen beim Runden winzige Kanten → doppelte Ecken in der STL)
            tip = pc.offset(-0.2, JoinType.Round).simplify(0.005)       # Spitze 0,2 kleiner: findet ins Loch
            if _konvex(pc):                                             # runder Stift: ein Körper mit gefaster Spitze
                body.append(Manifold.batch_hull([ext_xz(pc, yf - 0.01, yf + L - 0.3), ext_xz(tip, yf + L - 0.01, yf + L)]))
            else:                                                       # geformter Stift (Strahlen): gerade, ohne Fase
                body.append(ext_xz(pc, yf - 0.01, yf + L))
            sacks.append(ext_xz(pc.offset(clr, JoinType.Round).simplify(0.005), yf - 1, yf + L + 0.3))
        letters.append(U(body))
    pins = []
    r = GR_PIN_D / 2
    for (x, z) in frame_pins():
        pins.append(cyl_y(SEAT_D - 0.01, SEAT_D + GR_PIN_L - 0.4, x, z, r))
        pins.append(Manifold.cylinder(0.4, r, r - 0.4, SEG).rotate([-90, 0, 0]).translate([x, SEAT_D + GR_PIN_L - 0.4, z]))
    beige = U([plate - U(sacks)] + pins)
    return beige, U(letters)


def gitter_druck(m, bezug):
    """Gitter für den Druck: Vorderfläche auf die Platte, Oberkante nach hinten (+Y). Drehung, keine Spiegelung.
    Nahtposition „Rückseite“ landet so an der Oberseite jedes Lochs (von vorn-oben unsichtbar) und an der Gitter-Oberkante."""
    rot = lambda k: k.rotate([90, 0, 180])
    bb = rot(bezug).bounding_box()
    return rot(m).translate([-bb[0], -bb[1], -bb[2]])


def buchstaben_druck(letters=None, abstand=4.0):
    """Alle Logo-Teile auf einer Platte: Sichtseite unten auf der PEI, Stifte oben; Unterkante jedes Buchstabens zeigt nach
    hinten (+Y), damit die Naht „Rückseite“ an der im Einbau unteren Seite liegt. Reihenfolge wie im Logo, auseinandergezogen,
    bis zwischen allen Teilen mindestens `abstand` mm frei sind (sonst verschmelzen die 0,6-mm-Lücken)."""
    if letters is None:
        letters = gitter()[1]
    parts = letters.decompose() if isinstance(letters, Manifold) else letters
    rot = [p.rotate([90, 0, 180]).rotate([0, 0, 180]) for p in parts]        # = rotate([90, 0, 0]): Unterkante → +Y
    cen = [((b[0] + b[3]) / 2, (b[1] + b[4]) / 2) for b in (m.bounding_box() for m in rot)]
    gx = sum(c[0] for c in cen) / len(cen); gy = sum(c[1] for c in cen) / len(cen)
    f = 1.0
    while True:
        moved = [m.translate([(cx - gx) * (f - 1), (cy - gy) * (f - 1), 0]) for m, (cx, cy) in zip(rot, cen)]
        gap = min(a.min_gap(b, abstand + 1) for i, a in enumerate(moved) for b in moved[i + 1:])
        if gap >= abstand:
            break
        f += 0.02
    out = U(moved)
    bb = out.bounding_box()
    return out.translate([-bb[0], -bb[1], -bb[2]])


def knob_geo():
    """Lage der Knopf-Innenmaße entlang x (Wand außen = W)."""
    inner = W - FUZZ_REC - ENC_WALL                                   # Gehäusefläche des Drehgebers = Innenseite der Wand
    thread_end = inner + ENC_THREAD
    x0 = W + KNOB_GAP
    rec_end = max(thread_end, W - FUZZ_REC + ENC_NUT[0] + ENC_NUT[1]) + ENC_PUSH + 0.4
    tip = W + ENC_OUT
    bore_end = tip + KNOB_TIP
    return x0, rec_end, bore_end, bore_end + KNOB_ROOF


def drehknopf():
    """Orange Knopf auf der ganzen (ungekürzten) Schlitzachse: Führung im ungeschlitzten Teil, Klemmsitz Ø 6,1 im geschlitzten Teil,
    Steg im Schlitz; deckt Mutter und glatte Fläche ab."""
    x0, rec_end, bore_end, x1 = knob_geo()
    L = x1 - x0
    k = Manifold.batch_hull([cyl_x(x0, x1 - 2, ENC_Y, ENC_Z, KNOB_D / 2),
                             cyl_x(x1 - 0.01, x1, ENC_Y, ENC_Z, KNOB_D / 2 - 2)])
    for i in range(24):
        a = 2 * math.pi * i / 24
        k = k - cyl_x(x0 + 1.5, x1 - 3, ENC_Y + math.cos(a) * (KNOB_D / 2 + 0.6), ENC_Z + math.sin(a) * (KNOB_D / 2 + 0.6), 1.3)
    k = k - box(x1 - 0.6, ENC_Y - 0.9, ENC_Z + 6, x1 + 1, ENC_Y + 0.9, ENC_Z + 13)   # Markierung
    k = k - cyl_x(x0 - 1, rec_end, ENC_Y, ENC_Z, NUT_REC_D / 2)
    tip = W + ENC_OUT
    slot_bot = tip - ENC_SLOT_D                                                 # Schlitzgrund: darunter federt die Achse nicht
    clamp0 = max(rec_end, slot_bot + 0.5)
    k = k - cyl_x(rec_end - 0.1, clamp0 + 0.01, ENC_Y, ENC_Z, KNOB_GUIDE / 2)  # Führung
    k = k - cyl_x(clamp0, bore_end, ENC_Y, ENC_Z, KNOB_BORE / 2)                # Klemmsitz
    rib0 = bore_end - max(1.0, min(ENC_SLOT_D - 0.5, KNOB_RIB))
    k = k + box(rib0, ENC_Y - 3.2, ENC_Z - ENC_SLOT / 2 + 0.1, bore_end, ENC_Y + 3.2, ENC_Z + ENC_SLOT / 2 - 0.1)
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
    pcb_bot, pcb_top, y_edge, holes = usbc_geo()
    u = USBC
    x = u["x"]
    lat, a, b, _ = USBC_LEGS
    ph["USB-C-Platine mit Buchse und Kabeln"] = U([
        box(x - u["pcb"] / 2, y_edge - u["pcb"], pcb_bot, x + u["pcb"] / 2, y_edge, pcb_top),                       # Platine
        box(x - u["buchse_b"] / 2, y_edge - 7.9, pcb_top, x + u["buchse_b"] / 2, y_edge, pcb_top + u["buchse_h"]),     # Buchse
        box(x - u["pcb"] / 2, y_edge - u["pcb"], pcb_top, x + u["pcb"] / 2, y_edge - 15.0, pcb_top + 12.0),           # Lötreihe, Kabel, Widerstände
        box(x - lat - 0.5, y_edge - b - 0.5, pcb_bot - 1.2, x + lat + 0.5, y_edge - a + 0.5, pcb_bot),                # Lötfahnen unten
    ] + [cyl_z(hx, hy, pcb_top, 3.0, 3.1) for (hx, hy) in holes])                                                # Schraubenköpfe
    spk_front = BAY_D - SPK_FLANGE
    flange = ext_xz(rr(SPK_X - SPK_FRAME / 2, SPK_Z - SPK_FRAME / 2, SPK_X + SPK_FRAME / 2, SPK_Z + SPK_FRAME / 2, SPK_FRAME_R), spk_front, BAY_D)
    basket = cyl_y(BAY_D + 3, spk_front + SPK_DEPTH - 8, SPK_X, SPK_Z, 35.5)
    magnet = cyl_y(spk_front + SPK_DEPTH - 8, spk_front + SPK_DEPTH, SPK_X, SPK_Z, SPK_MAG / 2)
    ph["Lautsprecher"] = U([flange, basket, magnet])
    e = W - FUZZ_REC - ENC_WALL                                     # Innenfläche der Wand am Drehgeber
    ph["Drehgeber"] = box(e - 16, ENC_Y - 6.5, ENC_Z - 6.5, e, ENC_Y + 6.5, ENC_Z + 6.5)
    j = W - FUZZ_REC - JK_WALL
    ph["Klinkenbuchse"] = box(j - 15, JK_Y - 6, JK_Z - 6, j, JK_Y + 6, JK_Z + 6)
    ph["Kurzhubtaster"] = box(BTN_X - SW / 2, BTN_Y - SW / 2, act_top() - SW_H, BTN_X + SW / 2, BTN_Y + SW / 2, act_top())
    ph["RC522"] = rc522_placeholder()
    ph["RC522-Stecker (Zone)"] = rc522_stecker_zone()
    ph["Karte (gesteckt)"] = karte_world()
    return ph


# Gruppen für die Prüfungen
BASE_PH = ["Akku-Board mit Zellen", "Pi + Klemmen-Aufsatz", "Kabel Klemmreihe links (Zone)",
           "Kabel Klemmreihe rechts (Zone)", "Kabel Klemmreihe hinten (Zone)", "USB-C-Stecker am Akku-Board (Zone)",
           "Klinkenstecker am Pi (Zone)",
           "WAGO GND A", "WAGO 5 V", "Verstärker"]
LID_PH = ["RC522", "Kurzhubtaster", "Karte (gesteckt)", "WAGO GND B", "WAGO 3,3 V", "WAGO SCL", "Touch-Modul MPR121"]
WALL_PH = ["Lautsprecher", "Drehgeber", "Klinkenbuchse", "USB-C-Platine mit Buchse und Kabeln"]


def build():
    lid_o, lid_b = deckel()
    gr_b, gr_o = gitter()
    parts = {
        "korpus": korpus(),
        "deckel_orange": lid_o,
        "deckel_beige": lid_b,
        "deckelrahmen": deckelrahmen(),
        "kartenfach": kartentasche(),
        "boden": boden(),
        "gitter_beige": gr_b,
        "gitter_logo": gr_o,
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
