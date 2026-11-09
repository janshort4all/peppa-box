"""Tests der Hardware-Schicht ohne Hardware: GPIO-Register, MPR121, Drehgeber, I2C-Befreiung.
Aufruf: cd software && python3 -m unittest -v test_hardware
"""
import ctypes
import os
import struct
import tempfile
import unittest

import drehgeber
import gpio
import i2c
import mpr121


# ---------------------------------------------------------------- GPIO

class GpioRegister(unittest.TestCase):
    def bild(self, pegel=0, fsel=None):
        b = bytearray(4096)
        struct.pack_into("<I", b, gpio.GPLEV0, pegel)
        for reg, wert in (fsel or {}).items():
            struct.pack_into("<I", b, reg, wert)
        return b

    def test_pegel_einzeln_und_alle(self):
        g = gpio.Gpio(mm=self.bild(pegel=(1 << 3) | (1 << 26)))
        self.assertEqual(g.pegel(3), 1)
        self.assertEqual(g.pegel(26), 1)
        self.assertEqual(g.pegel(5), 0)
        self.assertEqual(g.pegel_alle(), (1 << 3) | (1 << 26))

    def test_funktion_pin16_ausgang(self):
        # GPFSEL1 (0x04) deckt GPIO 10..19 ab, Pin 16 = Bits 18..20
        g = gpio.Gpio(mm=self.bild(fsel={0x04: gpio.FUNKTION_AUSGANG << 18}))
        self.assertEqual(g.funktion(16), gpio.FUNKTION_AUSGANG)
        self.assertEqual(g.funktion(17), gpio.FUNKTION_EINGANG)
        g2 = gpio.Gpio(mm=self.bild(fsel={0x00: 4 << 9}))          # GPIO 3 in ALT0 (I2C)
        self.assertEqual(g2.funktion(3), 4)

    def test_pinctrl_zeilen(self):
        z = gpio.PinctrlGpio.ZEILE
        m = z.match(" 3: a0    pu | hi // GPIO3 = SCL1")
        self.assertEqual((m.group(1), m.group(2), m.group(3)), ("3", "a0", "hi"))
        m = z.match("26: ip    pu | lo // GPIO26 = input")
        self.assertEqual((m.group(1), m.group(3)), ("26", "lo"))


# ---------------------------------------------------------------- I2C

class I2CStruktur(unittest.TestCase):
    def test_struktur_wie_kernel(self):
        # struct i2c_msg: __u16 addr, flags, len; __u8 *buf
        zeiger = ctypes.sizeof(ctypes.c_void_p)
        self.assertEqual(ctypes.sizeof(i2c._Msg), 8 + zeiger if zeiger == 8 else 12)
        self.assertEqual(i2c._Msg.buf.offset, 8 if zeiger == 8 else 8)
        self.assertEqual(i2c._RdWr.nmsgs.offset, zeiger)


class FakeLeser:
    def __init__(self, scl=1, sda=0, sda_frei_nach=3):
        self.scl, self.sda, self.takte, self.frei_nach = scl, sda, 0, sda_frei_nach

    def pegel(self, pin):
        return self.scl if pin == i2c.SCL else self.sda


class Befreien(unittest.TestCase):
    def test_taktet_bis_sda_frei_und_stop(self):
        leser = FakeLeser()
        befehle = []

        def setzen(pin, *art, log=None):
            befehle.append((pin, art))
            if pin == i2c.SCL and art == ("ip", "pu"):
                leser.takte += 1
                if leser.takte >= leser.frei_nach:
                    leser.sda = 1
            return True
        self.assertTrue(i2c.befreien(leser, setzen=setzen, schlaf=lambda s: None, log=lambda t: None))
        self.assertEqual(sum(1 for b in befehle if b == (i2c.SCL, ("op", "dl"))), 3 + 0)
        self.assertNotIn((i2c.SCL, ("op", "dh")), befehle)               # SCL nie aktiv hoch
        self.assertEqual(befehle[-2:], [(i2c.SDA, ("a0",)), (i2c.SCL, ("a0",))])

    def test_nichts_tun_wenn_taste_gedrueckt(self):
        befehle = []
        self.assertFalse(i2c.befreien(FakeLeser(scl=0), setzen=lambda *a, **k: befehle.append(a),
                                      schlaf=lambda s: None, log=lambda t: None))
        self.assertEqual(befehle, [])

    def test_freier_bus_unveraendert(self):
        befehle = []
        self.assertTrue(i2c.befreien(FakeLeser(sda=1), setzen=lambda *a, **k: befehle.append(a),
                                     schlaf=lambda s: None, log=lambda t: None))
        self.assertEqual(befehle, [])


