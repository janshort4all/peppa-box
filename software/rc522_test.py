#!/usr/bin/env python3
"""RC522-Test fuer die Peppa Box: zeigt die Nummer (UID) jeder Karte an.

Anschluss: SPI0 / CE0 (Klemme E). RST liegt fest an 3,3 V, deshalb Soft-Reset per Befehl.
Voraussetzung: dtparam=spi=on in /boot/firmware/config.txt, Paket python3-spidev.
Start: python3 rc522_test.py   Diagnose: python3 rc522_test.py --debug [--gain=0..7]   Zaehlung: --stat   Beenden: Strg+C
"""
import sys
import time

import spidev

# Register des MFRC522
CMD, COMIRQ, ERR, FIFO, FIFOLVL, BITFRAME = 0x01, 0x04, 0x06, 0x09, 0x0A, 0x0D
MODE, RXMODE, TXCTRL, TXASK = 0x11, 0x13, 0x14, 0x15
TMODE, TPRESC, TRELH, TRELL, VERSION = 0x2A, 0x2B, 0x2C, 0x2D, 0x37
RFCFG, COLL = 0x26, 0x0E
DEBUG = "--debug" in sys.argv
GAIN = None                           # Empfangsverstaerkung 0..7 (Standard des Chips: 4 = 33 dB)
for a in sys.argv:
    if a.startswith("--gain="):
        GAIN = int(a.split("=")[1])
last_diag = ""

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1_000_000
spi.mode = 0


def w(reg, val):
    spi.xfer2([(reg << 1) & 0x7E, val])


def r(reg):
    return spi.xfer2([((reg << 1) & 0x7E) | 0x80, 0])[1]


def setb(reg, mask):
    w(reg, r(reg) | mask)


def clrb(reg, mask):
    w(reg, r(reg) & ~mask)


def init():
    w(CMD, 0x0F)                      # Soft-Reset (ersetzt den RST-Pin)
    time.sleep(0.05)
    w(TMODE, 0x8D); w(TPRESC, 0x3E)   # Zeitgeber ca. 15 ms Wartezeit auf die Karte
    w(TRELL, 30); w(TRELH, 0)
    w(TXASK, 0x40)                    # 100 % ASK
    w(MODE, 0x3D)                     # CRC-Startwert 0x6363
    if "--no-rxnoerr" not in sys.argv:
        setb(RXMODE, 0x08)            # RxNoErr: Stoerimpulse unter 4 Bit ignorieren, weiter empfangen
    if GAIN is not None:
        w(RFCFG, (GAIN & 0x07) << 4)  # Empfangsverstaerkung setzen
    setb(TXCTRL, 0x03)                # Antenne an
    time.sleep(0.01)


def transceive(data, bits=0):
    """Sendet Bytes an die Karte, gibt die Antwort zurueck (oder None)."""
    w(CMD, 0x00); w(COMIRQ, 0x7F); w(FIFOLVL, 0x80)
    for b in data:
        w(FIFO, b)
    w(BITFRAME, bits)
    w(CMD, 0x0C)                      # Transceive
    setb(BITFRAME, 0x80)              # Senden starten
    global last_diag
    t0 = time.time()
    while True:
        irq = r(COMIRQ)
        if irq & 0x30:                # Empfang fertig
            break
        if irq & 0x01 or time.time() - t0 > 0.05:   # Zeit abgelaufen: keine Karte
            clrb(BITFRAME, 0x80)
            if irq & 0x02:            # Fehler beim Empfang: Karte hat geantwortet, aber gestoert
                err = r(ERR)
                n = r(FIFOLVL)
                bits = r(0x0C) & 0x07
                data = [hex(r(FIFO)) for _ in range(n)]
                last_diag = (f"GESTOERTE Antwort: Error 0x{err:02X} ({fehlertext(err)}), "
                             f"{n} Byte {data}, letzte Bits {bits}, Coll 0x{r(COLL):02X}")
            else:
                last_diag = f"keine Antwort (ComIrq 0x{irq:02X}, TxControl 0x{r(TXCTRL):02X})"
            return None
    clrb(BITFRAME, 0x80)
    err = r(ERR)
    n = r(FIFOLVL)
    data = [r(FIFO) for _ in range(n)]
    last_diag = f"Antwort {n} Byte {[hex(x) for x in data]} (Error 0x{err:02X}, ComIrq 0x{irq:02X}, Control 0x{r(0x0C):02X})"
    if err & 0x1B:
        return None
    return data


def fehlertext(err):
    namen = [(0x01, "Protokoll"), (0x02, "Paritaet"), (0x04, "CRC"), (0x08, "Kollision"),
             (0x10, "Puffer voll"), (0x40, "Temperatur"), (0x80, "Schreibfehler")]
    return ", ".join(t for b, t in namen if err & b) or "keiner"


def crc_a(data):
    c = 0x6363
    for b in data:
        b ^= c & 0xFF
        b = (b ^ (b << 4)) & 0xFF
        c = ((c >> 8) ^ (b << 8) ^ (b << 3) ^ (b >> 4)) & 0xFFFF
    return [c & 0xFF, c >> 8]


def read_uid():
    """Weckt die Karte, liest die UID (4, 7 oder 10 Byte) und legt die Karte wieder schlafen."""
    atqa = transceive([0x52], 7)      # WUPA: weckt auch schlafende Karten
    if not atqa or len(atqa) != 2:
        if DEBUG:
            print("  WUPA:", last_diag)
        return None
    uid = []
    if DEBUG:
        print("  WUPA:", last_diag)
    for sel in (0x93, 0x95, 0x97):
        clrb(COLL, 0x80)
        part = transceive([sel, 0x20])
        if DEBUG:
            print(f"  Antikollision 0x{sel:02X}:", last_diag)
        if not part or len(part) != 5 or part[0] ^ part[1] ^ part[2] ^ part[3] != part[4]:
            return None
        frame = [sel, 0x70] + part
        sak = transceive(frame + crc_a(frame))
        if not sak or len(sak) != 3:
            return None
        uid += part[1:4] if part[0] == 0x88 else part[0:4]
        if not sak[0] & 0x04:         # UID vollstaendig
            break
    halt = [0x50, 0x00]
    transceive(halt + crc_a(halt))    # Karte schlafen legen (keine Antwort erwartet)
    return uid


def main():
    init()
    v = r(VERSION)
    if v in (0x00, 0xFF):
        print(f"Keine Antwort vom RC522 (Version 0x{v:02X}). Kabel und SPI pruefen.")
        sys.exit(1)
    print(f"RC522 gefunden (Version 0x{v:02X}). Verstaerkung 0x{r(RFCFG):02X}, RxMode 0x{r(RXMODE):02X}. Karte auflegen, Beenden mit Strg+C.")
    if "--stat" in sys.argv:
        print("Zaehlung: Karte ruhig liegen lassen. Je 20 Versuche eine Zeile.")
        while True:
            ok, nummern = 0, set()
            for _ in range(20):
                uid = read_uid()
                if uid:
                    ok += 1
                    nummern.add(":".join(f"{b:02X}" for b in uid))
                time.sleep(0.05)
            print(f"{ok:2d}/20 gelesen  {' '.join(sorted(nummern))}")
    last, miss = None, 0
    while True:
        uid = read_uid()
        if uid:
            miss = 0
            if uid != last:
                print("Karte:", ":".join(f"{b:02X}" for b in uid))
                last = uid
        else:
            miss += 1
            if last and miss >= 3:
                print("Karte entfernt")
                last = None
        time.sleep(0.5 if DEBUG else 0.1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    finally:
        spi.close()
