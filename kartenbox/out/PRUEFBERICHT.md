# Prüfbericht Kartenbox v2 (automatisch erzeugt von kartenbox/check.py)

Außenmaß geschlossen: 240.3 × 102.9 × 122.3 mm (B × T × H, mit Wölbung, ohne Ösen/Scharnier); mit Ösen 264.3 mm breit, mit Scharnier 113.0 mm tief

## 1. Netze und Masse
OK    Basis: wasserdicht, ein zusammenhängender Körper, 36018 Dreiecke, 190.3 cm³
OK    Deckel: wasserdicht, ein zusammenhängender Körper, 38378 Dreiecke, 122.8 cm³
OK    Inlay: wasserdicht, ein zusammenhängender Körper, 60166 Dreiecke, 157.0 cm³
OK    Stift (×2): wasserdicht, ein zusammenhängender Körper, 458 Dreiecke, 0.4 cm³
OK    Karte (v4/out/10_karte_orange.stl): wasserdicht, ein zusammenhängender Körper, 836 Dreiecke, 18.6 cm³
Masse bei massivem Volumen (Obergrenze, ANNAHME Dichte 1.27 g/cm³): Basis 242 g, Deckel 156 g, Inlay 199 g, zusammen 597 g. Gedruckt mit 6 Wänden und 15 % Füllung etwa 70–85 % davon (Wände sind fast überall massiv).

## 2. Geschlossen: Überschneidungen (mm³; 0 = frei)
OK    Deckel ↔ Basis: -0.000
OK    Inlay ↔ Basis: 0.000
OK    Inlay ↔ Deckel: 0.000
OK    Stifte ↔ Deckel (Deckelknöchel muss frei drehen): 0.000
OK    Stifte ↔ Basis: 6.4 mm³ = gewollte Pressung im inneren Basisknöchel (rechnerisch 10.8 mm³ für Ø 4.0 in Ø 3.9)
OK    30 Karten an der Stütze ↔ Basis: 0.000
OK    30 Karten an der Stütze ↔ Inlay: 0.000
OK    30 Karten an der Stütze ↔ Deckel: 0.000
OK    30 Karten seitlich verschoben bis 0,5 mm vor die Fachwand (dx -2.00 mm) ↔ Basis/Inlay/Deckel: 0.000
OK    30 Karten seitlich verschoben bis 0,5 mm vor die Fachwand (dx +2.00 mm) ↔ Basis/Inlay/Deckel: 0.000
OK    senkrechte Einzelkarte überall im Fach (ab 5 mm hinter der Fachwand, alle Fächer, quer mittig) passt unter den geschlossenen Deckel: größte Überschneidung 0.003 mm³
Hinweis: senkrechte Karte im Randfach ganz an die Stirnwand geschoben: Kartenecke berührt die Deckelrundung (größte Überschneidung 5.9 mm³, Ecke R 1,5); der schließende Deckel schiebt sie zur Mitte. Der normale Zustand (Stapel lehnt an der Stütze) ist in jeder Querlage frei.
Senkrechte Karte direkt an der Fachwand vorn (mittig): ebenfalls frei.
OK    Inlay lässt sich senkrecht einsetzen und herausziehen (an der Verschluss-Verstärkung vorbei): größte Überschneidung 0.000 mm³
OK    Stifte lassen sich von außen entlang der Achse einschieben (nichts im Weg außer den Knöcheln): 0.000 mm³

## 3. Fassungsvermögen
Mittleres Fach: Vorderwand springt auf 45 mm Breite hinter die Verschluss-Verstärkung zurück, dort 13.6 mm frei vor dem Stapel
OK    je Fach 10 Karten: Stapel 41.4 mm (waagerecht am Boden, 15° Neigung), davor 14.0 mm frei zum Greifen
OK    Fach 75 mm breit, Karte 70 mm: 5 mm Luft quer
Karten-Oberkante: 113.3 mm (geneigt) bzw. 116.1 mm (senkrecht); Deckeldecke innen 119.8 mm; Basisrand 78 mm
Cover-Fenster der Karte beginnt 43.5 mm über der Kartenunterkante (v4: INS_Y0) → sichtbar ab ca. 46 mm Höhe; Griffmulden im Inlay bis 52 mm hinunter, Basisrand 78 mm

