"""Erzeugt README, Parameterliste und Prüfbericht für das Druckpaket."""
import os as _os
ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

import os, zipfile, datetime
import model as M
import check as K
import coupons as C
from build_all import DRUCK, OUT

STAND = "27.10.2026"


def fmt(v):
    if isinstance(v, float):
        return f"{v:g}".replace(".", ",")
    if isinstance(v, (tuple, list)):
        return " / ".join(fmt(x) for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k} {fmt(x)}" for k, x in v.items())
    return str(v)


def parameter_md():
    order = ["vorläufig", "Probedruck", "gemessen", "belegt", "festgelegt"]
    head = {"vorläufig": "Vorläufig – am echten Teil messen", "Probedruck": "Mit Probedruck einstellen",
            "gemessen": "Von dir gemessen", "belegt": "Aus Datenblatt belegt", "festgelegt": "Gestaltung festgelegt"}
    out = [f"# Parameter Musikbox v4 (Stand {STAND})", "",
           "Jeder Wert steht in `model.py` ganz oben. Ändert sich ein Wert, rechnet das Modell alles neu: Löcher, Halter, Kollisionsprüfung.", ""]
    for st in order:
        rows = [(k, d) for k, d in M.P.items() if d["s"] == st]
        out += [f"## {head[st]} ({len(rows)})", "", "| Name | Wert (mm) | Bedeutung |", "| --- | --- | --- |"]
        out += [f"| `{k}` | {fmt(d['v'])} | {d['q']} |" for k, d in rows]
        out.append("")
    return "\n".join(out)


def pruefbericht_md(parts, ph):
    ins = K.insertion_top(parts, ph)
    insb = K.insertion_bottom(parts, ph)
    col = K.collisions(parts, ph)
    gp = K.gaps(ph, parts)
    lines = [f"# Prüfbericht Musikbox v4 (Stand {STAND})", "",
             "Automatisch gerechnet mit den Werten aus `model.py`. Bauteile, deren Maße noch fehlen, stecken als Platzhalter (Hüllquader) im Modell.", "",
             "## Kollisionen", ""]
    lines += ["Keine Überschneidung zwischen Druckteilen und Bauteilen." if not col else
              "\n".join(f"- {a} × {b}: {v:.1f} mm³" for a, b, v in col), "",
              "## Einbau", "",
              "**Deckel von oben:** Deckelrahmen mit Verteiler-Brücke, Kartenfach, Taster und die Module unter der Brücke passen an der "
              "ringsum geschlossenen Deckelauflage vorbei." if all(v < 0.5 for v in ins.values()) else
              "\n".join(f"- {k}: {v:.1f} mm³ außerhalb" for k, v in ins.items() if v >= 0.5), "",
              "**Boden von unten:** Der Boden mit Stapel, Klemmen, Verstärker und allen Kabel-Freiräumen lässt sich senkrecht hochschieben, "
              "ohne an Drehgeber, Klinke, USB-Buchse, Lautsprecher, Domen oder Deckelteilen hängen zu bleiben (Hubweg geprüft, nicht nur die Endlage)."
              if all(v < 0.5 for v in insb.values()) else "\n".join(f"- {k}: {v:.1f} mm³ im Weg" for k, v in insb.items() if v >= 0.5), "",
              "## Wichtige Abstände", "", "| Prüfung | Wert (mm) |", "| --- | --- |"]
    nice = {"kartenfach": "Kartenfach", "korpus": "Korpus", "boden": "Boden", "deckelrahmen": "Deckelrahmen"}
    def nk(k):
        for a_, b_ in nice.items():
            k = k.replace(a_, b_)
        return k
    lines += [f"| {nk(k)} | {v:.1f} |".replace(".", ",") for k, v in gp.items()]
    lines += ["", "0,0 heißt: Teile liegen bewusst aneinander an (Lautsprecher auf der Mulde, Korpus auf dem Boden).",
              "„Zone“ = Freiraum, den Kabel oder Stecker brauchen, kein Bauteil.", "",
              "## Druckbarkeit (Centauri Carbon 2, Bauraum 256 × 256 × 256 mm)", "",
              "| Datei | Größe in Druckausrichtung (mm) | Bewusste Brücken |", "| --- | --- | --- |"]
    bridges = {"korpus": "Kammerdecke ca. 40 mm, Lautsprecherausschnitt oben 28 mm, Kernlöcher der Dome, Schlitze 2 mm",
               "deckel_orange": "Taschen unter den Touch-Feldern (Ø 20–28 mm, verdeckt)",
               "deckelrahmen": "Boden Tasterhalter 12 mm", "kartenfach": "Seitenwand über dem Kartenschlitz 5 mm",
               "boden": "Decke der Senkbohrungen M2,5 (Ring 1,8 mm)"}
    for k, (fn, col_, note) in DRUCK.items():
        o = K.orient(k, parts[k]) if k not in ("deckel_orange", "deckel_beige") else parts[k]
        bb = o.bounding_box()
        size = f"{bb[3]-bb[0]:.0f} × {bb[4]-bb[1]:.0f} × {bb[5]-bb[2]:.0f}"
        lines.append(f"| {fn} | {size} | {bridges.get(k, '–')} |")
    lines += ["", "Alle anderen Flächen sind steiler als 45° oder liegen auf der Platte. Kein Teil braucht Stützmaterial.", ""]
    return "\n".join(lines)


