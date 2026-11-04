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
| coupon_C7_lochbild_stapel | **Lochbild 58 × 49 mm des Akku-Stapels**, ca. 20 min | Stapel mit den vorhandenen Schrauben daraufsetzen: Fallen alle 4 Köpfe in die Mulden? Liegt die Acrylplatte innerhalb der Ecken-Marken? |
| coupon_C8_bodenecke_* (2 Teile) | Schattenfuge Boden/Korpus, Zentrierkragen, Senkschraube 3,0 × 14 in den Dom | Rutscht der Kragen leicht hinein, ohne zu wackeln? Sitzt die Schraube bündig? |
| coupon_C10_fuzzy_ecke (+ _MODIFIER) | Ecke hinten rechts mit Anschlussfeld-Kante und USB-C-Öffnung, ca. 30 min je Stück | Beide Dateien zusammen laden, Objekt Fuzzy „Deaktiviert“, Modifier „Kontur“; 3–4 Kopien mit verschiedenen Fuzzy-Werten: Welche wirkt hochwertig? Bleibt die Kante des Feldes sauber? |
| coupon_C11_korpus_oben (+ _MODIFIER) | **Probeabschnitt vor dem nächsten Korpus:** obere 36 mm mit voller Grundfläche (Riemenloch, Deckelschrauben, Kammerdecke), etwa ein Viertel der Korpus-Druckzeit | Genau wie den Korpus einrichten (Modifier, Naht aufmalen). Innen glatt? Außen keine Querlinie am Riemenloch? Naht eine gerade Linie an der aufgemalten Stelle? |
| coupon_C1_wand_rechts_drehgeber_klinke | Loch und Wandstärke für Drehgeber (M7) und Klinke | Passt das Gewinde, greift die Mutter? |
| coupon_C1_wand_hinten_usbc | Öffnung für den USB-C-Stecker, 2 Dome für die Soldered-Platine | Platine anschrauben: Buchse mittig hinter der Öffnung? Stecker rastet voll ein? |
| coupon_C2_deckelecke_* (3 Teile) | Deckelspalt 0,4 mm, Auflage, hintere Deckelschraube | Spalt gleichmäßig? Klappert es? |
| coupon_C3_taste_* (3 Teile) | Ein-Taste: Kappe, Halter, Kurzhubtaster | Klickt sie sauber, klemmt nichts? |
| coupon_C4_rahmenstifte_* | Stoffrahmen-Stift in Loch 4,0 / 4,1 / 4,2 (1–3 Kerben) | Welches Loch hält fest, lässt sich aber lösen? |
| coupon_C5_touch_platte | Touch durch 3,3 mm (links, mit Tasche) und 5,3 mm (rechts) | Später mit dem MPR121: reagieren beide? |
| coupon_C6_schraubdome | Kernloch 2,3 / 2,5 / 2,7 mm für 3-mm-Kunststoffschrauben | Welches Loch: Schraube geht fest, Dom reißt nicht? |

## 2. Druckteile (erst nach Messung und Coupons)

| Datei | Farbe | Ausrichtung / Hinweis |
| --- | --- | --- |
| 01_korpus_beige.stl | Beige | aufrecht, Boden auf der Platte; Naht hinten; Kammerdecke als 45°-Satteldach (keine Brücke) |
| 02a_deckel_kern_orange.stl | Orange | Oberseite nach oben (kopfüber geplant, siehe C9); zusammen mit 02b als ein Objekt laden |
| 02b_deckel_haut_beige.stl | Beige | liegt passgenau auf 02a; kopfüber auf texturiertem PEI, sonst Ironing an |
| 03_deckelrahmen.stl | Schwarz/Grau | Deckelseite auf der Platte |
| 04_kartenfach.stl | Schwarz/Grau | auf der Seite, Kartenschlitz senkrecht; Brim |
| 05_boden_traeger.stl | Beige | flach, Unterseite auf der Platte; trägt die ganze Elektronik |
| 06_stoffrahmen.stl | Beige | Vorderseite unten, Stifte oben |
| 07_drehknopf_orange.stl | Orange | Stirnfläche unten |
| 08_ein_taste_orange.stl | Orange | Kopf unten |
| 09_riemen_gegenplatte.stl | Schwarz/Grau | flach |
| 02_deckel_einfarbig.stl | eine Farbe | Prototyp, gleiche Form wie 02a + 02b; Symbole 0,8 mm vertieft |
| 10_karte_orange.stl | Orange | Rückseite unten (NFC-Tasche an der Platte), Einschubtasche oben; Cover auf Papier von oben einschieben |

Die Dateien liegen bereits in Druckausrichtung. Ausnahme Deckel: liegt mit der Oberseite nach oben; geplant ist der Druck
kopfüber auf texturiertem PEI (erst Coupon C9 prüfen, dann im Slicer umdrehen). Das Tastenloch ist offen
(keine Mulde, keine Opferschicht mehr). `02a` und `02b` gemeinsam laden („als ein Objekt mit mehreren Teilen“),
02a Orange und 02b Beige zuweisen – dann macht CANVAS genau einen Farbwechsel. Die beiden `ansicht_…`-Dateien nur zum Anschauen.

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

Boden, Deckel, Rahmen, Kartenfach, Knopf: ohne Fuzzy Skin. Brim für Kartenfach und die C1-Coupons. Deckel: Ironing für die oberste Fläche.
Rolle vorher trocknen (Elegoo: 60 °C, 8 h).

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
