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
    bridges = {"korpus": "Lautsprecherausschnitt oben 28 mm, Kernlöcher der Dome, Schlitze 2 mm (Kammerdecke seit 04.11. als 45°-Satteldach, keine Brücke mehr)",
               "deckel_orange": "Böden der Symbol-Vertiefungen (bis 10,8 mm; Variante A: auf PLA-Einleger statt Brücke)",
               "deckelrahmen": "Boden Tasterhalter 12 mm", "kartenfach": "Seitenwand über dem Kartenschlitz 5 mm",
               "boden": "Decke der Senkbohrungen M2,5 (Ring 1,8 mm)", "gitter_beige": "Böden der Sacklöcher für die Buchstaben-Stifte (Ø 2,4, unsichtbar)",
               "gitter_logo": "keine"}
    for k, (fn, col_, note) in DRUCK.items():
        o = K.orient(k, parts[k])
        bb = o.bounding_box()
        size = f"{bb[3]-bb[0]:.0f} × {bb[4]-bb[1]:.0f} × {bb[5]-bb[2]:.0f}"
        lines.append(f"| {fn} | {size} | {bridges.get(k, '–')} |")
    lines += ["", "Alle anderen Flächen sind steiler als 45° oder liegen auf der Platte. Kein Teil braucht Stützmaterial.", ""]
    g = K.gitter_pruefung(parts)
    r1, b1 = g["rows"][0], g["rows_b"][0]
    back = [r for r in g["rows"] if M.GR_T - M.GR_PLENUM < r["z"] < M.GR_T]
    n = lambda v, k=1: f"{v:.{k}f}".replace(".", ",")
    lines += ["## Gitter und Logo-Buchstaben (Schichtanalyse in Druckausrichtung)", "",
              f"- Gitter einfarbig: {g['loecher']} Löcher Ø {n(M.GR_HOLE[0])} im Wabenraster {n(M.GR_HOLE[1])} (Steg 0,9 mm = 2 Linien).",
              f"- Offen direkt vor der Lautsprecheröffnung: {g['offen_direkt']:.0f} %; über den Luftraum ({n(g['luft'])} mm) erreichbar: {g['offen_mulde']:.0f} % der Öffnung.",
              f"- Gitter Schicht 1 (Sichtfläche): {r1['flaeche']:.0f} mm², schmaler als 1 Linie (0,4 mm): {n(r1['d04'], 2)} mm².",
              f"- Gitter hinten (Luftraum): Rand läuft durch die Lochmitten, schmaler als 0,4 mm höchstens {n(max(r['d04'] for r in back), 2)} mm² je Schicht (Ecken am Lochrand).",
              f"- Buchstaben: {g['teile']} Teile auf einer Platte ({g['platte'][3]:.0f} × {g['platte'][4]:.0f} mm), mindestens {n(g['abstand_platte'])} mm Abstand; "
              f"Schicht 1 (Sichtseite) {b1['flaeche']:.0f} mm², schmaler als 0,4 mm: {n(b1['d04'], 2)} mm² (Spitze im e-Schlitz, Ecken).",
              f"- {g['stifte']} Stifte in Sacklöchern (Spiel {n(M.GR_PEG[2])} je Seite, Loch 0,3 tiefer), Überschneidung mit dem Gitter {n(g['sitz'], 3)} mm³.",
              "- STL geschlossen, keine doppelten Ecken (Löcher als gedrehte 32-Ecke, Versätze vereinfacht).", ""]
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
- Die USB-C-Buchse (Soldered-Platine 333011) sitzt hinten rechts auf 60 mm Höhe (Buchsenmitte x 112). Platine mit Bauteilseite oben auf zwei Domen an der Rückwand, 2 Schrauben 3,0 mm von oben; die Wand hat eine Öffnung 13 × 7 mm für den Steckerkörper.

**Stapel einsetzen:** Überhang mit der BOOT-Taste nach links, Kante mit den gelben Stiften nach vorne (zum Lautsprecher),
Anschlusskante mit USB-C und Schalter nach hinten. Das Bild `boden_plan.png` zeigt es von oben.

## 1. Zuerst: Probedruck-Coupons

