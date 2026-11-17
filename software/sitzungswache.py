"""Wache über die Spotify-Verbindung von librespot (Befund 17.11.2026).

Was passiert war: Nach einem WLAN-Ausfall meldete librespot um 17:54:15 "Connection to server closed",
verband sich aber nicht neu und schickte auch kein Ereignis (kein session_disconnected). Die Box hielt
die Verbindung für gut. 25 min später wurde eine Karte aufgelegt: Spotify nahm den Startbefehl an,
die tote Verbindung brach sofort ab ("Spirc shut down unexpectedly", "Audio key response timeout"),
der Titel galt als nicht abspielbar.

Diese Wache liest deshalb das Protokoll von Raspotify mit (journalctl -f) und meldet solche Zeilen an
die Steuerung (Steuerung.verbindung_verloren). Die Steuerung entscheidet, was zu tun ist: im Leerlauf
Raspotify neu starten; liegt eine Karte, holt der Wächter die Musik mit einem Raspotify-Neustart zurück
(18:38: librespot bekam keine Schlüssel mehr, jeder Titel "nicht abspielbar", erneutes Anspielen allein
half nicht).

Nur lesen, nie schreiben; stirbt journalctl, startet die Wache es nach WIEDER_S neu.
"""
import shutil
import subprocess
import threading
import time

MUSTER = (
    "Connection to server closed",          # 17.11.2026 17:54:15: danach kein Neuaufbau
    "Spirc shut down unexpectedly",         # 15.11.2026 07:28 und 17.11.2026 18:19:54
    "Audio key response timeout",           # 17.11.2026 18:38: Titel für Titel nicht abspielbar
    "Websocket peer does not respond",      # 17.11.2026 19:04:21 in der Pause: danach war librespot tot
    "Websocket connection failed",
)
WIEDER_S = 5.0
JOURNALCTL = shutil.which("journalctl") or "/usr/bin/journalctl"


def passt(zeile):
    """Zeigt diese Protokollzeile von librespot eine verlorene Verbindung zu Spotify? (Text oder None)"""
    for m in MUSTER:
        if m in zeile:
            return m
    return None


class Sitzungswache:
    def __init__(self, melden, log=print, befehl=None, schlaf=time.sleep):
        self.melden, self.log, self.schlaf = melden, log, schlaf
        self.befehl = befehl or [JOURNALCTL, "-f", "-n", "0", "-o", "cat", "-u", "raspotify"]
        self._faden = None

    def zeile(self, text):
        m = passt(text)
        if m:
            try:
                self.melden(m)
            except Exception as e:                  # die Wache darf nie sterben
                self.log(f"Sitzungswache: Meldung fehlgeschlagen: {e!r}")
        return m

    def _einmal(self):
        p = subprocess.Popen(self.befehl, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                             errors="replace")
        try:
            for z in p.stdout:
                self.zeile(z)
        finally:
            try:
                p.kill()
            except OSError:
                pass
            p.wait()
            p.stdout.close()

    def _lauf(self):
        while True:
            try:
                self._einmal()
            except Exception as e:
                self.log(f"Sitzungswache: Protokoll nicht lesbar ({e!r}), neuer Versuch in {WIEDER_S:.0f} s.")
            self.schlaf(WIEDER_S)

    def starten(self):
        self._faden = threading.Thread(target=self._lauf, name="sitzungswache", daemon=True)
        self._faden.start()
        return self._faden

    def lebt(self):
        return self._faden is not None and self._faden.is_alive()
