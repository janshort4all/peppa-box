"""Bilder zu den Gummiecken (Nachtrag 09.11.2026, verschraubte Fassung).

out/gummiecken_ansicht.png   – Box mit Gummiecken, Ecke nah, Ecken mit Hülsen von unten
out/gummiecken_schnitt.png   – Schnitte: Seite (V-Fuge), vorne (Stufe, Korpus ohne Fase), durch die Eckschraube (Hülse)
out/gummiecken_varianten.png – Formvarianten A/B/C

Geometrie von Korpus und Boden aus den gedruckten STL-Dateien (out/01, out/05).
"""
import os, sys, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely import make_valid
from PIL import Image, ImageDraw, ImageFont
from manifold3d import Manifold, Mesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "v3"))
import model as M
from concept3 import render

OUT = os.path.join(HERE, "out")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BEIGE, ORANGE, DUNKEL = (230, 218, 196), (232, 119, 46), (60, 60, 64)
HUELSE, STAHL = (196, 92, 30), (150, 150, 155)


def stl(name, dz=0.0):
    t = trimesh.load(os.path.join(OUT, name))
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                         tri_verts=np.asarray(t.faces, np.uint32))).translate([0, 0, dz])


def gedruckt():
    """Korpus und Boden in Einbaulage, wie gedruckt (STL)."""
    return stl("01_korpus_beige.stl", M.BASE_T), stl("05_boden_traeger.stl")


# ---------------- Ansicht ----------------
def ansicht(rahmen, korpus, boden):
    lid_o, lid_b = M.deckel()
    gr_b, gr_o = M.gitter()
    ph = M.placeholders()
    box = [(korpus, BEIGE, None), (boden, BEIGE, None), (lid_o, ORANGE, None), (lid_b, BEIGE, None),
           (gr_b, BEIGE, None), (gr_o, ORANGE, None), (ph["Lautsprecher"], DUNKEL, None),
           (M.drehknopf(), ORANGE, None), (M.taste(), ORANGE, None), (M.karte_world(), ORANGE, None),
           (M.einleger_world(), (62, 132, 140), None)]
    teile = box + [(rahmen, ORANGE, None)]
    a = render(teile, 18, -36, size=1000, scale=3.0, center=(70, 70, 66))
    nah_cut = M.box(65, -10, -10, 150, 75, 60)                      # nur zum Beschleunigen; Ausschnitt liegt außerhalb des Bildes
    nah = [(m ^ nah_cut, c, t) for (m, c, t) in teile]
    b = render(nah, 12, -45, size=620, scale=6.0, center=(M.W - 14, 14, -6), light=(-0.45, -0.75, 0.6))
    unten = [(rahmen, ORANGE, None), (M.eckhuelsen(), HUELSE, None)] + [(M._an_ecke(M.eck_schraube(), k), STAHL, None) for k in range(4)]
    c = render(unten, -55, -30, size=620, scale=2.5, center=(70, 70, 0), light=(-0.3, -0.5, -0.9))
    W_, H_ = 1680, 1340
    cv = Image.new("RGB", (W_, H_), (245, 241, 234))
    cv.paste(a, (0, 70)); cv.paste(b, (1040, 110)); cv.paste(c, (1040, 720))
    d = ImageDraw.Draw(cv)
    ft, fs = ImageFont.truetype(FONTB, 32), ImageFont.truetype(FONT, 20)
    d.text((36, 22), "Peppa Box – Gummiecken mit Füßen (TPU orange, verschraubt)", fill=(50, 44, 38), font=ft)
    d.text((1060, 72), "Ecke vorne rechts: Schuh über Boden und Fuge", fill=(110, 100, 90), font=fs)
    d.text((1060, 712), "Von unten: 4 Ecken, Hülsen und Schrauben 3,0 × 16", fill=(110, 100, 90), font=fs)
    notizen = [f"Eckschuh an der Ecke {M.ECK_H[0]:g} mm, an den Schenkelenden {M.ECK_H[1]:g} mm hoch (ab Bodenunterseite); "
               f"Fuß {M.ECK_FUSS:g} mm: Box steht nur auf den Ecken",
               f"Wand {M.ECK_WAND:g} mm, Schenkel {M.ECK_SCHENKEL:g} mm über die Rundung hinaus, oben gerundet",
               f"Jede Ecke an der Eckschraube des Bodens: Senkschraube 3,0 × {M.ECK_SCHRAUBE:g} durch eine PETG-Hülse im Fuß, "
               "dazu Rastwulst unter der Fuge"]
    import textwrap
    y = 1100
    for n in notizen:
        for i, z in enumerate(textwrap.wrap(n, 84)):
            d.text((40, y), ("– " if i == 0 else "  ") + z, fill=(70, 62, 54), font=fs); y += 28
        y += 6
    p = os.path.join(OUT, "gummiecken_ansicht.png")
    cv.save(p)
    return p