| Datei | Prüft | Was du mir zurückmeldest |
| --- | --- | --- |
| coupon_C14_gitter_ecke_beige + coupon_C14_buchstaben_P_e_p_orange | **Probe vor dem Gitter:** Ecke oben links einfarbig (Löcher, Rand, schräge Oberkante, ein Stift) mit den Sacklöchern für „P“, „e“, „p“, dazu diese drei Buchstaben, ca. 12 g | Mit den Gitter- bzw. Buchstaben-Einstellungen (Abschnitt „Gitter“). Fäden in den Löchern weg? Buchstaben-Stifte: leicht hinein, ohne zu wackeln? Buchstaben liegen plan auf? In die obere linke Ecke des Korpus drücken: Stift fest? |
| coupon_C12_deckel_oberseite_* (5 Dateien) | **Probe vor dem Deckel:** obere 2,4 mm vorne rechts (Play, Vor, Mond, Kante mit Fase), kopfüber, Symbole vertieft, ca. 15 g | Wie den Deckel einrichten: Variante A mit `_opfer_PLA`, Variante B mit `_MODIFIER_bruecke_richtung`, beide mit `_MODIFIER_haut_1wand`. Beige in den Kreisen so ruhig wie außen? Symbolböden eben bzw. Fäden parallel? |
| coupon_C7_lochbild_stapel | **Lochbild 58 × 49 mm des Akku-Stapels**, ca. 20 min | Stapel mit den vorhandenen Schrauben daraufsetzen: Fallen alle 4 Köpfe in die Mulden? Liegt die Acrylplatte innerhalb der Ecken-Marken? |
| coupon_C8_bodenecke_* (2 Teile) | Schattenfuge Boden/Korpus, Zentrierkragen, Senkschraube 3,0 × 12 in den Dom | Rutscht der Kragen leicht hinein, ohne zu wackeln? Sitzt die Schraube bündig? |
| coupon_C10_fuzzy_ecke (+ _MODIFIER) | Ecke hinten rechts mit Anschlussfeld-Kante und USB-C-Öffnung, ca. 30 min je Stück | Beide Dateien zusammen laden, Objekt Fuzzy „Deaktiviert“, Modifier „Kontur“; 3–4 Kopien mit verschiedenen Fuzzy-Werten: Welche wirkt hochwertig? Bleibt die Kante des Feldes sauber? |
| coupon_C11_korpus_oben (+ _MODIFIER) | **Probeabschnitt vor dem nächsten Korpus:** obere 36 mm mit voller Grundfläche (Riemenloch, Deckelschrauben, Kammerdecke), etwa ein Viertel der Korpus-Druckzeit | Genau wie den Korpus einrichten (Modifier, Naht aufmalen). Innen glatt? Außen keine Querlinie am Riemenloch? Naht eine gerade Linie an der aufgemalten Stelle? |
| coupon_C1_wand_rechts_drehgeber_klinke | Loch und Wandstärke für Drehgeber (M7) und Klinke | Passt das Gewinde, greift die Mutter? |
| coupon_C1_wand_hinten_usbc | Öffnung für den USB-C-Stecker, 2 Dome für die Soldered-Platine | Platine anschrauben: Buchse mittig hinter der Öffnung? Stecker rastet voll ein? |
| coupon_C2_deckelecke_* (3 Teile) | Deckelspalt 0,4 mm, Auflage, hintere Deckelschraube | Spalt gleichmäßig? Klappert es? |
| coupon_C3_taste_* (3 Teile) | Ein-Taste: Kappe, Halter, Kurzhubtaster | Klickt sie sauber, klemmt nichts? |
| coupon_C4_rahmenstifte_* | Gitter-Stift in Loch 4,0 / 4,1 / 4,2 (1–3 Kerben); der Korpus hat 4,1 | Welches Loch hält fest, lässt sich aber lösen? (C14 prüft den Stift direkt am Korpus) |
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

Die Dateien liegen bereits in Druckausrichtung, auch der Deckel: `02a` und `02b` liegen seit 05.11. **kopfüber**
(Oberseite auf der Platte, hinten bleibt hinten). Das Tastenloch ist offen (keine Mulde, keine Opferschicht mehr).
`02a` und `02b` gemeinsam laden („als ein Objekt mit mehreren Teilen“), 02a Orange und 02b Beige zuweisen – dann macht
CANVAS genau einen Farbwechsel (Variante A: dazu PLA-Einleger `02p`, Variante B: Modifizierer `02r`), immer mit Modifizierer `02m`. Einstellungen: Abschnitt „Deckel“ unten. Die beiden `ansicht_…`-Dateien nur zum Anschauen.

Das Gitter `06a` ist einfarbig beige und liegt mit der Vorderfläche auf der Platte, die Oberkante zeigt nach hinten. Die orangen
Logo-Buchstaben `06b` sind ein eigener Druck (alle 11 Teile auf einer Platte) und werden danach aufgeklebt. Einstellungen: Abschnitt „Gitter“.

Der Boden darf auch orange sein: Dann läuft unten ein schmaler oranger Sockelstreifen um die Box.

## Einstellungen PETG auf der Centauri Carbon 2

Ausgangspunkt: Drucker „Elegoo Centauri Carbon 2 0.4 nozzle“, Filament „Elegoo PETG @ECC2“, Prozess „0.20mm Standard @Elegoo CC2 0.4 nozzle“,
Druckbetttyp „Texturierte PEI-Platte“. Im Prozess-Bereich die erweiterten Einstellungen einschalten. In Klammern: Profilwert vorher.

### Korpus (Stand 04.11.2026, Ziel höchste Außenqualität)

