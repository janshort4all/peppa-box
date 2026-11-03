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
- Vor jeder Anschlussanleitung die Produktseite bzw. das Datenblatt des Bauteils prüfen (Jumper, Lötbrücken, Spannung, Pinbelegung) und die Quelle nennen. Nicht geprüfte Aussagen ausdrücklich als Vermutung kennzeichnen.
- Bei der Fehlersuche zuerst den Aufbau der beteiligten Platinen prüfen, dann Kabel und Lötstellen.
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
- RC522 (SPI), MPR121 (I2C 0x5A, 4 Kupfer-Touchfelder im Deckel), STEC11B03 Drehgeber, Kurzhubtaster 12 × 12 × 7,3 (BerryBase KHT1212PV73) hinter gedruckter Ein-Taste (an SCL zum Wecken)
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
- **Klemmen-Aufsatz verstanden:** Je Zeile zwei gelbe Stifte. Die Reihe zur Pi-Seite ist mit dem Pi verbunden, die andere mit der Federklemme. Verbindung erst durch einen **Jumper** (24 Stück im Lieferumfang). Ohne Jumper sind die Klemmen tot – das war die Ursache der Fehlersuche am 25.10. Für RC522 Jumper in A, B, C, D, E, G.
- Pi am 25.10. neu aufgesetzt (SD-Karte nach Absturz beim Umstecken unter Spannung und hartem Ausschalten defekt). Regel: Kabel nur bei ausgeschaltetem Pi umstecken, vorher `sudo poweroff`.
- RC522-Test am 25.10. erfolgreich über die Federklemmen (Jumper A, B, C, D, E, G, I; RST an Klemme I = 3,3 V).
- Offen: Verdrahtungsplan um Jumper-Belegung des Aufsatzes ergänzen; übrige Module (MAX98357A, MPR121, UPS HAT D) gegen Produktseiten/Datenblätter prüfen.
- RC522-Diagnose 25.10.: SPI ok (Version 0x92 stabil), Antenne an (TxControl 0x83), Befehle werden gesendet. Ohne RxNoErr meldete der Empfänger nach jeder Abfrage Störempfang (0 Byte); mit RxNoErr sauberes Timeout. Karten aus dem Set werden nicht erkannt. Programm entspricht der Init-/Befehlsfolge der gängigen Bibliotheken. Verdacht: Hardware (bekanntes Problem billiger RC522: verstimmte Antenne / schwache Spulen L1, L2). Nächste Schritte: Karte mit Handy-NFC prüfen, zweites RC522-Modul testen.
- Gegenprobe mit unveränderter Bibliothek pimylifeup/MFRC522-python (`software/rc522_ref_test.py`): ebenfalls keine Karte. Karte per Handy-NFC geprüft: MIFARE Classic 1K, UID 19:81:15:20, in Ordnung. **Ergebnis: RC522-Modul defekt (Empfangsteil).** Offen: Modul reklamieren, Ersatz bestellen (3er-Pack, 60 × 40 mm, gewinkelte Stiftleiste wieder selbst einlöten).
- Zweites RC522-Modul eingebaut: liest Karten (`software/rc522_test.py`, z. B. UID 7B:6E:CD:55). Noch prüfen: Lesen durch ca. 5 mm Kunststoff/Pappe, stabile Erkennung bei ruhig liegender Karte.
- **Korrektur RC522:** Mit sicher steckenden Kabeln liest das zweite Modul fehlerfrei (z. B. 47:82:C6:2E bei ruhiger Karte jede Abfrage). Die Aussetzer kamen von einem Draht, der halb aus einer Federklemme gerutscht war. Das erste Modul ist daher vermutlich **nicht** defekt; vor einer Reklamation mit sicherer Verkabelung erneut testen (`--stat`). Regel: Drähte verzinnen, bis Anschlag einstecken, Zugtest; beim Einbau Zugentlastung.
- **RC522 abgeschlossen:** Karte 19:81:15:20 (per Handy-NFC geprüft) bei 3 cm Abstand durch 2–3 mm Plexiglas bei jeder Abfrage fehlerfrei gelesen. Reichweite für das Kartenfach ausreichend.

## Nachtrag 25.10.2026 – Spotify-Grundfunktion (Test)

- Recherche: Raspotify 0.48.4 (22.10.2026) unterstützt Debian 13 Trixie/arm64; Anmeldung nur noch über Zeroconf (Spotify-App im selben WLAN) oder OAuth, kein Passwort. Spotify-Entwickler-App: Inhaber braucht seit Feb. 2026 Premium; Redirect-URI `http://127.0.0.1:8888/callback` (localhost verboten); Entwicklungsmodus max. 5 Testnutzer.
- Raspotify-Einstellungen: `LIBRESPOT_NAME="Peppa Box"`, Zugangsdaten-Cache **an** (Zeile `LIBRESPOT_DISABLE_CREDENTIAL_CACHE=` auskommentieren), damit die Box nach Neustart ohne App in der Geräteliste der Web API erscheint. Ausgabe vorerst Pi-Klinke.
- Neue Programme in `software/`: `rc522.py` (Lesemodul), `spotify.py` (PKCE-Anmeldung, Web API, nur Standardbibliothek), `spotify_login.py`, `karte_zuordnen.py`, `peppa_player.py` (Karte auf = spielen, weg = Pause, gleiche Karte = weiter).
- Zugangsdaten und Kartenliste liegen nur auf dem Pi unter `~/.config/peppa-box/` (config.json, spotify_token.json, karten.json), nicht im Repository.
- Raspotify eingerichtet und geprüft: Gerät „Peppa Box“, Ausgabe `LIBRESPOT_DEVICE="plughw:CARD=Headphones,DEV=0"` (Pi-Klinke, Karte per Name statt Nummer). Zugangsdaten-Cache aktiv (`/var/lib/raspotify/credentials.json`), Box erscheint nach Neustart von Raspotify ohne App in der Web-API-Geräteliste. Spotify-Anmeldung (PKCE) erfolgreich. Hinweis: `/etc/raspotify/conf` nur mit sudo lesbar.
- **Meilenstein 25.10.2026: Grundfunktion läuft.** Karte auflegen startet die zugeordnete Playlist auf der Peppa Box (Pi-Klinke), Karte weg = Pause, gleiche Karte = weiter. Offen: Player als Dienst beim Start, Lautsprecher/MAX98357A, MPR121, Drehgeber, Ein-Taste, Kopfhörer-Umschaltung, Karten bequemer anlernen.
- Player als Dienst `peppa-player` (systemd, Neustart nach Fehlern, wartet auf das Spotify-Gerät). Einrichten: `sh ~/peppa-box/software/dienst_einrichten.sh` (Benutzername wird beim Einrichten eingesetzt, steht nicht im Repository). Protokoll: `journalctl -u peppa-player -f`.
- Einstellungsseite fürs Handy im Player (`software/webui.py`, Port 8080, nur Standardbibliothek): aufgelegte Karte live, Spotify-Link + Name speichern, umbenennen, löschen. Nach dem Speichern startet die aufgelegte Karte sofort. Kein Passwort (jeder im Heim-WLAN kann Karten ändern) – später ggf. PIN.
- **Umstellung 25.10.: Link steht auf der Karte** (keine Zuordnungsliste mehr). Bespielen mit dem Handy, z. B. NFC Tools: Schreiben → URL → Spotify-Link. Box liest NDEF-URI von NTAG/Ultralight (Typ 2) und MIFARE Classic (NDEF-Sektoren mit öffentlichem Schlüssel D3F7D3F7D3F7). `karten.py`/`karte_zuordnen.py` entfernt, Webseite zeigt nur noch Status (Karte, Link) und die Anleitung. Test: `python3 ~/peppa-box/software/rc522.py`. Noch am Gerät zu prüfen; Typ der endgültigen NFC-Aufkleber offen (NTAG213/215 empfohlen).
- Rauschen an der Pi-Klinke (Kopfhörer): DAC bleibt draußen (Entscheidung Jan). Maßnahmen: Leser fragt nur noch 1× pro Sekunde ab, Funkfeld zwischen den Abfragen aus, „Karte weg“ erst nach zwei verpassten Abfragen. Raspotify: `LIBRESPOT_VOLUME_CTRL=fixed`, `LIBRESPOT_INITIAL_VOLUME=100` (Spotify fest 100 %), Lautstärke über ALSA-Regler `PCM` der Karte `Headphones`, gespeichert mit `alsactl store`.
- **Spotify-Konto der Box:** Eigenes Mitgliedskonto im Familien-Abo angelegt, Raspotify damit aber „error audio key 0 1“ (Titel springen im Sekundentakt, kein Ton). Bekanntes offenes librespot-Problem bei manchen (v. a. neuen) Premium-Konten: librespot-org/librespot #1735, #1649. Vorerst wieder Jans Konto. **Offen:** nach Raspotify-Updates (`sudo apt update && sudo apt upgrade`) erneut mit dem Box-Konto testen; dann Konto in der Entwickler-App unter User Management eintragen und `spotify_login.py` mit dem Box-Konto wiederholen.
- Einfarbiger Deckel für den Prototyp: `v4/out/02_deckel_einfarbig.stl` (Vereinigung von 02a + 02b, volumengleich geprüft). Wird nicht von `build_all.py` erzeugt; nach Deckeländerungen neu vereinigen.

