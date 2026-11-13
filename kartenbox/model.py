"""Kartenbox v2 für 30 Peppa-Box-Karten – parametrisches Modell (manifold3d).

Koordinaten: x nach rechts, y nach hinten (Vorderseite bei y = -D_O/2), z nach oben, z = 0 Standfläche.
Box geschlossen in Einbaulage. Alle Maße in mm. Jede Größe trägt einen Status:
  belegt      – aus Datenblatt / Repository (Karte aus v4/out/10_karte_orange.stl)
  festgelegt  – Entwurfsentscheidung
  berechnet   – folgt aus anderen Größen
  Probedruck  – Startwert, wird am Coupon K1/K2 bestätigt oder geändert
"""
import math
import numpy as np
from manifold3d import Manifold, Mesh, CrossSection

P_ = {}


def par(name, val, status, note):
    P_[name] = (val, status, note)
    return val


# ----------------------------------------------------------------------------- Karte
CARD_W = par("CARD_W", 70.0, "belegt", "Karte Breite (v4/model.py, STL gemessen)")
CARD_H = par("CARD_H", 112.0, "belegt", "Karte Höhe")
CARD_T = par("CARD_T", 4.0, "belegt", "Karte Dicke")
N_PER = par("N_PER", 10, "festgelegt", "Karten je Fach (3 Fächer = 30)")
LEAN = par("LEAN", 15.0, "festgelegt", "Karten lehnen um diesen Winkel nach hinten an der Stütze (Cover zeigt schräg nach oben zum Kind, Box wird tiefer und standfester)")

# ----------------------------------------------------------------------------- Wände, Spiele
T = par("T", 2.5, "festgelegt", "Wand Basis/Deckel = 6 Linien à 0,42 mm (Slicer: 6 Wandschleifen)")
IW = par("IW", 1.68, "festgelegt", "Inlay-Wände und Trennwände = 4 Linien")
IF = par("IF", 1.6, "festgelegt", "Inlay-Boden (8 Schichten à 0,2)")
G_I = par("G_I", 0.3, "Probedruck", "Spiel Inlay ↔ Basis/Deckel je Seite")
CMP_W = par("CMP_W", 75.0, "festgelegt", "Fach innen quer (Karte 70 + 2,5 je Seite)")
FS = par("FS", 14.0, "festgelegt", "freier Raum vor dem Stapel am Fachboden (Blättern, Greifen)")
BACK_CLR = par("BACK_CLR", 6.5, "festgelegt", "Luft hinter der obersten Kartenkante zur Rückwand (Ecken-Rundung im Deckel)")
TOP_CLR = par("TOP_CLR", 2.0, "festgelegt", "Mindestluft über einer senkrecht stehenden Karte unter der Deckeldecke")
FRONT_STRIP = par("FRONT_STRIP", 5.0, "festgelegt", "senkrechte Karte muss überall passen, außer in diesem Streifen direkt an der Fachwand vorn (dort drückt der schließende Deckel sie nach hinten; Stapel lehnt sowieso hinten)")

# ----------------------------------------------------------------------------- Außenform
R0 = par("R0", 15.0, "festgelegt", "Eckradius im Grundriss außen (innen R0 - T, konzentrisch)")
RB = par("RB", 12.0, "festgelegt", "Rundung unten außen; unterhalb 45° als Fase (druckbar ohne Stützen); innen konzentrisch RB - T")
RT = par("RT", 16.0, "festgelegt", "Rundung oben am Deckel außen; Deckel liegt kopfüber, daher ebenfalls 45°-begrenzt; innen RT - T")
BY = par("BY", 2.5, "festgelegt", "Wölbung der langen Seiten (vorn/hinten) in der Mitte nach außen – weicher, kissenartiger Grundriss")
BX = par("BX", 1.5, "festgelegt", "Wölbung der Stirnseiten (links/rechts) in der Mitte nach außen")
GROOVE = par("GROOVE", 0.8, "festgelegt", "V-Fuge an der Teilungsebene, je Seite 45°")
CH_ANG = par("CH_ANG", 42.0, "festgelegt", "Rundungen unten/oben gehen ab diesem Winkel (gegen die Senkrechte) in eine Fase über; < 45°, damit auch nach der Wölbung kein Überhang > 45° entsteht")
P = par("P", 78.0, "festgelegt", "Teilungsebene Basis/Deckel (Höhe)")
LIP = par("LIP", 5.0, "festgelegt", "Inlay-Rand ragt so weit über P in den Deckel (Führung, beiger Rand)")