| Reiter → Gruppe | Einstellung | Wert |
| --- | --- | --- |
| Qualität → Schichthöhe | Schichthöhe / Höhe der ersten Schicht | 0,2 / 0,2 (bleibt) |
| Qualität → Naht | Nahtposition | Ausgerichtet (bleibt) + Naht aufmalen |
| | Schrägnaht (Beta) | Keine |
| | Naht Zwischenraum | 10 % (bleibt) |
| | Wischbewegung nach innen | an (aus) |
| Qualität → Präzision | Elefantenfußkompensation | 0,15 (0,1) |
| Qualität → Wandgenerator | Wandgenerator | Klassisch (bleibt) |
| Qualität → Wände und Oberflächen | Anordnung der Wände | Innen/Außen (bleibt) |
| Qualität → Brücken | Dicke externe Brücken | an (aus) – Lautsprecherausschnitt oben 28 mm |
| Struktur → Wände | Wandschleifen | 3 (2) |
| Struktur → Füllung | Fülldichte / Füllmuster | 15 % / Gyroid (Geradlinig) |
| Struktur → Obere/Untere Schichten | Muster der Oberfläche | **Konzentrisch** (Monotonische Linie) – die Deckelauflage innen bestand aus 3,2 m kurzer Linien: eine Schicht 158 s statt 60 s |
| Geschwindigkeit → erste Schicht | Erste Schicht | 30 mm/s (50) – Haftung |
| Geschwindigkeit → restliche Schichten | Außenwand / Innere Wand | 60 (160) / 120 (200) mm/s |
| Geschwindigkeit → Beschleunigung | Außenwand | 2000 (5000) mm/s² |
| Geschwindigkeit → Überhang-Geschwindigkeit | Verlangsamen bei Überhängen | **aus** (an) – sonst springt die Fuzzy-Außenwand zwischen 51 und 60 mm/s |
| Sonstiges → Umrandung | Randtyp / Randbreite / Lücke | Nur Innenrand / 8 mm / 0 |
| Sonstiges → Fuzzy Skin | Fuzzy Skin | Nur lackiert (Werte bleiben sichtbar; ohne Bemalung kein Fuzzy) |
| | Generierungsmodus / Rauschtyp | Verschiebung / Klassisch |
| | Punktabstand / Stärke | 0,30 / 0,20 |
| | Fuzzy Skin auf die erste Schicht anwenden | aus |
| Modifizierer `01f` → Sonstiges | Fuzzy Skin | **Kontur** |
| Filament → Kühlung | Lüftergeschwindigkeit (beide Zeilen) | 20 % / 20 % (10 / 40) – Kühlung unabhängig von der Schichtdauer |
| | Kühlung für Überhänge und Brücken erzwingen | an (bleibt) |
| | Überhänge und externe Brücken Lüftergeschwindigkeit | 50 % (90) |
| | Überhänge Kühlung Aktivierungsschwelle | **95 %** (10 % bei PETG/Rapid PETG) – sonst schaltet jeder nach außen springende Fuzzy-Punkt den Lüfter auf 50 % |
| Filament → Kühlung, Zeile „Minimale Lüftergeschwindigkeit“ | Schichtdauer | **100 s** (30) – muss über der Zeile darunter liegen; Lüfter bleibt bei 20 % |
| Filament → Kühlung, Zeile „Schwellenwert für die maximale Lüftergeschwindigkeit“ | Schichtdauer | **70 s** (12) – jede Schicht dauert mindestens 70 s, gleichmäßige Abkühlung |
| | Verlangsamen Sie den Druck für eine bessere Schichtkühlung | an (bleibt) |
| | Äußere Wände nicht verlangsamen | **an** (aus) – gebremst werden nur Innenwände und Füllung, die sichtbare Wand läuft immer mit 60 mm/s |
| Filament → Druckbett (Texturierte PEI) | Erste Schicht / Andere Schichten | 80 / 75 °C (70 / 70) – gegen Abheben |
| Drucker → Extruder | Z-Hub-Höhe | 0,4 (bleibt) |

Warum die Mindest-Schichtdauer: Sprünge in der Schichtdauer zeichnen sich bei PETG außen als Linie ab. Die harte Linie im ersten Druck
auf etwa 118 mm Druckhöhe kam von der flachen Kammerdecke (40-mm-Brücke, eine Schicht 5½ min statt 1 min). Die Decke ist jetzt ein
45°-Satteldach (innen, unsichtbar, kein Zusammenbau); die 70 s gleichen die restlichen kleinen Sprünge aus. Kostet rund 1 Stunde Druckzeit.
Bilder: `kammerdecke_satteldach.png`, `kammerdecke_schichtzeit.png`.

Naht aufmalen: ganzes Objekt markieren, Werkzeug „Naht aufmalen“, Pinselgröße 0,5 (schmaler Strich = Naht streut weniger), „Vertikal“ an; Menü Ansicht → Hinten;
senkrechten Strich auf der Rundung rechts neben den Lüftungsschlitzen (Mitte zwischen Ende des glatten Feldes und Außenkante)
von ganz unten bis ganz oben ziehen. Bild: `naht_aufmalen.png`.

Deckel, Rahmen, Kartenfach, Knopf: ohne Fuzzy Skin. Boden: Fuzzy nur am Rand, eigener Abschnitt unten. Brim für Kartenfach und die C1-Coupons. Deckel: eigener Abschnitt unten.
Rolle vorher trocknen (Elegoo: 60 °C, 8 h).

