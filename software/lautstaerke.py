"""Lautstärke der Peppa Box über den ALSA-Regler (amixer). Nur Standardbibliothek.

Prozent sind die des Reglers wie in alsamixer (`amixer -M`, der Regler folgt dem Hörempfinden
und nicht stur den Rohwerten). Spotify steht fest auf 100 % (LIBRESPOT_VOLUME_CTRL=fixed), die
Lautstärke wird nur hier geregelt.

Ausgänge:
  kopfhoerer    Klinke des Pi (Karte "Headphones", Regler "PCM"), läuft schon
  lautsprecher  MAX98357A: der Verstärker hat keinen eigenen Regler. Erst wenn der Lautsprecher
                eingebaut ist und eine Software-Lautstärke (ALSA softvol) eingerichtet wurde, hier
                Karte und Reglername eintragen. Bis dahin gilt er als "nicht eingerichtet".
"""
import re
import shutil
import subprocess

AUSGABEN = {
    "kopfhoerer": {"karte": "Headphones", "regler": "PCM"},
    "lautsprecher": None,
}
NAMEN = {"kopfhoerer": "Kopfhörer", "lautsprecher": "Lautsprecher"}
PROZENT = re.compile(r"\[(\d{1,3})%\]")


def eingerichtet(ausgang):
    return AUSGABEN.get(ausgang) is not None


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
    a = AUSGABEN.get(ausgang)
    if not a:
        return None
    aus = _amixer("-M", "-c", a["karte"], "sget", a["regler"])
    treffer = PROZENT.search(aus or "")
    return int(treffer.group(1)) if treffer else None


def setzen(ausgang, prozent):
    """Stellt die Lautstärke ein (0 bis 100). Gibt True zurück, wenn amixer es angenommen hat."""
    a = AUSGABEN.get(ausgang)
    if not a:
        return False
    prozent = max(0, min(100, int(round(prozent))))
    return _amixer("-M", "-c", a["karte"], "sset", a["regler"], f"{prozent}%") is not None