# ---------------------------------------------------------------- MPR121

class FakeBus:
    """Registersatz eines MPR121 (nur was die Software nutzt)."""

    def __init__(self):
        self.reg = bytearray(256)
        self.reg[mpr121.CDT] = 0x24
        self.schreibe = []
        self.fehler = None

    def schreiben(self, adr, reg, *werte):
        if self.fehler:
            raise self.fehler
        self.schreibe.append((reg, werte[0]))
        if reg == mpr121.RESET and werte[0] == 0x63:
            self.reg = bytearray(256)
            self.reg[mpr121.CDT] = 0x24
            return
        self.reg[reg] = werte[0]

    def lesen(self, adr, reg, n):
        if self.fehler:
            raise self.fehler
        return bytes(self.reg[reg:reg + n])


class MPR121Test(unittest.TestCase):
    def setUp(self):
        self.bus = FakeBus()
        self.m = mpr121.MPR121(self.bus, schlaf=lambda s: None)

    def test_einrichten_reihenfolge_und_werte(self):
        self.m.einrichten(schwelle=7, loslassen=3)
        w = dict(self.bus.schreibe)
        self.assertEqual(self.bus.schreibe[0], (mpr121.RESET, 0x63))
        self.assertEqual(self.bus.schreibe[1], (mpr121.ECR, 0x00))
        self.assertEqual(self.bus.schreibe[-1], (mpr121.ECR, 0x84))          # nur E0..E3, CL=10
        self.assertEqual((w[mpr121.SCHWELLEN], w[mpr121.SCHWELLEN + 1]), (7, 3))
        self.assertEqual((w[mpr121.SCHWELLEN + 22], w[mpr121.SCHWELLEN + 23]), (7, 3))
        self.assertEqual((w[mpr121.AUTO0], w[mpr121.USL], w[mpr121.TL], w[mpr121.LSL]), (0x8B, 200, 180, 130))
        self.assertEqual(w[mpr121.ENTPRELLEN], 0x22)
        # stärker gemittelt (Phantom-Berührungen 09.11.): FFI 18, SFI 10, ESI 2 ms
        self.assertEqual((w[mpr121.CDC], w[mpr121.CDT]), (0x90, 0x31))
        self.assertEqual(w[mpr121.CDC] >> 6, w[mpr121.AUTO0] >> 6)       # FFI muss übereinstimmen
        self.assertEqual((w[mpr121.CDT] >> 3) & 3, 2)                    # SFI = 10 Proben
        self.assertEqual(w[mpr121.CDT] & 7, 1)                           # ESI = 2 ms

    def test_kein_mpr121(self):
        self.bus.reg[mpr121.CDT] = 0x00
        self.bus.schreiben = lambda adr, reg, *w: None                      # Reset wirkt nicht
        with self.assertRaises(mpr121.Fehler):
            self.m.einrichten()

    def test_beruehrt_und_ueberstrom(self):
        self.m.einrichten()
        self.bus.reg[0], self.bus.reg[1] = 0b0000_0110, 0
        self.assertEqual(self.m.beruehrt(), 0b0110)
        self.bus.reg[0] = 0b1111_0001                                          # E4..E7 sind aus
        self.assertEqual(self.m.beruehrt(), 0b0001)
        self.bus.reg[1] = 0x80                                                  # OVCF
        with self.assertRaises(mpr121.Fehler):
            self.m.beruehrt()

    def test_pruefen_erkennt_neustart_des_chips(self):
        self.m.einrichten()
        self.m.pruefen()
        self.bus.reg[mpr121.ECR] = 0                                            # Chip nach Spannungseinbruch
        with self.assertRaises(mpr121.Fehler):
            self.m.pruefen()

    def test_rohwerte(self):
        self.m.einrichten()
        # E1: Messwert 0x2F0 = 752, Grundlinie 200 << 2 = 800 -> Abstand 48
        self.bus.reg[mpr121.DATEN + 2], self.bus.reg[mpr121.DATEN + 3] = 0xF0, 0x02
        self.bus.reg[mpr121.GRUNDLINIE + 1] = 200
        r = self.m.rohwerte()
        self.assertEqual(r[1], (752, 800, 48))
        self.assertEqual(len(r), 4)

    def test_kalibrieren_und_schlafen(self):
        self.m.einrichten()
        self.bus.schreibe.clear()
        self.m.neu_kalibrieren()
        self.assertEqual(self.bus.schreibe, [(mpr121.ECR, 0), (mpr121.ECR, 0x84)])
        self.m.schlafen()
        self.assertEqual(self.bus.reg[mpr121.ECR], 0)


