"""Erzeugt Druckdateien, Coupons, Renderings, Parameterliste und Prüfbericht für Musikbox v4."""
import os as _os
ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

import os, sys, io, json, zipfile, datetime, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, _os.path.join(ROOT, "v3"))
import model as M
import check as K
import coupons as C
from concept3 import render

OUT = _os.path.join(ROOT, "v4/out")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def tm(man):
    m = man.to_mesh()
    return trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts), process=False)


DRUCK = {   # Teil: (Datei, Farbe, Hinweis)
    "korpus": ("01_korpus_beige.stl", "Beige", "aufrecht, Boden auf der Platte; Naht hinten; Brücke Kammerdecke ca. 40 mm"),
    "deckel_orange": ("02a_deckel_kern_orange.stl", "Orange", "Oberseite nach oben; zusammen mit 02b als ein Objekt laden"),
    "deckel_beige": ("02b_deckel_haut_beige.stl", "Beige", "liegt passgenau auf 02a; Ironing an"),
    "deckelrahmen": ("03_deckelrahmen.stl", "Schwarz/Grau", "Deckelseite auf der Platte"),
    "kartenfach": ("04_kartenfach.stl", "Schwarz/Grau", "auf der Seite, Kartenschlitz senkrecht; Brim"),
    "boden": ("05_boden_traeger.stl", "Beige", "flach, Unterseite auf der Platte; trägt die ganze Elektronik"),
    "stoffrahmen": ("06_stoffrahmen.stl", "Beige", "Vorderseite unten, Stifte oben"),
    "drehknopf": ("07_drehknopf_orange.stl", "Orange", "Stirnfläche unten"),
    "ein_taste": ("08_ein_taste_orange.stl", "Orange", "Kopf unten"),
    "riemen_gegenplatte": ("09_riemen_gegenplatte.stl", "Schwarz/Grau", "flach"),
}


def export_parts(parts):
    files = {}
    for k, (fn, col, note) in DRUCK.items():
        if k in ("deckel_orange", "deckel_beige"):
            o = parts[k].translate([0, 0, -M.LID_BOT])          # beide Deckelteile gleich verschoben → deckungsgleich
        else:
            o = K.orient(k, parts[k])
        p = os.path.join(OUT, fn)
        tm(o).export(p)
        files[fn] = (k, col, note, o.bounding_box())
    # Karte
    card = M.karte_print()
    tm(card).export(os.path.join(OUT, "10_karte_orange.stl"))
    files["10_karte_orange.stl"] = ("karte", "Orange", "flach, NFC-Tasche oben", card.bounding_box())
    # Ansicht Zusammenbau (nicht drucken)
    ph = M.placeholders()
    asm = M.U([parts[k] for k in parts] + [M.karte_world()])
    tm(asm).export(os.path.join(OUT, "ansicht_zusammenbau_NICHT_DRUCKEN.stl"))
    tm(M.U(list(ph.values()))).export(os.path.join(OUT, "ansicht_bauteile_platzhalter_NICHT_DRUCKEN.stl"))
    return files


def export_coupons():
    files = {}
    for k, v in C.all_coupons().items():
        fn = f"coupon_{k}.stl"
        tm(v).export(os.path.join(OUT, fn))
        files[fn] = v.bounding_box()
    return files


# ---------------- Renderings ----------------
COL = {"beige": (230, 218, 196), "orange": (232, 119, 46), "fabric": (226, 211, 184), "dark": (52, 50, 48),
       "grey": (150, 150, 150), "pcb": (46, 120, 72), "ups": (40, 70, 140), "dac": (30, 90, 60), "spk": (60, 60, 64),
       "wago": (226, 228, 222), "rc": (40, 90, 170), "cover": (62, 132, 140), "frame": (205, 192, 168)}


def fabric_sheet():
    sx0, sx1, sz0, sz1 = M.SEAT
    m = M.CLR
    cs = M.rr(sx0 + m, sz0 + m, sx1 - m, sz1 - m, M.SEAT_R - m)
    env = M.Manifold.batch_hull([M.ext_xz(M.rr(sx0 + m, sz0 + m, sx1 - m, sz1 - m + 1, M.SEAT_R - m), -1, 0),
                                 M.ext_xz(M.rr(sx0 + m, sz0 + m, sx1 - m, sz1 - m - 3, M.SEAT_R - m), 2.0, 2.01)])
    return M.ext_xz(cs, M.SEAT_D - M.FR_T - M.FAB_T, M.SEAT_D - M.FR_T) ^ env


def card_cover():
    # Cover als dünne Fläche auf der Kartenvorderseite (sichtbarer Teil)
    a = M.to_world(M.box(-32, -(M.CARD_H - M.CARD_IN) + 3, -M.CARD_T / 2 + 0.4 - 0.3, 32, -(M.CARD_H - M.CARD_IN) + 67, -M.CARD_T / 2 + 0.4))
    return a


