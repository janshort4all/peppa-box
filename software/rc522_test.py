#!/usr/bin/env python3
"""RC522-Test fuer die Peppa Box: zeigt die Nummer (UID) jeder Karte an.

Anschluss: SPI0 / CE0 (Klemme E). RST liegt fest an 3,3 V, deshalb Soft-Reset per Befehl.
Voraussetzung: dtparam=spi=on in /boot/firmware/config.txt, Paket python3-spidev.
Start: python3 rc522_test.py   Beenden: Strg+C
"""
import sys
import time

import spidev

# Register des MFRC522
CMD, COMIRQ, ERR, FIFO, FIFOLVL, BITFRAME = 0x01, 0x04, 0x06, 0x09, 0x0A, 0x0D
MODE, TXCTRL, TXASK = 0x11, 0x14, 0x15
TMODE, TPRESC, TRELH, TRELL, VERSION = 0x2A, 0x2B, 0x2C, 0x2D, 0x37

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
    setb(TXCTRL, 0x03)                # Antenne an


def transceive(data, bits=0):
    """Sendet Bytes an die Karte, gibt die Antwort zurueck (oder None)."""
    w(CMD, 0x00); w(COMIRQ, 0x7F); w(FIFOLVL, 0x80)
    for b in data:
        w(FIFO, b)
    w(BITFRAME, bits)
    w(CMD, 0x0C)                      # Transceive
    setb(BITFRAME, 0x80)              # Senden starten
    t0 = time.time()
    while True:
        irq = r(COMIRQ)
        if irq & 0x30:                # Empfang fertig
            break
        if irq & 0x01 or time.time() - t0 > 0.05:   # Zeit abgelaufen: keine Karte
            clrb(BITFRAME, 0x80)
            return None
    clrb(BITFRAME, 0x80)
    if r(ERR) & 0x1B:
        return None
    return [r(FIFO) for _ in range(r(FIFOLVL))]


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
        return None
    uid = []
    for sel in (0x93, 0x95, 0x97):
        part = transceive([sel, 0x20])
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
    print(f"RC522 gefunden (Version 0x{v:02X}). Karte auflegen, Beenden mit Strg+C.")
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
        time.sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    finally:
        spi.close()
