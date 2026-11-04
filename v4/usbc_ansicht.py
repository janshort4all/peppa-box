"""USB-C hinten: Seitenschnitt und Ansicht von außen – warum die Öffnung so groß wie das Steckergehäuse sein muss
und warum man unter der Buchse die Platinenkante sieht. Maße aus model.py (USBC, USBC_PLUG), Steckergehäuse gemessen (Jan 04.11.)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import model as M

GEH = (10.0, 6.0)          # Steckergehäuse Jan 04.11. (B × H)
SHELL = (8.25, 2.4)        # Metallhülse Stecker, USB-C-Norm
ALT = (13.0, 7.0, 3.0)     # Öffnung bis 04.11.

u = M.USBC
x0, zc = u["x"], u["z"]
pcb_top = zc - u["buchse_h"] / 2
pcb_bot = pcb_top - u["pcb_t"]
face = M.W - M.FUZZ_REC                      # Oberfläche Anschlussfeld (y)
inner = M.W - M.WALL                         # Wand innen (y)
mouth = inner - u["spalt"]                   # Buchsenmund
b, h, r = M.USBC_PLUG


def rbox(ax, x, z, w, hh, rr, **kw):
    ax.add_patch(FancyBboxPatch((x - w / 2 + rr, z - hh / 2 + rr), w - 2 * rr, hh - 2 * rr,
                                boxstyle=f"round,pad={rr}", **kw))


fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.6), dpi=120, gridspec_kw=dict(width_ratios=[1, 1.15]))

# --- Seitenschnitt durch die Buchsenmitte (Blick von rechts, außen = rechts) ---
a1.add_patch(Rectangle((inner, 45), face - inner, zc - h / 2 - 45, fc="#e8dcc4", ec="#7a6a50"))
a1.add_patch(Rectangle((inner, zc + h / 2), face - inner, 75 - zc - h / 2, fc="#e8dcc4", ec="#7a6a50"))
a1.add_patch(Rectangle((mouth - 22, pcb_bot), 22, u["pcb_t"], fc="#3a5a40", ec="k", lw=0.6))
a1.add_patch(Rectangle((mouth - 7.3, pcb_top), 7.3, u["buchse_h"], fc="#b8b8b8", ec="k", lw=0.6))
a1.add_patch(Rectangle((mouth, zc - GEH[1] / 2), face + 6 - mouth, GEH[1], fc="none", ec="#d62728", lw=1.6, ls="--"))
a1.add_patch(Rectangle((mouth - 6.2, zc - SHELL[1] / 2), 6.2, SHELL[1], fc="none", ec="#d62728", lw=1.0, ls=":"))
a1.annotate("", (mouth, 53.2), (face, 53.2), arrowprops=dict(arrowstyle="<->", color="#d62728"))
a1.text((mouth + face) / 2, 52.4, f"{face - mouth:.1f} mm", color="#d62728", ha="center", va="top", fontsize=9)
a1.text(face + 0.4, zc + GEH[1] / 2 + 0.6, "Steckergehäuse 10 × 6\nmuss bis zur Buchse\nin die Wand", color="#d62728", fontsize=8.5, va="bottom")
a1.text(mouth - 11, pcb_bot - 0.6, "Platine", ha="center", va="top", fontsize=9, color="#3a5a40")
a1.text(mouth - 3.6, pcb_top + u["buchse_h"] + 0.4, "Buchse", ha="center", va="bottom", fontsize=9)
a1.text(inner + 1.3, 46, "Rückwand", ha="center", fontsize=8.5, rotation=90, va="bottom")
a1.set_xlim(mouth - 14, face + 7); a1.set_ylim(48, 72); a1.set_aspect("equal")
a1.set_xlabel("Tiefe y (mm), außen rechts"); a1.set_ylabel("Höhe z (mm)")
a1.set_title("Schnitt durch die Buchse", fontsize=11); a1.grid(alpha=0.25)

# --- Ansicht von außen ---
a2.add_patch(Rectangle((x0 - 14, 50), 28, 20, fc="#e8dcc4", ec="none"))
rbox(a2, x0, zc, ALT[0], ALT[1], ALT[2], fc="none", ec="#999", lw=1.2, ls="--")
rbox(a2, x0, zc, b, h, r, fc="#2b2b2b", ec="#7a6a50", lw=1.4)
a2.add_patch(Rectangle((x0 - b / 2 + 0.3, pcb_bot), b - 0.6, u["pcb_t"], fc="#3a5a40", ec="none"))
rbox(a2, x0, zc, u["buchse_b"], u["buchse_h"], 1.4, fc="#c9c9c9", ec="#555", lw=1)
rbox(a2, x0, zc, 7.0, 1.6, 0.7, fc="#111", ec="none")
a2.add_patch(Rectangle((x0 - GEH[0] / 2, zc - GEH[1] / 2), GEH[0], GEH[1], fc="none", ec="#d62728", lw=1.5, ls="--"))
a2.text(x0, zc + ALT[1] / 2 + 0.5, "bisher 13 × 7", ha="center", va="bottom", color="#777", fontsize=9)
a2.text(x0 + b / 2 + 0.4, zc + h / 2 - 0.3, f"neu {b:.1f} × {h:.1f}", ha="left", va="top", fontsize=9)
a2.text(x0 + GEH[0] / 2 + 0.4, zc - GEH[1] / 2 + 0.2, "Steckergehäuse\n10 × 6", color="#d62728", ha="left", va="bottom", fontsize=8.5)
a2.annotate("Platinenkante\n(sichtbar)", (x0 - 3, pcb_bot + 0.8), (x0 - 12, 52.2), fontsize=8.5, color="#3a5a40",
            arrowprops=dict(arrowstyle="->", color="#3a5a40"))
a2.set_xlim(x0 - 14, x0 + 14); a2.set_ylim(51, 69); a2.set_aspect("equal")
a2.set_xlabel("x (mm)"); a2.set_title("Ansicht von außen", fontsize=11); a2.grid(alpha=0.25)

fig.suptitle("USB-C: Das Steckergehäuse muss in die Wand eintauchen – deshalb ist die Öffnung so groß wie das Gehäuse", fontsize=11.5)
fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "usbc_ansicht.png")
fig.savefig(out, bbox_inches="tight")
print(out)
