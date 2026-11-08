"""Spotify-Steuerung der Peppa Box: setzt um, was die Karte will, und repariert Fehler selbst.

Grundidee: Der Kartenleser meldet nur einen WUNSCH ("spiele Link X" oder "Pause"). Die Steuerung
läuft in einem eigenen Faden, setzt immer nur den neuesten Wunsch um und PRÜFT danach, ob wirklich
Musik läuft. Klappt etwas nicht, arbeitet sie eine Leiter von Gegenmaßnahmen ab, solange die Karte
liegt. Das Kind muss nie etwas tun; Eltern sehen im Protokoll, was passiert ist.

Abgefangen wird
  Schnelle Kartenwechsel   Wünsche werden zusammengefasst, Startbefehle mit Mindestabstand
                           (START_ABSTAND); nur der zuletzt gewünschte Link wird gestartet.
  Spotify antwortet 5xx    (z. B. 502 "Bad gateway": Spotify erreicht die Box nicht) -> kurz
                           wiederholen, dann Raspotify neu starten und erneut abspielen.
  Befehl angenommen, aber  Prüfung nach jedem Start: läuft der Titel auf DIESER Box und rückt die
  keine Musik              Position vor? Sonst: frisch abspielen, dann Raspotify neu starten.
                           (Fall 03.11.2026: Box springt sofort auf Pause.)
  Gerät fehlt              Gerät neu suchen; fehlt es zu lange, Raspotify neu starten. Eine Karte,
                           die vor "bereit" aufgelegt wird, startet, sobald die Box bereit ist.
  Raspotify abgestürzt     Neustart wird am Startzeitpunkt des Dienstes erkannt; lag eine Karte
  während Musik läuft      und lief Musik, geht es an derselben Stelle weiter.
  Ton-Mischer weg          Läuft peppa-stille nicht, wird es vor Raspotify neu gestartet.
  401 / 429 / Netz weg     Token erneuern / Wartezeit von Spotify einhalten / mit wachsendem
                           Abstand wiederholen (nie Dauerfeuer).
  Pause durch Automatik    (Schlummer-Timer, Ruhezeit) gilt als gewollt: keine "Reparatur".
  Tasten im Deckel         Play = Pause/Weiter bei liegender Karte (Karte weg nach Tasten-Pause
                           ändert nichts), vor/zurück = Titel springen, Halten = spulen. Befehle
                           werden zusammengefasst und nur gesendet, solange Musik zur Karte läuft.
  Kopfhörer ein/aus        Raspotify wird mit dem anderen Ausgang neu gestartet (ausfuehren() vom
                           Player); lief Musik, geht es an derselben Stelle weiter.

Grenzen: Raspotify-Neustarts höchstens alle NEUSTART_ABSTAND Sekunden. Ist die Spotify-Anmeldung
abgelaufen, hilft nur spotify_login.py; das steht dann im Zustand für die Eltern-Seite.

Alles Äußere (Spotify, Dienste, Uhr) wird übergeben, damit sich die Abläufe mit simulierter Zeit
prüfen lassen (test_steuerung.py).
"""
import os
import shutil
import subprocess
import threading
import time

START_ABSTAND = 2.5        # s zwischen zwei Startbefehlen (gegen Dauerfeuer bei schnellen Kartenwechseln)
BEFEHL_ABSTAND = 0.5       # s zwischen beliebigen Befehlen
PRUEF_ERSTE = 2.0          # s nach dem Start bis zur ersten Prüfung
PRUEF_ABSTAND = 2.0
PRUEF_MAX = 4              # Prüfungen je Start (ca. 8 s; Musik läuft normal nach 4 s sicher)
GERAET_FRISCH = 30         # so lange gilt eine gefundene Geräte-ID ohne neue Suche (im Leerlauf)
GERAET_FEHLT_NEUSTART = 45     # Karte wartet, Gerät fehlt so lange -> Raspotify neu starten
LEERLAUF_FEHLT_NEUSTART = 180  # ohne Karte: Gerät fehlt so lange -> Raspotify neu starten
LEERLAUF_PRUEFUNG = 60     # im Leerlauf so oft nach dem Gerät sehen
NEUSTART_ABSTAND = 120     # höchstens ein Raspotify-Neustart je ... Sekunden
NACH_NEUSTART = 6          # s nach einem Neustart, bevor nach dem Gerät gefragt wird
WACHE_ABSTAND = 5          # s: Startzeit von Raspotify vergleichen (Absturz erkennen, nur lokal)
WARTEN = [2, 5, 15, 30, 60, 120, 300]   # Abstände bei wiederholten Fehlern
NACH_UMSTELLUNG = 3        # s nach dem Ausgangswechsel, bevor nach dem Gerät gefragt wird
SPRUNG_MAX = 5             # so viele Titelsprünge werden höchstens vorgemerkt
SYSTEMCTL = shutil.which("systemctl") or "/usr/bin/systemctl"
LOKAL_MIN_PROZENT = 2.0     # librespot rechnet mindestens so viel (% eines Kerns) -> dekodiert gerade Musik