## Nachtrag 26.10.2026 – Eltern-Seite (Stufe 1)

- Neuer Dienst **`peppa-web`** (`software/peppa_web.py`, Seite in `software/web/`), getrennt vom Player, damit Updates und Neustarts die Seite nicht mitreißen. Adresse: `http://<rechnername>.local` (Port 80) oder `:8080`. Nur Standardbibliothek. **Kein Passwort** (Entscheidung Jan); Schutz nur gegen untergeschobene Klicks fremder Webseiten (eigener Kopfeintrag `X-Peppa-Box`).
- Funktionen: Karte und Link live; Zustand (Akku, Musik bereit, WLAN, Temperatur, Speicher, Unterspannung über `vcgencmd get_throttled`, Laufzeit); **Nach Updates suchen / Jetzt aktualisieren / Zurück zur vorherigen Version** (git fetch, `merge --ff-only`, Rückweg per `reset --hard` auf die gespeicherte Version in `~/.config/peppa-box/vorherige_version.txt`; Update bricht ab, wenn auf dem Pi Dateien im Repository geändert wurden); Musik neu starten (Raspotify + Player); Box neu starten; Ausschalten; letzte Meldungen aus dem Protokoll.
- Player hat keine eigene Webseite mehr (`webui.py` entfernt). Er schreibt seinen Zustand jede Sekunde nach `/dev/shm/peppa-box-status.json` (Arbeitsspeicher, schont die SD-Karte).
- `dienst_einrichten.sh` richtet jetzt beide Dienste ein, dazu `/etc/sudoers.d/peppa-box` (nur `systemctl poweroff`, `reboot`, `restart peppa-player`, `restart raspotify`, geprüft mit `visudo`) und die Gruppen `i2c`, `adm`, `video`. **Einmal am Pi ausführen:** `cd ~/peppa-box && git pull && sh software/dienst_einrichten.sh`. Danach kommen Updates über die Seite.
- Akku: `software/akku.py` liest den INA219 des UPS HAT (D) an I2C 0x43 (laut Waveshare-Wiki), nur lesend. Spannung aus Register 0x02, Laderichtung aus dem Vorzeichen der Shunt-Spannung. **Offen:** Vorzeichen am Gerät prüfen (mit Netzteil = „wird geladen“?), Prozent ist eine grobe Kennlinie (Waveshare nennt nur 4,2 V = voll). Test: `python3 ~/peppa-box/software/akku.py`.
- Ausprobiert im Probelauf (`PEPPA_WEB_TROCKEN=1`, sudo-Befehle werden nur angezeigt): Update, Abbruch bei geänderten Dateien, Rückweg, alle Box-Aktionen, Seite hell/dunkel auf Handygröße. **Am Pi noch zu prüfen:** sudo-Freigabe, Port 80, Akkuanzeige, WLAN-Name (nmcli).
- Handy: Seite ist als Web-App vorbereitet (Manifest, Symbol). Über `http://` im Heimnetz legt Chrome nur eine Verknüpfung an (öffnet mit Adressleiste); als echte App ohne Adressleiste erst mit HTTPS.
- Plan unterwegs/Urlaub: **Tailscale** (Personal-Tarif kostenlos, privates Netz zwischen Box und Handys, ohne Portfreigabe im Router). `tailscale serve` liefert dabei HTTPS mit gültigem Zertifikat → echte Web-App. Noch nicht eingerichtet. Ebenfalls später: WLAN der Box umschalten (z. B. Urlaubs-WLAN, Handy-Hotspot); Systempakete (apt) über die Seite aktualisieren; Stufe 2 (Lautstärkegrenzen, Schlummer-Timer, Abendmodus, Auto-Aus).

## Nachtrag 26.10.2026 – Deckelrahmen war seitenverkehrt (Fehler behoben)

- Befund am Druck: Unter der Ein-Taste liegt der Rahmen statt des Tasterhalters, die vier Schrauben vorne/hinten passen nicht, nur die beiden seitlichen in der Rahmenmitte.
- Ursache: Fehler in der Druckausrichtung, nicht im Modell. `check.py/orient()` hat den Deckelrahmen für den Druck mit `mirror([0, 0, 1])` umgedreht. Eine Spiegelung ist keine Drehung → das STL `03_deckelrahmen.stl` war spiegelbildlich. Die seitlichen Schrauben (y 68 / 70) liegen fast auf der Mitte und passten deshalb trotzdem.
- Behoben: Deckelrahmen, Ein-Taste und die Coupons C2 (Rahmenecke) und C3 (Halter, Kappe) werden jetzt mit `rotate([180, 0, 0])` gedreht. Neue Prüfung in `check.py`: „Druckausrichtung ohne Spiegelung“ für alle Teile (Prüfkörper, Gegenprobe mit Spiegelung schlägt an). Neues STL gegen die Einbaulage geprüft: deckungsgleich.
- Deckel, Boden, Korpus, Kartenfach waren nicht betroffen. Ein-Taste ist rund und war nur formal betroffen; der alte Druck ist brauchbar.
- **Zu tun:** `03_deckelrahmen.stl` neu drucken. Coupons C2/C3, falls schon gedruckt, ebenfalls neu.

## Nachtrag 27.10.2026 – Eltern-Seite Stufe 2 (Lautstärke, Timer, Ruhezeit, Auto-Aus)

