"""Draufsicht und Höhenschnitt des Bodens mit Elektronik (Bild für den Aufbau)."""
import os as _os
ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrowPatch
from PIL import Image
sys.path.insert(0, _os.path.join(ROOT, "v3"))
import model as M
from concept3 import render

OUT = _os.path.join(ROOT, "v4/out")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
BG = "#f5f1ea"
INK = "#3a332c"
MUTED = "#8a7f72"
ORANGE = "#e8772e"
LB = dict(fc="#f5f1ea", ec="none", alpha=0.9, pad=1.2)
BLUE = "#3b6fb6"
GREEN = "#2f7a4a"


def cs_polys(cs):
    return [np.asarray(p) for p in cs.to_polygons()]


def rect(ax, x0, y0, x1, y1, **kw):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, **kw))


def bb(m):
    b = m.bounding_box()
    return b[0], b[1], b[3], b[4]


def top_view(ax, parts, ph):
    ax.set_facecolor(BG)
    # Außenkontur Boden, Innenkontur Korpus, Kammer
    for p in cs_polys(M.OUT.offset(-M.SHADOW)):
        ax.add_patch(Polygon(p, closed=True, fc="#e9dfcd", ec=INK, lw=1.2))
    for p in cs_polys(M.INN):
        ax.add_patch(Polygon(p, closed=True, fc="none", ec=MUTED, lw=0.8, ls=(0, (4, 3))))
    rect(ax, 3, 3, 137, M.DIV_Y + 3, fc="#d8cdb9", ec="none", hatch="////", alpha=0.6)
    ax.text(70, 26, "Lautsprecherkammer\n(gehört zum Korpus, eigener Boden)", ha="center", va="center", color=INK, fontsize=8.5, bbox=LB)
    # Kragen
    lw, lh = M.LIP
    ring = M.base_open().offset(-M.LIP_CLR) - M.base_open().offset(-M.LIP_CLR - lw)
    for p in cs_polys(ring):
        ax.add_patch(Polygon(p, closed=True, fc="#c9b99c", ec="none"))
    # Dome / Schrauben
    for (x, y) in M.BASE_BOSSES:
        ax.add_patch(Circle((x, y), M.BOSS_D / 2, fc="#cfc2aa", ec=INK, lw=0.6))
        ax.add_patch(Circle((x, y), M.CSK[0] / 2, fc="white", ec=INK, lw=0.6))
    # Kartenfach im Deckel (Projektion)
    x0, y0, x1, y1 = bb(parts["kartenfach"])
    rect(ax, x0, y0, x1, y1, fc="none", ec=ORANGE, lw=1.0, ls=(0, (2, 2)))
    ax.text(-13, 146.5, "orange gestrichelt: Kartenfach im Deckel (beginnt erst 87 mm über dem Tisch) · rot gestrichelt: Klinkenstecker am Pi (gewinkelt)", ha="left", va="center", color=ORANGE, fontsize=8)
    # Stapel
    sx, sy = M.STACK_X0, M.STACK_Y0
    L, B = M.UPS
    xp = sx + M.OVERHANG
    rect(ax, sx, sy, sx + L, sy + B, fc="#c7d6ee", ec=BLUE, lw=1.4)
    rect(ax, xp, sy, sx + L, sy + B, fc="#bfdcc8", ec=GREEN, lw=1.2)
    ax.text((xp + sx + L) / 2, sy + B / 2 + 4, "Pi + Klemmen-Aufsatz", ha="center", color=GREEN, fontsize=9, weight="bold")
    ax.text((xp + sx + L) / 2, sy + B / 2 - 3, "Oberkante Klemmen 77,5 mm", ha="center", color=GREEN, fontsize=7.5)
    ax.text(sx + M.OVERHANG / 2, sy + B / 2, "Über-\nhang\nAkku-\nBoard\nBOOT-\nTaste", ha="center", va="center", color=BLUE, fontsize=7.2, bbox=LB)
    # Stiftleiste vorne
    hx0 = xp + 7.0
    rect(ax, hx0, sy + 1.5, hx0 + 51, sy + 6.5, fc="#f2c94c", ec="#a07d10", lw=0.8)
    ax.text(hx0 + 25.5, sy + 9.0, "gelbe Stifte (Kante vorne)", ha="center", va="bottom", color="#7a5d00", fontsize=7.5, bbox=LB)
    ax.text((xp + sx + L) / 2, sy + B - 3.0, "Anschlusskante: USB-C, Schalter (zeigt nach hinten)", ha="center", va="top", color=BLUE, fontsize=7.5, bbox=LB)
    # Auflagen
    for (x, y) in M.stack_holes():
        ax.add_patch(Circle((x, y), 5.5, fc="#e9dfcd", ec=INK, lw=0.6, alpha=0.9))
        ax.add_patch(Circle((x, y), M.PAD_REC[0] / 2, fc="white", ec=INK, lw=0.5))
    hs = M.stack_holes()
    ax.annotate("", xy=(hs[0][0], hs[0][1] - 0), xytext=(hs[1][0], hs[1][1]), arrowprops=dict(arrowstyle="<->", color=INK, lw=0.6))
    ax.text((hs[0][0] + hs[1][0]) / 2, hs[0][1] + 1.5, "58", ha="center", fontsize=7.5, color=INK)
    ax.annotate("", xy=(hs[1][0], hs[1][1]), xytext=(hs[3][0], hs[3][1]), arrowprops=dict(arrowstyle="<->", color=INK, lw=0.6))
    ax.text(hs[1][0] - 1.5, (hs[1][1] + hs[3][1]) / 2, "49", ha="right", va="center", fontsize=7.5, color=INK)
    # Kabelzonen
    for k in ("Kabel Klemmreihe links (Zone)", "Kabel Klemmreihe rechts (Zone)", "Kabel Klemmreihe hinten (Zone)"):
        x0, y0, x1, y1 = bb(ph[k])
        rect(ax, x0, y0, x1, y1, fc="none", ec=GREEN, lw=0.6, hatch="...", alpha=0.6)
    # Mulden hinten
    for (name, x0, y0, w, d, h) in M.rear_layout():
        rect(ax, x0, y0, x0 + w, y0 + d, fc="white", ec=INK, lw=0.9)
        label = {"WAGO GND A": "GND A\n5-fach", "WAGO 5 V": "5 V\n3-fach", "Verstärker": "Verstärker\nMAX98357A"}[name]
        ax.text(x0 + w / 2, y0 + d / 2, label, ha="center", va="center", fontsize=7.5, color=INK)
    # rechts frei
    ax.text(115.5, 92, "frei\n(Kabelreserve,\nElko)", ha="center", va="center", color=MUTED, fontsize=7.8, bbox=LB)
    x0, y0, x1, y1 = bb(ph["Klinkenstecker am Pi (Zone)"])
    rect(ax, x0, y0, x1, y1, fc="none", ec="#c2410c", lw=0.8, ls=(0, (3, 2)))
    # Wandteile
    for k, lab, side in (("Drehgeber", "Drehknopf", "r"), ("Klinkenbuchse", "Klinke", "r")):
        x0, y0, x1, y1 = bb(ph[k])
        rect(ax, x0, y0, min(x1, 140), y1, fc="#d9d9d9", ec=INK, lw=0.6, alpha=0.8)
    ax.text(141.5, 84, "Drehknopf (z 60)\nKlinke (z 24)", ha="left", va="center", fontsize=7.5, color=INK)
    x0, y0, x1, y1 = bb(ph["USB-C-Einbaubuchse mit Kabel"])
    rect(ax, x0, y0, x1, y1, fc="#d9d9d9", ec=INK, lw=0.6, alpha=0.8)
    ax.text((x0 + x1) / 2, 141.5, "USB-C-Buchse (z 60)", ha="center", va="bottom", fontsize=7.5, color=INK)
    ax.text(-1.5, M.STRAP_Y, "Riemen\n(z 118)", ha="right", va="center", fontsize=7.5, color=INK)
    ax.text(70, -2.5, "VORNE  (Lautsprecher)", ha="center", va="top", fontsize=9, weight="bold", color=INK)
    ax.set_xlim(-14, 160)
    ax.set_ylim(-9, 149)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Boden von oben (Maße in mm, Korpus abgenommen)", loc="left", color=INK, fontsize=11, weight="bold")


