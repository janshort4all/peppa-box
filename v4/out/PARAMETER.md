# Parameter Musikbox v4 (Stand 27.10.2026)

Jeder Wert steht in `model.py` ganz oben. Ändert sich ein Wert, rechnet das Modell alles neu: Löcher, Halter, Kollisionsprüfung.

## Vorläufig – am echten Teil messen (22)

| Name | Wert (mm) | Bedeutung |
| --- | --- | --- |
| `FAB_T` | 0,6 | Stoffdicke, Stoff noch nicht gekauft |
| `SPK_FRAME_R` | 21 | Eckradius Korb, aus 93 mm Diagonale abgeleitet |
| `SPK_PITCH` | 58,5 | Lochabstand (Zeichnungswert ohne Beschriftung) |
| `NFC_T` | 0,4 | NFC-Aufkleber Dicke |
| `RC_T` | 1,6 | RC522 Platinendicke |
| `RC_BEND` | 8 | Platz für den Kabelbogen hinter den Buchsen |
| `RC_HDR_OFF` | 0 | Mitte der Stiftleiste gegenüber Platinenmitte, + = vom Deckel weg (nicht gemessen, mittig angenommen) |
| `SW_H` | 7,3 | Tasterhöhe gesamt (Quellen: 7,3 bzw. 6,5) |
| `ENC_WALL` | 2 | Wand am Drehgeber (Gewindelänge unbekannt) |
| `ENC_OUT` | 14 | Achse ragt so weit aus der Wand |
| `ENC_SLOT` | 1 | Schlitzbreite Achse |
| `NUT_REC` | 14 / 3 | Aussparung für Mutter+Scheibe im Knopf Ø, Tiefe |
| `JK_HOLE` | 6,2 | Loch für Klinkengewinde (Gewinde unbekannt) |
| `JK_WALL` | 2 | Wand an der Klinke |
| `STRAP_HOLE` | 5,2 | Buchschraube noch nicht gekauft |
| `PAT_END` | 3,5 | Lochmitte bis Pi-Ende des Stapels (Pi-Norm); ±3 mm deckt der Freiraum ab |
| `UPS_LEVEL` | 35 | Acrylplatte bis Oberkante Akku-Board (Zellen + Board) |
| `CLAMP_Z` | 52 | Unterkante der Klemmblöcke über der Acrylplatte |
| `USB_PANEL` | x 114; z 60; loch 16,4; mutter 24; tiefe 20 | USB-C-Einbaubuchse in der Rückwand (rund M16 angenommen, Produkt noch offen) |
| `AUDIO_PLUG` | 20 | Platz hinter der Klinke des Pi: Klinkenstecker 90° gewinkelt (Goobay 67782) |
| `MAXB` | 19 / 18 / 8 | Verstärker-Klon L, B, Höhe mit Klemme |
| `MPRB` | 25 / 20 / 4 | MPR121-Modul L, B, Höhe |

## Mit Probedruck einstellen (9)

| Name | Wert (mm) | Bedeutung |
| --- | --- | --- |
| `LIP_CLR` | 0,2 | Spiel Zentrierkragen zur Innenwand je Seite (Coupon C8) |
| `GAP_LID` | 0,4 | Spalt Deckel–Wand je Seite |
| `CLR` | 0,3 | Spiel für Passungen |
| `PILOT` | 2,5 | Kernloch für 3-mm-Kunststoffschraube in PETG |
| `PILOT25` | 2,1 | Kernloch M2,5 (Akku-Board) |
| `PIN_HOLE` | 4,1 | Loch für Rahmenstift (Coupon C4: 4,0 / 4,1 / 4,2) |
| `PAD_POCKET` | 2 | Tasche unter dem Feld → 4 mm Kunststoff über dem Kupfer, unter den Symbolen 3,2 mm |
| `INS_GAP` | 0,6 | Tasche: Spalt an der Außenwand (Einleger laminiert ca. 0,25–0,35 mm) |
| `ENC_HOLE` | 7,4 | Loch für M7-Gewinde |

## Von dir gemessen (10)

| Name | Wert (mm) | Bedeutung |
| --- | --- | --- |
| `RC_L` | 60 | RC522 Platine Länge |
| `RC_B` | 40 | RC522 Platine Breite |
| `RC_ANT` | 20 | Antennenmitte ab Platinenende (Antennenseite; 40 mm bis Lötlochende) |
| `RC_COMP` | 5 | Bauteilhöhe auf der Rückseite (Quarz, höchstes Bauteil) |
| `RC_PIN_OUT` | 6 | Überstand der 90°-Stifte über die Platinenkante |
| `RC_PLUG_OUT` | 14 | Platinenkante bis Ende Steckkabel-Hülse (gesteckt, Buchse sitzt bis an die Leiste) |
| `ACRYL` | 85 / 55 | Acrylplatte unter dem Stapel (von dir gemessen) |
| `STACK_H` | 70 | Acrylplatte bis Oberkante graue Klemmen, ohne Kabel |
| `PINS_H` | 60 | Acrylplatte bis Spitzen der gelben Stifte |
| `STACK_PAT` | 58 / 49 | Lochbild der Bolzen unter der Acrylplatte |