class LibrespotLast:
    """Lokaler Beleg, dass Raspotify gerade Musik dekodiert: Rechenzeit des Prozesses librespot.
    Hintergrund (08.11.2026): Die Spotify-Web-API meldete bei hörbarer Musik "spielt: nein" und eine
    stehende Position; die Prüfung startete deshalb immer wieder neu. Beim Spielen braucht librespot
    einige Prozent CPU (gesehen: 7,7 %), in Pause praktisch nichts.
    Aufruf liefert True/False, None wenn (noch) nicht messbar (kein Prozess, erste Messung)."""

    def __init__(self, proc="/proc", jetzt=time.monotonic, tick=None):
        self.proc, self.jetzt = proc, jetzt
        try:
            self.tick = tick or os.sysconf("SC_CLK_TCK")
        except (ValueError, OSError, AttributeError):
            self.tick = 100
        self.vorher = None          # (pid, ticks, zeit)

    def _pid(self):
        try:
            for name in os.listdir(self.proc):
                if name.isdigit():
                    try:
                        with open(os.path.join(self.proc, name, "comm")) as f:
                            if f.read().strip() == "librespot":
                                return name
                    except OSError:
                        continue
        except OSError:
            pass
        return None

    def _ticks(self, pid):
        try:
            with open(os.path.join(self.proc, pid, "stat")) as f:
                felder = f.read().rsplit(")", 1)[1].split()
            return int(felder[11]) + int(felder[12])    # utime + stime (Feld 14, 15)
        except (OSError, IndexError, ValueError):
            return None

    def __call__(self):
        pid = self._pid()
        t = self.jetzt()
        ticks = self._ticks(pid) if pid else None
        vorher, self.vorher = self.vorher, (pid, ticks, t) if ticks is not None else None
        if ticks is None or not vorher or vorher[0] != pid or t - vorher[2] < 0.5:
            return None
        prozent = (ticks - vorher[1]) / self.tick / (t - vorher[2]) * 100
        return prozent >= LOKAL_MIN_PROZENT


# ---------------------------------------------------------------- Dienste (echte Umsetzung)