### Boden (Stand 06.11.2026, sichtbarer Rand wie der Korpus)

Der Boden steht bündig unter dem Korpus, sein Rand ist von außen sichtbar. Deshalb **alle Einstellungen wie beim Korpus** und dieselbe beige Rolle.
Am einfachsten: das Korpus-Projekt (.3mf) öffnen, „Speichern unter“ als Boden-Projekt, Korpus und `01f` löschen, dann
`05_boden_traeger.stl` und `05f_modifier_boden_FUZZY_rand.stl` zusammen hineinziehen (ein Objekt mit zwei Teilen, `05f` → Typ Modifizierer, Fuzzy Skin **Kontur**).

| Abweichung vom Korpus | Wert | Grund |
| --- | --- | --- |
| Lage | Unterseite auf der Platte, nicht drehen | Standkante (0,8-Fase) unten, V-Fuge oben |
| Sonstiges → Umrandung | **keine** | „Nur Innenrand“ würde nur die Schraublöcher zufüllen; die volle Fläche haftet ohne Rand |
| Naht | aufmalen an derselben Rundung wie am Korpus (Pinselgröße 0,5, Vertikal) | Nähte von Korpus und Boden liegen übereinander |
| Stützen | aus | Überhang nur an den Decken der M2,5-Senkungen (102 mm², kurze Brücken) |

Fuzzy liegt nur auf dem senkrechten Streifen 0,8–3,2 mm; Fase unten und Fase oben (V-Fuge) bleiben glatt, genau wie die Fase unten am Korpus.
Vorschau prüfen: Schichten 5–16 außen körnig, Schicht 1–4 und ab 17 glatt.
Nach dem Druck: Senkungen der 6 Bodenschrauben auf Grat prüfen, Kopf muss bündig liegen.

### Deckel (Stand 05.11.2026 spät, kopfüber, Symbole 0,8 mm vertieft und ertastbar, ohne Fuzzy)

Die Oberseite entsteht auf der texturierten PEI-Platte. Beige sind die 4 untersten Schichten (0,8 mm), ab Schicht 5 Orange.
Befund Druck 05.11. (Bild `deckel_ursache.png`): Fläche außerhalb der Kreise sehr gut. In den Kreisen: Der Slicer hat die
Vertiefungen in Schicht 5 überbrückt und die Brücke auf den ganzen Kreis ausgedehnt (1760 mm² Brücke für 597 mm² Vertiefung).
Hinter 0,8 mm Beige lagen dort runde Brückenfäden mit Lücken statt dichter Füllung → Orange scheint wie Fäden durch; dazu 3 Wandringe
je Loch in Schicht 2–4, Punktreihen (Überlappung 5 %), Nahtpunkte und Härchen an den Lochkanten. Die 0,8 mm Beige selbst sind nicht
zu dünn: Außerhalb der Kreise ist es dieselbe Haut, dort liegt dahinter dichte Füllung.

**Variante A (empfohlen): PLA-Opfer-Einleger.** `02p` füllt die Vertiefungen in Schicht 1–4 mit PLA. Die erste orange Schicht
wird darauf als normale dichte Füllung gedruckt – keine Brücke, keine Fäden, Böden eben und in allen Symbolen in derselben Richtung.
PETG haftet nicht an PLA: Einleger nach dem Druck mit einer Nadel heraushebeln (zusammen ca. 0,6 g). Dafür eine PLA-Rolle in
einen freien CANVAS-Platz (am besten Orange, dann fallen Reste nicht auf).

**Variante B (ohne PLA): Fäden als Stilmittel, alle in eine Richtung.** `02r` ist ein Modifizierer nur für Schicht 5 über den
Vertiefungen (+0,4 mm). Dort „Externe Brücken Füllrichtung“ fest; die Brücke bleibt auf die Symbole begrenzt, dahinter dichte Füllung.

Ausgangspunkt sind die Korpus-Einstellungen (Profil „… - Peppa“); als eigenen Prozess speichern. In Klammern: Wert beim Korpus.

