#!/usr/bin/env python3
"""Wache der Peppa Box im Sparzustand. Nur Standardbibliothek (und die Module der Box).

Der Pi 3A+ kann nicht schlafen (kein Suspend, nur „läuft“ oder „heruntergefahren“). Der Sparzustand ist
darum ein Betrieb mit möglichst wenig Last: Player, Eltern-Seite, Raspotify und WLAN-Suche sind beendet,
das WLAN ist aus (Hilfsprogramm sparen.sh, Dienst peppa-standby). Übrig bleibt dieses kleine Programm:

  - wartet auf die Ein-Taste (Pegel von SCL, GPIO 3; gedrückt = tief, 3 Proben in Folge = entprellt)
  - Taste: sofort Startton (Startlautstärke, ansagen/start.wav), gleichzeitig Dienst peppa-aufwachen
    (WLAN an, Player/Eltern-Seite/Raspotify starten); danach endet dieses Programm
  - nach `sparzustand.aus_nach_h` Stunden (Einstellung, Standard 6) schaltet es die Box ganz aus
  - prüft alle 15 s den Akku (wie der Player) und schaltet bei leerem Akku sauber aus
  - Fehler: klappt das Aufwecken nicht (sudo, systemd), neuer Versuch, zuletzt Neustart der Box;
    ein unerwarteter Fehler im Programm weckt die Box ebenfalls, sie darf nie tot im Sparzustand hängen

Die Taste, mit der man in den Sparzustand ging, wird erst beachtet, wenn sie losgelassen war (FREI_S).
Alle Geräte, Uhr und Befehle kommen von außen, damit sich alles ohne Hardware prüfen lässt
(test_sparzustand.py).
"""
import shutil
import subprocess
import sys
import time

import akku
import einstellungen
import gpio

SYSTEMCTL = shutil.which("systemctl") or "/usr/bin/systemctl"
TAKT_S = 0.05            # Taste 20 mal je Sekunde prüfen
PROBEN = 3               # so viele gleiche Proben nacheinander = Taste gedrückt (150 ms)
FREI_S = 0.5             # so lange muss die Taste nach dem Eintritt losgelassen sein
AUFWECKEN_VERSUCHE = 3
AUFWECKEN_PAUSE_S = 1.0
STANDARD_AUS_NACH_H = 6


def befehl_aufwecken():
    r = subprocess.run(["sudo", "-n", SYSTEMCTL, "start", "--no-block", "peppa-aufwachen.service"],
                       capture_output=True, text=True, timeout=30)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def befehl_ausschalten():
    r = subprocess.run(["sudo", "-n", SYSTEMCTL, "poweroff"], capture_output=True, text=True, timeout=60)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def befehl_neustart():
    r = subprocess.run(["sudo", "-n", SYSTEMCTL, "reboot"], capture_output=True, text=True, timeout=60)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def startton(log=print):
    import toene                       # erst hier: zieht Lautstärke und Ansagen nach, nicht für Tests nötig
    return toene.startton(log=log)


def aus_nach_s(einst=einstellungen):
    try:
        return int(einst.laden()["sparzustand"]["aus_nach_h"]) * 3600
    except Exception:
        return STANDARD_AUS_NACH_H * 3600


