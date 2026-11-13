"""Peppa-Box Kartenbox – parametrisches Druckmodell (CadQuery, PETG, Elegoo Centauri Carbon 2).

Aufbewahrungsbox für bis zu 30 Karten (3 Fächer à 10), Klappdeckel mit Schnappverschluss, beiges Inlay, Bandösen.

Koordinaten im Gebrauchszustand (alles in mm):
  x  links→rechts (Mitte der Box = 0), Stapelrichtung der Karten
  y  vorne (0) → hinten (D_B), Kartenbreite
  z  oben, Boden der Basis = 0, Oberkante Basis (Deckelfuge) = Z_RIM
Status jedes Werts: belegt (aus echter Datei/Datenblatt) · festgelegt (Gestaltung) · berechnet · Probedruck (am Drucker einstellen).
"""
import math
import cadquery as cq

P = {}


def par(name, v, status, note=""):
    P[name] = dict(v=v, s=status, q=note)
    return v


# ---------------------------------------------------------------------------------------------
# Karte (belegt: Maße der gedruckten Karte 10_karte_orange.stl, Begrenzungsquader 70 × 112 × 4)
# ---------------------------------------------------------------------------------------------
CARD_W = par("CARD_W", 70.0, "belegt", "Kartenbreite (y in der Box)")
CARD_H = par("CARD_H", 112.0, "belegt", "Kartenhöhe (z in der Box)")
CARD_T = par("CARD_T", 4.0, "belegt", "Kartendicke (x, Stapelrichtung)")

# Fächer
NC = par("NC", 3, "festgelegt", "Anzahl Fächer")
PER = par("PER", 10, "festgelegt", "Karten je Fach → 30 insgesamt")
SPARE = par("SPARE", 8.0, "festgelegt", "freie Breite je Fach über den Kartenstapel hinaus (2 Karten Luft, Finger, Toleranz gedruckter Karten)")
SLOT_W = par("SLOT_W", PER * CARD_T + SPARE, "berechnet", "Fachbreite innen")
PLAY_Y = par("PLAY_Y", 4.0, "festgelegt", "Spiel der Karte in y (je Seite 2 mm). Klein halten: die Karte darf oben nicht nach vorn kippen (Schwenkprüfung Deckel)")

# Inlay (beige, eigenes Teil)
DIV = par("DIV", 2.1, "festgelegt", "Wand/Trennwand Inlay (5 Linien à 0,42)")
LINER_FLOOR = par("LINER_FLOOR", 2.0, "festgelegt", "Boden Inlay")
LINER_H = par("LINER_H", 50.0, "festgelegt", "Inlay-Höhe über dem Basisboden (Sparmöglichkeit: niedriger = weniger beiges Filament)")
LINER_CLR = par("LINER_CLR", 0.3, "Probedruck", "Spiel Inlay zur Basis je Seite")
LINER_X = par("LINER_X", NC * SLOT_W + (NC + 1) * DIV, "berechnet", "Inlay außen, x")
LINER_Y = par("LINER_Y", CARD_W + PLAY_Y + 2 * DIV, "berechnet", "Inlay außen, y")

LINER_R_IN = par("LINER_R_IN", 7.0, "festgelegt", "Eckradius innen im Inlay: klein genug, damit die Eckkante der Randkarte (70 mm breit) nicht in die Rundung stößt (Rechnung in check.py)")

# Basis (orange)
WALL = par("WALL", 2.52, "festgelegt", "Wandstärke Basis (6 Linien à 0,42)")
BASE_FLOOR = par("BASE_FLOOR", 3.0, "festgelegt", "Bodenstärke Basis")
R_OUT = par("R_OUT", 18.0, "festgelegt", "Eckradius außen (organisch, keine spitzen Ecken)")
HC = par("HC", 14.0, "festgelegt", "Karten stehen so weit über die Deckelfuge (Griff). Obergrenze durch Schwenkprüfung (check.py)")
W_I = par("W_I", LINER_X + 2 * LINER_CLR, "berechnet", "Basis innen, x")
D_I = par("D_I", LINER_Y + 2 * LINER_CLR, "berechnet", "Basis innen, y")
W_B = par("W_B", W_I + 2 * WALL, "berechnet", "Basis außen, x")
D_B = par("D_B", D_I + 2 * WALL, "berechnet", "Basis außen, y")
R_IN = par("R_IN", R_OUT - WALL, "berechnet", "Eckradius innen")
CARD_Z0 = par("CARD_Z0", BASE_FLOOR + LINER_FLOOR, "berechnet", "Kartenunterkante (Inlayboden)")
Z_RIM = par("Z_RIM", CARD_Z0 + CARD_H - HC, "berechnet", "Oberkante Basis = Deckelfuge")