| Reiter → Gruppe | Einstellung | Wert |
| --- | --- | --- |
| Objektliste | Teile laden („ein Objekt mit mehreren Teilen“) | A: `02a`, `02b`, `02p`, `02m` · B: `02a`, `02b`, `02r`, `02m` |
| | Filamente | 02a → Orange, 02b → Beige, 02p → PLA (Rechtsklick → Filament wechseln); 02m und 02r → Typ ändern → **Modifizierer**, danach Rechtsklick → Filament wechseln → **Standard** (sonst färbt der Modifizierer seinen Bereich mit Filament 1 ein – Probe 05.11.: Haut weiß, Wände über den Symbolen) |
| Modifizierer `02m` | Wandschleifen | **1** – in den Haut-Schichten nur eine Wand um jedes Loch (keine Ringe hinter der Sichtfläche) |
| Modifizierer `02r` (nur B) | Struktur → Erweiterte Einstellungen → Externe Brücken Füllrichtung | **45°** (0 = automatisch) – Fäden in allen Symbolen parallel zu den Linien der Oberfläche, längste Brücke 10,8 mm |
| Qualität → Brücken (nur B) | Dicke externe Brücken / Externe Brücken Dichte | **aus** (an) / **110 %** (100) – flache, dicht liegende Fäden |
| Geschwindigkeit → Überhanggeschwindigkeit → Überbrückung (nur B) | Extern | **30 mm/s** (50) – C12 05.11.: ein Faden im Play-Dreieck aus der Reihe |
| Filament Orange → Kühlung (nur B) | Überhänge und externe Brücken Lüftergeschwindigkeit | **100 %** (50) – Fäden erstarren sofort gerade; als eigenes Filamentprofil speichern und nur dem orangen Platz zuweisen |
| Qualität → Schichthöhe | Schichthöhe / erste Schicht | 0,2 / 0,2 (bleibt) |
| Qualität → Naht | Nahtposition | **Rückseite** (Ausgerichtet + aufgemalt) |
| Qualität → Präzision | Elefantenfußkompensation | 0,15 (bleibt) |
| Qualität → Wandgenerator | Wandgenerator | **Arachne** (Klassisch) – Ringe 1,1 mm und schmale Stege ohne Lückenfüllung |
| Qualität → Wände und Oberflächen | Nur eine Wand in der ersten Schicht / Vermeiden von Wandüberquerungen | an / an |
| Struktur → Obere/Untere Schichten | Untere Schalenschichten | **8** (3) |
| | Überlappung des oberen/unteren massiven Füllung/Wand | **25 %** (5 %) – gegen die Punktreihen |
| | Muster der unteren Fläche | Monotonisch (bleibt) |
| Struktur → Füllung | Fülldichte / Füllmuster | **25 %** / Gyroid (15 %) |
| Geschwindigkeit → erste Schicht | Füllung | **50 mm/s** (105) |
| Sonstiges → Umrandung | Randtyp | **Keine Umrandung** (Nur Innenrand) |
| Sonstiges → Fuzzy Skin | Fuzzy Skin | Deaktiviert |
| Multimaterial → Reinigungsturm | Aktivieren | an |
| Reinigungsvolumen | Multiplikator | **1,5** (1) |
| Drucker/Platte (nur A) | Betttemperaturtyp | **Nach der höchsten Temperatur** – Bett bleibt bei den PETG-Werten 80/75 °C |
| Filament PLA (nur A) | Düse | 230 °C; Einstellungen → Steuerung → Slicen: „Entfernen der Einschränkung für gemischte Temperaturen“ an (sonst lässt der Slicer PLA und PETG nicht zusammen zu) |
| Filament Beige/Orange | | wie beim Korpus (250 °C, Bett 80/75 °C, Lüfter 20 %, Schichtdauer 70/100) |

Vorher: Platte mit Spülmittel waschen, nicht mehr anfassen. Variante A: Haube oben offen lassen (PLA mag die warme Kammer nicht,
der flache Deckel verzieht sich nicht). Nach dem Druck auf der Platte abkühlen lassen, PLA-Einleger heraushebeln (bleiben sie auf
der Platte, dort abnehmen). Vorschau: Schicht 1–4 Beige + Einleger (A); Schicht 5 über den Symbolen keine „Überbrückung“ (A)
bzw. nur über den Symbolen, alle Linien parallel (B). Zuerst `coupon_C12_deckel_oberseite_*` mit derselben Variante.
`08_ein_taste_orange.stl` (Kopf unten, keine Umrandung) bekommt dieselbe Oberfläche, wenn der Kopf auf der texturierten PEI liegt –
am besten zusammen mit dem Drehknopf `07` drucken (beide Orange): Auf der Deckel-Platte müsste CANVAS in Schicht 1–4 jedes Mal
zwischen Beige und Orange wechseln. Bild: `deckel_draufsicht.png`.

### Gitter (Stand 06.11.2026: einfarbig, Buchstaben erhaben und aufgeklebt, ohne Fuzzy)

Befund C13 (06.11., eingelegtes Logo, zweifarbig): sehr viele Fäden in den Löchern, Fehler im Orange nach den Farbwechseln,
ein verbrannter dunkler Fleck hinten. Deshalb ohne Farbwechsel: **Gitter einfarbig beige**, die **Buchstaben als eigene orange
Teile**, 1,2 mm dick, aufgeklebt – sie stehen 1,0 mm vor der Korpusfront (3D-Effekt). Beide Sichtflächen entstehen auf der
texturierten PEI-Platte (matt wie der Deckel). Jeder Buchstabe hat hinten 2 Stifte Ø 2,0 (die drei Strahlen je einen Stift in
ihrer Form) und passt nur in seine Sacklöcher im Gitter. Bild: `gitter_ansicht.png` (`v4/gitter/render_gitter.py`).

`06a_gitter_beige.stl`: 115,4 × 115,7 mm, 3,6 mm dick (über dem Lautsprecher 2,4 mm, dahinter 2,5 mm Luft), 6 Stifte Ø 3,9, ca. 36 g.
`06b_logo_buchstaben_orange.stl`: 11 Teile in Logo-Reihenfolge auseinandergezogen (mindestens 4 mm Abstand), Sichtseite unten, ca. 4 g.

