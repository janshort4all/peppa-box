#!/usr/bin/python3 -IS
"""Peppa Box: Tonausgabe für Raspotify (librespot mit --backend subprocess).

librespot startet dieses Programm, sobald Musik spielt, schreibt den Ton (S16_LE, 44,1 kHz, Stereo)
auf seine Standardeingabe und beendet es bei Pause. Das Programm reicht den Ton an aplay weiter,
und zwar an den Ausgang, den der Player vorgibt (/dev/shm/peppa-box-ausgang.json, „lautsprecher“
oder „kopfhoerer“). Ändert der Player die Vorgabe, wechselt es den Ausgang sofort, ohne dass
Spotify etwas davon merkt. Vorher (bis 09.11.2026) wurde dafür Raspotify neu gestartet; danach war
die Box für Spotify oft nicht erreichbar (502 „Bad gateway“).

Fehler werden hier abgefangen:
  Kopfhörer-Ausgang geht nicht (aplay endet)  -> sofort zurück auf den Lautsprecher, Kopfhörer für
                                                 diesen Lauf gesperrt, Meldung an den Player
  Lautsprecher-Ausgang endet                   -> neu öffnen; dreimal in 10 s -> Ende mit Fehler
                                                 (librespot startet das Programm dann einmal neu)
  aplay nimmt 3 s lang nichts an (hängt)       -> aplay beenden und neu öffnen wie oben

Rückmeldung an den Player per UDP an 127.0.0.1:47150 (JSON, "q": "ausgabe"): start, fluss (jede
Sekunde, solange Ton fließt: lokaler Beleg, dass wirklich Musik läuft), wechsel, fehler, haengt, ende.
Fehlertexte von aplay landen im Protokoll von Raspotify (journalctl -u raspotify).

Installiert als root-eigene Kopie /usr/local/lib/peppa-box/ausgabe (dienst_einrichten.sh); läuft
unter Raspotify (ohne Zugriff auf /home). Nur Standardbibliothek. Umgebungsvariablen PEPPA_* nur
für Tests.
"""
import json
import os
import select
import socket
import subprocess
import sys
import threading
import time

WAHL = os.environ.get("PEPPA_AUSGABE_WAHL") or "/dev/shm/peppa-box-ausgang.json"
APLAY = os.environ.get("PEPPA_AUSGABE_APLAY") or "/usr/bin/aplay"
PORT = int(os.environ.get("PEPPA_RUECKMELDUNG_PORT") or 47150)
AUSGAENGE = ("lautsprecher", "kopfhoerer")
RUECKFALL = "lautsprecher"
FORMAT = ["-t", "raw", "-f", "S16_LE", "-r", "44100", "-c", "2"]
PRUEF_S = 0.25            # so oft nach der Vorgabe des Players sehen
MELDEN_S = 1.0            # so oft den Fluss melden
HAENGT_S = 3.0            # aplay nimmt so lange nichts an -> neu öffnen
STUECK = 16384
PIPE_GROESSE = 16384      # kleiner Puffer zu aplay: Wechsel und Pause wirken schnell (ca. 0,1 s)
FEHLER_GRENZE = 3
FEHLER_FENSTER_S = 10.0


def log(text):
    try:
        print(f"peppa-ausgabe: {text}", file=sys.stderr, flush=True)
    except OSError:
        pass


class Melder:
    def __init__(self, port=PORT):
        self.adresse = ("127.0.0.1", port)
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except OSError:
            self.sock = None

    def __call__(self, art, **daten):
        if self.sock is None:
            return
        try:
            nachricht = {"q": "ausgabe", "art": art, "pid": os.getpid(), **daten}
            self.sock.sendto(json.dumps(nachricht).encode(), self.adresse)
        except (OSError, ValueError):
            pass


def wahl_lesen(pfad=WAHL):
    try:
        with open(pfad, encoding="utf-8") as f:
            ziel = json.load(f).get("ausgang")
    except (OSError, ValueError, AttributeError):
        return RUECKFALL
    return ziel if ziel in AUSGAENGE else RUECKFALL


