"""Probedruck-Coupons: kleine Stücke, mit denen Passungen auf deinem Drucker eingestellt werden."""
import model as M
from model import box, cyl_z, cyl_y, slab, rr, U


def base_at_zero(m):
    bb = m.bounding_box()
    return m.translate([-bb[0], -bb[1], -bb[2]])


def c1_wand_rechts():
    """Rechte Wand mit Drehgeber- und Klinkenloch, aufrecht wie im Korpus."""
    k = M.korpus() ^ box(126, 70, 12, M.W, 98, 74)
    foot = box(126, 70, 12, M.W - 0.5, 98, 14)
    return base_at_zero(k + foot)


def c1_wand_hinten():
    """Rückwand mit Loch für die USB-C-Einbaubuchse – erst drucken, wenn die Buchse feststeht."""
    ux, uz = M.usb_panel()
    k = M.korpus() ^ box(ux - 16, M.W - 14, uz - 16, ux + 16, M.W, uz + 16)
    foot = box(ux - 16, M.W - 14, uz - 16, ux + 16, M.W - 0.5, uz - 14)
    return base_at_zero(k + foot)


def c2_deckelecke():
    z0 = M.LID_BOT - 20
    corner = M.korpus() ^ box(0, 95, z0, 45, M.W, M.HB)
    lo, lb = M.deckel()
    lid = (lo + lb) ^ box(0, 95, 0, 45, M.W, M.HB)
    ring = M.deckelrahmen() ^ box(0, 95, 0, 45, M.W, M.HB)
    return base_at_zero(corner), base_at_zero(lid), base_at_zero(ring.rotate([180, 0, 0]))


def c3_taste():
    s = 17
    lo, lb = M.deckel()
    lid = (lo + lb) ^ box(M.BTN_X - s, M.BTN_Y - s, 0, M.BTN_X + s, M.BTN_Y + s, M.HB)
    holder = M.deckelrahmen() ^ box(M.BTN_X - s, M.BTN_Y - s, 0, M.BTN_X + s, M.BTN_Y + s, M.HB)
    cap = M.taste()
    holder = max(holder.decompose(), key=lambda p: p.volume())      # dünne Schnittreste am Rand weglassen
    return base_at_zero(lid), base_at_zero(holder.rotate([180, 0, 0])), base_at_zero(cap.rotate([180, 0, 0]))


def c4_rahmenstifte():
    """Block mit drei Löchern 4,0 / 4,1 / 4,2 und Leiste mit drei Stiften – passende Kombination wählen."""
    blk = box(0, 0, 0, 44, 14, 8)
    for i, d in enumerate((4.0, 4.1, 4.2)):
        blk = blk - cyl_z(8 + i * 14, 7, 8 - 2.8, 3, d / 2)
        # Markierung: 1, 2, 3 Kerben
        for k in range(i + 1):
            blk = blk - box(3 + i * 14 + k * 2.2, 0.0, 6.8, 4.2 + i * 14 + k * 2.2, 1.0, 8.1)
    strip = box(0, 0, 0, 44, 14, M.FR_T)
    for i in range(3):
        strip = strip + cyl_z(8 + i * 14, 7, M.FR_T - 0.1, 2.5, M.PIN_D / 2 - 0.05)
    return blk, strip.translate([0, 20, 0])


def c5_touch():
    """Deckelstück: links mit Tasche (4 mm über dem Kupfer, unter der Ringnut 3,2 mm), rechts ohne."""
    p = slab(rr(0, 0, 70, 36, 3), 0, M.LID_T)
    p = p - cyl_z(18, 18, -1, 1 + M.PAD_POCKET, 10)
    p = p - (cyl_z(18, 18, M.LID_T - M.SKIN, 2, 11) - cyl_z(18, 18, -1, 9, 9.9))
    p = p - (cyl_z(52, 18, M.LID_T - M.SKIN, 2, 11) - cyl_z(52, 18, -1, 9, 9.9))
    return p


def c6_schraubdome():
    base = box(0, 0, 0, 44, 16, 2)
    for i, d in enumerate((2.3, 2.5, 2.7)):
        base = base + cyl_z(8 + i * 14, 8, 1.9, 10.1, M.BOSS_D / 2)
        base = base - cyl_z(8 + i * 14, 8, 3, 10, d / 2)
        for k in range(i + 1):
            base = base - box(3 + i * 14 + k * 2.2, 0, 1.2, 4.2 + i * 14 + k * 2.2, 1.0, 2.1)
    return base


