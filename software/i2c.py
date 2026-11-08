"""I2C-Bus 1 des Pi ohne Zusatzpakete (ioctl I2C_RDWR über ctypes, wie smbus2 es macht).

Auf dem Bus: MPR121 (0x5A, Touch) und INA219 des Akku-Boards (0x43). Die Ein-Taste zieht SCL
nach Masse; solange sie gedrückt ist, scheitern alle Übertragungen. Darum
  - laufen alle Zugriffe dieses Prozesses unter SPERRE: die Abfrage der Ein-Taste liest SCL nur,
    wenn gerade niemand sendet (sonst sähe sie den Takt als "gedrückt"),
  - gibt es befreien(): Hält ein Baustein nach einem Abbruch SDA fest (Taste mitten in einer
    Übertragung gedrückt), taktet es SCL neunmal und erzeugt ein STOP – der übliche Weg, einen
    hängenden I2C-Bus zu lösen. Dabei wird SCL nie aktiv hoch getrieben (nur Eingang mit Pull-up),
    damit nichts gegen die gedrückte Taste arbeitet.
Lesen mit wiederholtem START (Register schreiben, dann lesen, ohne STOP dazwischen), wie im
MPR121-Datenblatt beschrieben.
"""
import ctypes
import fcntl
import os
import threading
import time

import gpio

I2C_RDWR = 0x0707
I2C_M_RD = 0x0001
SDA, SCL = 2, 3
SPERRE = threading.RLock()


class _Msg(ctypes.Structure):
    _fields_ = [("addr", ctypes.c_uint16), ("flags", ctypes.c_uint16),
                ("len", ctypes.c_uint16), ("buf", ctypes.POINTER(ctypes.c_uint8))]


class _RdWr(ctypes.Structure):
    _fields_ = [("msgs", ctypes.POINTER(_Msg)), ("nmsgs", ctypes.c_uint32)]


class I2C:
    def __init__(self, bus=1):
        self.pfad = f"/dev/i2c-{bus}"
        self.fd = os.open(self.pfad, os.O_RDWR)

    def _uebertragen(self, msgs):
        feld = (_Msg * len(msgs))(*msgs)
        daten = _RdWr(feld, len(msgs))
        with SPERRE:
            fcntl.ioctl(self.fd, I2C_RDWR, daten)

    def lesen(self, adresse, register, anzahl):
        reg = (ctypes.c_uint8 * 1)(register)
        puffer = (ctypes.c_uint8 * anzahl)()
        self._uebertragen([_Msg(adresse, 0, 1, reg), _Msg(adresse, I2C_M_RD, anzahl, puffer)])
        return bytes(puffer)

    def schreiben(self, adresse, register, *werte):
        puffer = (ctypes.c_uint8 * (1 + len(werte)))(register, *werte)
        self._uebertragen([_Msg(adresse, 0, len(puffer), puffer)])

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass


def befreien(leser, setzen=gpio.pinctrl_setzen, schlaf=time.sleep, log=print):
    """Löst einen hängenden Bus (SDA dauerhaft tief). `leser`: gpio.Gpio. Gibt True zurück, wenn
    SDA danach frei ist. Tut nichts, wenn SCL tief ist (Ein-Taste gedrückt)."""
    with SPERRE:
        if not leser.pegel(SCL):
            return False                      # Taste gedrückt: nichts zu machen, später wieder
        if leser.pegel(SDA):
            return True
        log("I2C: SDA hängt, Bus wird freigetaktet.")
        try:
            setzen(SDA, "ip", "pu", log=log)
            for _ in range(9):
                setzen(SCL, "op", "dl", log=log)
                schlaf(0.0005)
                setzen(SCL, "ip", "pu", log=log)
                schlaf(0.0005)
                if leser.pegel(SDA):
                    break
            setzen(SDA, "op", "dl", log=log)      # STOP: SDA steigt, während SCL hoch ist
            schlaf(0.0005)
            setzen(SCL, "ip", "pu", log=log)
            schlaf(0.0005)
            setzen(SDA, "ip", "pu", log=log)
        finally:
            setzen(SDA, "a0", log=log)
            setzen(SCL, "a0", log=log)
        frei = bool(leser.pegel(SDA))
        log("I2C: Bus frei." if frei else "I2C: SDA hängt weiter.")
        return frei
