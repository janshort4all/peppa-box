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
