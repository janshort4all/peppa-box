#!/usr/bin/python3 -IS
"""Peppa Box: Ereignis-Programm für Raspotify (librespot --onevent).

librespot ruft das Programm bei jedem Ereignis auf (playing, paused, track_changed, stopped,
unavailable, session_connected, …) und übergibt die Angaben in Umgebungsvariablen. Es schickt sie
als JSON ("q": "ereignis") per UDP an den Player (127.0.0.1:47150) und endet sofort. Damit weiß der
Player aus erster Hand, was librespot gerade tut, statt sich nur auf die Spotify-Web-API zu
verlassen (die meldete am 08.11.2026 bei hörbarer Musik „Pause“).

Installiert als root-eigene Kopie /usr/local/lib/peppa-box/ereignis (dienst_einrichten.sh).
Endet immer mit 0 (librespot soll nie warten oder warnen müssen). Nur Standardbibliothek.
"""
import json
import os
import socket

PORT = int(os.environ.get("PEPPA_RUECKMELDUNG_PORT") or 47150)
FELDER = ("PLAYER_EVENT", "TRACK_ID", "URI", "POSITION_MS", "DURATION_MS", "CONNECTION_ID",
          "SINK_STATUS", "PLAY_REQUEST_ID")


def nachricht(umgebung):
    d = {"q": "ereignis"}
    for name in FELDER:
        wert = umgebung.get(name)
        if wert is not None:
            d[name.lower()] = str(wert)[:200]
    return d


def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(nachricht(os.environ)).encode(), ("127.0.0.1", PORT))
    except (OSError, ValueError):
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
