# Peppa Box – Projekt-Steckbrief (Stand 25.10.2026)

Eigenbau einer Toniebox-Alternative für Kinder. Eine NFC-Karte mit aufgeklebtem Cover-Bild startet eine Spotify-Playlist.
Gehäuse: gedruckter Würfel 140 × 140 × 140 mm in Beige mit orangen Akzenten, Elegoo Centauri Carbon 2 mit CANVAS (4 Rollen), PETG.

Diese Datei fasst alle Entscheidungen bis hierher zusammen. Sie gehört in das Projektwissen und ist die Grundlage für jeden neuen Chat.

## Regeln für die Zusammenarbeit

- Nur in der EU bestellen, am liebsten bei Shops in Deutschland oder den Niederlanden.
- Von sich aus auf Sparmöglichkeiten hinweisen.
- Möglichst wenig löten (erste Lötarbeiten).
- Keine Gewindeeinsätze. Schrauben gehen direkt in den Kunststoff, Dome 9 mm, damit Einsätze später möglich bleiben.
- Listen mit anklickbaren Links.
- Vor jedem Kauf prüfen, ob das Teil exakt passt.
- Kein Maß einfach annehmen. Ist etwas nicht belegt, das sagen oder nachfragen.
- Slicer ist ElegooSlicer (nicht SatelLite, das ist für Harz).

## Aktueller Stand

| Bereich | Stand |
| --- | --- |
| Bestellungen | BerryBase, Amazon (RC522, MAX98357A) geliefert. Reichelt: mehrere Artikel nicht lieferbar, wird gerade geklärt |
| Pi | Raspberry Pi OS Lite 64-bit (Debian 13 Trixie, 06.10.2026) auf SanDisk Ultra 128 GB A1; Ton über die Pi-Klinke getestet, gut |
| Stapel | Akku-Board + Pi + Klemmen-Aufsatz verschraubt, auf dem gedruckten Boden (Version mit DAC-Stiften) montiert, passt |
| Druck | Boden (erste Version) gedruckt; Korpus-Prototyp läuft (0,28 mm Extra Draft, 2 Wandschleifen, 10 % Gyroid, ohne Fuzzy Skin) |
| Verstärker | Stiftleiste und Lautsprecherklemme werden gerade gelötet |

## Hardware (endgültig)

- Raspberry Pi 3A+
- Waveshare UPS HAT (D) mit 2 × BAK N21700CG50; Acrylplatte 85 × 55 mm, Messingbolzen, Lochbild 58 × 49 mm
- BerryBase GPIO-Breakout-HAT mit Federklemmen (Reihen 1–8, A–H, I–P); gelbe Stifte gehen durch
- MAX98357A-Klon (Lautsprecher, I2S an Pin 12, 35, 40; SD/stumm an Pin 36)
- Visaton FRS 8, 4 Ω, in eigener geschlossener Kammer vorne
- Kopfhörer: **direkt aus der Klinke des Pi** (DAC entfällt, 25.10.). Kabel Goobay 67782 (ein Stecker 90°) halbiert zur Lumberg 1503-09 in der rechten Wand. Steckererkennung: Öffner L an Pin 37. Beim Ein-/Ausstecken stellt das Programm den Spotify-Ausgang um (3–5 s Pause), Lautsprecher stumm, Lautstärke begrenzt
- RC522 (SPI), MPR121 (I2C 0x5A, 4 Kupfer-Touchfelder im Deckel), STEC11B03 Drehgeber, DTS-24R hinter gedruckter Ein-Taste (an SCL zum Wecken)
- WAGO: auf dem Boden 5 V (3-fach) und GND A (5-fach); unter dem Deckel 3,3 V, SCL (je 3-fach) und GND B (5-fach)
- Elko 1000 µF / 10 V an 5 V / GND A

`config.txt`: `dtparam=spi=on`, `dtparam=i2c_arm=on`, `dtparam=audio=on`, `dtoverlay=hifiberry-dac` (I2S für den MAX98357A).

## Gehäuse (Modell v4, parametrisch in `v4/model.py`)

