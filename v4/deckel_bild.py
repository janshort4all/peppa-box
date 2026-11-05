"""Bild: Deckel von oben in den Druckfarben (beige Haut, orange Symbole/Ringe, orange Ein-Taste) im Korpusrand."""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import model as M

BEIGE, ORANGE, RAND, DUNKEL = "#efe0c3", "#f08a24", "#d9c7a3", "#3a3a3a"


def patch(ax, cs, **kw):
    verts, codes = [], []
    for p in cs.to_polygons():
        p = np.asarray(p)
        if len(p) < 3: continue
        verts += p.tolist() + [p[0].tolist()]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(p) - 1) + [Path.CLOSEPOLY]
    if verts:
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


def section(m, z):
    return m.slice(z)


fig, ax = plt.subplots(figsize=(8, 8.4), dpi=130)
K = M.korpus()
patch(ax, section(K, M.HB - 0.3), fc=RAND, ec="#a8956f", lw=0.6)                  # Korpusrand oben
patch(ax, M.LID_CS, fc=BEIGE, ec="#b9a57f", lw=0.4)                              # beige Haut (inkl. Fase)
patch(ax, M.pad_symbols(), fc=ORANGE, ec="none")                                  # Symbole und Ringnuten: Haut fehlt, oranger Kern sichtbar
patch(ax, M.CrossSection.circle(M.BTN_D / 2, M.SEG).translate([M.BTN_X, M.BTN_Y]), fc=ORANGE, ec="#b35f12", lw=0.6)
slot = (M.slot_cut() ^ M.slab(M.LID_CS, M.LID_TOP - 0.02, M.LID_TOP + 0.02)).project()
patch(ax, slot, fc=DUNKEL, ec="none")
names = {"zurück": "zurück", "play": "Play / Pause", "vor": "vor", "schlaf": "Schlummer (Mond)"}
for k, (x, y, d) in M.PADS.items():
    ax.text(x, y - d / 2 - 3.2, names[k], ha="center", va="top", fontsize=8.5, color="#5a4a30")
ax.text(M.BTN_X, M.BTN_Y - M.BTN_D / 2 - 3, "Ein-Taste", ha="center", va="top", fontsize=8.5, color="#5a4a30")
ax.text(70, M.SLOT_Y + 5, "Kartenschlitz", ha="center", va="bottom", fontsize=8.5, color="#5a4a30")
ax.text(70, -4, "vorne (Lautsprecher)", ha="center", va="top", fontsize=9, color="#555")
ax.set_xlim(-3, 143); ax.set_ylim(-9, 143); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Deckel von oben: beige Haut 0,8 mm, Symbole und Ringe orange bündig eingelegt, Ein-Taste orange bündig", fontsize=10)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "deckel_draufsicht.png")
fig.savefig(out, bbox_inches="tight"); print(out)
