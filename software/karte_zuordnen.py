#!/usr/bin/env python3
"""Karte anlernen: Karte auflegen, Spotify-Link einfuegen, fertig.
Start: python3 ~/peppa-box/software/karte_zuordnen.py      Beenden: Strg+C
Den Link bekommst du in der Spotify-App: Playlist -> ... -> Teilen -> Link kopieren.
Laeuft der Dienst peppa-player, vorher stoppen (sudo systemctl stop peppa-player) – oder einfach die Einstellungsseite nutzen.
"""
import time

import karten
import spotify
from rc522 import RC522


def warte_auf_karte(leser):
    print("\nKarte auf den Leser legen ...")
    while True:
        uid = leser.read_uid()
        if uid:
            return uid
        time.sleep(0.1)


def main():
    leser = RC522()
    print(f"RC522 Version 0x{leser.version():02X}")
    while True:
        uid = warte_auf_karte(leser)
        alle = karten.laden()
        if uid in alle:
            print(f"Karte {uid} ist schon zugeordnet: {alle[uid].get('name') or alle[uid]['uri']}")
        else:
            print(f"Karte {uid} erkannt.")
        link = input("Spotify-Link einfuegen (leer = ueberspringen): ").strip()
        if link:
            try:
                uri = spotify.link_zu_uri(link)
            except ValueError as e:
                print(e)
                continue
            name = input("Name fuer die Karte (z. B. 'Peppa Folge 1'): ").strip()
            alle[uid] = {"uri": uri, "name": name}
            karten.speichern(alle)
            print(f"Gespeichert: {uid} -> {name or uri}")
        print("Karte wegnehmen.")
        while leser.read_uid() == uid:
            time.sleep(0.3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
