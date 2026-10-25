"""Konzeptmodell Musikbox v3: beige, orange Akzente, Lederriemen, Kartenschlitz, versenkter Deckel."""
import math
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
import manifold3d as m3
from manifold3d import Manifold, CrossSection, JoinType

SEG = 96
W = D = 140.0
H = 124.0
R = 16.0
WALL = 3.0
LID_TOP = H - 1.2          # Deckel 1,2 mm unter der Kante
LID_T = 4.0
SKIN = 0.7                 # beige Deckschicht (Farbwechsel danach)
GAP = 0.4

# Karte
CARD_W, CARD_H, CARD_T = 70.0, 100.0, 4.0
CARD_IN = 25.0
SLOT_Y = 104.0
TILT = 8.0

# Touch-Layout (x, y, Ø)
PADS = {"prev": (30, 30, 22), "play": (70, 30, 30), "next": (110, 30, 22), "moon": (70, 64, 18)}

C = {
    "beige": (230, 218, 196), "orange": (232, 119, 46), "fabric": (226, 211, 184), "leather": (139, 88, 45),
    "brass": (201, 164, 76), "dark": (40, 38, 36), "cover_bg": (62, 132, 140), "sun": (247, 196, 66),
    "hill1": (118, 168, 92), "hill2": (82, 136, 74), "paper": (246, 240, 228), "ink": (120, 112, 100),
}


def rrect(w, d, r):
    r = max(min(r, w / 2 - 0.01, d / 2 - 0.01), 0.3)
    return CrossSection.square([w - 2 * r, d - 2 * r]).translate([r, r]).offset(r, JoinType.Round, circular_segments=SEG)


def ccw(p):
    a = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return p if a > 0 else p[::-1]


def poly(p):
    return CrossSection([ccw(p)])


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_z(x, y, z0, h, r, seg=SEG):
    return Manifold.cylinder(h, r, r, seg).translate([x, y, z0])


def cyl_x(x0, x1, y, z, r, seg=SEG):
    return Manifold.cylinder(x1 - x0, r, r, seg).rotate([0, 90, 0]).translate([x0, y, z])


def cyl_y(y0, y1, x, z, r, seg=SEG):
    return Manifold.cylinder(y1 - y0, r, r, seg).rotate([-90, 0, 0]).translate([x, y0, z])


def slab(cs, z0, z1):
    return Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def U(lst):
    return Manifold.batch_boolean(lst, m3.OpType.Add)


OUT = rrect(W, D, R)
INN = rrect(W - 2 * WALL, D - 2 * WALL, R - WALL).translate([WALL, WALL])

# ---------------- Korpus ----------------
body = Manifold.batch_hull([slab(OUT.offset(-1.2, JoinType.Round), 0, 0.01), slab(OUT, 1.2, H - 1.0), slab(OUT.offset(-1.0, JoinType.Round), H - 0.01, H)])
body = body - slab(INN, 3, H + 1)
# Front: Stoffvertiefung
FX0, FX1, FZ0, FZ1 = 12, 128, 12, 108
body = body - Manifold.extrude(rrect(FX1 - FX0, FZ1 - FZ0, 9).translate([FX0, FZ0]), 3).rotate([90, 0, 0]).translate([0, 2.2, 0])
# Rechts: Drehknopf-Durchführung + Klinke
KN_Y, KN_Z = 84.0, 50.0
JK_Y, JK_Z = 84.0, 20.0
body = body - cyl_x(W - 4, W + 1, JK_Y, JK_Z, 3.1)
# Rückseite
body = body - Manifold.extrude(rrect(13, 7, 3).translate([112 - 6.5, 50 - 3.5]), 6).rotate([90, 0, 0]).translate([0, D + 1, 0])
body = body - cyl_y(D - 4, D + 1, 112, 76, 8.0)
for i in range(6):
    body = body - Manifold.extrude(rrect(3.2, 18, 1.6).translate([22 + i * 6.4 - 1.6, 84]), 6).rotate([90, 0, 0]).translate([0, D + 1, 0])

# ---------------- Stoff ----------------
fabric = Manifold.extrude(rrect(FX1 - FX0 - 1, FZ1 - FZ0 - 1, 8.5).translate([FX0 + 0.5, FZ0 + 0.5]), 2.0).rotate([90, 0, 0]).translate([0, 1.9, 0])

# ---------------- Deckel (versenkt, zweifarbig) ----------------
LIDCS = INN.offset(-GAP, JoinType.Round)
lid_core = slab(LIDCS, LID_TOP - LID_T, LID_TOP - SKIN)
lid_skin = slab(LIDCS, LID_TOP - SKIN, LID_TOP)