- **Aufteilung:** Die Seite (`peppa-web`) ändert nur Einstellungen und Dateien, ausgeführt wird im **Player** (`software/automatik.py`, ein Aufruf pro Sekunde). Dadurch überstehen Timer ein Update der Seite. Neue Module: `einstellungen.py` (Einstellungen prüfen/speichern, Ruhezeit-Logik), `lautstaerke.py` (amixer), `automatik.py`. `spotify.spielt()` fragt per Web API, ob die Box gerade spielt (alle 10 s).
- **Speicherorte:** Einstellungen in `~/.config/peppa-box/einstellungen.json` (nur auf dem Pi, bleibt bei Updates erhalten). Timer, „Ruhezeit ausgesetzt“, Status in `/dev/shm/peppa-box-*.json` (Arbeitsspeicher, nach Neustart der Box weg).
- **Lautstärke:** Regler auf der Seite, Höchst- und Startlautstärke je Ausgang (Kopfhörer/Klinke, Lautsprecher). Die Grenze gilt für den Regler, wird aber auch vom Player durchgesetzt (zu laut wird in höchstens 10 s heruntergesetzt, eine neue Grenze wirkt sofort). Startlautstärke einmal je Einschalten (Markierung in /dev/shm), ein Neustart des Players ändert die laufende Lautstärke nicht. Prozent = Regler wie `alsamixer` (`amixer -M`). **Lautsprecher ist noch „nicht eingerichtet“:** Der MAX98357A hat keinen Regler, dafür braucht es eine Software-Lautstärke (ALSA softvol); danach Karte und Reglername in `lautstaerke.py` (`AUSGABEN["lautsprecher"]`) eintragen. Bis dahin sind die Lautsprecher-Werte nur vorgemerkt. Die Kopfhörer-Erkennung (Öffner an Pin 37) fehlt noch; `aktive_ausgabe()` nimmt den Lautsprecher, sobald er eingerichtet ist.
- **Schlummer-Timer:** 15/30/45/60 Min. Die letzten 20 s wird leiser, dann Pause, dann ist die Lautstärke wieder wie vorher (auch wenn der Player mitten im Ausblenden neu startet). Abbrechen stellt die Lautstärke wieder her.
- **Ruhezeit (Abendmodus):** Von/Bis (darf über Mitternacht gehen), Modus „leiser“ (höchstens X %) oder „keine Musik“ (laufende Musik wird pausiert, Karten starten nicht). „Für heute aussetzen“ gilt bis zum Ende der Ruhezeit. Nach der Ruhezeit wird die Lautstärke nie von selbst lauter. Standard aus. **Die Ruhezeit richtet sich nach der Uhr der Box**, die Seite zeigt sie an; Zeitzone am Pi prüfen: `timedatectl`, ggf. `sudo timedatectl set-timezone Europe/Berlin`.
- **Auto-Aus:** Box fährt herunter (`systemctl poweroff`, dieselbe sudo-Freigabe), wenn die eingestellte Zeit nichts gespielt wurde. Als Aktivität zählt: Musik spielt auf der Box, **die Eltern-Seite ist geöffnet** (sonst würde sie mitten in einem Update ausgehen). Nach dem Einschalten bleibt die Box mindestens so lange an. Standard **aus**, 30 Min.
- **Geprüft ohne Hardware:** `software/test_automatik.py` (31 Tests, simulierte Uhr: Ausblenden, Ruhezeit über Mitternacht, Aussetzen, Auto-Aus, Neustart mitten im Timer, ungültige Eingaben; 13 eingebaute Fehler werden alle erkannt). Aufruf: `cd software && python3 -m unittest -v test_automatik`. Player mit simuliertem Leser (Karte in Ruhezeit startet nicht), Seite im Browser mit simuliertem `amixer` bedient (Regler, Timer, Schalter, Ruhezeit, Fehlermeldungen, hell/dunkel).
- **Am Pi noch zu prüfen:** (1) `amixer -M -c Headphones sget PCM` liefert Prozent, und der Regler klingt sinnvoll (Zuordnung Prozent zu Lautstärke am Gerät hören; Standardwerte 60 % max, 30 % Start sind Schätzwerte). (2) Gruppe `audio` für den Benutzer (setzt `dienst_einrichten.sh`, danach Dienste neu gestartet). (3) Zeitzone der Box. (4) Auto-Aus einmal mit kurzer Frist ausprobieren (10 Min, Seite schließen, nichts spielen).
- **Einrichtung:** Einmal `cd ~/peppa-box && git pull && sh software/dienst_einrichten.sh` (neue Gruppe `audio`); alternativ Update über die Seite, danach die Hinweiszeile beachten, die auf `dienst_einrichten.sh` verweist.
- **Offen / später:** Tailscale (HTTPS, unterwegs, echte Web-App), WLAN umschalten, apt-Update über die Seite, Touchfelder/Drehgeber/Ein-Taste (setzen dieselbe Lautstärke und denselben Timer, die Logik liegt jetzt in `lautstaerke.py`/`automatik.py`), Schreibschutz-Overlay (Einstellungen und Laufzeitdateien liegen dann außerhalb bzw. im RAM; `~/.config/peppa-box` muss beschreibbar bleiben).

## Nachtrag 27.10.2026 – Fehlerbehebung Eltern-Seite: Höchstlautstärke 100 % wurde nicht übernommen

- **Fehler:** Beim Öffnen von „Grenzen und Startlautstärke“ (und von „Ruhezeit einstellen“) lud die Seite die gespeicherten Werte nach und überschrieb das Formular. War die Box langsam (Pi unter Last), kam die Antwort, nachdem der Regler schon auf 100 % gezogen war; gespeichert wurden dann wieder die alten Werte, die Lautstärke blieb begrenzt. Auf einem schnellen Rechner kaum zu sehen, deshalb war es im Probelauf am 27.10. nicht aufgefallen.
- **Behebung (`software/web/index.html`):** Das Formular wird nur noch gefüllt, solange nichts darin verändert wurde (`geaendert`); es wird nicht mehr neu aufgebaut. Antworten, die vor einem Speichern angefragt wurden, werden verworfen (`stand`). Bei einem Fehler beim Speichern bleiben die Eingaben stehen. Dieselbe Absicherung für Lautstärke-Regler und Schalter: Hat jemand seit der Anfrage etwas bedient, werden die veralteten Werte nicht angezeigt.
- **Nachgestellt und geprüft** mit künstlich verzögerter Antwort (0,1 / 0,6 / 2 s): Ziehen während des Nachladens, anderes Formular öffnen bei ungespeicherten Änderungen, verspätete Antwort nach dem Speichern, echtes Ziehen mit der Maus bis 100 % mit Neuladen. Gesamte Bedienung (Regler, Timer, Schalter, Ruhezeit, Fehlermeldungen) ohne Konsolenfehler.
- **Regel für die Seite:** Werte, die der Benutzer gerade bearbeitet, nie durch nachladende Daten ersetzen; langsame Antworten sind am Pi der Normalfall.
- Hinweis zur Anzeige: Ist die Ruhezeit mit „leiser“ gerade aktiv, begrenzt sie den Regler unabhängig von der Höchstlautstärke; die Seite zeigt dann „höchstens X % (Ruhezeit)“.

## Nachtrag 27.10.2026 – Reichelt-Ersatz
- Reichelt liefert nicht. Touch-Modul jetzt **Adafruit 1982 (MPR121) bei Conrad, Bestell-Nr. 1516630**, 11,99 €. Produktbild zeigt die ältere Ausführung ohne STEMMA QT; welche geliefert wird, ist offen. Nach Lieferung Maße messen (Adafruit nennt 30 × 22 × 3 mm für die STEMMA-Ausführung) und Verteiler-Brücke (24 mm breit) anpassen.
- Klinke: Ersatz für Lumberg 1503-09 noch offen (Conrad: Einbaubuchse 3,5 mm stereo, Tafelmontage, mit Schaltkontakt). SpeaKa SP-1300376 (2 m, gerader Stecker) passt nicht: nur 20 mm hinter der Pi-Klinke. Kabel bleibt Goobay 67782 (90°) oder gleichwertig.
- Elko-Ersatz: BerryBase 1000 µF / 16 V, Ø 10 × 16 mm, RM 5 mm, 0,29 € (Conrad 445386 nicht lieferbar; Alternative Conrad 792067). 16 V statt 10 V gleichwertig. Beinlänge auf der Produktseite nicht eindeutig; für die Hebelklemmen werden ca. 11 mm gebraucht.
- Warenkörbe 27.10. (Stand Jan, noch nicht bestellt): **Conrad** STEC11B03 (700697), Adafruit 1982 (1516630), Lumberg 1503 09 (738813), Visaton FRS 8 4 Ω (300293). **BerryBase** Goobay 67782, 3 × Elko 1000 µF/16 V, 3 × WAGO 221-413, 2 × WAGO 221-415, Soldered USB-C Breakout (SOL-333011), 4 × 5,1 kΩ (CC1/CC2 nach GND). Fehlen noch: 2 × Kurzhubtaster 12 × 12 × 7,3 (BerryBase KHT1212PV73), Schrumpfschlauch, Kunststoffschrauben 3,0 mm, Montageband.
- **USB-C (Entscheidung 27.10.):** Statt Einbau-Verlängerung Jans vorhandenes USB-C-Kabel mit 90°-Stecker (passt hinter dem Akku-Board) halbieren, rote/schwarze Ader an Soldered-Breakout (22 × 22 mm, 2 Befestigungslöcher) in der Rückwand, 2 × 5,1 kΩ an CC. Akku-Board lädt nur mit 5 V (Waveshare-Wiki), daher reichen VBUS/GND. Modell: rundes Einbauloch durch Schlitz + Halter mit 2 Domen ersetzen, Maße nach Lieferung.
- **WAGO 221-413/-415** statt 221-423/-425: andere Bauform, Mulden nach Messen anpassen.