# ----------------------------------------------------------------------------- abgeleitete Größen
TAN = math.tan(math.radians(LEAN))
COS = math.cos(math.radians(LEAN))
SIN = math.sin(math.radians(LEAN))
Z_F = T + IF                                                  # Fachboden (Karte steht hier)
STACK = N_PER * CARD_T / COS                                  # Stapel am Boden, waagerecht gemessen
X_IN = (3 * CMP_W + 2 * IW) / 2                               # halbe Innenbreite des Inlays
W_O = 2 * (X_IN + IW + G_I + T)
Y_CF0 = G_I + IW + FS + STACK                                  # vordere Hohlraumwand -> Stützebene am Boden
CARD_TOP_BACK = CARD_H * SIN                                   # oberste Kartenkante hinter der Stützebene
D_C = Y_CF0 + CARD_TOP_BACK + BACK_CLR
D_O = D_C + 2 * T
Y_CF = -D_O / 2 + T                                            # Hohlraum vorne (ungewölbt; in der Mitte BY weiter vorn)
Y_CB = D_O / 2 - T                                             # Hohlraum hinten (ungewölbt)
Y_FI = Y_CF + G_I + IW                                         # Fach-Vorderwand innen
Y_S0 = Y_CF + Y_CF0                                            # Stützebene auf Höhe Z_F
def _round(d, R, off=0.0):
    """Einzug einer Rundung R, die ab CH_ANG (gegen die Senkrechte) als gerade Fase zur Fläche läuft.
    d = Abstand von der Fläche (Boden bzw. Dach außen). off = Versatz nach innen (Innenfläche: T)."""
    a = math.radians(CH_ANG)
    r = R - off
    ua, da = R - r * math.cos(a), R - r * math.sin(a)      # Übergang Bogen/Fase
    if d >= R:
        return off
    if d >= da:
        return R - math.sqrt(max(r * r - (R - d) ** 2, 0.0))
    return ua + (da - d) * math.tan(a)


def _cav_round(d, R):
    """Einzug der Innenfläche (konzentrisch, um T nach innen versetzt)."""
    return _round(d, R, T)


def _min_H():
    """kleinste Höhe: senkrechte Karte passt unter die Innenrundung der Decke – vorn ab FRONT_STRIP hinter der
    Fachwand, an den Stirnseiten in mittiger Lage (seitliche Luft (CMP_W - CARD_W)/2)."""
    top = Z_F + CARD_H
    allow = min(G_I + IW + FRONT_STRIP, G_I + IW + (CMP_W - CARD_W) / 2) - 0.3
    h = top + TOP_CLR + T
    while _cav_round(h - top, RT) - T > allow:
        h += 0.1
    return round(h, 1)


H = _min_H()
CEIL = H - T                                                   # Deckeldecke innen
Z_LIP = P + LIP

P_["W_O"] = (W_O, "berechnet", "Breite außen ohne Ösen")
P_["D_O"] = (D_O, "berechnet", "Tiefe außen ohne Scharnier")
P_["H"] = (H, "berechnet", "Höhe außen")

# ----------------------------------------------------------------------------- Verschluss
TW = par("TW", 30.0, "festgelegt", "Breite der Rastzunge im Deckel vorne")
SLOT = par("SLOT", 1.0, "festgelegt", "Schlitz neben der Zunge")
T_TONGUE = par("T_TONGUE", 2.0, "festgelegt", "Zungendicke (Deckelwand innen 0,5 mm freigestellt)")
Z_ROOT = par("Z_ROOT", P + 18.0, "festgelegt", "Zungenwurzel (Schlitzende oben)")
Z_TIP = par("Z_TIP", P - 11.0, "festgelegt", "Zungenende unten (ragt in die Mulde der Basis)")
HOOK = par("HOOK", 1.2, "festgelegt", "Haken ragt so weit innen aus der Zunge")
HOOK_Z = par("HOOK_Z", P - 8.0, "festgelegt", "Unterkante der Haltefläche am Hakenende")
HOLD_ANG = par("HOLD_ANG", 60.0, "Probedruck", "Haltefläche gegen die Zugrichtung (senkrecht): 90° = hält starr, kleiner = lässt sich mit Gewalt aufziehen; 60° = 30° zur Waagerechten, im Druck kurzer Überhang 1 mm")
LEAD_ANG = par("LEAD_ANG", 30.0, "festgelegt", "Einlaufschräge gegen die Senkrechte (leichtes Schließen)")
REC_GAP = par("REC_GAP", 0.4, "Probedruck", "Luft zwischen Zungen-Innenseite und Mulde")
REC_SIDE = par("REC_SIDE", 0.6, "festgelegt", "seitliche Luft Zunge ↔ Mulde")
GROOVE_D = par("GROOVE_D", 1.0, "festgelegt", "Tiefe der Rastnut in der Mulde")
PLAY_V = par("PLAY_V", 0.2, "festgelegt", "senkrechtes Spiel Haken ↔ Nut (Deckel liegt auf, nicht auf dem Haken)")
LIP_OUT = par("LIP_OUT", 1.2, "festgelegt", "Griffnase außen am Zungenende")
BOSS_T = par("BOSS_T", 5.4, "festgelegt", "Wand der Basis hinter der Mulde, gesamt")
BOSS_W = par("BOSS_W", 20.0, "festgelegt", "halbe Breite der Verstärkung innen")