# Deckel (orange)
LID_CLR = par("LID_CLR", 0.4, "Probedruck", "Spiel Deckelhaut zur Basis (Außenseite)")
LID_WALL = par("LID_WALL", 1.68, "festgelegt", "Deckelwand (4 Linien à 0,42)")
LID_OVER = par("LID_OVER", LID_CLR + LID_WALL, "berechnet", "Deckel steht ringsum so weit über die Basis")
LID_ROOF = par("LID_ROOF", 3.0, "festgelegt", "Deckeldach")
LID_CAV = par("LID_CAV", HC + 4.0, "festgelegt", "Innenhöhe des Deckels über der Fuge: Kartenüberstand + 4 mm Luft")
LID_TOP = par("LID_TOP", LID_CAV + LID_ROOF, "berechnet", "Deckeloberkante über der Fuge")
SKIRT = par("SKIRT", 8.0, "festgelegt", "Deckelhaut reicht so weit unter die Fuge (vorn und seitlich)")
SEAT_H = par("SEAT_H", 3.0, "festgelegt", "Sitzleiste im Deckel auf der Basiskante, Höhe (45°-Anlauf, druckt ohne Stützen)")
SEAT_IN = par("SEAT_IN", 1.2, "festgelegt", "Sitzleiste endet so weit vor der Innenwand der Basis (Abstand zu den Karten)")
W_L = W_B + 2 * LID_OVER
D_L = D_B + 2 * LID_OVER
R_L = R_OUT + LID_OVER

ROOF_CH = par("ROOF_CH", 3.0, "festgelegt", "Dachkante: 45°-Fase (liegt beim Druck auf dem Bett → kein Überhang)")
ROOF_R1 = par("ROOF_R1", 3.0, "festgelegt", "Verrundung zwischen Fase und Seitenwand")
ROOF_R2 = par("ROOF_R2", 1.2, "festgelegt", "Verrundung der Kante zur Dachfläche (Bettseite, klein halten)")

# Scharnier
LH = par("LH", 92.0, "festgelegt", "Länge des Scharnierpakets (5 Knöchel) – Stift Ø 3 × 90 mm")
AX = par("AX", 0.5, "Probedruck", "Axialspiel zwischen den Knöcheln")
NSEG = 5
SEG = (LH - (NSEG - 1) * AX) / NSEG
RK = par("RK", 3.5, "festgelegt", "Knöchelradius (Wand um den Stift 1,85 mm)")
PIN_D = par("PIN_D", 3.0, "belegt", "Stahlstift Ø 3 mm (Zylinderstift, Länge 90 mm; Maß noch nicht beim Händler geprüft)")
BORE_BASE = par("BORE_BASE", 3.0, "Probedruck", "Bohrung in den Basis-Knöcheln: Presssitz (gedruckte Löcher werden ca. 0,1–0,2 mm enger)")
BORE_LID = par("BORE_LID", 3.5, "Probedruck", "Bohrung in den Deckel-Knöcheln: frei drehend")
END_WALL = par("END_WALL", 1.2, "festgelegt", "Blindende links im Basis-Knöchel")
Y_H = D_B + LID_OVER + LID_CLR + RK      # Achse hinter der Deckelrückwand
Z_H = Z_RIM                              # Achse liegt in der Fugenebene

# Schnappverschluss (Zunge am Deckel, Haken greift in Nut der Basis)
TW = par("TW", 30.0, "festgelegt", "Breite der Zunge")
SLIT = par("SLIT", 1.0, "festgelegt", "Schlitz neben der Zunge")
TONGUE_Z0 = par("TONGUE_Z0", -22.0, "festgelegt", "Zungenende unter der Fuge (freie Federlänge ca. 22 mm → Biegedehnung unter 0,5 %)")
HOOK_H = par("HOOK_H", 1.2, "festgelegt", "Hakenhöhe ab Zungeninnenseite (0,4 Spalt + 0,8 Eingriff)")
HOOK_TIP = par("HOOK_TIP", 0.6, "festgelegt", "flache Hakenspitze")
HOOK_W = par("HOOK_W", 24.0, "festgelegt", "Hakenbreite")
GROOVE_CLR = par("GROOVE_CLR", 0.2, "Probedruck", "Spiel Haken ↔ Nut je Seite")
PRELOAD = par("PRELOAD", 0.15, "Probedruck", "Nut sitzt so viel tiefer: Haken drückt den Deckel auf die Kante (kein Klappern)")
TAB_OUT = par("TAB_OUT", 4.0, "festgelegt", "Daumenlasche unten an der Zunge, Ausladung (45°-Flanke, druckt ohne Stützen)")
TAB_W = par("TAB_W", 26.0, "festgelegt", "Breite der Lasche")

