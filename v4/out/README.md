# Musikbox v4 – Druckpaket (Stand 24.10.2026)

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
| 01_korpus_beige.stl | Beige | aufrecht, Boden auf der Platte; Naht hinten; Brücke Kammerdecke ca. 40 mm |
| 02a_deckel_kern_orange.stl | Orange | Oberseite nach oben; zusammen mit 02b als ein Objekt laden |
| 02b_deckel_haut_beige.stl | Beige | liegt passgenau auf 02a; Ironing an |
| 03_deckelrahmen.stl | Schwarz/Grau | Deckelseite auf der Platte |
| 04_kartenfach.stl | Schwarz/Grau | auf der Seite, Kartenschlitz senkrecht; Brim |
| 05_boden_traeger.stl | Beige | flach, Unterseite auf der Platte; trägt die ganze Elektronik |
| 06_stoffrahmen.stl | Beige | Vorderseite unten, Stifte oben |
| 07_drehknopf_orange.stl | Orange | Stirnfläche unten |
| 08_ein_taste_orange.stl | Orange | Kopf unten |
| 09_riemen_gegenplatte.stl | Schwarz/Grau | flach |
| 10_karte_orange.stl | Orange | flach, NFC-Tasche oben; Cover-Bild auf die Vorderseite kleben |

Die Dateien liegen bereits in Druckausrichtung. `02a` und `02b` gemeinsam laden („als ein Objekt mit mehreren Teilen“),
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
