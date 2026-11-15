"""Neuer Deckel für die bereits gedruckte Basis v2 (Kartenbox v2, Commit e8504ba, Geometrie in model_v2.py).

Anforderungen (Jan, 15.11.2026): Deckel stülpt sich über die Basis (nicht Stoß auf Stoß), Verschluss hält sicher und übersteht
einen Transport, lässt sich gut greifen und öffnen. Die Basis ist schon gedruckt und wird nicht geändert.

Lösung:
  - Deckel steht vorn und seitlich S_N über die Basis und reicht OV unter deren Oberkante (Stülprand). Hinten bleibt er bündig,
    weil dort die Scharnierknöchel der Basis sitzen; der Seitenrand läuft vor den hinteren Ecken schräg aus (Schwenkfreiheit).
    Er liegt wie v2 auf der Oberkante der Basis auf; Scharnier, Stifte und Anschlag sind die von v2.
  - Rasteinsatz (neu, klein, beige): steckt in der vorhandenen Mulde vorn an der Basis, sein Zahn greift in die alte Rastnut.
    Seine Unterkante ist eine waagerechte Haltefläche. Der Stülprand deckt ihn von vorn ab: Unter Zug kann er nicht aus der Nut.
  - Klemmlasche (wie v3, auf der Seite gedruckt, vorgebogen): Lagerböcke am Deckel, Haken greift unter den Rasteinsatz,
    Griffnase in der vorhandenen Fingermulde der Basis.
Koordinaten wie model_v2 (x rechts, y nach hinten, z oben, Box geschlossen)."""
import math
import numpy as np
from manifold3d import Manifold
import model_v2 as V

P_ = {}


def par(name, val, status, note):
    P_[name] = (val, status, note)
    return val


box, cyl_x, teardrop_x, loft, bulge = V.box, V.cyl_x, V.teardrop_x, V.loft, V.bulge
ADD = V.manifold3d_op("add")

# ----------------------------------------------------------------------------- Stülprand
SK_T = par("SK_T", 1.68, "festgelegt", "Stülprand Wand (4 Linien)")
SK_CLR = par("SK_CLR", 0.35, "Probedruck", "Spiel Stülprand ↔ Außenfläche der Basis je Seite")
S_N = SK_T + SK_CLR
OV = par("OV", 10.0, "festgelegt", "Stülprand reicht so weit unter die Oberkante der Basis (vorn/seitlich); begrenzt durch die Bandösen (Oberkante ca. 66,6 mm)")
Z_S = V.P - OV
EDGE_CH = par("EDGE_CH", 0.5, "festgelegt", "Fase außen an der Unterkante des Stülprands")
RUN_Y = par("RUN_Y", V.D_O / 2 - V.R0 - OV, "Probedruck", "Seitenrand läuft ab hier nach hinten schräg (45°) bis zur Oberkante aus – sonst stößt er beim Öffnen hinten an die Basis (check prüft)")
SEAT_Z = V.Z_LIP + 0.5                     # bis hier Innenraum wie v2 (Auflage auf der Basis, Inlay-Rand frei)

# Deckel-Grundriss: vorn und seitlich S_N größer als die Basis, hinten bündig (Mitte um S_N/2 nach vorn)
HX_L = V.W_O / 2 + S_N
HY_L = V.D_O / 2 + S_N / 2
R_L = V.R0 + S_N
YC_L = -S_N / 2

# ----------------------------------------------------------------------------- Rasteinsatz (in der Mulde der Basis v2)
INS_CLR = par("INS_CLR", 0.15, "Probedruck", "seitliche Luft Einsatz ↔ Mulde (wird zusätzlich mit 2 Tropfen Kleber gesichert)")
Z_INS0 = par("Z_INS0", V.Z_TIP - 1.0 + 0.05, "berechnet", "Unterkante des Einsatzes = Haltefläche für den Haken (Muldenboden der Basis 66,0)")
Z_INS1 = par("Z_INS1", 72.0, "festgelegt", "Oberkante des Einsatzes (über der Rastnut, unter dem Stülprand verdeckt)")
X_INS = V.TW / 2 + V.REC_SIDE - INS_CLR
Y_BF = V.Y_OUT_F                          # Außenfläche der Basis vorn (Mitte)

