# Prüfbericht Kartenbox v3 – Stülpdeckel und Klemmlasche (automatisch erzeugt von kartenbox/check.py)

Außenmaß geschlossen: 244.4 × 106.9 × 122.3 mm (B × T × H, mit Wölbung, ohne Ösen/Scharnier/Lasche); mit Ösen 268.4 mm breit, mit Scharnier und Lasche 126.2 mm tief. Fuge (Auflage des Deckels) auf 66 mm, Hals bis 78 mm, Deckel stülpt sich 12 mm über den Hals.

## 1. Netze und Masse
OK    Basis: wasserdicht, ein zusammenhängender Körper, 48510 Dreiecke, 274.7 cm³
OK    Deckel: wasserdicht, ein zusammenhängender Körper, 40752 Dreiecke, 141.2 cm³
OK    Inlay: wasserdicht, ein zusammenhängender Körper, 60968 Dreiecke, 156.8 cm³
OK    Klemmlasche: wasserdicht, ein zusammenhängender Körper, 292 Dreiecke, 4.5 cm³
OK    Scharnierstift (×2): wasserdicht, ein zusammenhängender Körper, 458 Dreiecke, 0.4 cm³
OK    Laschenstift: wasserdicht, ein zusammenhängender Körper, 444 Dreiecke, 0.4 cm³
OK    Karte (v4/out/10_karte_orange.stl): wasserdicht, ein zusammenhängender Körper, 836 Dreiecke, 18.6 cm³
Masse bei massivem Volumen (Obergrenze, ANNAHME Dichte 1.27 g/cm³): Basis 349 g, Deckel 179 g, Inlay 199 g, Lasche 6 g, zusammen 733 g. Die Basis ist unter der Fuge 4.5 mm dick (Stufe für den Deckel); mit 4 Wandschleifen und 15 % Füllung ist sie innen teils gefüllt statt massiv.

## 2. Geschlossen: Überschneidungen (mm³; 0 = frei)
OK    Deckel ↔ Basis: 0.000
OK    Inlay ↔ Basis: 0.000
OK    Inlay ↔ Deckel: 0.000
OK    Klemmlasche ↔ Basis (Haken frei in der Nut): 0.000
OK    Klemmlasche ↔ Deckel: 0.000
OK    Laschenstift ↔ Lasche (Lasche dreht): 0.000
OK    Laschenstift ↔ Basis: 0.000
OK    Scharnierstifte ↔ Deckel (Deckelknöchel muss frei drehen): 0.000
OK    Stifte ↔ Basis: 6.4 mm³ = gewollte Pressung im inneren Basisknöchel (rechnerisch 10.8 mm³ für Ø 4.0 in Ø 3.9)
OK    Laschenstift ↔ Deckel: 2.1 mm³ = gewollte Pressung im linken Lagerbock (rechnerisch 2.9 mm³)
OK    30 Karten an der Stütze ↔ Basis: 0.000
OK    30 Karten an der Stütze ↔ Inlay: 0.000
OK    30 Karten an der Stütze ↔ Deckel: 0.000
OK    30 Karten seitlich verschoben bis 0,5 mm vor die Fachwand (dx -2.00 mm) ↔ Basis/Inlay/Deckel: 0.000
OK    30 Karten seitlich verschoben bis 0,5 mm vor die Fachwand (dx +2.00 mm) ↔ Basis/Inlay/Deckel: 0.000
OK    senkrechte Einzelkarte überall im Fach (ab 5 mm hinter der Fachwand, alle Fächer, quer mittig) passt unter den geschlossenen Deckel: größte Überschneidung 0.000 mm³
Hinweis: senkrechte Karte im Randfach ganz an die Stirnwand geschoben: Kartenecke berührt die Deckelrundung (größte Überschneidung 0.0 mm³, Ecke R 1,5); der schließende Deckel schiebt sie zur Mitte. Der normale Zustand (Stapel lehnt an der Stütze) ist in jeder Querlage frei.
Senkrechte Karte direkt an der Fachwand vorn (mittig): ebenfalls frei.
OK    Inlay lässt sich senkrecht einsetzen und herausziehen: größte Überschneidung 0.000 mm³
OK    Scharnierstifte lassen sich von außen entlang der Achse einschieben (nichts im Weg außer den Knöcheln): 0.000 mm³
OK    Laschenstift lässt sich von rechts durch Lagerbock und Lasche einschieben: 0.000 mm³

