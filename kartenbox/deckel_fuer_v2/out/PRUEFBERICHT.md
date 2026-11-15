# Prüfbericht: neuer Deckel für die gedruckte Basis v2 (automatisch erzeugt von deckel_fuer_v2/check_deckel.py)

Basis = Kartenbox v2 (Commit e8504ba, model_v2.py), unverändert. Deckel außen 244.4 × 104.9 × 122.3 mm (vorn und seitlich 2.03 mm über der Basis, hinten bündig), Stülprand bis 68 mm (10 mm über die Basis).

## 1. Netze
OK    Deckel: wasserdicht, ein Körper, 142.90 cm³ ≈ 181 g massiv
OK    Rasteinsatz: wasserdicht, ein Körper, 0.50 cm³ ≈ 1 g massiv
OK    Klemmlasche: wasserdicht, ein Körper, 4.11 cm³ ≈ 5 g massiv
OK    Laschenstift: wasserdicht, ein Körper, 0.42 cm³ ≈ 1 g massiv
OK    Lasche wie gedruckt (vorgebogen): wasserdicht, ein Körper, 4.10 cm³ ≈ 5 g massiv

## 2. Geschlossen (Überschneidung in mm³)
OK    Deckel ↔ Basis: 0.000
OK    Deckel ↔ Inlay: 0.000
OK    Deckel ↔ 30 Karten: 0.000
OK    Deckel ↔ Rasteinsatz: 0.000
OK    Rasteinsatz ↔ Basis (Zahn frei in der Rastnut): 0.000
OK    Rasteinsatz ↔ Inlay: 0.000
OK    Klemmlasche ↔ Basis: 0.000
OK    Klemmlasche ↔ Rasteinsatz (Haken frei darunter): 0.000
OK    Klemmlasche ↔ Deckel: 0.000
OK    Laschenstift ↔ Lasche: 0.000
OK    Scharnierstifte ↔ Deckel: 0.000
OK    Laschenstift ↔ Deckel: 2.1 mm³ = gewollte Pressung im linken Lagerbock (rechnerisch 2.9)
OK    Rasteinsatz lässt sich waagerecht von vorn in die Mulde schieben, Zahn voran in die Rastnut: 0.000 mm³
OK    Laschenstift lässt sich von rechts einschieben: 0.000 mm³
Haken in der Fingermulde der Basis: kleinster Abstand zur Mulde 0.53 mm
OK    Haken hat in der Fingermulde Luft (≥ 0,2 mm)

## 3. Deckelschwenk (um die Scharnierachse der Basis, 1°-Schritte)
OK    0° bis Anschlag frei: Stülprand (vorn, seitlich, schräger Auslauf hinten), Lasche, Inlay, 30 Karten (größte Überschneidung 0.000 mm³)
OK    Anschlag wie v2 bei 96°: Deckel bleibt offen stehen
OK    Schwerpunkt des offenen Deckels +32.2 mm hinter der Achse
Haken beim Schließen: größte Überdeckung quer 0.98 mm (= Federweg, höchstens 1.40 mm)
OK    Haken überdeckt höchstens so weit, wie die Lasche federn soll (in 1°-Schritten gemessen)
Reserve: Basis außen 0,2 mm dicker gedruckt (ohne Scharnierbereich): Überschneidung beim Aufschwenken 0.000 mm³
OK    Stülprand schwenkt auch bei 0,2 mm Übermaß der Basis frei