# ----------------------------------------------------------------------------- Klemmlasche
CL_W = par("CL_W", 22.0, "festgelegt", "Breite der Lasche")
CL_T = par("CL_T", 1.6, "Probedruck", "Federdicke (auf der Seite gedruckt, Schichten entlang der Feder)")
CL_GAP = par("CL_GAP", 0.2, "festgelegt", "Luft Lasche ↔ Deckel bzw. Einsatz")
HOOK_W = par("HOOK_W", 16.0, "festgelegt", "Breite des Hakens (passt in die Fingermulde der Basis)")
HOOK_D = par("HOOK_D", 1.2, "festgelegt", "Haken greift so weit unter den Einsatz (Fingermulde der Basis lässt nicht mehr zu)")
HOOK_FLAT = par("HOOK_FLAT", 1.0, "festgelegt", "senkrechte Stirn des Hakens")
PLAY_V = par("PLAY_V", 0.2, "festgelegt", "senkrechtes Spiel Haken ↔ Einsatz")
LEAD_ANG = par("LEAD_ANG", 30.0, "festgelegt", "Einlaufschräge gegen die Senkrechte")
Z_HC = Z_INS0 - PLAY_V
BLK_T = par("BLK_T", 8.5, "festgelegt", "Laschenkopf dick")
BLK_H = par("BLK_H", 11.0, "festgelegt", "Laschenkopf hoch")
Z_BLK0 = par("Z_BLK0", 88.0, "festgelegt", "Unterkante Laschenkopf (Lagerböcke bleiben unter der Dachrundung)")
Z_CPIN = Z_BLK0 + BLK_H / 2
CHEEK_W = par("CHEEK_W", 5.0, "festgelegt", "Lagerbock Breite")
CHEEK_CLR = par("CHEEK_CLR", 0.4, "festgelegt", "seitliche Luft Lasche ↔ Lagerbock")
HOLE_CLIP = par("HOLE_CLIP", 4.3, "Probedruck", "Bohrung im Laschenkopf (wenig Spiel)")
GRIP = par("GRIP", 6.0, "festgelegt", "Griffnase steht so weit vor")
Z_PAD = par("Z_PAD", 55.5, "festgelegt", "Druckpunkt unten (unter der Fingermulde, liegt an der Basis an)")
PRE_N = par("PRE_N", 2.0, "Probedruck", "Vorspannung am Druckpunkt (Lasche gedruckt vorgebogen)")
R_CHEEK = 4.8

Y_LF = -(V.D_O / 2 + S_N) * (1 + V.BY / (V.D_O / 2))   # Deckel-Außenfläche vorn (Mitte, nach Wölbung)
Y_PIN = Y_LF - 0.02 - BLK_T / 2
CL_X = CL_W / 2
CHEEK_X0 = CL_X + CHEEK_CLR
CHEEK_X1 = CHEEK_X0 + CHEEK_W
Z_KNEE = Z_S - 0.3                          # Lasche springt unter der Randkante nach innen auf die Basis
Z_GRIP = Z_PAD - 2.5


def skin(z):
    """Außenhaut v2 ohne Fuge (Einzug über z)."""
    return max(V._round(z, V.RB), V._round(V.H - z, V.RT))


def lid_loft(zs, insets):
    """Loft im Deckel-Grundriss (vorn/seitlich größer, hinten bündig), danach gewölbt wie v2."""
    m = loft(zs, insets, hx=HX_L, hy=HY_L, r=R_L, warp=False).translate([0, YC_L, 0])
    return bulge(m)


def lid_outer():
    zs = sorted(set([Z_S, Z_S + EDGE_CH] + list(V.zs_between(Z_S, V.H, [V.H - V.RT * (1 - math.sin(math.radians(V.CH_ANG)))]))))
    zs = [z for z in zs if z <= Z_S + 1 or z >= V.H - V.RT - 0.5 or z in (Z_S, V.H) or abs(z / 6 - round(z / 6)) < 0.05]
    return lid_loft(zs, [skin(z) + max(0.0, EDGE_CH - (z - Z_S)) for z in zs])