## 3. Fassungsvermögen
OK    je Fach 10 Karten: Stapel 41.4 mm (waagerecht am Boden, 15° Neigung), davor 14.0 mm frei zum Greifen
OK    Fach 75 mm breit, Karte 70 mm: 5 mm Luft quer
Karten-Oberkante: 113.3 mm (geneigt) bzw. 116.1 mm (senkrecht); Deckeldecke innen 119.8 mm; Halsoberkante 78 mm
Cover-Fenster der Karte beginnt 43.5 mm über der Kartenunterkante (v4: INS_Y0) → sichtbar ab ca. 46 mm Höhe; Griffmulden im Inlay bis 52 mm hinunter, Halsoberkante 78 mm

## 4. Deckelschwenk um die Scharnierachse (Schritt 1°)
OK    0° bis Anschlag: Deckel mit Lasche frei gegenüber Basis (Hals, Stufe, Scharnier; außer Haken in der Nut), Inlay und 30 Karten (größte Überschneidung 0.000 mm³)
OK    Öffnungsanschlag (Nase am Deckelknöchel trifft die Rückwand) bei 95° – Deckel kippt über die Senkrechte und bleibt offen
OK    Schwerpunkt des offenen Deckels +42.8 mm hinter der Achse → fällt nicht zu
Haken beim Schließen/Öffnen: größte Überdeckung mit der Basis 2.28 mm quer (Federweg der Lasche; Soll 2.40 mm)
OK    Haken überdeckt nur so weit, wie die Lasche federn soll
Vorspannung eingebaut: der Druckpunkt unten liegt an der Basis an (gedruckt 1.64 mm weiter innen); der Haken steht dann 0.20 mm tiefer in der Nut als gezeichnet, Luft zur Nutrückwand bleibt 0.20 mm
OK    Vorspannung geht über den Druckpunkt, der Haken bleibt frei in der Nut
OK    geschlossen sitzt der Haken frei in der Rastnut (0.000 mm³), senkrechtes Spiel 0.2 mm
OK    Basisknöchel ↔ Deckelrückwand: kleinster Abstand 0.64 mm (gleicher Radius beim Drehen, keine Berührung)

## 5. Klemmlasche und Scharnier (rechnerisch)
Feder der Lasche 22 × 1.8 mm; Wurzel → Haken 27 mm, → Griffnase 35 mm. Gedruckt um 1.64 mm vorgebogen: geschlossen drückt sie mit ca. 2.0 N gegen die Basis (kein Klappern, Haken bleibt in der Nut).
Öffnen: Haken 2.4 mm aus der Nut ziehen braucht an der Griffnase ca. 6.9 N; Randdehnung an der Wurzel 1.14 % (ANNAHME E = 1800 MPa)
OK    Dehnung unter 1,5 %: Lasche liegt beim Druck auf der Seite, die Biegung läuft entlang der Schichten (PETG-Streckdehnung ca. 4 %)
Zum Vergleich: wer die Griffnase 10 mm vom Deckel abbiegt, dehnt die Feder um 2.2 % – unter der Streckdehnung, sie bricht dabei nicht (die v2-Zunge bog quer zu den Schichten).
OK    Öffnen mit einem Finger hinter der Griffnase (6 mm Vorsprung): ca. 7 N (Kinderhand; ANNAHME, Probedruck K2 prüft)
OK    Schließen höchstens 15 N (Deckel mit der Hand zudrücken): ca. 10 N
Schließen: Deckel zudrücken, der Haken gleitet mit seiner 30°-Schräge über die Kante der Stufe und schnappt in die Nut, ca. 10 N (Reibung 0.3, ANNAHME).
Halten: Haltefläche von Haken und Nut liegt waagerecht (90° zur Zugrichtung). Zug am Deckel drückt den Haken nicht heraus – der Deckel geht nur auf, wenn die Lasche an der Griffnase nach vorn gezogen wird. Kraft geht als Zug durch die Feder in den Stift.
Spiel der Lasche: Stift Ø 4.0 in Ø 4.3 (0.15 mm je Seite), Kopf liegt am Deckel an; schlimmstenfalls weicht der Haken um ca. 0.2 mm nach außen – es bleiben ≥ 1.8 mm Eingriff (mit 0,3 mm Kantenrundung im Druck). Die Vorspannung hält die Lasche ohnehin angelegt.
OK    Eingriff auch im ungünstigen Fall ≥ 1,5 mm
Grobe Tragkraft (ANNAHMEN Scherfestigkeit): Hakenwurzel ca. 495 N, Stift zweischnittig ca. 251 N. Deckel wiegt ca. 179 g.
OK    Verschluss trägt ein Vielfaches dessen, was beim Tragen und Umkippen am Deckel zieht (≥ 100 N)
OK    Restwand der Basis hinter der Rastnut 1.73 mm (≥ 4 Linien)
OK    Hals an der Rinne für den Haken 1.73 mm (wie oben am Hals; vom Deckel verdeckt)
Lagerböcke: Stift Ø 4.0 (wie Scharnier), rechts Bohrung 4.15 (schiebt sich durch) mit Senkung für den Kopf, links 3.9 (klemmt), Lasche 4.3 (dreht mit wenig Spiel). Der Laschenkopf liegt flach am Deckel an: die Lasche kann nicht nach innen umklappen, Ziehen an der Griffnase biegt nur die Feder.
OK    Wand um die Bohrung im Lagerbock 2.72 mm
OK    Wand um die Bohrung im Laschenkopf 2.10 mm
Scharnier: 2 × 3 Knöchel (Basis 9 / Deckel 14 / Basis 9 mm, Spiel 0.5 mm), Knöchel R 5.0 mm, Stift Ø 4.0 gedruckt (Bohrungen: außen 4.15, Deckel 4.6, innen 3.9 klemmt). Achse jetzt auf Höhe der Fuge (66 mm), damit der Deckelrand hinten beim Öffnen vom Hals weg schwenkt.
OK    Lasche dreht auf dem Stift: 0.15 mm Luft je Seite
OK    Wand um die Deckelbohrung 2.70 mm
OK    Wand um die Basisbohrungen 2.92 mm
OK    Deckelknöchel drehen frei: 0.30 mm Luft je Seite

