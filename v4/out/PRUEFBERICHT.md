# Prüfbericht Musikbox v4 (Stand 27.10.2026)

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
| Unterkante Kartenfach (z) | 81,8 |
| Unterkante Klemmen im Deckel (z) | 117,4 |
| Abstand Pi + Klemmen-Aufsatz ↔ Kartenfach | 4,8 |
| Abstand Pi + Klemmen-Aufsatz ↔ RC522 | 7,8 |
| Abstand Klinkenstecker am Pi (Zone) ↔ Korpus | 5,5 |
| Abstand Pi + Klemmen-Aufsatz ↔ WAGO GND B | 39,9 |
| Abstand Pi + Klemmen-Aufsatz ↔ Touch-Modul MPR121 | 40,0 |
| Abstand Akku-Board mit Zellen ↔ Korpus | 4,1 |
| Abstand Kabel Klemmreihe links (Zone) ↔ Korpus | 4,5 |
| Abstand Kabel Klemmreihe rechts (Zone) ↔ Drehgeber | 12,0 |
| Abstand Kabel Klemmreihe hinten (Zone) ↔ USB-C-Platine mit Buchse und Kabeln | 7,0 |
| Abstand USB-C-Stecker am Akku-Board (Zone) ↔ Korpus | 4,5 |
| Abstand WAGO GND A ↔ Korpus | 2,4 |
| Abstand Verstärker ↔ Korpus | 5,0 |
| Abstand Boden ↔ Korpus | 0,0 |
| Abstand Lautsprecher ↔ Korpus | 0,0 |
| Abstand Lautsprecher ↔ gitter_beige | 1,3 |
| Abstand Kurzhubtaster ↔ Kartenfach | 4,2 |
| Abstand RC522 ↔ Deckelrahmen | 2,0 |
| Abstand RC522-Stecker (Zone) ↔ Korpus | 5,0 |
| Abstand RC522-Stecker (Zone) ↔ Deckelrahmen | 0,8 |
| Abstand RC522-Stecker (Zone) ↔ Kartenfach | 1,7 |
| Abstand Touch-Modul MPR121 ↔ Kartenfach | 13,5 |
| Abstand RC522-Stecker (Zone) ↔ Schraubblock Deckelrahmen hinten | 3,7 |

0,0 heißt: Teile liegen bewusst aneinander an (Lautsprecher auf der Mulde, Korpus auf dem Boden).
„Zone“ = Freiraum, den Kabel oder Stecker brauchen, kein Bauteil.

## Druckbarkeit (Centauri Carbon 2, Bauraum 256 × 256 × 256 mm)

| Datei | Größe in Druckausrichtung (mm) | Bewusste Brücken |
| --- | --- | --- |
| 01_korpus_beige.stl | 140 × 140 × 136 | Lautsprecherausschnitt oben 28 mm, Kernlöcher der Dome, Schlitze 2 mm (Kammerdecke seit 04.11. als 45°-Satteldach, keine Brücke mehr) |
| 02a_deckel_kern_orange.stl | 133 × 133 × 5 | Böden der Symbol-Vertiefungen (bis 10,8 mm; Variante A: auf PLA-Einleger statt Brücke) |
| 02b_deckel_haut_beige.stl | 133 × 133 × 1 | – |
| 03_deckelrahmen.stl | 128 × 128 × 17 | Boden Tasterhalter 12 mm |
| 04_kartenfach.stl | 14 × 52 × 88 | Seitenwand über dem Kartenschlitz 5 mm |
| 05_boden_traeger.stl | 140 × 140 × 8 | Decke der Senkbohrungen M2,5 (Ring 1,8 mm) |
| 06a_gitter_beige.stl | 115 × 116 × 6 | Böden der Sacklöcher für die Buchstaben-Stifte (Ø 2,4, unsichtbar) |
| 06b_logo_buchstaben_orange.stl | 71 × 109 × 2 | keine |
| 07_drehknopf_orange.stl | 34 × 34 × 23 | – |
| 08_ein_taste_orange.stl | 17 × 17 × 13 | – |
| 09_riemen_gegenplatte.stl | 18 × 24 × 4 | – |

Alle anderen Flächen sind steiler als 45° oder liegen auf der Platte. Kein Teil braucht Stützmaterial.

## Gitter und Logo-Buchstaben (Schichtanalyse in Druckausrichtung)

- Lochfeld rund (R 37,5) in Ringen: 222 Löcher Ø 3,3, Mindestabstand 4,2 (Steg ≥ 0,9 mm = 2 Linien).
- Offen direkt vor der Lautsprecheröffnung Ø 73: 45 %. Luft bis zum Lautsprecherrahmen 1,3 mm.
- Dämpfung durch das Gitter (Abschätzung, Lochplatte als Luftmasse): 2 kHz 0,3 dB, 5 kHz 1,5 dB, 10 kHz 4,3 dB (Stand vorher mit Logo vor dem Lautsprecher: 2 kHz 2,4 dB, 5 kHz 7,6 dB, 10 kHz 13,0 dB).
- Gitter Schicht 1 (Sichtfläche): 11191 mm², schmaler als 1 Linie (0,4 mm): 0,01 mm².
- Logo-Maßstab 0,644 der Vorlage; „peppa“ über, „BOX“ unter dem Lochfeld. Buchstaben: 11 Teile auf einer Platte (94 × 46 mm), mindestens 4,1 mm Abstand; Schicht 1 1049 mm², schmaler als 0,4 mm: 0,41 mm².
- 16 Stifte in Sacklöchern (Spiel 0,2 je Seite, Loch 0,3 tiefer); die 3 Strahlen in flachen Taschen (1 Schicht). Überschneidung mit dem Gitter -0,000 mm³.
- STL geschlossen, keine doppelten Ecken.
