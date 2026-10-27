"""Automatik der Peppa Box: Schlummer-Timer, Ruhezeit, Auto-Aus und Lautstärke-Grenzen.

Läuft im Player: peppa_player.py ruft tick() jede Sekunde auf. Die Eltern-Seite ändert nur
Dateien (Einstellungen, Timer); ausgeführt wird hier. So überstehen Timer ein Update der Seite.

Abläufe
  Start            Startlautstärke einmal je Einschalten setzen (Markierung in /dev/shm)
  Schlummer-Timer  die letzten FADE_S Sekunden wird die Musik leiser, dann Pause, dann ist die
                   Lautstärke wieder wie vorher
  Ruhezeit         "leiser": Lautstärke höchstens leise_max. "aus": keine Musik (laufende Musik
                   wird pausiert, neue Karten starten nicht). Nach der Ruhezeit bleibt die
                   Lautstärke wie sie ist (nie von selbst lauter)
  Grenzen          Lautstärke über der Höchstlautstärke wird heruntergesetzt
  Auto-Aus         Box fährt herunter, wenn die eingestellte Zeit nichts gespielt wurde. Als
                   Aktivität zählt: Musik spielt, Eltern-Seite ist offen (Wartung, Update)

Spotify, Lautstärke, Einstellungen und Uhr kommen von außen, damit sich alles mit simulierter Zeit
testen lässt (test_automatik.py).
"""
import shutil
import subprocess
import time

FADE_S = 20             # so lange wird beim Schlummer-Timer ausgeblendet
ABFRAGE_S = 10          # Spotify fragen und Grenzen prüfen
SEITE_AKTIV_S = 120     # so lange zählt eine geöffnete Eltern-Seite als Aktivität
TIMER_GNADE_S = 60      # so lange nach Ablauf wird die Pause bei Fehlern wiederholt
SYSTEMCTL = shutil.which("systemctl") or "/usr/bin/systemctl"