def lid_inner():
    """Innenraum: unter P Freiraum um die Basis (SK_CLR), von P bis SEAT_Z wie v2 (liegt auf, Inlay-Rand frei),
    darüber 45° auf Wand T zur neuen Außenhaut."""
    zs = [Z_S - 1.0, V.P + 0.01]
    clear = loft(zs, [-SK_CLR for _ in zs])                     # Grundriss der Basis v2 + SK_CLR, gewölbt
    a = V.cavity_body(V.P, V.CEIL)
    keys = [V.T, V.RB, V.H - V.RT, V.CEIL, SEAT_Z, SEAT_Z + S_N + 0.2]
    zz = [z for z in V.zs_between(V.P, V.CEIL, keys) if z <= SEAT_Z + S_N + 0.7 or z >= V.H - V.RT - 0.5 or z in (V.P, V.CEIL) or z in keys]
    zz = sorted(set(zz))
    # b liegt überall mindestens 0,3 mm innerhalb von a (keine fast deckungsgleichen Flächen → saubere STL); Wand oben 2,8 mm
    b = lid_loft(zz, [V.inset_cavity(z) + 0.3 + (S_N + 0.2) - min(S_N + 0.2, max(0.0, z - SEAT_Z)) for z in zz])
    return clear + a + b


def runout_cut():
    """Seitenrand hinten schräg auslaufen lassen (hinten kein Stülprand: dort sitzt das Scharnier)."""
    pts = [(RUN_Y, Z_S - 2), (RUN_Y, Z_S), (RUN_Y + (V.P - Z_S), V.P + 0.01), (200, V.P + 0.01), (200, Z_S - 2)]
    return V._yz_prism(pts, -300, 300)


# ----------------------------------------------------------------------------- Rasteinsatz
def insert():
    """Rasteinsatz in Einbaulage: füllt die Mulde der Basis von Z_INS0 bis Z_INS1, Zahn in der alten Rastnut."""
    yb = V.Y_RB - 0.1
    body = box(-X_INS, Y_BF + 0.02, Z_INS0, X_INS, yb, Z_INS1)
    # Einlauffase oben vorn (Haken gleitet beim Schließen darüber)
    ch = V._yz_prism([(Y_BF - 1, Z_INS1 - 1.2), (Y_BF + 1.2, Z_INS1 + 0.01), (Y_BF - 1, Z_INS1 + 0.01)], -X_INS - 1, X_INS + 1)
    body = body - ch
    # Zahn: folgt der Rastnut (Boden 45°, Haltefläche 30° zur Waagerechten), mit Luft
    g = V.groove_profile()                  # [(y0,z0) Boden vorn, (y1,z1) Boden hinten, (y1, zh1) Halt hinten, (y0, zh0) Halt vorn]
    (y0, z0), (y1, z1), (_, zh1), (_, zh0) = g
    yt = y1 - 0.2

    def zf(y):
        return z0 + (y - y0) * (z1 - z0) / (y1 - y0) + 0.25

    def zh(y):
        return zh0 + (y - y0) * (zh1 - zh0) / (y1 - y0) - 0.15
    tooth = V._yz_prism([(yb - 0.01, zf(yb)), (yt, zf(yt)), (yt, zh(yt)), (yb - 0.01, zh(yb))], -X_INS, X_INS)
    return body + tooth


