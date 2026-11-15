# Kartenbox v3 – 30 Peppa-Karten fürs Kinderzimmer

Stand 15.11.2026. Ersetzt v2 vom 13.11. (in der Git-Historie, Commit e8504ba) und den ersten Entwurf (`v1_entwurf/`).
Parametrisches Modell `model.py` (manifold3d), jede Größe mit Status in `P_` (belegt / festgelegt / berechnet / Probedruck).

## Was sich gegenüber v2 geändert hat (Rückmeldung nach dem Druck von v2)
1. **Deckel stülpt sich über die Basis.** v2 hatte Basis und Deckel bündig Stoß auf Stoß (V-Fuge auf 78 mm). Jetzt hat die Basis oben einen
   12 mm hohen **Hals**; der Deckel stülpt sich darüber und liegt auf einer Stufe auf (Fuge auf 66 mm). Außen bleiben Deckel und Basis bündig.
   Der Hals verjüngt sich nach oben um 0,8 mm, damit der Deckelrand beim Aufschwenken vorn nicht am Hals streift; die Scharnierachse liegt
   deshalb auf Höhe der Fuge (vorher 78 mm).
2. **Neuer Verschluss: Klemmlasche.** Die v2-Zunge war Teil der Deckelwand und wurde kopfüber gedruckt – die Schichten lagen quer zur Biegung,
   darum ist sie beim Nachbiegen gebrochen. Und ihre Haltefläche (30° zur Waagerechten) ließ den Haken unter Zug herausrutschen.
   Jetzt: eine **eigene beige Lasche**, an zwei Lagerböcken am Deckel mit einem gedruckten Stift befestigt. Sie wird **auf der Seite liegend**
   gedruckt, die Schichten laufen entlang der Feder. Ihr Haken greift **2,4 mm** tief unter eine **waagerechte** Haltefläche in der Basis:
   Zug am Deckel kann den Haken nicht herausdrücken. Damit der tiefe Haken beim Zuklappen am Hals vorbeikommt, hat der Hals vorn eine
   flache Rinne (vom Deckel verdeckt). Die Lasche wird **leicht nach innen vorgebogen** gedruckt: eingebaut drückt sie unten mit ca. 2 N
   gegen die Basis – sie klappert nicht und kann beim Tragen nicht von selbst aufgehen. Im Laschenkopf sitzt der Stift mit wenig Spiel
   (Bohrung 4,3), der Kopf liegt flach am Deckel an. Auch im ungünstigen Fall (Spiel, gerundete Druckkanten) bleiben ca. 1,9 mm Eingriff.
   Die Lasche ist ein kleines Ersatzteil (5 g), falls doch einmal etwas bricht.

## Bedienung
- **Öffnen:** einen Finger hinter die Griffnase legen (sie steht unten 8 mm vor, unten gerundet), ca. 2,5 mm nach vorn ziehen (ca. 7 N),
  Deckel hochklappen. Er bleibt bei ca. 95° offen stehen.
- **Schließen:** Deckel zuklappen und vorn kurz andrücken – der Haken gleitet mit seiner 30°-Schräge über die Kante der Stufe und schnappt ein (ca. 10 N).
- Die Lasche liegt flach am Deckel an; nach innen kann sie nicht umklappen.

## Maße
Box geschlossen 244 × 107 × 122 mm (B × T × H), mit Ösen 268 mm breit, mit Scharnier und Lasche 126 mm tief.
Fuge 66 mm, Hals bis 78 mm. Fach 75 mm breit (Karte 70), vor dem Stapel 14 mm frei. Karte 70 × 112 × 4 mm aus `v4/out/10_karte_orange.stl`.
Innenraum, Inlay und Kartenlage sind gegenüber v2 unverändert; die Außenhaut ist je Seite 2 mm größer (Hals + Deckelrand).

