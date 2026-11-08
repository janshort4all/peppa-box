#!/usr/bin/env python3
"""Ansagen der Peppa Box. Nur Standardbibliothek.

Jede Ansage hat einen Namen und einen Text (ANSAGEN). Abgespielt wird, was vorhanden ist:
  1. eigene Aufnahme   software/ansagen/<name>.wav (z. B. ElevenLabs, Stimme „Helmut“, wie „bereit“)
  2. Sprachausgabe     pico2wave (Paket libttspico-utils), sonst espeak-ng; einmal erzeugt und in
                       ~/.cache/peppa-box/ansagen/ gespeichert (auf -3 dBFS angehoben wie „bereit“)
  3. Töne              kurze Tonfolge, wenn es gar keine Sprachausgabe gibt
So spricht die Box sofort, und jede Aufnahme, die später dazukommt, ersetzt die Sprachausgabe
ohne Programmänderung. Die Texte für die Aufnahmen stehen in software/ansagen/TEXTE.md.

Ausgabe über den gerade aktiven Ausgang (Lautsprecher oder Kopfhörer) in der dort eingestellten
Lautstärke. Fehler beim Abspielen werden gemeldet, halten aber nichts auf.

Ansager: eigener Faden für den Player. Eine neue Ansage beendet die laufende (zählt nur die
neueste, z. B. beim Weiterschalten des Schlummer-Timers). Der Aufrufer wartet nie.

Von Hand:  python3 ~/peppa-box/software/toene.py bereit        (eine Ansage)
           python3 ~/peppa-box/software/toene.py --alle        (alle nacheinander, mit Quelle)
"""
import array
import hashlib
import math
import os
import shutil
import subprocess
import sys
import threading
import time
import wave

import einstellungen
import lautstaerke

ORDNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ansagen")
CACHE = os.environ.get("PEPPA_CACHE_DIR", os.path.expanduser("~/.cache/peppa-box/ansagen"))
ASOUND = os.environ.get("PEPPA_ASOUND", "/etc/asound.conf")
SPITZE = 0.708                        # -3 dBFS, wie die Aufnahme „bereit“
STILLE_VORNE_S = 0.15

ANSAGEN = {
    "bereit": "Peppa Box bereit – viel Spaß!",
    "tschuess": "Tschüss, bis bald!",
    "karte_leer": "Auf dieser Karte ist noch keine Musik.",
    "karte_auflegen": "Leg eine Karte auf!",
    "ruhezeit": "Jetzt ist Ruhezeit. Gute Nacht!",
    "moment": "Einen Moment, die Musik kommt gleich.",
    "kein_internet": "Ich finde gerade kein Internet. Ich versuche es weiter.",
    "anmeldung": "Ich bin nicht bei Spotify angemeldet. Bitte frag Mama oder Papa.",
    "timer_15": "Schlummer-Timer: Die Musik geht in fünfzehn Minuten aus.",
    "timer_30": "Schlummer-Timer: Die Musik geht in dreißig Minuten aus.",
    "timer_45": "Schlummer-Timer: Die Musik geht in fünfundvierzig Minuten aus.",
    "timer_60": "Schlummer-Timer: Die Musik geht in einer Stunde aus.",
    "timer_aus": "Schlummer-Timer aus.",
    "akku_laedt": "Der Akku wird gerade geladen.",
    "akku_voll": "Der Akku ist voll.",
    "akku_schwach": "Mein Akku ist fast leer. Bitte bald aufladen!",
    "akku_leer": "Mein Akku ist leer. Ich schalte mich jetzt aus. Tschüss!",
    "akku_unbekannt": "Ich kann den Akku gerade nicht messen.",
}
ZAHLWORT = {10: "zehn", 20: "zwanzig", 30: "dreißig", 40: "vierzig", 50: "fünfzig", 60: "sechzig",
            70: "siebzig", 80: "achtzig", 90: "neunzig", 100: "hundert"}
for _p, _w in ZAHLWORT.items():
    ANSAGEN[f"akku_{_p}"] = f"Akku: {_w} Prozent."