## Nachtrag 27.10.2026 – Deckel-Probedruck ausgewertet (Symbole, RC522-Halter)

- **Befund Deckel (einfarbig, 0,28 mm Extra Draft):** Bei vor/zurück lagen die Dreiecke auf der Ringnut (Ecken 0,06 mm von der Nut entfernt) und wurden angeschnitten. Mond unscharf, unruhige Oberfläche, Pickel an den Ringen, eine Kratzspur vom Kartenschlitz nach vorne (Fahrweg ohne Z-Hop).
- **Symbole neu (`pad_symbols`):** Jedes Symbol wird auf mindestens `SYM_GAP` = 1,8 mm Abstand zur Nut verkleinert (`_fit`), vor/zurück als zwei um 30 % überlappende Dreiecke (eine Fläche, kein dünner Steg), alles schmaler als `SYM_MIN` = 0,9 mm wird abgerundet (Mondspitzen, Ecken). Abstände jetzt: vor/zurück 2,2 mm, Play 3,2 mm, Mond 2,1 mm. Neue Prüfung in `check.py`.
- **`SKIN` 0,7 → 0,8 mm:** liegt jetzt auf dem Schichtraster (4 × 0,2 oder 5 × 0,16); Symbole sind 0,8 mm tief. Kunststoff über dem Kupfer: 4 mm, unter den Symbolen 3,2 mm.
- **Einfarbiger Deckel** `02_deckel_einfarbig.stl` wird jetzt von `build_all.py` erzeugt (`deckel(einfarbig=True)`, ein Körper statt Vereinigung). Dabei gefunden: `offset` erzeugte doppelte Punkte im Mond → nicht dichtes STL; behoben mit `simplify`. Alle STL geprüft: dicht.
- **RC522-Halter, Befund:** Die Steckkabel stießen an den hinteren Schraubblock des Deckelrahmens (x 116, Modell: 0,9 mm). Der Quarz liegt an der deckelseitigen Platinenkante nahe der Stiftleiste und lief gegen die Lippe der Schiene.
- **Behebung:** RC522 sitzt `RC_DROP` = 5 mm tiefer (weg vom Deckel). Nicht seitlich verschoben: Der Block liegt über den Steckern, seitlich bräuchte es über 20 mm und die Antenne käme weit vom NFC-Aufkleber weg. Antennenmitte liegt jetzt ca. 5 mm unter der Aufklebermitte → **Lesetest nach dem Druck**. Schraubblöcke hinten am Deckelrahmen enden 2 mm höher (`LS_BLOCK_Z0` 119, 3,2 mm Wand unter dem Kernloch). Deckelseitige Schiene: Lippe auf den letzten `RC_XTAL_FREE` = 18 mm vor dem Stiftleisten-Ende entfernt (Quarz laut Foto ca. 12 mm lang).
- Abstand Stecker ↔ Schraubblock: 3,7 mm (nur neues Kartenfach mit altem Rahmen: 2,1 mm). Kartenfach-Unterkante 81,8 mm, 4,8 mm über den Klemmen (vorher 9,8). Zum Tasterhalter bleiben seitlich 0,8 mm wie bisher (oberster Stecker).
- Die rechte Kartenfach-Schraube liegt direkt am Platinenende: erst Kartenfach verschrauben, dann RC522 einschieben.
- **Offen (messen):** Lage der Stiftleiste auf der RC522-Platine (deckelseitige Kante bis Mitte SDA-Stift; Modell nimmt mittig an, `RC_HDR_OFF`) und Länge des Quarzes ab Stiftleisten-Kante.
- **Druck Deckel (Empfehlung):** 0,2 mm (oder 0,16), mindestens 5 obere Schichten, „Nur eine Wand auf oberen Flächen“, Bügeln nur oberste Fläche, Z-Hop 0,4 mm, „Wände nicht kreuzen“, Oberflächen langsamer. Deckel mit 100 % Füllung (massiv ca. 125 g PETG): kein Durchzeichnen über den Taschen, gleichmäßigere Touchfelder. Für den endgültigen zweifarbigen Deckel als Option: kopfüber drucken mit bündig eingelegten Symbolen (glatteste Oberfläche) – noch nicht entschieden.
- **Touchfelder (Foto Unterseite):** Lage passt zum Modell. Die Taschendecken sind gebrückt und etwas rau; Kupferband trotzdem fest andrücken. Kupferband (BerryBase, 5 mm) steht in der Einkaufsliste, fehlt aber im BerryBase-Warenkorb vom 27.10. MPR121-Mulde (25,6 × 20,6 mm innen) passt nicht, falls die STEMMA-Ausführung (30 × 22 mm) kommt → nach Lieferung messen.
- **Zu drucken:** `04_kartenfach.stl` (zuerst, mit vorhandenem Rahmen testen), `02_deckel_einfarbig.stl` mit den Einstellungen oben; `03_deckelrahmen.stl` erst beim endgültigen Druck nötig.

## Nachtrag 27.10.2026 – Deckel kopfüber, Karte mit Einschub-Cover

- **Entscheidung:** Symbole bleiben ertastbar (0,8 mm vertieft). Für eine glatte Oberseite wird der Deckel **kopfüber** gedruckt (Oberseite auf dem texturierten PEI der Wendeplatte, nicht auf der glatten PLA-Seite). Die Böden der Symbolvertiefungen werden dabei als kurze Brücken gedruckt. Vorher Probe mit Coupon C9.
- **Modell Deckel:** 0,5-mm-Fase an der Oberkante (`LID_EDGE_CH`, gegen Elefantenfuß), Einführfase 0,6 mm am Kartenschlitz (`SLOT_CH`), Mulde der Ein-Taste mit 45°-Wand (Boden Ø 17 statt 20), Tastenloch endet unter einer **Opferschicht 0,2 mm** am Muldenboden (`BTN_MEMBRANE`) → nach dem Druck mit dem Cutter ausschneiden. Taschen für das Kupferband sind kopfüber oben offen (flacher Boden statt Brücke). Hilfsfunktion `deckel_kopfueber()` (Drehung, keine Spiegelung).
- **Coupon C9** (einfarbig, schon kopfüber ausgerichtet): `coupon_C9_deckel_kopfueber_felder.stl` (Ecke vorne rechts: Play, Vor, Kante, Kupfertaschen) und `coupon_C9_deckel_kopfueber_taste_schlitz.stl` (Ein-Taste mit Opferschicht, Ende des Kartenschlitzes, Kante). Slicer: Elefantenfuß-Kompensation ca. 0,15 mm, erste Schicht sauber, Platte vorher mit Spülmittel waschen. Die Deckel-STL liegen weiter mit der Oberseite nach oben; nach erfolgreichem C9 auf kopfüber umstellen.
- **Karte mit Einschubtasche** (`10_karte_orange.stl`, `karte_print()`): Cover auf Papier statt Aufkleber, wird von oben eingeschoben. Rahmen links, rechts, unten mit Lippen, deren Unterseite 45° geneigt ist (Schwalbenschwanz) → Druck **Rückseite unten** ohne Stützen, Vorderseite oben (bügeln). Einleger **67 × 68 mm**, sichtbares Fenster 64,6 × 67 mm. Spalt an der Außenwand `INS_GAP` 0,6 mm (Probedruck), Taschenboden 1,3 mm dick. Griffmulde R 7 oben Mitte in der Rückwand (Cover von vorn und hinten greifbar). NFC-Tasche jetzt an der Plattenseite (Decke Ø 25,6 als Brücke). Obere Ecken R 1,5 (Tasche muss gerade bis zur Kante laufen); die schräge Ecke oben rechts entfällt, die Richtung zeigt jetzt das Cover. Kartenstärke und Steckteil unverändert, Kollisionsprüfung jetzt mit der echten Karte.
- Empfehlung Cover: Farbdruck auf normalem Papier, laminieren (stabiler, abwischbar, ca. 0,25–0,35 mm), danach auf 67 × 68 mm schneiden.
- **Am Probedruck prüfen:** Spiel des Covers (fällt es heraus, wenn die Karte kopfüber gehalten wird?), Steifigkeit der Karte oben (1,3 mm hinter dem Cover), Lesen durch die neue Kartenrückseite.
- **Idee für später:** Druckvorlage für Cover auf der Eltern-Seite (Cover-Bild per Spotify Web API zur Karte holen, A4 mit Schnittmarken in Einlegergröße).

