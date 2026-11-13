# Kartenbox (30 Peppa-Karten, Kinderzimmer)

Stand 11.11.2026. Parametrisches Modell in CadQuery (`model.py`), alle Maße mit Status (belegt / festgelegt / berechnet / Probedruck) in `P`.

## Dateien
| Datei | Inhalt |
|---|---|
| `out/druck/01_basis_orange.stl` | Basis mit Scharnierknöcheln und zwei Bandösen, steht auf dem Boden |
| `out/druck/02_deckel_orange_kopfueber.stl` | Deckel, **Dach auf der Platte** (kopfüber) |
| `out/druck/03_inlay_beige.stl` | Inlay mit 3 Fächern |
| `out/druck/01f_…`, `02f_modifier_…_FUZZY.stl` | Fuzzy-Streifen (Modifier), erster Entwurf, erst am Coupon prüfen |
| `out/druck/probedruck/K1*`, `K2*` | Scharnier (3 Bohrungsvarianten) und Rastung (3 Vorspannungen) |
| `out/kartenbox_zusammenbau.step`, `kartenbox_*.step`, `kartenbox.glb` | 3D-CAD-Dateien (Ansicht, Farben im Zusammenbau-STEP) |
| `out/00_zusammenbau_NICHT_DRUCKEN.stl`, `04_stahlstift_…` | nur Ansicht |
| `out/PRUEFBERICHT.md` | Ergebnis von `check.py` |

Skripte: `python3 build.py` (Netze), `python3 check.py` (Prüfung), `python3 export.py` (alle Dateien), `render.py`, `sect.py`, `mkviewer.py` (3D-Seite).

## Maße (Außen)
Basis 158 × 84 × 103 mm (mit Ösen 186 breit), Deckel 162 × 99 × 43 mm, Inlay 152 × 78 × 50 mm. Alle Teile passen in 256³ (Elegoo Centauri Carbon 2).
Fach 48 mm innen für 10 Karten à 4 mm (8 mm Luft), Karten (70 × 112 × 4 mm, Eckenradius 5 mm) stehen 14 mm über der Deckelfuge (Griff).

## Druckeinstellung (Vorschlag, noch nicht gedruckt)
PETG, 0,4er Düse, 0,2 mm, 6 Wände Basis (2,52 mm), Deckel 4 Wände, Basis stehend, Deckel kopfüber, Inlay stehend (beige, CANVAS oder getrennter Druck). Fuzzy: wie `v4/out/README.md` (Fuzzy 0,20/0,30 Classic, Modifier „Kontur“, Prozess „Nur lackiert“ nicht nötig, wenn Fuzzy gewollt ist). Brim für Basis und Inlay. Kein Stützmaterial vorgesehen; Restüberhänge im Prüfbericht (Scharnierunterseite der Basis, Dachkante des Deckels, Zungenlasche).

## Einkauf
- Stahlstift Ø 3 × 90 mm (Zylinderstift oder Rundstab, 3 mm): **Produkt nicht geprüft, kein Link**. Günstiger: 3-mm-Rundstab vom Meter und selbst kürzen. Maß vorher am Händler gegen die Bohrung prüfen.
- Band/Kordel für die Ösen (Loch 6,5 mm, Ösenbreite 14 mm): Material noch offen, Breite des Bandes bitte nennen.

## Sparhinweise
- `LINER_H` niedriger = weniger beiges Filament (jede 10 mm weniger sparen ca. 10 g).
- Ösen nur auf einer Seite = weniger Druckzeit; Band an einem Ende, andere Seite Schlaufe.

## Offene Punkte
1. **Kein harter Öffnungsstopp**: Der Deckel bleibt durch Reibung der Bohrung offen (Coupon K1), ein Stopp wäre ein Zusatzteil.
2. **Probedrucke vor dem Hauptdruck**: Scharnierspiel (K1), Rastkraft (K2), Spiel Inlay/Deckel (Wert 0,3/0,4 mm ist Annahme).
3. Verschlusskraft (ca. 5–10 N) und Federdehnung sind gerechnet mit PETG E = 1800 MPa (Annahme), nicht gemessen.
4. Grenzfall Kartenneigung: Karten dürfen höchstens 3,7° lehnen, sonst streift der Deckel beim Öffnen (0,05 mm Eindringtiefe im Extremfall).
5. Fuzzy-Modifier und Ösen-Aussparung sind ein erster Entwurf.