# ---------------------------------------------------------------- Drehgeber

def ereignis(typ, code, wert):
    return drehgeber.EREIGNIS.pack(0, 0, typ, code, wert)


class Drehgeber(unittest.TestCase):
    def test_kernel_ereignisse(self):
        daten = (ereignis(drehgeber.EV_REL, drehgeber.REL_X, 1) + ereignis(0, 0, 0)
                 + ereignis(drehgeber.EV_REL, drehgeber.REL_X, -1) + ereignis(drehgeber.EV_REL, drehgeber.REL_X, 1))
        self.assertEqual(drehgeber.ereignisse(daten), [1, -1, 1])
        self.assertEqual(drehgeber.ereignisse(daten[:-3]), [1, -1])          # angerissenes Ereignis ignorieren

    def test_geraet_finden(self):
        with tempfile.TemporaryDirectory() as d:
            for nr, name in ((0, "gpio_keys"), (1, "rotary@11")):
                os.makedirs(os.path.join(d, f"event{nr}", "device"))
                with open(os.path.join(d, f"event{nr}", "device", "name"), "w") as f:
                    f.write(name + "\n")
            self.assertEqual(drehgeber.geraet_finden(sysfs=d, dev="/dev/input"), "/dev/input/event1")
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(drehgeber.geraet_finden(sysfs=d))

    def folge(self, zustaende):
        a = drehgeber.Abtaster()
        return [s for z in zustaende if (s := a.neu(z >> 1, z & 1))]

    def test_abtaster_eine_meldung_je_raste_wie_kernel(self):
        # 00 -> 01 -> 11 ist eine Raste; der Kernel-Treiber zählt diese Richtung als -1
        self.assertEqual(self.folge([0b00, 0b01, 0b11]), [-1])
        self.assertEqual(self.folge([0b00, 0b01, 0b11, 0b10, 0b00]), [-1, -1])
        self.assertEqual(self.folge([0b00, 0b10, 0b11, 0b01, 0b00]), [1, 1])

    def test_abtaster_prellen_und_umkehr(self):
        self.assertEqual(self.folge([0b00, 0b01, 0b00, 0b01, 0b00]), [])       # Prellen ohne Raste
        self.assertEqual(self.folge([0b00, 0b01, 0b00, 0b10, 0b11]), [1])      # halb hin, zurück, andersherum
        self.assertEqual(self.folge([0b00, 0b11]), [])                          # Sprung (verpasst) zählt nicht

    def test_melden_zaehlt_und_faengt_fehler(self):
        log, schritte = [], []
        d = drehgeber.Drehgeber(lambda s: schritte.append(s) or (_ for _ in ()).throw(ValueError("x")),
                                log=log.append)
        d._melden(2)
        d._melden(-1)
        self.assertEqual(schritte, [1, 1, -1])
        self.assertEqual((d.schritte, d.letzter), (1, -1))
        self.assertEqual(len(log), 3)


if __name__ == "__main__":
    unittest.main()
