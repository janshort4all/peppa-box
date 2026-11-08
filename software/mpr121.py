"""Touch-Chip MPR121 (Adafruit 1982, Adresse 0x5A) für die vier Kupferfelder im Deckel.

Einstellungen nach Datenblatt / Application Note AN3944 und der Adafruit-Bibliothek:
  Soft-Reset, Filter (MHD/NHD/NCL/FDL), Entprellen 1 Probe, Auto-Konfiguration für 3,3 V
  (USL 200, TL 180, LSL 130), Grundlinie beim Start aus den ersten Messwerten (CL = 10).
  Nur die benutzten Elektroden E0 … E3 laufen (schneller, weniger Störungen durch offene Eingänge).
Berührt heißt: Messwert liegt um `schwelle` unter der Grundlinie, losgelassen bei `loslassen`.
Durch 4 mm PETG ist das Signal schwach; die Eltern-Seite zeigt den Abstand (delta) live an, damit
sich die Schwelle passend einstellen lässt.

Fehler, die abgefangen werden (alle als OSError gemeldet, der Aufrufer richtet neu ein):
  falsche Antwort nach dem Reset (kein MPR121), Überstrom-Merker (OVCF, Chip steht dann still),
  Chip nicht mehr im Messbetrieb (z. B. nach Spannungseinbruch), I2C-Fehler.
"""
import time

ADRESSE = 0x5A
TOUCH_STATUS, OOR_STATUS = 0x00, 0x02
DATEN, GRUNDLINIE = 0x04, 0x1E
MHDR, NHDR, NCLR, FDLR, MHDF, NHDF, NCLF, FDLF, NHDT, NCLT, FDLT = range(0x2B, 0x36)
SCHWELLEN = 0x41
ENTPRELLEN, CDC, CDT, ECR = 0x5B, 0x5C, 0x5D, 0x5E
AUTO0, USL, LSL, TL = 0x7B, 0x7D, 0x7E, 0x7F
RESET = 0x80
OVCF = 0x8000


class Fehler(OSError):
    pass


class MPR121:
    def __init__(self, bus, adresse=ADRESSE, felder=4, schlaf=time.sleep):
        self.bus, self.adresse, self.felder, self.schlaf = bus, adresse, felder, schlaf
        self.ecr = 0x80 | felder                   # CL = 10, Elektroden E0 … E(felder-1)

    def _w(self, reg, wert):
        self.bus.schreiben(self.adresse, reg, wert)

    def _r(self, reg, n=1):
        return self.bus.lesen(self.adresse, reg, n)

    def einrichten(self, schwelle=8, loslassen=4):
        self._w(RESET, 0x63)
        self.schlaf(0.002)
        self._w(ECR, 0x00)                          # Stopp: nur so lassen sich Register ändern
        if self._r(CDT)[0] != 0x24:                 # Wert nach Reset laut Datenblatt
            raise Fehler("Touch-Chip antwortet nicht wie ein MPR121")
        for e in range(12):
            self._w(SCHWELLEN + 2 * e, schwelle)
            self._w(SCHWELLEN + 2 * e + 1, loslassen)
        for reg, wert in ((MHDR, 0x01), (NHDR, 0x01), (NCLR, 0x0E), (FDLR, 0x00),
                          (MHDF, 0x01), (NHDF, 0x05), (NCLF, 0x01), (FDLF, 0x00),
                          (NHDT, 0x00), (NCLT, 0x00), (FDLT, 0x00)):
            self._w(reg, wert)
        self._w(ENTPRELLEN, 0x11)                   # Berühren und Loslassen je 1 Probe entprellen
        self._w(CDC, 0x10)                          # 16 µA, 6 Proben erster Filter
        self._w(CDT, 0x20)                          # 0,5 µs, 4 Proben zweiter Filter, alle 1 ms
        self._w(AUTO0, 0x0B)                        # Auto-Konfiguration an, bei Abweichung erneut
        self._w(USL, 200)
        self._w(TL, 180)
        self._w(LSL, 130)
        self._w(ECR, self.ecr)                      # messen
        self.schlaf(0.05)
        self.pruefen()

    def pruefen(self):
        """Wirft Fehler, wenn der Chip nicht mehr misst (z. B. nach Spannungseinbruch neu gestartet)."""
        if self._r(ECR)[0] != self.ecr:
            raise Fehler("Touch-Chip misst nicht mehr")

    def beruehrt(self):
        """Bitmaske der berührten Elektroden (Bit 0 = E0)."""
        lo, hi = self._r(TOUCH_STATUS, 2)
        status = lo | (hi << 8)
        if status & OVCF:
            raise Fehler("Touch-Chip meldet Überstrom (Kurzschluss an einem Feld?)")
        return status & ((1 << self.felder) - 1)

    def rohwerte(self):
        """Je Elektrode (Messwert, Grundlinie, Abstand). Abstand > Schwelle = berührt."""
        daten = self._r(DATEN, 2 * self.felder)
        basis = self._r(GRUNDLINIE, self.felder)
        erg = []
        for e in range(self.felder):
            wert = daten[2 * e] | ((daten[2 * e + 1] & 0x03) << 8)
            grund = basis[e] << 2
            erg.append((wert, grund, grund - wert))
        return erg

    def neu_kalibrieren(self):
        """Grundlinie neu aus den aktuellen Messwerten (z. B. wenn ein Feld dauerhaft 'berührt' meldet)."""
        self._w(ECR, 0x00)
        self.schlaf(0.002)
        self._w(ECR, self.ecr)

    def schlafen(self):
        """Stopp-Betrieb (wenige µA), z. B. vor dem Ausschalten."""
        self._w(ECR, 0x00)