# Bandöse (beidseitig an der Basis)
LUG_R = par("LUG_R", 8.0, "festgelegt", "Radius der Ösenrundung")
LUG_OUT = par("LUG_OUT", 6.0, "festgelegt", "Abstand Ösenmitte von der Wand")
LUG_T = par("LUG_T", 14.0, "festgelegt", "Ösenbreite in y (Bandbreite)")
LUG_HOLE = par("LUG_HOLE", 6.5, "festgelegt", "Loch Ø (Kordel bis 5 mm, Tropfenform druckt ohne Stützen)")
LUG_Z = par("LUG_Z", Z_RIM - 24.0, "festgelegt", "Ösenmitte, unterhalb der Deckelhaut")

# ---------------------------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------------------------
YC = D_B / 2.0


def rr(w, d, r, z0, z1, yc=YC):
    """gerundetes Rechteck, extrudiert von z0 bis z1, mittig in x, y-Mitte yc."""
    return (cq.Workplane("XY").workplane(offset=z0).center(0, yc).rect(w, d).extrude(z1 - z0)
            .edges("|Z").fillet(r))


def rr_wire(w, d, r, z, yc=YC):
    wp = cq.Workplane("XY", origin=(0, yc, z)).rect(w, d).val()
    return wp.fillet2D(r, wp.Vertices())


def loft_rr(w0, d0, r0, z0, w1, d1, r1, z1):
    return cq.Workplane("XY").add(cq.Solid.makeLoft([rr_wire(w0, d0, r0, z0), rr_wire(w1, d1, r1, z1)], True))


def yz_poly(pts, x0, x1):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0)


def yz_circle(yc, zc, r, x0, x1):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).center(yc, zc).circle(r).extrude(x1 - x0)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def soft_bottom_edge(wp, chamfer, rad):
    """untere Kante (Druckbett): 45°-Fase, darüber Verrundung – druckt ohne Überhang."""
    wp = wp.faces("<Z").edges().chamfer(chamfer)
    return wp


# ---------------------------------------------------------------------------------------------
# Scharnier-Segmente
# ---------------------------------------------------------------------------------------------
def seg_x(i):
    x0 = -LH / 2 + i * (SEG + AX)
    return x0, x0 + SEG


def base_knuckle(i):
    x0, x1 = seg_x(i)
    z = Z_H
    d = Y_H - D_B
    web = yz_poly([(D_B - 1.0, z - 0.5), (Y_H, z - 0.5), (Y_H, z - RK), (D_B, z - RK - d), (D_B - 1.0, z - RK - d)], x0, x1)
    return web.union(yz_circle(Y_H, z, RK, x0, x1))


def lid_knuckle(i):
    x0, x1 = seg_x(i)
    z = Z_H
    wo = D_B + LID_OVER                      # Außenfläche Deckelrückwand
    d = Y_H - wo
    web = yz_poly([(wo - 0.6, z), (Y_H, z), (Y_H, z + RK), (wo, z + RK + d), (wo - 0.6, z + RK + d)], x0, x1)
    return web.union(yz_circle(Y_H, z, RK, x0, x1))


def bore(i, dia, blind_left=False):
    x0, x1 = seg_x(i)
    if blind_left:
        x0 += END_WALL
    return yz_circle(Y_H, Z_H, dia / 2, x0, x1)


# ---------------------------------------------------------------------------------------------
# Haken und Nut (gemeinsames Profil in y/z, global)
# ---------------------------------------------------------------------------------------------
def hook_profile():
    """Haken an der Zungeninnenseite. y = Zungeninnenseite (−LID_CLR) … Spitze; z global, Zungenende = Z_RIM+TONGUE_Z0."""
    z0 = Z_RIM + TONGUE_Z0
    y_in = -LID_CLR
    y_tip = y_in + HOOK_H
    return [(y_in, z0), (y_tip, z0 + HOOK_H), (y_tip, z0 + HOOK_H + HOOK_TIP), (y_in, z0 + 2 * HOOK_H + HOOK_TIP)]


def groove_profile():
    pts = hook_profile()
    ext = [(-3.0, pts[0][1]), (pts[0][0], pts[0][1]), pts[1], pts[2], pts[3], (-3.0, pts[3][1])]
    return ext


