"""Schnittbilder (y/z bei x=0 und x/z bei y=Mitte) der Kartenbox, Deckel optional geöffnet."""
import os, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import model as M
from render import load, rot_lid, OUT

COL = {"basis": "#e8742a", "deckel": "#c9561a", "inlay": "#d8c49a"}

def polys(mesh, origin, normal):
    s = mesh.section(plane_origin=origin, plane_normal=normal)
    if s is None: return []
    out=[]
    for e in s.discrete:
        out.append(e)
    return out

def plot(ax, origin, normal, uidx, vidx, lid_ang=0, window=None, title=""):
    for n in ("basis","inlay","deckel"):
        m = load(n)
        if n=="deckel": m = rot_lid(m, lid_ang)
        for e in polys(m, origin, normal):
            ax.fill(e[:,uidx], e[:,vidx], color=COL[n], alpha=0.85, lw=0.3, ec="k")
    ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
    if window: ax.set_xlim(window[0], window[1]); ax.set_ylim(window[2], window[3])

if __name__ == "__main__":
    fig, axs = plt.subplots(1, 3, figsize=(20, 9))
    plot(axs[0], (0,0,0), (1,0,0), 1, 2, 0, title="Schnitt x=0 (Verschluss vorn, Scharnier hinten)")
    # Karte als Linien
    for ax in axs[:1]:
        ax.add_patch(plt.Rectangle((M.YC-M.CARD_W/2, M.CARD_Z0), M.CARD_W, M.CARD_H, fill=False, ec="b", lw=1))
    plot(axs[1], (0,0,0), (1,0,0), 1, 2, 0, window=(-12, 20, 70, 130), title="Detail Verschluss")
    plot(axs[2], (0,0,0), (1,0,0), 1, 2, 0, window=(70, 100, 90, 125), title="Detail Scharnier (Knöchel an x=0 gehört zur Basis)")
    fig.savefig(os.path.join(OUT, "s_x0.png"), dpi=70, bbox_inches="tight")