**Gegen die Fäden (Befund C13):** Rolle trocknen (Elegoo: 60 °C, 8 h) – wichtigste Maßnahme. Düse heiß reinigen, Silikonwischer
hinten von PETG-Resten befreien (sonst nimmt die Düse sie wieder auf und sie verbrennen). Platte mit Spülmittel waschen, nicht anfassen.
Für das Gitter einen eigenen Prozess und ein eigenes Filamentprofil anlegen und alle Werte aus der Tabelle unten eintragen.

**Gitter `06a` – alle Abweichungen von den Elegoo-Standardprofilen** (Drucker „Elegoo Centauri Carbon 2 0.4 nozzle“, Prozess
„0.20mm Standard @Elegoo CC2 0.4 nozzle“, Filament „Elegoo PETG @ECC2“, Druckbetttyp „Texturierte PEI-Platte“; erweiterte
Einstellungen einschalten). In Klammern der Profilwert, wo er bekannt ist. Prozess und Filament unter eigenem Namen speichern.

| Reiter | Einstellung | Wert |
| --- | --- | --- |
| Prozess → Qualität | Nahtposition | **Rückseite** (Ausgerichtet) |
| | Schrägnaht (Beta) | **Keine** |
| | Wischbewegung nach innen | **an** (aus) |
| | Elefantenfußkompensation | **0,15** (0,1) |
| | Wandgenerator | **Arachne** (Klassisch) |
| | Nur eine Wand in der ersten Schicht | **an** |
| | Vermeiden von Wandüberquerungen | **an** |
| | Vermeide das Überqueren der Wand – Maximale Umleitungslänge | **0** (keine Grenze) |
| Prozess → Struktur | Wandschleifen | **3** (2) |
| | Untere Schalenschichten | **8** (3) |
| | Überlappung des oberen/unteren massiven Füllung/Wand | **25 %** (5 %) |
| | Muster der Oberfläche | **Konzentrisch** (Monotonische Linie) |
| | Fülldichte / Füllmuster | **25 % / Gyroid** (15 % / Geradlinig) |
| Prozess → Geschwindigkeit | Erste Schicht / Füllung der ersten Schicht | **30 / 50 mm/s** (50 / 105) |
| | Außenwand / Innere Wand | **40 / 120 mm/s** (160 / 200) |
| | Beschleunigung Außenwand | **2000 mm/s²** (5000) |
| | Verlangsamen bei Überhängen | **aus** (an) |
| Prozess → Sonstiges | Randtyp | **Keine Umrandung** |
| | Fuzzy Skin | **Deaktiviert** |
| Filament | Düsentemperatur erste Schicht / andere Schichten | **245 / 240 °C** (250 / 250) |
| | Druckbett Texturierte PEI erste / andere Schichten | **80 / 75 °C** (70 / 70) |
| Filament → Kühlung | Lüftergeschwindigkeit (beide Zeilen) | **35 % / 35 %** (10 / 40) |
| | Zeile „Minimale Lüftergeschwindigkeit“ → Schichtdauer | **100 s** (30) |
| | Zeile „Schwellenwert für die maximale Lüftergeschwindigkeit“ → Schichtdauer | **70 s** (12) |
| | Äußere Wände nicht verlangsamen | **an** (aus) |
| | Keine Kühlung für die erste | **3** Schichten |
| | Überhänge und externe Brücken Lüftergeschwindigkeit | **50 %** (90) |
| | Überhänge Kühlung Aktivierungsschwelle | **95 %** (10 %) |
| Filament → Überschreiben der Einstellungen (Häkchen je Zeile setzen) | Länge (Rückzug) | **1,0 mm** |
| | Rückzugsgeschwindigkeit / Wiedereinzugsgeschwindigkeit | **40 / 30 mm/s** |
| | Zurückziehen beim Schichtwechsel | **an** |
| | Während des Rückzugs wischen / Wischabstand | **an / 2 mm** |
| | Rückzugsmenge vor der Reinigung | **70 %** |
| | Schwellenwert für die Fahrstrecke | **0,5 mm** |
| | Z-Hub-Höhe / Z-Hub Typ | **0,2 mm / Normal** (0,4) |

Platte: `06a` allein, mittig, nicht drehen (Vorderfläche unten, Oberkante hinten), nur Filament Beige, keine Modifizierer.

**Buchstaben `06b` – alle Abweichungen von den Elegoo-Standardprofilen** (gleiche Ausgangsprofile wie beim Gitter; Filament: die
orange Rolle). Schichthöhe bleibt 0,2: Die Buchstaben sind genau 6 Schichten dick, die Stifte 5 Schichten, und weniger Schichten
heißen weniger Fahrten zwischen den 11 Teilen (Fäden an den Buchstabenkanten).

