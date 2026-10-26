#!/usr/bin/env python3
"""Akkustand vom Waveshare UPS HAT (D) lesen: INA219 an I2C-Bus 1, Adresse 0x43 (laut Waveshare-Wiki).

Nur Lesen, die Einstellung des Chips wird nicht veraendert. Nur Standardbibliothek.
  Spannung: Register 0x02, Bit 15..3, 4 mV je Schritt (INA219-Datenblatt)
  Shunt-Spannung: Register 0x01, vorzeichenbehaftet, 10 uV je Schritt
Laut Waveshare zeigt das Vorzeichen des Stroms die Richtung: positiv = Akku wird geladen,
negativ = Akku gibt Strom ab. Am Geraet pruefen (Steckbrief-Nachtrag 26.10.2026).
Der Prozentwert ist nur eine grobe Schaetzung aus der Spannung (Waveshare nennt nur: voll = 4,2 V).

Test auf dem Pi:  python3 ~/peppa-box/software/akku.py
"""
import fcntl
import os

BUS = "/dev/i2c-1"
ADRESSE = 0x43
I2C_SLAVE = 0x0703

# Grobe Kennlinie einer Li-Ionen-Zelle (Spannung in V -> Prozent), dazwischen linear.
KENNLINIE = [(3.00, 0), (3.30, 5), (3.50, 15), (3.65, 30), (3.75, 45), (3.85, 60),
             (3.95, 72), (4.05, 85), (4.15, 96), (4.20, 100)]
SCHWELLE_SHUNT_MV = 0.3     # darunter gilt der Strom als "kaum Strom" (ruhend/voll)


def _register(fd, reg):
    os.write(fd, bytes([reg]))
    hoch, tief = os.read(fd, 2)
    return (hoch << 8) | tief


def prozent(spannung):
    if spannung <= KENNLINIE[0][0]:
        return 0
    for (u1, p1), (u2, p2) in zip(KENNLINIE, KENNLINIE[1:]):
        if spannung <= u2:
            return round(p1 + (p2 - p1) * (spannung - u1) / (u2 - u1))
    return 100


def lesen():
    """Gibt ein dict zurueck: spannung (V), prozent (Schaetzung), shunt_mv, richtung, fehler."""
    try:
        fd = os.open(BUS, os.O_RDWR)
    except OSError as e:
        return {"fehler": f"I2C nicht verfügbar ({e.strerror})"}
    try:
        fcntl.ioctl(fd, I2C_SLAVE, ADRESSE)
        bus = _register(fd, 0x02)
        shunt = _register(fd, 0x01)
    except OSError as e:
        return {"fehler": f"Akku-Chip antwortet nicht ({e.strerror})"}
    finally:
        os.close(fd)
    spannung = (bus >> 3) * 0.004
    if shunt >= 0x8000:
        shunt -= 0x10000
    shunt_mv = shunt * 0.01
    if shunt_mv > SCHWELLE_SHUNT_MV:
        richtung = "laedt"
    elif shunt_mv < -SCHWELLE_SHUNT_MV:
        richtung = "akku"
    else:
        richtung = "ruhend"
    return {"spannung": round(spannung, 3), "prozent": prozent(spannung),
            "shunt_mv": round(shunt_mv, 2), "richtung": richtung}


if __name__ == "__main__":
    print(lesen())
