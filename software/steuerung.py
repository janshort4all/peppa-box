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
  Ton-Mischer weg          Reparatur = Ton-Neustart über den Root-Helfer: Raspotify anhalten,
                           peppa-stille (Mischer, Verstärker) neu, Raspotify starten. Ohne neuen
                           Helfer wie früher: peppa-stille nur, wenn es nicht läuft, dann Raspotify.
  Lokaler Beleg            Die Tonausgabe meldet, ob wirklich Ton fließt (rueckmeldung.py); das
                           zählt bei der Prüfung mehr als die Web-API (die irrt sich manchmal).
  401 / 429 / Netz weg     Token erneuern / Wartezeit von Spotify einhalten / mit wachsendem
                           Abstand wiederholen (nie Dauerfeuer).
  Pause durch Automatik    (Schlummer-Timer, Ruhezeit) gilt als gewollt: keine "Reparatur".
  Weiterspielen            Jeder Neustart einer Karte (Störung, Raspotify-/Player-Neustart, Box
                           aus und an, Karte wieder aufgelegt) beginnt an der gemerkten Stelle
                           (fortschritt.py); lässt sie sich nicht anspielen, von vorn. Von vorn
                           auch: Play-Feld 2 s halten (von_vorn).
  Tasten im Deckel         Play = Pause/Weiter bei liegender Karte (Karte weg nach Tasten-Pause
                           ändert nichts), vor/zurück = Titel springen, Halten = spulen. Befehle
                           werden zusammengefasst und nur gesendet, solange Musik zur Karte läuft.
  Musik bricht später ab   Wächter (Audit 12.11.2026, Befund 1): Liegt die Karte, soll gespielt werden
                           und meldet die Tonausgabe STILL_NACH_S lang keinen Ton, wird die Karte an der
                           gemerkten Stelle neu gestartet (höchstens WAECHTER_VERSUCHE mal, dann Hinweis).
                           Nicht bei gewollter Pause und nicht, wenn die Karte zu Ende gehört ist.
  Pause kommt nicht an     (Netz weg, Spotify 5xx): Die Box schaltet den Ton selbst stumm, bis die Pause
                           bestätigt ist oder wieder gespielt werden soll (Befund 8).
  Fremder Inhalt           Nach "Weiter" wird geprüft, ob wirklich die Playlist der Karte läuft (das Konto
                           kann inzwischen am Handy etwas anderes gespielt haben); sonst frisch (Befund 10).
  Kopfhörer ein/aus        betrifft die Steuerung nicht mehr: die Tonausgabe (ausgabe.py) wechselt
                           den Ausgang ohne Neustart (seit 09.11.2026). Nur wenn sie hängt, fordert
                           ausgang.py eine Reparatur an (reparatur_anfordern).

Grenzen: Raspotify-Neustarts höchstens alle NEUSTART_ABSTAND Sekunden; hilft das nicht, wächst der
Abstand bis 15 min (NEUSTART_ABSTAENDE). Ist die Spotify-Anmeldung
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
# Bleibt Musik trotz Neustart aus, wächst der Abstand: Viele Neustarts kurz hintereinander machen es
# schlimmer (09.11.2026: danach antwortete Spotify minutenlang mit 502, auch nach weiteren Neustarts).
NEUSTART_ABSTAENDE = (NEUSTART_ABSTAND, 300, 600, 900)
NACH_NEUSTART = 6          # s nach einem Neustart, bevor nach dem Gerät gefragt wird
WACHE_ABSTAND = 5          # s: Startzeit von Raspotify vergleichen (Absturz erkennen, nur lokal)
WARTEN = [2, 5, 15, 30, 60, 120, 300]   # Abstände bei wiederholten Fehlern
NETZ_WARTEN_MAX = 15       # ohne Netz höchstens so lange bis zum nächsten Versuch (vorher bis 5 min: nach einem
                           # WLAN-Ausfall kam die Musik erst Minuten später wieder, Audit Befund 9)
