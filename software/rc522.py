"""RC522-Leser (MFRC522) ueber SPI0/CE0. RST liegt fest an 3,3 V, daher Soft-Reset.

Gleiche Ablauffolge wie rc522_test.py (dort gegen pimylifeup/MFRC522-python geprueft).
"""
import time

import spidev

CMD, COMIRQ, ERR, FIFO, FIFOLVL, BITFRAME, COLL = 0x01, 0x04, 0x06, 0x09, 0x0A, 0x0D, 0x0E
MODE, RXMODE, TXCTRL, TXASK = 0x11, 0x13, 0x14, 0x15
TMODE, TPRESC, TRELH, TRELL, VERSION = 0x2A, 0x2B, 0x2C, 0x2D, 0x37


def crc_a(data):
    c = 0x6363
    for b in data:
        b ^= c & 0xFF
        b = (b ^ (b << 4)) & 0xFF
        c = ((c >> 8) ^ (b << 8) ^ (b << 3) ^ (b >> 4)) & 0xFFFF
    return [c & 0xFF, c >> 8]


class RC522:
    def __init__(self, bus=0, device=0):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 1_000_000
        self.spi.mode = 0
        self.w(CMD, 0x0F)                      # Soft-Reset
        time.sleep(0.05)
        self.w(TMODE, 0x8D); self.w(TPRESC, 0x3E)
        self.w(TRELL, 30); self.w(TRELH, 0)
        self.w(TXASK, 0x40)
        self.w(MODE, 0x3D)
        self.setb(RXMODE, 0x08)                # RxNoErr
        self.setb(TXCTRL, 0x03)                # Antenne an
        time.sleep(0.01)

    def w(self, reg, val):
        self.spi.xfer2([(reg << 1) & 0x7E, val])

    def r(self, reg):
        return self.spi.xfer2([((reg << 1) & 0x7E) | 0x80, 0])[1]

    def setb(self, reg, m):
        self.w(reg, self.r(reg) | m)

    def clrb(self, reg, m):
        self.w(reg, self.r(reg) & ~m)

    def version(self):
        return self.r(VERSION)

    def _transceive(self, data, bits=0):
        self.w(CMD, 0x00); self.w(COMIRQ, 0x7F); self.w(FIFOLVL, 0x80)
        for b in data:
            self.w(FIFO, b)
        self.w(BITFRAME, bits)
        self.w(CMD, 0x0C)
        self.setb(BITFRAME, 0x80)
        t0 = time.time()
        while True:
            irq = self.r(COMIRQ)
            if irq & 0x30:
                break
            if irq & 0x01 or time.time() - t0 > 0.05:
                self.clrb(BITFRAME, 0x80)
                return None
        self.clrb(BITFRAME, 0x80)
        if self.r(ERR) & 0x1B:
            return None
        return [self.r(FIFO) for _ in range(self.r(FIFOLVL))]

    def read_uid(self):
        """UID als Text 'AA:BB:CC:DD' oder None."""
        atqa = self._transceive([0x52], 7)    # WUPA
        if not atqa or len(atqa) != 2:
            return None
        uid = []
        for sel in (0x93, 0x95, 0x97):
            self.clrb(COLL, 0x80)
            part = self._transceive([sel, 0x20])
            if not part or len(part) != 5 or part[0] ^ part[1] ^ part[2] ^ part[3] != part[4]:
                return None
            frame = [sel, 0x70] + part
            sak = self._transceive(frame + crc_a(frame))
            if not sak or len(sak) != 3:
                return None
            uid += part[1:4] if part[0] == 0x88 else part[0:4]
            if not sak[0] & 0x04:
                break
        halt = [0x50, 0x00]
        self._transceive(halt + crc_a(halt))
        return ":".join(f"{b:02X}" for b in uid)

    def close(self):
        self.spi.close()