def _poweroff():
    r = subprocess.run(["sudo", "-n", SYSTEMCTL, "poweroff"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError((r.stdout + r.stderr).strip() or f"Rückgabewert {r.returncode}")


class Automatik:
    def __init__(self, spotify, laut, einst, jetzt=time.time, schlaf=time.sleep,
                 ausschalten=_poweroff, log=print):
        self.spotify, self.laut, self.einst = spotify, laut, einst
        self.jetzt, self.schlaf, self.ausschalten, self.log = jetzt, schlaf, ausschalten, log
        self.spielt = None                       # letzter bekannter Zustand: True, False, None
        self.letzte_aktivitaet = jetzt()         # nach dem Einschalten bleibt die Box mindestens so lange an
        self._naechste_abfrage = 0.0
        self.status = {"ausgabe": laut.aktive_ausgabe(), "ruhezeit": False, "auto_aus_in": None}

    # ------------------------------------------------------------ Start

    def beim_start(self):
        """Startlautstärke setzen, aber nur einmal je Einschalten. Ein Neustart des Players
        (Update, 'Musik neu starten') ändert die laufende Lautstärke nicht."""
        if self.einst.lauf_lesen("gestartet"):
            return
        cfg = self.einst.laden()
        aus = self.laut.aktive_ausgabe()
        ziel = min(cfg["lautstaerke"][aus]["start"], self.einst.wirksames_max(cfg, aus, self.jetzt()))
        if self.laut.setzen(aus, ziel):
            self.log(f"Startlautstärke {ziel} % ({aus})")
        self.einst.lauf_schreiben("gestartet", {"zeit": self.jetzt()})

    # ------------------------------------------------------------ Abfragen vom Player

    def sperrt(self):
        """True, wenn der Player gerade keine Musik starten soll (Ruhezeit, Modus 'aus')."""
        return self.einst.musik_gesperrt(self.einst.laden(), self.jetzt())

    # ------------------------------------------------------------ jede Sekunde

    def tick(self, dev):
        jetzt = self.jetzt()
        cfg = self.einst.laden()
        aus = self.laut.aktive_ausgabe()

        abfrage = jetzt >= self._naechste_abfrage
        if abfrage:
            self._naechste_abfrage = jetzt + ABFRAGE_S
            try:
                self.spielt = self.spotify.spielt(dev)
            except Exception as e:                       # Netz weg: nichts Neues, alter Wert bleibt
                self.log(f"Spotify-Abfrage fehlgeschlagen: {e!r}")
                self.spielt = None
        if self.spielt is True:
            self.letzte_aktivitaet = jetzt

        self._timer(dev, aus, jetzt)

        ruhe = self.einst.ruhezeit_aktiv(cfg, jetzt)
        if abfrage:
            if self.einst.musik_gesperrt(cfg, jetzt) and self.spielt is True:
                status, _ = self.spotify.pause(dev)
                self.log(f"Ruhezeit: Musik pausiert (Spotify {status})")
                self.spielt = False
            self._grenzen(cfg, aus, jetzt)

        self._auto_aus(cfg, jetzt)
        self.status.update(ausgabe=aus, ruhezeit=ruhe)

    # ------------------------------------------------------------ Schlummer-Timer

    def _timer(self, dev, aus, jetzt):
        t = self.einst.lauf_lesen("timer")
        if not t:
            return
        rest = t["ende"] - jetzt
        if rest > 0:
            if rest <= FADE_S and self.spielt is True:
                self._ausblenden(t, aus, rest)
            return
        # Zeit ist um: pausieren (bei Fehlern kurz wiederholen), dann Lautstärke zurück
        fertig = jetzt - t["ende"] > TIMER_GNADE_S
        if self.spielt is not False:
            try:
                status, _ = self.spotify.pause(dev)
                fertig = fertig or status < 300 or status in (403, 404)   # 404: kein aktives Gerät
                self.log(f"Schlummer-Timer abgelaufen, Pause (Spotify {status})")
            except Exception as e:
                self.log(f"Schlummer-Timer: Pause fehlgeschlagen: {e!r}")
        else:
            fertig = True
        if fertig:
            self.spielt = False
            vorher = t.get("vorher")
            if vorher is not None:
                self.schlaf(1.5)                         # Spotify soll wirklich still sein, bevor es wieder laut wird
                self.laut.setzen(aus, vorher)
            self.einst.lauf_loeschen("timer")

    def _ausblenden(self, t, aus, rest):
        if t.get("vorher") is None:
            vorher = self.laut.lesen(aus)
            if vorher is None:
                return
            t["vorher"] = vorher                         # merken, falls der Player mittendrin neu startet
            if self.einst.lauf_lesen("timer") is None:   # inzwischen von der Seite abgebrochen
                return
            self.einst.lauf_schreiben("timer", t)
        self.laut.setzen(aus, t["vorher"] * rest / FADE_S)

    # ------------------------------------------------------------ Grenzen

    def _grenzen(self, cfg, aus, jetzt):
        t = self.einst.lauf_lesen("timer")
        if t and t.get("vorher") is not None:
            return                                       # Ausblenden läuft, nicht dazwischenfunken
        aktuell = self.laut.lesen(aus)
        grenze = self.einst.wirksames_max(cfg, aus, jetzt)
        if aktuell is not None and aktuell > grenze:
            self.laut.setzen(aus, grenze)
            self.log(f"Lautstärke {aktuell} % über der Grenze, auf {grenze} % gesetzt ({aus})")

    # ------------------------------------------------------------ Auto-Aus

    def _auto_aus(self, cfg, jetzt):
        seite = self.einst.lauf_alter("seite", jetzt)
        if seite is not None and seite < SEITE_AKTIV_S:
            self.letzte_aktivitaet = jetzt
        aa = cfg["auto_aus"]
        if not aa["an"]:
            self.status["auto_aus_in"] = None
            return
        rest = aa["minuten"] * 60 - (jetzt - self.letzte_aktivitaet)
        self.status["auto_aus_in"] = max(0, int(rest))
        if rest > 0:
            return
        self.log(f"Auto-Aus: seit {aa['minuten']} Minuten nichts gespielt, Box wird ausgeschaltet")
        self.letzte_aktivitaet = jetzt                   # falls es nicht klappt: erst nach der nächsten Frist wieder versuchen
        try:
            self.ausschalten()
        except Exception as e:
            self.log(f"Auto-Aus fehlgeschlagen: {e}")