WAECHTER_ABSTAND = 2.0     # s: so oft sieht der Wächter nach dem Tonfluss
STILL_NACH_S = 12.0        # so lange kein Ton bei liegender Karte -> Karte neu anspielen
WAECHTER_VERSUCHE = 2      # höchstens so oft zurückholen (Entscheidung Jan 12.11.2026), dann nur Hinweis
WAECHTER_RUHE_S = 300.0    # so lange muss wieder Ton fließen, bis die Versuche neu zählen
SPRUNG_MAX = 5             # so viele Titelsprünge werden höchstens vorgemerkt
SYSTEMCTL = shutil.which("systemctl") or "/usr/bin/systemctl"
HELFER = "/usr/local/sbin/peppa-ausgang"
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

    def ton_neu(self):
        """Raspotify anhalten, peppa-stille neu, Raspotify starten (Root-Helfer). (ok, Text); ok None =
        Helfer kann das noch nicht (alte Einrichtung)."""
        code, aus = self._lauf(["sudo", "-n", HELFER, "neustart"], zeit=90)
        if code == 0:
            return True, aus
        if "Aufruf:" in aus or "password" in aus.lower() or "not allowed" in aus.lower() or "Errno 2" in aus:
            return None, aus
        return False, aus

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
                 log=print, bei_bereit=None, lokal=None, fortschritt=None, zu_ende=None, stumm=None, ton=None):
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
        self.neustarts = 0          # Neustarts seit der letzten nachweislich laufenden Musik
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
        self.reparatur = None       # Grund, wenn ein anderer Teil (Ausgang) Raspotify neu haben will
        # Weiterspielen an der gemerkten Stelle (fortschritt.py): stelle(uri) -> dict|None, vergessen(uri)
        self.fortschritt = fortschritt
        self.von_vorn_uri = None    # Play-Feld lange gehalten: diese Karte von vorn
        self.ohne_stelle = set()    # Stelle ließ sich nicht anspielen: von vorn
        self._mit_stelle = None     # letzter Start lief mit gemerkter Stelle (Karte)
        # Wächter für die laufende Wiedergabe (Befund 1)
        # ton(): fließt gerade Ton durch die Tonausgabe? True/False, None = unbekannt. Bewusst NICHT der
        # Messfühler `lokal`: dessen Rückfall (Rechenzeit von librespot) ist für eine Dauerüberwachung zu
        # unsicher; ohne Tonausgabe-Meldung unternimmt der Wächter nichts.
        self.ton = ton or (lambda: None)
        self.zu_ende = zu_ende      # Rückfrage: ist die Karte zu Ende gehört? (Player, aus den librespot-Ereignissen)
        self.still_seit = None      # seit wann bei laufender Karte kein Ton fließt
        self.fluss_seit = None      # seit wann wieder Ton fließt
        self.waechter_versuche = 0
        self.naechste_waechter = 0.0
        # Fortsetzen mit fremdem Inhalt (Befund 10)
        self._start_art = None      # "weiter" | "uebertragen" | "frisch": wie der letzte Start gesendet wurde
        self._frisch = None         # diese Karte beim nächsten Start nicht fortsetzen, sondern frisch abspielen
        # Pause kommt nicht an (Befund 8): Ton selbst stumm schalten, stumm(True/False) kommt vom Player
        self.stumm = stumm
        self._pause_haengt = False
        self._stumm_ist = False

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

    def von_vorn(self):
        """Play-Feld lange gehalten: liegende Karte von vorn. True, wenn eine Karte liegt."""
        with self._sperre:
            uri = self.karte_uri
            if not uri:
                return False
            self.von_vorn_uri = uri
            if self.ist and self.ist[1] == uri:
                self.ist = None                     # nicht "läuft schon" / "weiter", sondern neu
            self.wunsch = None                      # gleicher Wunsch soll trotzdem neu umgesetzt werden
            self._wunsch_setzen(("spielen", uri))
        if self.fortschritt is not None:
            try:
                self.fortschritt.vergessen(uri)
            except Exception as e:
                self.log(f"Gemerkte Stelle nicht gelöscht: {e!r}")
        return True

    def _stelle(self, uri):
        """Gemerkte Stelle für einen Start dieser Karte (oder {} = von vorn)."""
        if self.von_vorn_uri == uri:
            self.von_vorn_uri = None
            return {}
        if self.fortschritt is None or uri in self.ohne_stelle:
            return {}
        try:
            st = self.fortschritt.stelle(uri)
        except Exception as e:
            self.log(f"Gemerkte Stelle nicht lesbar: {e!r}")
            return {}
        return dict(st) if st else {}

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

    def reparatur_anfordern(self, grund):
        """Raspotify (mit Mischer) neu starten lassen, z. B. wenn die Tonausgabe hängt. Läuft im Faden
        der Steuerung (nie zwei Neustarts gleichzeitig); lief Musik, geht es an derselben Stelle weiter."""
        with self._sperre:
            self.reparatur = grund
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
        self.waechter_versuche = 0                  # jemand hat etwas getan: der Wächter zählt neu
        self.still_seit = self.fluss_seit = None
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
        self._stumm_pruefen()
        if self.reparatur is not None:
            self._reparieren(jetzt)
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
            self._waechter(jetzt)
            self._leerlauf(jetzt)

    # ------------------------------------------------------------ Wächter für die laufende Wiedergabe

    def _waechter(self, jetzt):
        """Die Karte gilt als "spielt": fließt wirklich Ton? Sonst an der gemerkten Stelle neu anspielen.
        Ohne Auskunft der Tonausgabe (ton() liefert None) wird nichts unternommen."""
        with self._sperre:
            aktiv = (self.wunsch is not None and self.wunsch[0] == "spielen"
                     and self.erledigt_nr == self.wunsch_nr and self.ist == ("spielt", self.wunsch[1]))
            uri, nr = (self.wunsch[1], self.wunsch_nr) if aktiv else (None, None)
        if not aktiv:
            self.still_seit = self.fluss_seit = None
            return
        if jetzt < self.naechste_waechter:
            return
        self.naechste_waechter = jetzt + WAECHTER_ABSTAND
        try:
            ton = self.ton()
        except Exception as e:
            self.log(f"  Wächter: Tonfluss nicht lesbar: {e!r}")
            ton = None
        if ton is None:
            return
        if ton:
            self.still_seit = None
            if self.fluss_seit is None:
                self.fluss_seit = jetzt
            elif self.waechter_versuche and jetzt - self.fluss_seit >= WAECHTER_RUHE_S:
                self.waechter_versuche = 0
            return
        self.fluss_seit = None
        if self.still_seit is None:
            self.still_seit = jetzt
            return
        if jetzt - self.still_seit < STILL_NACH_S:
            return
        still = int(jetzt - self.still_seit)
        self.still_seit = None
        try:
            ende = bool(self.zu_ende and self.zu_ende())
        except Exception as e:
            self.log(f"  Wächter: Ende der Karte nicht prüfbar: {e!r}")
            ende = False
        with self._sperre:
            if nr != self.wunsch_nr:                    # inzwischen hat jemand etwas getan
                return
            if ende:
                self._wunsch_ablegen(None)
                text = "Karte zu Ende gehört. Play antippen oder neu einstecken spielt sie noch einmal."
            elif self.waechter_versuche >= WAECHTER_VERSUCHE:
                self._wunsch_ablegen(("pause", uri))
                self._frisch = uri
                text = None
            else:
                self.waechter_versuche += 1
                self.ist = None                         # nicht "weiter", sondern an der gemerkten Stelle neu
                self.erledigt_nr = self.wunsch_nr - 1
                self.fehler = 0
                text = (f"Musik ist ausgegangen (seit {still} s kein Ton, Karte liegt) – wird zurückgeholt "
                        f"(Versuch {self.waechter_versuche} von {WAECHTER_VERSUCHE}).")
        if text:
            self.log(text)
        else:
            self._melden(f"Musik ist wieder ausgegangen und wurde schon {WAECHTER_VERSUCHE} mal zurückgeholt. "
                         "Die Box lässt sie jetzt aus (spielt vielleicht ein Handy mit demselben Spotify-Konto?). "
                         "Play antippen oder Karte neu einstecken startet sie wieder.")

    def _wunsch_ablegen(self, ist):
        """Nichts mehr wollen (wie nach einer Pause der Automatik); die Karte bleibt gemerkt, Play startet sie.
        Nur unter der Sperre aufrufen."""
        self.wunsch = None
        self.wunsch_nr += 1
        self.erledigt_nr = self.wunsch_nr
        self.ist = ist
        self.phase, self.pruef = "frei", None

    # ------------------------------------------------------------ Pause kommt nicht an: Ton selbst stumm

    def _stumm_pruefen(self):
        """Stumm nur, solange eine Pause offen ist, die Spotify nicht annimmt. Bei jedem anderen Zustand
        (Pause bestätigt, wieder spielen, Wunsch abgelegt) sofort wieder frei."""
        with self._sperre:
            pause_offen = (self.wunsch is not None and self.wunsch[0] == "pause"
                           and self.erledigt_nr != self.wunsch_nr)
        if not pause_offen:
            self._pause_haengt = False
        soll = pause_offen and self._pause_haengt
        if soll == self._stumm_ist:
            return
        self._stumm_ist = soll
        if self.stumm is None:
            return
        try:
            self.stumm(soll)
        except Exception as e:
            self.log(f"  Ton stumm/frei schalten: {e!r}")
        self.log("Pause kommt bei Spotify nicht an – die Box schaltet den Ton selbst stumm."
                 if soll else "Ton wieder frei.")

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
            elif self.bereit and self.problem_art == "netz":
                # Netz war kurz weg (z. B. WLAN-Wechsel zum Handy-Hotspot): Spotify antwortet wieder,
                # alte Meldung weg (Befund Jan 09.11.2026: blieb sonst bis zur nächsten Taste stehen)
                self.log("Spotify wieder erreichbar.")
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
        if weiter and (self.fehler >= 1 or self._frisch == uri):
            weiter = uebertragen = False                # Fortsetzen hat nicht geklappt: frisch starten
        self._mit_stelle = None
        self._start_art = "uebertragen" if uebertragen else "weiter" if weiter else "frisch"
        try:
            if uebertragen:
                status, data = self.sp.uebertragen(dev, True)
                text = "Weiter nach Neustart"
            elif weiter:
                status, data = self.sp.fortsetzen(dev)
                text = "Weiter"
            else:
                stelle = self._stelle(uri)
                if stelle:
                    status, data = self.sp.abspielen(dev, uri, **stelle)
                    sek = stelle.get("position_ms", 0) // 1000
                    text = f"Spiele ab gemerkter Stelle ({sek // 60}:{sek % 60:02d} in {stelle.get('titel')})"
                else:
                    status, data = self.sp.abspielen(dev, uri)
                    text = "Spiele"
                self._mit_stelle = uri if stelle else None
        except Exception as e:
            self._netzfehler(e, jetzt)
            return
        self.letzter_befehl = self.letzter_start = jetzt
        self.nach_neustart_uebertragen = False
        self.log(f"{text}: {uri} (Spotify {status})")
        if status < 300 or (weiter and status == 403):  # 403 beim Fortsetzen: läuft vermutlich schon
            if self._start_art == "frisch" and self._frisch == uri:
                self._frisch = None
            with self._sperre:
                # Der Befehl ist bei Spotify angekommen, auch wenn inzwischen ein anderer Wunsch gilt (Karte
                # nur kurz erkannt): als gestartet verbuchen, sonst würde die folgende Pause nie gesendet und
                # die Musik liefe ohne Karte weiter (Audit 12.11.2026, Befund 8).
                # Ausnahme: dieselbe Karte soll inzwischen neu starten (Play 2 s gehalten) – das bleibt offen.
                if nr != self.wunsch_nr:
                    if self.wunsch != ("spielen", uri):
                        self.ist = ("startet", uri)
                    return
                self.ist = ("startet", uri)
            self.phase = "pruefen"
            self.pruef = {"nr": nr, "uri": uri, "naechste": jetzt + PRUEF_ERSTE, "proben": [], "anzahl": 0}
            self._lokal_messen()                        # Ausgangswert für den lokalen Beleg
            return
        self._befehl_fehlgeschlagen(status, data, jetzt)

    def _befehl_fehlgeschlagen(self, status, data, jetzt):
        if self._mit_stelle and status in (400, 403, 404):  # z. B. Titel nicht mehr in der Playlist
            self.log("  Gemerkte Stelle lässt sich nicht anspielen – Karte von vorn.")
            self.ohne_stelle.add(self._mit_stelle)
            self._mit_stelle = None
            self.naechster_versuch = jetzt + 1
            return
        # 12.11.2026: nach Neustart jeder Start an der gemerkten Stelle 502, Leiter lief mit derselben
        # Stelle bis 60 s Wartezeit. Ab dem zweiten 5xx darum ohne Stelle (von vorn) weiter versuchen;
        # scheitert auch das, geht die Leiter normal weiter (Raspotify-Neustart).
        if self._mit_stelle and status >= 500 and self.fehler >= 1:
            self.log(f"  Start an der gemerkten Stelle scheitert wiederholt (Spotify {status}) "
                     "– nächster Versuch von vorn.")
            self.ohne_stelle.add(self._mit_stelle)
            self._mit_stelle = None
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
            tipp = (" Tipp: in der Spotify-App einmal das Gerät „Peppa Box“ auswählen."
                    if grund.startswith("Spotify 5") else "")
            self._melden(f"Musik startet nicht ({grund}), neuer Versuch in {warte} s.{tipp}")
        self.naechster_versuch = jetzt + warte

    def _netzfehler(self, e, jetzt, zaehlen=True):
        name = type(e).__name__
        if name == "AnmeldungFehlt":
            self._melden(str(e), "anmeldung")
            self.naechster_versuch = jetzt + 60
            return
        warte = min(WARTEN[min(self.fehler, len(WARTEN) - 1)], NETZ_WARTEN_MAX)
        if zaehlen:
            self.fehler += 1
        status = getattr(e, "status", None)
        if status is not None:                          # Spotify hat geantwortet, aber mit einem Fehler
            if status == 401:
                try:
                    self.sp.token_verwerfen()
                except Exception:
                    pass
                self._melden("Spotify-Zugang wird erneuert (401).", "netz")
                self.naechster_versuch = jetzt + 2
                return
            if status == 429:
                verlangt = getattr(e, "warten", None)
                warte = max(warte, min(int(verlangt), 900) if isinstance(verlangt, (int, float)) else 30)
                self._melden(f"Spotify bremst (zu viele Anfragen), neuer Versuch in {warte} s.", "netz")
            else:
                self._melden(f"Spotify antwortet gerade mit einem Fehler ({status}), neuer Versuch in {warte} s.", "netz")
            self.naechster_versuch = jetzt + warte
            return
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
                self._pause_haengt = True
                self._netzfehler(e, jetzt)
                return
        if dev is None:                               # Box nicht bei Spotify: es spielt auch nichts
            self.ist = ("pause", self.ist[1])
            self._erledigt(nr)
            return
        try:
            status, data = self.sp.pause(dev)
        except Exception as e:
            self._pause_haengt = True                   # Musik liefe sonst weiter: Ton selbst stumm (tick)
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
            self._pause_haengt = True
            self.fehler += 1
            self.naechster_versuch = jetzt + min(WARTEN[min(self.fehler - 1, len(WARTEN) - 1)], NETZ_WARTEN_MAX)

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
            # lokal: Spotify kennt die Box und einen Titel, und librespot gibt wirklich Ton aus
            lokal_gut = bool(lokal) and not z.get("leer") and z.get("geraet") == self.dev
            probe = (gut, z.get("titel"), z.get("position", 0), jetzt, lokal_gut)
        elif lokal:                                     # Web-API stumm, aber Ton fließt nachweislich
            probe = (False, "(lokal)", 0, jetzt, True)
        if z is not None and self._fremd(z, p["uri"]):
            self.log(f"  Nach „Weiter“ läuft nicht die Karte, sondern {z.get('kontext') or z.get('titel_uri')} "
                     "(das Spotify-Konto hat inzwischen etwas anderes gespielt) – Karte wird frisch gestartet.")
            self.phase, self.pruef = "frei", None
            self._frisch = p["uri"]
            self.ist = ("pause", p["uri"])
            self.naechster_versuch = 0.0
            return
        p["proben"].append(probe)
        if z and probe and probe[0] and self.fortschritt is not None and z.get("titel_uri"):
            try:
                self.fortschritt.merken(p["uri"], z["titel_uri"], z.get("position", 0))
            except Exception:
                pass
        if self._laeuft_sicher(p["proben"]):
            if not p["proben"][-1][0]:
                self.log("  Spotify meldet keine Wiedergabe, Raspotify spielt aber nachweislich – läuft.")
            with self._sperre:
                if p["nr"] == self.wunsch_nr:
                    self.ist = ("spielt", p["uri"])
            self.ohne_stelle.discard(p["uri"])          # läuft: ab jetzt gilt die neu gemerkte Stelle
            self.phase, self.pruef = "frei", None
            self.neustarts = 0
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

    def _fremd(self, z, uri):
        """Nach Weiter/Übertragen: läuft etwas anderes als die Karte? Nur wenn Spotify es eindeutig sagt."""
        if self._start_art not in ("weiter", "uebertragen") or z.get("leer") or z.get("geraet") != self.dev:
            return False
        nr = uri.split(":")[-1]
        if uri.split(":")[1:2] in (["track"], ["episode"]):
            titel = z.get("titel_uri")
            return bool(titel) and titel.split(":")[-1] != nr
        kontext = z.get("kontext")
        return bool(kontext) and kontext.split(":")[-1] != nr

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

    # ------------------------------------------------------------ Reparatur auf Anforderung

    def _reparieren(self, jetzt):
        with self._sperre:
            grund, self.reparatur = self.reparatur, None
            lief = self._laeuft()
        if not self._raspotify_neu(jetzt, grund, abstand=False):
            return
        if lief:                                        # weiter an derselben Stelle
            with self._sperre:
                if self.wunsch and self.wunsch[0] == "spielen":
                    self.ist = ("pause", self.wunsch[1])
                    self.nach_neustart_uebertragen = True
                    self._frisch = None                 # hier bewusst an derselben Stelle übertragen
                    if self.erledigt_nr == self.wunsch_nr:
                        self.erledigt_nr = self.wunsch_nr - 1
                    self.fehler = 0
            self.log("  Musik zur liegenden Karte geht gleich weiter.")

    # ------------------------------------------------------------ Neustart

    def _raspotify_neu(self, jetzt, grund, abstand=True):
        noetig = NEUSTART_ABSTAENDE[min(max(self.neustarts - 1, 0), len(NEUSTART_ABSTAENDE) - 1)]
        if abstand and jetzt - self.letzter_neustart < noetig:
            return False
        self.letzter_neustart = jetzt
        self.neustarts += 1
        ok, aus = self._ton_neu()
        if ok is None:                                  # alte Einrichtung: wie früher
            if self.dienste.aktiv("peppa-stille") is False:  # ohne Mischer kann Raspotify nichts ausgeben
                ok, aus = self.dienste.neu_starten("peppa-stille")
                self.log(f"Ton-Mischer (peppa-stille) lief nicht, neu gestartet: {'ok' if ok else aus}")
            ok, aus = self.dienste.neu_starten("raspotify")
            self._melden(f"Raspotify neu gestartet ({grund}): {'ok' if ok else aus}")
        else:
            self._melden(f"Ton neu gestartet: Raspotify und Mischer ({grund}): {'ok' if ok else aus}")
        self.raspotify_start = self.dienste.startzeit("raspotify")   # eigener Neustart, keine "Absturz"-Meldung
        self.dev, self.dev_zeit = None, -1e9
        self.dev_fehlt_seit = None
        with self._sperre:
            if self.ist and self.ist[0] in ("spielt", "startet"):
                self.ist = ("pause", self.ist[1])
                # Die Karte liegt und sollte spielen (z. B. Gerät fehlte im Leerlauf): nach dem Neustart
                # wieder anspielen, an der gemerkten Stelle. Vorher blieb die Box danach still (Befund 1).
                if self.wunsch == ("spielen", self.ist[1]) and self.erledigt_nr == self.wunsch_nr:
                    self.erledigt_nr = self.wunsch_nr - 1
                    self._frisch = self.ist[1]
                    self.fehler = 0
        self.nach_neustart_uebertragen = False          # nach Reparatur frisch abspielen
        self.neustart_wartet_bis = jetzt + NACH_NEUSTART
        self.naechster_versuch = jetzt + NACH_NEUSTART
        return True

    def _ton_neu(self):
        ton_neu = getattr(self.dienste, "ton_neu", None)
        if ton_neu is None:
            return None, ""
        try:
            return ton_neu()
        except Exception as e:
            return None, repr(e)

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