# ---------------- Schnitt ----------------
def shp(cs):
    g = None
    for p in cs.to_polygons():
        p = np.asarray(p)
        if len(p) < 3:
            continue
        q = make_valid(Polygon(p))
        g = q if g is None else g.symmetric_difference(q)
    return g


def fill(ax, g, flip, **kw):
    if g is None:
        return
    for poly in (g.geoms if hasattr(g, "geoms") else [g]):
        if poly.geom_type != "Polygon":
            continue
        ex = np.asarray(poly.exterior.coords)
        ax.fill(*flip(ex), **kw)
        for h in poly.interiors:
            ax.fill(*flip(np.asarray(h.coords)), color="white")


def schnitt(rahmen, korpus, boden):
    fig, axs = plt.subplots(1, 3, figsize=(19, 6.4), dpi=130)
    faelle = [("Seite links, Schnitt y = 20 mm: V-Fuge (Boden- und Korpusfase)", "y", 20.0),
              ("Vorne, Schnitt x = 20 mm: Stufe (Korpus vorne ohne Fase)", "x", 20.0)]
    for ax, (titel, eb, v) in zip(axs[:2], faelle):
        for m, kw in ((korpus, dict(color="#e3d5b8", ec="#7a6a50", lw=0.6)), (boden, dict(color="#d9c7a3", ec="#7a6a50", lw=0.6)),
                      (rahmen, dict(color="#e8772e", ec="#9a4a14", lw=0.6))):
            if eb == "y":
                g = shp(m.rotate([90, 0, 0]).slice(v))        # Ebene y = v: Punkte (x, −z)
                fill(ax, g, lambda p: (p[:, 0], -p[:, 1]), **kw)
            else:
                g = shp(m.rotate([0, -90, 0]).slice(v))       # Ebene x = v: Punkte (−z, y)
                fill(ax, g, lambda p: (p[:, 1], -p[:, 0]), **kw)
        ax.set_xlim(-4, 14); ax.set_ylim(-4, 12); ax.set_aspect("equal"); ax.grid(alpha=0.3)
        ax.set_title(titel, fontsize=10)
        ax.set_xlabel(("x" if eb == "y" else "y") + " (mm), außen links")
        ax.axhline(0, color="#555", lw=0.6, ls=":")
        ax.text(6, -0.6, "Bodenunterseite (z 0)", fontsize=8, color="#555")
        ax.text(6.5, 1.8, "Boden", fontsize=9, color="#5a4a30")
        ax.text(6.5, 8, "Korpus", fontsize=9, color="#5a4a30")
        ax.text(-3.6, -2.4, "Fuß", fontsize=9, color="white")
        ax.annotate("Rastwulst", xy=(0.25, M.BASE_T - 0.35), xytext=(3, M.BASE_T + 2.6), fontsize=9,
                    arrowprops=dict(arrowstyle="->", color="#9a4a14"), color="#9a4a14")
    # drittes Bild: durch die Eckschraube (Ebene x = 8,6), Hülse und Schraube
    ax = axs[2]
    x0, y0 = M.BASE_BOSSES[0]
    for m, kw in ((korpus, dict(color="#e3d5b8", ec="#7a6a50", lw=0.6)), (boden, dict(color="#d9c7a3", ec="#7a6a50", lw=0.6)),
                  (rahmen, dict(color="#e8772e", ec="#9a4a14", lw=0.6)), (M.eckhuelse(), dict(color="#c45c1e", ec="#5a2a0a", lw=0.8)),
                  (M.eck_schraube(), dict(color="#9a9aa0", ec="#444", lw=0.6))):
        g = shp(m.rotate([0, -90, 0]).slice(x0))
        fill(ax, g, lambda p: (p[:, 1], -p[:, 0]), **kw)
    ax.set_xlim(-4, 22); ax.set_ylim(-4, 20); ax.set_aspect("equal"); ax.grid(alpha=0.3)
    ax.set_title(f"Durch die Eckschraube (x = {x0:g} mm): Hülse und Schraube 3,0 × {M.ECK_SCHRAUBE:g}", fontsize=10)
    ax.set_xlabel("y (mm), außen links")
    ax.axhline(0, color="#555", lw=0.6, ls=":")
    ax.annotate("PETG-Hülse", xy=(y0 + 4.0, -1.8), xytext=(13.5, -3.3), fontsize=9, color="#5a2a0a",
                arrowprops=dict(arrowstyle="->", color="#5a2a0a"))
    ax.text(y0 + 2.2, 9, "Dom", fontsize=9, color="#5a4a30")
    ax.text(15.5, 1.8, "Boden", fontsize=9, color="#5a4a30")
    axs[0].set_ylabel("Höhe z (mm)")
    fig.suptitle("Gummiecke im Schnitt (so, wie sie sitzt). Der Wulst hakt unter die Korpus-Unterkante "
                 f"(Wulst {M.ECK_WULST:g} mm); die Schraube drückt nur auf die Hülse, die Hülse auf den Boden", fontsize=11)
    p = os.path.join(OUT, "gummiecken_schnitt.png")
    fig.savefig(p, bbox_inches="tight")
    return p