class Dienste:
    """systemd-Zugriffe. Neustarts über die sudo-Freigabe aus dienst_einrichten.sh."""

    def _lauf(self, args, zeit=30):
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=zeit)
            return r.returncode, (r.stdout + r.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as e:
            return 1, repr(e)

    def neu_starten(self, name):
        code, aus = self._lauf(["sudo", "-n", SYSTEMCTL, "restart", name], zeit=60)
        return code == 0, aus

    def aktiv(self, name):
        """True/False; None, wenn es den Dienst nicht gibt."""
        code, aus = self._lauf([SYSTEMCTL, "show", "-p", "LoadState,ActiveState", name], zeit=10)
        werte = dict(z.split("=", 1) for z in aus.splitlines() if "=" in z)
        if werte.get("LoadState") != "loaded":
            return None
        return werte.get("ActiveState") in ("active", "activating", "reloading")

    def startzeit(self, name):
        """Kennung des letzten Starts (ändert sich bei jedem Neustart), None wenn unbekannt."""
        code, aus = self._lauf([SYSTEMCTL, "show", "-p", "ActiveEnterTimestampMonotonic", name], zeit=10)
        wert = aus.partition("=")[2].strip()
        return wert if code == 0 and wert not in ("", "0") else None


# ---------------------------------------------------------------- Steuerung

class Steuerung:
    def __init__(self, spotify, dienste=None, geraet="Peppa Box", jetzt=time.monotonic,
                 log=print, bei_bereit=None, lokal=None):
        self.sp, self.dienste = spotify, dienste or Dienste()
        self.lokal = lokal or (lambda: None)   # Messfühler: spielt Raspotify wirklich? (LibrespotLast)
        self.geraet, self.jetzt, self.log, self.bei_bereit = geraet, jetzt, log, bei_bereit
        self._sperre = threading.Condition()
        # Wunsch (vom Kartenleser) und erreichter Zustand
        self.wunsch = None          # None | ("spielen", uri) | ("pause", None)
        self.wunsch_nr = 0
        self.ist = None             # None | ("spielt", uri) | ("startet", uri) | ("pause", uri)
        self.erledigt_nr = 0
        # Gerät
        self.dev = None
        self.dev_zeit = -1e9
        self.dev_fehlt_seit = None
        self.bereit = False
        # Ablauf
        self.phase = "frei"         # frei | pruefen
        self.naechster_versuch = 0.0
        self.letzter_befehl = -1e9
        self.letzter_start = -1e9
        self.fehler = 0             # Fehlschläge für den aktuellen Wunsch
        self.letzter_neustart = -1e9
        self.neustart_wartet_bis = 0.0
        self.pruef = None           # dict während der Prüfung
        self.naechste_leerlauf = 0.0
        self.naechste_wache = 0.0
        self.raspotify_start = None
        self.problem = None         # Klartext für die Eltern-Seite
        self.problem_art = None     # netz | anmeldung | geraet | spotify (für Ansagen)
        self._gemeldet = None       # gegen Wiederholung derselben Meldung
        self.nach_neustart_uebertragen = False
        # Tasten und Ausgang
        self.karte_uri = None       # Link der liegenden Karte (auch nach Tasten-Pause)
        self.wunsch_zeit = None     # seit wann der aktuelle "spielen"-Wunsch besteht
        self.sprung = 0             # vorgemerkte Titelsprünge (+ vor, - zurück)
        self.spul_ms = 0            # vorgemerktes Spulen
        self.umstellung = None      # (ziel, ausfuehren): Ausgang wechseln

    # ------------------------------------------------------------ vom Kartenleser / der Automatik

    def karte_auf(self, uri):
        with self._sperre:
            self.karte_uri = uri
            self._wunsch_setzen(("spielen", uri))

    def karte_weg(self):
        with self._sperre:
            self.karte_uri = None
            if self.wunsch and self.wunsch[0] == "spielen":
                self._wunsch_setzen(("pause", None))

    # ------------------------------------------------------------ Tasten im Deckel

    def taste_play(self):
        """Play/Pause. Gibt "pause", "weiter" oder "keine_karte" zurück."""
        with self._sperre:
            if self.wunsch and self.wunsch[0] == "spielen":
                self._wunsch_setzen(("pause", None))
                return "pause"
            if self.karte_uri:
                self._wunsch_setzen(("spielen", self.karte_uri))
                return "weiter"
            return "keine_karte"

    def pausieren(self):
        """Pause wünschen, die Karte bleibt gemerkt (Ein-Taste vor dem Ausschalten). True, wenn etwas lief."""
        with self._sperre:
            if self.wunsch and self.wunsch[0] == "spielen":
                self._wunsch_setzen(("pause", None))
                return True
            return False

    def _laeuft(self):
        return (self.wunsch is not None and self.wunsch[0] == "spielen"
                and self.ist is not None and self.ist[0] in ("spielt", "startet"))

    def taste_springen(self, richtung):
        """Titel vor (+1) / zurück (-1). Nur, solange Musik zur Karte läuft. True = vorgemerkt."""
        with self._sperre:
            if not self._laeuft():
                return False
            self.sprung = max(-SPRUNG_MAX, min(SPRUNG_MAX, self.sprung + (1 if richtung > 0 else -1)))
            self._sperre.notify_all()
            return True

    def taste_spulen(self, ms):
        with self._sperre:
            if not self._laeuft():
                return False
            self.spul_ms += int(ms)
            self._sperre.notify_all()
            return True

    def ausgang_umstellen(self, ziel, ausfuehren):
        """Kopfhörer ein/aus: ausfuehren(ziel) stellt Raspotify um (Neustart) und gibt True/False
        zurück. Läuft im Faden der Steuerung, damit nie zwei Neustarts gleichzeitig laufen."""
        with self._sperre:
            self.umstellung = (ziel, ausfuehren)
            self._sperre.notify_all()

    def wartezeit(self):
        """Sekunden, die eine Karte schon auf Musik wartet; None, wenn nichts wartet."""
        with self._sperre:
            if not (self.wunsch and self.wunsch[0] == "spielen") or self.wunsch_zeit is None:
                return None
            if self.ist == ("spielt", self.wunsch[1]):
                return None
            return self.jetzt() - self.wunsch_zeit

    def extern_pausiert(self):
        """Automatik (Timer, Ruhezeit) hat pausiert: gewollt, nicht reparieren, Karte weg = nichts tun."""
        with self._sperre:
            uri = self.ist[1] if self.ist else None
            self.wunsch = None
            self.wunsch_nr += 1
            self.erledigt_nr = self.wunsch_nr
            self.ist = ("pause", uri) if uri else None
            self.phase, self.pruef = "frei", None

    def _wunsch_setzen(self, w):
        if w == self.wunsch and self.erledigt_nr != self.wunsch_nr:
            return                                  # derselbe Wunsch ist schon unterwegs
        if w[0] == "spielen" and w != self.wunsch:
            self.wunsch_zeit = self.jetzt()
        self.wunsch = w
        self.wunsch_nr += 1
        self.fehler = 0
        self.naechster_versuch = 0.0
        if w[0] != "spielen":
            self.sprung = self.spul_ms = 0
        if self.phase == "pruefen":
            self.phase, self.pruef = "frei", None   # neuer Wunsch hat Vorrang vor der Prüfung
        self._sperre.notify_all()

    # ------------------------------------------------------------ Faden

    def starten(self):
        self._faden = threading.Thread(target=self._lauf, name="spotify-steuerung", daemon=True)
        self._faden.start()
        return self._faden

    def lebt(self):
        return getattr(self, "_faden", None) is not None and self._faden.is_alive()

    def _lauf(self):
        while True:
            try:
                self.tick()
            except Exception as e:                  # darf nie sterben
                self._melden(f"Steuerung: unerwarteter Fehler {e!r}")
                self.naechster_versuch = self.jetzt() + 5
            with self._sperre:
                self._sperre.wait(timeout=0.25)

    @property
    def status(self):
        return {"spotify_bereit": self.bereit, "problem": self.problem, "problem_art": self.problem_art}

    # ------------------------------------------------------------ ein Schritt (auch für Tests)

    def tick(self):
        jetzt = self.jetzt()
        self._wache(jetzt)
        if self.umstellung is not None:
            self._umstellen(jetzt)
            return
        if jetzt < self.naechster_versuch or jetzt < self.neustart_wartet_bis:
            return
        if self._befehle(jetzt):
            return
        if self.phase == "pruefen":
            self._pruefen(jetzt)
            return
        with self._sperre:
            offen = self.wunsch is not None and self.erledigt_nr != self.wunsch_nr
            wunsch, nr = self.wunsch, self.wunsch_nr
        if offen:
            self._umsetzen(wunsch, nr, jetzt)
        else:
            self._leerlauf(jetzt)

    # ------------------------------------------------------------ Gerät

    def _geraet(self, jetzt, frisch=False):
        if self.dev and not frisch and jetzt - self.dev_zeit < GERAET_FRISCH:
            return self.dev
        dev = self.sp.geraet_id(self.geraet)
        if dev:
            if self.dev_fehlt_seit is not None or not self.bereit:
                self.log("Spotify kennt die Box." if self.bereit else "Bereit. Karte auflegen.")
            if self.dev_fehlt_seit is not None:
                self._ok()
            self.dev, self.dev_zeit, self.dev_fehlt_seit = dev, jetzt, None
            if not self.bereit:
                self.bereit = True
                self._ok()
                if self.bei_bereit:
                    try:
                        self.bei_bereit()
                    except Exception as e:
                        self.log(f"Ansage fehlgeschlagen: {e!r}")
        else:
            self.dev = None
            if self.dev_fehlt_seit is None:
                self.dev_fehlt_seit = jetzt
                self._melden(f"Spotify kennt die Box gerade nicht (Gerät '{self.geraet}' fehlt).", "geraet")
        return self.dev

    def _leerlauf(self, jetzt):
        if jetzt < self.naechste_leerlauf:
            return
        self.naechste_leerlauf = jetzt + (1 if not self.bereit else LEERLAUF_PRUEFUNG)
        try:
            dev = self._geraet(jetzt, frisch=True)
        except Exception as e:
            self._netzfehler(e, jetzt, zaehlen=False)
            return
        if dev is None and jetzt - self.dev_fehlt_seit >= LEERLAUF_FEHLT_NEUSTART:
            self._raspotify_neu(jetzt, "Gerät fehlt seit über "
                                f"{int(jetzt - self.dev_fehlt_seit)} s")

    # ------------------------------------------------------------ Absturz-Wache (nur lokal, kein Netz)

    def _wache(self, jetzt):
        if jetzt < self.naechste_wache:
            return
        self.naechste_wache = jetzt + WACHE_ABSTAND
        start = self.dienste.startzeit("raspotify")
        if start is None:
            return
        if self.raspotify_start is not None and start != self.raspotify_start:
            self._nach_raspotify_neustart(jetzt, "Raspotify wurde neu gestartet")
        self.raspotify_start = start

    def _nach_raspotify_neustart(self, jetzt, grund):
        """Raspotify ist neu: altes Gerät ungültig. Lief Musik zur liegenden Karte, wieder anstoßen."""
        self.dev, self.dev_zeit = None, -1e9
        with self._sperre:
            lief = self.ist and self.ist[0] in ("spielt", "startet")
            if self.wunsch and self.wunsch[0] == "spielen" and lief:
                self.log(f"{grund} – Musik zur liegenden Karte wird fortgesetzt.")
                self.ist = ("pause", self.wunsch[1])
                self.nach_neustart_uebertragen = True
                self.erledigt_nr = self.wunsch_nr - 1 if self.erledigt_nr == self.wunsch_nr else self.erledigt_nr
                self.phase, self.pruef = "frei", None
                self.naechster_versuch = max(self.naechster_versuch, jetzt + 2)
            elif lief:
                self.ist = None

    # ------------------------------------------------------------ Wunsch umsetzen

    def _umsetzen(self, wunsch, nr, jetzt):
        art, uri = wunsch
        if jetzt - self.letzter_befehl < BEFEHL_ABSTAND:
            return
        if art == "pause":
            self._pause(nr, jetzt)
            return
        # spielen
        if self.ist == ("spielt", uri):              # läuft schon (z. B. Karte kurz angehoben)
            self._erledigt(nr)
            return
        if self.ist == ("startet", uri):             # Start dieser Karte läuft schon: nur weiter prüfen
            self.phase = "pruefen"
            self.pruef = {"nr": nr, "uri": uri, "naechste": jetzt, "proben": [], "anzahl": 0}
            return
        if jetzt - self.letzter_start < START_ABSTAND:
            return                                    # schnelle Wechsel: abwarten, dann nur den neuesten
        try:
            dev = self._geraet(jetzt, frisch=self.fehler > 0)
        except Exception as e:
            self._netzfehler(e, jetzt)
            return
        if dev is None:
            if jetzt - self.dev_fehlt_seit >= GERAET_FEHLT_NEUSTART:
                self._raspotify_neu(jetzt, "Karte wartet, Spotify kennt die Box nicht")
            self.naechster_versuch = jetzt + 2
            return
        weiter = self.ist == ("pause", uri)
        uebertragen = weiter and self.nach_neustart_uebertragen
        if weiter and self.fehler >= 1:
            weiter = uebertragen = False                # Fortsetzen hat nicht geklappt: frisch starten
        try:
            if uebertragen:
                status, data = self.sp.uebertragen(dev, True)
                text = "Weiter nach Neustart"
            elif weiter:
                status, data = self.sp.fortsetzen(dev)
                text = "Weiter"
            else:
                status, data = self.sp.abspielen(dev, uri)
                text = "Spiele"
        except Exception as e:
            self._netzfehler(e, jetzt)
            return
        self.letzter_befehl = self.letzter_start = jetzt
        self.nach_neustart_uebertragen = False
        self.log(f"{text}: {uri} (Spotify {status})")
        if status < 300 or (weiter and status == 403):  # 403 beim Fortsetzen: läuft vermutlich schon
            with self._sperre:
                if nr != self.wunsch_nr:
                    return
                self.ist = ("startet", uri)
            self.phase = "pruefen"
            self.pruef = {"nr": nr, "uri": uri, "naechste": jetzt + PRUEF_ERSTE, "proben": [], "anzahl": 0}
            self._lokal_messen()                        # Ausgangswert für den lokalen Beleg
            return
        self._befehl_fehlgeschlagen(status, data, jetzt)

    def _befehl_fehlgeschlagen(self, status, data, jetzt):
        if status == 401:
            self.sp.token_verwerfen()
            self.log("  Spotify-Zugang erneuert (401).")
            self.naechster_versuch = jetzt + 1
            return
        if status == 429:
            warte = (data or {}).get("retry_after", 5) if isinstance(data, dict) else 5
            self.log(f"  Spotify bremst (429), warte {warte} s.")
            self.naechster_versuch = jetzt + max(1, warte)
            return
        if status == 404:
            self.dev, self.dev_zeit = None, -1e9         # Gerät neu suchen
        self.log(f"  Fehler: {data}")
        self._fehlschlag(jetzt, f"Spotify {status}")

    def _fehlschlag(self, jetzt, grund, neustart_ab=3):
        """Leiter: 1. kurz wiederholen  2. frisch abspielen  3. Raspotify (und ggf. Mischer) neu
        starten  danach mit wachsendem Abstand weiter versuchen, solange die Karte liegt."""
        self.fehler += 1
        if self.fehler == 1 and neustart_ab == 2:     # Prüfung: sofort einmal frisch abspielen
            self.naechster_versuch = jetzt
            return
        if self.fehler >= neustart_ab and self._raspotify_neu(jetzt, grund):
            return
        warte = WARTEN[min(self.fehler - 1, len(WARTEN) - 1)]
        if self.fehler >= neustart_ab:
            self._melden(f"Musik startet nicht ({grund}), neuer Versuch in {warte} s.")
        self.naechster_versuch = jetzt + warte

    def _netzfehler(self, e, jetzt, zaehlen=True):
        name = type(e).__name__
        if name == "AnmeldungFehlt":
            self._melden(str(e), "anmeldung")
            self.naechster_versuch = jetzt + 60
            return
        warte = WARTEN[min(self.fehler, len(WARTEN) - 1)]
        if zaehlen:
            self.fehler += 1
        self._melden(f"Keine Verbindung zu Spotify ({e!r}), neuer Versuch in {warte} s.", "netz")
        self.naechster_versuch = jetzt + warte

    def _pause(self, nr, jetzt):
        if not self.ist or self.ist[0] == "pause":
            self._erledigt(nr)
            return
        dev = self.dev
        if dev is None:
            try:
                dev = self._geraet(jetzt)
            except Exception as e:
                self._netzfehler(e, jetzt)
                return
        if dev is None:                               # Box nicht bei Spotify: es spielt auch nichts
            self.ist = ("pause", self.ist[1])
            self._erledigt(nr)
            return
        try:
            status, data = self.sp.pause(dev)
        except Exception as e:
            self._netzfehler(e, jetzt)
            return
        self.letzter_befehl = jetzt
        self.log(f"Pause (Spotify {status})")
        if status < 300 or status in (403, 404):      # 403: war schon pausiert, 404: nichts aktiv
            self.ist = ("pause", self.ist[1])
            self._erledigt(nr)
        elif status == 429 or status == 401:
            self._befehl_fehlgeschlagen(status, data, jetzt)
        else:
            self.fehler += 1
            self.naechster_versuch = jetzt + WARTEN[min(self.fehler - 1, len(WARTEN) - 1)]

    def _erledigt(self, nr):
        with self._sperre:
            if nr == self.wunsch_nr:
                self.erledigt_nr = nr
                self.fehler = 0
        if self.bereit:
            self._ok()

    # ------------------------------------------------------------ Prüfung nach dem Start

    def _pruefen(self, jetzt):
        p = self.pruef
        if jetzt < p["naechste"]:
            return
        with self._sperre:
            if p["nr"] != self.wunsch_nr:               # inzwischen anderer Wunsch
                self.phase, self.pruef = "frei", None
                return
        try:
            z = self.sp.zustand()
        except Exception:
            z = None
        p["anzahl"] += 1
        p["naechste"] = jetzt + PRUEF_ABSTAND
        lokal = self._lokal_messen()
        probe = None
        if z is not None:
            gut = (not z.get("leer")) and z.get("geraet") == self.dev and z.get("spielt")
            # lokal: Spotify kennt die Box und einen Titel, und librespot dekodiert wirklich
            lokal_gut = bool(lokal) and not z.get("leer") and z.get("geraet") == self.dev
            probe = (gut, z.get("titel"), z.get("position", 0), jetzt, lokal_gut)
        p["proben"].append(probe)
        if self._laeuft_sicher(p["proben"]):
            if not p["proben"][-1][0]:
                self.log("  Spotify meldet keine Wiedergabe, Raspotify spielt aber nachweislich – läuft.")
            with self._sperre:
                if p["nr"] == self.wunsch_nr:
                    self.ist = ("spielt", p["uri"])
            self.phase, self.pruef = "frei", None
            if self.fehler:
                self.log("  Musik läuft wieder.")
            self._erledigt(p["nr"])
            return
        if p["anzahl"] < PRUEF_MAX:
            return
        self.phase, self.pruef = "frei", None
        echte = [x for x in p["proben"] if x is not None]
        if not echte:                                   # Spotify gab keine Auskunft: nicht eingreifen
            self.log("  Prüfung ohne Antwort von Spotify – nehme an, dass es läuft.")
            self.ist = ("spielt", p["uri"])
            self._erledigt(p["nr"])
            return
        self.log("  Prüfung: Box spielt nicht (Befehl angenommen, aber keine Musik).")
        self.ist = ("pause", p["uri"]) if self.ist else None
        # schon einmal frisch gestartet und wieder nichts: Raspotify ist das Problem
        self.naechster_versuch = 0.0
        self._fehlschlag(jetzt, "Box spielt nach dem Start nicht", neustart_ab=2)

    @staticmethod
    def _laeuft_sicher(proben):
        """Zwei aufeinanderfolgende gute Proben mit gleichem Titel: entweder meldet Spotify "spielt" und
        die Position rückt vor, oder librespot dekodiert lokal nachweislich (Spotify-Meldung hinkt nach)."""
        if len(proben) < 2 or proben[-1] is None or proben[-2] is None:
            return False
        (g1, t1, p1, _, l1), (g2, t2, p2, _, l2) = proben[-2], proben[-1]
        if t1 != t2 or t1 is None:
            return False
        return (g1 and g2 and p2 - p1 >= 500) or (l1 and l2)

    def _lokal_messen(self):
        try:
            return self.lokal()
        except Exception as e:                          # Messfühler darf nie die Steuerung stören
            self.log(f"  Lokale Prüfung nicht möglich: {e!r}")
            return None

    # ------------------------------------------------------------ Tasten-Befehle (vor, zurück, spulen)

    def _befehle_verwerfen(self):
        with self._sperre:
            self.sprung = self.spul_ms = 0

    def _befehle(self, jetzt):
        """Vorgemerkte Sprünge/Spulen senden. True, wenn dieser Durchlauf damit belegt ist."""
        with self._sperre:
            sprung, spul = self.sprung, self.spul_ms
            laeuft = self._laeuft()
        if not sprung and not spul:
            return False
        if not laeuft:                                  # inzwischen Pause oder Karte weg
            self._befehle_verwerfen()
            return False
        if jetzt - self.letzter_befehl < BEFEHL_ABSTAND:
            return True
        dev = self.dev
        try:
            if dev is None:
                dev = self._geraet(jetzt)
            if dev is None:
                self._befehle_verwerfen()
                return False
            if sprung:
                n = 1 if sprung > 0 else -1
                status, data = (self.sp.naechster if n > 0 else self.sp.vorheriger)(dev)
                with self._sperre:
                    self.sprung -= n if self.sprung * n > 0 else 0
                text = "Nächster Titel" if n > 0 else "Vorheriger Titel"
            else:
                with self._sperre:
                    delta, self.spul_ms = self.spul_ms, 0
                z = self.sp.zustand()
                if not z or z.get("leer") or z.get("geraet") != dev:
                    return True
                ziel = max(0, int(z.get("position", 0)) + delta)
                status, data = self.sp.springen(dev, ziel)
                text = f"Spulen {'vor' if delta > 0 else 'zurück'} auf {ziel // 1000} s"
        except Exception as e:
            self._befehle_verwerfen()
            self._netzfehler(e, jetzt, zaehlen=False)
            return True
        self.letzter_befehl = jetzt
        self.log(f"{text} (Spotify {status})")
        if status >= 300:
            self._befehle_verwerfen()
            if status == 401:
                self.sp.token_verwerfen()
            elif status == 429:
                warte = (data or {}).get("retry_after", 5) if isinstance(data, dict) else 5
                self.naechster_versuch = jetzt + max(1, warte)
            elif status == 404:
                self.dev, self.dev_zeit = None, -1e9
        if self.phase == "pruefen" and self.pruef:       # Titel/Stelle hat sich bewusst geändert:
            self.pruef.update(proben=[], anzahl=0, naechste=jetzt + PRUEF_ERSTE)   # Prüfung neu
        return True

    # ------------------------------------------------------------ Ausgang wechseln (Kopfhörer)

    def _umstellen(self, jetzt):
        with self._sperre:
            ziel, ausfuehren = self.umstellung
            self.umstellung = None
            lief = self._laeuft()
        try:
            ok = ausfuehren(ziel)
        except Exception as e:
            self.log(f"Ausgang wechseln fehlgeschlagen: {e!r}")
            ok = False
        if not ok:
            return
        self.raspotify_start = self.dienste.startzeit("raspotify")   # eigener Neustart, kein "Absturz"
        self.dev, self.dev_zeit, self.dev_fehlt_seit = None, -1e9, None
        with self._sperre:
            if lief:                                    # weiter an derselben Stelle
                self.ist = ("pause", self.wunsch[1])
                self.nach_neustart_uebertragen = True
                if self.erledigt_nr == self.wunsch_nr:
                    self.erledigt_nr = self.wunsch_nr - 1
                self.wunsch_zeit = jetzt
                self.fehler = 0
            elif self.ist and self.ist[0] in ("spielt", "startet"):
                self.ist = ("pause", self.ist[1])
            self.phase, self.pruef = "frei", None
            self.sprung = self.spul_ms = 0
        self.naechster_versuch = self.neustart_wartet_bis = jetzt + NACH_UMSTELLUNG
        self.log(f"Ausgang: {ziel}" + (", Musik geht gleich weiter." if lief else "."))

    # ------------------------------------------------------------ Neustart

    def _raspotify_neu(self, jetzt, grund):
        if jetzt - self.letzter_neustart < NEUSTART_ABSTAND:
            return False
        self.letzter_neustart = jetzt
        if self.dienste.aktiv("peppa-stille") is False:  # ohne Mischer kann Raspotify nichts ausgeben
            ok, aus = self.dienste.neu_starten("peppa-stille")
            self.log(f"Ton-Mischer (peppa-stille) lief nicht, neu gestartet: {'ok' if ok else aus}")
        ok, aus = self.dienste.neu_starten("raspotify")
        self._melden(f"Raspotify neu gestartet ({grund}): {'ok' if ok else aus}")
        self.raspotify_start = self.dienste.startzeit("raspotify")   # eigener Neustart, keine "Absturz"-Meldung
        self.dev, self.dev_zeit = None, -1e9
        self.dev_fehlt_seit = None
        if self.ist and self.ist[0] in ("spielt", "startet"):
            self.ist = ("pause", self.ist[1])
        self.nach_neustart_uebertragen = False          # nach Reparatur frisch abspielen
        self.neustart_wartet_bis = jetzt + NACH_NEUSTART
        self.naechster_versuch = jetzt + NACH_NEUSTART
        return True

    def _ok(self):
        self.problem = None
        self.problem_art = None
        self._gemeldet = None

    def _melden(self, text, art="spotify"):
        self.problem = text
        self.problem_art = art
        if text != self._gemeldet:
            self.log(text)
            self._gemeldet = text
