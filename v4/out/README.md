# Musikbox v4 – Druckpaket (Stand 27.10.2026)

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
| coupon_C13_gitter_ecke_* (2 Dateien) | **Probe vor dem Gitter:** Ecke oben links mit „P“, „e“, „p“ (engste Lücken zwischen den Buchstaben 0,6–0,9 mm, e-Schlitz), Löcher, Rand mit Fase, schräge Oberkante, ein Stift; zweifarbig wie das Gitter, ca. 10 g | Wie das Gitter einrichten (Abschnitt „Gitter“). Grenze Orange/Beige scharf, ohne Spalt und ohne orange Punkte im Beige? Lücken zwischen den Buchstaben durchgehend beige? Härchen in den Löchern? In die obere linke Ecke des Korpus drücken: Stift fest, Fase und Spalt gleichmäßig? |
| coupon_C12_deckel_oberseite_* (5 Dateien) | **Probe vor dem Deckel:** obere 2,4 mm vorne rechts (Play, Vor, Mond, Kante mit Fase), kopfüber, Symbole vertieft, ca. 15 g | Wie den Deckel einrichten: Variante A mit `_opfer_PLA`, Variante B mit `_MODIFIER_bruecke_richtung`, beide mit `_MODIFIER_haut_1wand`. Beige in den Kreisen so ruhig wie außen? Symbolböden eben bzw. Fäden parallel? |
| coupon_C7_lochbild_stapel | **Lochbild 58 × 49 mm des Akku-Stapels**, ca. 20 min | Stapel mit den vorhandenen Schrauben daraufsetzen: Fallen alle 4 Köpfe in die Mulden? Liegt die Acrylplatte innerhalb der Ecken-Marken? |
| coupon_C8_bodenecke_* (2 Teile) | Schattenfuge Boden/Korpus, Zentrierkragen, Senkschraube 3,0 × 14 in den Dom | Rutscht der Kragen leicht hinein, ohne zu wackeln? Sitzt die Schraube bündig? |
| coupon_C10_fuzzy_ecke (+ _MODIFIER) | Ecke hinten rechts mit Anschlussfeld-Kante und USB-C-Öffnung, ca. 30 min je Stück | Beide Dateien zusammen laden, Objekt Fuzzy „Deaktiviert“, Modifier „Kontur“; 3–4 Kopien mit verschiedenen Fuzzy-Werten: Welche wirkt hochwertig? Bleibt die Kante des Feldes sauber? |
| coupon_C11_korpus_oben (+ _MODIFIER) | **Probeabschnitt vor dem nächsten Korpus:** obere 36 mm mit voller Grundfläche (Riemenloch, Deckelschrauben, Kammerdecke), etwa ein Viertel der Korpus-Druckzeit | Genau wie den Korpus einrichten (Modifier, Naht aufmalen). Innen glatt? Außen keine Querlinie am Riemenloch? Naht eine gerade Linie an der aufgemalten Stelle? |
| coupon_C1_wand_rechts_drehgeber_klinke | Loch und Wandstärke für Drehgeber (M7) und Klinke | Passt das Gewinde, greift die Mutter? |
| coupon_C1_wand_hinten_usbc | Öffnung für den USB-C-Stecker, 2 Dome für die Soldered-Platine | Platine anschrauben: Buchse mittig hinter der Öffnung? Stecker rastet voll ein? |
| coupon_C2_deckelecke_* (3 Teile) | Deckelspalt 0,4 mm, Auflage, hintere Deckelschraube | Spalt gleichmäßig? Klappert es? |
| coupon_C3_taste_* (3 Teile) | Ein-Taste: Kappe, Halter, Kurzhubtaster | Klickt sie sauber, klemmt nichts? |
| coupon_C4_rahmenstifte_* | Gitter-Stift in Loch 4,0 / 4,1 / 4,2 (1–3 Kerben); der Korpus hat 4,1 | Welches Loch hält fest, lässt sich aber lösen? (C13 prüft den Stift direkt am Korpus) |
| coupon_C5_touch_platte | Touch durch 3,3 mm (links, mit Tasche) und 5,3 mm (rechts) | Später mit dem MPR121: reagieren beide? |
| coupon_C6_schraubdome | Kernloch 2,3 / 2,5 / 2,7 mm für 3-mm-Kunststoffschrauben | Welches Loch: Schraube geht fest, Dom reißt nicht? |

## 2. Druckteile (erst nach Messung und Coupons)

