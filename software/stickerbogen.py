#!/usr/bin/env python3
"""Stickerbogen für den Freiform-Sticker an der CEWE-Fotostation (dm), Bogen 9 × 14 cm.

Legt quadratische Cover auf transparenten Hintergrund in einem Bild mit dem Seitenverhältnis
des Bogens (90 : 140). Füllt die Station den Bogen mit dem Bild aus, hat jedes Quadrat seine
Sollgröße; die Station erkennt die Motive und schneidet sie entlang der Kontur aus.

Belegt: Bogenfläche 9 × 14 cm, freigestellte Motive (weißer oder transparenter Hintergrund),
mehrere Motive pro Bogen, Dateiformate JPEG/PNG/HEIC. NICHT belegt: ob die Station das Bild
formatfüllend und ohne Skalierung druckt, welchen Abstand sie zwischen den Motiven und zum Rand
braucht und wie genau sie schneidet. Deshalb zuerst den Testbogen drucken und nachmessen.

Aufruf:
  python3 stickerbogen.py --test testbogen_60mm.png             # Testbogen mit Messskala
  python3 stickerbogen.py --groesse 42 --test testbogen_42mm.png
  python3 stickerbogen.py cover1.jpg cover2.jpg -o bogen.png      # echte Cover
"""
import argparse
import sys

from PIL import Image, ImageDraw, ImageFont

BOGEN_MM = (90.0, 140.0)   # CEWE Freiform-Sticker, Druckfläche laut CEWE
DPI = 300
RAND_MM = 5.0              # Mindestabstand zum Bogenrand (Annahme, mit dem Testbogen prüfen)
ABSTAND_MM = 5.0           # Mindestabstand zwischen zwei Stickern (Annahme, mit dem Testbogen prüfen)
ORANGE = (232, 121, 43, 255)
BEIGE = (240, 228, 205, 255)


def px(mm):
    return int(round(mm / 25.4 * DPI))


def raster(groesse_mm):
    """Spalten, Zeilen und linke obere Ecken (mm) für quadratische Sticker, auf dem Bogen zentriert."""
    b, h = BOGEN_MM
    spalten = int((b - 2 * RAND_MM + ABSTAND_MM) // (groesse_mm + ABSTAND_MM))
    zeilen = int((h - 2 * RAND_MM + ABSTAND_MM) // (groesse_mm + ABSTAND_MM))
    if spalten < 1 or zeilen < 1:
        raise ValueError(f"{groesse_mm} mm passt nicht auf den Bogen {b:g} × {h:g} mm")
    breite = spalten * groesse_mm + (spalten - 1) * ABSTAND_MM
    hoehe = zeilen * groesse_mm + (zeilen - 1) * ABSTAND_MM
    x0, y0 = (b - breite) / 2, (h - hoehe) / 2
    ecken = [(x0 + s * (groesse_mm + ABSTAND_MM), y0 + z * (groesse_mm + ABSTAND_MM))
             for z in range(zeilen) for s in range(spalten)]
    return spalten, zeilen, ecken


def schrift(groesse_px, fett=True):
    namen = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if fett else ["DejaVuSans.ttf"]
    for name in namen:
        try:
            return ImageFont.truetype(name, groesse_px)
        except OSError:
            pass
    return ImageFont.load_default()


def teststicker(groesse_mm, nummer):
    """Orangefarbenes Quadrat mit Millimeterskala an zwei Kanten und einer 50-mm-Messlinie."""
    n = px(groesse_mm)
    img = Image.new("RGBA", (n, n), ORANGE)
    d = ImageDraw.Draw(img)
    for mm in range(0, int(groesse_mm) + 1, 5):          # Striche alle 5 mm, lang alle 10 mm
        lang = px(4 if mm % 10 == 0 else 2)
        x = min(px(mm), n - 2)
        d.line([(x, n - 1), (x, n - 1 - lang)], fill=BEIGE, width=3)   # unten
        d.line([(0, x), (lang, x)], fill=BEIGE, width=3)               # links
    linie = min(50.0, groesse_mm - 10.0)
    xa, xb, y = px((groesse_mm - linie) / 2), px((groesse_mm + linie) / 2), px(groesse_mm * 0.62)
    d.line([(xa, y), (xb, y)], fill=BEIGE, width=4)
    for x in (xa, xb):
        d.line([(x, y - px(2)), (x, y + px(2))], fill=BEIGE, width=4)
    f_gross, f_klein = schrift(px(groesse_mm * 0.11)), schrift(px(groesse_mm * 0.07), fett=False)
    d.text((n / 2, px(groesse_mm * 0.30)), f"TEST {groesse_mm:g} mm", font=f_gross, fill=BEIGE, anchor="mm")
    d.text((n / 2, px(groesse_mm * 0.45)), f"Sticker {nummer}", font=f_klein, fill=BEIGE, anchor="mm")
    d.text((n / 2, y + px(5)), f"Linie {linie:g} mm", font=f_klein, fill=BEIGE, anchor="mm")
    return img


def cover_quadrat(pfad, groesse_mm):
    """Cover mittig quadratisch zuschneiden und auf die Stickergröße bringen."""
    img = Image.open(pfad).convert("RGBA")
    k = min(img.size)
    links, oben = (img.width - k) // 2, (img.height - k) // 2
    img = img.crop((links, oben, links + k, oben + k))
    return img.resize((px(groesse_mm), px(groesse_mm)), Image.LANCZOS)


def bogen(sticker, groesse_mm):
    """Sticker-Bilder auf einen transparenten Bogen legen; gibt (Bild, Anzahl Plätze) zurück."""
    _, _, ecken = raster(groesse_mm)
    if len(sticker) > len(ecken):
        raise ValueError(f"{len(sticker)} Sticker, aber nur {len(ecken)} Plätze bei {groesse_mm:g} mm")
    bild = Image.new("RGBA", (px(BOGEN_MM[0]), px(BOGEN_MM[1])), (0, 0, 0, 0))
    for s, (x, y) in zip(sticker, ecken):
        bild.alpha_composite(s, (px(x), px(y)))
    return bild, len(ecken)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Stickerbogen für den CEWE Freiform-Sticker (9 × 14 cm)")
    ap.add_argument("cover", nargs="*", help="Cover-Bilder (JPEG/PNG)")
    ap.add_argument("-o", "--ausgabe", help="Ausgabedatei (PNG)")
    ap.add_argument("--test", metavar="DATEI", help="Testbogen mit Messskala schreiben")
    ap.add_argument("--groesse", type=float, default=60.0, help="Kantenlänge der Sticker in mm (Standard 60)")
    a = ap.parse_args(argv)
    spalten, zeilen, ecken = raster(a.groesse)
    if a.test:
        bild, plaetze = bogen([teststicker(a.groesse, i + 1) for i in range(len(ecken))], a.groesse)
        ziel = a.test
    elif a.cover and a.ausgabe:
        bild, plaetze = bogen([cover_quadrat(p, a.groesse) for p in a.cover], a.groesse)
        ziel = a.ausgabe
    else:
        ap.error("entweder --test DATEI oder Cover-Bilder mit -o DATEI angeben")
    bild.save(ziel, dpi=(DPI, DPI))
    print(f"{ziel}: {bild.width} × {bild.height} px ({BOGEN_MM[0]:g} × {BOGEN_MM[1]:g} mm bei {DPI} dpi), "
          f"{a.groesse:g} mm, {spalten} × {zeilen} = {plaetze} Plätze")
    return 0


if __name__ == "__main__":
    sys.exit(main())
