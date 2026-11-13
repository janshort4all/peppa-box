# Prüfbericht Kartenbox (automatisch erzeugt von kartenbox/check.py)

## 1. Netze
OK    basis: Netz wasserdicht, 24720 Dreiecke, 159.3 cm³
OK    deckel: Netz wasserdicht, 11016 Dreiecke, 61.0 cm³
OK    deckel_ohne_haken: Netz wasserdicht, 11000 Dreiecke, 61.0 cm³
OK    inlay: Netz wasserdicht, 1276 Dreiecke, 65.9 cm³
Masse bei massivem Volumen und PETG 1,27 g/cm³ (Obergrenze, Füllung und Wände zählen voll): Basis 202 g, Deckel 78 g, Inlay 84 g, zusammen 364 g (ANNAHME Dichte 1,27 g/cm³)

## 2. Statische Kollisionen (geschlossen, Überschneidungsvolumen in mm³)
OK    Deckel (ohne Haken) ↔ Basis: 0.00 mm³
OK    Inlay ↔ Basis: 0.00 mm³
OK    Inlay ↔ Deckel: 0.00 mm³
OK    30 Karten ganz hinten im Inlay ↔ Basis: 0.00 mm³
OK    30 Karten ganz hinten im Inlay ↔ Inlay: 0.00 mm³
OK    30 Karten ganz hinten im Inlay ↔ Deckel: 0.00 mm³
OK    30 Karten ganz vorn im Inlay ↔ Basis: 0.00 mm³
OK    30 Karten ganz vorn im Inlay ↔ Inlay: 0.00 mm³
OK    30 Karten ganz vorn im Inlay ↔ Deckel: 0.00 mm³

## 3. Fassungsvermögen und Ecken
Fach innen 48.0 mm, 10 Karten = 40.0 mm, frei 8.0 mm je Fach (Karte 70 × 112 × 4 mm aus 10_karte_orange.stl)
Randfach: Kartenlänge 70 mm in 74 mm Inlay-Tiefe → die Randkarte muss mindestens 2.1 mm von der Außenwand weg stehen (Ecken-Rundung); ganz hinten/vorn im Spiel sind es 7 mm. Im Test liegt der linke Stapel an der Trennwand (+7 mm).
OK    Randfach fasst 10 Karten auch bei 7 mm Abstand der Randkarte von der Außenwand (Luft > 0,5 mm)
OK    Gesamtzahl 30 Karten

## 4. Deckel-Schwenk (Rotation um die Scharnierachse, Schritt 1°, 0–125°)
Größte Kippung einer Karte nach vorn/hinten: 3.74° (Wand 3.74°, Inlay-Vorderwand 8.13°) – Schwenkprüfung mit 3.69° (mehr lässt die Basiswand nicht zu)
OK    Deckel ↔ Basis (Wände, Knöchel, Ösen) im ganzen Schwenkbereich frei
OK    Deckel ↔ Karten senkrecht, ganz hinten im Inlay: frei bis 125° (größte Überschneidung 0.0 mm³; Toleranz 2 mm³ ≈ 0,05 mm Eindringtiefe am Grenzfall)
OK    Deckel ↔ Karten senkrecht, ganz vorn im Inlay: frei bis 125° (größte Überschneidung 0.0 mm³; Toleranz 2 mm³ ≈ 0,05 mm Eindringtiefe am Grenzfall)
OK    Deckel ↔ Karten 3.7° nach vorn gekippt: frei bis 125° (größte Überschneidung 0.8 mm³; Toleranz 2 mm³ ≈ 0,05 mm Eindringtiefe am Grenzfall)
OK    Deckel ↔ Karten 3.7° nach hinten gekippt: frei bis 125° (größte Überschneidung 0.0 mm³; Toleranz 2 mm³ ≈ 0,05 mm Eindringtiefe am Grenzfall)