| Reiter | Einstellung | Wert |
| --- | --- | --- |
| Prozess → Qualität | Schichthöhe / erste Schicht | 0,2 / 0,2 (Profilwert, bleibt) |
| | Nahtposition | **Rückseite** (Ausgerichtet) – die im Einbau untere Kante jedes Buchstabens liegt hinten |
| | Schrägnaht (Beta) | **Keine** |
| | Wischbewegung nach innen | **an** (aus) |
| | Elefantenfußkompensation | **0,15** (0,1) – scharfe Kante an der Sichtseite |
| | Wandgenerator | **Arachne** (Klassisch) – schmale Stellen (e-Schlitz, Strahlen) sauber |
| | Nur eine Wand in der ersten Schicht | **an** – Sichtseite wie Deckel und Gitter |
| | Vermeiden von Wandüberquerungen / Maximale Umleitungslänge | **an / 0** |
| Prozess → Struktur | Wandschleifen | **3** (2) |
| | Untere Schalenschichten | **8** (3) – Buchstabe durchgehend massiv |
| | Überlappung des oberen/unteren massiven Füllung/Wand | **25 %** (5 %) |
| | Muster der unteren Fläche | Monotonisch (Profilwert, bleibt) – gleiche Linien wie auf dem Gitter |
| | Fülldichte | **100 %** (15 %) – dünne Teile ganz massiv |
| Prozess → Geschwindigkeit | Erste Schicht / Füllung der ersten Schicht | **30 / 50 mm/s** (50 / 105) |
| | Außenwand / Innere Wand | **40 / 120 mm/s** (160 / 200) |
| | Beschleunigung Außenwand | **2000 mm/s²** (5000) |
| | Verlangsamen bei Überhängen | **aus** (an) |
| Prozess → Sonstiges | Randtyp | **Keine Umrandung** – ein Rand säße an der Sichtkante |
| | Fuzzy Skin | **Deaktiviert** |
| Filament | Düsentemperatur erste / andere Schichten | **245 / 240 °C** (250 / 250) |
| | Druckbett Texturierte PEI erste / andere Schichten | **80 / 75 °C** (70 / 70) |
| Filament → Kühlung | Lüftergeschwindigkeit (beide Zeilen) | **35 % / 35 %** (10 / 40) |
| | Zeile „Minimale Lüftergeschwindigkeit“ → Schichtdauer | **100 s** (30) |
| | Zeile „Schwellenwert für die maximale Lüftergeschwindigkeit“ → Schichtdauer | **70 s** (12) |
| | Äußere Wände nicht verlangsamen | **an** (aus) |
| | Keine Kühlung für die erste | **3** Schichten |
| | Überhänge Kühlung Aktivierungsschwelle | **95 %** (10 %) |
| Filament → Überschreiben der Einstellungen (Häkchen je Zeile) | Länge (Rückzug) | **1,0 mm** |
| | Rückzugsgeschwindigkeit / Wiedereinzugsgeschwindigkeit | **40 / 30 mm/s** |
| | Zurückziehen beim Schichtwechsel | **an** |
| | Während des Rückzugs wischen / Wischabstand | **an / 2 mm** |
| | Rückzugsmenge vor der Reinigung | **70 %** |
| | Schwellenwert für die Fahrstrecke | **0,5 mm** |
| | Z-Hub-Höhe / Z-Hub Typ | **0,2 mm / Normal** (0,4) |

Platte: `06b` allein, mittig, nicht drehen (Sichtseite unten, Stifte oben, „BOX“ hinten), nur Orange, keine Modifizierer.
Vorher Düse heiß reinigen, Wischer prüfen, Platte waschen. Die orange Rolle ist neu – frisch aus der Verpackung meist trocken genug;
lag sie offen, auch trocknen.

**Einkleben:** Zuerst trocken probieren: Jeder Buchstabe muss mit leichtem Druck plan aufliegen. Geht ein Stift zu stramm, das
Loch mit einem 2,5-mm-Bohrer von Hand nachdrehen; ist er locker, füllt der Kleber das Spiel. Dann je einen kleinen Tropfen
**nur in die Sacklöcher** (nicht auf die Fläche), Buchstaben eindrücken, Gitter mit der Vorderseite nach oben aushärten lassen.
Am besten 5-Minuten-Epoxid (Zeit zum Ausrichten, kein Schleier); Sekundenkleber hält auch, kann aber um die Fuge einen weißen
Schleier bilden. Reihenfolge: wie auf der Druckplatte, oben „peppa“ und die Strahlen, unten „BOX“.
Einsetzen ins Gehäuse: 6 Stifte in die Löcher, gleichmäßig eindrücken. Herausnehmen: Schraubendreher unten in die Kerbe.

### Drehknopf (Stand 05.11.2026, volle Achse, ohne Fuzzy)

`07_drehknopf_orange.stl`: Ø 34 × 22,8 mm, ca. 24 g. Die Drehgeberachse wird **nicht** gekürzt. Stirnfläche unten auf der
texturierten PEI-Platte → dieselbe matte Oberfläche wie die Tasten im Deckel; dieselbe orange Rolle wie beim Deckel.
Innen: Führung Ø 6,3 im ungeschlitzten Teil der Achse, Klemmsitz Ø 6,1 nur im geschlitzten Teil (federt), Steg 8 mm im Schlitz.
Bild: `drehknopf_schnitt.png`. Die Ein-Taste `08` passt mit auf die Platte (gleiche Einstellungen).