- **Korpus** unten offen, Lautsprecherkammer mit eigenem Boden (2,4 mm), Kammerdecke als Brücke ca. 40 mm. Deckelauflage ringsum geschlossen.
- **Boden = Elektronikträger**, 4 mm, außen 0,4 mm kleiner (Schattenfuge), Zentrierkragen hinten. Wird von unten eingesetzt, 6 Senkschrauben 3,0 × 14 in Dome (4 Ecken, 2 an der Kammerwand). Einbau inkl. Hubweg geprüft.
- **Stapel auf dem Boden:** Überhang mit BOOT-Taste links, gelbe Stifte vorne, Anschlusskante (USB-C, Schalter, Pi-Klinke) hinten. 4 Auflagen mit Mulde; Befestigung später mit M2,5-Schrauben von unten (alte Länge + ca. 5 mm, Linsen-/Flachkopf). **Offen:** Länge der vorhandenen Schrauben.
- **Hinten auf dem Boden:** Mulden für WAGO GND A, WAGO 5 V, Verstärker. Rechter Teil frei (Kabelreserve, Elko).
- **Deckel:** zweifarbig (oranger Kern, beige Haut 0,7 mm), 4 Touchfelder mit Symbolen, Kartenschlitz, Ein-Taste hinten rechts in Mulde. **Deckelrahmen** mit Verteiler-Brücke (MPR121 + 3 WAGO hängend), Tasterhalter, Zungen vorne, 2 Schrauben hinten durch die Rückwand.
- **Kartenfach:** Karte 70 × 112 × 4 mm, 42 mm tief, 8° geneigt, Federzunge, RC522 in Schienen dahinter.
- **Rechts:** Drehknopf (y 84, z 60) und Klinke (y 84, z 24). **Links:** Riemen (z 118). **Hinten:** USB-C-Einbaubuchse x 114, z 60, innen höchstens 20 mm tief (Produkt offen; Stecker am Akku-Board gewinkelt oder ≤ 20 mm), Lüftungsschlitze.
- **Front:** gedrucktes Gitter statt Stoff, orange, mit „Peppa Box“-Logo (Variante A empfohlen, siehe `gitter_logo_varianten.png`). **Noch nicht im Modell.**
- Höhen: Klemmen 77,5 mm, Kartenfach ab 86,8 mm, Deckel-Module ab 117,4 mm.

Druck (endgültig): Düse 0,4, 0,2 mm, 3 Wandschleifen, 15 % Gyroid, Fuzzy Skin nur Kontur (0,2–0,25 / 0,6–0,7 mm) mit Modifier `01m_…`, keine Stützen.

## Software (Plan, Kapitel 9 im Konzept-Dokument)

- Raspotify/librespot als Spotify-Lautsprecher (Premium nötig), eigenes Python-Programm für Karte, Tasten, Drehgeber, Kopfhörer-Umschaltung, Spotify Web API zum Starten der Playlist.
- Lautstärke lokal regeln, Spotify fest auf 100 %.
- Schreibschutz (Overlay) mit eigener kleiner Datenpartition, Wartungsmodus für Updates; ganz zum Schluss einrichten.
- Watchdog, automatischer Neustart der Dienste; Ziel unter 20 s bis zum Startton.
- Offen: Karten anlernen (E9: Link per Handy auf die Karte oder Zuordnungsliste), Einstellungsseite/App für Eltern.

## Offene Punkte

1. Reichelt-Bestellung klären; DAC und Cinch-Kabel stornieren, ebenso die 32-GB-SD-Karte.
2. Bestellen (gesammelt): Klinkenkabel Goobay 67782, Kunststoffschrauben 3,0 mm (Sortiment), 4 × M2,5 (Länge folgt), USB-C-Verlängerung (Produkt offen), Montageband.
3. Länge der M2,5-Schrauben unter der Acrylplatte messen → Auflagenhöhe anpassen.
4. Nach Lieferung von Reichelt messen: Lautsprecher-Lochabstand, Gewindelängen Drehgeber und Klinke, Tasterhöhe; RC522- und MAX-Maße; NFC-Aufkleber-Dicke.
5. Coupons drucken und auswerten: C2, C4, C6, C7, C8.
6. Korpus-Prototyp: Boden einsetzen, Schrauben, Kammerdecke ansehen. Ist die Decke schlecht → Kammerdecke als eigenes Teil.
7. Gitter mit Logo ins Modell aufnehmen (+ Coupon).
8. Optional: Lichtleiter für die Lade-LED, Ideen zur optischen Individualisierung (Seitenteile, Deckeleinlage, Magnete).

## Links (Artefakte, bleiben dauerhaft erhalten)

- Konzeptprüfung (Dokument mit Kapitel 1–13): https://claude.ai/artifact/6e3WZJZKozFgtdKq3825og
- Einkaufsliste: https://claude.ai/artifact/YbnQM68dkUknMvpfWoy1yh
- Verdrahtungsplan: https://claude.ai/artifact/SBLr57seH7cgAwgjYAD57C

## Quellcode (Datei `peppabox_quellcode.zip`)

In einem neuen Chat die Zip anhängen und sagen: „Entpacke nach /home/claude/musikbox“. Dann laufen die Skripte wie bisher.