class Wache:
    def __init__(self, pegel, aufwecken=befehl_aufwecken, ton=startton, ausschalten=befehl_ausschalten,
                 neustart=befehl_neustart, akku_lesen=akku.lesen, aus_nach=None,
                 jetzt=time.monotonic, schlaf=time.sleep, log=print):
        self.pegel, self.aufwecken, self.ton = pegel, aufwecken, ton
        self.ausschalten_befehl, self.neustart_befehl = ausschalten, neustart
        self.jetzt, self.schlaf, self.log = jetzt, schlaf, log
        self.aus_nach = aus_nach if aus_nach is not None else aus_nach_s()
        self.akkuwache = akku.Akkuwache(lesen=akku_lesen, ansage=None, ausschalten=self._akku_leer, log=log)
        self.beginn = jetzt()
        self.ergebnis = None             # "aufgewacht" | "aus_zeit" | "aus_akku"
        self._frei_seit = None
        self._tief = 0
        self._aus_versucht = False
        self._bewaffnet = False          # erst nach FREI_S losgelassener Taste

    # ------------------------------------------------------------ Schritte

    def _taste_gedrueckt(self):
        w = self.pegel()
        return None if w is None else not w

    def aufwachen(self):
        """Box aufwecken: erst der Dienst (WLAN, Player …), dann der Ton – beides läuft gleichzeitig,
        der Ton ist das, was das Kind merkt. Klappt der Dienst nicht, mehrmals versuchen, zuletzt Neustart."""
        self.log("Ein-Taste: Box wacht auf.")
        ok = False
        for i in range(AUFWECKEN_VERSUCHE):
            try:
                ok, meldung = self.aufwecken()
            except Exception as e:
                ok, meldung = False, repr(e)
            if ok:
                break
            self.log(f"Aufwecken fehlgeschlagen ({i + 1}/{AUFWECKEN_VERSUCHE}): {meldung}")
            self.schlaf(AUFWECKEN_PAUSE_S)
        try:
            self.ton()
        except Exception as e:
            self.log(f"Startton: {e!r}")
        if not ok:
            self.log("Aufwecken nicht möglich: Box startet neu.")
            try:
                self.neustart_befehl()
            except Exception as e:
                self.log(f"Neustart: {e!r}")
        self.ergebnis = "aufgewacht"

    def _ganz_aus(self, grund, ergebnis):
        if self._aus_versucht:
            return
        self._aus_versucht = True
        self.log(f"Sparzustand: Box wird ganz ausgeschaltet ({grund}).")
        try:
            ok, meldung = self.ausschalten_befehl()
        except Exception as e:
            ok, meldung = False, repr(e)
        if ok:
            self.ergebnis = ergebnis
        else:
            self.log(f"Ausschalten fehlgeschlagen: {meldung}")
            self._aus_versucht = False        # beim nächsten Durchlauf noch einmal

    def _akku_leer(self, grund, ansage):
        self._ganz_aus(grund, "aus_akku")

    def schritt(self):
        """Ein Durchlauf. Setzt self.ergebnis, wenn der Sparzustand endet."""
        t = self.jetzt()
        g = self._taste_gedrueckt()
        if g is None:                                       # Taste nicht lesbar: nichts erkennen, Zeit läuft weiter
            self._tief = 0
        elif g:
            self._frei_seit = None
            self._tief += 1
            if self._tief >= PROBEN and self._bewaffnet:
                self.aufwachen()
                return
        else:
            self._tief = 0
            if self._frei_seit is None:
                self._frei_seit = t
            if t - self._frei_seit >= FREI_S:
                self._bewaffnet = True
        try:
            self.akkuwache.tick(t)
        except Exception as e:
            self.log(f"Akku-Wache: {e!r}")
        if t - self.beginn >= self.aus_nach:
            self._ganz_aus(f"{self.aus_nach // 3600} Std im Sparzustand", "aus_zeit")

    def lauf(self):
        self.log(f"Sparzustand: wartet auf die Ein-Taste, schaltet nach {self.aus_nach // 3600} Std ganz aus.")
        while self.ergebnis is None:
            self.schritt()
            if self.ergebnis is None:
                self.schlaf(TAKT_S)
        return self.ergebnis


def main():
    log = print
    try:
        leser = gpio.oeffnen(pins=(gpio.SCL,), log=log)
    except OSError as e:
        log(f"Sparzustand: GPIO nicht lesbar ({e}) – Box wird geweckt.")
        befehl_aufwecken()
        return 1
    w = Wache(lambda: leser.pegel(gpio.SCL), log=log)
    try:
        ergebnis = w.lauf()
    except Exception as e:                      # nie tot im Sparzustand hängen bleiben
        log(f"Sparzustand: unerwarteter Fehler {e!r} – Box wird geweckt.")
        try:
            ok, _ = befehl_aufwecken()
            if not ok:
                befehl_neustart()
        except Exception as e2:
            log(f"Aufwecken: {e2!r}")
        return 1
    finally:
        try:
            leser.close()
        except Exception:
            pass
    log(f"Sparzustand beendet: {ergebnis}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
