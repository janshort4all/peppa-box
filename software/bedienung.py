"""Bedienung am Gerät: vier Touchfelder (MPR121), Drehknopf, Ein-Taste, Kopfhörer-Erkennung, Akku.

Belegung (Verdrahtungsplan 08.11.2026; welche Elektrode welches Feld ist, steht in den Einstellungen):
  E0 zurück   antippen: vorheriger Titel        halten: zurückspulen (15 s alle 0,8 s)
  E1 Play     antippen: Pause / weiter (die Karte bleibt liegen)
              2 s halten: Karte von vorn (sonst immer an der gemerkten Stelle weiter)
  E2 vor      antippen: nächster Titel          halten: vorspulen
  E3 Mond     antippen: Schlummer-Timer 15 -> 30 -> 45 -> 60 Min -> aus, jeweils mit Ansage
              5 s halten: Akkustand ansagen
  Drehknopf   Lautstärke (2 % je Raste, Einstellung), nie über die Höchstlautstärke, nie unter 5 %
  Ein-Taste   ausgeschaltet: einschalten (das macht der Pi selbst: GPIO 3 nach Masse weckt ihn)
              kurz drücken: Akkustand ansagen
              2 s halten: „Tschüss“, Musik pausiert, beim Loslassen ausschalten
              (erst beim Loslassen, sonst weckte die noch gedrückte Taste den Pi sofort wieder)
Schutz gegen Fehlbedienung: Berührungen unter 70 ms lösen nichts aus (Rauschen, kein Finger; das
Protokoll zählt sie zusammengefasst); mehrere Felder gleichzeitig (Hand auf dem Deckel) lösen nichts aus;
ein Feld, das über 60 s „berührt“ meldet, wird neu kalibriert; eine Ein-Taste, die schon beim Start
gedrückt ist oder über 15 s gedrückt bleibt, schaltet nie aus.

Hardware: eigener Faden, alle 20 ms (Hardware.schritt). Touch-Chip über INT (P05) und zur
Sicherheit alle 0,25 s abgefragt; Ein-Taste über den Pegel von SCL (nur gelesen, wenn gerade keine
I2C-Übertragung läuft, 3 gleiche Proben = entprellt); fällt der Touch-Chip aus, wird er mit
wachsendem Abstand neu eingerichtet, ein hängender I2C-Bus wird freigetaktet.
Alle Abläufe bekommen Uhr und Geräte von außen, damit sie sich ohne Hardware prüfen lassen
(test_bedienung.py).
"""
import json
import threading
import time

import akku
import automatik
import gpio
import i2c
import mpr121

LANG_SPRUNG_S = 0.7       # vor/zurück so lange halten = spulen
SPUL_MS = 15000
SPUL_TAKT_S = 0.8
TIPP_MAX_S = 1.5          # länger gehalten = kein Antippen (Play, Mond)
VON_VORN_S = 2.0          # Play so lange halten: Karte von vorn (sonst geht es an der gemerkten Stelle weiter)
TIPP_MIN_S = 0.07         # kürzer = kein Finger, sondern Rauschen (Phantom-Berührung, Befund 09.11.2026)
KURZ_MELDEN_S = 60.0      # ignorierte Phantom-Berührungen höchstens so oft zusammengefasst melden
AKKU_HALTEN_S = 5.0
AUS_HALTEN_S = 2.0
TASTE_MIN_S = 0.05
TASTE_KLEMMT_S = 15.0
TIMER_STUFEN = (15, 30, 45, 60)
KNOPF_MIN = 5
SPERRE_ANSAGE_S = {"karte_auflegen": 8, "ruhezeit": 8, "karte_leer": 3, "akku_unbekannt": 3}

TAKT_S = 0.02
SCL_PROBEN = 3
TOUCH_ABFRAGE_S = 0.25
TOUCH_PRUEFEN_S = 5.0
TOUCH_KLEMMT_S = 60.0
INT_HAENGT_S = 2.0
NEU_VERSUCH_S = [1, 2, 5, 10, 30, 60]
SEITE_OFFEN_S = 5.0
STUMM_PRUEFEN_S = 2.0
LIVE_MIN_S, LIVE_MAX_S = 0.2, 2.0


# ====================================================================== Logik

