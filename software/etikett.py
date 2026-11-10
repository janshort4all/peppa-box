"""Etiketten für die Karten: quadratisch, abgerundete Ecken, weißer Rand, transparenter Hintergrund.

Gedacht für den Freiform-Sticker an der Fotostation (dm/CEWE): Die Station erkennt freigestellte Motive und
schneidet an der Kontur. Standardgröße 40 × 40 mm (einstellbar in einstellungen.py, "etikett"), 300 dpi.

  etikett(bild, titel, einst)   ein Etikett als Bild (RGBA); ohne Cover entsteht ein oranges Namensschild
  png_bytes(bild)               PNG mit Auflösungsangabe (300 dpi), zum Herunterladen
  bogen(etiketten, einst)       mehrere Etiketten auf einen Bogen 90 × 140 mm (Seitenverhältnis des Freiform-Bogens)

Braucht Pillow (apt: python3-pil, steht in dienst_einrichten.sh). Fehlt es, meldet verfuegbar() False.
"""
import io
import os

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:                                       # Eltern-Seite zeigt dann einen Hinweis
    Image = None

import stickerbogen

DPI = stickerbogen.DPI
ORANGE = (232, 121, 43, 255)
BEIGE = (251, 246, 239, 255)
WEISS = (255, 255, 255, 255)
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "logo.png")
SCHRIFTEN = ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "LiberationSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
             "Arial Bold.ttf")


def verfuegbar():
    return Image is not None


def mm_px(mm, dpi=DPI):
    return int(round(mm / 25.4 * dpi))


def _runde_maske(n, radius_px, faktor=4):
    """Weich abgerundetes Quadrat n × n als Alphamaske (vierfach gezeichnet, dann verkleinert)."""
    gross = Image.new("L", (n * faktor, n * faktor), 0)
    ImageDraw.Draw(gross).rounded_rectangle([0, 0, n * faktor - 1, n * faktor - 1],
                                            radius=max(0, radius_px) * faktor, fill=255)
    return gross.resize((n, n), Image.LANCZOS)


def _schrift(groesse):
    for name in SCHRIFTEN:
        try:
            return ImageFont.truetype(name, groesse)
        except OSError:
            pass
    try:
        return ImageFont.load_default(groesse)           # Pillow >= 10.1: eingebaute skalierbare Schrift
    except TypeError:
        return ImageFont.load_default()


def _umbrechen(zeichner, text, schrift, breite):
    zeilen, aktuell = [], ""
    for wort in text.split():
        probe = (aktuell + " " + wort).strip()
        if aktuell and zeichner.textlength(probe, font=schrift) > breite:
            zeilen.append(aktuell)
            aktuell = wort
        else:
            aktuell = probe
    if aktuell:
        zeilen.append(aktuell)
    return zeilen


def _bild_oeffnen(daten):
    if not daten or Image is None:
        return None
    try:
        b = Image.open(io.BytesIO(daten))
        b.load()
        b = ImageOps.exif_transpose(b).convert("RGB")
    except Exception:                                     # kaputte oder fremde Datei: wie "kein Cover"
        return None
    return b if min(b.size) >= 16 else None


def _quadrat(b, n):
    k = min(b.size)
    links, oben = (b.width - k) // 2, (b.height - k) // 2
    return b.crop((links, oben, links + k, oben + k)).resize((n, n), Image.LANCZOS)


def _namensschild(n, titel):
    """Ohne Cover: oranges Feld mit dem Logo und dem Titel in Beige."""
    feld = Image.new("RGBA", (n, n), ORANGE)
    z = ImageDraw.Draw(feld)
    oben = int(n * 0.10)
    try:
        logo = Image.open(LOGO).convert("RGBA")
        breite = int(n * 0.62)
        logo = logo.resize((breite, int(logo.height * breite / logo.width)), Image.LANCZOS)
        beige = Image.new("RGBA", logo.size, BEIGE)
        beige.putalpha(logo.getchannel("A"))
        feld.alpha_composite(beige, ((n - breite) // 2, oben))
        oben += logo.height + int(n * 0.06)
    except OSError:
        pass
    text = (titel or "").strip()
    if text:
        platz_h, platz_b = n - oben - int(n * 0.08), int(n * 0.84)
        for groesse in range(int(n * 0.15), int(n * 0.06), -2):
            schrift = _schrift(groesse)
            zeilen = _umbrechen(z, text, schrift, platz_b)
            if len(zeilen) * groesse * 1.2 <= platz_h and all(z.textlength(l, font=schrift) <= platz_b for l in zeilen):
                break
        zeilen = zeilen[:max(1, int(platz_h // (groesse * 1.2)))]
        y = oben + (platz_h - len(zeilen) * groesse * 1.2) / 2
        for zeile in zeilen:
            z.text((n / 2, y), zeile, font=schrift, fill=BEIGE, anchor="mt")
            y += groesse * 1.2
    return feld.convert("RGB")


def etikett(bild_bytes, titel, einst):
    """Ein Etikett. `einst` ist einstellungen['etikett']. Rückgabe: Bild RGBA (n × n Pixel, 300 dpi)."""
    n = mm_px(einst["groesse_mm"])
    weiss = mm_px(einst["weiss_mm"]) if einst["weiss_mm"] > 0 else 0
    ecke = mm_px(einst["ecke_mm"])
    innen = n - 2 * weiss
    quelle = _bild_oeffnen(bild_bytes)
    inhalt = _quadrat(quelle, innen) if quelle else _namensschild(innen, titel)
    aus = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    aussen = _runde_maske(n, ecke)
    if weiss:
        aus.paste(Image.new("RGBA", (n, n), WEISS), (0, 0), aussen)
    inhalt = inhalt.convert("RGBA")
    aus.paste(inhalt, (weiss, weiss), _runde_maske(innen, ecke - weiss))
    if not weiss:                                         # ohne Weißrand: Kontur ist das Cover selbst
        aus.putalpha(aussen)
    return aus


def png_bytes(bild):
    puffer = io.BytesIO()
    bild.save(puffer, "PNG", dpi=(DPI, DPI), optimize=True)
    return puffer.getvalue()


def plaetze(einst):
    """Wie viele Etiketten passen auf einen Bogen (Spalten, Zeilen)?"""
    spalten, zeilen, _ = stickerbogen.raster(einst["groesse_mm"], einst["rand_mm"], einst["abstand_mm"])
    return spalten, zeilen


def bogen(etiketten, einst):
    """Etiketten (Bilder) auf einen transparenten Bogen 90 × 140 mm legen. Wirft ValueError, wenn zu viele."""
    bild, anzahl = stickerbogen.bogen(etiketten, einst["groesse_mm"], einst["rand_mm"], einst["abstand_mm"])
    return bild


def testbogen(einst):
    """Bogen mit Messskala, damit sich an der Station nachmessen lässt, wie groß und wie genau gedruckt wird."""
    _, _, ecken = stickerbogen.raster(einst["groesse_mm"], einst["rand_mm"], einst["abstand_mm"])
    stuecke = [stickerbogen.teststicker(einst["groesse_mm"], i + 1) for i in range(len(ecken))]
    return bogen(stuecke, einst)