## Nachtrag 31.10.2026 – Lautsprecher (MAX98357A) eingerichtet

- Verstärker angeschlossen, `dtoverlay=hifiberry-dac` von Jan in `config.txt` ergänzt, `speaker-test` über die hifiberry-Karte erfolgreich.
- **Neu `software/lautsprecher_einrichten.sh`** (wird von `dienst_einrichten.sh` aufgerufen, wiederholbar): ergänzt in `config.txt` `dtoverlay=hifiberry-dac` und `gpio=16=ip,pn` (SD/stumm als Eingang ohne Pull, sonst zieht der Pi den Pin nach unten), nur wenn `config.txt` mit `[all]` endet; sucht die Karte in `/proc/asound/cards` (Name mit „hifiberry“, nicht angenommen); legt in `/etc/asound.conf` einen eigenen Block (Markierungen `# >>> / <<< peppa-box lautsprecher`) mit softvol `lautsprecher`, Regler `Lautsprecher` an; stellt Raspotify auf `LIBRESPOT_DEVICE="lautsprecher"` um; legt den Regler beim ersten Mal an (1 s Stille) und stellt ihn auf 30 %, `alsactl store`.
- **`lautstaerke.py`:** Ausgang `lautsprecher` = gesuchte hifiberry-Karte + Regler `Lautsprecher`. Gilt als eingerichtet, sobald Karte und Regler da sind (sonst alle 30 s neu geprüft). Damit gelten Eltern-Seite, Höchst-/Startlautstärke (Standard 70/40 %), Timer und Ruhezeit für den Lautsprecher.
- **Folge bis zur Kopfhörer-Erkennung (Pin 37):** Die Pi-Klinke ist stumm, alles läuft über den Lautsprecher. Zurück auf die Klinke: in `/etc/raspotify/conf` `LIBRESPOT_DEVICE="plughw:CARD=Headphones,DEV=0"`.
- Update-Hinweis der Eltern-Seite erscheint jetzt auch bei Änderungen an `lautsprecher_einrichten.sh`.
- Geprüft ohne Hardware: `software/test_lautsprecher.py` (11 Tests: Kartensuche, Regler fehlt, spätere Einrichtung, Skript mit nachgebauten Systemdateien, zweiter Lauf ändert nichts, Abbruch ohne `[all]`, Raspotify ohne Device-Zeile); `test_automatik` weiter grün.
- **Am Pi einmal ausführen:** Update über die Eltern-Seite, dann per SSH `sh ~/peppa-box/software/dienst_einrichten.sh`. Root-Änderungen (config.txt, asound.conf, Raspotify) gehen bewusst nicht über die Seite, weil sie ohne Passwort erreichbar ist.
- **Am Pi noch zu prüfen:** Karte auflegen → Ton aus dem Lautsprecher; Regler der Eltern-Seite wirkt; nach Neustart nicht stumm (GPIO 16); Prozentwerte klingen sinnvoll.
- **Erster Lauf am Pi (31.10.):** Karte `sndrpihifiberry` gefunden, softvol und Regler angelegt, `gpio=16=ip,pn` ergänzt. Raspotify wurde **nicht** umgestellt: Das Skript prüfte `/etc/raspotify/conf` ohne sudo (Datei nur mit sudo lesbar) und hielt sie für nicht vorhanden. Behoben mit `sudo test -f`. Regel: Dateien unter `/etc/raspotify/` immer mit sudo prüfen und lesen.

## Nachtrag 02.11.2026 – Lautsprecher läuft sauber (Fehlersuche Kratzen)

- **Befund:** Mit Verstärker an 5 V/GND direkt auf den gelben Stiften (Pin 2/6, Steckkabel 35 cm), ohne Elko: kein Ton oder starkes Kratzen, Ton nur beim Berühren eines Kontakts (Daumen, Messspitze) oder Zusammendrücken des Kabelbündels. Zweiter, neu gelöteter MAX98357A zeigte dasselbe → Verstärker und Lötstellen nicht die Ursache. Gemessen in Ordnung: 5,2 V am Aufsatz und am Verstärker, BCLK/LRC ≈ 1,6 V, SD > 0,2 V, Lautsprecher 4 Ω.
- **Behebung:** **Elko 1000 µF / 16 V** wie geplant in die WAGO 5 V / GND A, Rot (VIN) und Braun (GND) dafür ca. 10 cm vor dem Verstärker getrennt und über die WAGO geführt. Danach Musik sauber. Signalleitungen BCLK/LRC/DIN/SD unverändert (35 cm, direkt auf den gelben Stiften P18/P19/P21/P16) – Länge ist also kein Hindernis; für den Einbau trotzdem kürzer (≤ 15 cm).
- **Zwischenfehler:** Dünne, unverzinnte Steckkabel-Litze hatte in der WAGO keinen Kontakt (Litze an der Feder vorbei). **Regel:** Steckkabel-Litze für WAGO (min. 0,14–0,2 mm² laut Hersteller) 11 mm abisolieren, doppelt falten, verdrillen, verzinnen, bei offenem Hebel bis Anschlag, Zugtest, Durchgang prüfen.
- **Hinweise:** Die 5,1-kΩ-Widerstände aus der BerryBase-Bestellung sind für USB-C (CC), nicht für Signalleitungen. Lautsprecheranschlüsse des MAX98357A nie mit GND verbinden (Brückenausgang). Mehrzeilige Befehle per SSH einzeln einfügen (sonst werden Zeilen von der sudo-Passwortabfrage verschluckt).
- **Noch offen:** Lautsprecher-Regler der Eltern-Seite und Höchstlautstärke (70 %) am Gerät hören; Raspotify startet nach dem Einschalten vor dem WLAN (Fehlstart ca. 20 s, Neustart durch systemd) → auf `network-online` warten lassen.
- **Lauter (02.11.):** MAX98357A **GAIN an GND** (WAGO GND A bzw. freier GND-Stift) → 12 dB statt 9 dB (+3 dB), Jan gefällt es so. 15 dB (100 kΩ nach GND) bewusst nicht: bei 5 V übersteuert der Verstärker schon mit 12 dB an lauten Stellen; bei Verzerrung Höchstlautstärke auf der Eltern-Seite auf ca. 85–90 % senken. Belastbarkeit des Visaton FRS 8 noch prüfen (MAX liefert an 4 Ω/5 V max. ca. 3 W). Verdrahtungsplan nachgeführt (GAIN-Verbindung, WAGO GND A).
- **Raspotify wartet auf das Netz (02.11.):** `dienst_einrichten.sh` legt `/etc/systemd/system/raspotify.service.d/peppa-netz.conf` an (`Wants=`/`After=network-online.target`, `RestartSec=3`) und aktiviert `NetworkManager-wait-online`, falls vorhanden. Grund: Raspotify startete vor dem WLAN („could not initialize spirc: Service unavailable“), Neustart erst ca. 23 s später. Wirkt ab dem nächsten Einschalten. **Am Pi prüfen:** nach `sudo reboot` `journalctl -b -u raspotify --no-pager | head` (kein Fehler mehr) und `systemd-analyze blame | head` (wie lange `NetworkManager-wait-online` braucht).

