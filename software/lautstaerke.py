"""Lautstärke der Peppa Box über den ALSA-Regler (amixer). Nur Standardbibliothek.

Prozent sind die des Reglers wie in alsamixer (`amixer -M`, der Regler folgt dem Hörempfinden
und nicht stur den Rohwerten). Spotify steht fest auf 100 % (LIBRESPOT_VOLUME_CTRL=fixed), die
Lautstärke wird nur hier geregelt.

Ausgänge:
  kopfhoerer    Klinke des Pi (Karte "Headphones", Regler "PCM"), läuft schon
  lautsprecher  MAX98357A: der Verstärker hat keinen eigenen Regler. Software-Lautstärke (ALSA
                softvol "lautsprecher", Regler "Lautsprecher") richtet lautsprecher_einrichten.sh ein.
                Die Karte wird in /proc/asound/cards gesucht (Name enthält "hifiberry"). Gilt als
                eingerichtet, sobald Karte und Regler da sind; sonst "nicht eingerichtet".
"""
import re
import shutil
import subprocess
import time

AUSGABEN = {
    "kopfhoerer": {"karte": "Headphones", "regler": "PCM"},
    "lautsprecher": {"suche": "hifiberry", "regler": "Lautsprecher"},
}
KARTEN_DATEI = "/proc/asound/cards"
KARTE_ZEILE = re.compile(r"^\s*\d+\s+\[([^\]\s]+)\s*\]:(.*)$")
NEU_SUCHEN_S = 30            # nicht gefunden: frühestens nach so vielen Sekunden neu suchen
_gefunden = {}               # ausgang -> Kartenname (bleibt, einmal gefunden)
_zuletzt_gesucht = {}        # ausgang -> Zeitpunkt der letzten erfolglosen Suche
NAMEN = {"kopfhoerer": "Kopfhörer", "lautsprecher": "Lautsprecher"}
PROZENT = re.compile(r"\[(\d{1,3})%\]")


def _karte_suchen(muster):
    try:
        with open(KARTEN_DATEI, encoding="utf-8", errors="replace") as f:
            for zeile in f:
                m = KARTE_ZEILE.match(zeile)
                if m and muster in zeile.lower():
                    return m.group(1)
    except OSError:
        pass
    return None


def _ausgang(ausgang):
    """Karte und Regler eines Ausgangs, None wenn nicht (oder noch nicht) eingerichtet."""
    a = AUSGABEN.get(ausgang)
    if not a:
        return None
    if "karte" in a:
        return a
    if ausgang in _gefunden:
        return {"karte": _gefunden[ausgang], "regler": a["regler"]}
    jetzt = time.monotonic()
    if ausgang in _zuletzt_gesucht and jetzt - _zuletzt_gesucht[ausgang] < NEU_SUCHEN_S:
        return None
    _zuletzt_gesucht[ausgang] = jetzt
    karte = _karte_suchen(a["suche"])
    if karte and _amixer("-c", karte, "sget", a["regler"]) is not None:   # Regler muss es geben
        _gefunden[ausgang] = karte
        return {"karte": karte, "regler": a["regler"]}
    return None


def eingerichtet(ausgang):
    return _ausgang(ausgang) is not None


def aktive_ausgabe():
    """Welcher Ausgang gerade Ton macht. Solange es keine Kopfhörer-Erkennung (Öffner an Pin 37)
    gibt: der Lautsprecher, sobald er eingerichtet ist, sonst die Klinke."""
    return "lautsprecher" if eingerichtet("lautsprecher") else "kopfhoerer"


def _amixer(*args):
    exe = shutil.which("amixer")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def lesen(ausgang):
    """Aktuelle Lautstärke in Prozent, None wenn nicht lesbar oder Ausgang nicht eingerichtet."""
    a = _ausgang(ausgang)
    if not a:
        return None
    aus = _amixer("-M", "-c", a["karte"], "sget", a["regler"])
    treffer = PROZENT.search(aus or "")
    return int(treffer.group(1)) if treffer else None


def setzen(ausgang, prozent):
    """Stellt die Lautstärke ein (0 bis 100). Gibt True zurück, wenn amixer es angenommen hat."""
    a = _ausgang(ausgang)
    if not a:
        return False
    prozent = max(0, min(100, int(round(prozent))))
    return _amixer("-M", "-c", a["karte"], "sset", a["regler"], f"{prozent}%") is not None