| Datei | Zweck |
| --- | --- |
| `v4/model.py` | parametrisches Modell, alle Maße oben mit Status (belegt / gemessen / festgelegt / vorläufig / Probedruck) |
| `v4/check.py` | Kollisionen, Einbau (Deckel von oben, Boden von unten mit Hubweg), Überhänge |
| `v4/build_all.py` | STL-Export in Druckausrichtung, Ansichten (braucht `v3/concept3.py`) |
| `v4/coupons.py` | Probedruck-Coupons C1–C8 |
| `v4/docs.py` | README, PARAMETER, PRÜFBERICHT, Druckpaket-Zip |
| `v4/boden_plan.py` | Draufsicht und Höhen des Bodens |
| `v4/modifier.py` | Modifier-Körper „ohne Fuzzy Skin“ |
| `v4/gitter/` | Logo-Vektorisierung und Gitter-Varianten |
| `plan/gen_plan4.py` | erzeugt `verdrahtungsplan.html` |
| `plan/einkaufsliste.html` | Einkaufsliste (Daten stehen im Skriptteil) |
| `v4/out/` | aktuelle STL-Dateien, Bilder, PARAMETER.md, PRUEFBERICHT.md |

Python-Pakete: manifold3d, trimesh, numpy, pillow, matplotlib, opencv-python.

## Nachtrag 25.10.2026 – Prototyp-Korpus ausgewertet, Fuge Boden/Korpus

- Prototyp (0,28 mm, 2 Wände, 10 %) gedruckt: Maße und Einbau des Bodens mit Stapel passen. Sichtbar: Schichtlinien, Naht hinten, raue 45°-Schrägen oben an Rahmen-Vertiefung und Lautsprecher-Mulde, „X“-Kratzspur auf der Kammerdecke (fehlender Z-Hop), Reste der Umrandung an der Unterkante.
- Entscheidung: Boden bleibt unter dem Korpus (kein eingelassener Boden).
- Boden jetzt **exakt bündig** mit dem Korpus (vorher 0,4 mm kleiner). Fuge außen als **V-Fuge**: je 0,8 mm Fase an Korpus-Unterkante und Boden-Oberkante; Standkante des Bodens 0,8 mm gefast. Zentrierkragen mit 0,2 mm Spiel (vorher 0,3), per Coupon C8 prüfen. Eckdome dafür 0,4 mm nach innen gerückt.
- Für den endgültigen Druck: keine Umrandung am Korpus, Elefantenfuß-Kompensation ca. 0,15 mm, Z-Hop 0,4 mm, Scarf Seam.
- Skripte nutzen jetzt relative Pfade; das Repository läuft an beliebigem Ort.

## Nachtrag 25.10.2026 – RC522 gemessen, Stiftleiste gewinkelt

- RC522 gemessen: 60 × 40 mm, Antennenmitte 20 mm vom Antennenende (40 mm bis zum Lötlochende), Quarz 5 mm hoch (Modell vorher 3 mm). Prüfung ok, Abstand zum Deckelrahmen 2,0 mm.
- Stiftleiste **gewinkelt (90°)**, Kunststoffleiste auf der Bauteilseite, Stifte flach in Platinenebene zur rechten Seitenwand, Überstand 6 mm. Neue Zone „RC522-Stecker“ im Modell (Stiftleiste + Steckkabel-Buchsen + Kabelbogen).
- Platz von der Platinenkante bis zur Innenwand: ca. 27 mm. Gesteckte Kabel enden 14 mm hinter der Platinenkante (gemessen), es bleiben ca. 13 mm für den Kabelbogen. Prüfung ok.
- MAX98357A: SD an Pin 36 (GPIO 16) hat beim Start den internen Pull-down des Pi → Verstärker stumm. Programm muss GPIO 16 als Eingang **ohne** Pull setzen (`pinctrl set 16 ip pn`). Noch nicht im Verdrahtungsplan.
- Klemmen-Aufsatz (BerryBase) hat GPIO 25 nicht auf einer Klemme. Entscheidung: **RC522 RST an 3,3 V** (Klemme I), Reset per Software (Soft-Reset). GPIO 25 / Pin 22 wird frei. Belegung RC522 am Aufsatz: SDA→E (CE0), SCK→D (SCLK), MOSI→B, MISO→C, GND→G, RST→I (3,3 V), 3.3V→A, IRQ frei. Verdrahtungsplan noch nachziehen.
- **Korrektur `config.txt`:** Auf dem Pi waren `dtparam=spi=on` und `dtparam=i2c_arm=on` noch auskommentiert, `dtoverlay=hifiberry-dac` fehlt. SPI und I2C am 25.10. eingeschaltet. hifiberry-dac wird ergänzt, wenn der Lautsprecher getestet wird.
- Pi holt das Repository jetzt selbst: Klon unter `~/peppa-box`, Lesezugang per Deploy Key (nur lesen). Aktualisieren mit `cd ~/peppa-box && git pull`. Testprogramm RC522: `software/rc522_test.py`.
