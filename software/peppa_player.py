#!/usr/bin/env python3
"""Peppa Box – Grundfunktion: Karte auflegen = Spotify-Link auf der Karte spielt, Karte weg = Pause,
dieselbe Karte wieder auflegen = weiter, andere Karte = neue Playlist.
Den Link schreibt man mit einer Handy-App (z. B. NFC Tools: Schreiben -> URL) auf die Karte.
Zustand (Karte, Link, Spotify bereit, Ausgang, Ruhezeit, Auto-Aus) schreibt der Player nach
/dev/shm/peppa-box-status.json; die Eltern-Seite (Dienst peppa-web, peppa_web.py) zeigt ihn an.
Die Automatik (Schlummer-Timer, Ruhezeit, Auto-Aus, Lautstärke-Grenzen) steht in automatik.py.
Start von Hand: python3 ~/peppa-box/software/peppa_player.py   (laeuft sonst als Dienst peppa-player)
"""
import json
import os
import time

import automatik
import einstellungen
import lautstaerke
import spotify
from rc522 import RC522

GERAET = "Peppa Box"          # Name in /etc/raspotify/conf (LIBRESPOT_NAME)
ABFRAGE = 1.0                 # Sekunden zwischen zwei Abfragen des Lesers
WEG_NACH = 1.5                # Sekunden ohne Karte, bis "entfernt" gilt (= zwei verpasste Abfragen)
STATUS_DATEI = einstellungen.lauf_pfad("status")    # im Arbeitsspeicher, schont die SD-Karte
ZUSTAND = {"karte": None, "link": None, "spotify_bereit": False}


def log(text):
    print(time.strftime("%H:%M:%S"), text, flush=True)


def status_schreiben():
    """Zustand fuer die Eltern-Seite ablegen (atomar: erst temporaere Datei, dann umbenennen)."""
    try:
        tmp = STATUS_DATEI + ".tmp"
        with open(tmp, "w") as f:
            json.dump(dict(ZUSTAND, zeit=time.time()), f)
        os.replace(tmp, STATUS_DATEI)
    except OSError:
        pass


def warte_auf_geraet():
    """Wartet, bis Raspotify bei Spotify angemeldet ist (nach dem Einschalten dauert das etwas)."""
    gemeldet = False
    while True:
        status_schreiben()
        try:
            dev = spotify.geraet_id(GERAET)
            if dev:
                return dev
            if not gemeldet:
                namen = ", ".join(d["name"] for d in spotify.geraete()) or "keine"
                log(f"Warte auf Spotify-Geraet '{GERAET}' (sichtbar: {namen}) ...")
                gemeldet = True
        except Exception as e:
            if not gemeldet:
                log(f"Warte auf Spotify ({e!r}) ...")
                gemeldet = True
        time.sleep(5)


def main():
    leser = RC522()
    log(f"RC522 Version 0x{leser.version():02X}.")
    auto = automatik.Automatik(spotify, lautstaerke, einstellungen, log=log)
    auto.beim_start()                           # Startlautstärke, bevor irgendetwas spielt
    status_schreiben()
    dev = warte_auf_geraet()
    ZUSTAND["spotify_bereit"] = True
    log("Bereit. Karte auflegen.")
    aktuell, zuletzt, letzte_sicht = None, None, 0.0
    while True:
        beginn = time.time()
        try:
            leser.antenne(True)
            aktuell, zuletzt, letzte_sicht, dev = schritt(leser, aktuell, zuletzt, letzte_sicht, dev, auto)
        except Exception as e:                  # Netz- oder Spotify-Fehler: melden, weiterlaufen
            log(f"Fehler: {e!r} – laufe weiter")
        finally:
            leser.antenne(False)                # Funkfeld zwischen den Abfragen aus
        try:
            auto.tick(dev)
        except Exception as e:                  # die Automatik darf die Kartenabfrage nie lahmlegen
            log(f"Automatik-Fehler: {e!r} – laufe weiter")
        ZUSTAND.update(auto.status)
        ZUSTAND["karte"] = aktuell
        status_schreiben()
        time.sleep(max(0.05, ABFRAGE - (time.time() - beginn)))


def link_lesen(leser):
    """Link von der aufgelegten Karte, mit ein paar Versuchen (Lesen kann mal haken)."""
    for _ in range(5):
        karte = leser.read_card()
        if karte and karte[1]:
            return karte[1]
        time.sleep(0.05)
    return None


def schritt(leser, aktuell, zuletzt, letzte_sicht, dev, auto):
    """Ein Durchlauf: Karte lesen und bei Wechsel Spotify steuern. Gibt den neuen Zustand zurueck."""
    uid = leser.read_uid()
    jetzt = time.time()
    if uid:
        letzte_sicht = jetzt
        if uid != aktuell:
            vorher = aktuell
            aktuell = uid
            link = link_lesen(leser)
            ZUSTAND["link"] = link
            uri = None
            if not link:
                log(f"Karte {uid}: kein Link gefunden. Mit NFC Tools eine Spotify-URL auf die Karte schreiben.")
            else:
                try:
                    uri = spotify.link_zu_uri(link)
                except ValueError:
                    log(f"Karte {uid}: Link ist kein Spotify-Link: {link}")
            if uri and auto.sperrt():
                log(f"Karte {uid}: Ruhezeit, es wird nicht abgespielt.")
                uri = None
            if uri:
                dev = spotify.geraet_id(GERAET) or dev
                if uid == zuletzt:
                    status, data = spotify.fortsetzen(dev)
                    log(f"Weiter: {uri} (Spotify {status})")
                else:
                    status, data = spotify.abspielen(dev, uri)
                    log(f"Spiele: {uri} (Spotify {status})")
                if status >= 300:
                    log(f"  Fehler: {data}")
                zuletzt = uid
            elif vorher and vorher == zuletzt:      # Karte ohne Link ersetzt eine spielende Karte
                status, _ = spotify.pause(dev)
                log(f"Pause (Spotify {status})")
    elif aktuell and jetzt - letzte_sicht > WEG_NACH:
        if aktuell == zuletzt:
            status, _ = spotify.pause(dev)
            log(f"Karte weg, Pause (Spotify {status})")
        aktuell = None
        ZUSTAND["link"] = None
    return aktuell, zuletzt, letzte_sicht, dev


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