## Nachtrag 02.11.2026 – Signaltöne
- **Startton** (zwei aufsteigende Töne E5–A5): neuer Dienst `peppa-startton` (oneshot, nach `sound.target`/`alsa-restore`, vor dem WLAN). Setzt vorher die Startlautstärke (gleiche Logik wie der Player, einmal je Einschalten), wenn der Lautsprecher-Regler schon da ist; sonst macht es später der Player.
- **Bereit-Ton** (drei helle Töne C6–E6–G6): spielt der Player, sobald Spotify die Box kennt – nicht schon beim WLAN, weil erst dann eine Karte Musik starten kann. Einmal je Einschalten (Markierung in `/dev/shm`), also nicht nach Updates oder „Musik neu starten“.
- Beide Töne: `software/toene.py`, nur Standardbibliothek, WAV im Arbeitsspeicher erzeugt, Pegel 35 % der Vollaussteuerung, über den aktiven Ausgang. In der Ruhezeit mit Modus „keine Musik“ still. Fehler beim Abspielen werden protokolliert und halten nichts auf. Von Hand: `python3 ~/peppa-box/software/toene.py start` bzw. `bereit`.
- Geprüft ohne Hardware: `test_toene.py` (8 Tests). **Am Pi prüfen:** beide Töne nach dem Einschalten hörbar; Zeitpunkte mit `journalctl -b -u peppa-startton -u peppa-player --no-pager -o short-monotonic | head -30`.
- Offen/Idee: Fehlerton, wenn nach ca. 60 s kein WLAN/Spotify.
- **Änderung (02.11., ersetzt die Signaltöne oben):** Keine Pieptöne mehr. Stattdessen die Ansage **„Peppa Box bereit – viel Spaß“** (Stimme „Helmut“, von Jan mit ElevenLabs erzeugt), sobald eine Karte Musik starten kann – also wenn Spotify die Box kennt, einmal je Einschalten, über den aktiven Ausgang in der Startlautstärke. Datei `software/ansagen/peppa_box_bereit.wav` (aus Jans MP3: Ende ab 2,62 s abgeschnitten, 80 ms ausgeblendet, Spitze −3 dBFS, 150 ms Stille vorne gegen Verschlucken beim Aufwachen des Verstärkers, 44,1 kHz mono). Startton-Dienst entfernt; `dienst_einrichten.sh` räumt einen schon eingerichteten `peppa-startton` wieder ab. Test von Hand: `python3 ~/peppa-box/software/toene.py bereit`. Tests: `test_toene.py` (6).

## Nachtrag 02.11.2026 – Kurzhubtaster KHT1212PV73 geprüft

- Geliefert: BerryBase KHT1212PV73, 12 × 12 mm, H 7,30 mm (Etikett), Stößel 3,8 × 3,8 mm (Shopangabe). Hub steht nirgends, bei 12 × 12 üblich 0,25–0,3 mm (nicht belegt).
- Modell v4 ist schon seit 25.10. auf genau diesen Taster ausgelegt (`SW` 12, `SW_H` 7,3; jetzt Status „belegt“ statt „vorläufig“). Die alte Angabe „DTS-24R“ in der Hardwareliste ist ersetzt.
- Kette in Ruhe: Kragen der Kappe liegt unter dem Deckel an, Stößel Ø 5 endet 0,05 mm über dem Taster. Beim Drücken bleiben bis zum Anschlag am Trichter 0,52 mm, also ca. 0,2 mm Reserve über dem Schaltweg. Die Taschenwand fängt kräftiges Drücken nicht ab, der 3-mm-Halterboden trägt.
- Einbau: Beinchen nach links/rechts (Schlitz 14 × 7 mm läuft in x). Um 90° gedreht passen die Beinchen nicht durch. Anschluss diagonal (zwei gegenüberliegende Ecken), dann ist die Belegung egal.
- Toleranz: Ist der Taster 0,2 mm niedriger als 7,3, schaltet er knapp oder gar nicht. Ausgleich nur über die Kappe (`PLUNGER_L`), Rahmen bleibt. Höhe mit dem Messschieber nachmessen; Coupon C3 (Halter, Kappe, Deckelstück) zeigt es am Druck.

- **Nachtrag 02.11. (2):** Jan misst über die Beinchen ca. 13 mm (`SW_LEGS`, gemessen). Die Tasche war nur 12,4 mm breit, der Taster ging mit Beinchen nicht von oben hinein. Neu: Beinchen-Kanal 14 × 7 mm (`SW_LEG_CLR` 0,5 je Seite) über die ganze Taschenhöhe bis unten durch den Halterboden. Die Tasche bleibt sonst 12,4 × 12,4 und führt den Taster an den Ecken. Seitenwand des Halters jetzt 2,3 mm. Lage und Höhe des Tasters unverändert → Kappe (`08_ein_taste_orange.stl`) bleibt gleich. Neu gebaut: `03_deckelrahmen.stl`, `coupon_C3_taste_halter.stl`; Prüfungen ohne Kollision.

## Nachtrag 02.11.2026 – Box nach einer Weile nicht mehr erreichbar
- Befund Jan: Musik läuft, aber `peppabox.local` (Eltern-Seite, SSH) nach einiger Zeit nicht mehr erreichbar. Vermutete Ursache: Stromsparmodus des WLAN-Chips (brcmfmac) – eingehende Anfragen bleiben liegen, ausgehende Verbindungen (Spotify) laufen weiter. Noch am Pi bestätigen: `iw dev wlan0 get power_save` (vorher „on“).
- `dienst_einrichten.sh` legt `/etc/NetworkManager/conf.d/peppa-wlan-stromsparen-aus.conf` an (`wifi.powersave = 2`, dauerhaft ab dem nächsten Einschalten) und schaltet es sofort mit `iw dev wlan0 set power_save off` ab (ohne die Verbindung neu aufzubauen). Etwas mehr Stromverbrauch im Leerlauf; Akkulaufzeit beobachten.

## Nachtrag 02.11.2026 – Knacken beim Abspielbeginn
- Befund: Lautes Knacken bei jedem Abspielbeginn (Karte, Ansage). Ursache: In Pausen stoppt der Pi den I2S-Takt, der MAX98357A schaltet ab und springt beim nächsten Ton hart wieder an.
- **Lösung (in `lautsprecher_einrichten.sh`):** Mischer `peppa_dmix` (44,1 kHz, S16_LE, `ipc_perm 0666`) → `peppa_plug` → softvol `lautsprecher` (Regler wie bisher). Neuer Dienst **`peppa-stille`** spielt dauerhaft Stille in den Mischer; Spotify und Ansage werden dazugemischt, der Takt reißt nie ab.
- **Gegen das Knacken beim Ein-/Ausschalten:** `config.txt` jetzt `gpio=16=op,dl` (SD beim Start low = stumm; ersetzt `ip,pn`). `peppa-stille`: vor dem Start SD low, Stille starten, 0,5 s später SD frei (Eingang ohne Pull); beim Stoppen erst SD low, dann Stille aus. Raspotify bekommt `PrivateIPC=no` (Zusatzdatei `peppa-ipc.conf`), damit es den Mischer mitbenutzen kann. Skript macht am Ende eine Probe (zweites Programm spielt neben der Stille).
- Nebenwirkung: Verstärker dauerhaft an (laut Hersteller wenige mA Ruhestrom), etwas CPU für die Stille. Akkulaufzeit beobachten.
- Geprüft ohne Hardware: ALSA liest die Konfiguration fehlerfrei (`aplay -L`), `test_lautsprecher.py` angepasst (12 Tests). **Am Pi prüfen:** kein Knacken bei Karte/Ansage, beim Einschalten, beim Ausschalten; `systemctl status peppa-stille`.