DATEINAMEN = {"bereit": "peppa_box_bereit.wav"}          # ältere Aufnahme mit eigenem Namen

# Töne, falls es keine Sprachausgabe gibt: (Frequenz Hz, Dauer s); 0 Hz = Pause
TOENE = {
    "bereit": [(523, .12), (659, .12), (784, .2)],
    "tschuess": [(784, .15), (659, .15), (523, .3)],
    "akku_leer": [(392, .2), (330, .2), (262, .4)],
    "karte_leer": [(330, .15), (0, .08), (330, .15)],
    "timer_aus": [(523, .12), (392, .25)],
}


def datei(name):
    return os.path.join(ORDNER, DATEINAMEN.get(name, f"{name}.wav"))


def kopfhoerer_geraet():
    """ALSA-Gerät der Kopfhörer: der Mischer 'kopfhoerer' (lautsprecher_einrichten.sh), sonst direkt."""
    try:
        with open(ASOUND, encoding="utf-8", errors="replace") as f:
            if "pcm.kopfhoerer " in f.read():
                return "kopfhoerer"
    except OSError:
        pass
    return "plughw:CARD=Headphones,DEV=0"


def geraet():
    return "lautsprecher" if lautstaerke.aktive_ausgabe() == "lautsprecher" else kopfhoerer_geraet()


# ---------------------------------------------------------------- Quelle einer Ansage

def _cache_pfad(name, art):
    kennung = hashlib.sha1(f"{art}|{ANSAGEN.get(name, name)}".encode()).hexdigest()[:10]
    return os.path.join(CACHE, f"{name}-{art}-{kennung}.wav")


def _anheben(quelle, ziel):
    """WAV (mono/stereo, 16 Bit) auf SPITZE normalisieren, Stille vorne, nach `ziel` schreiben."""
    with wave.open(quelle) as w:
        kanaele, breite, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
        roh = w.readframes(w.getnframes())
    if breite != 2:
        raise ValueError("nur 16-Bit-WAV")
    werte = array.array("h", roh)
    if sys.byteorder == "big":
        werte.byteswap()
    spitze = max((abs(v) for v in werte), default=0)
    if spitze:
        faktor = SPITZE * 32767 / spitze
        werte = array.array("h", (max(-32768, min(32767, int(v * faktor))) for v in werte))
    stille = array.array("h", [0] * int(rate * STILLE_VORNE_S) * kanaele)
    werte = stille + werte
    if sys.byteorder == "big":
        werte.byteswap()
    tmp = ziel + ".tmp"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(kanaele)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(werte.tobytes())
    os.replace(tmp, ziel)


def _sprache(name, log):
    """Sprachausgabe erzeugen (pico2wave, sonst espeak-ng). Gibt den Pfad zurück oder None."""
    text = ANSAGEN.get(name)
    if not text:
        return None
    for art, exe, args in (("pico", "pico2wave", ["-l", "de-DE", "-w"]),
                           ("espeak", "espeak-ng", ["-v", "de", "-s", "150", "-w"])):
        pfad = shutil.which(exe)
        if not pfad:
            continue
        ziel = _cache_pfad(name, art)
        if os.path.isfile(ziel):
            return ziel
        try:
            os.makedirs(CACHE, exist_ok=True)
            roh = ziel[:-4] + "-roh.wav"                # pico2wave verlangt die Endung .wav
            nice = [shutil.which("nice"), "-n", "10"] if shutil.which("nice") else []
            r = subprocess.run(nice + [pfad, *args, roh, text], capture_output=True, text=True, timeout=30)
            if r.returncode != 0 or not os.path.isfile(roh):
                log(f"Sprachausgabe ({exe}) für '{name}' fehlgeschlagen: {r.stderr.strip()[:200]}")
                continue
            _anheben(roh, ziel)
            os.remove(roh)
            return ziel
        except (OSError, ValueError, wave.Error, subprocess.TimeoutExpired) as e:
            log(f"Sprachausgabe ({exe}) für '{name}' fehlgeschlagen: {e!r}")
    return None


