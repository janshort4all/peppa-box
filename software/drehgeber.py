"""Drehknopf (Alps STEC11B03: 15 Impulse, 30 Rasten je Umdrehung) an P17 (A) und P27 (B), C an Masse.

Normalfall: Der Kernel liest den Drehgeber selbst (Overlay in config.txt, richtet
bedienung_einrichten.sh ein):
    dtoverlay=rotary-encoder,pin_a=17,pin_b=27,relative_axis=1,steps-per-period=2
Bei 30 Rasten auf 15 Impulse liegt jede Raste auf einem halben Takt ("half-period mode",
steps-per-period=2): genau eine Meldung +1/-1 je Raste. Das Overlay schaltet die Pull-ups ein.
Der Kernel arbeitet mit Interrupts und verpasst auch bei schnellem Drehen keine Raste.
Gelesen wird das Eingabegerät /dev/input/eventX (Name "rotary@11", 0x11 = GPIO 17) ohne Zusatzpakete.

Rückfall, falls das Overlay (noch) fehlt: die Pegel selbst alle 1,5 ms abtasten (Gray-Code,
Zustandstabelle, Raste = Zustand 00 oder 11). Kostet etwas Rechenzeit, die Eltern-Seite zeigt
dann "Drehknopf ohne Kernel-Treiber". Alle 30 s wird nach dem Kernel-Gerät gesehen.
"""
import glob
import os
import select
import struct
import time

import gpio

EV_REL, REL_X = 0x02, 0x00
EREIGNIS = struct.Struct("llHHi")      # struct input_event: timeval (2 × long), type, code, value
# Übergang (alt << 2 | neu), Zustand = A << 1 | B -> Viertelschritt; ungültige Sprünge = 0.
# Vorzeichen wie der Kernel-Treiber (rotary_encoder_half_period_irq: dir = ((last_stable - state + 1)
# % 4) - 1 mit Gray-Zustand 0, 1, 2, 3 = A/B 00, 01, 11, 10): Folge 00 -> 01 -> 11 zählt -1.
GRAY = [0, -1, +1, 0, +1, 0, 0, -1, -1, 0, 0, +1, 0, +1, -1, 0]
NEU_SUCHEN_S = 30


def geraet_finden(sysfs="/sys/class/input", dev="/dev/input"):
    """Pfad des Kernel-Drehgebers oder None."""
    for name_datei in sorted(glob.glob(os.path.join(sysfs, "event*", "device", "name"))):
        try:
            with open(name_datei) as f:
                name = f.read().strip()
        except OSError:
            continue
        if name.startswith("rotary"):
            return os.path.join(dev, name_datei.split(os.sep)[-3])
    return None


def ereignisse(daten):
    """Bytes aus /dev/input/eventX -> Liste der Drehschritte (+1/-1)."""
    schritte = []
    for i in range(0, len(daten) - EREIGNIS.size + 1, EREIGNIS.size):
        _, _, typ, code, wert = EREIGNIS.unpack_from(daten, i)
        if typ == EV_REL and code == REL_X and wert:
            schritte.append(wert)
    return schritte


class Abtaster:
    """Rückfall: Gray-Code aus zwei Pegeln. Liefert +1/-1 je Raste (Rasten bei 00 und 11)."""

    def __init__(self):
        self.alt = None
        self.summe = 0

    def neu(self, a, b):
        zustand = (a << 1) | b
        if self.alt is None:
            self.alt = zustand
            return 0
        if zustand == self.alt:
            return 0
        self.summe += GRAY[(self.alt << 2) | zustand]
        self.alt = zustand
        if zustand in (0b00, 0b11):                   # Raste erreicht
            schritt = (self.summe > 0) - (self.summe < 0) if abs(self.summe) >= 2 else 0
            self.summe = 0                            # Prellen zwischen zwei Rasten verwerfen
            return schritt
        return 0


class Drehgeber:
    """Läuft als eigener Faden: lauf() blockiert und ruft bei_schritt(+1/-1) auf."""

    def __init__(self, bei_schritt, leser=None, log=print, jetzt=time.monotonic):
        self.bei_schritt, self.leser, self.log, self.jetzt = bei_schritt, leser, log, jetzt
        self.art = None                    # "kernel" | "abtasten" | None
        self.schritte = 0                  # Zähler für die Eltern-Seite
        self.letzter = 0                   # letzte Richtung
        self.lebenszeichen = jetzt()

    def _melden(self, n):
        for s in ([1] * n if n > 0 else [-1] * -n):
            self.schritte += s
            self.letzter = s
            try:
                self.bei_schritt(s)
            except Exception as e:
                self.log(f"Drehknopf: Fehler bei der Verarbeitung: {e!r}")

    def lauf(self):
        while True:
            self.lebenszeichen = self.jetzt()
            pfad = geraet_finden()
            if pfad:
                self._kernel(pfad)
            elif self.leser is not None:
                self._abtasten()
            else:
                self.art = None
                time.sleep(5)

    def _kernel(self, pfad):
        try:
            fd = os.open(pfad, os.O_RDONLY | os.O_NONBLOCK)
        except OSError as e:
            self.log(f"Drehknopf: {pfad} nicht lesbar ({e.strerror}). Gruppe 'input'? Lese selbst.")
            if self.leser is not None:
                self._abtasten()
            else:
                time.sleep(5)
            return
        if self.art != "kernel":
            self.log(f"Drehknopf über Kernel-Treiber ({pfad}).")
        self.art = "kernel"
        try:
            while True:
                self.lebenszeichen = self.jetzt()
                bereit, _, _ = select.select([fd], [], [], 1.0)
                if not bereit:
                    continue
                try:
                    daten = os.read(fd, EREIGNIS.size * 64)
                except BlockingIOError:
                    continue
                if not daten:
                    return
                n = sum(ereignisse(daten))
                if n:
                    self._melden(n)
        except OSError as e:
            self.log(f"Drehknopf: Gerät weg ({e.strerror}), suche neu.")
        finally:
            os.close(fd)

    def _abtasten(self):
        if self.art != "abtasten":
            self.log("Drehknopf: kein Kernel-Treiber (Overlay rotary-encoder fehlt?), taste selbst ab.")
            gpio.pinctrl_setzen(gpio.DREH_A, "ip", "pu", log=self.log)
            gpio.pinctrl_setzen(gpio.DREH_B, "ip", "pu", log=self.log)
        self.art = "abtasten"
        a = Abtaster()
        gemeldet = False
        ende = self.jetzt() + NEU_SUCHEN_S
        while self.jetzt() < ende:
            self.lebenszeichen = self.jetzt()
            try:
                w = self.leser.pegel_alle()
            except Exception as e:
                if not gemeldet:
                    gemeldet = True
                    self.log(f"Drehknopf: Pegel nicht lesbar ({e}), versuche es weiter.")
                time.sleep(1)
                continue
            n = a.neu((w >> gpio.DREH_A) & 1, (w >> gpio.DREH_B) & 1)
            if n:
                self._melden(n)
            time.sleep(0.0015)
