"""Bild: Schnitt durch die Lautsprecherkammer (x = 70) – Satteldach statt flacher Decke."""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely import make_valid
import model as M

def shp(cs):
    g = None
    for p in cs.to_polygons():
        p = np.asarray(p)
        if len(p) < 3: continue
        q = make_valid(Polygon(p)); g = q if g is None else g.symmetric_difference(q)
    return g

def draw(ax, m, x, **kw):
    g = shp(m.rotate([0, -90, 0]).slice(x))           # Ebene x: Punkte (−z, y)
    if g is None: return
    for poly in (g.geoms if hasattr(g, "geoms") else [g]):
        if poly.geom_type != "Polygon": continue
        ex = np.asarray(poly.exterior.coords)
        ax.fill(ex[:, 1], -ex[:, 0], **kw)
        for h in poly.interiors:
            hi = np.asarray(h.coords); ax.fill(hi[:, 1], -hi[:, 0], color="white")

K, LS, DR = M.korpus(), M.placeholders()["Lautsprecher"], M.deckelrahmen()
fig, axs = plt.subplots(1, 2, figsize=(14, 6.6), dpi=120, sharey=True)
for ax, x, wo in zip(axs, (35.0, 105.0), ("links", "rechts")):
    draw(ax, K, x, color="#e3d5b8", ec="#7a6a50", lw=0.6)
    draw(ax, LS, x, color="#6a3d9a", alpha=0.85)
    draw(ax, DR, x, color="#f2a65a", alpha=0.9)
    ax.add_patch(plt.Rectangle((3, M.CH_Z), M.DIV_Y, 3, fill=False, ls="--", ec="#d62728", lw=1.5))
    ax.text(40, M.CH_Z + 3.8, "bisher: flache Decke = 40-mm-Brücke", color="#d62728", fontsize=9, ha="center")
    ax.text(25, 70, "Lautsprecher", color="white", fontsize=9, ha="center")
    ax.text(25, 108, "neu: Satteldach 45°\nohne Brücke", color="#2c7a2c", fontsize=10, ha="center", va="center")
    ax.text(22, 134, "Deckelrahmen", color="#a0521d", fontsize=9, ha="left")
    ax.set_xlim(-2, 58); ax.set_ylim(28, 141); ax.set_aspect("equal"); ax.grid(alpha=0.25)
    ax.set_xlabel("Tiefe y (mm), vorne links")
    ax.set_title(f"Schnitt {wo} (x = {x:.0f} mm)", fontsize=11)
axs[0].set_ylabel("Höhe im Modell (mm)")
fig.suptitle("Lautsprecherkammer: Satteldach statt flacher Decke – der First steigt von links nach rechts um "
             "ca. " + f"{M.ROOF[3] * (M.W - 2 * M.WALL):.1f}".replace(".", ",") + " mm,\nso schließt sich das Dach nicht in einer Schicht, sondern verteilt über ca. 27 Schichten",
             fontsize=11)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "kammerdecke_satteldach.png")
fig.savefig(out, bbox_inches="tight"); print(out)