## Nachtrag 02.11.2026 – Startzeit
- Messung (`systemd-analyze`, Neustart 21:50): Kernel 4,2 s + Userspace 47,0 s; Ansage „bereit“ bei ca. 57 s. Kritischer Pfad: cloud-init (main 3,55 s + local 0,76 s + network 0,27 s) → NetworkManager 14,8 s → NetworkManager-wait-online 19,1 s → network-online bei ca. 50 s → Raspotify → Player (fragte nur alle 5 s).
- Umgesetzt: `dienst_einrichten.sh` schaltet **cloud-init** ab (`/etc/cloud/cloud-init.disabled`, nur für den ersten Start mit dem Imager nötig; rückgängig durch Löschen der Datei). Player fragt Spotify in der ersten Minute **jede Sekunde** statt alle 5 s.
- **Offen, größter Posten:** WLAN-Aufbau (NetworkManager + wait-online ≈ 34 s). Nächster Schritt: `journalctl -b -u NetworkManager -o short-monotonic` ansehen (Suche, Anmeldung, DHCP, IPv6?).
- **Fehler durch cloud-init-Abschalten (02.11., 22:00):** Nach dem Neustart kam die Ansage (WLAN/Spotify ok), aber weder `peppabox.local` noch `raspberrypi.local` waren erreichbar. Vermutete Ursache: cloud-init setzte den Rechnernamen bei jedem Start; ohne cloud-init fehlt er (Bestätigung mit `hostnamectl` am Pi steht aus). Zugang über IP aus dem Router (Pi-MAC beginnt mit B8:27:EB), dann `sudo hostnamectl set-hostname peppabox`, `127.0.1.1 peppabox` in `/etc/hosts`, `avahi-daemon` neu starten.
- `dienst_einrichten.sh` schreibt den Namen jetzt **vor** dem Abschalten fest (`hostnamectl`, `/etc/hosts`; „localhost“/„raspberrypi“/leer → „peppabox“) und läuft auch bei schon abgeschaltetem cloud-init. **Regel:** Systemdienste, die beim Start etwas setzen, erst abschalten, wenn geprüft ist, was sie setzen.
- **Korrektur, eigentliche Ursache (02.11., 22:06):** Name war nie weg (`hostnamectl`: peppabox; Speedport zeigt „peppabox“, 192.168.2.223). Avahi-Protokoll: „Host name conflict, retrying with peppabox-2“ nach Neuaufbau der WLAN-Adressen (v. a. IPv6) → Box hieß **peppabox-2.local**. Bekannter Avahi-Selbstkonflikt auf dem Pi; vermutlich auch die Ursache der früheren „nach einer Weile nicht erreichbar“-Fälle (WLAN-Stromsparen-aus bleibt trotzdem drin).
- `dienst_einrichten.sh` setzt in `/etc/avahi/avahi-daemon.conf` `use-ipv6=no` und `allow-interfaces=wlan0` und startet Avahi neu. Sofortmaßnahme bei Auftreten: `sudo systemctl restart avahi-daemon`. Notzugang immer über IP (Speedport → Heimnetz). Tipp: im Speedport feste IP für die Box einstellen.
- **WLAN-Aufbau analysiert (02.11., 22:16):** Anmeldung am Speedport dauert 0,4 s, DHCP 3 s – das WLAN ist nicht das Problem. Die Zeit geht **vorher** verloren: NetworkManager ruft beim Start viermal `netplan generate` auf (je ca. 3,4 s, 13,5 → 27,5 s). Netplan stammt vom Imager/cloud-init (`/etc/netplan/90-NM-*.yaml`, Verbindung `netplan-wlan0-…`; außerdem eine überflüssige `netplan-eth0`, der Pi 3A+ hat kein LAN).
- **Neu `software/wlan_beschleunigen.sh`** (bewusst von Hand, nicht über `dienst_einrichten.sh`): übernimmt SSID und Passwort der laufenden Netplan-Verbindung auf dem Pi in `/etc/NetworkManager/system-connections/peppa-wlan.nmconnection` (0600, Passwort wird nie angezeigt, nicht im Repository), verschiebt `/etc/netplan/*.yaml` nach `/etc/netplan.peppa-sicherung`, richtet `peppa-wlan-rueckfall` ein (`wlan_rueckfall.sh`: ohne WLAN nach 120 s → Netplan-Zustand zurück, NetworkManager neu starten). Rückweg: `sh wlan_beschleunigen.sh --zurueck` + Neustart. Tests: `test_wlan.py` (5). **Am Pi:** ausführen, `sudo reboot`, Startzeit erneut messen.

## Nachtrag 02.11.2026 – USB-C-Breakout
- Soldered-Breakout geliefert (mit beiliegender 8er-Stiftleiste). **Stiftleiste wird nicht eingelötet:** Kabeladern direkt in die Lötaugen (weniger Lötstellen, kein Steckkontakt im Ladestrom, flacher in der Rückwand).
- Messung Jan (Multimeter Ω, CC1–GND): **O.L** → keine CC-Widerstände auf der Platine. Die 2 × 5,1 kΩ (CC1 → GND, CC2 → GND) werden eingelötet. Belegung: VBUS = rote Ader, GND = schwarze Ader, D+/D−/SBU1/SBU2 frei.
- **Offen:** CC2–GND ebenfalls messen; nach dem Löten Lochabstand der 2 Befestigungslöcher und Buchsenhöhe über der Platine messen → Halter in der Rückwand.
- **Ergebnis am Pi (02.11., 22:30):** `wlan_beschleunigen.sh` läuft, Box im WLAN. NetworkManager 4,9 s (vorher 14,8 s), Ansage „bereit“ bei **40,6 s** (vorher ca. 57 s). `peppa-wlan-rueckfall` 20,6 s ist nur seine Warteschleife bis zur WLAN-Verbindung (läuft parallel, bremst den Player nicht). Verbleibend: NetworkManager-wait-online 19,3 s – noch unklar, ob WLAN-Chip/Treiber oder Suche; nächster Blick: NetworkManager-Protokoll dieses Starts.
- **Eltern-Seite nicht erreichbar, SSH schon (02.11., 22:55):** Avahi in Ordnung (`use-ipv6=no`, `allow-interfaces=wlan0`, kein Umbenennen), WLAN-Stromsparen aus. Vermutete Ursache: Die Seite lauschte nur auf IPv4 (`0.0.0.0`), der Windows-PC spricht die Box per IPv6 an (Anmeldung „from 2003:…“), und mit der neuen WLAN-Verbindung hat sich die IPv6-Adresse geändert. **`peppa_web.py` lauscht jetzt auf IPv6 und IPv4** (`::`, `IPV6_V6ONLY=0`; ohne IPv6 Rückfall auf IPv4). In der Arbeitsumgebung nur der IPv4-Rückfall testbar (dort kein IPv6). Notzugang zur Seite: `http://<IP>` (z. B. 192.168.2.223). **Am Pi bestätigt (22:57): Seite wieder erreichbar.**

## Offener Punkt (02.11.2026): WLAN wechseln unterwegs – Konzept, Umsetzung später (Entscheidung Jan)
- **Problem:** Am Urlaubsort kennt die Box kein WLAN → offline → Eltern-Seite nicht erreichbar.
- **Baustein 1 – WLAN-Verwaltung auf der Eltern-Seite:** gespeicherte WLANs anzeigen/hinzufügen/löschen, „WLANs in der Nähe suchen“, Passwort eingeben; sicherer Wechsel (klappt das neue WLAN nicht in ca. 60 s → zurück ins alte). Neue WLANs als NetworkManager-Keyfile schreiben (nicht über `nmcli connection add`, das legt wieder Netplan-Dateien an → langsamer Start). Rechte: kleines Hilfsprogramm über die bestehende sudo-Freigabe.
- **Baustein 2 – Handy-Hotspots von Jan und seiner Frau** zu Hause vorab eintragen: unterwegs Hotspot an → Box verbindet sich → Eltern-Seite übers Handy → Hotel-/Ferien-WLAN eintragen → Hotspot aus.
- **Baustein 3 – Notfall-WLAN der Box** („Peppa Box Einrichtung“, mit Passwort), wenn nach ca. 90 s kein bekanntes WLAN: Handy verbinden, Einrichtungsseite, WLAN wählen. WLAN-Chip kann AP-Modus (NetworkManager-Protokoll).
- Grenzen: WLANs mit Anmeldeseite (Hotels) gehen nur über den Handy-Hotspot.
- **Vorher reparieren:** `peppa-wlan-rueckfall` würde ohne bekanntes WLAN (Urlaub) nach 120 s die Netplan-Sicherung zurückholen und `peppa-wlan` löschen (nicht gefährlich, Heim-WLAN bleibt, aber Start wieder langsam). Soll sich nach dem ersten erfolgreichen Start abschalten.
- Empfehlung: erst Baustein 1+2, danach 3.

