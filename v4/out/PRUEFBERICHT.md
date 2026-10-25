# Prüfbericht Musikbox v4 (Stand 24.10.2026)

Automatisch gerechnet mit den Werten aus `model.py`. Bauteile, deren Maße noch fehlen, stecken als Platzhalter (Hüllquader) im Modell.

## Kollisionen

Keine Überschneidung zwischen Druckteilen und Bauteilen.

## Einbau

**Deckel von oben:** Deckelrahmen mit Verteiler-Brücke, Kartenfach, Taster und die Module unter der Brücke passen an der ringsum geschlossenen Deckelauflage vorbei.

**Boden von unten:** Der Boden mit Stapel, Klemmen, Verstärker und allen Kabel-Freiräumen lässt sich senkrecht hochschieben, ohne an Drehgeber, Klinke, USB-Buchse, Lautsprecher, Domen oder Deckelteilen hängen zu bleiben (Hubweg geprüft, nicht nur die Endlage).

## Wichtige Abstände

| Prüfung | Wert (mm) |
| --- | --- |
| Oberkante Klemmen (z) | 77,5 |
| Unterkante Kartenfach (z) | 86,8 |
| Unterkante Klemmen im Deckel (z) | 117,4 |
| Abstand Pi + Klemmen-Aufsatz ↔ Kartenfach | 9,8 |
| Abstand Pi + Klemmen-Aufsatz ↔ RC522 | 12,8 |
| Abstand Klinkenstecker am Pi (Zone) ↔ Korpus | 5,5 |
| Abstand Pi + Klemmen-Aufsatz ↔ WAGO GND B | 39,9 |
| Abstand Pi + Klemmen-Aufsatz ↔ Touch-Modul MPR121 | 40,0 |
| Abstand Akku-Board mit Zellen ↔ Korpus | 4,1 |
| Abstand Kabel Klemmreihe links (Zone) ↔ Korpus | 4,5 |
| Abstand Kabel Klemmreihe rechts (Zone) ↔ Drehgeber | 13,0 |
| Abstand Kabel Klemmreihe hinten (Zone) ↔ USB-C-Einbaubuchse mit Kabel | 8,0 |
| Abstand USB-C-Stecker am Akku-Board (Zone) ↔ Korpus | 4,5 |
| Abstand WAGO GND A ↔ Korpus | 2,4 |
| Abstand Verstärker ↔ Korpus | 5,0 |
| Abstand Boden ↔ Korpus | 0,0 |
| Abstand Lautsprecher ↔ Korpus | 0,0 |
| Abstand Kurzhubtaster ↔ Kartenfach | 4,2 |
| Abstand RC522 ↔ Deckelrahmen | 2,0 |
| Abstand RC522-Stecker (Zone) ↔ Korpus | 0,0 |
| Abstand RC522-Stecker (Zone) ↔ Deckelrahmen | 0,8 |
| Abstand RC522-Stecker (Zone) ↔ Kartenfach | 1,7 |
| Abstand Touch-Modul MPR121 ↔ Kartenfach | 13,6 |

0,0 heißt: Teile liegen bewusst aneinander an (Lautsprecher auf der Mulde, Korpus auf dem Boden).
„Zone“ = Freiraum, den Kabel oder Stecker brauchen, kein Bauteil.

## Druckbarkeit (Centauri Carbon 2, Bauraum 256 × 256 × 256 mm)

| Datei | Größe in Druckausrichtung (mm) | Bewusste Brücken |
| --- | --- | --- |
| 01_korpus_beige.stl | 140 × 140 × 136 | Kammerdecke ca. 40 mm, Lautsprecherausschnitt oben 28 mm, Kernlöcher der Dome, Schlitze 2 mm |
| 02a_deckel_kern_orange.stl | 133 × 133 × 5 | Taschen unter den Touch-Feldern (Ø 20–28 mm, verdeckt) |
| 02b_deckel_haut_beige.stl | 133 × 133 × 1 | – |
| 03_deckelrahmen.stl | 127 × 128 × 17 | Boden Tasterhalter 12 mm |
| 04_kartenfach.stl | 14 × 47 × 88 | Seitenwand über dem Kartenschlitz 5 mm |
| 05_boden_traeger.stl | 140 × 140 × 8 | Decke der Senkbohrungen M2,5 (Ring 1,8 mm) |
| 06_stoffrahmen.stl | 114 × 114 × 5 | – |
| 07_drehknopf_orange.stl | 34 × 34 × 16 | – |
| 08_ein_taste_orange.stl | 17 × 17 × 12 | – |
| 09_riemen_gegenplatte.stl | 18 × 24 × 4 | – |

Alle anderen Flächen sind steiler als 45° oder liegen auf der Platte. Kein Teil braucht Stützmaterial.