# ----------------------------------------------------------------------------- Klemmlasche
def clip_profile():
    yi = Y_LF - CL_GAP                       # innen am Deckel
    yo = yi - CL_T
    yb = Y_BF - CL_GAP                       # innen an Einsatz/Basis (unter der Randkante)
    yhead = Y_LF - 0.02
    z0, z1 = Z_BLK0, Z_BLK0 + BLK_H
    hz1 = Z_HC
    hz0 = Z_HC - HOOK_FLAT
    ytip = Y_BF + HOOK_D
    hz_r = hz0 - (ytip - yb) / math.tan(math.radians(LEAD_ANG))
    ylo = yb - CL_T - 0.4                    # unterer Teil etwas kräftiger
    gz = Z_GRIP
    return [
        (yb, hz_r), (ytip, hz0), (ytip, hz1), (yb, hz1),               # Haken
        (yb, Z_KNEE), (yi, Z_KNEE), (yi, z0 - 0.01),                   # Knie: unter der Randkante nach innen
        (yhead, z0), (yhead, z1),
        (yhead - BLK_T + 1.5, z1), (yhead - BLK_T, z1 - 1.5), (yhead - BLK_T, z0 + 1.5), (yhead - BLK_T + 1.5, z0),
        (yo - 2.5, z0 - 0.01), (yo - 1.2, z0 - 1.0), (yo - 0.4, z0 - 2.4), (yo, z0 - 4.0),
        (yo, Z_KNEE - CL_T - 1.0), (ylo, Z_KNEE - CL_T - 1.0 - (yo - ylo)),   # Knie außen (45°)
        (ylo, gz + GRIP + 4.0), (ylo - GRIP + 0.6, gz + 4.6), (ylo - GRIP, gz + 3.6), (ylo - GRIP, gz + 2.2),
        (ylo - GRIP + 0.5, gz + 1.0), (ylo - GRIP + 1.6, gz + 0.2), (ylo - GRIP + 3.0, gz),
        (Y_BF - 0.05, gz + 0.6), (Y_BF - 0.05, Z_PAD + 1.5), (yb, Z_PAD + 2.0),       # Druckpunkt
    ]


def clip():
    m = V._yz_prism(clip_profile(), -CL_X, CL_X)
    hw = HOOK_W / 2
    trim = [box(-CL_X - 1, Y_BF - CL_GAP + 0.01, Z_HC - 6, -hw, Y_BF + HOOK_D + 1, Z_HC + 0.5),
            box(hw, Y_BF - CL_GAP + 0.01, Z_HC - 6, CL_X + 1, Y_BF + HOOK_D + 1, Z_HC + 0.5)]
    m = m - Manifold.batch_boolean(trim, ADD)
    return m - cyl_x(-CL_X - 1, CL_X + 1, Y_PIN, Z_CPIN, HOLE_CLIP / 2, 48)


def clip_pivot():
    return Y_LF - CL_GAP - CL_T / 2, Z_BLK0 - 4.0


def clip_free():
    """Lasche wie gedruckt: um die Wurzel vorgebogen, eingebaut drückt sie mit PRE_N am Druckpunkt gegen die Basis."""
    m = clip()
    py, pz = clip_pivot()
    L = pz - (Z_PAD + 0.75)
    E, I = 1800.0, CL_W * CL_T ** 3 / 12
    d = PRE_N * L ** 3 / (3 * E * I)
    a = math.atan2(d, L)
    lower = m ^ box(-50, -200, -50, 50, 200, pz)
    upper = m - box(-50, -200, -50, 50, 200, pz)
    c, s = math.cos(a), math.sin(a)
    T = np.array([[1, 0, 0, 0], [0, c, -s, py - c * py + s * pz], [0, s, c, pz - s * py - c * pz]], dtype=np.float32)
    return upper + lower.transform(T), d


def cheeks():
    tip_z = Z_CPIN + R_CHEEK * math.sqrt(2)
    parts = []
    for s in (-1, 1):
        x0, x1 = sorted((s * CHEEK_X0, s * CHEEK_X1))
        parts.append(Manifold.batch_hull([cyl_x(x0 + 0.5, x1 - 0.5, Y_PIN, Z_CPIN, R_CHEEK, 64), cyl_x(x0, x1, Y_PIN, Z_CPIN, R_CHEEK - 0.5, 64),
                                          box(x0 + 0.5, Y_PIN - 0.01, tip_z - 0.01, x1 - 0.5, Y_PIN + 0.01, tip_z),
                                          box(x0, Y_LF - 0.01, Z_CPIN - R_CHEEK, x1, Y_LF + 2.0, tip_z + 1.2 * (Y_LF - 0.01 - Y_PIN))]))
    zone = box(-60, Y_LF - 20, Z_S + 1.0, 60, Y_LF + 2.0, V.H - 2)
    return Manifold.batch_boolean(parts, ADD) ^ zone


