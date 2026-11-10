#!/usr/bin/env python3
"""Akkustand vom Waveshare UPS HAT (D) lesen: INA219 an I2C-Bus 1, Adresse 0x43 (laut Waveshare-Wiki).

Nur Lesen, die Einstellung des Chips wird nicht veraendert. Nur Standardbibliothek.
  Spannung: Register 0x02, Bit 15..3, 4 mV je Schritt (INA219-Datenblatt)
  Shunt-Spannung: Register 0x01, vorzeichenbehaftet, 10 uV je Schritt
Waveshare nennt positiv = Akku wird geladen. Am Geraet ist es UMGEKEHRT (gemessen 02.11. und
05.11.2026: mit Netzteil negativ, ohne Netzteil positiv, Spannung mit Netzteil 0,12 V hoeher).
Deshalb VORZEICHEN = -1.
Der Prozentwert ist nur eine grobe Schaetzung aus der Ruhespannung (Waveshare nennt nur: voll = 4,2 V).
Beim Laden liegt die Spannung hoeher als die Ruhespannung, der Wert waere zu hoch. Waehrend des
Ladens wird daher kein Prozentwert geliefert (prozent = None), nur die Richtung.

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
VORZEICHEN = -1             # am Geraet gemessen, siehe oben
VOLL_AB_V = 4.10            # kaum Strom bei dieser Spannung: Netzteil steckt, Akku (fast) voll


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
    return auswerten(bus, shunt)


def auswerten(bus, shunt):
    """Rohwerte der Register 0x02 und 0x01 in Anzeige-Werte umrechnen (ohne Hardware testbar)."""
    spannung = (bus >> 3) * 0.004
    if shunt >= 0x8000:
        shunt -= 0x10000
    shunt_mv = shunt * 0.01 * VORZEICHEN      # positiv = Akku wird geladen
    if shunt_mv > SCHWELLE_SHUNT_MV:
        richtung = "laedt"
    elif shunt_mv < -SCHWELLE_SHUNT_MV:
        richtung = "akku"
    else:
        # Ohne Netzteil zieht der Pi immer deutlich Strom; kaum Strom heisst also Netzteil + voll.
        richtung = "voll" if spannung >= VOLL_AB_V else "ruhend"
    return {"spannung": round(spannung, 3),
            "prozent": None if richtung == "laedt" else prozent(spannung),
            "shunt_mv": round(shunt_mv, 2), "richtung": richtung}


def ansage_name(info):
    """Welche Ansage den Akkustand beschreibt (Mond-Feld 5 s halten, Ein-Taste kurz drücken)."""
    if not info or info.get("fehler"):
        return "akku_unbekannt"
    if info.get("richtung") == "laedt":
        return "akku_laedt"
    if info.get("richtung") == "voll":
        return "akku_voll"
    p = info.get("prozent")
    if p is None:
        return "akku_unbekannt"
    return f"akku_{min(100, max(10, int(p / 10 + 0.5) * 10))}"


class Akkuwache:
    """Liest den Akku alle ABSTAND_S Sekunden (im Faden der Bedienung, damit sich I2C-Zugriffe und
    die Ein-Taste an SCL nicht in die Quere kommen).
      - Akkubetrieb und höchstens WARNEN_PROZENT: einmal „Mein Akku ist fast leer“ (wieder scharf
        nach dem Laden)
      - Akkubetrieb und AUS_SPANNUNG oder weniger bei AUS_MESSUNGEN Messungen in Folge: Ansage und
        sauber ausschalten, bevor das Akku-Board hart abschaltet (schützt die SD-Karte)
      - merkt den letzten Prozentwert ohne Netzteil (die Eltern-Seite zeigt ihn beim Laden an)
    Schwellen festgelegt, nicht gemessen (Kennlinie oben: 3,50 V ≈ 15 %, 3,30 V ≈ 5 %)."""
    ABSTAND_S = 15              # Abstand der Auswertung (Warnung, Aus): bleibt, die Schwellen zählen Messungen
    ABSTAND_NETZ_S = 2          # Abstand der Messung selbst: so schnell hört man den Ton nach dem Einstecken
    NETZ_MESSUNGEN = 2          # so viele Messungen in Folge mit Netzteil, bis „Deine Box wird geladen“ kommt
    WARNEN_PROZENT = 15
    AUS_SPANNUNG = 3.30
    AUS_MESSUNGEN = 3

    def __init__(self, lesen=lesen, ansage=None, ausschalten=None, log=print):
        self.lesen, self.ansage, self.ausschalten, self.log = lesen, ansage, ausschalten, log
        self.wert = None
        self.prozent_ohne_netzteil = None
        self.zeit = None
        self._naechste = 0.0
        self._gewarnt = False
        self._kritisch = 0
        self._aus = False
        self._lesen_ab = 0.0
        self._netz = None               # None = noch unbekannt, sonst: steckte das Netzteil zuletzt?
        self._netz_zaehler = 0          # Messungen in Folge, die vom bisherigen Zustand abweichen

    def tick(self, t):
        if t < self._lesen_ab:
            return
        self._lesen_ab = t + self.ABSTAND_NETZ_S
        try:
            w = self.lesen()
        except Exception as e:
            w = {"fehler": repr(e)}
        self._netzteil(w)
        if t >= self._naechste:
            self._naechste = t + self.ABSTAND_S
            self.verarbeiten(w, t)

    def _netzteil(self, w):
        """Netzteil eingesteckt? Nur der Wechsel von Akkubetrieb auf Netzteil macht die Ansage, nicht
        der Zustand beim Start (dort läuft der Startton) und nicht das Ausstecken. Zwei Messungen in
        Folge gegen Zittern um die Schwelle."""
        if w.get("fehler") or w.get("richtung") is None:
            return
        steckt = w["richtung"] in ("laedt", "voll")
        if self._netz is None or steckt == self._netz:
            self._netz, self._netz_zaehler = steckt, 0
            return
        self._netz_zaehler += 1
        if self._netz_zaehler < self.NETZ_MESSUNGEN:
            return
        self._netz, self._netz_zaehler = steckt, 0
        if steckt:
            self.log("Netzteil eingesteckt.")
            if self.ansage:
                self.ansage("netzteil")
        else:
            self.log("Netzteil abgezogen.")

    def verarbeiten(self, w, t):
        self.zeit = t
        if w.get("fehler"):
            if self.wert is None or self.wert.get("fehler"):
                self.wert = w                       # sonst den letzten guten Wert behalten
            return
        self.wert = w
        richtung = w.get("richtung")
        if richtung in ("laedt", "voll"):
            self._gewarnt, self._kritisch = False, 0
            return
        if w.get("prozent") is not None:
            self.prozent_ohne_netzteil = w["prozent"]
        if w.get("prozent") is not None and w["prozent"] <= self.WARNEN_PROZENT and not self._gewarnt:
            self._gewarnt = True
            self.log(f"Akku schwach ({w['spannung']:.2f} V, ca. {w['prozent']} %).")
            if self.ansage:
                self.ansage("akku_schwach")
        if w.get("spannung", 9) <= self.AUS_SPANNUNG:
            self._kritisch += 1
            if self._kritisch >= self.AUS_MESSUNGEN and not self._aus and self.ausschalten:
                self._aus = True
                self.log(f"Akku leer ({w['spannung']:.2f} V): Box wird sicher ausgeschaltet.")
                self.ausschalten("Akku leer", "akku_leer")
        else:
            self._kritisch = 0

    @property
    def status(self):
        if self.wert is None:
            return None
        return dict(self.wert, prozent_ohne_netzteil=self.prozent_ohne_netzteil)


if __name__ == "__main__":
    print(lesen())