def _ton(name):
    """Kurze Tonfolge als WAV (44,1 kHz mono) im Cache; Rückfall, wenn es keine Sprachausgabe gibt."""
    folge = TOENE.get(name)
    if folge is None:
        if name.startswith("akku_") and name[5:].isdigit():                  # 1 … 5 Töne = 20 … 100 %
            folge = [(659, .1), (0, .12)] * max(1, round(int(name[5:]) / 20))
        elif name.startswith("timer_") and name[6:].isdigit():                # 1 … 4 Töne = 15 … 60 Min
            folge = [(523, .1), (0, .12)] * (int(name[6:]) // 15)
        else:
            folge = [(440, .15), (0, .08), (440, .15)]
    ziel = _cache_pfad(name, "ton")
    if os.path.isfile(ziel):
        return ziel
    rate = 44100
    werte = array.array("h", [0] * int(rate * STILLE_VORNE_S))
    for freq, dauer in folge:
        n = int(rate * dauer)
        for i in range(n):
            huelle = min(1.0, i / 400, (n - i) / 400)                          # weich ein/aus, kein Knacken
            werte.append(int(0.35 * 32767 * huelle * math.sin(2 * math.pi * freq * i / rate)) if freq else 0)
    if sys.byteorder == "big":
        werte.byteswap()
    os.makedirs(CACHE, exist_ok=True)
    tmp = ziel + ".tmp"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(werte.tobytes())
    os.replace(tmp, ziel)
    return ziel


def quelle(name, log=print):
    """(Pfad, Art) einer Ansage; Art = 'aufnahme' | 'sprache' | 'ton'. (None, None), wenn nichts geht."""
    p = datei(name)
    if os.path.isfile(p):
        return p, "aufnahme"
    p = _sprache(name, log)
    if p:
        return p, "sprache"
    try:
        return _ton(name), "ton"
    except OSError as e:
        log(f"Ansage '{name}': auch kein Ton möglich ({e!r})")
        return None, None


def quelle_ohne_erzeugen(name):
    """Wie quelle(), erzeugt aber nichts (für die Eltern-Seite: was würde gerade gespielt?)."""
    if os.path.isfile(datei(name)):
        return "aufnahme"
    for art, exe in (("pico", "pico2wave"), ("espeak", "espeak-ng")):
        if shutil.which(exe):
            return "sprache"
    return "ton"


# ---------------------------------------------------------------- Abspielen

def _befehl(pfad):
    return [shutil.which("aplay"), "-q", "-D", geraet(), pfad]


def spielen(name, warten=False, log=print):
    """Spielt eine Ansage. warten=False: läuft im Hintergrund, der Aufrufer macht sofort weiter
    (eine noch fehlende Sprachausgabe wird vorher erzeugt, das dauert beim ersten Mal ca. 1 s)."""
    aplay = shutil.which("aplay")
    if not aplay:
        log("Ansage: aplay fehlt")
        return False
    pfad, art = quelle(name, log=log)
    if not pfad or not os.path.isfile(pfad):
        log(f"Ansage '{name}' fehlt: {datei(name)}")
        return False
    cmd = [aplay, "-q", "-D", geraet(), pfad]
    try:
        if warten:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if r.returncode != 0:
                log(f"Ansage '{name}' nicht abgespielt: {r.stderr.strip()[:200]}")
                return False
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"Ansage '{name}' nicht abgespielt: {e!r}")
        return False


def einmal_je_einschalten(name, log=print, spieler=None):
    """Spielt die Ansage nur beim ersten Aufruf nach dem Einschalten (Markierung im Arbeitsspeicher),
    damit ein Neustart des Players (z. B. nach einem Update) sie nicht wiederholt."""
    marke = einstellungen.lauf_pfad(f"ansage-{name}")
    if os.path.exists(marke):
        return False
    try:
        open(marke, "w").close()
    except OSError:
        pass
    if spieler is not None:
        spieler(name)
        return True
    return spielen(name, log=log)


