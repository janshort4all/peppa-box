"""Rückmeldungen von Raspotify an den Player: Tonausgabe (ausgabe.py) und Ereignisse (ereignis.py).

Beide schicken kleine JSON-Nachrichten per UDP an 127.0.0.1:47150. Hier laufen sie in einem
eigenen Faden ein und werden zu einem Zustand zusammengefasst:
  fliesst()      kam in den letzten Sekunden Ton durch die Ausgabe? Das ist der sicherste lokale
                 Beleg, dass Musik wirklich spielt (die Web-API von Spotify irrt sich manchmal).
  ausgabe_ziel   auf welchen Ausgang die Ausgabe gerade spielt (lautsprecher/kopfhoerer)
  relais_aktiv() hat sich die Ausgabe seit dem Start überhaupt gemeldet? (sonst ist sie noch
                 nicht eingerichtet: Raspotify spielt dann wie früher direkt über ALSA)
  spielt         letztes Ereignis von librespot: True (playing), False (paused/stopped/…), None
Fehler der Ausgabe (Kopfhörer-Ausgang geht nicht) gibt es zusätzlich als Rückruf bei_fehler.

Uhr und Empfang sind austauschbar (Tests: verarbeiten() direkt aufrufen).
"""
import json
import socket
import threading
import time

PORT = 47150
FLUSS_ALTER_S = 2.5
NEU_VERSUCH_S = 10.0