def c7_lochbild():
    """Lochbild-Test für den Akku-Stapel: Rahmen mit den 4 Auflagen und Ecken-Marken der Acrylplatte (ca. 20 min).
    Stapel mit den vorhandenen Schrauben aufsetzen: Fallen die Köpfe in die Mulden, stimmt das Lochbild."""
    hs = M.stack_holes()
    xs = sorted({x for x, _ in hs}); ys = sorted({y for _, y in hs})
    t = 2.0
    bars = [box(xs[0] - 5, y - 4, 0, xs[1] + 5, y + 4, t) for y in ys] + [box(x - 4, ys[0] - 5, 0, x + 4, ys[1] + 5, t) for x in xs]
    rd, rdep = M.PAD_REC
    pads = [cyl_z(x, y, t - 0.01, M.PAD_H + 0.01, 5.5) for (x, y) in hs]
    # Ecken-Marken: Acrylplatte 85 × 55 mittig auf dem Akku-Board angenommen, Marke 1 mm außen
    ax0, ay0 = M.STACK_X0, M.STACK_Y0 + (M.UPS[1] - M.ACRYL[1]) / 2
    ax1, ay1 = ax0 + M.ACRYL[0], ay0 + M.ACRYL[1]
    marks = []
    for (cx, cy, sx, sy) in ((ax0, ay0, -1, -1), (ax1, ay0, 1, -1), (ax0, ay1, -1, 1), (ax1, ay1, 1, 1)):
        def bx(xa, xb, ya, yb, h):
            return box(min(xa, xb), min(ya, yb), 0, max(xa, xb), max(ya, yb), h)
        # L-Marke 1 mm außerhalb der Acrylkante, 1,2 breit, 1 mm höher als der Rahmen
        marks.append(bx(cx + sx * 2.2, cx - sx * 10, cy + sy * 1.0, cy + sy * 2.2, t + 1.0))
        marks.append(bx(cx + sx * 1.0, cx + sx * 2.2, cy + sy * 2.2, cy - sy * 10, t + 1.0))
        # Arme zum nächsten Steg
        hx = min(xs, key=lambda v: abs(v - cx))
        hy = min(ys, key=lambda v: abs(v - cy))
        marks.append(bx(cx + sx * 1.6, hx, cy + sy * 1.6 - 2, cy + sy * 1.6 + 2, t))
        marks.append(bx(cx + sx * 1.6 - 2, cx + sx * 1.6 + 2, cy + sy * 1.6, hy, t))
    c = U(bars + pads + marks)
    for (x, y) in hs:
        c = c - cyl_z(x, y, t + M.PAD_H - rdep, rdep + 1, rd / 2) - cyl_z(x, y, -1, 20, M.HOLE25 / 2)
    return base_at_zero(c)


def c8_bodenecke():
    """Hintere linke Ecke: Korpus unten mit Dom + Bodenplatte mit Kragen und Senkung. Prüft Schattenfuge, Kragen und Schraube 3,0 × 14."""
    k = M.korpus() ^ box(0, 98, 0, 42, M.W, M.BASE_T + 18)
    b = M.boden() ^ box(0, 98, -1, 42, M.W, 20)
    return base_at_zero(k), base_at_zero(b)


def all_coupons():
    out = {}
    out["C1_wand_rechts_drehgeber_klinke"] = c1_wand_rechts()
    out["C1_wand_hinten_usbc"] = c1_wand_hinten()
    a, b, c = c2_deckelecke()
    out["C2_deckelecke_korpus"] = a
    out["C2_deckelecke_deckel"] = b
    out["C2_deckelecke_rahmen"] = c
    a, b, c = c3_taste()
    out["C3_taste_deckelstueck"] = a
    out["C3_taste_halter"] = b
    out["C3_taste_kappe"] = c
    a, b = c4_rahmenstifte()
    out["C4_rahmenstifte_block"] = a
    out["C4_rahmenstifte_leiste"] = b
    out["C5_touch_platte"] = c5_touch()
    out["C6_schraubdome_2-3_2-5_2-7"] = c6_schraubdome()
    out["C7_lochbild_stapel"] = c7_lochbild()
    a, b = c8_bodenecke()
    out["C8_bodenecke_korpus"] = a
    out["C8_bodenecke_boden"] = b
    return out


if __name__ == "__main__":
    for k, v in all_coupons().items():
        bb = v.bounding_box()
        print(f"{k:34s} {bb[3]-bb[0]:6.1f} × {bb[4]-bb[1]:6.1f} × {bb[5]-bb[2]:6.1f}  vol {v.volume()/1000:5.1f} cm³ genus {v.genus()}")