def renders(parts):
    ph = M.placeholders()
    lid = parts["deckel_orange"] + parts["deckel_beige"]
    ext = [(parts["korpus"], COL["beige"], None), (parts["deckel_orange"], COL["orange"], None), (parts["deckel_beige"], COL["beige"], None),
           (fabric_sheet(), COL["fabric"], "fabric"), (parts["drehknopf"], COL["orange"], None), (parts["ein_taste"], COL["orange"], None),
           (M.karte_world(), COL["orange"], None), (card_cover(), COL["cover"], None)]
    a = render(ext, 22, -36, size=1000, scale=3.0, center=(70, 70, 75))
    b = render(ext, 20, 150, size=620, scale=2.2, center=(70, 70, 78), light=(0.5, 0.7, 0.8))
    # Schnitt bei x = 70 (linke Hälfte entfernt)
    cut = M.box(40, -5, -5, 200, 200, 200)
    sect = [(parts["korpus"] ^ cut, COL["beige"], None), (lid ^ cut, COL["orange"], None),
            (parts["deckelrahmen"] ^ cut, COL["dark"], None), (parts["kartenfach"] ^ cut, COL["grey"], None),
            (parts["boden"] ^ cut, COL["beige"], None), (parts["stoffrahmen"] ^ cut, COL["frame"], None),
            (parts["ein_taste"], COL["orange"], None), (parts["drehknopf"], COL["orange"], None),
            (M.karte_world() ^ cut, COL["orange"], None)]
    pc = {"Akku-Board mit Zellen": "ups", "Pi + Klemmen-Aufsatz": "pcb", "Lautsprecher": "spk",
          "RC522": "rc", "Verstärker": "rc", "Touch-Modul MPR121": "rc", "Drehgeber": "grey", "Klinkenbuchse": "grey", "Kurzhubtaster": "dark",
          "USB-C-Einbaubuchse mit Kabel": "grey"}
    for k, c in pc.items():
        sect.append((ph[k] ^ cut, COL[c], None))
    for k in ph:
        if k.startswith("WAGO"):
            sect.append((ph[k] ^ cut, COL["wago"], None))
    s = render(sect, 6, 90, size=1000, scale=3.1, center=(70, 70, 76), light=(0.6, -0.3, 0.8))
    # Deckel von unten mit Rahmen, Kartenfach, Taster
    under = [(lid, COL["orange"], None), (parts["deckelrahmen"], COL["dark"], None), (parts["kartenfach"], COL["grey"], None),
             (ph["RC522"], COL["rc"], None), (ph["Kurzhubtaster"], COL["dark"], None), (parts["ein_taste"], COL["orange"], None),
             (ph["Touch-Modul MPR121"], COL["rc"], None)] + [(ph[k], COL["wago"], None) for k in ("WAGO GND B", "WAGO 3,3 V", "WAGO SCL")]
    u = render(under, -60, 20, size=620, scale=2.6, center=(70, 70, 120), light=(0.2, -0.5, -0.9))
    return a, b, s, u


def sheet(a, b, s, u):
    W_, H_ = 1700, 2120
    cv = Image.new("RGB", (W_, H_), (245, 241, 234))
    cv.paste(a, (0, 60)); cv.paste(b, (1060, 90)); cv.paste(u, (1060, 740))
    cv.paste(s, (0, 1080))
    d = ImageDraw.Draw(cv)
    ft, fs, fb = ImageFont.truetype(FONTB, 34), ImageFont.truetype(FONT, 21), ImageFont.truetype(FONTB, 22)
    d.text((40, 24), "Musikbox v4 – parametrisches Druckmodell (Stand mit Platzhaltern)", fill=(50, 44, 38), font=ft)
    d.text((1080, 76), "Hinten: USB-C-Buchse, Lüftung, Deckelschrauben", fill=(110, 100, 90), font=fs)
    d.text((1080, 726), "Deckel von unten: Verteiler-Brücke, Kartenfach, NFC", fill=(110, 100, 90), font=fs)
    d.text((40, 1090), "Schnitt bei x = 40 mm, von links gesehen (vorne ist rechts)", fill=(110, 100, 90), font=fs)
    d.text((40, 1116), "blau = Akku-Board und Module, grün = Pi mit Klemmen-Aufsatz, weiß = Hebelklemmen, dunkel = Lautsprecher", fill=(110, 100, 90), font=fs)
    notes = [
        "Würfel 140 × 140 × 140 mm; Boden 4 mm abnehmbar, Korpus steht darauf (Schattenfuge)",
        "Boden = Elektronikträger: Stapel, Klemmen und Verstärker sitzen darauf, Einbau von unten mit 6 Schrauben",
        "Lautsprecher vorne in geschlossener Kammer mit eigenem Boden, Stoffrahmen mit 6 Stiften",
        "Karte 70 × 112 mm, 42 mm tief im geschlossenen Fach, NFC-Leser direkt dahinter",
        "Unter dem Deckel: Touch-Modul und Klemmen für 3,3 V, SCL, GND B (kurze Wege)",
        "USB-C-Buchse hinten rechts; Drehknopf und Klinke rechts, Riemen links",
    ]
    y = 1400
    d.text((1070, y), "Festlegungen in diesem Stand", fill=(50, 44, 38), font=fb); y += 40
    import textwrap
    for n in notes:
        for i, line in enumerate(textwrap.wrap(n, 52)):
            d.text((1078, y), ("– " if i == 0 else "  ") + line, fill=(70, 62, 54), font=fs); y += 28
        y += 8
    p = os.path.join(OUT, "musikbox_v4_ansichten.png")
    cv.save(p)
    return p


if __name__ == "__main__":
    parts = M.build()
    pf = export_parts(parts)
    cf = export_coupons()
    print("export ok", len(pf), len(cf))
    if "--norender" not in sys.argv:
        a, b, s, u = renders(parts)
        print(sheet(a, b, s, u))