# ----------------------------------------------------------------------------- Scharnier
PX = par("PX", 70.0, "festgelegt", "Mitte der beiden Scharniere (±)")
E_AX = par("E_AX", 6.0, "festgelegt", "Achse so weit hinter der Rückwand (auf Höhe P)")
R_K = par("R_K", 5.0, "festgelegt", "Knöchelradius")
KB_L = par("KB_L", 9.0, "festgelegt", "Länge Basisknöchel")
KL_L = par("KL_L", 14.0, "festgelegt", "Länge Deckelknöchel")
K_GAP = par("K_GAP", 0.5, "festgelegt", "Axialspiel zwischen den Knöcheln")
PIN_D = par("PIN_D", 4.0, "festgelegt", "Stift Ø (gedruckt, liegend)")
HOLE_SLIP = par("HOLE_SLIP", 4.15, "Probedruck", "Bohrung äußerer Basisknöchel (Stift schiebt sich durch)")
HOLE_PRESS = par("HOLE_PRESS", 3.9, "Probedruck", "Bohrung innerer Basisknöchel (Stift klemmt)")
HOLE_LID = par("HOLE_LID", 4.6, "Probedruck", "Bohrung Deckelknöchel (dreht frei)")
HEAD_D = par("HEAD_D", 6.4, "festgelegt", "Stiftkopf Ø (Senkung 7,0; Tropfenspitze bleibt im Knöchel R 5)")
HEAD_T = par("HEAD_T", 1.6, "festgelegt", "Stiftkopf Dicke")
TAIL_DIR = par("TAIL_DIR", 61.0, "festgelegt", "Anschlagnase am Deckelknöchel: Richtung (Grad von senkrecht nach unten Richtung hinten)")
TAIL_R = par("TAIL_R", 2.5, "festgelegt", "Anschlagnase Radius")
TAIL_E = par("TAIL_E", 6.0, "festgelegt", "Anschlagnase Abstand zur Achse")

Y_BACK_PX = D_O / 2 + BY * (1 - (PX / (W_O / 2)) ** 2)   # Rückwand außen in Scharniermitte
Y_H = Y_BACK_PX + E_AX
Z_H = P
POD = 2 * KB_L + KL_L + 2 * K_GAP

# ----------------------------------------------------------------------------- Bandösen
EAR_Z = par("EAR_Z", P - 24.0, "festgelegt", "Höhe der Bandöse (Mitte)")
EAR_OUT = par("EAR_OUT", 12.0, "festgelegt", "Öse steht so weit seitlich vor")
EAR_HOLE = par("EAR_HOLE", 5.2, "festgelegt", "senkrechtes Loch Ø für Kordel bis 4 mm (z. B. Paracord)")
EAR_HX = par("EAR_HX", 5.6, "festgelegt", "Lochmitte so weit von der Seitenwand")

# ----------------------------------------------------------------------------- Inlay-Mulden vorne
SCOOP_Z = par("SCOOP_Z", 52.0, "festgelegt", "tiefster Punkt der Griffmulde in der Fach-Vorderwand")
SCOOP_FLAT = par("SCOOP_FLAT", 21.0, "festgelegt", "halbe Breite des flachen Muldengrunds")
SCOOP_RISE = par("SCOOP_RISE", 13.5, "festgelegt", "Breite des Bogens bis zum Rand")

SEG = 18  # Segmente je Viertelkreis


# ============================================================================= Grundformen
def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_x(x0, x1, y, z, r, seg=48):
    return Manifold.cylinder(x1 - x0, r, r, seg).rotate([0, 90, 0]).translate([x0, y, z])


def cyl_z(x, y, z0, z1, r, seg=48):
    return Manifold.cylinder(z1 - z0, r, r, seg).translate([x, y, z0])


def teardrop_x(x0, x1, y, z, d, up=True, seg=48):
    """Bohrung entlang x mit 45°-Spitze nach oben (up) bzw. unten: druckbar ohne Stützen."""
    r = d / 2
    c = Manifold.cylinder(x1 - x0, r, r, seg).rotate([0, 90, 0])
    sq = Manifold.cube([x1 - x0, r, r]).rotate([45, 0, 0])      # Raute: Ecken (0,0), (±r/√2, r/√2), (0, r√2)
    if not up:
        sq = sq.mirror([0, 0, 1])
    return (c + sq).translate([x0, y, z])


def rr_ring(hx, hy, r, n=SEG, step=4.0):
    """Ring eines Rechtecks mit gerundeten Ecken, gegen den Uhrzeigersinn. Punktzahl hängt nur von
    hx - r und hy - r ab (bei konzentrischen Ringen gleich), Geraden sind unterteilt (für die Wölbung)."""
    r = max(r, 0.2)
    ax, ay = hx - r, hy - r
    nx, ny = max(1, round(2 * ax / step)), max(1, round(2 * ay / step))
    pts = []
    corners = ((ax, ay, 0), (-ax, ay, 90), (-ax, -ay, 180), (ax, -ay, 270))
    for k, (cx, cy, a0) in enumerate(corners):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        nxt = corners[(k + 1) % 4]
        p0 = pts[-1]
        a1 = math.radians(nxt[2])
        p1 = (nxt[0] + r * math.cos(a1), nxt[1] + r * math.sin(a1))
        m = nx if k in (0, 2) else ny
        for i in range(1, m):
            t = i / m
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    return pts