## 4. Verschluss (rechnerisch)
Feder 22 × 1.6 mm; Wurzel → Haken 19 mm, → Griffnase 28 mm; gedruckt 1.05 mm vorgebogen → drückt geschlossen mit ca. 2.0 N unten an die Basis
Öffnen: Haken 1.4 mm unter dem Einsatz hervorziehen, an der Griffnase ca. 6.9 N; Dehnung an der Wurzel 1.16 % (ANNAHME E = 1800 MPa)
OK    Dehnung < 1,5 % (Lasche auf der Seite gedruckt, Biegung entlang der Schichten)
OK    Öffnen mit einem Finger hinter der Griffnase: ca. 7 N
OK    Schließen: Deckel zudrücken, Haken gleitet über die Fase des Einsatzes und schnappt darunter, ca. 12 N
OK    Vorspannung über den Druckpunkt: Haken steht 0.15 mm weiter innen als gezeichnet, Luft in der Mulde bleibt 0.37 mm
Halten: Hakenoberseite und Unterkante des Einsatzes sind waagerecht – Zug am Deckel drückt den Haken nicht heraus. Der Einsatz hängt mit seinem Zahn in der alten Rastnut (30°); die schräge Fläche will ihn dabei nach vorn drücken, daran hindert ihn der Stülprand (0.35 mm Luft, Zahn steckt 0.8 mm in der Nut).
OK    Einsatz kann unter Zug höchstens bis zum Stülprand ausweichen und bleibt dabei in der Nut (≥ 0,3 mm Rest)
OK    Stülprand reicht bis 68 mm, deckt den Einsatz auf Höhe der Rastnut (70–71 mm) ab
Grobe Tragkraft (ANNAHMEN Scherfestigkeit 10–15 MPa): Haken 360 N, Stift 251 N, Zahn des Einsatzes 463 N, Rand der Rastnut in der Basis 463 N. Deckel wiegt ca. 181 g.
OK    Verschluss trägt ≥ 100 N (Tragen, Umkippen, Box auf dem Kopf mit Karten)

## 5. Wände
Stülprand: kleinste 1.60 mm, Median 1.70 mm
OK    Stülprand ≥ 1.53 mm
Deckelwand oberhalb: kleinste 2.50 mm
OK    Deckelwand ≥ 2.3 mm
Rasteinsatz 30.9 × 2.3 × 6.0 mm (B × T × H), Seitenluft je 0.15 mm
Bandösen: Oberkante ca. 67 mm, Stülprand endet 1.0 mm darüber
OK    Stülprand berührt die Ösen nicht

## 6. Druck (Centauri Carbon 2, 256³, PETG)
OK    deckel in Druckausrichtung 244 × 127 × 54 mm
    Überhang > 45°: 859 mm² (Tropfenbohrungen zählen mit)
OK    einsatz in Druckausrichtung 31 × 6 × 3 mm
    Überhang > 45°: 0 mm² (Tropfenbohrungen zählen mit)
OK    lasche in Druckausrichtung 46 × 13 × 22 mm
    Überhang > 45°: 3 mm² (Tropfenbohrungen zählen mit)

## 7. Ergebnis
Alle Prüfungen bestanden.

## 10. Gegenprüfung (zweite Methode: Schichten wie im Slicer, 0,2 mm, aus den fertigen STL)
Freie Fläche = Teil einer Schicht, der nicht auf der Schicht darunter (um 0,2 mm = 45° erweitert) steht. Schmal = Stellen unter 0,42 mm Linienbreite.
- **02n_deckel_orange_kopfueber.stl** (272 Schichten): frei 14 mm² in 8 Schichten; schmal 5 mm² in 1 Schichten
    z 36.9–38.3: 14 mm² (x -119…119, y -32…51)
- **04n_laschenstifte_2_beige.stl** (25 Schichten): frei 4 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
- **05n_klemmlasche_beige_auf_der_seite.stl** (110 Schichten): frei 2 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
- **06_rasteinsatz_beige_auf_der_vorderseite.stl** (16 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/N1a_lasche_deckelstueck_kopfueber.stl** (205 Schichten): frei 4 mm² in 8 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/N1b_lasche_feder_1.4.stl** (110 Schichten): frei 2 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/N1b_lasche_feder_1.6.stl** (110 Schichten): frei 2 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/N1b_lasche_feder_1.8.stl** (110 Schichten): frei 2 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/N1c_rasteinsatz.stl** (16 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
- **probedruck/N1d_laschenstifte_3.9_4.0_4.1.stl** (25 Schichten): frei 5 mm² in 1 Schichten; schmal 0 mm² in 0 Schichten
    z 0.3–0.3: 5 mm² (x -16…14, y -1…21)
- **probedruck/N2_ecke_stuelprand_kopfueber.stl** (98 Schichten): frei 0 mm² in 0 Schichten; schmal 0 mm² in 0 Schichten