def readme_md():
    t = f"""# Musikbox v4 – Druckpaket (Stand {STAND})

**Noch nicht das Gehäuse drucken.** Einige Maße sind Platzhalter, bis deine Teile gemessen sind
(Liste in `PARAMETER.md`, Abschnitt „Vorläufig“). Jetzt sinnvoll: C7 (Lochbild) und die Probedruck-Coupons.

## Neu in diesem Stand: Boden = Elektronikträger

- Der Korpus ist unten offen. Nur die Lautsprecherkammer hat einen eigenen, festen Boden und bleibt dicht.
- Die Bodenplatte (`05_boden_traeger.stl`) trägt Akku-Stapel, Hebelklemmen GND A und 5 V sowie den Verstärker. Einen DAC gibt es nicht mehr: Die Kopfhörer hängen an der Klinke des Pi, ein kurzes Kabel mit gewinkeltem Stecker führt zur Buchse in der Wand.
- Du verdrahtest alles am Tisch und schiebst die Einheit dann von unten in den Korpus. Gehalten wird sie von 6 Senkschrauben.
- Ein Kragen auf der Platte zentriert sie in der Öffnung. Weil die Kammer vorne gerade ist und die Ecken hinten rund sind, passt sie nur richtig herum.
- Unter dem Deckel sitzt jetzt eine Verteiler-Brücke mit Touch-Modul und den Klemmen für 3,3 V, SCL und GND B. Die Kabel zu Touchfeldern, NFC-Leser und Taste werden dadurch kurz.
- Die Deckelauflage ist ringsum geschlossen, weil nichts mehr von oben eingesetzt werden muss.
- Die USB-C-Einbaubuchse sitzt hinten rechts auf 60 mm Höhe. Die Position ist vorläufig, bis die Buchse feststeht.

**Stapel einsetzen:** Überhang mit der BOOT-Taste nach links, Kante mit den gelben Stiften nach vorne (zum Lautsprecher),
Anschlusskante mit USB-C und Schalter nach hinten. Das Bild `boden_plan.png` zeigt es von oben.

## 1. Zuerst: Probedruck-Coupons

| Datei | Prüft | Was du mir zurückmeldest |
| --- | --- | --- |
| coupon_C7_lochbild_stapel | **Lochbild 58 × 49 mm des Akku-Stapels**, ca. 20 min | Stapel mit den vorhandenen Schrauben daraufsetzen: Fallen alle 4 Köpfe in die Mulden? Liegt die Acrylplatte innerhalb der Ecken-Marken? |
| coupon_C8_bodenecke_* (2 Teile) | Schattenfuge Boden/Korpus, Zentrierkragen, Senkschraube 3,0 × 14 in den Dom | Rutscht der Kragen leicht hinein, ohne zu wackeln? Sitzt die Schraube bündig? |
| coupon_C1_wand_rechts_drehgeber_klinke | Loch und Wandstärke für Drehgeber (M7) und Klinke | Passt das Gewinde, greift die Mutter? |
| coupon_C1_wand_hinten_usbc | Loch für die USB-C-Einbaubuchse | **Erst drucken, wenn die Buchse feststeht.** |
| coupon_C2_deckelecke_* (3 Teile) | Deckelspalt 0,4 mm, Auflage, hintere Deckelschraube | Spalt gleichmäßig? Klappert es? |
| coupon_C3_taste_* (3 Teile) | Ein-Taste: Kappe, Halter, Kurzhubtaster | Klickt sie sauber, klemmt nichts? |
| coupon_C4_rahmenstifte_* | Stoffrahmen-Stift in Loch 4,0 / 4,1 / 4,2 (1–3 Kerben) | Welches Loch hält fest, lässt sich aber lösen? |
| coupon_C5_touch_platte | Touch durch 3,3 mm (links, mit Tasche) und 5,3 mm (rechts) | Später mit dem MPR121: reagieren beide? |
| coupon_C6_schraubdome | Kernloch 2,3 / 2,5 / 2,7 mm für 3-mm-Kunststoffschrauben | Welches Loch: Schraube geht fest, Dom reißt nicht? |

## 2. Druckteile (erst nach Messung und Coupons)

| Datei | Farbe | Ausrichtung / Hinweis |
| --- | --- | --- |
"""
    for k, (fn, col, note) in DRUCK.items():
        t += f"| {fn} | {col} | {note} |\n"
    t += """| 02_deckel_einfarbig.stl | eine Farbe | Prototyp, gleiche Form wie 02a + 02b; Symbole 0,8 mm vertieft |
| 10_karte_orange.stl | Orange | Rückseite unten (NFC-Tasche an der Platte), Einschubtasche oben; Cover auf Papier von oben einschieben |

Die Dateien liegen bereits in Druckausrichtung. Ausnahme Deckel: liegt mit der Oberseite nach oben; geplant ist der Druck
kopfüber auf texturiertem PEI (erst Coupon C9 prüfen, dann im Slicer umdrehen). Nach dem Druck die Opferschicht im Tastenloch
mit dem Cutter ausschneiden. `02a` und `02b` gemeinsam laden („als ein Objekt mit mehreren Teilen“),
02a Orange und 02b Beige zuweisen – dann macht CANVAS genau einen Farbwechsel. Die beiden `ansicht_…`-Dateien nur zum Anschauen.

Der Boden darf auch orange sein: Dann läuft unten ein schmaler oranger Sockelstreifen um die Box.

## Einstellungen PETG auf der Centauri Carbon 2 (Startwerte)

- Düse 0,4, Schichthöhe 0,2 mm, 3 Wandlinien, 15 % Gyroid
- Korpus außen: **Fuzzy Skin** nur Kontur, Stärke 0,2–0,25 mm, Punktabstand 0,6–0,7 mm
- Boden, Deckel, Rahmen, Kartenfach, Knopf: ohne Fuzzy Skin
- Keine Stützen. Brim für Kartenfach und die C1-Coupons
- Naht hinten (Korpus); Deckel: Ironing (Bügeln) für die oberste Fläche
- Rolle vorher trocknen (Elegoo: 60 °C, 8 h)

### Fuzzy Skin gezielt ausnehmen (Modifier)

1. `01_korpus_beige.stl` und `01m_modifier_korpus_OHNE_fuzzy.stl` **zusammen** markieren und in den Slicer ziehen.
2. Die Frage „als ein Objekt mit mehreren Teilen laden?“ mit **Ja** beantworten – beide Teile behalten dann ihre exakte Lage.
3. In der Objektliste den Teil `01m_…` rechts anklicken → **Typ ändern → Modifier**.
4. Beim Korpus Fuzzy Skin = **Kontur**, beim Modifier Fuzzy Skin = **Keine**.
5. Vorschau prüfen: Stoffrahmen-Vertiefung, Drehgeber, Klinke, USB-C, Riemenloch und Deckelschrauben glatt, der Rest körnig.

## Module befestigen

Alle Module und Klemmen liegen in Mulden mit 2,5 mm Rand. Ein Streifen doppelseitiges Montageband oder ein Tropfen Heißkleber reicht.
Unter dem Deckel hängen sie kopfüber; dort am besten Montageband nehmen.

## Was für die Montage noch fehlt (nicht bestellt)

| Teil | Menge | Wofür |
| --- | --- | --- |
| Kunststoffschraube 3,0 × 14, Senkkopf | 8 | Boden in den Korpus (6), Deckel hinten durch die Rückwand (2) |
| Kunststoffschraube 3,0 × 8 | 6 | Deckelrahmen an den Deckel |
| Kunststoffschraube 3,0 × 12 | 6 | Lautsprecher (4), Kartenfach (2) |
| Schraube M2,5, ca. 5 mm länger als die jetzigen unter der Acrylplatte | 4 | Stapel von unten durch den Boden (Länge folgt nach deiner Messung) |
| Doppelseitiges Montageband | 1 Rolle | Module in den Mulden |
| Lautsprecherstoff beige, ca. 20 × 20 cm | 1 | Stoffrahmen (entfällt mit gedrucktem Gitter) |
| Buchschraube Ø 5 mm + Lederriemen | 1 | Riemen links |
| Polyesterwatte, eine Handvoll | – | Lautsprecherkammer |

Tipp zum Sparen: Boden und Deckel nutzen jetzt dieselbe Schraube 3,0 × 14 mit Senkkopf. Ein Sortiment „Kunststoffschrauben 3,0 mm“
deckt alle Längen ab und ist meist günstiger als Einzelpackungen.

## Dateien

- `model.py` – das parametrische Modell, alle Maße oben als benannte Werte
- `check.py` – Kollisionen, Einbau (Deckel von oben, Boden von unten mit Hubweg), Druckbarkeit
- `PARAMETER.md`, `PRUEFBERICHT.md` – Werte mit Status und Prüfergebnis
- `boden_plan.png` – Boden von oben und Höhen von der Seite
"""
    return t


if __name__ == "__main__":
    parts = M.build()
    ph = M.placeholders()
    open(os.path.join(OUT, "PARAMETER.md"), "w").write(parameter_md())
    open(os.path.join(OUT, "PRUEFBERICHT.md"), "w").write(pruefbericht_md(parts, ph))
    open(os.path.join(OUT, "README.md"), "w").write(readme_md())
    zp = _os.path.join(ROOT, "v4/musikbox_v4_druckpaket.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(OUT)):
            if f.endswith((".stl", ".md", ".png")):
                z.write(os.path.join(OUT, f), "musikbox_v4/" + f)
        for f in ("model.py", "check.py", "coupons.py", "boden_plan.py"):
            z.write(os.path.join(_os.path.join(ROOT, "v4"), f), "musikbox_v4/quellcode/" + f)
    print(zp, os.path.getsize(zp) // 1024, "KB")
    counts = {}
    for d in M.P.values():
        counts[d["s"]] = counts.get(d["s"], 0) + 1
    print(counts)
