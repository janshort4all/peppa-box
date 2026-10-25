"""Konzept Elektronikträger v3: Platte mit Pi 3A+, Klemmen-Aufsatz, Audio-, Lade- und Ein/Aus-Modul."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from manifold3d import Manifold
import concept3 as c3
from concept3 import box, cyl_z, rrect, slab, U, render, rot, C

S24 = 24
def cz(x, y, z0, h, r): return Manifold.cylinder(h, r, r, S24).translate([x, y, z0])

COL = {
    "plate": (214, 200, 176), "pcb": (46, 120, 72), "perf": (176, 150, 96), "chip": (70, 74, 78), "metal": (190, 192, 196),
    "hdr": (30, 30, 32), "jst": (238, 236, 228), "pb": (40, 70, 140), "pol": (36, 110, 130), "max": (52, 84, 170),
    "pcm": (110, 64, 150), "cell": (60, 120, 190), "cellcap": (205, 205, 210), "body": (230, 218, 196), "screw": (160, 160, 165),
    "elko": (40, 60, 120), "term": (40, 110, 200), "wago": (226, 228, 222), "lever": (240, 128, 40),
}

PZ = 32.0          # Unterkante Trägerplatte
PT = 3.0
TOP = PZ + PT
parts = []
def add(m, col): parts.append((m, COL[col] if isinstance(col, str) else col, None))

# ---------- Trägerplatte ----------
plate = slab(rrect(116, 70, 6).translate([6, 63]), PZ, TOP) + slab(rrect(30, 37, 5).translate([104, 96]), PZ, TOP)
plate = plate - box(110, 66, PZ - 1, 118, 84, TOP + 1)               # Kabeldurchlass Akku/Klinke
grip = box(52, 63, TOP, 76, 66, TOP + 14) - box(56, 62, TOP + 4, 72, 67, TOP + 11)   # Griff zum Herausheben
plate = plate + grip
screws = U([cz(11, 128, TOP, 1.4, 3.0), cz(117, 90, TOP, 1.4, 3.0)])
plate = plate - U([cz(11, 128, PZ - 1, 6, 1.6), cz(117, 90, PZ - 1, 6, 1.6)])
add(plate, "plate"); add(screws, "screw")

# ---------- Raspberry Pi 3A+ (65 × 56), SD-Kante rechts ----------
PX0, PY0 = 9, 70
holes = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]
add(U([cz(PX0 + hx, PY0 + hy, TOP, 5, 2.6) for hx, hy in holes]), "plate")
pz = TOP + 5
add(box(PX0, PY0, pz, PX0 + 65, PY0 + 56, pz + 1.6), "pcb")
add(box(PX0 + 22, PY0 + 18, pz + 1.6, PX0 + 36, PY0 + 32, pz + 2.8), "chip")
add(box(PX0 + 50, PY0 - 1.5, pz + 1.6, PX0 + 63, PY0 + 12, pz + 8.5), "metal")          # USB-A
add(box(PX0 + 25, PY0 - 1, pz + 1.6, PX0 + 40, PY0 + 10, pz + 7.5), "metal")           # HDMI
add(box(PX0 + 63, PY0 + 20, pz - 1.2, PX0 + 67, PY0 + 32, pz), "chip")                   # SD-Karte (unten, rechts)
add(box(PX0 + 7, PY0 + 49, pz + 1.6, PX0 + 58, PY0 + 54, pz + 10), "hdr")               # Stiftleiste
# ---------- Klemmen-Aufsatz Pi-EzConnect (68,8 × 56,6) ----------
hz = pz + 1.6 + 10
add(box(PX0 + 6, PY0 + 47.5, pz + 10, PX0 + 59, PY0 + 55.5, hz), "hdr")
add(box(PX0 - 2, PY0, hz, PX0 + 66.8, PY0 + 56.6, hz + 1.6), "pcb")
for (x0, y0, x1, y1) in [(PX0 + 2, PY0 + 1, PX0 + 62, PY0 + 8.5), (PX0 + 2, PY0 + 47, PX0 + 62, PY0 + 54.5), (PX0 + 57, PY0 + 12, PX0 + 64.5, PY0 + 44)]:
    add(box(x0, y0, hz + 1.6, x1, y1, hz + 1.6 + 8.5), "term")
    n = int((x1 - x0) / 3.5) if (x1 - x0) > (y1 - y0) else int((y1 - y0) / 3.5)
    for k in range(n):
        if (x1 - x0) > (y1 - y0):
            add(cz(x0 + 1.75 + k * 3.5, y0 + 3.75, hz + 1.6 + 8.5, 0.6, 1.1), "metal")
        else:
            add(cz(x0 + 3.75, y0 + 1.75 + k * 3.5, hz + 1.6 + 8.5, 0.6, 1.1), "metal")
# ---------- Hebelklemmen WAGO 221 unter der Platte ----------
for y0 in (97, 115):
    add(box(108, y0, 22.5, 133, y0 + 17, PZ - 0.5), "wago")
    for k in range(5):
        add(box(110 + k * 4.6, y0 + 9, 20.5, 113.5 + k * 4.6, y0 + 16, 22.5), "lever")
add(box(108, 96, PZ - 0.5, 133, 98, PZ), "plate"); add(box(108, 132, PZ - 0.5, 133, 134, PZ), "plate")

# ---------- Module rechts ----------
def module(x0, y0, w, d, col, h=1.6, so=4):
    add(U([cz(x0 + 2.5, y0 + 2.5, TOP, so, 2.0), cz(x0 + w - 2.5, y0 + d - 2.5, TOP, so, 2.0)]), "plate")
    add(box(x0, y0, TOP + so, x0 + w, y0 + d, TOP + so + h), col)
    return TOP + so + h
z = module(82, 66, 25, 20, "pcm");  add(box(84, 70, z, 96, 76, z + 3), "chip"); add(box(96, 68, z, 104, 84, z + 5.5), "jst")
z = module(82, 90, 19.5, 18, "max"); add(box(88, 95, z, 95, 102, z + 1.2), "chip"); add(box(82.5, 102, z, 91, 107.5, z + 7), (40, 120, 70))
z = module(104, 92, 15, 13, "pol");  add(box(108, 95, z, 113, 100, z + 1.2), "chip")
z = module(83, 110, 36, 23, "pb");   add(box(110, 113, z, 119, 121, z + 3), "metal"); add(box(88, 116, z, 96, 122, z + 1.4), "chip")

CARRIER = list(parts)
parts = []
# ---------- Akku in der Bodenklappe (unter der Platte) ----------
hatch = slab(rrect(110, 72, 5).translate([12, 62]), 0.0, 3.0)
frame = U([box(26, 66, 3, 110, 69, 11), box(26, 109, 3, 110, 112, 11), box(26, 66, 3, 29, 112, 20), box(107, 66, 3, 110, 112, 20),
           box(29, 87.5, 3, 107, 89.5, 9)])
add(hatch + frame, "body")
for yc in (77.5, 99.5):
    add(Manifold.cylinder(70, 10.75, 10.75, 40).rotate([0, 90, 0]).translate([32, yc, 14.5]), "cell")
    add(Manifold.cylinder(4.5, 10.75, 10.75, 40).rotate([0, 90, 0]).translate([102, yc, 14.5]), "cellcap")

BATTERY = parts
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def project(p, elev, azim, size, scale, center):
    v = (np.array(p, float) - np.array(center)) @ rot(elev, azim).T
    return v[0] * scale + size / 2, -v[2] * scale + size / 2


def label(dr, img_off, p, txt, view, at, font, col=(60, 52, 44)):
    sx, sy = project(p, *view)
    sx += img_off[0]; sy += img_off[1]
    tx, ty = at
    dr.line([(sx, sy), (tx, ty + 12)], fill=(120, 110, 100), width=2)
    dr.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(120, 110, 100))
    dr.text((tx, ty), txt, fill=col, font=font)



def autolabel(dr, off, items, view, font, xl, xr, xmid, miny=150, maxy=1100):
    pts = []
    for p, t in items:
        sx, sy = project(p, *view); pts.append((sx + off[0], sy + off[1], t))
    for side in ("L", "R"):
        grp = sorted([q for q in pts if (q[0] < xmid) == (side == "L")], key=lambda q: q[1])
        last = miny - 40
        for sx, sy, t in grp:
            ty = max(sy - 11, last + 36); last = ty
            w = dr.textlength(t, font=font)
            tx = xl if side == "L" else xr
            ex = tx + w + 8 if side == "L" else tx - 8
            dr.line([(sx, sy), (ex, ty + 11)], fill=(130, 118, 104), width=2)
            dr.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(130, 118, 104))
            dr.text((tx, ty), t, fill=(60, 52, 44), font=font)


if __name__ == "__main__":
    V1 = (30, -36, 1000, 6.0, (68, 98, 46))
    a = render(CARRIER, V1[0], V1[1], size=V1[2], scale=V1[3], center=V1[4], bg=(245, 241, 234))
    cut = c3.body - box(-5, -5, -5, 150, 58, 140) - box(128, -5, -5, 150, 150, 140)
    V2 = (26, -40, 760, 3.7, (70, 95, 50))
    b = render(CARRIER + BATTERY + [(cut, C["beige"], None)], V2[0], V2[1], size=V2[2], scale=V2[3], center=V2[4], bg=(245, 241, 234))
    canvas = Image.new("RGB", (2250, 1180), (245, 241, 234))
    off1 = (250, 40); canvas.paste(a, off1)
    off2 = (1470, 220); canvas.paste(b, off2)
    dr = ImageDraw.Draw(canvas)
    ft = ImageFont.truetype(FONTB, 34); fl = ImageFont.truetype(FONT, 21); fs = ImageFont.truetype(FONT, 19)
    dr.text((50, 30), "Elektronikträger – Konzept", fill=(50, 44, 38), font=ft)
    dr.text((50, 76), "Eine Platte mit allen Platinen. Auf dem Tisch verkabeln und testen, dann als ein Teil von oben einsetzen.", fill=(110, 100, 90), font=fl)
    items = [
        ((PX0 + 20, PY0 + 50, hz + 10), "Klemmen-Aufsatz: jeder Pin eine Schraubklemme"),
        ((120, 112, 22), "2 Hebelklemmen 5 V / GND (unter der Platte)"),
        ((PX0 + 1, PY0 + 20, pz + 1.6), "Raspberry Pi 3A+"),
        ((PX0 + 66, PY0 + 26, pz - 0.6), "SD-Karte"),
        ((94, 74, 43), "PCM5102A · Kopfhörer"),
        ((90, 97, 41.5), "MAX98357A · Lautsprecher"),
        ((111, 99, 40.5), "Ein/Aus-Modul"),
        ((100, 125, 40.5), "Lademodul PowerBoost"),
        ((64, 64.5, TOP + 13), "Griff zum Herausheben"),
        ((114, 72, TOP), "Durchlass für Akkukabel"),
        ((20, 66, PZ + 1.5), "Trägerplatte 116 × 70 mm"),
    ]
    autolabel(dr, off1, items, V1[:2] + (V1[2], V1[3], V1[4]), fs, 40, 1130, off1[0] + 500, 150, 1000)
    dr.text((1500, 200), "Im Gehäuse (vorne und rechts aufgeschnitten)", fill=(110, 100, 90), font=fl)
    items2 = [((70, 88, 14.5), "2 × 21700 in der Bodenklappe")]
    sx, sy = project(items2[0][0], *(V2[:2] + (V2[2], V2[3], V2[4])))
    sx += off2[0]; sy += off2[1]
    dr.line([(sx, sy), (1900, 1000)], fill=(130, 118, 104), width=2); dr.ellipse([sx-4, sy-4, sx+4, sy+4], fill=(130, 118, 104))
    dr.text((1760, 1005), items2[0][1], fill=(60, 52, 44), font=fs)
    notes = [
        "Liegt über dem Akkufach auf zwei Leisten, gehalten von 2 Schrauben",
        "Alle Platinen auf gedruckten Stützen, direkt in den Kunststoff geschraubt",
        "Höchster Punkt ca. 67 mm über dem Boden, darüber Platz für Kartenschacht und NFC-Leser",
        "Kabel nicht gezeichnet · Maße der Module passe ich nach Lieferung an",
    ]
    y = 1030
    for t in notes:
        dr.text((60, y), "•  " + t, fill=(70, 62, 54), font=fs); y += 34
    canvas.save("/home/claude/musikbox/v3/elektroniktraeger_konzept.png")
    print("ok")
