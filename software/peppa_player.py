#!/usr/bin/env python3
"""Peppa Box – Grundfunktion: Karte auflegen = Playlist spielt, Karte weg = Pause,
dieselbe Karte wieder auflegen = weiter, andere Karte = neue Playlist.
Start: python3 ~/peppa-box/software/peppa_player.py      Beenden: Strg+C
"""
import sys
import time

import karten
import spotify
from rc522 import RC522

GERAET = "Peppa Box"          # Name in /etc/raspotify/conf (LIBRESPOT_NAME)
WEG_NACH = 1.0                # Sekunden ohne Karte, bis "entfernt" gilt


def log(text):
    print(time.strftime("%H:%M:%S"), text, flush=True)


def main():
    leser = RC522()
    log(f"RC522 Version 0x{leser.version():02X}. Suche Spotify-Geraet '{GERAET}' ...")
    dev = spotify.geraet_id(GERAET)
    if not dev:
        namen = ", ".join(d["name"] for d in spotify.geraete()) or "keine"
        log(f"'{GERAET}' nicht gefunden (gefunden: {namen}). In der Spotify-App einmal die Peppa Box auswaehlen.")
        sys.exit(1)
    log("Bereit. Karte auflegen.")
    aktuell, zuletzt, letzte_sicht = None, None, 0.0
    while True:
        try:
            aktuell, zuletzt, letzte_sicht, dev = schritt(leser, aktuell, zuletzt, letzte_sicht, dev)
        except Exception as e:                  # Netz- oder Spotify-Fehler: melden, weiterlaufen
            log(f"Fehler: {e!r} – laufe weiter")
            time.sleep(1)
        time.sleep(0.1)


def schritt(leser, aktuell, zuletzt, letzte_sicht, dev):
    """Ein Durchlauf: Karte lesen und bei Wechsel Spotify steuern. Gibt den neuen Zustand zurueck."""
    uid = leser.read_uid()
    jetzt = time.time()
    if uid:
        letzte_sicht = jetzt
        if uid != aktuell:
            aktuell = uid
            eintrag = karten.laden().get(uid)
            if not eintrag:
                log(f"Unbekannte Karte {uid}. Zuordnen mit: python3 ~/peppa-box/software/karte_zuordnen.py")
            else:
                dev = spotify.geraet_id(GERAET) or dev
                name = eintrag.get("name") or eintrag["uri"]
                if uid == zuletzt:
                    status, data = spotify.fortsetzen(dev)
                    log(f"Weiter: {name} (Spotify {status})")
                else:
                    status, data = spotify.abspielen(dev, eintrag["uri"])
                    log(f"Spiele: {name} (Spotify {status})")
                if status >= 300:
                    log(f"  Fehler: {data}")
                zuletzt = uid
    elif aktuell and jetzt - letzte_sicht > WEG_NACH:
        if karten.laden().get(aktuell):
            status, _ = spotify.pause(dev)
            log(f"Karte weg, Pause (Spotify {status})")
        aktuell = None
    return aktuell, zuletzt, letzte_sicht, dev


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