## 6. Wandstärken und Spiele (gemessen an den Netzen)
Basis unter der Fuge (ohne Fugenfase) (Bereich z 13…62 mm): kleinste 4.34 mm, Median 4.65 mm (Hilfskanten der Messkörper ausgespart)
OK    Basis unter der Fuge (ohne Fugenfase): Wand ≥ 4.28 mm
Hals (unten → oben verjüngt) (Bereich z 69…76 mm): kleinste 1.76 mm, Median 2.12 mm (Hilfskanten der Messkörper ausgespart)
OK    Hals (unten → oben verjüngt): Wand ≥ 1.55 mm
Deckelrand über dem Hals: kleinste 1.60 mm (Soll 1.68)
OK    Deckelrand ≥ 1.53 mm
Spiel Deckelrand ↔ Hals auf 66.5 mm: kleinstes 0.37 mm, größtes 0.40 mm
Spiel Deckelrand ↔ Hals auf 72.0 mm: kleinstes 0.72 mm, größtes 0.79 mm
Spiel Deckelrand ↔ Hals auf 77.2 mm: kleinstes 1.05 mm, größtes 1.15 mm
OK    Hals verjüngt sich um 0.8 mm nach oben; das Spiel wächst von 0.35 auf 1.15 mm (geführt wird unten am Halsfuß)
Auflage des Deckels auf der Stufe: Ring 1.18 mm breit (Deckelrand 1.68 mm minus Fugenfase 0.5 mm); an der Fugenfase ist die Basiswand 4.03 mm
OK    Deckel liegt auf einem Ring ≥ 1 mm auf
Inlay 1.68 mm (4 Linien), Inlay-Boden 1.6 mm; Basisboden 2.5 mm; Deckeldach 2.5 mm
OK    Öse: Wand außen 3.8 mm, zur Box hin 3.0 mm

## 7. Standfestigkeit (Kippen)
OK    geschlossen, 30 Karten: Schwerpunkt y +1.8 / z 48.8 mm, kippt nach hinten erst bei 41°, nach vorn bei 43° (Masse ca. 1080 g, ANNAHME Karte 75 % gefüllt)
OK    leer, Deckel offen am Anschlag: Schwerpunkt y +29.4 / z 57.0 mm, kippt nach hinten erst bei 15°, nach vorn bei 52° (Masse ca. 548 g, ANNAHME Karte 75 % gefüllt)
OK    30 Karten, Deckel offen: Schwerpunkt y +15.8 / z 51.4 mm, kippt nach hinten erst bei 29°, nach vorn bei 49° (Masse ca. 1080 g, ANNAHME Karte 75 % gefüllt)

