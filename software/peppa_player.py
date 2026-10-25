#!/usr/bin/env python3
"""Peppa Box – Grundfunktion: Karte auflegen = Playlist spielt, Karte weg = Pause,
dieselbe Karte wieder auflegen = weiter, andere Karte = neue Playlist.
Dazu die Einstellungsseite fuers Handy: http://peppabox.local:8080
Start von Hand: python3 ~/peppa-box/software/peppa_player.py   (laeuft sonst als Dienst peppa-player)
"""
import socket
import time

import karten
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
    log(f"Einstellungsseite: http://{socket.gethostname()}.local:{PORT}  oder  http://{eigene_ip()}:{PORT}")
    dev = warte_auf_geraet()
    log("Bereit. Karte auflegen.")
    aktuell, zuletzt, letzte_sicht = None, None, 0.0
    while True:
        if webui.NEU_LADEN.is_set():           # Karte wurde gerade auf der Webseite zugeordnet
            webui.NEU_LADEN.clear()
            aktuell, zuletzt = None, None
        try:
            aktuell, zuletzt, letzte_sicht, dev = schritt(leser, aktuell, zuletzt, letzte_sicht, dev)
        except Exception as e:                  # Netz- oder Spotify-Fehler: melden, weiterlaufen
            log(f"Fehler: {e!r} – laufe weiter")
            time.sleep(1)
        webui.ZUSTAND["karte"] = aktuell
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
                log(f"Unbekannte Karte {uid}. Zuordnen auf der Einstellungsseite.")
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