class Relais:
    def __init__(self, wahl=WAHL, aplay=APLAY, melden=None, jetzt=time.monotonic, schlaf=time.sleep):
        self.wahl, self.aplay = wahl, aplay
        self.melden = melden or Melder()
        self.jetzt, self.schlaf = jetzt, schlaf
        self.ziel = None
        self.proc = None
        self.gesperrt = set()           # Ausgänge, die in diesem Lauf versagt haben
        self.fehlstarts = []
        self.schreibt_seit = None
        self._wahl_stand = None
        self._sperre = threading.Lock()

    # ------------------------------------------------------------ Vorgabe des Players

    def _gewuenscht(self):
        ziel = wahl_lesen(self.wahl)
        return RUECKFALL if ziel in self.gesperrt else ziel

    def _wahl_geaendert(self):
        try:
            st = os.stat(self.wahl)
            stand = (st.st_ino, st.st_mtime_ns, st.st_size)
        except OSError:
            stand = None
        if stand == self._wahl_stand:
            return False
        self._wahl_stand = stand
        return True

    def wahl_pruefen(self):
        if not self._wahl_geaendert():
            return
        neu = self._gewuenscht()
        if neu != self.ziel:
            log(f"Ausgang {self.ziel} -> {neu}")
            self.melden("wechsel", von=self.ziel, nach=neu)
            self._beenden()
            self._starten(neu)

    # ------------------------------------------------------------ aplay

    def _starten(self, ziel):
        befehl = [self.aplay, "-q", "-D", ziel, *FORMAT]
        try:
            p = subprocess.Popen(befehl, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, bufsize=0,
                                 close_fds=True)
        except OSError as e:
            self.ziel, self.proc = ziel, None
            self.melden("fehler", ziel=ziel, text=f"aplay startet nicht: {e}", rueckfall=None)
            raise
        try:
            import fcntl
            fcntl.fcntl(p.stdin.fileno(), getattr(fcntl, "F_SETPIPE_SZ", 1031), PIPE_GROESSE)
        except (OSError, ImportError, ValueError):
            pass
        with self._sperre:
            self.proc, self.ziel = p, ziel

    def _beenden(self, sanft=False):
        with self._sperre:
            p, self.proc = self.proc, None
        if p is None:
            return None
        try:
            p.stdin.close()
        except OSError:
            pass
        if not sanft:
            try:
                p.kill()
            except OSError:
                pass
        try:
            return p.wait(timeout=2 if sanft else 1)
        except subprocess.TimeoutExpired:
            try:
                p.kill()
                return p.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                return None

    def _fehlstart(self, grund=None):
        p = self.proc
        code = p.poll() if p else None
        self._beenden()
        t = self.jetzt()
        self.fehlstarts = [x for x in self.fehlstarts if t - x < FEHLER_FENSTER_S] + [t]
        text = grund or f"aplay auf '{self.ziel}' beendet (Code {code})"
        if self.ziel != RUECKFALL:
            self.gesperrt.add(self.ziel)
            log(f"{text} – zurück auf {RUECKFALL}")
            self.melden("fehler", ziel=self.ziel, text=text, rueckfall=RUECKFALL)
            self.ziel = RUECKFALL
            return
        log(text)
        self.melden("fehler", ziel=self.ziel, text=text, rueckfall=None)
        if len(self.fehlstarts) >= FEHLER_GRENZE:
            raise SystemExit(f"{RUECKFALL}: {FEHLER_GRENZE} Fehlstarts in {FEHLER_FENSTER_S:.0f} s")
        self.schlaf(0.3)

    def pruefen_lebt(self):
        if self.proc is not None and self.proc.poll() is not None:
            self._fehlstart()

    def schreiben(self, daten):
        rest = memoryview(daten)
        while rest:
            if self.proc is None:
                self._starten(self.ziel or self._gewuenscht())
            p = self.proc
            try:
                self.schreibt_seit = self.jetzt()
                n = p.stdin.write(rest)
            except (BrokenPipeError, ValueError, OSError):
                self.schreibt_seit = None
                self._fehlstart()
                continue
            self.schreibt_seit = None
            rest = rest[n or 0:]

    # ------------------------------------------------------------ Wächter gegen hängendes aplay

    def waechter(self, ende):
        while not ende.wait(0.5):
            seit = self.schreibt_seit
            if seit is not None and self.jetzt() - seit > HAENGT_S:
                with self._sperre:
                    p = self.proc
                if p is not None:
                    log(f"aplay auf '{self.ziel}' nimmt seit {HAENGT_S:.0f} s nichts an – neu öffnen")
                    self.melden("haengt", ziel=self.ziel)
                    try:
                        p.kill()
                    except OSError:
                        pass
                    self.schreibt_seit = None


def main(eingabe=None):
    fd = sys.stdin.fileno() if eingabe is None else eingabe
    melden = Melder()
    r = Relais(melden=melden)
    r._wahl_geaendert()
    r._starten(r._gewuenscht())
    melden("start", ziel=r.ziel)
    ende = threading.Event()
    threading.Thread(target=r.waechter, args=(ende,), daemon=True).start()
    menge, letzte = 0, time.monotonic()
    naechste_wahl = naechste_meldung = letzte
    try:
        while True:
            bereit, _, _ = select.select([fd], [], [], PRUEF_S)
            if bereit:
                daten = os.read(fd, STUECK)
                if not daten:
                    break
                r.schreiben(daten)
                menge += len(daten)
            t = time.monotonic()
            if t >= naechste_wahl:
                naechste_wahl = t + PRUEF_S
                r.wahl_pruefen()
                r.pruefen_lebt()
            if t >= naechste_meldung:
                naechste_meldung = t + MELDEN_S
                if menge:
                    melden("fluss", ziel=r.ziel, bytes=menge, s=round(t - letzte, 2))
                menge, letzte = 0, t
    finally:
        ende.set()
        melden("ende", ziel=r.ziel)
        r._beenden(sanft=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