def bulge_xy(x, y):
    """Verschiebung (dx, dy) der Wölbung an der Stelle (x, y) – gilt für Außenhaut, Innenraum und Inlay gleich."""
    X0, Y0 = W_O / 2, D_O / 2
    dy = BY * (1 - (x / X0) ** 2) * (y / Y0)
    dx = BX * (1 - (y / Y0) ** 2) * (x / X0)
    return dx, dy


def bulge(m, inlay=False):
    """Wölbung anwenden. Beim Inlay bleibt das Innere in x gerade (Trennwände senkrecht, Fächer gleich breit):
    die x-Wölbung greift nur an den Stirnwänden (weicher Übergang ab |x| = X_IN - 20)."""
    def f(V):
        V = np.array(V, dtype=np.float64)
        dx, dy = bulge_xy(V[:, 0], V[:, 1])
        if inlay:
            t = np.clip((np.abs(V[:, 0]) - (X_IN - 20)) / 20.0, 0, 1)
            dx = dx * t * t * (3 - 2 * t)
        V[:, 0] += dx
        V[:, 1] += dy
        return V
    return m.warp_batch(f)


def loft(zs, insets, hx=None, hy=None, r=None, warp=True):
    """Körper aus waagerechten Ringen: Grundriss = Außenrechteck (W_O, D_O, R0) um 'inset' verkleinert."""
    hx = W_O / 2 if hx is None else hx
    hy = D_O / 2 if hy is None else hy
    r = R0 if r is None else r
    rings = [rr_ring(hx - i, hy - i, r - i) for i in insets]
    n = len(rings[0])
    V = []
    for z, ring in zip(zs, rings):
        V += [(x, y, z) for x, y in ring]
    V.append((0, 0, zs[0]))
    V.append((0, 0, zs[-1]))
    b, t = len(V) - 2, len(V) - 1
    F = []
    for k in range(len(zs) - 1):
        o0, o1 = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            F.append((o0 + i, o0 + j, o1 + j))
            F.append((o0 + i, o1 + j, o1 + i))
    last = (len(zs) - 1) * n
    for i in range(n):
        j = (i + 1) % n
        F.append((b, j, i))
        F.append((t, last + i, last + j))
    m = Manifold(Mesh(vert_properties=np.array(V, dtype=np.float32), tri_verts=np.array(F, dtype=np.uint32)))
    assert m.status().name == "NoError", m.status()
    return bulge(m) if warp else m


# ============================================================================= Profile (inset über z)
def inset_outer(z):
    v = max(_round(z, RB), _round(H - z, RT))
    v += max(0.0, GROOVE - abs(z - P))
    return v


def inset_cavity(z):
    """Innenfläche = Außenfläche um T nach innen versetzt (ohne V-Fuge)."""
    return max(_cav_round(z, RB), _cav_round(H - z, RT))


def zs_between(z0, z1, extra=()):
    pts = set([z0, z1])
    step = 0.4
    z = z0
    while z < z1:
        pts.add(round(z, 4))
        z += step
    for e in extra:
        if z0 <= e <= z1:
            pts.add(e)
    return sorted(pts)


def zs_outer(z0, z1):
    a = math.radians(CH_ANG)
    keys = [P - GROOVE, P, P + GROOVE, RB * (1 - math.sin(a)), H - RT * (1 - math.sin(a))]
    pts = [z for z in zs_between(z0, z1, keys)
           if z <= RB + 0.5 or z >= H - RT - 0.5 or abs(z - P) <= GROOVE + 0.5 or z in (z0, z1) or abs(z / 6 - round(z / 6)) < 0.05]
    return sorted(set(pts))


def outer_body(z0, z1, extra=0.0):
    zs = zs_outer(z0, z1)
    return loft(zs, [inset_outer(z) + extra for z in zs])


def cavity_body(z0, z1, extra=0.0):
    keys = [T, RB, H - RT, CEIL]
    zs = [z for z in zs_between(z0, z1, keys) if z <= RB + 0.5 or z >= H - RT - 0.5 or z in (z0, z1)]
    zs = sorted(set(zs))
    return loft(zs, [inset_cavity(z) + extra for z in zs])


# ============================================================================= Scharnier
def _knuckle(x0, x1, r, ch=0.6):
    """Zylinder entlang x mit gefasten Enden."""
    a = cyl_x(x0 + ch, x1 - ch, Y_H, Z_H, r, 64)
    b = cyl_x(x0, x1, Y_H, Z_H, r - ch, 64)
    return Manifold.batch_hull([a, b])


def pod_ranges(side):
    """x-Bereiche (Basis außen, Deckel, Basis innen) eines Scharniers; side = +1 rechts, -1 links."""
    c = side * PX
    a = (c - POD / 2, c - POD / 2 + KB_L)
    m = (c - KL_L / 2, c + KL_L / 2)
    b = (c + POD / 2 - KB_L, c + POD / 2)
    return (b, m, a) if side > 0 else (a, m, b)   # (außen, Deckel, innen)


