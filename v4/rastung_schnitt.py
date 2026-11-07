import sys, numpy as np; sys.path.insert(0,'.')
import model as M
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
F = M.card_frame(); R = F[:, :3]
inv = np.eye(4); inv[:3,:3]=R.T; inv[:3,3]=-R.T@F[:,3]
def local(m): return m.transform(inv[:3,:].astype(np.float32))
kf = local(M.kartentasche())
def sl(m, s=0.0):   # Schnitt bei u=0 → (v, w)
    return m.rotate([0,90,0]).slice(0.0) , None
fig, ax0 = plt.subplots(figsize=(11, 4.6)); axes=[ax0]
for ax, s, title in ((ax0, 0.0, "Schnitt Kartenfach-Mitte: Karte steckt, Nase liegt entspannt in der Rille"),):
    card = M._karte_nach_kartenrahmen(M.karte_print()).translate([0, -s, 0])
    for m, col, lab in ((kf, "#8a8f98", "Kartenfach mit Federzunge"), (card, "#f08a24", "Karte")):
        cs = m.rotate([0, 90, 0]).slice(0.0)   # nach Drehung: x' = -w ... Koordinaten prüfen
        for i, p in enumerate(cs.to_polygons()):
            p = np.asarray(p)
            # rotate([0,90,0]): (u,v,w) -> (w, v, -u); Schnitt bei z=0 ⇒ u=0; Punkte (x=w, y=v)
            ax.add_patch(Polygon(np.c_[p[:,1], p[:,0]], closed=True, fc=col, ec="k", lw=0.4, alpha=0.9, label=lab if i == 0 else None))
    ax.set_xlim(18, 44); ax.set_ylim(-6.5, 3.8); ax.set_aspect("equal"); ax.invert_xaxis()
    ax.set_xlabel("Tiefe im Fach v [mm] (rechts = Deckel/Öffnung, links = Fachboden)"); ax.set_ylabel("w [mm]  (unten = Vorderwand)")
    ax.set_title(title, fontsize=10); ax.grid(alpha=0.25)
axes[0].legend(loc="upper right", fontsize=8)
axes[0].annotate("Nase: 1,5 mm hoch, 0,7 mm über der Kartenfläche", xy=(31.1, -1.0), xytext=(33.5, -6.1), fontsize=8, arrowprops=dict(arrowstyle="->"))
axes[0].annotate("Rille 0,9 mm tief, Auszugsflanke 30°", xy=(32.6, -1.2), xytext=(43.5, -5.6), fontsize=8, arrowprops=dict(arrowstyle="->"))
axes[0].annotate("Federzunge 1,4 mm", xy=(22, -3.2), xytext=(22.5, -4.9), fontsize=8, arrowprops=dict(arrowstyle="->"))
axes[0].annotate("Einführfase 30°", xy=(41.8, -1.2), xytext=(43.5, -4.2), fontsize=8, arrowprops=dict(arrowstyle="->"))
axes[0].annotate("Fachboden", xy=(42.5, 0), xytext=(43.8, 3.2), fontsize=8, arrowprops=dict(arrowstyle="->"))
plt.tight_layout(); plt.savefig("out/rastung_schnitt.png", dpi=150)
print("ok")