## 4. Deckelschwenk um die Scharnierachse (Schritt 1°)
OK    0° bis Anschlag: Deckel frei gegenüber Basis (außer Rasthaken), Inlay und 30 Karten (größte Überschneidung 0.000 mm³)
OK    Öffnungsanschlag (Nase am Deckelknöchel trifft die Rückwand) bei 96° – Deckel kippt über die Senkrechte und bleibt offen
OK    Schwerpunkt des offenen Deckels +34.9 mm hinter der Achse → fällt nicht zu
Rasthaken beim Schließen: größte Überdeckung mit der Basis 0.68 mm (Federweg der Zunge; Soll 0.80 mm)
OK    Haken überdeckt nur so weit, wie die Zunge federn soll
OK    geschlossen sitzt der Haken frei in der Rastnut (-0.000 mm³), senkrechtes Spiel 0.2 mm
OK    Basisknöchel ↔ Deckelrückwand: kleinster Abstand 0.64 mm (gleicher Radius beim Drehen, keine Berührung)

## 5. Verschluss und Scharnier (rechnerisch)
Zunge 30 × 2.0 mm, freie Länge 27 mm, Federweg 0.80 mm → Randdehnung 0.33 %, Federkraft 4.4 N (ANNAHME E = 1800 MPa)
OK    Dehnung unter 0,6 % (Biegung geht quer zu den Schichten, daher niedrig gehalten; PETG-Streckdehnung ca. 4 %)
Öffnen: Griffnase 1.2 mm nach außen ziehen (ca. 4 N), dann Deckel heben. Schließen: Haken gleitet über die 30°-Schräge, ca. 5 N, hörbares Einrasten.
Haltefläche 60° gegen die Zugrichtung: Deckel ohne Betätigen der Zunge aufreißen braucht ca. 19 N (Reibung 0.3, ANNAHME). Bei Gewalt springt der Haken heraus, statt zu brechen.
OK    Verschluss hält mindestens das Dreifache der Betätigungskraft und ≥ 15 N (Tragen, Umkippen)
OK    Öffnungskraft an der Zunge höchstens 10 N (6-Jähriger, ANNAHME; Coupon K2 prüft)
OK    Restwand hinter der Rastnut 2.00 mm (≥ 4 Linien)
Scharnier: 2 × 3 Knöchel (Basis 9 / Deckel 14 / Basis 9 mm, Spiel 0.5 mm), Knöchel R 5.0 mm, Stift Ø 4.0 gedruckt (Bohrungen: außen 4.15, Deckel 4.6, innen 3.9 klemmt)
OK    Wand um die Deckelbohrung 2.70 mm
OK    Wand um die Basisbohrungen 2.92 mm
OK    Deckelknöchel dreht frei: 0.30 mm Luft je Seite

## 6. Wandstärken (gemessen an den Netzen)
Außenhaut ↔ Innenraum (ohne V-Fuge): kleinste 2.40 mm, Median 2.52 mm
OK    Wand überall ≥ 2.35 mm
an der V-Fuge: kleinste Wand 1.70 mm (Fuge 0.8 mm tief, nur auf ±0.8 mm Höhe)
OK    Wand an der V-Fuge ≥ 1,6 mm
Inlay 1.68 mm (4 Linien), Inlay-Boden 1.6 mm; Basisboden 2.5 mm; Deckeldach 2.5 mm
OK    Öse: Wand außen 3.8 mm, zur Box hin 3.0 mm

## 7. Standfestigkeit (Kippen)
OK    geschlossen, 30 Karten: Schwerpunkt y +2.2 / z 49.6 mm, kippt nach hinten erst bei 39°, nach vorn bei 42° (Masse ca. 970 g, ANNAHME Karte 75 % gefüllt)
OK    leer, Deckel offen am Anschlag: Schwerpunkt y +28.4 / z 60.9 mm, kippt nach hinten erst bei 13°, nach vorn bei 49° (Masse ca. 438 g, ANNAHME Karte 75 % gefüllt)
OK    30 Karten, Deckel offen: Schwerpunkt y +13.8 / z 52.5 mm, kippt nach hinten erst bei 28°, nach vorn bei 47° (Masse ca. 970 g, ANNAHME Karte 75 % gefüllt)