def base_knuckles():
    parts = []
    for side in (1, -1):
        outer, _, inner = pod_ranges(side)
        for k, (x0, x1) in enumerate((outer, inner)):
            web = Manifold.batch_hull([cyl_x(x0 + 0.6, x1 - 0.6, Y_BACK_PX - 2.6, P - 12.5, 2.4, 40),
                                       cyl_x(x0, x1, Y_BACK_PX - 2.6, P - 12.5, 1.8, 40)])
            parts.append(Manifold.batch_hull([_knuckle(x0, x1, R_K), web]))
    return Manifold.batch_boolean(parts, manifold3d_op("add"))


def base_knuckle_holes():
    cut = []
    for side in (1, -1):
        outer, _, inner = pod_ranges(side)
        cut.append(teardrop_x(min(outer) - 1, max(outer) + 1, Y_H, Z_H, HOLE_SLIP, up=True))
        cut.append(teardrop_x(min(inner) - 1, max(inner) + 1, Y_H, Z_H, HOLE_PRESS, up=True))
        # Senkung für den Stiftkopf an der Außenseite
        xo = outer[1] if side > 0 else outer[0]
        d = HEAD_T + 0.2
        x0, x1 = (xo - d, xo + 1) if side > 0 else (xo - 1, xo + d)
        cut.append(teardrop_x(x0, x1, Y_H, Z_H, HEAD_D + 0.6, up=True))
    return Manifold.batch_boolean(cut, manifold3d_op("add"))


def tail_center():
    a = math.radians(TAIL_DIR)
    return Y_H + TAIL_E * math.sin(a), Z_H - TAIL_E * math.cos(a)


def lid_knuckles():
    parts = []
    ty, tz = tail_center()
    for side in (1, -1):
        _, (x0, x1), _ = pod_ranges(side)
        web = Manifold.batch_hull([cyl_x(x0 + 0.6, x1 - 0.6, Y_BACK_PX - 2.6, P + 12.5, 2.4, 40),
                                   cyl_x(x0, x1, Y_BACK_PX - 2.6, P + 12.5, 1.8, 40)])
        tail = Manifold.batch_hull([cyl_x(x0 + 0.6, x1 - 0.6, ty, tz, TAIL_R, 32), cyl_x(x0, x1, ty, tz, TAIL_R - 0.6, 32)])
        parts.append(Manifold.batch_hull([_knuckle(x0, x1, R_K), web, tail]))
    return Manifold.batch_boolean(parts, manifold3d_op("add"))


def lid_knuckle_holes():
    cut = []
    for side in (1, -1):
        _, (x0, x1), _ = pod_ranges(side)
        cut.append(teardrop_x(x0 - 1, x1 + 1, Y_H, Z_H, HOLE_LID, up=False))   # Deckel liegt kopfüber: Spitze im Druck oben
    return Manifold.batch_boolean(cut, manifold3d_op("add"))


def pin(d=None):
    """Scharnierstift in Einbaulage für das rechte Scharnier (Kopf außen rechts)."""
    outer, _, inner = pod_ranges(1)
    x_head = outer[1]
    x_end = inner[0] + 0.3
    r = (PIN_D if d is None else d) / 2
    shaft = cyl_x(x_end + 0.5, x_head - HEAD_T, Y_H, Z_H, r, 48)
    tip = Manifold.batch_hull([cyl_x(x_end, x_end + 0.5, Y_H, Z_H, r - 0.5, 48), cyl_x(x_end + 0.5, x_end + 0.6, Y_H, Z_H, r, 48)])
    head = cyl_x(x_head - HEAD_T, x_head, Y_H, Z_H, HEAD_D / 2, 48)
    p = shaft + tip + head
    flat = box(x_end - 1, Y_H - 10, Z_H - 10, x_head + 1, Y_H + 10, Z_H - r + 0.3)   # Druckfläche (D-Form)
    return p - flat


def manifold3d_op(name):
    import manifold3d
    return {"add": manifold3d.OpType.Add, "sub": manifold3d.OpType.Subtract, "int": manifold3d.OpType.Intersect}[name]


# ============================================================================= Verschluss
def _ccw(pts):
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts if a > 0 else pts[::-1]


def _yz_prism(pts_yz, x0, x1):
    """Prisma entlang x aus einem Polygon in der y-z-Ebene."""
    cs = CrossSection([_ccw(list(pts_yz))])
    m = Manifold.extrude(cs, x1 - x0)          # Polygon (y,z) in XY, Extrusion entlang z
    # (u,v,w) -> (x=w, y=u, z=v)
    m = m.transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32))
    return m


def _xz_prism(pts_xz, y0, y1):
    cs = CrossSection([_ccw(list(pts_xz))])
    m = Manifold.extrude(cs, y1 - y0)
    m = m.transform(np.array([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0]], dtype=np.float32))   # y = y1 - w (keine Spiegelung)
    return m


Y_OUT_F = -D_O / 2 - BY                  # Außenfläche vorne in der Mitte (im Bereich der Zunge praktisch flach)
Y_TI = Y_OUT_F + T_TONGUE                # Zunge innen
Y_RB = Y_TI + REC_GAP                    # Muldenrückwand
TH = 1.0 / math.tan(math.radians(HOLD_ANG))     # Anstieg der Haltefläche je mm Hakentiefe


