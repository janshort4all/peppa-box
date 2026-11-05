"""Bild zum Frontgitter mit Logo (Stand 05.11.2026): Ansichten, Schnitt durch Logo und Luftraum, Lage auf der Druckplatte.
Aufruf: python3 v4/gitter/render_gitter.py  →  v4/out/gitter_ansicht.png"""
import os as _os
ROOT2 = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, io
sys.path.insert(0, _os.path.join(ROOT2, "v4")); sys.path.insert(0, _os.path.join(ROOT2, "v3"))
import model as M
import check as K
from concept3 import render
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly

OR, BE, DK, BG = (232, 119, 46), (236, 224, 202), (40, 38, 36), (245, 241, 234)
parts = M.build(); ph = M.placeholders()
gb, go = parts["gitter_beige"], parts["gitter_logo"]
spk = ph["Lautsprecher"]

ext = [(parts["korpus"], BE, None), (parts["deckel_orange"], OR, None), (parts["deckel_beige"], BE, None),
       (parts["drehknopf"], OR, None), (parts["ein_taste"], OR, None), (M.karte_world(), OR, None),
       (gb, BE, None), (go, OR, None), (spk, DK, None)]
persp = render(ext, 18, -32, size=760, scale=2.55, center=(70, 70, 78))
front = render([(parts["korpus"], BE, None), (gb, BE, None), (go, OR, None), (spk, DK, None)], 0, 0, size=620, scale=2.55, center=(70, 70, 70))

# Druckplatte: so liegt das Gitter (Ansicht von oben, Rückseite oben, Logo unten an der Platte)
ref = gb + go
B, O = M.gitter_druck(gb, ref), M.gitter_druck(go, ref)
bed = render([(B, BE, None), (O, OR, None)], 90, 0, size=430, scale=2.9, center=(57.7, 57.9, 3), light=(-0.3, 0.4, 0.9))

# Schnitt bei x = 50 (durch P/e-Bereich nicht nötig: x = 47 trifft „e“ und den Luftraum), von links gesehen
X = 47.0
def section(m):
    cs = m.rotate([0, -90, 0]).slice(X)          # (x,y,z) → Höhe = x
    return [list(p) for p in cs.to_polygons()]
fig, axs = plt.subplots(1, 2, figsize=(7.0, 6.6), dpi=110)
secs = [(m, col, lab, section(m)) for m, col, lab in ((parts["korpus"], "#e4d8c2", "Korpus"), (gb, "#efe3cc", "Gitter beige"),
                                                      (go, "#e8772e", "Logo orange"), (spk, "#3a3836", "Lautsprecher"))]
for ax, (z0, z1), title in zip(axs, ((98, 131), (60, 93)), ("oben: schräge Oberkante, Rand", "Mitte: Logo vor dem Lautsprecher")):
    for m, col, lab, polys in secs:
        for i, poly in enumerate(polys):
            pts = [(q[1], -q[0]) for q in poly]      # rotate([0,-90,0]): (x,y,z) → (−z, y, x); Punkt (−z, y) → (y, z)
            ax.add_patch(MPoly(pts, closed=True, fc=col, ec="#6b6259", lw=0.4, label=lab if i == 0 else None))
    ax.set_xlim(-1.5, 12); ax.set_ylim(z0, z1); ax.set_aspect("equal"); ax.set_title(title, fontsize=9)
    ax.set_xlabel("Tiefe ab Front (mm)", fontsize=8); ax.tick_params(labelsize=7)
axs[0].set_ylabel("Höhe (mm)", fontsize=8)
axs[1].legend(loc="lower right", fontsize=7)
axs[1].annotate("Luftraum\n2,5 mm", xy=(3.9, 66), xytext=(9.9, 70), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
axs[1].annotate("Logo 0,8 mm\nbündig", xy=(0.6, 80), xytext=(3.5, 86), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
fig.suptitle(f"Schnitt bei x = {X:g} mm, von links (vorne ist links)", fontsize=10)
buf = io.BytesIO(); fig.tight_layout(); fig.savefig(buf, format="png"); plt.close(fig)
sec = Image.open(buf).convert("RGB")

g = K.gitter_pruefung(parts)
cv = Image.new("RGB", (1560, 1560), BG)
cv.paste(persp, (0, 60)); cv.paste(front, (800, 120))
cv.paste(sec, (20, 790)); cv.paste(bed, (830, 960))
d = ImageDraw.Draw(cv)
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
d.text((30, 18), "Frontgitter mit Logo – Gitter beige, Logo orange bündig eingelegt", fill=(50, 44, 38), font=FB)
d.text((820, 90), "von vorne", fill=(70, 62, 54), font=F)
d.text((800, 880), "auf der Druckplatte (von oben): Logo unten an der Platte,", fill=(70, 62, 54), font=F)
d.text((800, 906), "Oberkante des Gitters hinten → Naht „Rückseite“ oben in jedem Loch", fill=(70, 62, 54), font=F)
d.text((30, 1500), f"{g['loecher']} Löcher Ø {M.GR_HOLE[0]:g} im Wabenraster {M.GR_HOLE[1]:g} (Steg 0,9) · Gitter {M.GR_T:g} mm, über der Mulde {M.GR_T - M.GR_PLENUM:g} mm · 6 Stifte Ø {M.GR_PIN_D:g}".replace(".", ","), fill=(90, 82, 74), font=F)
d.text((30, 1528), f"offen direkt vor dem Lautsprecher {g['offen_direkt']:.0f} %, mit Luftraum dahinter {g['offen_mulde']:.0f} % der Öffnung · Logo nur in Schicht 1–4", fill=(90, 82, 74), font=F)
p = _os.path.join(ROOT2, "v4/out/gitter_ansicht.png")
cv.save(p); print(p)
