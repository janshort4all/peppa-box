"""Bild zum Niederhalter (Steg über der gelben Stiftleiste): Draufsicht und Querschnitt → out/niederhalter.png

Maße aus model.py. Lage der Stiftleiste aus Jans Messung (a ca. 4,5, b ca. 5,3, symmetrisch);
Klemmblöcke der Schmalseiten aus dem Foto vom 07.11. geschätzt (gestrichelt).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
import model as M

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
B_LEISTE = 5.3          # Jan 07.11.: Lochlinie bis Mitte zwischen den beiden Stiftreihen (ca.)
P = 2.54

holes, zp, yv, (xe0, xe1) = M.niederhalter_geo()
fl, fb = M.NH_FREI
ya, yb = M.NH_Y
# alles relativ: x ab Platinenende links, y ab Vorderkante, z ab Platinenoberseite
hx = [h[0] - xe0 for h in holes]
hy = holes[0][1] - yv
yc = hy + B_LEISTE                                  # Mitte zwischen den Stiftreihen
xc = (hx[0] + hx[1]) / 2
xs = [xc + (i - 9.5) * P for i in range(20)]
z0 = M.NH_STECKER + M.NH_KABEL
z1 = z0 + M.NH_T

fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 11.5), gridspec_kw={"height_ratios": [1.05, 1]})
fig.suptitle("Niederhalter für die Steckkabel auf der gelben Stiftleiste", fontsize=15, fontweight="bold")

# --- Draufsicht ---
a1.set_title("Draufsicht (Vorderkante der Platine unten, gelbe Stiftleiste vorne)", fontsize=11)
a1.add_patch(Rectangle((0, 0), 65, 34, fc="#2f6fa8", ec="k", alpha=0.18))
a1.text(1, 32.5, "blaue Platine Klemmen-Aufsatz (vorderer Teil)", fontsize=9, va="top")
for x0 in (0, 65 - 14):
    a1.add_patch(Rectangle((x0, 18), 14, 16, fc="#999", ec="k", ls="--", alpha=0.35))
a1.text(7, 26, "Klemm-\nblock\n(geschätzt)", ha="center", va="center", fontsize=8)
a1.text(58, 26, "Klemm-\nblock\n(geschätzt)", ha="center", va="center", fontsize=8)
for x in xs:                                         # Pi-Leiste (dunkle Stifte) auf der Lochlinie
    for dy in (-P / 2, P / 2):
        a1.add_patch(Rectangle((x - 0.3, hy + dy - 0.3), 0.6, 0.6, fc="#333"))
for x in xs:                                         # Steckergehäuse auf den gelben Stiften
    for dy in (-P / 2, P / 2):
        a1.add_patch(Rectangle((x - 1.25, yc + dy - 1.25), 2.5, 2.5, fc="#222", ec="#e7c33a", lw=0.6))
roof = [(0, ya), (65, ya), (65, fb), (65 - fl, fb), (65 - fl, yb), (fl, yb), (fl, fb), (0, fb)]
a1.add_patch(Polygon(roof, closed=True, fc="#e07b2a", ec="#a04a10", lw=1.5, alpha=0.35))
for x in hx:
    a1.add_patch(Circle((x, hy), M.NH_POST / 2, fc="#e07b2a", ec="#a04a10", alpha=0.6))
    a1.add_patch(Circle((x, hy), M.NH_SENK[0] / 2, fc="none", ec="k", ls=":"))
    a1.add_patch(Circle((x, hy), M.HOLE25 / 2, fc="w", ec="k"))
a1.annotate("", (hx[0], -4), (hx[1], -4), arrowprops=dict(arrowstyle="<->"))
a1.text(xc, -5, f"Lochabstand {M.NH_LOCH:g}", ha="center", va="top", fontsize=9)
a1.annotate("", (67, ya), (67, yb), arrowprops=dict(arrowstyle="<->"))
a1.text(67.8, (ya + yb) / 2, f"Dach {yb - ya:g} breit", va="center", fontsize=9)
a1.text(xc, yb + 0.8, f"Dach {M.NH_T:g} mm stark, ganze Platinenlänge 65 mm; hinten an den Ecken frei über den Klemmblöcken",
        ha="center", fontsize=8.5, color="#a04a10")
a1.text(xc, yc + 3.4, "Steckkabel auf den gelben Stiften (2 × 20)", ha="center", fontsize=8.5)
a1.text(xc, hy - 2.6, "Pi-Leiste (dunkle Stifte) auf der Lochlinie", ha="center", fontsize=8, color="#333")
a1.set_xlim(-3, 80); a1.set_ylim(-9, 35); a1.set_aspect("equal"); a1.axis("off")

# --- Querschnitt ---
a2.set_title("Querschnitt durch die Stiftleiste (Säule und Schraube liegen an den Enden, hier hineingeklappt)", fontsize=11)
a2.add_patch(Rectangle((-3, -1.6), 26, 1.6, fc="#2f6fa8", alpha=0.5))
a2.text(12, -2.0, "Platine 1,6", fontsize=8, va="top")
for dy, d in ((-P / 2, -1), (P / 2, 1)):
    y = yc + dy
    a2.add_patch(Rectangle((y - 1.25, 0), 2.5, M.NH_STECKER, fc="#222"))
    a2.plot([y, y], [M.NH_STECKER - 3, M.NH_STECKER - 0.2], color="#e7c33a", lw=2)
    zk = M.NH_STECKER + 0.75
    a2.plot([y, y, y + d * 0.8, y + d * 9], [M.NH_STECKER, zk - 0.2, zk, zk], color="#c0392b", lw=3.5, solid_capstyle="round")
a2.add_patch(Rectangle((ya, z0), yb - ya, M.NH_T, fc="#e07b2a", ec="#a04a10", alpha=0.6))
a2.add_patch(Rectangle((hy - M.NH_POST / 2, 0), M.NH_POST, z0, fc="#e07b2a", ec="#a04a10", alpha=0.25, ls="--"))
sd, st = M.NH_SENK
a2.add_patch(Rectangle((hy - 2.5, z1 - st), 5.0, 1.8, fc="#888", ec="k"))              # Kopf
L = M.niederhalter_schraube() + 2.4
a2.add_patch(Rectangle((hy - 1.25, z1 - st - L), 2.5, L, fc="#aaa", ec="k"))           # Schaft
a2.add_patch(Rectangle((hy - 2.5, -1.6 - 2.0), 5.0, 2.0, fc="#666", ec="k"))           # Mutter
a2.text(hy - 3.3, -2.6, "Mutter oder\nAbstandsbolzen", fontsize=8, ha="right", va="center")
a2.text(hy, z1 + 0.6, "M2,5 × 20\nLinsenkopf, versenkt", ha="center", fontsize=8)
a2.annotate("", (25, 0), (25, M.NH_STECKER), arrowprops=dict(arrowstyle="<->"))
a2.text(25.5, M.NH_STECKER / 2, f"{M.NH_STECKER:g} Stecker\n(gemessen)", va="center", fontsize=8.5)
a2.annotate("", (25, M.NH_STECKER), (25, z0), arrowprops=dict(arrowstyle="<->"))
a2.text(25.5, M.NH_STECKER + M.NH_KABEL / 2, f"{M.NH_KABEL:g} Kabelknick (vorläufig, bitte messen)", va="center", fontsize=8.5, color="#c0392b")
a2.annotate("", (25, z0), (25, z1), arrowprops=dict(arrowstyle="<->"))
a2.text(25.5, (z0 + z1) / 2, f"{M.NH_T:g} Dach", va="center", fontsize=8.5)
a2.text(yc + 6, M.NH_STECKER - 1.5, "innere Reihe:\nKabel nach hinten", fontsize=8, color="#c0392b", va="top")
a2.text(-2.6, z1 + 2.2, "vorne (Kammerwand)", fontsize=8.5)
a2.text(21, z1 + 2.2, "hinten (Box-Mitte)", fontsize=8.5, ha="right")
a2.set_xlim(-4, 42); a2.set_ylim(-5.5, z1 + 4); a2.set_aspect("equal"); a2.axis("off")

fig.text(0.02, 0.012,
         "Kabel direkt über dem Stecker zur Seite knicken: äußere Reihe nach vorne, innere Reihe nach hinten. Das Dach drückt über den Knick auf die Stecker.",
         fontsize=9)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
p = os.path.join(OUT, "niederhalter.png")
fig.savefig(p, dpi=130)
print(p)
