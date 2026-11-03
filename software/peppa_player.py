#!/usr/bin/env python3
"""Peppa Box – Grundfunktion: Karte auflegen = Spotify-Link auf der Karte spielt, Karte weg = Pause,
dieselbe Karte wieder auflegen = weiter, andere Karte = neue Playlist.
Den Link schreibt man mit einer Handy-App (z. B. NFC Tools: Schreiben -> URL) auf die Karte.
Zustand (Karte, Link, Spotify bereit, Ausgang, Ruhezeit, Auto-Aus) schreibt der Player nach
/dev/shm/peppa-box-status.json; die Eltern-Seite (Dienst peppa-web, peppa_web.py) zeigt ihn an.
Die Automatik (Schlummer-Timer, Ruhezeit, Auto-Aus, Lautstärke-Grenzen) steht in automatik.py.
Ansage „Peppa Box bereit – viel Spaß“, sobald Spotify die Box kennt und eine Karte Musik starten kann (toene.py).
Spotify steuert die Steuerung (steuerung.py) in einem eigenen Faden: Sie fasst schnelle
Kartenwechsel zusammen, prüft nach jedem Start, ob wirklich Musik läuft, und repariert Fehler selbst
(Gerät neu suchen, Raspotify neu starten, nach Absturz weiterspielen). Der Kartenleser wartet nie auf
das Netz. Liest der Leser wiederholt fehlerhaft, wird er neu eingerichtet. Läuft der Dienst mit
systemd-Watchdog, meldet sich die Schleife jede Sekunde; hängt sie, startet systemd den Player neu.
Start von Hand: python3 ~/peppa-box/software/peppa_player.py   (laeuft sonst als Dienst peppa-player)
"""
import json
import os
import socket
import time

import automatik
import einstellungen
import lautstaerke
import spotify
import toene
from rc522 import RC522
from steuerung import Steuerung

GERAET = "Peppa Box"          # Name in /etc/raspotify/conf (LIBRESPOT_NAME)
ABFRAGE = 1.0                 # Sekunden zwischen zwei Abfragen des Lesers
WEG_NACH = 1.5                # Sekunden ohne Karte, bis "entfernt" gilt (= zwei verpasste Abfragen)
LESER_NEU_NACH = 5            # so viele Lesefehler in Folge -> Leser neu einrichten
STATUS_DATEI = einstellungen.lauf_pfad("status")    # im Arbeitsspeicher, schont die SD-Karte
ZUSTAND = {"karte": None, "link": None, "spotify_bereit": False, "problem": None}


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


def systemd_melden(text):
    """sd_notify ohne Zusatzpaket (READY=1, WATCHDOG=1). Ohne systemd-Watchdog wirkungslos."""
    adresse = os.environ.get("NOTIFY_SOCKET")
    if not adresse:
        return
    if adresse.startswith("@"):
        adresse = "\0" + adresse[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
            s.connect(adresse)
            s.sendall(text.encode())
    except OSError:
        pass


class SpotifyFuerAutomatik:
    """Automatik (Timer, Ruhezeit) pausiert über diese Hülle: Die Steuerung weiß dann, dass die Pause
    gewollt ist, und „repariert“ sie nicht. Ohne bekanntes Gerät wird nichts pausiert (sonst träfe
    die Pause womöglich das Handy der Eltern)."""

    def __init__(self, st):
        self.st = st

    def spielt(self, dev):
        return spotify.spielt(dev) if dev else False

    def pause(self, dev):
        self.st.extern_pausiert()
        if not dev:
            return 404, None
        return spotify.pause(dev)


def leser_einrichten():
    leser = RC522()
    version = leser.version()
    log(f"RC522 Version 0x{version:02X}.")
    return leser


def main():
    leser = leser_einrichten()
    st = Steuerung(spotify, geraet=GERAET, log=log)
    auto = automatik.Automatik(SpotifyFuerAutomatik(st), lautstaerke, einstellungen, log=log)

    def bereit():                               # Ansage, einmal je Einschalten (nicht in der Ruhezeit "keine Musik")
        if not auto.sperrt():
            toene.einmal_je_einschalten("bereit", log=log)
    st.bei_bereit = bereit

    auto.beim_start()                           # Startlautstärke, bevor irgendetwas spielt
    status_schreiben()
    st.starten()
    systemd_melden("READY=1")
    log("Warte auf Spotify, Karten werden schon gelesen.")
    aktuell, letzte_sicht, lesefehler = None, 0.0, 0
    while True:
        beginn = time.time()
        try:
            leser.antenne(True)
            aktuell, letzte_sicht = schritt(leser, aktuell, letzte_sicht, auto, st)
            lesefehler = 0
        except Exception as e:                  # Lesefehler: melden, weiterlaufen
            lesefehler += 1
            log(f"Lesefehler: {e!r} – laufe weiter")
        finally:
            try:
                leser.antenne(False)            # Funkfeld zwischen den Abfragen aus
            except Exception:
                pass
        if lesefehler >= LESER_NEU_NACH:
            lesefehler = 0
            try:
                leser.close()
            except Exception:
                pass
            try:
                leser = leser_einrichten()
                log("Kartenleser neu eingerichtet.")
            except Exception as e:
                log(f"Kartenleser lässt sich nicht einrichten: {e!r}")
        if not st.lebt():                       # Steuerung darf nie fehlen
            log("Spotify-Steuerung lief nicht mehr, neu gestartet.")
            st.starten()
        try:
            auto.tick(st.dev)
        except Exception as e:                  # die Automatik darf die Kartenabfrage nie lahmlegen
            log(f"Automatik-Fehler: {e!r} – laufe weiter")
        ZUSTAND.update(auto.status)
        ZUSTAND.update(st.status)
        ZUSTAND["karte"] = aktuell
        status_schreiben()
        systemd_melden("WATCHDOG=1")
        time.sleep(max(0.05, ABFRAGE - (time.time() - beginn)))


def link_lesen(leser):
    """Link von der aufgelegten Karte, mit ein paar Versuchen (Lesen kann mal haken)."""
    for _ in range(5):
        karte = leser.read_card()
        if karte and karte[1]:
            return karte[1]
        time.sleep(0.05)
    return None


def schritt(leser, aktuell, letzte_sicht, auto, st):
    """Ein Durchlauf: Karte lesen und bei Wechsel der Steuerung den Wunsch melden (wartet nie auf das Netz)."""
    uid = leser.read_uid()
    jetzt = time.time()
    if uid:
        letzte_sicht = jetzt
        if uid != aktuell:
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
                st.karte_auf(uri)
            else:
                st.karte_weg()                  # Karte ohne Link ersetzt eine spielende Karte
    elif aktuell and jetzt - letzte_sicht > WEG_NACH:
        st.karte_weg()
        aktuell = None
        ZUSTAND["link"] = None
    return aktuell, letzte_sicht


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
