#!/usr/bin/python3 -IS
"""Peppa Box: Tonausgabe für Raspotify (librespot mit --backend subprocess).

librespot startet dieses Programm, sobald Musik spielt, schreibt den Ton (S16_LE, 44,1 kHz, Stereo)
auf seine Standardeingabe und beendet es bei Pause. Das Programm reicht den Ton an aplay weiter,
und zwar an den Ausgang, den der Player vorgibt (/dev/shm/peppa-box-ausgang.json, „lautsprecher“
oder „kopfhoerer“). Ändert der Player die Vorgabe, wechselt es den Ausgang sofort, ohne dass
Spotify etwas davon merkt. Vorher (bis 09.11.2026) wurde dafür Raspotify neu gestartet; danach war
die Box für Spotify oft nicht erreichbar (502 „Bad gateway“).

Fehler werden hier abgefangen:
  Kopfhörer-Ausgang geht nicht (aplay endet)  -> zweimal nach 0,5 s neu versuchen (die Pi-Klinke hat
                                                 keinen Mischer, eine Ansage kann sie kurz belegen),
                                                 dann zurück auf den Lautsprecher, Kopfhörer für
                                                 diesen Lauf gesperrt, Meldung an den Player
  Lautsprecher-Ausgang endet                   -> neu öffnen; dreimal in 10 s -> Ende mit Fehler
                                                 (librespot startet das Programm dann einmal neu)
  aplay nimmt 3 s lang nichts an (hängt)       -> aplay beenden und neu öffnen wie oben

Rückmeldung an den Player per UDP an 127.0.0.1:47150 (JSON, "q": "ausgabe"): start, fluss (jede
Sekunde, solange Ton fließt: lokaler Beleg, dass wirklich Musik läuft), wechsel, fehler, haengt, ende.
Ansagen während der Musik (seit 09.11.2026): toene.py legt eine Ansage als Roh-Ton (S16_LE,
44,1 kHz, Stereo) nach /dev/shm/peppa-box-ansage.raw und einen Auftrag nach
/dev/shm/peppa-box-ansage.json. Dieses Programm mischt sie in den Musikstrom und senkt die Musik
dabei weich ab („Ducking“): S-Kurve in dB auf −12 dB in 0,35 s, die Ansage beginnt nach 0,3 s,
nach der Ansage 0,4 s halten, dann in 1,2 s zurück. So hört man die Ansage auf Lautsprecher und
Kopfhörern gleich, und die Pi-Klinke (ohne Mischer) wird nicht doppelt belegt. Quittung und
Lebenszeichen in /dev/shm/peppa-box-ausgabe.json; ohne Quittung spielt toene.py wie bisher selbst.

Fehlertexte von aplay landen im Protokoll von Raspotify (journalctl -u raspotify).

Installiert als root-eigene Kopie /usr/local/lib/peppa-box/ausgabe (dienst_einrichten.sh); läuft
unter Raspotify (ohne Zugriff auf /home). Nur Standardbibliothek. Umgebungsvariablen PEPPA_* nur
für Tests.
"""
import array
import json
import math
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
BELEGT_VERSUCHE = 3       # Kopfhörer ohne Mischer: kurz belegt (z. B. Ansage) -> so oft neu versuchen
BELEGT_PAUSE_S = 0.5

AUFTRAG = os.environ.get("PEPPA_ANSAGE_AUFTRAG") or "/dev/shm/peppa-box-ansage.json"
STATUS = os.environ.get("PEPPA_AUSGABE_STATUS") or "/dev/shm/peppa-box-ausgabe.json"
RATE = 44100
DUCK_DB = -12.0           # Musik während der Ansage (−12 dB ≈ ein Viertel)
AB_S = 0.35               # weich absenken
VORLAUF_S = 0.30          # Ansage beginnt, wenn die Musik schon fast unten ist
HALTEN_S = 0.40           # nach der Ansage noch leise bleiben
AUF_S = 1.20              # langsam zurück
BLOCK = 512               # Verstärkung je 512 Frames (12 ms) als Stützstelle, dazwischen linear – glatt und sparsam


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
        if self.ziel != RUECKFALL and grund is None and code != -9 and len([x for x in self.fehlstarts if t - x < 3]) < BELEGT_VERSUCHE:
            log(f"{text} – neuer Versuch")              # Pi-Klinke ohne Mischer: evtl. gerade belegt
            self.schlaf(BELEGT_PAUSE_S)
            return
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


def _s_kurve(x):
    return 0.5 - 0.5 * math.cos(math.pi * x)