def box_teile(korpus, boden):
    lid_o, lid_b = M.deckel()
    gr_b, gr_o = M.gitter()
    ph = M.placeholders()
    return [(korpus, BEIGE, None), (boden, BEIGE, None), (lid_o, ORANGE, None), (lid_b, BEIGE, None),
            (gr_b, BEIGE, None), (gr_o, ORANGE, None), (ph["Lautsprecher"], DUNKEL, None), (M.drehknopf(), ORANGE, None)]


def varianten(korpus, boden, liste=((10.0, 10.0), (16.0, 8.0), (20.0, 8.0))):
    """Höhenvarianten nebeneinander (vorne links, untere Hälfte)."""
    alt = M.ECK_H
    teile = box_teile(korpus, boden) + [(M.taste(), ORANGE, None), (M.karte_world(), ORANGE, None),
                                        (M.einleger_world(), (62, 132, 140), None)]
    bilder = []
    for h in liste:
        M.ECK_H = h
        r = M.gummiecken()
        ganz = render(teile + [(r, ORANGE, None)], 16, -36, size=560, scale=1.75, center=(70, 70, 70))
        nah = render(teile + [(r, ORANGE, None)], 10, -45, size=560, scale=5.5, center=(M.W - 14, 14, 12), light=(-0.45, -0.75, 0.6))
        bilder.append((ganz, nah))
    M.ECK_H = alt
    cv = Image.new("RGB", (560 * len(liste), 1220), (245, 241, 234))
    d = ImageDraw.Draw(cv)
    ft, fs = ImageFont.truetype(FONTB, 24), ImageFont.truetype(FONT, 19)
    for i, (h, (ganz, nah)) in enumerate(zip(liste, bilder)):
        cv.paste(ganz, (560 * i, 60))
        cv.paste(nah, (560 * i, 620))
        name = "flach" if h[0] == h[1] else "geschwungen"
        wahl = "  (gewählt)" if tuple(h) == tuple(alt) else ""
        d.text((560 * i + 24, 18), f"{chr(65 + i)}: {name} {h[0]:g} / {h[1]:g} mm{wahl}", fill=(50, 44, 38), font=ft)
    d.text((24, 1186), "Höhe an der Ecke / an den Schenkelenden, ab Bodenunterseite (dazu 3 mm Fuß). Vorne begrenzt der Gittersitz.",
           fill=(110, 100, 90), font=fs)
    p = os.path.join(OUT, "gummiecken_varianten.png")
    cv.save(p)
    return p


if __name__ == "__main__":
    k, b = gedruckt()
    r = M.gummiecken()
    print(schnitt(r, k, b))
    if "--nur-schnitt" not in sys.argv:
        print(ansicht(r, k, b))
    if "--varianten" in sys.argv:
        print(varianten(k, b))
