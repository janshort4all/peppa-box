#!/usr/bin/env python3
"""Signaltöne der Peppa Box. Nur Standardbibliothek.

  start   zwei kurze, aufsteigende Töne: Box ist hochgefahren (Dienst peppa-startton, vor dem WLAN)
  bereit  drei helle Töne: Spotify kennt die Box, Karten starten jetzt Musik (Player, einmal je Einschalten)

Die Töne werden bei Bedarf als kleine WAV-Datei in den Arbeitsspeicher (/dev/shm) geschrieben,
nicht auf die SD-Karte. Ausgabe über den gerade aktiven Ausgang (Lautsprecher oder Pi-Klinke),
in der dort eingestellten Lautstärke. Fehler beim Abspielen werden gemeldet, halten aber nichts auf.

Von Hand:  python3 ~/peppa-box/software/toene.py start   (oder: bereit)
"""
import math
import os
import shutil
import struct
import subprocess
import sys
import wave

import einstellungen
import lautstaerke

RATE = 22050
PEGEL = 0.35                  # Anteil der Vollaussteuerung: deutlich leiser als Musik
GERAETE = {"lautsprecher": "lautsprecher", "kopfhoerer": "plughw:CARD=Headphones,DEV=0"}

# Ton = Folge von (Frequenz in Hz, Dauer in s); Noten: E5 659, A5 880, C6 1047, E6 1319, G6 1568
TOENE = {
    "start": [(659.3, 0.16), (880.0, 0.30)],
    "bereit": [(1046.5, 0.12), (1318.5, 0.12), (1568.0, 0.40)],
}


def samples(folge, rate=RATE, pegel=PEGEL):
    """Glockenartige Töne: Sinus mit leiser Oberwelle, weicher Einsatz, abklingend."""
    daten = []
    for freq, dauer in folge:
        n = int(rate * dauer)
        anstieg = int(rate * 0.005)
        for i in range(n):
            t = i / rate
            huelle = math.exp(-4.0 * t / dauer)
            if i < anstieg:
                huelle *= i / anstieg
            if i > n - anstieg:                      # Ende auf null, kein Knacken
                huelle *= (n - i) / anstieg
            w = math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * 2 * freq * t)
            daten.append(int(max(-1.0, min(1.0, pegel * huelle * w / 1.25)) * 32767))
    daten.extend([0] * int(rate * 0.05))             # kurze Stille am Ende
    return daten


def datei(name, ordner=None):
    """Schreibt den Ton als WAV (mono, 16 bit) und gibt den Pfad zurück."""
    ordner = ordner or ("/dev/shm" if os.path.isdir("/dev/shm") else "/tmp")
    pfad = os.path.join(ordner, f"peppa-box-ton-{name}.wav")
    werte = samples(TOENE[name])
    with wave.open(pfad, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(struct.pack(f"<{len(werte)}h", *werte))
    return pfad


def geraet():
    return GERAETE[lautstaerke.aktive_ausgabe()]


def spielen(name, warten=False, log=print):
    """Spielt einen Ton. warten=False: läuft im Hintergrund, der Aufrufer macht sofort weiter."""
    aplay = shutil.which("aplay")
    if not aplay:
        log("Ton: aplay fehlt")
        return False
    try:
        cmd = [aplay, "-q", "-D", geraet(), datei(name)]
        if warten:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if r.returncode != 0:
                log(f"Ton '{name}' nicht abgespielt: {r.stderr.strip()[:200]}")
                return False
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"Ton '{name}' nicht abgespielt: {e!r}")
        return False


def einmal_je_einschalten(name, log=print):
    """Spielt den Ton nur beim ersten Aufruf nach dem Einschalten (Markierung im Arbeitsspeicher),
    damit ein Neustart des Players (z. B. nach einem Update) nicht noch einmal klingelt."""
    marke = einstellungen.lauf_pfad(f"ton-{name}")
    if os.path.exists(marke):
        return False
    try:
        open(marke, "w").close()
    except OSError:
        pass
    return spielen(name, log=log)


def startton(log=print):
    """Für den Dienst peppa-startton: Startlautstärke setzen (sonst klänge der Ton in der Lautstärke
    vom letzten Mal), dann den Startton. In der Ruhezeit mit Modus 'keine Musik' bleibt es still."""
    import time
    import automatik
    if einstellungen.musik_gesperrt(einstellungen.laden(), time.time()):
        log("Ruhezeit (keine Musik): kein Startton")
        return True
    if lautstaerke.aktive_ausgabe() == "lautsprecher":
        # Nur wenn der Lautsprecher-Regler schon da ist; sonst übernimmt das später der Player
        automatik.Automatik(None, lautstaerke, einstellungen, log=log).beim_start()
    return spielen("start", warten=True, log=log)


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "start"
    if name not in TOENE:
        sys.exit(f"Unbekannter Ton '{name}', möglich: {', '.join(TOENE)}")
    ok = startton() if name == "start" else spielen(name, warten=True)
    sys.exit(0 if ok else 1)
