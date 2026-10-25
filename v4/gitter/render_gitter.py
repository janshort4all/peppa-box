import os as _os
ROOT2 = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import sys, math
sys.path.insert(0, _os.path.join(ROOT2, "v4")); sys.path.insert(0, _os.path.join(ROOT2, "v3"))
import model as M
from manifold3d import CrossSection, Manifold
from concept3 import render
from PIL import Image, ImageDraw, ImageFont
from logo import logo_cs

OR, BE, DK = (232, 119, 46), (236, 224, 202), (40, 38, 36)
sx0, sx1, sz0, sz1 = M.SEAT
m = M.CLR
x0, x1, z0, z1 = sx0 + m, sx1 - m, sz0 + m, sz1 - m
outer = M.rr(x0, z0, x1, z1, M.SEAT_R - m)
LOGO_Z = 76.0
logo = logo_cs(100).translate([70, LOGO_Z])
keep = logo.offset(1.4)
inner = M.rr(x0 + 4.5, z0 + 4.5, x1 - 4.5, z1 - 4.5, 5)
P, D = 4.0, 3.2
holes = []
row = 0
z = z0 + 4.5 + D / 2
while z < z1 - 4.5:
    off = (P / 2) if row % 2 else 0
    x = x0 + 4.5 + D / 2 + off
    while x < x1 - 4.5:
        holes.append(CrossSection.circle(D / 2, 20).translate([x, z]))
        x += P
    z += P * math.sqrt(3) / 2; row += 1
hcs = CrossSection.batch_boolean(holes, __import__("manifold3d").OpType.Add) ^ inner.offset(-0.5)
hcs = hcs - keep
grille = outer - hcs
plate = M.ext_xz(grille, 0.1, 3.7)
inlay = M.ext_xz(logo, 0.1, 0.7)
plate_rest = plate - inlay
open_frac = hcs.area() / outer.area()
print("offene Fläche", round(open_frac * 100), "%")

parts = M.build(); ph = M.placeholders()
base = [(parts["korpus"], BE, None), (parts["deckel_orange"], OR, None), (parts["deckel_beige"], BE, None),
        (parts["drehknopf"], OR, None), (parts["ein_taste"], OR, None), (M.karte_world(), OR, None),
        (ph["Lautsprecher"], DK, None)]
A = base + [(plate_rest, OR, None), (inlay, BE, None)]
B = base + [(plate, OR, None)]
ra = render(A, 18, -32, size=760, scale=2.55, center=(70, 70, 78))
rb = render(B, 18, -32, size=760, scale=2.55, center=(70, 70, 78))
fa = render([(parts["korpus"], BE, None), (plate_rest, OR, None), (inlay, BE, None), (ph["Lautsprecher"], DK, None)], 0, 0, size=560, scale=2.3, center=(70, 70, 70))
cv = Image.new("RGB", (1560, 1420), (245, 241, 234))
cv.paste(ra, (0, 70)); cv.paste(rb, (790, 70)); cv.paste(fa, (500, 850))
d = ImageDraw.Draw(cv)
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 21)
d.text((30, 18), "Gedrucktes Gitter mit Logo – zwei Varianten", fill=(50, 44, 38), font=FB)
d.text((40, 80), "A: Gitter orange, Logo beige eingelegt", fill=(70, 62, 54), font=F)
d.text((830, 80), "B: alles orange, Logo als geschlossene Fläche", fill=(70, 62, 54), font=F)
d.text((560, 860), "A von vorne", fill=(70, 62, 54), font=F)
d.text((30, 1380), f"Löcher Ø 3,2 mm im Wabenraster 4,0 mm · offene Fläche ca. {round(open_frac*100)} % · Gitter 3,6 mm dick, mit Stiften gesteckt", fill=(90, 82, 74), font=F)
cv.save(_os.path.join(ROOT2, "v4/out/gitter_logo_varianten.png"))