## 8. Druckbarkeit (Elegoo Centauri Carbon 2: 256 × 256 × 256 mm, Herstellerangabe; Düse 0,4; PETG)
OK    basis in Druckausrichtung 225 × 225 × 83 mm (≤ 250, 3 mm Rand)
OK    basis: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    deckel in Druckausrichtung 240 × 117 × 55 mm (≤ 250, 3 mm Rand)
OK    deckel: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    inlay in Druckausrichtung 235 × 97 × 81 mm (≤ 250, 3 mm Rand)
OK    inlay: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    stift in Druckausrichtung 33 × 6 × 5 mm (≤ 250, 3 mm Rand)
OK    stift: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
- basis: Überhang > 45° 113 mm², davon waagerecht (Brücke) 0 mm²
    z≈69: 36 mm² (x 31…38, y -38…-31)
    z≈81: 76 mm² (x -100…22, y -22…99)
- deckel: Überhang > 45° 83 mm², davon waagerecht (Brücke) 0 mm²
    z≈51: 83 mm² (x -5…5, y 54…58)
- inlay: Überhang > 45° 2543 mm², davon waagerecht (Brücke) 2543 mm²
    z≈78: 2543 mm² (x -113…113, y 34…46)
- stift: Überhang > 45° 0 mm², davon waagerecht (Brücke) 0 mm²

Erwartete Überhänge (bewusst): Bohrungen als Tropfen (Spitze 45°), Brücke über den Hohlräumen des Inlays (Dach ≤ 14 mm Spannweite), Haltefläche von Haken und Rastnut (30° zur Waagerechten, 1 mm breit), Unterseite der Stiftrundung direkt über dem Bett.
Haftfläche: Basis 224 × 85 mm, Deckel-Dach 220 × 80 mm – kein Brim nötig

## 9. Ergebnis
Alle Prüfungen bestanden.

## 10. Gegenprüfung (zweite Methode: Schichten wie im Slicer, 0,2 mm, aus den fertigen STL)
Freie Fläche = Teil einer Schicht, der nicht auf der Schicht darunter (um 0,2 mm = 45° erweitert) steht. Schmal = Stellen unter 0,42 mm Linienbreite.
- **01_basis_orange.stl** (415 Schichten): frei 11 mm² in 3 Schichten; schmal 0 mm² in 0 Schichten
    z 70.3–70.7: 11 mm² (x 23…46, y -46…-23)
- **02_deckel_orange_kopfueber.stl** (277 Schichten): frei 13 mm² in 3 Schichten; schmal 16 mm² in 2 Schichten
    z 51.9–52.3: 13 mm² (x -14…14, y 54…58)
    schmal z 55.1–55.1: 11 mm²
- **03_inlay_beige.stl** (402 Schichten): frei 2448 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 78.9–78.9: 2448 mm² (x -115…115, y 34…46)
- **04_stift_3x_beige.stl** (25 Schichten): frei 5 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 0.3–0.3: 5 mm² (x -16…15, y -11…11)
- **probedruck/K1a_scharnier_basis.stl** (143 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K1b_scharnier_deckel_kopfueber.stl** (145 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K1c_stifte_3.9_4.0_4.1.stl** (25 Schichten): frei 5 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 0.3–0.3: 5 mm² (x -16…15, y -1…21)
- **probedruck/K2a_verschluss_basis.stl** (148 Schichten): frei 11 mm² in 3 Schichten; schmal 0 mm² in 0 Schichten
    z 21.9–22.3: 11 mm² (x -15…15, y -0…0)
- **probedruck/K2b_verschluss_deckel_kopfueber.stl** (183 Schichten): frei 12 mm² in 3 Schichten; schmal 5 mm² in 1 Schichten
    z 33.1–33.5: 12 mm² (x -14…14, y -2…2)
- **probedruck/K3a_passung_basis.stl** (50 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K3b_passung_inlay.stl** (75 Schichten): frei 242 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 13.5–13.5: 242 mm² (x -14…11, y 33…44)
- **probedruck/K3c_passung_deckel_kopfueber.stl** (50 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