## Dateien
| Datei | Inhalt |
|---|---|
| `out/druck/01_basis_orange.stl` + `01f_modifier_basis_FUZZY.stl` | Basis, liegt **diagonal** (mit Ösen breiter als 256 mm), Unterseite auf der Platte |
| `out/druck/02_deckel_orange_kopfueber.stl` + `02f_modifier_deckel_FUZZY.stl` | Deckel **kopfüber**, Dach auf der Platte |
| `out/druck/03_inlay_beige.stl` | Inlay, aufrecht |
| `out/druck/04_stifte_beige_3_scharnier_2_lasche.stl` | 3 Scharnierstifte + 2 Laschenstifte (je einer Reserve), liegen auf ihrer Abflachung |
| `out/druck/05_klemmlasche_beige_auf_der_seite.stl` | Klemmlasche, **auf der Seite** (Profil auf der Platte, 22 mm hoch) |
| `out/druck/probedruck/K1…K3` | Probedrucke Scharnier, Lasche, Stülpdeckel (siehe unten) |
| `out/kartenbox_zusammenbau.3mf` | farbiger Zusammenbau mit 30 Karten (ElegooSlicer, Windows „3D-Viewer“) – **nicht drucken** |
| `out/kartenbox.glb` | farbiger Zusammenbau für jeden 3D-Viewer, auch am Handy |
| `out/viewer.html` | 3D-Ansicht mit Deckelregler und Schnitt (als Artefakt veröffentlicht) |
| `out/PRUEFBERICHT.md` | Ergebnis von `check.py` und `gegenpruefung.py` |
| `out/v_*.png` | Ansichten, u. a. `v_halb_offen.png` (Hals sichtbar), `v_schnitt_verschluss.png` (Haken in der Nut) |

Skripte: `python3 export.py` (alle Dateien), `python3 check.py` (Prüfung), `python3 gegenpruefung.py` (Schichtprüfung der STL), `python3 render.py` (Bilder).

## Reihenfolge
1. **Probedrucke** (orange bzw. beige PETG wie später):
   - **K2 Klemmlasche** (zuerst, ca. 1 h zusammen): `K2a` Basis-Vorderstück (Stufe, Hals, Nut), `K2b` Deckel-Vorderstück mit Lagerböcken (kopfüber),
     `K2c` drei Laschen mit Federdicke 1,6 / 1,8 / 2,0 mm (auf der Seite, vorgebogen), `K2d` Laschenstifte Ø 3,9 / 4,0 / 4,1.
     Lasche mit Stift einbauen (Stift **von rechts**, Kopf rechts; klemmt im linken Bock), Deckelstück auf das Basisstück drücken:
     rastet es hörbar ein? Geht es mit der Griffnase leicht auf? Hält es, wenn man am Deckelstück zieht, ohne die Lasche zu betätigen?
     Kann ein Kind sie mit einem Finger öffnen? Liegt die Lasche geschlossen spürbar an (kein Klappern)? Welche Federdicke fühlt sich richtig an?
     → `CL_T` (1,8), `PRE_N` (2 N), `HOLE_CLIP` (4,3) bzw. `PIN_D`/`HOLE_*` anpassen.
   - **K3 Stülpdeckel** (rechtes Ende, Basis + Inlay + Deckel, mit Fuzzy-Modifiern): Deckelstück über den Hals stülpen.
     Gleitet es ohne Klemmen bis auf die Stufe? Wackelt es kaum? Fuge gleichmäßig? Inlay geht leicht hinein? → `SK_CLR` (0,35), `G_I` (0,3).
   - **K1 Scharnier**: Deckelstück zwischen die Basisknöchel, Stifte Ø 3,9 / 4,0 / 4,1 probieren; Anschlag bei ca. 95°?
2. Basis, Deckel (orange), Inlay, Lasche und Stifte (beige).
3. Zusammenbau: Inlay einsetzen. Lasche zwischen die Lagerböcke am Deckel, Laschenstift von rechts durchschieben, bis der Kopf in der Senkung sitzt.
   Deckel schließen (rastet ein), dann je Scharnier einen Stift **von außen** einschieben, Kopf nach außen
   (mit dem Daumen oder einer Zange drücken, nicht hämmern).
4. Kordel durch eine Öse fädeln und verknoten (Handschlaufe) oder durch beide Ösen.