class Mischer:
    """Mischt Ansagen in den Musikstrom und senkt die Musik dabei weich ab (siehe oben)."""

    def __init__(self, auftrag=AUFTRAG, status=STATUS, uhr=time.time):
        self.auftrag, self.status, self.uhr = auftrag, status, uhr
        self.tiefe = 0.0                 # 0 = volle Musik, 1 = ganz abgesenkt
        self.ansage = None               # array('h') Stereo
        self.pos = 0
        self.vorlauf = 0                 # Frames bis zum Beginn der Ansage
        self.halten = 0                  # Frames nach der Ansage
        self.rest = b""
        self.quittung = None
        self._stand = None
        self._status_fehler = False

    def status_schreiben(self):
        try:
            tmp = self.status + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"pid": os.getpid(), "t": self.uhr(), "quittung": self.quittung}, f)
            os.replace(tmp, self.status)
            self._status_fehler = False
        except OSError as e:
            if not self._status_fehler:
                log(f"Status nicht schreibbar ({e}) – Ansagen spielen dann ohne Absenken")
            self._status_fehler = True

    def status_entfernen(self):
        try:
            os.remove(self.status)
        except OSError:
            pass

    def auftrag_pruefen(self):
        """Neuen Auftrag übernehmen. True, wenn sich etwas geändert hat (dann Quittung schreiben)."""
        try:
            st = os.stat(self.auftrag)
            stand = (st.st_ino, st.st_mtime_ns, st.st_size)
        except OSError:
            return False
        if stand == self._stand:
            return False
        self._stand = stand
        try:
            with open(self.auftrag, encoding="utf-8") as f:
                a = json.load(f)
            kennung = a.get("id")
        except (OSError, ValueError, AttributeError):
            return False
        if not kennung or kennung == self.quittung or self.uhr() > float(a.get("bis") or 0):
            return False                 # alt oder abgelaufen: toene.py spielt dann selbst
        werte = None
        if a.get("pcm"):
            try:
                with open(a["pcm"], "rb") as f:
                    roh = f.read()
                werte = array.array("h")
                werte.frombytes(roh[:len(roh) // 4 * 4])
                if sys.byteorder == "big":
                    werte.byteswap()
            except OSError as e:
                log(f"Ansage nicht lesbar: {e}")
                return False
        if werte:
            if self.ansage is None:      # neue Ansage: erst absenken; folgt sie direkt einer anderen, sofort
                self.vorlauf = int(VORLAUF_S * RATE * (1.0 - self.tiefe))
            self.ansage, self.pos, self.halten = werte, 0, 0
        else:                            # Stopp
            if self.ansage is not None:
                self.halten = int(HALTEN_S * RATE)
            self.ansage = None
        self.quittung = kennung
        return True

    def _gain(self):
        return 10 ** (DUCK_DB * _s_kurve(self.tiefe) / 20)

    def verarbeiten(self, daten):
        daten = self.rest + daten
        n = len(daten) // 4 * 4
        self.rest, daten = daten[n:], daten[:n]
        if self.ansage is None and self.halten <= 0 and self.tiefe <= 0.0:
            return daten                 # nichts zu tun: Musik unverändert durchreichen
        werte = array.array("h")
        werte.frombytes(daten)
        if sys.byteorder == "big":
            werte.byteswap()
        frames = len(werte) // 2
        ab, auf = BLOCK / (AB_S * RATE), BLOCK / (AUF_S * RATE)
        i = 0
        while i < frames:
            m = min(BLOCK, frames - i)
            unten = self.ansage is not None or self.halten > 0
            g0 = self._gain()
            self.tiefe = min(1.0, self.tiefe + ab) if unten else max(0.0, self.tiefe - auf)
            g1 = self._gain()
            j0, j1 = 2 * i, 2 * (i + m)
            if g0 == g1:
                musik = [v * g0 for v in werte[j0:j1]]
            else:
                d = (g1 - g0) / m
                musik = [v * (g0 + d * (k >> 1)) for k, v in enumerate(werte[j0:j1])]
            # Ansage: zuerst Vorlauf (Musik senkt sich), dann dazumischen
            a, pos, frei = self.ansage, self.pos, 0
            if a is not None:
                frei = min(self.vorlauf, m)
                self.vorlauf -= frei
                n = min(m - frei, (len(a) - pos) // 2)
                if n > 0:
                    o = 2 * frei
                    musik[o:o + 2 * n] = [x + y for x, y in zip(musik[o:o + 2 * n], a[pos:pos + 2 * n])]
                    pos += 2 * n
                if pos >= len(a) and frei < m:
                    self.ansage = None
                    self.halten = int(HALTEN_S * RATE) - (m - frei - max(n, 0))
            elif self.halten > 0:
                self.halten -= m
            werte[j0:j1] = array.array("h", [-32768 if x < -32768 else 32767 if x > 32767 else int(x)
                                             for x in musik])
            self.pos = pos
            i += m
        if sys.byteorder == "big":
            werte.byteswap()
        return werte.tobytes()


def main(eingabe=None):
    fd = sys.stdin.fileno() if eingabe is None else eingabe
    melden = Melder()
    r = Relais(melden=melden)
    mix = Mischer()
    mix.auftrag_pruefen()                # gerade gestellter Auftrag (alte sind abgelaufen)
    mix.status_schreiben()
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
                menge += len(daten)
                daten = mix.verarbeiten(daten)
                if daten:
                    r.schreiben(daten)
            t = time.monotonic()
            if t >= naechste_wahl:
                naechste_wahl = t + PRUEF_S
                r.wahl_pruefen()
                r.pruefen_lebt()
                if mix.auftrag_pruefen():
                    mix.status_schreiben()
            if t >= naechste_meldung:
                naechste_meldung = t + MELDEN_S
                if menge:
                    melden("fluss", ziel=r.ziel, bytes=menge, s=round(t - letzte, 2))
                menge, letzte = 0, t
                mix.status_schreiben()
    finally:
        mix.status_entfernen()
        ende.set()
        melden("ende", ziel=r.ziel)
        r._beenden(sanft=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