# ---------------------------------------------------------------------------------------------
# Basis
# ---------------------------------------------------------------------------------------------
def basis():
    b = rr(W_B, D_B, R_OUT, 0, Z_RIM)
    b = b.faces("<Z").edges().chamfer(1.5)
    try:
        b = b.edges(cq.selectors.BoxSelector((-200, -50, 1.4), (200, 200, 1.6))).fillet(2.5)
    except Exception:
        pass
    b = b.cut(rr(W_I, D_I, R_IN, BASE_FLOOR, Z_RIM + 1))
    # Oberkante verrunden
    try:
        b = b.faces(">Z").edges().fillet(0.6)
    except Exception:
        pass
    # Nut für den Haken (außen, vorn Mitte), Vorspannung: Nut liegt PRELOAD tiefer
    g = (cq.Workplane("YZ", origin=(-HOOK_W / 2 - GROOVE_CLR, 0, 0)).polyline(groove_profile()).close()
         .offset2D(GROOVE_CLR, "intersection").extrude(HOOK_W + 2 * GROOVE_CLR)).translate((0, 0, -PRELOAD))
    b = b.cut(g)
    # Scharnierknöchel
    for i in (0, 2, 4):
        b = b.union(base_knuckle(i))
    for i in (0, 2, 4):
        b = b.cut(bore(i, BORE_BASE, blind_left=(i == 0)))
    # Bandösen
    for sgn in (-1, 1):
        b = b.union(lug(sgn))
    return b


def lug(sgn):
    wall = W_B / 2
    xo = wall + LUG_OUT
    R = LUG_R
    zl = LUG_Z
    k = R * math.sqrt(0.5)
    zw = zl - 2 * k - LUG_OUT
    pts = [(wall - 1.0, zl + R), (xo, zl + R), (xo, zl), (xo + k, zl - k), (wall, zw), (wall - 1.0, zw)]
    prof = (cq.Workplane("XZ", origin=(0, YC + LUG_T / 2, 0)).polyline(pts).close().extrude(LUG_T))
    prof = prof.union(cq.Workplane("XZ", origin=(0, YC + LUG_T / 2, 0)).center(xo, zl).circle(R).extrude(LUG_T))
    try:
        prof = prof.faces(">Y or <Y").edges().fillet(2.0)
    except Exception:
        pass
    r = LUG_HOLE / 2
    t = r * math.sqrt(0.5)
    hole = (cq.Workplane("XZ", origin=(0, YC + LUG_T, 0)).polyline([(xo - t, zl + t), (xo, zl + r * math.sqrt(2)), (xo + t, zl + t), (xo, zl)]).close().extrude(2 * LUG_T)
            .union(cq.Workplane("XZ", origin=(0, YC + LUG_T, 0)).center(xo, zl).circle(r).extrude(2 * LUG_T)))
    prof = prof.cut(hole)
    if sgn < 0:
        prof = prof.mirror("YZ")
    return prof