| Reiter | Einstellung | Wert |
| --- | --- | --- |
| Qualität | Schichthöhe | **0,12 mm** (erste Schicht 0,2) – feinere Schichtlinien auf dem Mantel |
| Qualität | Nahtposition | Ausgerichtet + **Naht aufmalen** in eine Rille **links (−X)**, gegenüber der Markierung (liegt beim Laden rechts, +X); Schrägnaht keine |
| Festigkeit | Wandschleifen / Füllung | 3 / 25 % Gyroid |
| Sonstiges | Fuzzy Skin | **Keine** – Griff geben die 24 Rillen; Fuzzy würde ihre Kanten verwischen |
| Sonstiges | Randtyp | Keine Umrandung |
| Filament | | wie beim Deckel; die Mindest-Schichtdauer bremst bei dem kleinen Teil Innenwände und Füllung – gewollt, die Rillenkanten kühlen besser |

Aufstecken: Steg in den Achsschlitz ausrichten, Knopf gerade **bis Anschlag** aufschieben (Achsende liegt am Knopfboden) –
dann bleibt 1 mm Luft zur Wand. Die Markierung ist nur Zierde: Der Drehgeber dreht endlos, sie zeigt keine Lautstärke an.

### Fuzzy Skin nur außen (Modifier „Außenhaut“, seit 04.11.2026)

Warum: Jedes Loch durch die Wand (Klinke, Drehgeber, USB-C, Schlitze, Riemen, Deckelschrauben, Lautsprecher) schneidet den
Wandring in diesen Schichten auf. Der Slicer zählt dann die ganze Innenseite zur „Kontur“ und verfuzzt sie mit. Der neue Modifier
ist eine 1 mm dünne Haut nur an den Außenflächen – Fuzzy entsteht ausschließlich dort.

1. `01_korpus_beige.stl` und `01f_modifier_korpus_FUZZY_aussenhaut.stl` **zusammen** markieren und in den Slicer ziehen.
2. Die Frage „als ein Objekt mit mehreren Teilen laden?“ mit **Ja** beantworten – beide Teile behalten dann ihre exakte Lage.
3. In der Objektliste den Teil `01f_…` rechts anklicken → **Typ ändern → Modifizierer**.
4. Prozess (global): Fuzzy Skin = **Nur lackiert**, Stärke 0,20, Punktabstand 0,30, Klassisch. Modifizierer in der Objektliste anklicken → Reiter Sonstiges → Fuzzy Skin = **Kontur**.
5. Vorschau prüfen (Linientyp-Ansicht, Schieberegler durch die Höhe): innen überall glatt, auch auf Höhe der Löcher;
   außen körnig; Anschlussfeld, Gitter-Sitz, Loch-Flächen und die beiden Fasen (unten, oben) glatt.
6. Der alte Modifier `01m_…OHNE_fuzzy` ist entfernt und darf nicht mehr verwendet werden.

## Module befestigen

Alle Module und Klemmen liegen in Mulden mit 2,5 mm Rand. Ein Streifen doppelseitiges Montageband oder ein Tropfen Heißkleber reicht.
Unter dem Deckel hängen sie kopfüber; dort am besten Montageband nehmen.

## Schrauben (Stand 06.11.2026)

Alle Dome, Kernlöcher und Senkungen sind auf die vorhandenen Kunststoffschrauben **3,0 × 12** ausgelegt (`SCREW_L`).

| Teil | Menge | Wofür |
| --- | --- | --- |
| Kunststoffschraube 3,0 × 12, Senkkopf | 14 | Boden in den Korpus (6), Deckel hinten durch die Rückwand (2), Deckelrahmen an den Deckel (6, Kopf versenkt im Dom) |
| Kunststoffschraube 3,0 × 12, Flachkopf | 8 | Lautsprecher (4, mit M3-Scheiben), Kartenfach (2), USB-C-Buchse (2) |
| Schraube M2,5, ca. 5 mm länger als die jetzigen unter der Acrylplatte | 4 | Stapel von unten durch den Boden (Länge folgt nach deiner Messung) |

## Was für die Montage noch fehlt (nicht bestellt)

| Teil | Menge | Wofür |
| --- | --- | --- |
| Doppelseitiges Montageband | 1 Rolle | Module in den Mulden |
| Buchschraube (Schaft Ø 7,5) + Lederriemen | 1 | Riemen links |
| Polyesterwatte, eine Handvoll | – | Lautsprecherkammer |

## Dateien

- `model.py` – das parametrische Modell, alle Maße oben als benannte Werte
- `check.py` – Kollisionen, Einbau (Deckel von oben, Boden von unten mit Hubweg), Druckbarkeit
- `PARAMETER.md`, `PRUEFBERICHT.md` – Werte mit Status und Prüfergebnis
- `boden_plan.png` – Boden von oben und Höhen von der Seite
- `gitter_ansicht.png` – Frontgitter: Ansichten, Schnitt durch Buchstabe, Stift und Luftraum, Lage auf den Druckplatten
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