def hook_profile():
    """Haken an der Zungeninnenseite (y-z), geschlossene Lage."""
    yi, h = Y_TI, HOOK
    z_lead0 = HOOK_Z - 2.5
    z_lead1 = z_lead0 + h / math.tan(math.radians(LEAD_ANG))
    return [(yi - 0.01, z_lead0), (yi + h, z_lead1), (yi + h, HOOK_Z), (yi - 0.01, HOOK_Z + h * TH)]


def groove_profile():
    """Rastnut in der Muldenrückwand der Basis (y-z)."""
    yb, d = Y_RB, GROOVE_D
    # Haltefläche parallel zur Hakenfläche, PLAY_V darüber
    def z_hold(y):
        return HOOK_Z + PLAY_V + (Y_TI + HOOK - y) * TH
    zb_top = HOOK_Z - 2.5            # Unterkante innen
    return [(yb - 0.5, HOOK_Z - 3.5 - 0.5), (yb + d, zb_top), (yb + d, z_hold(yb + d)), (yb - 0.5, z_hold(yb - 0.5))]


def tongue():
    """Zunge unterhalb der Teilungsebene (oberhalb ist sie Teil der Deckelwand) + Haken + Griffnase."""
    x0, x1 = -TW / 2, TW / 2
    lower = box(x0, Y_OUT_F, Z_TIP + 1.0, x1, Y_TI, P + GROOVE + 0.5)
    tipr = Manifold.batch_hull([box(x0, Y_OUT_F + 0.5, Z_TIP, x1, Y_TI, Z_TIP + 1.0), box(x0, Y_OUT_F, Z_TIP + 1.0, x1, Y_TI, Z_TIP + 1.01)])
    hook = _yz_prism(hook_profile(), x0 + 1.0, x1 - 1.0)
    # Griffnase: Oberseite 45° (im Kopfüber-Druck Unterseite), außen senkrecht, unten gerundet
    zt = Z_TIP
    nose = _yz_prism([(Y_OUT_F + 0.01, zt + 0.6), (Y_OUT_F - LIP_OUT + 0.4, zt), (Y_OUT_F - LIP_OUT, zt + 0.6),
                      (Y_OUT_F - LIP_OUT, zt + 3.3), (Y_OUT_F + 0.01, zt + 3.3 + LIP_OUT)], x0 + 2, x1 - 2)
    return lower + tipr + hook + nose


def lid_tongue_cuts():
    """Schlitze links/rechts der Zunge und Freistellung innen (Zunge 2,0 statt 2,5 mm)."""
    cuts = []
    for s in (-1, 1):
        xa = s * TW / 2
        xb = s * (TW / 2 + SLOT)
        x0, x1 = min(xa, xb), max(xa, xb)
        cuts.append(box(x0, Y_OUT_F - 2, P - 2, x1, Y_OUT_F + T + 1.5, Z_ROOT - SLOT / 2))
        cuts.append(Manifold.cylinder(T + 3.5, SLOT / 2, SLOT / 2, 24).rotate([-90, 0, 0]).translate([(x0 + x1) / 2, Y_OUT_F - 2, Z_ROOT - SLOT / 2]))
    cuts.append(box(-TW / 2 - 0.01, Y_TI, P - 2, TW / 2 + 0.01, Y_OUT_F + T + 1, Z_ROOT - 3))
    # unter der Zunge darf nichts vom Deckel bleiben (V-Fuge)
    cuts.append(box(-TW / 2 - SLOT, Y_OUT_F - 2, P - 5, TW / 2 + SLOT, Y_OUT_F + T + 1, P + GROOVE + 0.5))
    return Manifold.batch_boolean(cuts, manifold3d_op("add"))


def base_latch_add():
    """Verstärkung innen hinter der Mulde (Unterseite 45°)."""
    yw = Y_OUT_F + T                     # Innenfläche der gewölbten Vorderwand in der Mitte
    a = box(-BOSS_W, yw - 1.0, P - 20.0, BOSS_W, Y_OUT_F + BOSS_T, P)
    b = box(-BOSS_W, yw - 1.0, P - 23.0, BOSS_W, yw + 0.1, P)
    a2 = box(-BOSS_W - 2.0, yw - 1.0, P - 20.0, -BOSS_W, yw + 0.1, P)
    b2 = box(BOSS_W, yw - 1.0, P - 20.0, BOSS_W + 2.0, yw + 0.1, P)
    return Manifold.batch_hull([a, b, a2, b2])


def base_latch_cut():
    xr = TW / 2 + REC_SIDE
    rec = box(-xr, Y_OUT_F - 3, Z_TIP - 1.0, xr, Y_RB, P + 2)
    # Einführfase oben an der Muldenrückwand
    ch = _yz_prism([(Y_RB - 0.01, P - 1.2), (Y_RB + 1.2, P + 0.01), (Y_RB + 1.2, P + 2), (Y_RB - 0.01, P + 2)], -xr, xr)
    gro = _yz_prism(groove_profile(), -xr, xr)
    # Fingermulde unter dem Zungenende
    dip = Manifold.sphere(1.0, 64).scale([13.0, 2.9, 8.0]).translate([0, Y_OUT_F - 0.5, Z_TIP - 1.0])
    return rec + ch + gro + dip