# ---------------------------------------------------------------------------------------------
# Deckel
# ---------------------------------------------------------------------------------------------
def deckel(hook=True):
    zb = -SKIRT + Z_RIM
    z_top = Z_RIM + LID_TOP
    lid = rr(W_L, D_L, R_L, zb, z_top)
    # Dachkante (liegt beim Druck auf dem Bett): 45°-Fase, darüber Verrundung → druckt ohne Überhang
    lid = lid.faces(">Z").edges().chamfer(ROOF_CH)
    lid = lid.edges(cq.selectors.BoxSelector((-300, -100, z_top - ROOF_CH - 0.1), (300, 300, z_top - ROOF_CH + 0.1))).fillet(ROOF_R1)
    lid = lid.edges(cq.selectors.BoxSelector((-300, -100, z_top - 0.1), (300, 300, z_top + 0.1))).fillet(ROOF_R2)
    # Innenraum: Haut (um die Basis +LID_CLR), Sitzleiste mit Anlauf, Kartenraum
    o1w, o1d, o1r = W_B + 2 * LID_CLR, D_B + 2 * LID_CLR, R_OUT + LID_CLR
    o2w, o2d, o2r = W_I + 2 * SEAT_IN, D_I + 2 * SEAT_IN, R_IN + SEAT_IN
    cav = rr(o1w, o1d, o1r, zb - 1, Z_RIM)
    cav = cav.union(loft_rr(o2w, o2d, o2r, Z_RIM, o1w, o1d, o1r, Z_RIM + SEAT_H))
    cav = cav.union(rr(o1w, o1d, o1r, Z_RIM + SEAT_H - 0.01, Z_RIM + LID_CAV))
    lid = lid.cut(cav)
    # Haut hinten wegnehmen (Schwenk): ab Beginn der Rückecken, 45°-Auslauf
    y_a = D_B - R_OUT - SKIRT
    cut = (cq.Workplane("YZ", origin=(-200, 0, 0)).polyline([(y_a, zb - 2), (y_a, zb), (y_a + SKIRT, Z_RIM), (D_L + 40, Z_RIM), (D_L + 40, zb - 2)])
           .close().extrude(400))
    lid = lid.cut(cut)
    # Zunge (verlängerte Vorderwand) mit Lasche und Haken
    wo = LID_OVER
    z_end = Z_RIM + TONGUE_Z0
    tongue = box(-TW / 2, TW / 2, -wo, -LID_CLR, z_end, zb + 0.5)
    lid = lid.union(tongue)
    if hook:
        hk = (cq.Workplane("YZ", origin=(-HOOK_W / 2, 0, 0)).polyline(hook_profile()).close().extrude(HOOK_W))
        lid = lid.union(hk)
    tab = (cq.Workplane("YZ", origin=(-TAB_W / 2, 0, 0))
           .polyline([(-wo + 0.01, z_end + TAB_OUT + 3.0), (-wo - TAB_OUT, z_end + 3.0), (-wo - TAB_OUT, z_end), (-wo + 0.01, z_end)]).close().extrude(TAB_W))
    try:
        tab = tab.edges("|Z").fillet(3.0)
    except Exception:
        pass
    lid = lid.union(tab)
    for s in (-1, 1):
        x0 = s * (TW / 2) if s > 0 else -(TW / 2 + SLIT)
        lid = lid.cut(box(x0, x0 + SLIT, -wo - 6, -LID_CLR + 0.0, z_end - 1, Z_RIM + 4.0))
    # Scharnierknöchel
    for i in (1, 3):
        lid = lid.union(lid_knuckle(i))
    for i in (1, 3):
        lid = lid.cut(bore(i, BORE_LID))
    return lid


# ---------------------------------------------------------------------------------------------
# Inlay (beige)
# ---------------------------------------------------------------------------------------------
def inlay():
    z0 = BASE_FLOOR
    z1 = BASE_FLOOR + LINER_H
    r_o = R_IN - LINER_CLR
    o = rr(LINER_X, LINER_Y, r_o, z0, z1)
    o = o.faces("<Z").edges().chamfer(0.6)
    ix, iy = LINER_X - 2 * DIV, LINER_Y - 2 * DIV
    o = o.cut(rr(ix, iy, LINER_R_IN, z0 + LINER_FLOOR, z1 + 1))
    # Trennwände
    for k in range(1, NC):
        xc = -LINER_X / 2 + DIV + k * SLOT_W + (k - 0.5) * DIV
        o = o.union(box(xc - DIV / 2, xc + DIV / 2, YC - iy / 2 - 0.5, YC + iy / 2 + 0.5, z0 + LINER_FLOOR - 0.01, z1))
    # Schwung: Oberkante fällt nach vorn ab (Kreis um Achse parallel zu x)
    y_front = YC - LINER_Y / 2
    z_front = z1 - 20.0
    y_full = y_front + 55.0
    # Kreis durch (y_front, z_front) mit tiefstem Punkt bei y_front und (y_full, z1)
    dz = z1 - z_front
    dy = y_full - y_front
    Rs = (dy * dy + dz * dz) / (2 * dz)
    sw = (cq.Workplane("YZ", origin=(-LINER_X, 0, 0)).center(y_front, z_front + Rs).circle(Rs).extrude(2 * LINER_X))
    o = o.cut(sw)
    # Oberkanten verrunden (weich, kindgerecht); schlägt es fehl, bleibt die Kante scharf
    try:
        o = o.edges(cq.selectors.BoxSelector((-200, -10, z_front - 1.0), (200, 200, z1 + 1.0))).fillet(0.8)
    except Exception:
        pass
    return o


def pin():
    x0 = -LH / 2 + END_WALL
    return yz_circle(Y_H, Z_H, PIN_D / 2, x0, x0 + 90.0)


if __name__ == "__main__":
    for n, f in (("basis", basis), ("deckel", deckel), ("inlay", inlay)):
        s = f()
        v = s.val()
        bb = v.BoundingBox()
        print(n, "gültig", v.isValid(), "Vol cm3", round(v.Volume() / 1000, 1), "BB", round(bb.xmin, 1), round(bb.xmax, 1), round(bb.ymin, 1), round(bb.ymax, 1), round(bb.zmin, 1), round(bb.zmax, 1))
