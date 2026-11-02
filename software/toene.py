#!/usr/bin/env python3
"""Ansagen der Peppa Box. Nur Standardbibliothek.

  bereit  „Peppa Box bereit“: Spotify kennt die Box, eine Karte startet jetzt Musik.
          Spielt der Player einmal je Einschalten (nicht nach Updates oder „Musik neu starten“).

Die Ansagen liegen als WAV in software/ansagen/. Ausgabe über den gerade aktiven Ausgang
(Lautsprecher oder Pi-Klinke) in der dort eingestellten Lautstärke; der Player setzt vorher die
Startlautstärke. Fehler beim Abspielen werden gemeldet, halten aber nichts auf.
Keine Pieptöne mehr (Entscheidung Jan, 02.11.2026).

Von Hand:  python3 ~/peppa-box/software/toene.py bereit
"""
import os
import shutil
import subprocess
import sys

import einstellungen
import lautstaerke

ORDNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ansagen")
ANSAGEN = {"bereit": "peppa_box_bereit.wav"}
GERAETE = {"lautsprecher": "lautsprecher", "kopfhoerer": "plughw:CARD=Headphones,DEV=0"}


def datei(name):
    return os.path.join(ORDNER, ANSAGEN[name])


def geraet():
    return GERAETE[lautstaerke.aktive_ausgabe()]


def spielen(name, warten=False, log=print):
    """Spielt eine Ansage. warten=False: läuft im Hintergrund, der Aufrufer macht sofort weiter."""
    aplay = shutil.which("aplay")
    if not aplay:
        log("Ansage: aplay fehlt")
        return False
    pfad = datei(name)
    if not os.path.isfile(pfad):
        log(f"Ansage '{name}' fehlt: {pfad}")
        return False
    cmd = [aplay, "-q", "-D", geraet(), pfad]
    try:
        if warten:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode != 0:
                log(f"Ansage '{name}' nicht abgespielt: {r.stderr.strip()[:200]}")
                return False
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"Ansage '{name}' nicht abgespielt: {e!r}")
        return False


def einmal_je_einschalten(name, log=print):
    """Spielt die Ansage nur beim ersten Aufruf nach dem Einschalten (Markierung im Arbeitsspeicher),
    damit ein Neustart des Players (z. B. nach einem Update) sie nicht wiederholt."""
    marke = einstellungen.lauf_pfad(f"ansage-{name}")
    if os.path.exists(marke):
        return False
    try:
        open(marke, "w").close()
    except OSError:
        pass
    return spielen(name, log=log)


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "bereit"
    if name not in ANSAGEN:
        sys.exit(f"Unbekannte Ansage '{name}', möglich: {', '.join(ANSAGEN)}")
    sys.exit(0 if spielen(name, warten=True) else 1)