## Nachtrag 02.11.2026 – USB-C-Buchse und Ladeanzeige
- USB-C-Breakout (Soldered) eingebaut: an der Platine 4,95 V, GND-Durchgang zum Stecker ok, **blaue LED am Akku-Board leuchtet** (laut Waveshare-Wiki UPS HAT (D): blau an = lädt, aus = voll, blinkt = Fehler). Buchse damit sehr wahrscheinlich in Ordnung. Netzteil: Notebook-USB-C-Netzteil (5-V-Angabe noch ablesen).
- `akku.py` zeigt mit Netzteil trotzdem „akku“ (shunt −6,48 mV über die Buchse, −4,47 mV direkt; Akku 4,14–4,15 V ≈ 95 %). Waveshare: negativ = Akku gibt Strom ab (Laststrom), positiv = Ladestrom. Vermutung (nicht belegt): Bei fast vollem Akku lädt das Board nur noch wenig nach, Pi + Verstärker ziehen mehr → unterm Strich negativ. **Die Ladeanzeige der Eltern-Seite ist also bei fast vollem Akku irreführend.**
- **Offen:** Test bei ca. 60 % Akku mit Netzteil in der Buchse (`shunt_mv` positiv erwartet). Danach Anzeige überarbeiten; möglich: prüfen, ob das zweite I2C-Gerät des Boards (0x2D) einen Ladezustand liefert (nicht belegt, erst nachsehen).

## Nachtrag 02.11.2026 (3) – Ein-Taste bündig, Mulde entfällt

- Befund am Druck: Kappe und Taster passen genau, Ringspalt gut. Die Mulde um die Taste wirkt billig.
- Neu: **keine Mulde mehr**. Die Kappe endet **bündig** mit der Deckeloberfläche (`BTN_FLUSH` 0), sichtbar bleibt nur der Ringspalt 0,25 mm je Seite (`BTN_GAP`, wie gedruckt). Oberkante der Kappe mit Fase 0,3 mm (`BTN_TOP_CH`).
- Bohrung geht glatt bis zur Oberfläche. Beim Druck kopfüber liegt die Öffnung auf der Platte → keine Brücke, **Opferschicht entfällt** (`DISH_D`, `DISH_DEPTH`, `DISH_WALL`, `BTN_MEMBRANE` gelöscht). Elefantenfuß-Kompensation (ca. 0,15 mm) bleibt wichtig, sonst wird das Loch an der Oberfläche enger.
- Unter dem Deckel unverändert: Kragen, Stößel, Tasterhalter, Schaltweg. Die Kappe ist oben 1,5 mm länger. Neu gebaut: `02_deckel_einfarbig`, `02a`, `02b`, `08_ein_taste_orange`, Coupons C2 (Deckel), C3 (Deckelstück, Kappe), C9; Schnitt `ein_taste_schnitt.png`. Prüfungen ohne Kollision.
- Folge: Die Mulde schützte gegen versehentliches Drücken. Ausgleich in der Software: Ausschalten erst nach ca. 2 s Halten, kurzes Drücken nur Wecken/Anzeige.

## Nachtrag 03.11.2026 – Kein Ton trotz erkannter Karte (Fehlersuche läuft)
- Befund Jan (19:00): Karte wird erkannt, Player schickt den Startbefehl, Spotify antwortet **502 „Bad gateway“** (Spotify erreicht die Box nicht). Vorher mehrere Karten schnell hintereinander gewechselt. Auch nach „Musik neu starten“ und Neustart kein Ton. In der Spotify-App ist „Peppa Box“ auswählbar, springt aber sofort auf Pause → Raspotify/librespot spielt nicht (Verdacht: Audio-Key-Fehler, Anmeldung oder Ausgang `lautsprecher` nicht zu öffnen). Raspotify-Protokoll steht noch aus.
- Eltern-Seite: „Letzte Meldungen“ zeigt jetzt auch `raspotify` und `peppa-stille` (100 Zeilen) und springt automatisch ans Ende (neueste Meldung unten). Update über die Seite, kein SSH nötig.
- Geplant: Player fasst schnelle Kartenwechsel zusammen (nur letzter Befehl) und startet Raspotify bei 502 selbst neu.

## Nachtrag 03.11.2026 – Selbstreparatur Spotify (Player-Umbau)
- **Ziel (Jan):** Das Kind darf nie Fehler beheben müssen; alles abfangen, ohne Komforteinbußen.
- **Neu `software/steuerung.py`** (eigener Faden im Player): Kartenleser meldet nur noch den Wunsch (spielen/Pause) und wartet nie auf das Netz. Die Steuerung setzt immer nur den neuesten Wunsch um und **prüft nach jedem Start** über `GET /me/player`, ob auf dieser Box ein Titel läuft und die Position vorrückt (zwei Proben, 2 s Abstand, höchstens 4).
- **Reparatur-Leiter:** 1. kurz wiederholen bzw. sofort frisch abspielen (statt Fortsetzen), 2. Raspotify neu starten (vorher `peppa-stille` neu, falls der Mischer nicht läuft), 3. mit wachsendem Abstand weiter (2 s … 5 min), solange die Karte liegt. Raspotify-Neustart höchstens alle 120 s. 401 → Token erneuern, 429 → Retry-After, Netz weg → warten (kein Neustart). Gerät fehlt bei liegender Karte 45 s bzw. im Leerlauf 180 s → Raspotify neu.
- **Absturz-Wache:** Startzeit von Raspotify (systemd, lokal, alle 5 s). Neustart während Musik und liegender Karte → Wiedergabe an derselben Stelle übertragen, sonst frisch abspielen.
- **Schnelle Kartenwechsel:** Startbefehle mindestens 2,5 s auseinander, dazwischen nur der zuletzt gewünschte Link. Normalfall unverändert schnell (Start sofort).
- **Karte vor „bereit“ aufgelegt:** startet automatisch, sobald Spotify die Box kennt.
- **Automatik** pausiert über eine Hülle (`SpotifyFuerAutomatik`): Timer-/Ruhezeit-Pause gilt als gewollt und wird nicht „repariert“; ohne bekanntes Gerät wird nichts pausiert (traf sonst evtl. das Handy).
- **Player:** Lesefehler 5× in Folge → RC522 neu einrichten. Steuerungsfaden wird überwacht und neu gestartet. systemd-Watchdog (`WatchdogSec=30`, sd_notify ohne Zusatzpaket). `spotify.py`: `AnmeldungFehlt` statt `SystemExit` (Player läuft weiter, Klartext auf der Seite), Token-Sperre zwischen Fäden, Zeitlimit 8 s, Retry-After bei 429, neu `zustand()`, `uebertragen()`, `token_verwerfen()`.
- **Eltern-Seite:** Musik zeigt „kümmert sich“ mit Klartext, solange die Steuerung repariert.
- **Gemessen in der Simulation (Zeit bis Musik):** normal sofort; 502 ca. 14 s; „angenommen, spielt nicht“ / springende Titel / hängende Position ca. 23 s. Langsamer Start (Ton nach 5 s) löst keinen Neustart aus.
- **Geprüft ohne Hardware:** `test_steuerung.py` (24 Tests, simulierte Uhr), 13 eingebaute Fehler werden alle erkannt; Probelauf des ganzen Players mit simuliertem Leser/Spotify (502 → Neustart → spielt, READY/WATCHDOG kommen an); Seite im Browser mit Problemanzeige. Alle 78 Tests grün.
- **Am Pi einmal per SSH:** `cd ~/peppa-box && git pull && sh software/dienst_einrichten.sh` (Watchdog, „nie aufgeben“ für Player und Raspotify, sudo-Freigabe `restart peppa-stille`). Ohne diesen Schritt läuft alles andere schon nach dem Update über die Seite.
- **Am Pi prüfen:** Karte auflegen (Start wie bisher sofort), mehrere Karten schnell wechseln (am Ende spielt die letzte), `sudo systemctl restart raspotify` während Musik (geht nach einigen Sekunden an derselben Stelle weiter), Karte während des Hochfahrens auflegen.
- **Idee:** kurze Ansage „Einen Moment …“ (ElevenLabs, Stimme Helmut), wenn eine Reparatur länger als ca. 5 s dauert, damit das Kind weiß, dass die Box arbeitet.
