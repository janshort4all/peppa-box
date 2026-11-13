# Kartenbox v2 – 30 Peppa-Karten fürs Kinderzimmer

Stand 11.11.2026. Ersetzt den ersten Entwurf (liegt in `v1_entwurf/`).
Parametrisches Modell `model.py` (manifold3d), jede Größe mit Status in `P_` (belegt / festgelegt / berechnet / Probedruck).

## Idee
- 3 Fächer à 10 Karten nebeneinander, **Cover zeigen nach vorn**. Die Karten lehnen um 15° an einer schrägen Stütze:
  Das Kind sieht die Cover schräg von oben, und die Box wird tiefer und damit standfester.
- Weiche, kissenartige Form: große Rundungen oben/unten, Grundriss-Ecken R 15, Längsseiten 2,5 mm und Stirnseiten 1,5 mm nach außen gewölbt,
  feine V-Fuge zwischen Basis und Deckel. Außen Fuzzy Skin, Passflächen glatt.
- **Beiges Inlay** mit Griffmulden vorn; sein Rand ragt 5 mm über die Basis in den Deckel (führt den Deckel, sieht man beim Öffnen als beigen Rand).
- **Verschluss** bündig in der Front: Federzunge im Deckel mit Haken, rastet in eine Nut der Basis. Öffnen: Griffnase nach vorn ziehen, Deckel heben.
- **Scharnier**: zwei Scharniere hinten, je 3 Knöchel und ein gedruckter Stift. Anschlag bei ca. 96°, der Deckel bleibt offen stehen.
- **Bandösen** links und rechts mit senkrechtem Loch Ø 5,2 für eine Kordel bis 4 mm (z. B. Paracord).

## Maße
Box geschlossen 240 × 103 × 122 mm (B × T × H), mit Ösen 264 mm breit, mit Scharnier 113 mm tief. Teilung auf 78 mm Höhe.
Fach 75 mm breit (Karte 70), vor dem Stapel 14 mm frei. Karte 70 × 112 × 4 mm aus `v4/out/10_karte_orange.stl`.

## Dateien
| Datei | Inhalt |
|---|---|
| `out/druck/01_basis_orange.stl` + `01f_modifier_basis_FUZZY.stl` | Basis, liegt **diagonal** (mit Ösen breiter als 256 mm), Unterseite auf der Platte |
| `out/druck/02_deckel_orange_kopfueber.stl` + `02f_modifier_deckel_FUZZY.stl` | Deckel **kopfüber**, Dach auf der Platte |
| `out/druck/03_inlay_beige.stl` | Inlay, aufrecht |
| `out/druck/04_stift_3x_beige.stl` | 3 Scharnierstifte (einer Reserve), liegen auf ihrer Abflachung |
| `out/druck/probedruck/K1…K3` | Probedrucke Scharnier, Verschluss, Passung (siehe unten) |
| `out/kartenbox_zusammenbau.3mf` | farbiger Zusammenbau mit 30 Karten (ElegooSlicer, Windows „3D-Viewer“) – **nicht drucken** |
| `out/kartenbox.glb` | farbiger Zusammenbau für jeden 3D-Viewer, auch am Handy |
| `out/viewer.html` | 3D-Ansicht mit Deckelregler und Schnitt (als Artefakt veröffentlicht) |
| `out/PRUEFBERICHT.md` | Ergebnis von `check.py` und `gegenpruefung.py` |
| `out/v_*.png` | Ansichten |

Skripte: `python3 export.py` (alle Dateien), `python3 check.py` (Prüfung), `python3 gegenpruefung.py` (Schichtprüfung der STL), `python3 render.py` (Bilder).

## Reihenfolge
1. **Probedrucke** (je 20–40 min, orange PETG wie später):
   - **K3 Passung** (rechtes Ende, Basis + Inlay + Deckel, mit Fuzzy-Modifiern): Inlay-Stück in das Basis-Stück stecken, Deckel-Stück darüber.
     Inlay geht leicht hinein, wackelt kaum? Deckel sitzt ohne Klemmen? Fuge gleichmäßig? Gefällt das Fuzzy? → `G_I` (0,3) bestätigen.
   - **K1 Scharnier**: Deckel-Stück zwischen die Basisknöchel, Stifte Ø 3,9 / 4,0 / 4,1 probieren.
     Ziel: Stift schiebt sich durch den äußeren Knöchel, dreht im Deckelknöchel frei und klemmt im inneren Knöchel fest. Anschlag bei ca. 96°?
     Danach `PIN_D` bzw. `HOLE_*` anpassen.
   - **K2 Verschluss**: Deckel-Stück senkrecht auf das Basis-Stück drücken: rastet es hörbar ein? Mit der Griffnase leicht zu öffnen?
     Hält es, wenn man ohne Nase zieht? → ggf. `HOLD_ANG` (60°) oder `REC_GAP` ändern.