| Datei | Farbe | Ausrichtung / Hinweis |
| --- | --- | --- |
| 01_korpus_beige.stl | Beige | aufrecht, Boden auf der Platte; Naht hinten; Kammerdecke als 45°-Satteldach (keine Brücke) |
| 02a_deckel_kern_orange.stl | Orange | kopfüber (Oberseite auf der Platte, hinten bleibt hinten); mit 02b zusammen als ein Objekt mit zwei Teilen laden |
| 02b_deckel_haut_beige.stl | Beige | kopfüber, die 4 untersten Schichten ohne Symbole; Symbole und Ringe 0,8 mm vertieft (ertastbar) |
| 03_deckelrahmen.stl | Schwarz/Grau | Deckelseite auf der Platte |
| 04_kartenfach.stl | Schwarz/Grau | auf der Seite, Kartenschlitz senkrecht; Brim |
| 05_boden_traeger.stl | Beige | flach, Unterseite auf der Platte; trägt die ganze Elektronik |
| 06a_gitter_beige.stl | Beige | Vorderfläche auf der texturierten PEI, Oberkante nach hinten; mit 06b als ein Objekt mit zwei Teilen laden |
| 06b_gitter_logo_orange.stl | Orange | Logo-Einleger, nur Schicht 1–4 (0,8 mm), deckungsgleich mit 06a |
| 07_drehknopf_orange.stl | Orange | Stirnfläche unten |
| 08_ein_taste_orange.stl | Orange | Kopf unten |
| 09_riemen_gegenplatte.stl | Schwarz/Grau | flach |
| 06_gitter_einfarbig_HOERPROBE.stl | eine Farbe | Schneller Probedruck (0,28 Entwurf, Reste-Rolle): Sitz und Stifte im Korpus, Hörtest mit und ohne Gitter. Gleiche Form wie 06a + 06b |
| 02_deckel_einfarbig.stl | eine Farbe | Prototyp, gleiche Form wie 02a + 02b; Symbole 0,8 mm vertieft |
| 10_karte_orange.stl | Orange | Rückseite unten (NFC-Tasche an der Platte), Einschubtasche oben; Cover auf Papier von oben einschieben |

Die Dateien liegen bereits in Druckausrichtung, auch der Deckel: `02a` und `02b` liegen seit 05.11. **kopfüber**
(Oberseite auf der Platte, hinten bleibt hinten). Das Tastenloch ist offen (keine Mulde, keine Opferschicht mehr).
`02a` und `02b` gemeinsam laden („als ein Objekt mit mehreren Teilen“), 02a Orange und 02b Beige zuweisen – dann macht
CANVAS genau einen Farbwechsel (Variante A: dazu PLA-Einleger `02p`, Variante B: Modifizierer `02r`), immer mit Modifizierer `02m`. Einstellungen: Abschnitt „Deckel“ unten. Die beiden `ansicht_…`-Dateien nur zum Anschauen.

Das Gitter (`06a` beige + `06b` Logo orange) liegt mit der Vorderfläche auf der Platte, die Oberkante zeigt nach hinten.
Beide gemeinsam laden („als ein Objekt mit mehreren Teilen“) – das Logo füllt nur die Schichten 1–4. Einstellungen: Abschnitt „Gitter“.

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

Boden, Deckel, Rahmen, Kartenfach, Knopf: ohne Fuzzy Skin. Brim für Kartenfach und die C1-Coupons. Deckel: eigener Abschnitt unten.
Rolle vorher trocknen (Elegoo: 60 °C, 8 h).

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

### Gitter (Stand 05.11.2026 spät, Vorderfläche auf der Platte, Logo bündig eingelegt, ohne Fuzzy)

`06a_gitter_beige.stl` + `06b_gitter_logo_orange.stl`, 115,4 × 115,7 mm, 3,6 mm dick (über dem Lautsprecher 2,4 mm, dahinter
2,5 mm Luft), 6 Stifte Ø 3,9 hinten, zusammen ca. 37 g. Logo: Vorlage `v4/gitter/peppa_box_logo.png`, 100 mm breit, Kontur auf
unter 0,1 mm genau. Die Sichtfläche entsteht auf der texturierten PEI-Platte (matt wie der Deckel). Orange liegt nur in Schicht 1–4,
**bündig** – keine Vertiefung, also keine Brücke und keine Fäden (die Ursache beim ersten Deckel). Hinter dem Orange liegt dichtes Beige.
Neu gegenüber dem Deckel: Zwei Farben **in** den sichtbaren Schichten 1–4 → CANVAS wechselt in jeder dieser Schichten. Das ist auf
diesem Drucker noch nicht erprobt, deshalb zuerst Coupon C13. Bild: `gitter_ansicht.png` (`v4/gitter/render_gitter.py`).

Ausgangspunkt sind die Deckel-Einstellungen (Prozess „Deckel“); als eigenen Prozess speichern. In Klammern: Wert beim Deckel.

