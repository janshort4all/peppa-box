"""Schnitte durch den Halter der USB-C-Platine (Soldered 333011) in der Rückwand und Ansicht der Öffnung von außen."""
import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
k = M.korpus(); ph = M.placeholders()["USB-C-Platine mit Buchse und Kabeln"]
def sec(m, x):
    # Schnitt bei x: drehen, sodass x -> z
    s = m.rotate([0, -90, 0]).slice(-x) if False else m.rotate([0, 90, 0]).slice(-x)
    return s.to_polygons()
def draw(ax, polys, fc, ec, alpha=1):
    for p in polys:
        p = np.asarray(p)
        # nach rotate([0,90,0]): (x,y,z)->(z? ) ermitteln wir empirisch unten
        ax.add_patch(Polygon(p[:, ::-1], closed=True, fc=fc, ec=ec, lw=0.6, alpha=alpha))
# Achsen der Rotation prüfen
fig, axs = plt.subplots(1, 3, figsize=(16, 6))
x, z = M.usb_panel()
for ax, xs, title in ((axs[0], x, f"Schnitt durch die Buchse (x {x:.0f})"), (axs[1], x - 8, f"Schnitt durch einen Dom (x {x-8:.0f})")):
    for m, fc, ec in ((k, "#e8dcc4", "#7a6a50"), (ph, "#6a3d9a", "#3b1f5a")):
        draw(ax, sec(m, xs), fc, ec, 0.85 if m is ph else 1)
    ax.set_title(title); ax.set_aspect('equal'); ax.autoscale()
    # Koordinaten: nach rotate([0,90,0]) gilt (y, -x?) – Achsenbeschriftung aus Polygonen
for ax in axs[:2]:
    ax.set_xlim(100, 142); ax.set_ylim(38, 76)
    ax.set_xlabel("y (Tiefe, Rückwand rechts) [mm]"); ax.set_ylabel("z (Höhe) [mm]"); ax.grid(alpha=.3)
# Ansicht von außen auf die Rückwand
s = [np.c_[np.asarray(p)[:,0], -np.asarray(p)[:,1]] for p in k.rotate([90, 0, 0]).slice(M.W - 0.3).to_polygons()]
ax = axs[2]
for p in s:
    ax.add_patch(Polygon(np.asarray(p), closed=True, fc="#e8dcc4", ec="#7a6a50", lw=0.6))
ax.set_aspect('equal'); ax.set_xlim(135, 85); ax.set_ylim(40, 80); ax.set_xlabel('x [mm] (von hinten gesehen)'); ax.set_ylabel('z [mm]')
ax.set_title("Rückwand von außen (Schnitt 0,3 mm unter der Oberfläche)"); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'usbc_schnitt.png'), dpi=110)
