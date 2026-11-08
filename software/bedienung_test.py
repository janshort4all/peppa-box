#!/usr/bin/env python3
"""Bedienelemente live prüfen (Konsole). Strg+C beendet.

  python3 ~/peppa-box/software/bedienung_test.py

Läuft der Player, zeigt das Programm, was der Player gerade sieht (er bleibt ungestört). Läuft er
nicht (sudo systemctl stop peppa-player), liest es die Hardware selbst: Touch-Chip (Abstand je Feld),
Ein-Taste (SCL), Klinke (P26), INT (P05) und Drehknopf (Kernel-Gerät, sonst Pegel P17/P27).
Die Eltern-Seite zeigt dasselbe unter „Bedienung → Prüfen und einstellen“.
"""
import os
import select
import subprocess
import sys
import time

import drehgeber
import einstellungen
import gpio
import i2c
import mpr121

NAMEN = {"zurueck": "zurück", "play": "Play", "vor": "vor", "schlaf": "Mond"}


def player_laeuft():
    r = subprocess.run(["systemctl", "is-active", "--quiet", "peppa-player"], capture_output=True)
    return r.returncode == 0


def zeile(text):
    sys.stdout.write("\r\033[K" + text)
    sys.stdout.flush()


def ueber_player():
    print("Player läuft – zeige, was er sieht. Felder berühren, Knopf drehen, Ein-Taste kurz drücken, Kopfhörer stecken.\n")
    while True:
        einstellungen.lauf_beruehren("seite-bedienung")          # Player liefert dann auch die Rohwerte
        b = einstellungen.lauf_lesen("bedienung") or {}
        if time.time() - b.get("zeit", 0) > 5:
            zeile("Keine Angaben vom Player (läuft er wirklich?)")
        else:
            t, d, k = b["touch"], b["drehknopf"], b["klinke"]
            felder = " ".join(f"[{NAMEN[f]}]" for f in t["beruehrt"]) or "–"
            roh = " ".join(f"E{i}:{r[2]:>3}" for i, r in enumerate(t["roh"] or []))
            zeile(f"Touch {'ok' if t['ok'] else 'FEHLER ' + str(t['fehler'])}: {felder:28} {roh} | "
                  f"Knopf {d['schritte']:+4} ({d['art']}) | Taste {'GEDRÜCKT' if b['taste']['gedrueckt'] else 'los'} | "
                  f"P26 {'hoch' if k['pegel'] else 'tief'} {'Kopfhörer' if k['eingesteckt'] else ''}")
        time.sleep(0.2)


def direkt():
    print("Player ist aus – lese die Hardware selbst.\n")
    cfg = einstellungen.laden()["bedienung"]
    zuordnung = {nr: name for name, nr in cfg["felder"].items()}
    leser = gpio.oeffnen()
    try:
        bus = i2c.I2C()
        m = mpr121.MPR121(bus)
        m.einrichten(cfg["touch_schwelle"], cfg["touch_loslassen"])
        print(f"Touch-Chip gefunden (Schwelle {cfg['touch_schwelle']}).")
    except OSError as e:
        m = None
        print(f"Touch-Chip: {e}  (I2C an, Kabel SDA Klemme 2, SCL Klemme 3, 3,3 V, GND? Jumper 2 und 3?)")
    pfad = drehgeber.geraet_finden()
    fd = os.open(pfad, os.O_RDONLY | os.O_NONBLOCK) if pfad else None
    print(f"Drehknopf: {'Kernel-Gerät ' + pfad if pfad else 'kein Kernel-Gerät (Overlay fehlt?), lese Pegel'}\n")
    abt, schritte = drehgeber.Abtaster(), 0
    for pin in (gpio.KLINKE, gpio.MPR_INT):
        gpio.pinctrl_setzen(pin, "ip", "pu")
    naechste = 0
    while True:
        if fd is not None:
            if select.select([fd], [], [], 0.002)[0]:
                schritte += sum(drehgeber.ereignisse(os.read(fd, drehgeber.EREIGNIS.size * 64)))
        else:
            w = leser.pegel_alle()
            schritte += abt.neu((w >> gpio.DREH_A) & 1, (w >> gpio.DREH_B) & 1)
            time.sleep(0.0015)
        if time.monotonic() < naechste:
            continue
        naechste = time.monotonic() + 0.15
        with i2c.SPERRE:
            w = leser.pegel_alle()
        taste = not (w >> gpio.SCL) & 1
        touch = "–"
        if m is not None and not taste:
            try:
                maske = m.beruehrt()
                roh = m.rohwerte()
                touch = (" ".join(f"[{NAMEN[zuordnung[e]]}]" for e in range(4) if maske >> e & 1) or "–") + "  " + \
                    " ".join(f"E{e}:{r[2]:>3}" for e, r in enumerate(roh))
            except OSError as e:
                touch = f"Fehler {e}"
        zeile(f"Touch {touch:40} | Knopf {schritte:+4} | Taste {'GEDRÜCKT' if taste else 'los'} | "
              f"P26 {'hoch' if (w >> gpio.KLINKE) & 1 else 'tief'} | INT {'tief' if not (w >> gpio.MPR_INT) & 1 else 'hoch'}")


if __name__ == "__main__":
    try:
        ueber_player() if player_laeuft() else direkt()
    except KeyboardInterrupt:
        print()
