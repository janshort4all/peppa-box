"""Klang des Lautsprechers: Equalizer mit 10 Bändern (alsaequal mit dem LADSPA-Modul Eq10 aus caps).

Der Equalizer sitzt in /etc/asound.conf in einem eigenen Weg "lautsprecher_klang" neben dem
normalen "lautsprecher" (lautsprecher_einrichten.sh). Nur die Tonausgabe (ausgabe.py) spielt über ihn,
und nur wenn der Player ihn freigibt; geht er nicht, spielt sie sofort ohne ihn weiter. Eingestellt
wird er über die ALSA-Steuerung "peppa_klang". Die Werte liegen in
/dev/shm/peppa-box-klang.bin (Arbeitsspeicher, Raspotify darf dort lesen); gespeichert werden sie in
den Einstellungen ("klang"), der Player schreibt sie beim Start hinein, die Eltern-Seite bei jeder
Änderung. Änderungen wirken sofort, auch während Musik läuft.

Einstellung je Band in dB von -24 bis +6. Eq10 rechnet 0 … 100 auf -48 … +24 dB um. Die Bänder
überlappen sich: Ein einzelnes Band wirkt schwächer als sein Wert (am Pi nachgemessen 09.11.2026:
1 kHz ganz unten = -4 dB, ganz oben ≈ +11 dB); für „weniger Bass“ darum mehrere tiefe Bänder senken.
In der Mittelstellung hebt Eq10 alles um ca. 3 dB an; das gleicht die Mischung (asound.conf) aus.
Kopfhörer laufen ohne Equalizer.
"""
import os
import shutil
import subprocess

STEUERUNG = "peppa_klang"
DATEI = "/dev/shm/peppa-box-klang.bin"
BAENDER = ("31 Hz", "63 Hz", "125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz", "8 kHz", "16 kHz")
MIN_DB, MAX_DB = -24, 6
VORLAGEN = {
    "neutral": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    # kleiner Lautsprecher: tiefen Bass weg (kann er nicht, verzerrt nur), Stimmen etwas nach vorn
    "klein": [-24, -18, -8, -2, 0, 0, 2, 3, 2, 0],
    # Hörspiele: Sprache klar, wenig Bass, keine scharfen Höhen
    "sprache": [-24, -20, -10, -4, 0, 2, 3, 2, 0, -4],
    # weicher: weniger Höhen (falls es blechern oder zischelig klingt)
    "weich": [-18, -8, 0, 2, 2, 0, -3, -6, -9, -12],
}


def wert(db):
    """dB (-24 … +6) -> Wert der Steuerung (0 … 100, Eq10: -48 … +24 dB)."""
    db = max(MIN_DB, min(MAX_DB, int(db)))
    return round((db + 48) / 72 * 100)


def _amixer(*args, eingabe=None):
    exe = shutil.which("amixer")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, "-D", STEUERUNG, *args], input=eingabe, capture_output=True, text=True,
                           timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def _datei_ok():
    """Die Datei legt nur peppa-stille (root) an, für alle beschreibbar. Fehlt sie, darf sie hier NICHT
    entstehen: amixer legte sie sonst als Benutzer mit 0644 an, und Raspotify (root ohne Rechte)
    könnte den Equalizer nicht öffnen – genau so ging am 09.11.2026 die Musik aus."""
    try:
        return (os.stat(DATEI).st_mode & 0o666) == 0o666
    except OSError:
        return False


def eingerichtet():
    if not _datei_ok():
        return False
    aus = _amixer("controls")
    return bool(aus) and aus.count("Playback Volume") == len(BAENDER)


def anwenden(baender, log=print):
    """Schreibt die 10 Bänder in den Equalizer. True, wenn amixer es angenommen hat."""
    if len(baender) != len(BAENDER):
        raise ValueError("10 Bänder erwartet")
    befehle = "".join(f"cset numid={i + 1} {wert(db)},{wert(db)}\n" for i, db in enumerate(baender))
    ok = _datei_ok() and _amixer("-q", "-s", eingabe=befehle) is not None
    if not ok:
        log("Klang: Equalizer nicht erreichbar (lautsprecher_einrichten.sh / dienst_einrichten.sh ausführen).")
    return ok
