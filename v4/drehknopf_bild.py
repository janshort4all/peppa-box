"""Schnittbild Drehknopf auf der ungekürzten Drehgeberachse → out/drehknopf_schnitt.png"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "v3"))
import model as M
from concept3 import render
from PIL import Image, ImageDraw, ImageFont

OR, BE, ME, DK, TX = (232, 119, 46), (230, 218, 196), (170, 170, 172), (90, 90, 92), (60, 55, 50)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
W, Y, Z = M.W, M.ENC_Y, M.ENC_Z
SZ, SC = 1000, 14.0
CX = W + 21.0


def px(x, z):
    return ((x - CX) * SC + SZ / 2, -(z - Z) * SC + SZ / 2)


def teile():
    """Knopf, Achse mit Schlitz, Gewinde, Mutter (vereinfacht rund), Wandstück mit glatter Fläche – vordere Hälfte weggeschnitten."""
    tip = W + M.ENC_OUT
    inner = W - M.FUZZ_REC - M.ENC_WALL
    shaft = M.cyl_x(inner, tip, Y, Z, 3.0) - M.box(tip - M.ENC_SLOT_D, Y - 4, Z - M.ENC_SLOT / 2, tip + 1, Y + 4, Z + M.ENC_SLOT / 2)
    thread = M.cyl_x(inner, inner + M.ENC_THREAD, Y, Z, 3.5)
    nut = M.cyl_x(W - M.FUZZ_REC, W - M.FUZZ_REC + M.ENC_NUT[0], Y, Z, 5.75)
    wall = (M.box(W - M.WALL, Y - 24, Z - 24, W, Y + 24, Z + 24) - M.cyl_x(W - M.FUZZ_REC, W + 1, Y, Z, M.ENC_SPOT / 2)
            - M.cyl_x(W - 4, W + 1, Y, Z, M.ENC_HOLE / 2))
    cut = M.box(W - 10, Y - 40, Z - 40, W + 40, Y, Z + 40)
    return [(p - cut, c, None) for p, c in ((wall, BE), (M.drehknopf(), OR), (shaft, ME), (thread, DK), (nut, ME))]


def mass(d, xa, xb, zz, txt, oben):
    p, q = px(xa, zz), px(xb, zz)
    d.line([p, q], fill=TX, width=2)
    for u in (p, q):
        d.line([(u[0], u[1] - 7), (u[0], u[1] + 7)], fill=TX, width=2)
    w = d.textlength(txt, font=F)
    d.text(((p[0] + q[0]) / 2 - w / 2, p[1] - 30 if oben else p[1] + 8), txt, font=F, fill=TX)


def zeiger(d, x, z, tx, tz, txt):
    a, b = px(x, z), px(tx, tz)
    d.line([a, b], fill=TX, width=2)
    d.text((b[0] + 6, b[1] - 12), txt, font=F, fill=TX)


def main():
    x0, rec, bore, x1 = M.knob_geo()
    tip = W + M.ENC_OUT
    sb = tip - M.ENC_SLOT_D
    im = render(teile(), 0, 0, size=SZ, scale=SC, center=(CX, Y, Z), light=(0.3, -0.8, 0.5))
    d = ImageDraw.Draw(im)
    f = lambda v: f"{v:.1f}".replace(".", ",")
    mass(d, x0, x1, Z + 19.5, f"Knopf {f(x1 - x0)}", True)
    mass(d, W, x1, Z - 19.5, f"{f(x1 - W)} ab Wand", False)
    mass(d, W - M.FUZZ_REC, tip, Z - 7.5, f"Achse {f(tip - W + M.FUZZ_REC)} ab Mutterauflage", False)
    mass(d, sb, tip, Z + 7.5, f"Schlitz {f(M.ENC_SLOT_D)}", True)
    zeiger(d, (rec + sb) / 2, Z + 3.15, W + 27, Z + 12.0, f"Führung Ø {f(M.KNOB_GUIDE)}")
    zeiger(d, bore - 2, Z - 3.05, W + 27, Z - 12.0, f"Klemmsitz Ø {f(M.KNOB_BORE)}")
    zeiger(d, bore - M.KNOB_RIB / 2, Z, W + 27, Z + 2.0, f"Steg {f(M.KNOB_RIB)} im Schlitz")
    im = im.crop((0, 200, SZ, SZ - 80))                                  # leeren Rand oben/unten abschneiden
    cv = Image.new("RGB", (SZ + 40, im.height + 150), (245, 241, 234))
    cv.paste(im, (20, 70))
    dd = ImageDraw.Draw(cv)
    dd.text((24, 18), "Drehknopf auf der ungekürzten Achse (Schnitt, von vorn)", font=FB, fill=TX)
    dd.text((24, im.height + 80), "Bis Anschlag aufschieben: Achsende liegt am Knopfboden, 1 mm Luft zur Wand.", font=F, fill=TX)
    dd.text((24, im.height + 110), "grau = Achse, Mutter (vereinfacht rund), dunkel = Gewinde, beige = Seitenwand", font=F, fill=TX)
    out = os.path.join(ROOT, "v4/out/drehknopf_schnitt.png")
    cv.save(out)
    print(out)


if __name__ == "__main__":
    main()