def tri(x0, y0, s, left):
    if left:
        return [(x0, y0), (x0 + s, y0 + s * 0.62), (x0 + s, y0 - s * 0.62)]
    return [(x0, y0 + s * 0.62), (x0, y0 - s * 0.62), (x0 + s, y0)]


sym = []
px, py, _ = PADS["prev"]; sym += [poly(tri(px - 9, py, 8, True)), poly(tri(px + 0.5, py, 8, True))]
px, py, _ = PADS["next"]; sym += [poly(tri(px - 8.5, py, 8, False)), poly(tri(px + 0.5, py, 8, False))]
px, py, _ = PADS["play"]
sym += [poly(tri(px - 9, py, 9.5, False)), CrossSection.square([2.6, 11.5]).translate([px + 2.5, py - 5.75]), CrossSection.square([2.6, 11.5]).translate([px + 6.6, py - 5.75])]
px, py, _ = PADS["moon"]
sym += [CrossSection.circle(5.2, SEG).translate([px - 0.6, py]) - CrossSection.circle(4.5, SEG).translate([px + 2.0, py + 1.8])]
for k, (x, y, d) in PADS.items():
    sym.append(CrossSection.circle(d / 2, SEG).translate([x, y]) - CrossSection.circle(d / 2 - 1.1, SEG).translate([x, y]))
symcs = sym[0]
for s in sym[1:]:
    symcs = symcs + s
lid_skin = lid_skin - slab(symcs, LID_TOP - SKIN - 0.1, LID_TOP + 1)

# Kartenschlitz (geneigt)
slot = box(-CARD_W / 2 - 1.5, -CARD_T / 2 - 0.4, -40, CARD_W / 2 + 1.5, CARD_T / 2 + 0.4, 20).rotate([-TILT, 0, 0]).translate([70, SLOT_Y, LID_TOP])
lid_core = lid_core - slot
lid_skin = lid_skin - slot
body = body - slot  # (nur Deckelbereich betroffen)

# ---------------- Karte ----------------
cw, ch, ct = CARD_W, CARD_H, CARD_T
card = Manifold.extrude(rrect(cw, ch, 5), ct)          # xy = Kartenfläche, z = Dicke
card = card - Manifold.extrude(rrect(cw - 6, cw - 6, 2).translate([3, ch - 3 - (cw - 6)]), 2).translate([0, 0, ct - 0.8])  # Cover-Vertiefung
cover_bg = Manifold.extrude(rrect(cw - 6, cw - 6, 2).translate([3, ch - 3 - (cw - 6)]), 0.3).translate([0, 0, ct - 0.8])
cx0, cy0, cs = 3, ch - 3 - (cw - 6), cw - 6
sun = Manifold.extrude(CrossSection.circle(9, SEG).translate([cx0 + cs * 0.68, cy0 + cs * 0.68]), 0.35).translate([0, 0, ct - 0.5])
hill1 = Manifold.extrude(CrossSection.circle(30, SEG).translate([cx0 + cs * 0.2, cy0 - 12]) ^ CrossSection.square([cs, cs]).translate([cx0, cy0]), 0.36).translate([0, 0, ct - 0.49])
hill2 = Manifold.extrude(CrossSection.circle(26, SEG).translate([cx0 + cs * 0.85, cy0 - 14]) ^ CrossSection.square([cs, cs]).translate([cx0, cy0]), 0.37).translate([0, 0, ct - 0.48])
title = Manifold.extrude(rrect(cw - 6, 11, 2).translate([3, cy0 - 14]), 0.3).translate([0, 0, ct])
ink = U([Manifold.extrude(rrect(w, 1.6, 0.8).translate([7, cy0 - 14 + yy]), 0.3).translate([0, 0, ct + 0.05]) for w, yy in ((40, 6.2), (26, 2.8))])


def place_card(m):
    # Kartenfläche (x, y) -> Welt (x, z), Dicke -> -y (Vorderseite zeigt nach vorne)
    m = m.rotate([90, 0, 0])                      # (x,y,z) -> (x,-z,y)
    m = m.translate([70 - cw / 2, SLOT_Y + ct / 2, LID_TOP - CARD_IN])
    m = m.translate([-70, -SLOT_Y, -LID_TOP]).rotate([-TILT, 0, 0]).translate([70, SLOT_Y, LID_TOP])
    return m


card_parts = {k: place_card(v) for k, v in {"card": card, "cover_bg": cover_bg, "sun": sun, "hill1": hill1, "hill2": hill2, "title": title, "ink": ink}.items()}

