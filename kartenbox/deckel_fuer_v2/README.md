# Neuer Deckel für die gedruckte Basis v2

Stand 15.11.2026. Für Jans bereits gedruckte **Basis v2** (Kartenbox v2 vom 13.11., Commit e8504ba). Die Basis bleibt unverändert;
neu gedruckt werden nur **Deckel, Rasteinsatz, Klemmlasche und Laschenstift**. Inlay und Scharnierstifte von v2 passen weiter.
Geometrie der Basis: `model_v2.py` (unveränderte Kopie, nur Pfad zur Karten-STL angepasst). Deckel: `deckel.py`.

## Was der neue Deckel kann
- **Stülpdeckel:** Er steht vorn und seitlich 2 mm über die Basis und reicht 10 mm über ihren Rand nach unten (bis 68 mm).
  Er liegt wie v2 auf der Oberkante der Basis auf. Hinten bleibt er bündig, dort sitzen die Scharnierknöchel der Basis; der Seitenrand
  läuft hinten schräg aus, damit er beim Öffnen frei schwenkt. Scharnier, Stifte und Öffnungsanschlag (ca. 96°) sind die von v2.
- **Verschluss, der wirklich hält:** An der v2-Basis gibt es nur die alte Rastnut (1 mm tief, 30° schräg) – daran rutscht jeder Haken
  unter Zug heraus. Deshalb:
  - **Rasteinsatz** (beige, 31 × 2,3 × 6 mm): wird von vorn in die vorhandene Mulde geschoben, sein Zahn greift in die alte Rastnut.
    Seine Unterkante ist eine **waagerechte** Haltefläche. Der Stülprand deckt ihn von vorn ab: Unter Zug kann er nicht aus der Nut.
    Zwei Tropfen Sekundenkleber halten ihn bei offenem Deckel an seinem Platz.
  - **Klemmlasche** (wie bei v3): hängt mit einem gedruckten Stift an zwei Lagerböcken am Deckel, auf der Seite gedruckt
    (Schichten entlang der Feder), vorgebogen (drückt geschlossen mit ca. 2 N an die Basis, klappert nicht). Ihr Haken greift
    1,2 mm unter den Einsatz; die Griffnase sitzt über der vorhandenen Fingermulde.
- **Bedienung:** Öffnen – Finger hinter die Griffnase, nach vorn ziehen (ca. 7 N), Deckel hochklappen. Schließen – zuklappen und vorn
  andrücken, der Haken schnappt unter den Einsatz (ca. 12 N). Kräfte gerechnet mit Annahmen (PETG E = 1800 MPa, Reibung 0,3).

## Dateien (`out/`)
| Datei | Inhalt |
|---|---|
| `druck/02n_deckel_orange_kopfueber.stl` + `02nf_modifier_deckel_FUZZY.stl` | Deckel kopfüber, Dach auf der Platte |
| `druck/05n_klemmlasche_beige_auf_der_seite.stl` | Lasche, auf der Seite (vorgebogen) |
| `druck/06_rasteinsatz_beige_auf_der_vorderseite.stl` | Rasteinsatz, liegt auf seiner Vorderseite (Zahn oben) |
| `druck/04n_laschenstifte_2_beige.stl` | 2 Laschenstifte Ø 4 (einer Reserve) |
| `druck/probedruck/N1…` | Lasche am echten Korpus testen: Deckel-Vorderstück, Laschen 1,4 / 1,6 / 1,8 mm, Einsatz, Stifte 3,9 / 4,0 / 4,1 |
| `druck/probedruck/N2…` | Ecke vorn rechts mit Stülprand (+ Fuzzy-Modifier): Passung an der echten Basis testen |
| `deckel_neu_zusammenbau.3mf`, `deckel_neu.glb`, `viewer.html` | Zusammenbau mit Basis v2, Inlay, 30 Karten (nicht drucken) |
| `PRUEFBERICHT.md` | Ergebnis von `check_deckel.py` und `gegenpruefung_deckel.py` |
| `n_*.png` | Ansichten |

Skripte: `python3 export_deckel.py`, `python3 check_deckel.py`, `python3 gegenpruefung_deckel.py`, `python3 render_deckel.py`.

## Reihenfolge
1. **Rasteinsatz** drucken (wenige Minuten) und probeweise von vorn in die Mulde der Basis schieben, Zahn voran in die alte Rastnut.
   Sitzt er ohne Klemmen? Noch nicht kleben.
2. **Probedruck N2** (Ecke mit Stülprand) auf die Basis setzen: gleitet er ohne Klemmen bis zur Auflage, wackelt kaum? → `SK_CLR` (0,35).
3. **Probedruck N1**: Lasche mit Stift ins Deckel-Vorderstück, Stück auf die Basis halten und andrücken: schnappt der Haken unter den Einsatz?
   Mit dem Finger leicht zu öffnen? Hält es, wenn man am Stück zieht? Welche Federdicke fühlt sich richtig an? → `CL_T` (1,6).
4. Deckel (orange), Lasche, Stifte (beige) drucken. Einsatz mit 2 Tropfen Sekundenkleber hinten in die Mulde kleben.
5. Alten Deckel abnehmen (Scharnierstifte herausdrücken), neuen Deckel mit denselben Stiften einhängen, Lasche mit Stift von rechts montieren.

## Druckeinstellungen (ElegooSlicer, PETG, Düse 0,4) – Vorschlag, noch nicht gedruckt
| | Deckel | Lasche | Einsatz | Stifte |
|---|---|---|---|---|
| Schicht | 0,2 | 0,2 | 0,2 | 0,2 |
| Wandschleifen | 4 (Stülprand 1,68 mm massiv) | 5 | 3 | 4 |
| Füllung | 15 % Gyroid | 100 % | 100 % | 100 % |
| Stützen / Brim | aus / aus | aus / **an, 5 mm** | aus / aus | aus / aus |
| Fuzzy Skin | nur über den Modifier (Kontur), Werte wie v2 | – | – | – |

Schichtprüfung der fertigen STL: Deckel frei nur 14 mm² (verteilt über die 45°-Schräge innen), Lasche 2 mm², Einsatz 0 mm².

## Grenzen / offen
1. Nichts davon ist gedruckt. Spiele (`SK_CLR`, `INS_CLR`, `HOLE_CLIP`, `CL_T`) sind Startwerte → Probedrucke N1/N2.
2. Der Haken greift nur 1,2 mm unter den Einsatz (die vorhandene Fingermulde lässt nicht mehr Platz). Er hält trotzdem formschlüssig, weil beide
   Flächen waagerecht sind; die Vorspannung hält die Lasche angelegt. Im Probedruck N1 prüfen, ob es satt einrastet.
3. Der Stülprand endet nur ca. 1 mm über den Bandösen.
4. Hinten ist der Deckel bündig (Stoß auf Stoß) – an der v2-Basis wegen der Scharnierknöchel nicht anders möglich.
5. Der Einsatz wird geklebt (Sekundenkleber). Halten muss der Kleber nur, solange der Deckel offen ist.