2. Basis, Deckel (orange), Inlay und Stifte (beige).
3. Zusammenbau: Inlay einsetzen. Deckel schließen (rastet ein), dann je Scharnier einen Stift **von außen** einschieben, Kopf nach außen:
   durch den äußeren Knöchel, den Deckelknöchel und in den inneren Knöchel, wo er klemmt (mit dem Daumen oder einer Zange drücken, nicht hämmern).
4. Kordel durch eine Öse fädeln und verknoten (Handschlaufe wie im Vorbild) oder durch beide Ösen.

## Druckeinstellungen (ElegooSlicer, PETG, Düse 0,4) – Vorschlag, noch nicht gedruckt
| Einstellung | Basis / Deckel | Inlay | Stifte |
|---|---|---|---|
| Schichthöhe | 0,2 | 0,2 | 0,2 |
| Wandschleifen | **6** (Wand 2,5 mm massiv) | **4** (1,68 mm) | 4 (massiv) |
| Boden/Deckschichten | 5 / 5 | 4 / 5 | – |
| Füllung | 15 % Gyroid | 15 % Gyroid | 100 % |
| Stützen | aus | aus | aus |
| Brim | aus (Haftfläche 223 × 83 bzw. 219 × 79 mm) | aus | aus |
| Elefantenfuß-Kompensation | 0,15 | 0,15 | 0,1 |
| Fuzzy Skin | nur über den Modifier: beide Dateien zusammen hineinziehen („ein Objekt mit mehreren Teilen“), `01f`/`02f` → Typ Modifizierer, dort Fuzzy Skin **Kontur**; Objekt selbst ohne Fuzzy. Werte wie am Korpus: Punktabstand 0,30, Stärke 0,20, Klassisch, nicht auf der ersten Schicht | – | – |
| Naht | aufmalen an einer hinteren Ecke (Rundung), senkrecht | hinten | – |

Kühlung, Temperaturen und Mindest-Schichtdauer wie beim Korpus (`v4/out/README.md`, Abschnitt Korpus). Rolle vorher trocknen.
Fuzzy bleibt aus an: Fasen unten/oben, V-Fuge, Scharnieren, Verschluss mit Zunge und Mulde, Ösen (Passflächen).

Überhänge (aus `PRUEFBERICHT.md`): Basis nur die Haltefläche der Rastnut (≈ 11 mm², 1 mm breit, 30° zur Waagerechten), Deckel nur die
Haltefläche am Haken (≈ 13 mm²), Inlay die Brücken über den Hohlräumen hinter den Kartenstützen (Spannweite ≤ 13 mm).
Bohrungen sind Tropfen (Spitze 45°), Unterseiten der Rundungen und Ösen ≤ 42°.

## Material (geschätzt aus dem Volumen, Wände fast massiv)
Basis ca. 220–240 g, Deckel ca. 150 g, Inlay ca. 190 g, Stifte 1 g → zusammen gut 0,55 kg (0,37 kg orange, 0,19 kg beige).

## Sparhinweise
- Wand 2,5 → 2,1 mm (`T`, 5 statt 6 Wandschleifen) spart ca. 60 g; die Box wird dabei etwas weicher.
- Die Rückwand des Inlays sitzt hinter den Kartenstützen und ist bis auf den beigen Rand unsichtbar; mit Fenstern darin ließen sich ca. 20 g sparen (noch nicht im Modell).
- Kordel: jede runde Kordel bis 4 mm passt durch die Öse (Loch Ø 5,2); ein Reststück genügt.

## Offene Punkte / Grenzen
1. Nichts davon ist gedruckt. Spiele (`G_I`, Bohrungen, `REC_GAP`, `HOLD_ANG`) sind Startwerte → Probedrucke K1–K3.
2. Federkraft der Zunge (ca. 4 N) und Haltekraft (ca. 19 N) sind mit PETG E = 1800 MPa und Reibung 0,3 gerechnet (Annahmen).
3. **Leere Box mit offenem Deckel** kippt schon bei ca. 13° nach hinten (Deckel hängt hinter der Achse); mit Karten erst bei 28°. Geschlossen 39°.
4. Eine **senkrecht** ganz an die Stirnwand geschobene Karte im linken/rechten Fach berührt mit der Ecke die Deckelrundung; der Deckel schiebt sie beim Schließen zur Mitte.
   Der Normalzustand (Karten lehnen an der Stütze) ist in jeder Lage frei.
5. Keine Kennzeichnung der Fächer (z. B. Symbole wie am Deckel der Peppa Box) – bei Bedarf als vertiefte Symbole im Inlay-Rand ergänzen.