class Ansager:
    """Spielt Ansagen in einem eigenen Faden. sagen() kehrt sofort zurück; eine neue Ansage
    beendet die laufende. sagen_und_warten() für „Tschüss“ vor dem Ausschalten."""

    def __init__(self, log=print, popen=subprocess.Popen):
        self.log, self.popen = log, popen
        self._bed = threading.Condition()
        self._wunsch = None
        self._proc = None
        self.zuletzt = None                  # (name, Art) der letzten Ansage, für die Eltern-Seite
        self._faden = None
        self._beschaeftigt = False

    def starten(self):
        self._faden = threading.Thread(target=self._lauf, name="ansagen", daemon=True)
        self._faden.start()
        return self._faden

    def lebt(self):
        return self._faden is not None and self._faden.is_alive()

    def _stoppen(self):
        p = self._proc
        if p is not None and p.poll() is None:
            try:
                p.terminate()
            except OSError:
                pass

    def sagen(self, name):
        if name not in ANSAGEN:
            self.log(f"Unbekannte Ansage '{name}'")
            return
        with self._bed:
            self._wunsch = name
            self._stoppen()
            self._bed.notify_all()

    def warten(self, zeit=5.0):
        """Wartet, bis keine Ansage mehr läuft oder ansteht (z. B. „Tschüss“ vor dem Ausschalten)."""
        ende = time.monotonic() + zeit
        while time.monotonic() < ende:
            with self._bed:
                offen = self._wunsch is not None or self._beschaeftigt
            if not offen:
                return True
            time.sleep(0.05)
        return False

    def sagen_und_warten(self, name, zeit=8.0):
        with self._bed:
            self._wunsch = None
            self._stoppen()
        p = self._abspielen(name)
        if p is None:
            return False
        try:
            p.wait(timeout=zeit)
        except subprocess.TimeoutExpired:
            p.terminate()
        return True

    def _abspielen(self, name):
        if not shutil.which("aplay"):
            self.log("Ansage: aplay fehlt")
            return None
        pfad, art = quelle(name, log=self.log)
        if not pfad:
            return None
        try:
            p = self.popen(_befehl(pfad), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except OSError as e:
            self.log(f"Ansage '{name}' nicht abgespielt: {e!r}")
            return None
        self._proc = p
        self.zuletzt = (name, art)
        return p

    def _lauf(self):
        while True:
            with self._bed:
                while self._wunsch is None:
                    self._bed.wait()
                name, self._wunsch = self._wunsch, None
                self._beschaeftigt = True
            try:
                p = self._abspielen(name)
                if p is not None:
                    try:
                        _, fehler = p.communicate(timeout=30)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        fehler = b""
                    if p.returncode not in (0, -15) and fehler:   # -15: von einer neueren Ansage beendet
                        self.log(f"Ansage '{name}' nicht abgespielt: {fehler.decode(errors='replace').strip()[:200]}")
            except Exception as e:                                 # der Faden darf nie sterben
                self.log(f"Ansage '{name}': Fehler {e!r}")
            finally:
                with self._bed:
                    self._beschaeftigt = False

    def vorbereiten(self):
        """Fehlende Sprachausgaben im Hintergrund erzeugen, damit später nichts wartet."""
        def lauf():
            erzeugt = 0
            for name in ANSAGEN:
                if not os.path.isfile(datei(name)) and _sprache(name, self.log):
                    erzeugt += 1
                time.sleep(0.05)
            if erzeugt:
                self.log(f"Sprachausgabe für {erzeugt} Ansagen bereit.")
        threading.Thread(target=lauf, name="ansagen-vorbereiten", daemon=True).start()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--alle":
        for n in ANSAGEN:
            pfad, art = quelle(n)
            print(f"{n:16} {art:9} {ANSAGEN[n]}")
            spielen(n, warten=True)
            time.sleep(0.4)
        sys.exit(0)
    name = sys.argv[1] if len(sys.argv) > 1 else "bereit"
    if name not in ANSAGEN:
        sys.exit(f"Unbekannte Ansage '{name}', möglich: {', '.join(ANSAGEN)}")
    sys.exit(0 if spielen(name, warten=True) else 1)