# ============================================================================= Bandösen
def ears():
    parts = []
    for s in (1, -1):
        xw = s * (W_O / 2 + BX)
        def sp(dx, y, z, r):
            return Manifold.sphere(r, 40).translate([xw + s * dx, y, z])
        hull = Manifold.batch_hull([sp(EAR_OUT - 5, y, EAR_Z + dz, 5) for y in (-6, 6) for dz in (-3, 3)] +
                                   [sp(-3, y, EAR_Z - 17, 3) for y in (-6, 6)] +
                                   [sp(-3, y, EAR_Z + 10, 3) for y in (-6, 6)])
        parts.append(hull)
    return Manifold.batch_boolean(parts, manifold3d_op("add"))


def ear_holes():
    cut = []
    for s in (1, -1):
        cut.append(cyl_z(s * (W_O / 2 + BX + EAR_HX), 0, EAR_Z - 25, EAR_Z + 25, EAR_HOLE / 2, 40))
    return Manifold.batch_boolean(cut, manifold3d_op("add"))


# ============================================================================= Teile
def base():
    cav = cavity_body(T, P + 1)
    shell = outer_body(0, P) - cav
    shell = shell + (base_latch_add() ^ outer_body(0, P)) + (base_knuckles() - cav - cavity_body(P - 1, CEIL)) + (ears() - cav)
    shell = shell - base_latch_cut() - base_knuckle_holes() - ear_holes()
    return shell


def lid():
    shell = outer_body(P, H) - cavity_body(P - 1, CEIL)
    shell = shell - lid_tongue_cuts()
    shell = shell + tongue() + (lid_knuckles() - cavity_body(P - 1, CEIL) - cavity_body(T, P + 1))
    shell = shell - lid_knuckle_holes()
    return shell


# ----------------------------------------------------------------------------- Inlay
def inlay_outer(extra=0.0, z1=None, warp=True):
    z1 = Z_LIP if z1 is None else z1
    keys = [T, RB]
    zs = [z for z in zs_between(T, z1, keys) if z <= RB + 0.5 or z in (T, z1)]
    zs = sorted(set(zs))
    return loft(zs, [inset_cavity(z) + G_I + extra for z in zs], warp=warp)


def support_y(z):
    """Vorderfläche der schrägen Kartenstütze."""
    return Y_S0 + (z - Z_F) * TAN


def scoop_cut(xc):
    pts = []
    zt = Z_LIP + 2
    a = SCOOP_RISE
    for i in range(0, 25):
        t = math.pi / 2 * i / 24
        pts.append((xc - SCOOP_FLAT - a * math.sin(t), SCOOP_Z + (zt - SCOOP_Z) * (1 - math.cos(t))))
    left = pts[::-1]
    right = [(2 * xc - x, z) for x, z in pts]
    poly = left + right
    return _xz_prism(poly, Y_CF - 1, Y_FI + 0.5)


def inlay():
    """Inlay ungewölbt aufbauen und als Ganzes wölben: Wände bleiben überall IW dick, die Fächer werden in der Mitte etwas weiter."""
    out = inlay_outer(warp=False)
    inner = inlay_outer(IW, Z_LIP + 10, warp=False)     # Wände mindestens IW (auch in den Ecken)
    comps, hollows = [], []
    y_top = Z_LIP + 10
    for k in (-1, 0, 1):
        xc = k * (CMP_W + IW)
        x0, x1 = xc - CMP_W / 2, xc + CMP_W / 2
        # Fach: vorne senkrecht, hinten schräge Stütze
        poly = [(Y_FI, Z_F), (support_y(Z_F), Z_F), (support_y(y_top), y_top), (Y_FI, y_top)]
        comps.append(_yz_prism(poly, x0, x1))
        # Hohlraum hinter der Stütze, Dach als kurze Brücke unter Z_LIP
        yb = Y_CB - G_I - IW
        z_roof = Z_LIP - IW
        dy = IW / COS
        z0 = T - 1.0                                     # nach unten offen (kein eingeschlossener Hohlraum, spart Material)
        polyh = [(support_y(z0) + dy, z0), (yb, z0), (yb, z_roof), (support_y(z_roof) + dy, z_roof)]
        hollows.append(_yz_prism(polyh, x0, x1))
    cut = (Manifold.batch_boolean(comps, manifold3d_op("add")) ^ inner)
    cut = cut + (Manifold.batch_boolean(hollows, manifold3d_op("add")) ^ inner)
    m = out - cut
    m = m - Manifold.batch_boolean([scoop_cut(k * (CMP_W + IW)) for k in (-1, 0, 1)], manifold3d_op("add"))
    m = bulge(m.refine_to_length(6.0), inlay=True)
    # Aussparung für die Verschluss-Verstärkung der Basis: das Inlay muss beim Einsetzen senkrecht daran vorbei.
    # Die Vorderwand des mittleren Fachs springt dort um die Verstärkung zurück (U-förmig).
    xb = BOSS_W + 2.0 + 0.5
    yb = Y_OUT_F + BOSS_T + 0.3
    clear = box(-xb, -200, -1, xb, yb, 200)
    jog = box(-xb - IW, Y_OUT_F - 1, T - 0.5, xb + IW, yb + IW, SCOOP_Z) ^ bulge(inlay_outer(warp=False), inlay=True)
    return (m + jog) - clear