| Reiter → Gruppe | Einstellung | Wert |
| --- | --- | --- |
| Objektliste | Teile laden („ein Objekt mit mehreren Teilen“) | `06a` + `06b` (Coupon: `coupon_C13_gitter_ecke_beige` + `_logo_orange`) – keine Modifizierer |
| | Filamente | 06a → Beige, 06b → Orange (dieselben Rollen wie Korpus und Deckel) |
| Qualität → Schichthöhe | Schichthöhe / erste Schicht | 0,2 / 0,2 (bleibt) – das Logo ist genau Schicht 1–4 |
| Qualität → Naht | Nahtposition | Rückseite (bleibt) – die Oberkante liegt hinten: Naht in jedem Loch oben (von vorn-oben nicht sichtbar), am Rand oben im Spalt |
| Qualität → Präzision | Elefantenfußkompensation | 0,15 (bleibt) – scharfe Lochkanten vorne |
| Qualität → Wandgenerator | Wandgenerator | Arachne (bleibt) – Stege 0,9 mm zwischen den Löchern und die Lücken zwischen den Buchstaben als saubere Linien |
| Qualität → Wände und Oberflächen | Nur eine Wand in der ersten Schicht / Vermeiden von Wandüberquerungen | an / an (bleibt) – weniger Fahrten über Löcher, weniger Härchen |
| Struktur → Obere/Untere Schichten | Untere Schalenschichten / Überlappung des oberen/unteren massiven Füllung/Wand | 8 / 25 % (bleibt) – Gitter fast massiv, hinter dem Logo dichtes Beige |
| Struktur → Füllung | Fülldichte / Füllmuster | 25 % / Gyroid (bleibt) |
| Sonstiges → Umrandung | Randtyp | Keine Umrandung (bleibt) – ein Innenrand würde die Löcher füllen |
| Sonstiges → Fuzzy Skin | Fuzzy Skin | Deaktiviert |
| Multimaterial → Reinigungsturm | Aktivieren | an; Reinigungsvolumen Multiplikator 1,5 (bleibt) – Beige nach Orange braucht mehr Spülung |
| Filament Beige/Orange | | wie beim Korpus (250 °C, Bett 80/75 °C, Lüfter 20 %, Schichtdauer 70/100) |

Vorher: Rollen trocknen (PETG zieht sonst Fäden durch die 400 Löcher), Platte mit Spülmittel waschen, nicht mehr anfassen.
Vorschau prüfen: Schicht 1–4 Orange nur im Logo, ab Schicht 5 nur Beige; Schicht 13–18 außen am Lautsprecher dünner (Luftraum).
Härchen in Löchern nach dem Druck mit einem kurzen Föhnstoß (Heißluft, Abstand) oder einem 3-mm-Bohrer von Hand entfernen.
Einsetzen: Stifte in die 6 Löcher, gleichmäßig eindrücken. Herausnehmen: Schraubendreher unten in die Kerbe.

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

## Was für die Montage noch fehlt (nicht bestellt)

| Teil | Menge | Wofür |
| --- | --- | --- |
| Kunststoffschraube 3,0 × 14, Senkkopf | 8 | Boden in den Korpus (6), Deckel hinten durch die Rückwand (2) |
| Kunststoffschraube 3,0 × 8 | 6 | Deckelrahmen an den Deckel |
| Kunststoffschraube 3,0 × 12 | 6 | Lautsprecher (4), Kartenfach (2) |
| Schraube M2,5, ca. 5 mm länger als die jetzigen unter der Acrylplatte | 4 | Stapel von unten durch den Boden (Länge folgt nach deiner Messung) |
| Doppelseitiges Montageband | 1 Rolle | Module in den Mulden |
| Buchschraube Ø 5 mm + Lederriemen | 1 | Riemen links |
| Polyesterwatte, eine Handvoll | – | Lautsprecherkammer |

Tipp zum Sparen: Boden und Deckel nutzen jetzt dieselbe Schraube 3,0 × 14 mit Senkkopf. Ein Sortiment „Kunststoffschrauben 3,0 mm“
deckt alle Längen ab und ist meist günstiger als Einzelpackungen.

## Dateien

- `model.py` – das parametrische Modell, alle Maße oben als benannte Werte
- `check.py` – Kollisionen, Einbau (Deckel von oben, Boden von unten mit Hubweg), Druckbarkeit
- `PARAMETER.md`, `PRUEFBERICHT.md` – Werte mit Status und Prüfergebnis
- `boden_plan.png` – Boden von oben und Höhen von der Seite
- `gitter_ansicht.png` – Frontgitter: Ansichten, Schnitt durch Logo und Luftraum, Lage auf der Druckplatte