class Bedienung:
    def __init__(self, st, auto, regler, einst, sagen, akku_info, herunterfahren, karte,
                 jetzt=time.monotonic, uhr=time.time, log=print, timer=automatik, laut=None):
        self.st, self.auto, self.regler, self.einst = st, auto, regler, einst
        self.sagen_roh, self.akku_info, self.herunterfahren, self.karte = sagen, akku_info, herunterfahren, karte
        self.jetzt, self.uhr, self.log, self.timer, self.laut = jetzt, uhr, log, timer, laut
        self.gesten = {}                 # Feld -> {"start", "lang", "naechster"}
        self.mehrfach = False
        self.kurz = {}                   # Feld -> Anzahl ignorierter Phantom-Berührungen seit der letzten Meldung
        self.kurz_gesamt = 0
        self._kurz_gemeldet = None
        self._angesagt = {}
        # Ein-Taste
        self.taste_gesperrt = None       # None = noch kein Wert; True = beim Start gedrückt, erst loslassen
        self.taste_start = None
        self.taste_aus = False
        self.taste_klemmt = False

    # ------------------------------------------------------------ Hilfen

    def _sagen(self, name):
        t = self.jetzt()
        sperre = SPERRE_ANSAGE_S.get(name)
        if sperre and t - self._angesagt.get(name, -1e9) < sperre:
            return
        self._angesagt[name] = t
        self.sagen_roh(name)

    def akku_ansagen(self):
        try:
            info = self.akku_info()
        except Exception:
            info = None
        self._sagen(akku.ansage_name(info))

    # ------------------------------------------------------------ Touchfelder

    def felder(self, beruehrt, t):
        """Aktuell berührte Felder (Menge von Namen). Löst beim Loslassen die kurzen Gesten aus."""
        neu = set(beruehrt)
        if len(neu) >= 2 and not self.mehrfach:
            self.mehrfach = True
            self.log(f"Mehrere Felder gleichzeitig ({', '.join(sorted(neu))}) – nichts ausgelöst.")
        for f in set(self.gesten) - neu:
            self._los(f, t)
        for f in neu - set(self.gesten):
            self.gesten[f] = {"start": t, "lang": False, "naechster": None}
        if not neu:
            self.mehrfach = False

    def felder_abbrechen(self):
        """Touch-Chip ausgefallen: laufende Gesten verwerfen, ohne etwas auszulösen."""
        self.gesten.clear()
        self.mehrfach = False

    def _los(self, f, t):
        g = self.gesten.pop(f)
        if self.mehrfach or g["lang"]:
            return
        dauer = t - g["start"]
        if dauer < TIPP_MIN_S:
            self._kurz(f, t)
            return
        if f == "play" and dauer < TIPP_MAX_S:
            self._play()
        elif f in ("vor", "zurueck") and dauer < LANG_SPRUNG_S:
            self.st.taste_springen(+1 if f == "vor" else -1)
        elif f == "schlaf" and dauer < TIPP_MAX_S:
            self._timer_weiter()

    def _kurz(self, f, t):
        """Zu kurze Berührung: nichts auslösen, aber zählen (zeigt, ob ein Feld rauscht)."""
        self.kurz[f] = self.kurz.get(f, 0) + 1
        self.kurz_gesamt += 1
        if self._kurz_gemeldet is None:
            self._kurz_gemeldet = t - KURZ_MELDEN_S          # erste gleich melden
        self.kurz_melden(t)

    def kurz_melden(self, t, immer=False):
        if not self.kurz or (not immer and t - self._kurz_gemeldet < KURZ_MELDEN_S):
            return
        teile = ", ".join(f"{k} {n}×" for k, n in sorted(self.kurz.items()))
        self.log(f"Touch: zu kurze Berührungen ignoriert ({teile}) – Rauschen, kein Finger.")
        self.kurz.clear()
        self._kurz_gemeldet = t

    def _play(self):
        if self.auto.sperrt():
            self._sagen("ruhezeit")
            return
        r = self.st.taste_play()
        if r == "keine_karte":
            liegt, _ = self.karte()
            if liegt:
                self._sagen("karte_leer")
            else:   # keine Ansage "Leg eine Karte auf" (Wunsch Jan 08.11.: nervt, v. a. bei Fehlberuehrungen)
                self.log("Play-Feld ohne Karte – nichts zu tun.")
        else:
            self.log("Play-Feld: " + ("Pause" if r == "pause" else "weiter"))

    def _timer_weiter(self):
        laufend = self.einst.lauf_lesen("timer")
        if laufend:
            m = laufend.get("minuten") or 0
            neu = next((s for s in TIMER_STUFEN if s > m), None)
        else:
            neu = TIMER_STUFEN[0]
        if neu:
            self.timer.timer_starten(neu, self.laut, self.einst, jetzt=self.uhr())
            self.log(f"Mond-Feld: Schlummer-Timer {neu} Min.")
            self._sagen(f"timer_{neu}")
        else:
            self.timer.timer_abbrechen(self.laut, self.einst)
            self.log("Mond-Feld: Schlummer-Timer aus.")
            self._sagen("timer_aus")

    # ------------------------------------------------------------ Drehknopf

    def drehen(self, schritte):
        cfg = self.einst.laden()["bedienung"]
        if cfg["drehknopf_umkehren"]:
            schritte = -schritte
        self.regler.aendern(schritte * cfg["drehknopf_schritt"])

    # ------------------------------------------------------------ Ein-Taste

    def ein_taste(self, gedrueckt, t):
        if self.taste_gesperrt is None:
            self.taste_gesperrt = bool(gedrueckt)
            if gedrueckt:
                self.log("Ein-Taste ist beim Start gedrückt – wird erst nach dem Loslassen beachtet.")
            return
        if gedrueckt:
            if self.taste_gesperrt:
                return
            if self.taste_start is None:
                self.taste_start = t
            dauer = t - self.taste_start
            if dauer >= TASTE_KLEMMT_S:
                if not self.taste_klemmt:
                    self.taste_klemmt, self.taste_aus = True, False
                    self.log("Ein-Taste über 15 s gedrückt – klemmt sie? Es wird nicht ausgeschaltet.")
                return
            if dauer >= AUS_HALTEN_S and not self.taste_aus and not self.taste_klemmt:
                self.taste_aus = True
                self.log("Ein-Taste 2 s gehalten: Box geht beim Loslassen aus.")
                self.st.pausieren()
                self._sagen("tschuess")
            return
        # losgelassen
        if self.taste_gesperrt:
            self.taste_gesperrt = False
            return
        if self.taste_start is None:
            return
        dauer, self.taste_start = t - self.taste_start, None
        if self.taste_klemmt:
            self.taste_klemmt = False
            return
        if self.taste_aus:
            self.taste_aus = False
            self.herunterfahren("Ein-Taste", None)        # „Tschüss“ lief schon
            return
        if dauer >= TASTE_MIN_S:
            self.akku_ansagen()

    # ------------------------------------------------------------ Zeitabhängiges (jeder Durchlauf)

    def tick(self, t):
        self.kurz_melden(t)
        if self.mehrfach:
            return
        for f, g in self.gesten.items():
            d = t - g["start"]
            if f in ("vor", "zurueck") and d >= LANG_SPRUNG_S:
                if g["naechster"] is None or t >= g["naechster"]:
                    g["lang"] = True
                    g["naechster"] = t + SPUL_TAKT_S
                    self.st.taste_spulen(SPUL_MS if f == "vor" else -SPUL_MS)
            elif f == "schlaf" and d >= AKKU_HALTEN_S and not g["lang"]:
                g["lang"] = True
                self.akku_ansagen()
            elif f == "play" and d >= VON_VORN_S and not g.get("vorn"):
                g["lang"] = g["vorn"] = True
                if self.st.von_vorn():
                    self.log("Play-Feld 2 s gehalten: Karte von vorn.")
            elif f == "play" and d >= TIPP_MAX_S:
                g["lang"] = True                           # zu lang für ein Antippen: nichts