def height_view(ax, parts, ph):
    """Höhen über der Tischplatte, Blick von rechts (vorne links)."""
    ax.set_facecolor(BG)
    def band(y0, y1, z0, z1, fc, ec, label=None, lx=None, lz=None, ha="center", **kw):
        rect(ax, y0, z0, y1, z1, fc=fc, ec=ec, lw=0.8, **kw)
        if label:
            ax.text(lx if lx is not None else (y0 + y1) / 2, lz if lz is not None else (z0 + z1) / 2, label, ha=ha, va="center", fontsize=7.5, color=INK, bbox=LB)
    # Korpus-Umriss
    ax.add_patch(Rectangle((0, M.BASE_T), 140, M.HB - M.BASE_T, fc="none", ec=MUTED, lw=1.0))
    band(0.4, 139.6, 0, M.BASE_T, "#e9dfcd", INK)
    ax.text(141.5, 2, "Boden 4", va="center", fontsize=7.5, color=INK)
    band(3, M.DIV_Y + 3, M.BASE_T, M.CH_Z + 3, "#d8cdb9", "none", "Lautsprecher-\nkammer", hatch="////", alpha=0.6)
    za = M.BASE_T + M.PAD_H
    sy, B = M.STACK_Y0, M.UPS[1]
    band(sy, sy + B, za, za + M.UPS_LEVEL, "#c7d6ee", BLUE, "Akku-Board\nmit Zellen")
    band(sy, sy + B, za + M.UPS_LEVEL, za + M.STACK_H, "#bfdcc8", GREEN, "Pi +\nKlemmen-\nAufsatz")
    k = parts["kartenfach"].bounding_box()
    band(k[1], k[4], k[2], k[5], "#f3c9a6", ORANGE, None)
    ax.text(k[4] + 1, k[2] + 6, "Kartenfach\nab 86,8", ha="left", va="center", fontsize=7, color=ORANGE)
    for (name, x0, y0, w, d, h) in M.lid_layout()[:1]:
        b = ph[name].bounding_box()
        band(M.BRIDGE_Y[0], M.BRIDGE_Y[1], b[2], M.LID_BOT, "#ececec", INK, None)
        ax.text(M.BRIDGE_Y[0] - 1, b[2] + 6, "Klemmen + Touch\nunter dem Deckel", ha="right", va="center", fontsize=7, color=INK, bbox=LB)
    band(3.4, 136.6, M.LID_BOT, M.LID_TOP, "#f0a873", ORANGE, None)
    for (name, x0, y0, w, d, h) in M.rear_layout():
        b = ph[name].bounding_box()
        band(b[1], b[4], b[2], b[5], "white", INK, None)
    ax.text(124, 24, "Klemmen,\nVerstärker", ha="center", va="center", fontsize=7, color=INK, bbox=LB)
    for zz, lab in ((77.5, "77,5"), (86.8, "86,8"), (117.4, "117,4")):
        ax.axhline(zz, xmin=0.0, xmax=1.0, color=MUTED, lw=0.4, ls=":")
        ax.text(-2, zz, lab, ha="right", va="center", fontsize=7, color=MUTED)
    ax.text(70, -6, "vorne  ←  y  →  hinten", ha="center", va="top", fontsize=8, color=INK)
    ax.set_xlim(-14, 160)
    ax.set_ylim(-12, 146)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Höhen (Blick von der Seite)", loc="left", color=INK, fontsize=11, weight="bold")


def render_base(parts, ph):
    """Leerer Boden, so wie er aus dem Drucker kommt (Blick von vorne rechts oben)."""
    return render([(parts["boden"], (232, 220, 198), None)], 34, -24, size=760, scale=3.7, center=(70, 66, 4), light=(-0.35, -0.6, 0.9))


if __name__ == "__main__":
    parts = M.build()
    ph = M.placeholders()
    fig = plt.figure(figsize=(14.0, 7.2), dpi=150, facecolor=BG)
    a1 = fig.add_axes([0.0, 0.0, 0.52, 0.96])
    a2 = fig.add_axes([0.53, 0.0, 0.47, 0.96])
    top_view(a1, parts, ph)
    height_view(a2, parts, ph)
    p = f"{OUT}/boden_plan.png"
    fig.savefig(p, facecolor=BG)
    img = render_base(parts, ph)
    img.save(f"{OUT}/boden_3d.png")
    print(p)
