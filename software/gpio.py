"""GPIO-Pegel lesen ohne Zusatzpakete. Nur Standardbibliothek.

Gelesen wird das Pegel-Register GPLEV0 über /dev/gpiomem (Raspberry Pi 3A+, BCM2837: GPIO-Block ab
Versatz 0, GPLEV0 bei 0x34). Ein Zugriff liefert alle Pins 0 … 31 auf einmal und ändert nichts an
der Funktion der Pins. Darum lässt sich auch SCL (GPIO 3) lesen, obwohl der Pin für I2C arbeitet –
dort hängt die Ein-Taste.

Pins der Peppa Box (Aufdruck des Klemmen-Aufsatzes → GPIO):
  Klemme 3 / SCL1   GPIO 3    Ein-Taste (gedrückt = tief), auch I2C-Takt
  gelber Stift P05  GPIO 5    MPR121 INT (Berührung geändert = tief)
  gelber Stift P16  GPIO 16   MAX98357A SD (Ausgang tief = Verstärker stumm)
  gelber Stift P17  GPIO 17   Drehgeber A
  gelber Stift P27  GPIO 27   Drehgeber B
  gelber Stift P26  GPIO 26   Klinke, Öffner L (Pull-up; ohne Stecker mit L verbunden = tief)

Setzen (Richtung, Pull-up) über das Systemprogramm pinctrl (Raspberry Pi OS, braucht die Gruppe gpio).
Fehlt /dev/gpiomem, liest PinctrlGpio den Pegel über pinctrl (langsamer, nur als Rückfall).
"""
import mmap
import os
import re
import shutil
import subprocess

GPIOMEM = "/dev/gpiomem"
GPFSEL0 = 0x00
GPLEV0 = 0x34

SCL, MPR_INT, VERSTAERKER_SD, DREH_A, DREH_B, KLINKE = 3, 5, 16, 17, 27, 26

FUNKTION_EINGANG, FUNKTION_AUSGANG = 0, 1


class Gpio:
    """Pegel und Pin-Funktion aus den Registern. `mm` nur für Tests (bytearray mit Registerbild)."""

    def __init__(self, pfad=GPIOMEM, mm=None):
        self._mm = None
        if mm is None:
            fd = os.open(pfad, os.O_RDWR | os.O_SYNC)
            try:
                mm = mmap.mmap(fd, 4096, mmap.MAP_SHARED, mmap.PROT_READ)
            finally:
                os.close(fd)
            self._mm = mm
        self._reg = memoryview(mm).cast("I")            # 32-Bit-Zugriffe, wie die Register es verlangen

    def pegel_alle(self):
        return self._reg[GPLEV0 // 4]

    def pegel(self, pin):
        return (self.pegel_alle() >> pin) & 1

    def funktion(self, pin):
        """0 Eingang, 1 Ausgang, 4 … 7 / 2 / 3 Sonderfunktionen (ALT0 … ALT5)."""
        wert = self._reg[(GPFSEL0 + 4 * (pin // 10)) // 4]
        return (wert >> (3 * (pin % 10))) & 7

    def close(self):
        try:
            self._reg.release()
        except Exception:
            pass
        if self._mm is not None:
            self._mm.close()


class PinctrlGpio:
    """Rückfall ohne /dev/gpiomem: Pegel über 'pinctrl get' (ein Programmaufruf je Abfrage)."""
    ZEILE = re.compile(r"^\s*(\d+):\s*(\S+).*?\|\s*(hi|lo)")

    def __init__(self, pins):
        self.pins = sorted(set(pins))
        self.exe = shutil.which("pinctrl")
        if not self.exe:
            raise OSError("pinctrl fehlt")
        self.pegel_alle()                                # einmal probieren, wirft bei Fehler

    def _get(self):
        r = subprocess.run([self.exe, "get", ",".join(str(p) for p in self.pins)],
                           capture_output=True, text=True, timeout=3)
        if r.returncode != 0:
            raise OSError(r.stderr.strip() or "pinctrl get fehlgeschlagen")
        return [self.ZEILE.match(z) for z in r.stdout.splitlines()]

    def pegel_alle(self):
        wert = 0
        for m in self._get():
            if m and m.group(3) == "hi":
                wert |= 1 << int(m.group(1))
        return wert

    def pegel(self, pin):
        return (self.pegel_alle() >> pin) & 1

    def funktion(self, pin):
        for m in self._get():
            if m and int(m.group(1)) == pin:
                return {"ip": 0, "op": 1}.get(m.group(2), 4)
        return None

    def close(self):
        pass


def oeffnen(pins=(SCL, MPR_INT, KLINKE, DREH_A, DREH_B, VERSTAERKER_SD), log=print):
    """Bestmöglicher Leser: /dev/gpiomem, sonst pinctrl. Wirft OSError, wenn beides fehlt."""
    try:
        return Gpio()
    except OSError as e:
        log(f"GPIO: /dev/gpiomem nicht nutzbar ({e.strerror or e}), lese über pinctrl.")
    return PinctrlGpio(pins)


def pinctrl_setzen(pin, *art, log=print):
    """z. B. pinctrl_setzen(26, 'ip', 'pu') oder (16, 'op', 'dl'). Gibt True zurück, wenn es klappte."""
    exe = shutil.which("pinctrl")
    if not exe:
        log("pinctrl fehlt")
        return False
    try:
        r = subprocess.run([exe, "set", str(pin), *art], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"pinctrl set {pin} {' '.join(art)}: {e!r}")
        return False
    if r.returncode != 0:
        log(f"pinctrl set {pin} {' '.join(art)}: {r.stderr.strip()[:200]}")
    return r.returncode == 0