# ====================================================================== Lautstärke

class Regler:
    """Lautstärke vom Drehknopf in eigenem Faden: Rasten werden gesammelt (amixer braucht ca. 20 ms),
    die Grenze gilt sofort. Unter KNOPF_MIN wird nicht gedreht (Box wirkt sonst kaputt)."""

    def __init__(self, laut, einst, uhr=time.time, log=print):
        self.laut, self.einst, self.uhr, self.log = laut, einst, uhr, log
        self._bed = threading.Condition()
        self._offen = 0
        self.zuletzt = None
        self._faden = None

    def aendern(self, delta):
        with self._bed:
            self._offen += delta
            self._bed.notify_all()

    def starten(self):
        self._faden = threading.Thread(target=self._lauf, name="lautstaerke", daemon=True)
        self._faden.start()

    def lebt(self):
        return self._faden is not None and self._faden.is_alive()

    def _lauf(self):
        while True:
            with self._bed:
                while not self._offen:
                    self._bed.wait()
                delta, self._offen = self._offen, 0
            try:
                self.anwenden(delta)
            except Exception as e:
                self.log(f"Lautstärke: Fehler {e!r}")
                time.sleep(0.5)

    def anwenden(self, delta):
        aus = self.laut.aktive_ausgabe()
        aktuell = self.laut.lesen(aus)
        if aktuell is None:
            return None
        grenze = self.einst.wirksames_max(self.einst.laden(), aus, self.uhr())
        if delta > 0:
            ziel = min(grenze, max(KNOPF_MIN, aktuell + delta))
        else:
            ziel = max(min(aktuell, KNOPF_MIN), aktuell + delta)
        if ziel != aktuell:
            self.laut.setzen(aus, ziel)
        self.zuletzt = ziel
        return ziel