## Druckeinstellungen (ElegooSlicer, PETG, Düse 0,4) – Vorschlag, noch nicht gedruckt
| Einstellung | Basis / Deckel | Inlay | Lasche | Stifte |
|---|---|---|---|---|
| Schichthöhe | 0,2 | 0,2 | 0,2 | 0,2 |
| Wandschleifen | **4** (Deckelrand 1,68 und Hals massiv; Basis unter der Fuge 4,5 mm = 2 × 4 Linien + Füllung) | **4** (1,68 mm) | **5** (Feder massiv) | 4 (massiv) |
| Boden/Deckschichten | 5 / 5 | 4 / 5 | 3 / 3 | – |
| Füllung | 15 % Gyroid | 15 % Gyroid | 100 % | 100 % |
| Stützen | aus | aus | aus | aus |
| Brim | aus (Haftfläche 228 × 89 bzw. 224 × 84 mm) | aus | **an, 5 mm** (22 mm hoch auf schmalem Profil) | aus |
| Elefantenfuß-Kompensation | 0,15 | 0,15 | 0,1 | 0,1 |
| Fuzzy Skin | nur über den Modifier: beide Dateien zusammen hineinziehen („ein Objekt mit mehreren Teilen“), `01f`/`02f` → Typ Modifizierer, dort Fuzzy Skin **Kontur**; Objekt selbst ohne Fuzzy. Werte wie am Korpus: Punktabstand 0,30, Stärke 0,20, Klassisch, nicht auf der ersten Schicht | – | – | – |
| Naht | aufmalen an einer hinteren Ecke (Rundung), senkrecht | hinten | egal | – |
| Brücken | Standard (Rastnut-Decke ist eine 23 mm breite Brücke) | Standard | – | – |

Kühlung, Temperaturen und Mindest-Schichtdauer wie beim Korpus (`v4/out/README.md`, Abschnitt Korpus). Rolle vorher trocknen.
Fuzzy bleibt aus an: Fasen unten/oben, Fuge, Hals (verdeckt, mit Rinne für den Haken), Scharnieren, Lasche mit Lagerböcken und Nut, Ösen.

Überhänge (aus `PRUEFBERICHT.md`, Schichtprüfung der fertigen STL): Basis nur die Decke der Rastnut (59 mm², Brücke über 23 mm),
Deckel keine, Lasche keine (auf der Seite), Inlay die Brücken über den Hohlräumen hinter den Kartenstützen (≤ 14 mm Spannweite).
Bohrungen sind Tropfen (Spitze 45°).

## Material (geschätzt aus dem Volumen)
Massiv gerechnet: Basis 349 g, Deckel 179 g, Inlay 199 g, Lasche 5 g, Stifte 2 g. Gedruckt mit 4 Wandschleifen und 15 % Füllung
etwa 0,65 kg (ca. 0,47 kg orange, 0,2 kg beige). Gegenüber v2 ca. 0,1 kg mehr, fast alles in der dickeren Basiswand unter der Fuge.

## Sparhinweise
- Basis mit **3 statt 4 Wandschleifen**: unter der Fuge bleibt mehr Füllung statt Vollmaterial, spart ca. 30–40 g; Hals und Deckelrand werden
  dabei nicht dünner (eigene Wandstärke). Für Kinderhände bleibt die Basis stabil, die Stufe muss nur den Deckel tragen.
- Die Rückwand des Inlays sitzt hinter den Kartenstützen und ist bis auf den beigen Rand unsichtbar; mit Fenstern darin ließen sich ca. 20 g sparen (noch nicht im Modell).
- Erst die Probedrucke K2 und K3 (zusammen unter 50 g) – dann kein Fehldruck der großen Teile.
- Kordel: jede runde Kordel bis 4 mm passt durch die Öse (Loch Ø 5,2); ein Reststück genügt.

## Offene Punkte / Grenzen
1. Nichts davon ist gedruckt. Spiele (`SK_CLR`, `G_I`, Bohrungen, `CL_T`) sind Startwerte → Probedrucke K1–K3.
2. Kräfte der Lasche (ca. 7 N zum Öffnen, ca. 10 N zum Schließen, 2 N Vorspannung) und Tragkraft (Hakenwurzel ca. 500 N, Stift ca. 250 N) sind mit Annahmen gerechnet
   (PETG E = 1800 MPa, Scherfestigkeit 10–15 MPa, Reibung 0,3).
3. **Leere Box mit offenem Deckel** kippt schon bei ca. 15° nach hinten (Deckel hängt hinter der Achse); mit Karten erst bei 29°. Geschlossen 41°.
4. Die Lasche steht vorn ca. 9 mm vor (Lagerböcke). Falls sie beim Tragen stört: kürzere Lagerböcke gehen nur mit dünnerem Stift (Ø 3, dann Stahlstift kaufen).
5. Keine Kennzeichnung der Fächer – bei Bedarf als vertiefte Symbole im Inlay-Rand ergänzen.