# ---------------- Drehknopf ----------------
kn = Manifold.batch_hull([cyl_x(W - 0.3, W + 15, KN_Y, KN_Z, 16), cyl_x(W + 15, W + 16.2, KN_Y, KN_Z, 14.8)])
grip = cyl_x(W + 2, W + 11, KN_Y, KN_Z, 17.2) - cyl_x(W + 1, W + 12, KN_Y, KN_Z, 15.9)
for i in range(28):
    a = 2 * math.pi * i / 28
    grip = grip - cyl_x(W + 1, W + 12, KN_Y + math.cos(a) * 17.6, KN_Z + math.sin(a) * 17.6, 1.0, 16)
marker = box(W + 15.9, KN_Y - 1.0, KN_Z + 5, W + 16.5, KN_Y + 1.0, KN_Z + 13)
jack_ring = cyl_x(W - 0.2, W + 0.6, JK_Y, JK_Z, 5.0) - cyl_x(W - 1, W + 1, JK_Y, JK_Z, 3.1)
jack_hole = cyl_x(W - 6, W - 0.5, JK_Y, JK_Z, 3.0)

# ---------------- Handschlaufe links (wie bei einer Kamera) ----------------
MY, MZ = 104.0, 104.0          # Befestigungspunkt oben hinten an der linken Seite
BY, BZ = 84.0, 34.0            # unteres Ende der Schlaufe
outer = CrossSection.batch_hull([CrossSection.circle(9, 64).translate([MY, MZ]), CrossSection.circle(21, 96).translate([BY, BZ])])
inner = CrossSection.batch_hull([CrossSection.circle(0.6, 32).translate([MY - 3, MZ - 20]), CrossSection.circle(10.5, 96).translate([BY, BZ])])
loop_cs = outer - inner
def ext_yz_left(cs, x0, x1):
    e = Manifold.extrude(cs, x1 - x0)            # Ebene (y,z), Dicke entlang +z
    return e.rotate([90, 0, 90]).translate([x0, 0, 0])
strap = ext_yz_left(loop_cs, -3.6, -0.6)
tab = ext_yz_left(rrect(16, 26, 6).translate([MY - 8, MZ - 18]), -4.4, -0.6)
strap = strap + tab
stitch = U([cyl_x(-4.7, -4.3, MY + dy, MZ + dz, 0.6, 12) for dy in (-5, 0, 5) for dz in (-14,)])
studs = cyl_x(-6.0, -4.3, MY, MZ - 3, 4.6) + cyl_x(-6.4, -5.8, MY, MZ - 3, 3.0)
mount = cyl_x(-0.8, 0.2, MY, MZ - 3, 6.5)

feet = U([cyl_z(x, y, -1.0, 1.2, 5) for x in (20, 120) for y in (20, 120)])


def tm(man):
    m = man.to_mesh()
    return trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts))


PARTS = [
    (body, C["beige"], None), (fabric, C["fabric"], "fabric"), (lid_core, C["orange"], None), (lid_skin, C["beige"], None),
    (card_parts["card"], C["orange"], None), (card_parts["cover_bg"], C["cover_bg"], None), (card_parts["sun"], C["sun"], None),
    (card_parts["hill1"], C["hill1"], None), (card_parts["hill2"], C["hill2"], None), (card_parts["title"], C["paper"], None), (card_parts["ink"], C["ink"], None),
    (kn, C["orange"], None), (grip, C["dark"], None), (marker, C["beige"], None), (jack_ring, C["orange"], None), (jack_hole, C["dark"], None),
    (strap, C["leather"], "leather"), (stitch, (236, 220, 190), None), (studs, C["brass"], None), (mount, C["beige"], None), (feet, C["dark"], None),
]


# ---------------- Renderer ----------------
def rot(elev, azim):
    a, e = np.radians(azim), np.radians(elev)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return Rx @ Rz