class Rueckmeldung:
    def __init__(self, port=PORT, jetzt=time.monotonic, log=print, bei_fehler=None):
        self.port, self.jetzt, self.log, self.bei_fehler = port, jetzt, log, bei_fehler
        self._sperre = threading.Lock()
        self.relais_zeit = None          # letzte Nachricht der Ausgabe
        self.fluss_zeit = None
        self.fluss_bytes = 0
        self.ausgabe_ziel = None
        self.ausgabe_pid = None
        self.fehler = []                 # letzte Fehler der Ausgabe (Klartext)
        self.ereignis = None             # (Name, Titel-ID, Zeit)
        self.ereignis_zeit = None
        self.spielt = None
        self.titel = None
        self.titel_uri = None            # spotify:track:… (aus track_changed)
        self.dauer_ms = None
        self._pos = None                 # (Position in ms, Zeit) aus playing/paused/seeked
        self.verbunden = None            # session_connected / session_disconnected
        self._faden = None
        self.empfang_ok = False

    # ------------------------------------------------------------ Empfang

    def starten(self):
        self._faden = threading.Thread(target=self._lauf, name="rueckmeldung", daemon=True)
        self._faden.start()
        return self._faden

    def lebt(self):
        return self._faden is not None and self._faden.is_alive()

    def _lauf(self):
        gemeldet = False
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(("127.0.0.1", self.port))
            except OSError as e:
                self.empfang_ok = False
                if not gemeldet:
                    self.log(f"Rückmeldung von Raspotify nicht möglich (Port {self.port}): {e!r}")
                    gemeldet = True
                time.sleep(NEU_VERSUCH_S)
                continue
            self.empfang_ok = True
            try:
                while True:
                    daten, _ = sock.recvfrom(4096)
                    try:
                        self.verarbeiten(json.loads(daten.decode("utf-8")))
                    except Exception as e:      # eine kaputte Nachricht darf nichts anhalten
                        self.log(f"Rückmeldung nicht verstanden: {e!r}")
            except OSError:
                self.empfang_ok = False
            finally:
                try:
                    sock.close()
                except OSError:
                    pass
            time.sleep(1)

    # ------------------------------------------------------------ Auswertung

    def verarbeiten(self, n):
        if not isinstance(n, dict):
            return
        t = self.jetzt()
        if n.get("q") == "ausgabe":
            self._ausgabe(n, t)
        elif n.get("q") == "ereignis":
            self._ereignis(n, t)

    def _ausgabe(self, n, t):
        art, ziel = n.get("art"), n.get("ziel")
        rueckruf = None
        with self._sperre:
            self.relais_zeit = t
            if ziel in ("lautsprecher", "kopfhoerer"):
                self.ausgabe_ziel = ziel
            self.ausgabe_pid = n.get("pid", self.ausgabe_pid)
            if art == "fluss" and int(n.get("bytes") or 0) > 0:
                self.fluss_zeit, self.fluss_bytes = t, int(n["bytes"])
            elif art in ("fehler", "haengt"):
                text = n.get("text") or ("aplay hängt" if art == "haengt" else "Fehler")
                self.fehler = (self.fehler + [f"{ziel}: {text}"])[-5:]
                if art == "fehler":
                    rueckruf = (ziel, text, n.get("rueckfall"))
            elif art == "wechsel":
                self.ausgabe_ziel = n.get("nach") or self.ausgabe_ziel
        if art == "fehler":
            self.log(f"Tonausgabe: {ziel} – {n.get('text')}"
                     + (f", weiter über {n['rueckfall']}" if n.get("rueckfall") else ""))
        elif art == "haengt":
            self.log(f"Tonausgabe: {ziel} nahm 3 s nichts an, neu geöffnet.")
        if rueckruf and self.bei_fehler:
            try:
                self.bei_fehler(*rueckruf)
            except Exception as e:
                self.log(f"Rückmeldung: Fehlerbehandlung gescheitert: {e!r}")

    def _ereignis(self, n, t):
        name = n.get("player_event")
        with self._sperre:
            self.ereignis, self.ereignis_zeit = (name, n.get("track_id")), t
            if name in ("playing",):
                self.spielt = True
            elif name in ("paused", "stopped", "end_of_track", "unavailable"):
                self.spielt = False
            if name in ("track_changed", "playing", "paused", "loading") and n.get("track_id"):
                if n.get("track_id") != self.titel:
                    self._pos = None
                self.titel = n.get("track_id")
            if name == "track_changed":
                self.titel_uri = n.get("uri") or self.titel_uri
                try:
                    self.dauer_ms = int(n.get("duration_ms"))
                except (TypeError, ValueError):
                    self.dauer_ms = None
                self._pos = (0, t)
            if n.get("position_ms") is not None:
                try:
                    self._pos = (int(n["position_ms"]), t)
                except (TypeError, ValueError):
                    pass
            if name == "session_connected":
                self.verbunden = True
            elif name == "session_disconnected":
                self.verbunden, self.spielt = False, False
        if name == "unavailable":
            self.log(f"Raspotify: Titel {n.get('track_id')} nicht abspielbar (wird übersprungen).")
        elif name == "session_disconnected":
            self.log("Raspotify: Verbindung zu Spotify getrennt.")
        elif name == "session_connected":
            self.log("Raspotify: mit Spotify verbunden.")

    # ------------------------------------------------------------ Abfragen

    def position(self):
        """Geschätzte Stelle im aktuellen Titel (ms) aus den Ereignissen, None wenn unbekannt."""
        with self._sperre:
            pos, spielt = self._pos, self.spielt
        if pos is None:
            return None
        ms = pos[0] + (int((self.jetzt() - pos[1]) * 1000) if spielt else 0)
        return min(ms, self.dauer_ms) if self.dauer_ms else ms

    def stelle(self):
        """(Titel-URI, Position) für fortschritt.py, wenn librespot gerade spielt; sonst None."""
        p = self.position()
        if not self.spielt or not self.titel_uri or p is None:
            return None
        return self.titel_uri, p

    def relais_aktiv(self):
        return self.relais_zeit is not None

    def fliesst(self, alter=FLUSS_ALTER_S):
        t = self.fluss_zeit
        return t is not None and self.jetzt() - t <= alter

    def lokal(self):
        """Für die Prüfung nach dem Start: True/False aus dem Tonfluss, None ohne Ausgabe-Relais."""
        if not self.relais_aktiv():
            return None
        return self.fliesst()

    @property
    def status(self):
        t = self.jetzt()
        with self._sperre:
            return {
                "empfang": self.empfang_ok,
                "relais": self.relais_zeit is not None,
                "fliesst": self.fluss_zeit is not None and t - self.fluss_zeit <= FLUSS_ALTER_S,
                "ausgabe": self.ausgabe_ziel,
                "fehler": list(self.fehler),
                "ereignis": self.ereignis[0] if self.ereignis else None,
                "ereignis_vor_s": round(t - self.ereignis_zeit, 1) if self.ereignis_zeit else None,
                "spielt": self.spielt,
                "verbunden": self.verbunden,
            }
