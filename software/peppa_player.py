#!/usr/bin/env python3
"""Peppa Box – Grundfunktion: Karte auflegen = Spotify-Link auf der Karte spielt, Karte weg = Pause,
dieselbe Karte wieder auflegen = weiter, andere Karte = neue Playlist.
Den Link schreibt man mit einer Handy-App (z. B. NFC Tools: Schreiben -> URL) auf die Karte.
Statusseite: http://peppabox.local:8080
Start von Hand: python3 ~/peppa-box/software/peppa_player.py   (laeuft sonst als Dienst peppa-player)
"""
import socket
import time

import spotify
import webui
from rc522 import RC522

GERAET = "Peppa Box"          # Name in /etc/raspotify/conf (LIBRESPOT_NAME)
WEG_NACH = 1.0                # Sekunden ohne Karte, bis "entfernt" gilt
PORT = 8080


def log(text):
    print(time.strftime("%H:%M:%S"), text, flush=True)


def eigene_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 80))          # nur Routing-Abfrage, es wird nichts gesendet
            return s.getsockname()[0]
    except OSError:
        return "?"


def warte_auf_geraet():
    """Wartet, bis Raspotify bei Spotify angemeldet ist (nach dem Einschalten dauert das etwas)."""
    gemeldet = False
    while True:
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
    webui.starten(PORT)
    log(f"Statusseite: http://{socket.gethostname()}.local:{PORT}  oder  http://{eigene_ip()}:{PORT}")
    dev = warte_auf_geraet()
    log("Bereit. Karte auflegen.")
    aktuell, zuletzt, letzte_sicht = None, None, 0.0
    while True:
        try:
            aktuell, zuletzt, letzte_sicht, dev = schritt(leser, aktuell, zuletzt, letzte_sicht, dev)
        except Exception as e:                  # Netz- oder Spotify-Fehler: melden, weiterlaufen
            log(f"Fehler: {e!r} – laufe weiter")
            time.sleep(1)
        webui.ZUSTAND["karte"] = aktuell
        time.sleep(0.1)


def link_lesen(leser):
    """Link von der aufgelegten Karte, mit ein paar Versuchen (Lesen kann mal haken)."""
    for _ in range(5):
        karte = leser.read_card()
        if karte and karte[1]:
            return karte[1]
        time.sleep(0.05)
    return None


def schritt(leser, aktuell, zuletzt, letzte_sicht, dev):
    """Ein Durchlauf: Karte lesen und bei Wechsel Spotify steuern. Gibt den neuen Zustand zurueck."""
    uid = leser.read_uid()
    jetzt = time.time()
    if uid:
        letzte_sicht = jetzt
        if uid != aktuell:
            vorher = aktuell
            aktuell = uid
            link = link_lesen(leser)
            webui.ZUSTAND["link"] = link
            uri = None
            if not link:
                log(f"Karte {uid}: kein Link gefunden. Mit NFC Tools eine Spotify-URL auf die Karte schreiben.")
            else:
                try:
                    uri = spotify.link_zu_uri(link)
                except ValueError:
                    log(f"Karte {uid}: Link ist kein Spotify-Link: {link}")
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
        webui.ZUSTAND["link"] = None
    return aktuell, zuletzt, letzte_sicht, dev


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