## 8. Druckbarkeit (Elegoo Centauri Carbon 2: 256 × 256 × 256 mm, Herstellerangabe; Düse 0,4; PETG)
OK    basis in Druckausrichtung 229 × 229 × 78 mm (≤ 250, 3 mm Rand)
OK    basis: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    deckel in Druckausrichtung 244 × 129 × 62 mm (≤ 250, 3 mm Rand)
OK    deckel: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    inlay in Druckausrichtung 235 × 97 × 81 mm (≤ 250, 3 mm Rand)
OK    inlay: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    lasche in Druckausrichtung 53 × 11 × 22 mm (≤ 250, 3 mm Rand)
OK    lasche: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    stift in Druckausrichtung 33 × 6 × 5 mm (≤ 250, 3 mm Rand)
OK    stift: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
OK    laschenstift in Druckausrichtung 32 × 6 × 5 mm (≤ 250, 3 mm Rand)
OK    laschenstift: Druckausrichtung ist eine reine Drehung (Volumen gleich, keine Spiegelung im Code)
- basis: Überhang > 45° 142 mm², davon waagerecht (Brücke) 65 mm²
    z≈57: 65 mm² (x 30…45, y -45…-30)
    z≈69: 76 mm² (x -103…18, y -20…103)
- deckel: Überhang > 45° 0 mm², davon waagerecht (Brücke) 0 mm²
- inlay: Überhang > 45° 2543 mm², davon waagerecht (Brücke) 2543 mm²
    z≈78: 2543 mm² (x -113…113, y 34…46)
- lasche: Überhang > 45° 0 mm², davon waagerecht (Brücke) 0 mm²
- stift: Überhang > 45° 0 mm², davon waagerecht (Brücke) 0 mm²
- laschenstift: Überhang > 45° 0 mm², davon waagerecht (Brücke) 0 mm²

Erwartete Überhänge (bewusst): Bohrungen als Tropfen (Spitze 45°, zählen wegen Rundung auf genau 45° mit), Brücke über den Hohlräumen des Inlays (Dach ≤ 14 mm Spannweite), Haltefläche der Rastnut in der Basis (waagerecht, 3.8 mm tief, 23.2 mm breit: druckt als kurze Brücke zwischen den Nutwänden), Unterseite der Stiftrundung direkt über dem Bett. Die Lasche liegt auf der Seite: alle Formen liegen in der Druckebene, keine Überhänge.
Haftfläche: Basis 228 × 89 mm, Deckel-Dach 224 × 84 mm – kein Brim nötig

## 9. Ergebnis
Alle Prüfungen bestanden.

## 10. Gegenprüfung (zweite Methode: Schichten wie im Slicer, 0,2 mm, aus den fertigen STL)
Freie Fläche = Teil einer Schicht, der nicht auf der Schicht darunter (um 0,2 mm = 45° erweitert) steht. Schmal = Stellen unter 0,42 mm Linienbreite.
- **01_basis_orange.stl** (390 Schichten): frei 59 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 58.3–58.3: 59 mm² (x 28…46, y -46…-28)
- **02_deckel_orange_kopfueber.stl** (309 Schichten): frei 0 mm² in 0 Schichten; schmal 5 mm² in 1 Schichten
- **03_inlay_beige.stl** (402 Schichten): frei 2448 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 78.9–78.9: 2448 mm² (x -115…115, y 34…47)
- **04_stifte_beige_3_scharnier_2_lasche.stl** (25 Schichten): frei 9 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 0.3–0.3: 9 mm² (x -16…15, y -11…31)
- **05_klemmlasche_beige_auf_der_seite.stl** (110 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K1a_scharnier_basis.stl** (178 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K1b_scharnier_deckel_kopfueber.stl** (155 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K1c_stifte_3.9_4.0_4.1.stl** (25 Schichten): frei 5 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 0.3–0.3: 5 mm² (x -16…15, y -1…21)
- **probedruck/K2a_lasche_basis.stl** (193 Schichten): frei 59 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 18.9–18.9: 59 mm² (x -11…11, y -2…0)
- **probedruck/K2b_lasche_deckel_kopfueber.stl** (210 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K2c_lasche_feder_1.6.stl** (110 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K2c_lasche_feder_1.8.stl** (110 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K2c_lasche_feder_2.0.stl** (110 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K2d_laschenstifte_3.9_4.0_4.1.stl** (25 Schichten): frei 5 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 0.3–0.3: 5 mm² (x -16…14, y -1…21)
- **probedruck/K3a_passung_basis.stl** (100 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/K3b_passung_inlay.stl** (125 Schichten): frei 242 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 23.5–23.5: 242 mm² (x -14…11, y 33…45)
- **probedruck/K3c_passung_deckel_kopfueber.stl** (110 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