# ----------------------------------------------------------------------------- Karten (Prüfkörper)
def card_mesh():
    import os, trimesh
    here = os.path.dirname(os.path.abspath(__file__))
    m = trimesh.load(os.path.join(here, "..", "v4", "out", "10_karte_orange.stl"))
    return Manifold(Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32), tri_verts=np.asarray(m.faces, dtype=np.uint32)))


def card_place(card, x_center, y_back_bottom, lean_deg=LEAN, front_to_viewer=True):
    """Karte (STL: x 0..70, y 0..112 Höhe, z 0..4 Dicke, z=4 Vorderseite) in die Box setzen.
    Hintere Unterkante liegt bei (y_back_bottom, Z_F), Karte um lean_deg nach hinten geneigt."""
    # STL -> Box: x' = x - 35 + xc ; Kartenhöhe y -> z ; Dicke z -> -y (Vorderseite nach vorn)
    m = card.transform(np.array([[1, 0, 0, -CARD_W / 2], [0, 0, -1, 0], [0, 1, 0, 0]], dtype=np.float32))
    # jetzt: hintere Fläche bei y=0, vordere bei y=-4, unten z=0; neigen um x durch die hintere Unterkante
    m = m.rotate([-lean_deg, 0, 0])
    return m.translate([x_center, y_back_bottom, Z_F])


def cards_stack(card, n=N_PER, dx=0.0, lean=LEAN):
    out = []
    for k in (-1, 0, 1):
        xc = k * (CMP_W + IW) + dx
        for i in range(n):
            out.append(card_place(card, xc, Y_S0 - i * CARD_T / math.cos(math.radians(lean)), lean))
    return Manifold.batch_boolean(out, manifold3d_op("add"))


def rot_lid(m, ang):
    """Deckel um die Scharnierachse öffnen (Vorderkante hoch)."""
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    # Drehung um x durch (Y_H, Z_H): y' = Y_H + (y-Y_H) c + (z-Z_H) s ; z' = Z_H - (y-Y_H) s + (z-Z_H) c
    M = np.array([[1, 0, 0, 0],
                  [0, c, s, Y_H - c * Y_H - s * Z_H],
                  [0, -s, c, Z_H + s * Y_H - c * Z_H]], dtype=np.float32)
    return m.transform(M)


# ============================================================================= Fuzzy-Modifier
def fuzzy_modifier(part):
    """Modifier-Körper für Fuzzy Skin (Kontur): Band 0,6 mm außen bis 1,2 mm innen an der Außenhaut.
    Glatt bleiben: Fasen an Boden/Dach, V-Fuge, Scharniere, Verschluss, Ösen (Passflächen, Optik)."""
    if part == "basis":
        z0, z1 = 3.0, P - GROOVE - 0.8
    else:
        z0, z1 = P + GROOVE + 0.8, H - 3.0
    band = outer_body(z0, z1, extra=-0.6) - outer_body(z0 - 1, z1 + 1, extra=1.2)
    ex = []
    for s in (1, -1):
        ex.append(box(s * PX - POD / 2 - 4, D_O / 2 - 6, P - 24, s * PX + POD / 2 + 4, D_O / 2 + 20, P + 22))
        ex.append(box(-400, -16, EAR_Z - 24, -(W_O / 2 - 4), 16, EAR_Z + 16) if s < 0 else box(W_O / 2 - 4, -16, EAR_Z - 24, 400, 16, EAR_Z + 16))
    ex.append(box(-TW / 2 - SLOT - 3, -D_O / 2 - 20, P - 24, TW / 2 + SLOT + 3, -D_O / 2 + 6, Z_ROOT + 3))
    return band - Manifold.batch_boolean(ex, manifold3d_op("add"))


# ============================================================================= Druckausrichtung
def orient_tf(name, m):
    """Drehung + Verschiebung in Druckausrichtung (nur Drehungen, nie spiegeln), als Funktion für Teil und Modifier."""
    rot = {"basis": [0, 0, 45],          # diagonal: mit Ösen breiter als 256 mm
           "deckel": [180, 0, 0],        # kopfüber, Dach auf der Platte
           }.get(name, [0, 0, 0])
    r = m.rotate(rot)
    b = r.bounding_box()
    t = [-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]]
    return lambda x: x.rotate(rot).translate(t)


def orient(name, m):
    return orient_tf(name, m)(m)


if __name__ == "__main__":
    print(f"Außen {W_O:.1f} × {D_O:.1f} × {H:.1f} mm, Teilung {P}, Achse y {Y_H:.1f}")
    for name, f in (("basis", base), ("deckel", lid), ("inlay", inlay)):
        m = f()
        print(name, m.status(), round(m.volume() / 1000, 1), "cm³", [round(v, 1) for v in m.bounding_box()])