def render(parts, elev, azim, size=900, scale=3.4, center=(70, 70, 95), light=(-0.45, -0.75, 0.9), bg=(245, 241, 234)):
    S = size * 2
    Rm = rot(elev, azim)
    L = np.array(light, float); L /= np.linalg.norm(L)
    img = np.ones((S, S, 3)) * (np.array(bg) / 255)
    zbuf = np.full((S, S), np.inf)
    tag = np.zeros((S, S), np.int8)
    tags = {None: 0, "fabric": 1, "leather": 2}
    yy, xx = np.mgrid[0:S, 0:S]
    wuv = np.zeros((S, S, 2))
    for man, col, tg in parts:
        mesh = tm(man)
        if len(mesh.faces) == 0:
            continue
        col = np.array(col, float) / 255
        v = (mesh.vertices - center) @ Rm.T
        n = mesh.face_normals @ Rm.T
        pxs = v[:, 0] * scale * 2 + S / 2
        pys = -v[:, 2] * scale * 2 + S / 2
        pz = v[:, 1]
        for f, nn, nw in zip(mesh.faces, n, mesh.face_normals):
            if nn[1] > 0.02:
                continue
            x, y, z = pxs[f], pys[f], pz[f]
            x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), S - 1))
            y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), S - 1))
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(d) < 1e-9:
                continue
            w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
            w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
            if not inside.any():
                continue
            zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            mask = inside & (zz < sub - 1e-3)
            if not mask.any():
                continue
            sub[mask] = zz[mask]
            if tg == "fabric":
                wv = mesh.vertices[f]
                wu = w0 * wv[0, 0] + w1 * wv[1, 0] + w2 * wv[2, 0]
                wz = w0 * wv[0, 2] + w1 * wv[1, 2] + w2 * wv[2, 2]
                wuv[y0:y1 + 1, x0:x1 + 1][mask] = np.stack([wu[mask], wz[mask]], -1)
            shade = 0.44 + 0.46 * max(float(nw @ L), 0) + 0.12 * max(-nn[1], 0)
            img[y0:y1 + 1, x0:x1 + 1][mask] = np.clip(col * shade, 0, 1)
            tag[y0:y1 + 1, x0:x1 + 1][mask] = tags[tg]
    fab = tag == 1
    pitch = 1.5  # mm pro Faden: grobes Leinen-/Lautsprechergewebe
    u = wuv[..., 0] / pitch; v = wuv[..., 1] / pitch
    iu, iv = np.floor(u).astype(int), np.floor(v).astype(int)
    fu, fv = u - iu, v - iv
    warp = ((iu + iv) % 2) == 0
    prof = np.where(warp, np.sin(np.pi * fu), np.sin(np.pi * fv)) ** 0.6
    along = np.where(warp, np.sin(np.pi * fv), np.sin(np.pi * fu)) ** 0.3
    rng0 = np.random.default_rng(3)
    slub_u = 0.94 + 0.06 * rng0.random(4000); slub_v = 0.94 + 0.06 * rng0.random(4000)
    slub = np.where(warp, slub_u[iu % 4000], slub_v[iv % 4000])
    weave = (0.66 + 0.34 * prof * along) * slub * 1.08
    img[fab] *= weave[fab][:, None]
    lea = tag == 2
    rng = np.random.default_rng(1)
    grain = 0.96 + 0.04 * rng.random((S, S))
    img[lea] *= grain[lea][:, None]
    zb = np.where(np.isinf(zbuf), 1e4, zbuf)
    edge = (np.abs(np.diff(zb, axis=0, prepend=zb[:1])) > 2.2) | (np.abs(np.diff(zb, axis=1, prepend=zb[:, :1])) > 2.2)
    img[edge] *= 0.62
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    a = render(PARTS, 20, -34, size=1100, scale=3.15, center=(70, 70, 100))
    b = render(PARTS, 18, 140, size=640, scale=2.7, center=(70, 70, 92), light=(0.5, 0.7, 0.8))
    c = render(PARTS, 89, 0, size=640, scale=3.6, center=(70, 72, 120), light=(-0.2, -0.4, 0.9))
    d = render(PARTS, 14, 30, size=640, scale=2.6, center=(70, 70, 92))
    canvas = Image.new("RGB", (1780, 1400), (245, 241, 234))
    canvas.paste(a, (-30, 40))
    canvas.paste(b, (1110, 30))
    canvas.paste(c, (1110, 690))
    dr = ImageDraw.Draw(canvas)
    ft = ImageFont.truetype(FONT, 34); fs = ImageFont.truetype(FONT, 21)
    dr.text((50, 28), "Musikbox v3 – Konzept", fill=(50, 44, 38), font=ft)
    dr.text((1140, 40), "Hinten links: Handschlaufe", fill=(110, 100, 90), font=fs)
    dr.text((1140, 700), "Deckel von oben", fill=(110, 100, 90), font=fs)
    notes = [
        "Beiges Gehäuse mit beigem Lautsprecherstoff, Akzente in Orange",
        "Karte 70 × 100 mm im leicht geneigten Schlitz, Cover zeigt nach vorne",
        "Versenkter beiger Deckel, Tasten vertieft in Orange: Zurück, Play/Pause, Weiter, darüber Schlummer",
        "Rechts: Lautstärkeknopf, darunter die Kopfhörerbuchse",
        "Links: Handschlaufe aus Leder mit Messing-Buchschraube, wie bei einer Kamera",
        "Hinten: USB-C zum Laden, Ein/Aus-Schalter, Lüftung",
    ]
    y = 1150
    for t in notes:
        dr.text((60, y), "•  " + t, fill=(70, 62, 54), font=fs)
        y += 38
    canvas.save("/home/claude/musikbox/v3/musikbox_v3_konzept.png")
    d.save("/home/claude/musikbox/v3/musikbox_v3_vorne_links.png")
    print("ok")