## 5. Scharnier und Verschluss (rechnerisch)
Hakenhöhe 1.20 mm, Spalt zur Basiswand 0.40 mm → Zunge muss beim Schließen 0.80 mm nach außen federn (plus 0,1 mm Reserve für Druckabweichung)
Freie Federlänge 22 mm, Dicke 1.68 mm, Breite 30 mm → Randfaserdehnung 0.47 % (ANNAHME PETG E = 1800 MPa; Streckdehnung PETG ca. 4 %), Federkraft 5.4 N, mit 45°-Flanke und Reibung 0,3 ca. 10 N Öffnungs-/Schließkraft
OK    Biegedehnung der Zunge unter 1 % (Dauerfestigkeit, kein Ermüdungsbruch zu erwarten)
OK    Öffnungskraft unter 10 N, für ein Kind (6 Jahre) machbar (ANNAHME, nicht gemessen → Coupon K2)
Basiswand an der Haken-Nut: 1.52 mm Restwand (Wand 2.52 mm, Nut 1.00 mm tief)
OK    Restwand an der Nut mindestens 1,2 mm (3 Linien)
Scharnier: Knöchelradius 3.5 mm, Wand um den Stift 2.00 mm, Stift Ø 3.0 mm, Stiftlänge 90 mm, Paketlänge 92 mm, Knöchelbreite 18.0 mm
OK    Knöchelwand mindestens 1,5 mm
OK    Scharnierpaket: 5 Knöchel + 4 × Axialspiel = Paketlänge
OK    Stift 90 mm passt zwischen Blindende und rechtes Ende

## 6. Spiele und Wandstärken (aus den Netzen gemessen)
Deckelhaut ↔ Basis (Innenseite der Haut): kleinster Abstand 0.50 mm (Soll 0.40)
OK    Spiel Deckelhaut ↔ Basis eingehalten
Inlay ↔ Basisinnenseite: kleinster Abstand 0.30 mm (Soll 0.30)
OK    Spiel Inlay ↔ Basis eingehalten
Wände: Basis 2.52 mm (6 Linien), Boden 3.0 mm, Deckelwand 1.68 mm (4 Linien), Dach 3.0 mm, Inlay-Wand 2.1 mm, Inlay-Boden 2.0 mm
OK    Wandstärken ≥ 4–5 Linien à 0,42 mm
OK    Karten stehen genau Kartenüberstand über der Fuge
OK    Deckelinnenraum: mindestens 4 mm Luft über den Karten

## 7. Druckbarkeit (Elegoo Centauri Carbon 2: Bauraum 256 × 256 × 256 mm laut Hersteller/Testberichten, Düse 0,4, PETG)
OK    Basis (stehend, Boden auf dem Bett): 186 × 93 × 106 mm passt in 256³
OK    Deckel (Dach auf dem Bett, kopfüber): 162 × 99 × 43 mm passt in 256³
OK    Inlay (stehend): 152 × 78 × 50 mm passt in 256³

Überhänge (Flächen, deren Normale mehr als 45° nach unten geneigt ist, ohne Bettfläche), Flächenanteil an der Gesamtfläche:
  Basis (stehend, Boden auf dem Bett): 329 mm² von 119408 mm² (0.3 %)
     z≈0: 56 mm² (x -78…78, y 1…83)
     z≈100: 150 mm² (x -40…40, y 90…92)
     z≈105: 122 mm² (x -39…40, y 89…91)
  Deckel (Dach auf dem Bett, kopfüber): 721 mm² von 52464 mm² (1.4 %)
     z≈0: 374 mm² (x -80…80, y -85…1)
     z≈20: 131 mm² (x -79…79, y -92…0)
     z≈25: 69 mm² (x -22…22, y -91…-89)
     z≈35: 73 mm² (x -4…-4, y 3…3)
     z≈40: 73 mm² (x 4…4, y 5…5)
  Inlay (stehend): 0 mm² von 66377 mm² (0.0 %)

## 8. Ergebnis
Alle Prüfungen bestanden.