## Aus Datenblatt belegt (11)

| Name | Wert (mm) | Bedeutung |
| --- | --- | --- |
| `SPK_CUT` | 73 | Einbauausschnitt Visaton FRS 8 |
| `SPK_FRAME` | 78 | Außenmaß Korb (Kante) |
| `SPK_FLANGE` | 4,5 | Frontflansch |
| `SPK_DEPTH` | 40 | Gesamttiefe |
| `SPK_MAG` | 60 | Magnet-Ø |
| `NFC_D` | 25 | NFC-Aufkleber Ø |
| `SW` | 12 | Kurzhubtaster 12 × 12 |
| `UPS` | 85 / 56 | Akku-Board Grundriss |
| `OVERHANG` | 20 | Akku-Board steht so weit über den Pi hinaus (85 − 65), BOOT-Taste dort |
| `WAGO5` | 30 / 18,6 / 8,4 | WAGO 221-425 B, T, H |
| `WAGO3` | 18,6 / 18,6 / 8,4 | WAGO 221-423 B, T, H |

## Gestaltung festgelegt (79)

| Name | Wert (mm) | Bedeutung |
| --- | --- | --- |
| `W` | 140 | Außenmaß Breite = Tiefe |
| `HB` | 140 | Höhe Korpus. Echter Würfel; 124 mm reichen für Akku-Stapel + Kartenfach nicht |
| `R` | 16 | Eckradius außen |
| `WALL` | 3 | Wandstärke (7 Linien à 0,42) |
| `BASE_T` | 4 | Bodenplatte, abnehmbar, trägt die Elektronik; Korpus steht darauf |
| `CH_FLOOR` | 2,4 | eigener Boden der Lautsprecherkammer im Korpus (Kammer bleibt dicht) |
| `SHADOW` | 0 | Bodenplatte außen exakt so groß wie der Korpus (bündig) |
| `EDGE_V` | 0,8 | Fase 45° an Korpus-Unterkante und Boden-Oberkante: bilden zusammen eine V-Fuge, kaschiert kleinen Versatz |
| `BASE_CHAMF` | 0,8 | Fase an der Boden-Unterkante (Standkante, gegen Elefantenfuß) |
| `CHAMF` | 0,5 | Fase Unterkante gegen Elefantenfuß (D2) |
| `LID_T` | 6 | Deckelstärke (Schrauben von unten brauchen Fleisch) |
| `LID_SINK` | 1,2 | Deckel liegt so tief unter der Kante |
| `LEDGE` | 2,5 | Auflage-Schräge 45° innen |
| `SKIN` | 0,8 | beige Deckschicht über orangem Kern (D1); 0,8 = 4 Schichten à 0,2 bzw. 5 à 0,16 (vorher 0,7, lag zwischen zwei Schichten) |
| `HOLE3` | 3,4 | Durchgangsloch 3-mm-Schraube |
| `BOSS_D` | 9 | Dom-Ø, groß genug für spätere M3-Einsätze |
| `SEAT` | 12 / 128 / 12 / 128 | Stoffrahmen-Vertiefung x0,x1,z0,z1 |
| `SEAT_D` | 3,8 | Tiefe Stoffrahmen-Sitz |
| `FR_T` | 3 | Stoffrahmen-Dicke |
| `FR_BORDER` | 6 | Rahmenrand |
| `PIN_D` | 4 | Stift am Stoffrahmen |
| `SPK_X` | 70 | Lautsprecher Mitte x |
| `SPK_Z` | 70 | Lautsprecher Mitte z |
| `BAY_D` | 9,6 | Tiefe Lautsprecher-Mulde ab Front |
| `DIV_Y` | 48 | Vorderkante Trennwand Lautsprecherkammer |
| `CH_Z` | 122 | Unterkante Kammerdecke |
| `PADS` | zurück 30 / 30 / 22; play 70 / 30 / 30; vor 110 / 30 / 22; schlaf 70 / 64 / 18 | Touch-Felder x, y, Ø |
| `PAD_RING` | 1,1 | Breite der Ringnut um jedes Touchfeld |
| `SYM_GAP` | 1,8 | Mindestabstand Symbol ↔ Ringnut (Probedruck 27.10.: Dreiecke lagen auf der Nut) |
| `SYM_MIN` | 0,9 | kleinste Breite in Symbolen (2 Linien bei Düse 0,4); dünnere Spitzen werden abgerundet |
| `CARD_W` | 70 | Karte Breite |
| `CARD_H` | 112 | Karte Höhe (70 sichtbar + 42 im Fach) |
| `CARD_T` | 4 | Karte Dicke |
| `CARD_IN` | 42 | Einstecktiefe |
| `SLOT_Y` | 116 | Schlitzmitte auf dem Deckel |
| `TILT` | 8 | Neigung der Karte nach hinten |
| `INS_LIP` | 1,5 | Lippe überdeckt den Einleger je Seite und unten; Unterseite 45°, druckbar ohne Stütze |
| `INS_WALL` | 1,2 | Außenwand neben der Tasche |
| `INS_FRONT` | 0,6 | Lippe an der Fensterkante mindestens so dick |
| `INS_Y0` | 43,5 | Taschenunterkante ab Kartenunterkante (1,5 mm über dem Deckel) |
| `INS_CLR` | 0,3 | Spiel Einleger zur Tasche je Seite |
| `CARD_TOP_R` | 1,5 | Eckradius oben (Tasche ist oben offen und muss gerade bis zur Kante laufen) |
| `GRIP_R` | 7 | Griffmulde oben Mitte in der Rückwand: Einleger von vorn und hinten greifbar |
| `RC_DROP` | 5 | RC522 so viel tiefer (weg vom Deckel) als mittig hinter dem NFC-Aufkleber; Probedruck 27.10.: Steckkabel stießen an den Schraubblock des Deckelrahmens |
| `RC_XTAL_FREE` | 18 | deckelseitige Schiene: Lippe auf so viel Länge vor dem Stiftleisten-Ende entfernt (Quarz; laut Foto ca. 12 mm lang) |
| `BTN_X` | 124,5 | Ein-Taste x (hinten rechts) |
| `BTN_Y` | 108 | Ein-Taste y |
| `BTN_D` | 12 | Tastenkopf-Ø |
| `DISH_D` | 20 | Mulde um die Taste |
| `DISH_DEPTH` | 1,5 | Taste liegt so tief (gegen versehentliches Drücken) |
| `DISH_WALL` | 45 | Mulde um die Taste mit 45°-Wand (kopfüber druckbar, Boden Ø = DISH_D − 2 × DISH_DEPTH) |
| `BTN_MEMBRANE` | 0,2 | Opferschicht über dem Tastenloch am Muldenboden (kopfüber wird der Muldenboden als Brücke gedruckt); nach dem Druck mit Cutter ausschneiden |
| `LID_EDGE_CH` | 0,5 | Fase 45° an der Deckel-Oberkante (kopfüber: verdeckt den Elefantenfuß) |
| `SLOT_CH` | 0,6 | Einführfase am Kartenschlitz oben |
| `ENC_Y` | 84 | Drehgeber y |
| `ENC_Z` | 60 | Drehgeber z |
| `KNOB_D` | 34 | Knopf-Ø |
| `KNOB_L` | 16 | Knopflänge |
| `JK_Y` | 84 | Klinke y |
| `JK_Z` | 24 | Klinke z |
| `STRAP_Y` | 104 | Riemenpunkt y |
| `STRAP_Z` | 118 | Riemenpunkt z |
| `BASE_BOSSES` | 8,6 / 8,6 / 131,4 / 8,6 / 7,7 / 47 / 132,3 / 47 / 8,6 / 131,4 / 131,4 / 131,4 | Bodenschrauben: 4 Ecken + 2 an der Kammerwand (vordere Dome stehen dicht in der Kammer) |
| `BOSS_H` | 14 | Höhe der Bodendome im Korpus; Kernloch 12 tief |
| `CSK` | 6,2 / 3,4 | Senkung für Kunststoffschraube 3,0 × 14 Senkkopf (Ø Kopf, Ø Loch) |
| `LIP` | 1,6 / 3 | Zentrierkragen der Bodenplatte im hinteren Teil (Breite, Höhe) |
| `STACK_X0` | 9 | Stapel links; Überhang mit BOOT-Taste zeigt nach links |
| `STACK_Y0` | 55,5 | Stapel vorne = Kante mit den gelben Stiften; Anschlusskante (USB-C, Schalter) zeigt nach hinten |
| `PAD_H` | 3,5 | Auflagen unter der Acrylplatte |
| `PAD_REC` | 7 / 2,4 | Mulde in jeder Auflage (Ø, Tiefe): vorhandene Schraubenköpfe oder Muttern passen hinein |
| `HOLE25` | 2,9 | Durchgang M2,5 |
| `CB25` | 6,4 / 2,2 | Senkbohrung von unten für Kopf/Mutter M2,5 (Ø, Tiefe) |
| `WIRE_CLR` | 15 | Platz für die Kabel an jeder Klemmreihe |
| `STACK_CLR` | 3 | Luft rings um den Stapel |
| `USB_PLUG` | 20 | Platz hinter der Anschlusskante: Stecker am Akku-Board gewinkelt oder höchstens 20 mm lang |
| `BRIDGE_Y` | 74 / 98 | Verteiler-Brücke am Deckelrahmen: MPR121 + Klemmen für 3,3 V, SCL, GND B |
| `LS_X` | 24 / 116 | Deckelschrauben hinten x |
| `LS_Z` | 124 | Deckelschrauben hinten z |
| `LS_BLOCK_Z0` | 119 | Unterkante der Schraubblöcke hinten am Deckelrahmen (vorher 117; 2 mm mehr Platz für die RC522-Stecker, 3,2 mm Wand unter dem Kernloch) |