# ====================================================================== Hardware-Abfrage

class Hardware:
    def __init__(self, bedienung, ausgang, akkuwache, einst, drehgeber=None, log=print,
                 gpio_oeffnen=None, bus_oeffnen=i2c.I2C, mpr_klasse=mpr121.MPR121,
                 befreien=i2c.befreien, pins_setzen=gpio.pinctrl_setzen, jetzt=time.monotonic,
                 uhr=time.time, schlaf=time.sleep):
        self.bed, self.ausgang, self.akkuwache, self.einst = bedienung, ausgang, akkuwache, einst
        self.drehgeber, self.log = drehgeber, log
        self.gpio_oeffnen = gpio_oeffnen or (lambda: gpio.oeffnen(log=log))
        self.bus_oeffnen, self.mpr_klasse, self.befreien = bus_oeffnen, mpr_klasse, befreien
        self.pins_setzen, self.jetzt, self.uhr, self.schlaf = pins_setzen, jetzt, uhr, schlaf
        self.gpio = None
        self._gpio_naechster = 0.0
        self._gpio_gemeldet = False
        self.bus = None
        self.mpr = None
        self._mpr_naechster = 0.0
        self._mpr_versuche = 0
        self._mpr_schwellen = None
        self._mpr_fehler = 0
        self.touch_fehler = None
        self._gemeldet = None
        self._touch_naechste = 0.0
        self._pruef_naechste = 0.0
        self._roh_naechste = 0.0
        self._int_seit = None
        self._int_haengt = False
        self._beruehrt_seit = {}
        self.maske = 0
        self.beruehrt = set()
        self.roh = None
        self.int_tief = False
        self._scl_tief = self._scl_hoch = 0
        self.scl = 1
        self.taste = None
        self._stumm_naechste = 0.0
        self._live_alt, self._live_zeit = None, -1e9
        self.lebenszeichen = jetzt()
        self._faden = None

    # ------------------------------------------------------------ Faden

    def starten(self):
        self._faden = threading.Thread(target=self.lauf, name="bedienung", daemon=True)
        self._faden.start()

    def lebt(self):
        return self._faden is not None and self._faden.is_alive()

    def lauf(self):
        while True:
            beginn = self.jetzt()
            try:
                self.schritt(beginn)
            except Exception as e:                         # darf nie sterben
                self._melden(f"Bedienung: unerwarteter Fehler {e!r}")
                self.schlaf(0.5)
            self.schlaf(max(0.002, TAKT_S - (self.jetzt() - beginn)))

    def _melden(self, text):
        if text != self._gemeldet:
            self.log(text)
            self._gemeldet = text

    # ------------------------------------------------------------ ein Durchlauf

    def schritt(self, t):
        self.lebenszeichen = t
        cfg = self.einst.laden()
        if self.gpio is None and t >= self._gpio_naechster:
            self._gpio_einrichten(t)
        w = self._pegel()
        frei = w is not None and self.scl and not self.taste     # I2C nur, wenn die Taste nicht gedrückt ist
        if w is None:
            frei = True                                           # ohne GPIO: Taste unbekannt, I2C trotzdem
        if self.taste is not None:
            self.bed.ein_taste(self.taste, t)
        if frei:
            self._touch(w, t, cfg)
            self.akkuwache.tick(t)
        if w is not None:
            self.ausgang.tick((w >> gpio.KLINKE) & 1, t)
            if t >= self._stumm_naechste:
                self._stumm_naechste = t + STUMM_PRUEFEN_S
                self.ausgang.stumm_halten(self.gpio)
        self.bed.tick(t)
        self._live(t)

    def _gpio_einrichten(self, t):
        try:
            self.gpio = self.gpio_oeffnen()
        except Exception as e:
            self.gpio = None
            self._gpio_naechster = t + 10
            if not self._gpio_gemeldet:
                self._gpio_gemeldet = True
                self.log(f"GPIO nicht lesbar ({e!r}): Ein-Taste und Kopfhörer-Erkennung aus, Touch ohne INT.")
            return
        self._gpio_gemeldet = False
        for pin in (gpio.KLINKE, gpio.MPR_INT):                   # falls config.txt noch nicht gilt
            self.pins_setzen(pin, "ip", "pu", log=self.log)

    def _pegel(self):
        """Pegel aller Pins; SCL nur, wenn dieser Prozess gerade nicht über I2C sendet."""
        if self.gpio is None:
            return None
        if not i2c.SPERRE.acquire(blocking=False):
            return None
        try:
            w = self.gpio.pegel_alle()
        except Exception as e:
            self.log(f"GPIO-Pegel nicht lesbar: {e!r}")
            self.gpio = None
            return None
        finally:
            i2c.SPERRE.release()
        self.scl = (w >> gpio.SCL) & 1
        if self.scl:
            self._scl_hoch, self._scl_tief = self._scl_hoch + 1, 0
        else:
            self._scl_tief, self._scl_hoch = self._scl_tief + 1, 0
        if self._scl_tief >= SCL_PROBEN:
            self.taste = True
        elif self._scl_hoch >= SCL_PROBEN:
            self.taste = False
        return w

    # ------------------------------------------------------------ Touch

    def _mpr_einrichten(self, t, cfg):
        b = cfg["bedienung"]
        schwellen = (b["touch_schwelle"], b["touch_loslassen"])
        try:
            if self.bus is None:
                self.bus = self.bus_oeffnen()
            m = self.mpr_klasse(self.bus)
            m.einrichten(*schwellen)
        except Exception as e:
            self.mpr = None
            warte = NEU_VERSUCH_S[min(self._mpr_versuche, len(NEU_VERSUCH_S) - 1)]
            self._mpr_versuche += 1
            self._mpr_naechster = t + warte
            self.touch_fehler = f"{e}"
            self._melden(f"Touch-Chip nicht bereit ({e}), neuer Versuch in {warte} s.")
            if self.gpio is not None and isinstance(e, OSError):
                try:
                    self.befreien(self.gpio, log=self.log)
                except Exception:
                    pass
            return
        self.mpr, self._mpr_schwellen = m, schwellen
        self._mpr_versuche = self._mpr_fehler = 0
        self._beruehrt_seit.clear()
        self.touch_fehler = None
        self._gemeldet = None
        self.log(f"Touch-Chip bereit (Schwelle {schwellen[0]}, loslassen {schwellen[1]}).")

    def _touch(self, w, t, cfg):
        if self.mpr is not None:
            b = cfg["bedienung"]
            if (b["touch_schwelle"], b["touch_loslassen"]) != self._mpr_schwellen:
                self.log("Touch-Empfindlichkeit geändert, Chip wird neu eingestellt.")
                self.mpr = None
                self._mpr_naechster = t
        if self.mpr is None:
            if t >= self._mpr_naechster:
                self._mpr_einrichten(t, cfg)
            if self.mpr is None:
                self.bed.felder_abbrechen()
                self.maske, self.beruehrt = 0, set()
                return
        self.int_tief = w is not None and not (w >> gpio.MPR_INT) & 1
        if self.int_tief:
            self._int_seit = self._int_seit if self._int_seit is not None else t
            if t - self._int_seit > INT_HAENGT_S and not self._int_haengt:
                self._int_haengt = True
                self.log("Touch: INT (P05) bleibt tief – frage nur noch regelmäßig ab.")
        else:
            self._int_seit, self._int_haengt = None, False
        faellig = (self.int_tief and not self._int_haengt) or t >= self._touch_naechste
        try:
            if t >= self._pruef_naechste:
                self._pruef_naechste = t + TOUCH_PRUEFEN_S
                self.mpr.pruefen()
            if self._seite_offen(t) and t >= self._roh_naechste:
                self._roh_naechste = t + TOUCH_ABFRAGE_S
                self.roh = self.mpr.rohwerte()
            elif not self._seite_offen(t):
                self.roh = None
            if not faellig:
                return
            maske = self.mpr.beruehrt()
        except OSError as e:
            if self.taste or self._taste_jetzt():
                return                                         # Ein-Taste hält SCL: erwartet
            self._mpr_fehler += 1
            if self._mpr_fehler >= 3 or isinstance(e, mpr121.Fehler):
                self._melden(f"Touch-Chip: {e} – wird neu eingerichtet.")
                self.touch_fehler = str(e)
                self.mpr = None
                self._mpr_naechster = t + 0.5
            return
        self._mpr_fehler = 0
        self._touch_naechste = t + TOUCH_ABFRAGE_S
        for e in range(4):
            if maske & (1 << e):
                self._beruehrt_seit.setdefault(e, t)
            else:
                self._beruehrt_seit.pop(e, None)
        klemmt = [e for e, s in self._beruehrt_seit.items() if t - s > TOUCH_KLEMMT_S]
        if klemmt:
            self.log(f"Touchfeld E{klemmt[0]} meldet seit über {int(TOUCH_KLEMMT_S)} s Berührung – neu kalibriert.")
            try:
                self.mpr.neu_kalibrieren()
            except OSError:
                self.mpr = None
            self._beruehrt_seit.clear()
            maske = 0
        self._felder_melden(maske, t, cfg)

    def _taste_jetzt(self):
        """Frisch gelesen: zieht die Ein-Taste gerade SCL nach Masse? (z. B. während einer Übertragung gedrückt)"""
        if self.gpio is None:
            return False
        try:
            return not (self.gpio.pegel_alle() >> gpio.SCL) & 1
        except Exception:
            return False

    def _felder_melden(self, maske, t, cfg):
        zuordnung = {nr: name for name, nr in cfg["bedienung"]["felder"].items()}
        self.maske = maske
        self.beruehrt = {zuordnung[e] for e in range(4) if maske & (1 << e) and e in zuordnung}
        self.bed.felder(self.beruehrt, t)

    def _seite_offen(self, t):
        alter = self.einst.lauf_alter("seite-bedienung", self.uhr())
        return alter is not None and alter < SEITE_OFFEN_S

    # ------------------------------------------------------------ Eltern-Seite (live)

    def _zu_kurz(self):
        n = getattr(self.bed, "kurz_gesamt", 0)
        return n if isinstance(n, int) else 0

    def live(self):
        d = self.drehgeber
        return {
            "touch": {"ok": self.mpr is not None, "fehler": self.touch_fehler, "beruehrt": sorted(self.beruehrt),
                      "maske": self.maske, "int": self.int_tief, "roh": self.roh,
                      "zu_kurz": self._zu_kurz()},
            "taste": {"gedrueckt": bool(self.taste), "bekannt": self.gpio is not None},
            "drehknopf": {"art": d.art if d else None, "schritte": d.schritte if d else 0,
                          "letzter": d.letzter if d else 0},
            "klinke": self.ausgang.status,
            "akku": self.akkuwache.status,
            "gpio": self.gpio is not None,
        }

    def _live(self, t):
        if t - self._live_zeit < LIVE_MIN_S:
            return
        daten = self.live()
        text = json.dumps(daten, sort_keys=True, default=str)
        if text == self._live_alt and t - self._live_zeit < LIVE_MAX_S:
            return
        self._live_alt, self._live_zeit = text, t
        self.einst.lauf_schreiben("bedienung", dict(daten, zeit=self.uhr()))

    # ------------------------------------------------------------ Ausschalten

    def schlafen(self):
        """Touch-Chip in den Stopp-Betrieb (vor dem Ausschalten)."""
        if self.mpr is None:
            return
        if i2c.SPERRE.acquire(timeout=1):
            try:
                self.mpr.schlafen()
            except OSError:
                pass
            finally:
                i2c.SPERRE.release()
