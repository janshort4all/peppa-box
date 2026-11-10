"""RC522-Leser (MFRC522) ueber SPI0/CE0. RST liegt fest an 3,3 V, daher Soft-Reset.
Liest Kartennummer und den Link (NDEF-URI) von NTAG/Ultralight und MIFARE Classic.

Gleiche Ablauffolge wie rc522_test.py (dort gegen pimylifeup/MFRC522-python geprueft).
"""
import time

import spidev

from ndef import FEHLT, URI_PREFIX, ndef_aus_tlv, uri_aus_ndef   # noqa: F401  (hier weiter importierbar)

CMD, COMIRQ, ERR, FIFO, FIFOLVL, BITFRAME, COLL = 0x01, 0x04, 0x06, 0x09, 0x0A, 0x0D, 0x0E
MODE, RXMODE, TXCTRL, TXASK = 0x11, 0x13, 0x14, 0x15
TMODE, TPRESC, TRELH, TRELL, VERSION = 0x2A, 0x2B, 0x2C, 0x2D, 0x37
STATUS2 = 0x08
NDEF_KEY = bytes.fromhex("D3F7D3F7D3F7")   # oeffentlicher NFC-Forum-Schluessel fuer NDEF-Sektoren (MIFARE Classic)


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

    def _select(self):
        """Weckt und waehlt eine Karte. Gibt (uid_bytes, sak, auth_uid) zurueck oder None."""
        atqa = self._transceive([0x52], 7)    # WUPA
        if not atqa or len(atqa) != 2:
            return None
        uid, sak_wert, auth_uid = [], 0, []
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
            auth_uid = part[0:4]
            sak_wert = sak[0]
            if not sak_wert & 0x04:
                break
        return uid, sak_wert, auth_uid

    def _halt(self):
        self.clrb(STATUS2, 0x08)               # Verschluesselung (MIFARE Classic) aus
        halt = [0x50, 0x00]
        self._transceive(halt + crc_a(halt))

    def _read_block(self, adr):
        """READ-Befehl: 16 Byte (NTAG: 4 Seiten ab adr, Classic: ein Block)."""
        cmd = [0x30, adr]
        antwort = self._transceive(cmd + crc_a(cmd))
        if not antwort or len(antwort) < 16:
            return None
        return antwort[:16]

    def _auth(self, block, key, auth_uid):
        """MIFARE Classic: Sektor mit Schluessel A freischalten."""
        self.w(CMD, 0x00); self.w(COMIRQ, 0x7F); self.w(FIFOLVL, 0x80)
        for b in [0x60, block] + list(key) + list(auth_uid):
            self.w(FIFO, b)
        self.w(CMD, 0x0E)                      # MFAuthent
        t0 = time.time()
        while True:
            irq = self.r(COMIRQ)
            if irq & 0x10:
                break
            if irq & 0x01 or time.time() - t0 > 0.05:
                return False
        return bool(self.r(STATUS2) & 0x08)

    # ---- Schreiben (Typ 2: NTAG21x / Ultralight). Nur über kartenschreiber.py benutzen.

    def lese16(self, seite):
        """16 Byte ab einer Seite (READ). None bei Fehler."""
        return self._read_block(seite)

    def schreibe4(self, seite, daten):
        """4 Byte auf eine Seite schreiben (WRITE 0xA2). True, wenn die Karte mit ACK (0xA) antwortet."""
        if len(daten) != 4:
            raise ValueError("eine Seite hat 4 Byte")
        cmd = [0xA2, seite] + list(daten)
        antwort = self._transceive(cmd + crc_a(cmd))
        return bool(antwort) and (antwort[0] & 0x0F) == 0x0A

    def beschreiben(self, link):
        """Wählt die aufliegende Karte und schreibt den Link (NDEF) darauf, soweit sie das kann.
        Gibt dict(uid, typ, ok, grund, meldung) zurück; `typ` ist "ntag", "classic" oder "andere"."""
        auswahl = self._select()
        if not auswahl:
            return {"uid": None, "typ": None, "ok": False, "grund": "keine_karte",
                    "meldung": "Keine Karte erkannt."}
        uid, sak, _ = auswahl
        text = ":".join(f"{b:02X}" for b in uid)
        try:
            if sak & 0x7F == 0x00:                                # NTAG / Ultralight (Typ 2)
                import kartenschreiber
                erg = kartenschreiber.ntag_beschreiben(self, link)
                return dict(erg, uid=text, typ="ntag")
            typ = "classic" if sak & 0x08 else "andere"
            return {"uid": text, "typ": typ, "ok": False, "grund": "typ",
                    "meldung": "Dieser Kartentyp lässt sich hier nicht beschreiben."}
        finally:
            self._halt()

    def _ndef_ntag(self):
        daten = []
        for seite in range(4, 4 + 4 * 60, 4):  # bis ca. 960 Byte, NTAG216 hat 888
            block = self._read_block(seite)
            if block is None:
                return None
            daten += block
            ergebnis = ndef_aus_tlv(daten)
            if ergebnis is not FEHLT:
                return ergebnis
        return None

    def _ndef_classic(self, auth_uid):
        daten = []
        for sektor in range(1, 16):            # Sektor 0 ist das Inhaltsverzeichnis (MAD)
            if not self._auth(4 * sektor, NDEF_KEY, auth_uid):
                return None
            for b in range(3):                 # 4. Block jedes Sektors ist der Schluesselblock
                block = self._read_block(4 * sektor + b)
                if block is None:
                    return None
                daten += block
            ergebnis = ndef_aus_tlv(daten)
            if ergebnis is not FEHLT:
                return ergebnis
        return None

    def read_card(self, mit_link=True):
        """Liest eine Karte. Gibt (uid_text, link_oder_None) zurueck oder None, wenn keine da ist."""
        auswahl = self._select()
        if not auswahl:
            return None
        uid, sak, auth_uid = auswahl
        link = None
        if mit_link:
            try:
                if sak & 0x18 == 0x08 or sak & 0x18 == 0x18:      # MIFARE Classic 1K/4K
                    nachricht = self._ndef_classic(auth_uid)
                elif sak & 0x7F == 0x00:                          # NTAG / Ultralight (Typ 2)
                    nachricht = self._ndef_ntag()
                else:
                    nachricht = None
                link = uri_aus_ndef(nachricht) if nachricht else None
            except Exception:
                link = None
        self._halt()
        return ":".join(f"{b:02X}" for b in uid), link

    def read_uid(self):
        """Nur die Kartennummer als Text 'AA:BB:CC:DD' oder None."""
        karte = self.read_card(mit_link=False)
        return karte[0] if karte else None

    def antenne(self, an):
        """Funkfeld ein/aus. Aus zwischen den Abfragen spart Strom und vermeidet Stoerungen."""
        if an:
            self.setb(TXCTRL, 0x03)
            time.sleep(0.005)                  # Karte braucht einen Moment Energie zum Starten
        else:
            self.clrb(TXCTRL, 0x03)

    def schlafen(self):
        """Soft-Power-Down (wenige µA), z. B. vor dem Ausschalten. Aufwecken: neu einrichten (Soft-Reset)."""
        self.w(CMD, 0x10)

    def close(self):
        self.spi.close()


if __name__ == "__main__":
    # Test: python3 ~/peppa-box/software/rc522.py  -> zeigt Kartennummer und Link
    leser = RC522()
    print(f"RC522 Version 0x{leser.version():02X}. Karte auflegen, Strg+C beendet.")
    zuletzt = None
    try:
        while True:
            karte = leser.read_card()
            if karte and karte != zuletzt:
                print("Karte:", karte[0], "Link:", karte[1] or "(kein Link gefunden)")
            zuletzt = karte
            time.sleep(0.2)
    except KeyboardInterrupt:
        print()