def cheek_holes():
    cut = [teardrop_x(-CHEEK_X1 - 1, -CHEEK_X0 + 0.5, Y_PIN, Z_CPIN, V.HOLE_PRESS, up=False),
           teardrop_x(CHEEK_X0 - 0.5, CHEEK_X1 + 1, Y_PIN, Z_CPIN, V.HOLE_SLIP, up=False),
           teardrop_x(CHEEK_X1 - V.HEAD_T - 0.2, CHEEK_X1 + 1, Y_PIN, Z_CPIN, V.HEAD_D + 0.6, up=False)]
    return Manifold.batch_boolean(cut, ADD)


def clip_pin(d=None):
    x_head, x_end = CHEEK_X1, -CHEEK_X1 + 0.3
    r = (V.PIN_D if d is None else d) / 2
    shaft = cyl_x(x_end + 0.5, x_head - V.HEAD_T, Y_PIN, Z_CPIN, r, 48)
    tip = Manifold.batch_hull([cyl_x(x_end, x_end + 0.5, Y_PIN, Z_CPIN, r - 0.5, 48), cyl_x(x_end + 0.5, x_end + 0.6, Y_PIN, Z_CPIN, r, 48)])
    head = cyl_x(x_head - V.HEAD_T, x_head, Y_PIN, Z_CPIN, V.HEAD_D / 2, 48)
    flat = box(x_end - 1, Y_PIN - 10, Z_CPIN - 10, x_head + 1, Y_PIN + 10, Z_CPIN - r + 0.3)
    return shaft + tip + head - flat


# ----------------------------------------------------------------------------- Deckel
def lid():
    inner = lid_inner()
    shell = lid_outer() - inner - runout_cut()
    shell = shell + cheeks()
    shell = shell + (V.lid_knuckles() - V.cavity_body(V.P - 1, V.CEIL) - V.cavity_body(V.T, V.P + 1))
    return shell - V.lid_knuckle_holes() - cheek_holes()


def fuzzy_modifier():
    band = (lid_loft(*_band_profile(-0.6)) - lid_loft(*_band_profile(1.2)))
    ex = []
    for s in (1, -1):
        ex.append(box(s * V.PX - V.POD / 2 - 4, V.D_O / 2 - 8, V.P - 24, s * V.PX + V.POD / 2 + 4, V.D_O / 2 + 30, V.P + 22))
    ex.append(box(-CHEEK_X1 - 3, Y_LF - 30, Z_S - 5, CHEEK_X1 + 3, Y_LF + 8, Z_CPIN + 12))
    return band - Manifold.batch_boolean(ex, ADD) - runout_cut().translate([0, -1.5, 0])


def _band_profile(extra):
    z0, z1 = Z_S + EDGE_CH + 0.8, V.H - 3.0
    zs = [z for z in V.zs_between(z0, z1) if z >= V.H - V.RT - 0.5 or z in (z0, z1) or abs(z / 6 - round(z / 6)) < 0.05]
    return zs, [skin(z) + extra for z in zs]


def orient(name, m):
    rot = {"deckel": [180, 0, 0], "lasche": [0, -90, 0], "einsatz": [90, 0, 0]}.get(name, [0, 0, 0])
    r = m.rotate(rot)
    b = r.bounding_box()
    return r.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])


def orient_tf(name, m):
    rot = {"deckel": [180, 0, 0], "lasche": [0, -90, 0], "einsatz": [90, 0, 0]}.get(name, [0, 0, 0])
    r = m.rotate(rot)
    b = r.bounding_box()
    t = [-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]]
    return lambda x: x.rotate(rot).translate(t)


if __name__ == "__main__":
    print(f"Deckel außen {2 * HX_L + 2 * V.BX:.1f} × {2 * HY_L + V.BY * 2:.1f}, Stülprand bis {Z_S} mm, Lasche Y_LF {Y_LF:.2f}, Basis vorn {Y_BF:.2f}")
    for n, f in (("deckel", lid), ("einsatz", insert), ("lasche", clip)):
        m = f()
        print(n, m.status(), round(m.volume() / 1000, 2), "cm³", [round(v, 1) for v in m.bounding_box()])
