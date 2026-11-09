"""Kopfhörer-Erkennung und Umschalten zwischen Lautsprecher und Kopfhörer.

Erkennung: Öffner L der Klinkenbuchse (Lumberg 1503 09, Fahne C) an gelbem Stift P26 (GPIO 26),
Pull-up im Pi. Ohne Stecker ist der Öffner geschlossen und verbindet P26 mit dem L-Kanal der
Pi-Klinke; der liegt hinter dem Trennkondensator über einen Widerstand an Masse (Raspberry Pi
Audio-Schaltung) -> P26 tief. Mit Stecker öffnet der Kontakt -> Pull-up -> P26 hoch.
(Die Richtung ist umstellbar: Einstellung bedienung.klinke_eingesteckt_bei, die Eltern-Seite zeigt
den Pegel live.)

Umschalten (seit 09.11.2026 OHNE Neustart von Raspotify): Raspotify gibt den Ton über das kleine
Programm ausgabe.py aus (librespot --backend subprocess). Das liest die Vorgabe
/dev/shm/peppa-box-ausgang.json und wechselt den Ausgang in höchstens 0,25 s; Spotify merkt nichts.
Vorher wurde Raspotify für jeden Wechsel neu gestartet; danach war die Box für Spotify oft nicht
erreichbar (09.11.: Kopfhörer eingesteckt -> kein Ton mehr, auch nicht nach dem Ausstecken).
  eingesteckt  Verstärker stumm (SD tief), Kopfhörer auf ihre Startlautstärke (Gehörschutz, jedes
               Mal) und eingeschaltet, Vorgabe = kopfhoerer
  ausgesteckt  Kopfhörer auf 0, Vorgabe = lautsprecher, Verstärker an
Entprellt (0,4 s), höchstens alle 3 s eine Umstellung, nur der zuletzt gewünschte Ausgang zählt.

Fängt sich selbst:
  Kopfhörer-Ausgang geht nicht   ausgabe.py meldet den Fehler und spielt selbst schon über den
                                 Lautsprecher weiter; hier: Verstärker an, Kopfhörer gesperrt
                                 (10 min, bei Wiederholung länger, höchstens 1 h), Meldung für die
                                 Eltern-Seite
  Tonausgabe folgt nicht         Musik fließt 3 s nach dem Umschalten noch über den alten Ausgang
                                 -> wie oben zurück auf den Lautsprecher
  Verstärker ungewollt stumm     Lautsprecher aktiv, SD aber zweimal hintereinander tief -> wieder an
  Verstärker ungewollt an        Kopfhörer aktiv, SD hoch (z. B. nach Neustart von peppa-stille) -> stumm
Ist ausgabe.py noch nicht eingerichtet (Raspotify spielt wie früher direkt über ALSA), wird nie
umgeschaltet: alles bleibt beim Lautsprecher, die Eltern-Seite sagt, was zu tun ist.
"""
import shutil
import subprocess
import time

import gpio

HELFER = "/usr/local/sbin/peppa-ausgang"
ENTPRELL_S = 0.4
MIN_ABSTAND_S = 3.0
FOLGT_S = 3.0
SPERRE_S = (600, 1200, 2400, 3600)
AUSGAENGE = ("lautsprecher", "kopfhoerer")
NICHT_EINGERICHTET = ("Kopfhörer-Umschaltung ist noch nicht eingerichtet: einmal "
                      "'sh software/dienst_einrichten.sh' am Pi ausführen, dann neu starten")


class Helfer:
    """Aufruf des Root-Helfers über die sudo-Freigabe aus dienst_einrichten.sh."""

    def __init__(self, pfad=HELFER):
        self.pfad = pfad

    def _lauf(self, *args, zeit=60):
        try:
            r = subprocess.run(["sudo", "-n", self.pfad, *args], capture_output=True, text=True, timeout=zeit)
            return r.returncode == 0, (r.stdout + r.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, repr(e)

    def zeigen(self):
        """'relais' (Ausgabe über ausgabe.py), sonst das ALSA-Gerät aus /etc/raspotify/conf; None = kein Helfer."""
        if not shutil.which("sudo"):
            return None
        ok, aus = self._lauf("zeigen", zeit=10)
        return aus.splitlines()[-1].strip() if ok and aus else None

    def umstellen(self, ziel):
        """Nur noch für den alten Weg: Raspotify fest auf den Lautsprecher stellen (mit Neustart)."""
        return self._lauf(ziel)

    def ton_neu(self):
        """Raspotify anhalten, Mischer (peppa-stille) neu, Raspotify starten."""
        return self._lauf("neustart", zeit=90)


def verstaerker(an, log=print):
    """MAX98357A über SD (P16): an = Ausgang hoch (3,3 V), aus = Ausgang tief (stumm).
    Nicht mehr offen lassen (Befund 08.11.2026): Offen lag SD bei 0–0,2 V, an der Abschaltschwelle des
    Verstärkers -> Knistern, Aussetzer. Hoch = linker Kanal; die Mischung L+R macht ALSA (peppa_mono)."""
    return gpio.pinctrl_setzen(gpio.VERSTAERKER_SD, *(("op", "dh") if an else ("op", "dl")), log=log)


class Ausgang:
    def __init__(self, st, laut, einst, rueck=None, helfer=None, verstaerker=verstaerker, jetzt=time.monotonic,
                 uhr=time.time, log=print):
        self.st, self.laut, self.einst, self.rueck = st, laut, einst, rueck
        self.helfer = helfer or Helfer()
        self.verstaerker, self.jetzt, self.uhr, self.log = verstaerker, jetzt, uhr, log
        self.weg = None                  # "relais" (Umschalten möglich) | "alt" | None (kein Helfer)
        self.aktuell = "lautsprecher"    # Vorgabe für die Tonausgabe
        self.eingesteckt = None          # entprellt
        self.pegel = None
        self._roh, self._roh_seit = None, 0.0
        self.letzte = -1e9
        self.folgt_bis = None            # nach dem Umschalten: bis dann muss die Tonausgabe folgen
        self.gesperrt_bis = None         # Kopfhörer gesperrt (Fehler), Zeit aus jetzt()
        self.sperren = 0
        self.fehler = None               # Klartext für die Eltern-Seite
        self._relais_fehler = None       # vom Empfangsfaden gemeldet, hier im Takt behandelt
        self._sd_tief = 0
        if rueck is not None:
            rueck.bei_fehler = self.relais_fehler

    # ------------------------------------------------------------ Start

    def start(self):
        """Welcher Weg ist eingerichtet? Beginnt immer mit dem Lautsprecher (Klinke folgt im ersten Takt)."""
        geraet = self.helfer.zeigen()
        if geraet == "relais":
            self.weg = "relais"
        elif geraet is None:
            self.weg, self.fehler = None, NICHT_EINGERICHTET
            self.log(f"Kopfhörer: {self.fehler}.")
        else:
            self.weg, self.fehler = "alt", NICHT_EINGERICHTET
            self.log(f"Kopfhörer: {self.fehler}.")
            if geraet != "lautsprecher":     # vom alten Umschalten auf den Kopfhörern geblieben
                ok, text = self.helfer.umstellen("lautsprecher")
                self.log("Raspotify zurück auf den Lautsprecher: " + ("ok" if ok else text))
        self.aktuell = "lautsprecher"
        self._merken()

    def _merken(self):
        self.einst.lauf_schreiben("ausgang", {"ausgang": self.aktuell})

    # ------------------------------------------------------------ vom Empfangsfaden (ausgabe.py meldet Fehler)

    def relais_fehler(self, ziel, text, rueckfall):
        if ziel == "kopfhoerer":
            self._relais_fehler = text

    # ------------------------------------------------------------ alle 20 ms aus der Bedienung

    def tick(self, pegel, t):
        cfg = self.einst.laden()["bedienung"]
        self.pegel = pegel
        roh = (pegel == 1) == (cfg["klinke_eingesteckt_bei"] == "hoch")
        if roh != self._roh:
            self._roh, self._roh_seit = roh, t
        if t - self._roh_seit >= ENTPRELL_S and self.eingesteckt != roh:
            self.eingesteckt = roh
            self.log("Kopfhörer eingesteckt." if roh else "Kopfhörer ausgesteckt.")
        if self.weg != "relais" or self.eingesteckt is None:
            return
        if self._relais_fehler is not None:
            text, self._relais_fehler = self._relais_fehler, None
            self._sperren(f"Kopfhörer-Ausgang geht nicht ({text})", t)
            return
        self._folgt_pruefen(t)
        gesperrt = self.gesperrt_bis is not None and t < self.gesperrt_bis
        if self.gesperrt_bis is not None and not gesperrt:
            self.gesperrt_bis, self.fehler = None, None
            self.log("Kopfhörer: Sperre vorbei, nächster Versuch beim Umschalten.")
        ziel = "kopfhoerer" if (self.eingesteckt and cfg["kopfhoerer_erkennung"] and not gesperrt) else "lautsprecher"
        if ziel == self.aktuell or t - self.letzte < MIN_ABSTAND_S:
            return
        if not self.laut.eingerichtet(ziel):
            if self.fehler is None:
                self.fehler = f"Ausgang '{ziel}' ist nicht eingerichtet (lautsprecher_einrichten.sh)"
                self.log(f"Kopfhörer: {self.fehler}.")
            return
        self._umschalten(ziel, t)

    def _umschalten(self, ziel, t):
        self.letzte = t
        if ziel == "kopfhoerer":
            self.verstaerker(False, log=self.log)            # sofort still im Lautsprecher
            cfg = self.einst.laden()
            start = min(cfg["lautstaerke"]["kopfhoerer"]["start"],
                        self.einst.wirksames_max(cfg, "kopfhoerer", self.uhr()))
            self.laut.setzen("kopfhoerer", start)
        else:
            self.laut.setzen("kopfhoerer", 0)                 # sofort still in den Kopfhörern
        self.aktuell = ziel
        self._merken()                                       # ausgabe.py folgt in höchstens 0,25 s
        if ziel == "lautsprecher":
            self.verstaerker(True, log=self.log)
        self.folgt_bis = t + FOLGT_S
        self.log(f"Ausgang: {ziel}.")

    def _folgt_pruefen(self, t):
        """Fließt Musik, muss die Tonausgabe binnen FOLGT_S auf den neuen Ausgang wechseln. Spielt gerade
        nichts, gibt es nichts zu prüfen: ausgabe.py liest die Vorgabe beim nächsten Start ohnehin."""
        if self.folgt_bis is None or self.rueck is None:
            return
        folgt = self.rueck.ausgabe_ziel == self.aktuell
        if folgt or not self.rueck.fliesst():
            if folgt or t >= self.folgt_bis:
                self.folgt_bis = None
            return
        if t < self.folgt_bis:
            return
        self.folgt_bis = None
        if self.aktuell == "kopfhoerer":
            self._sperren(f"Tonausgabe blieb auf {self.rueck.ausgabe_ziel}", t)
        else:                                                # hängt auf den Kopfhörern: Raspotify neu
            self.fehler = "Tonausgabe blieb auf den Kopfhörern – Raspotify wird neu gestartet"
            self.log(f"Kopfhörer: {self.fehler}.")
            self.st.reparatur_anfordern("Tonausgabe folgt dem Ausgang nicht")

    def _sperren(self, grund, t):
        dauer = SPERRE_S[min(self.sperren, len(SPERRE_S) - 1)]
        self.sperren += 1
        self.gesperrt_bis = t + dauer
        self.folgt_bis = None
        self.fehler = f"{grund} – Musik läuft über den Lautsprecher, nächster Versuch in {dauer // 60} min"
        self.log(f"Kopfhörer: {self.fehler}.")
        self.laut.setzen("kopfhoerer", 0)
        self.aktuell = "lautsprecher"
        self._merken()
        self.letzte = t
        self.verstaerker(True, log=self.log)

    # ------------------------------------------------------------ Verstärker passend halten (alle 2 s)

    def stumm_halten(self, leser):
        """Kopfhörer aktiv: SD muss tief sein (peppa-stille setzt SD bei einem Neustart hoch).
        Lautsprecher aktiv: SD muss hoch sein; zweimal hintereinander tief -> wieder an (einmal tief ist
        normal, während peppa-stille startet)."""
        try:
            sd = leser.pegel(gpio.VERSTAERKER_SD)
        except Exception:
            return
        if self.aktuell == "kopfhoerer":
            self._sd_tief = 0
            if sd:
                self.verstaerker(False, log=self.log)
            return
        if sd:
            self._sd_tief = 0
            return
        self._sd_tief += 1
        if self._sd_tief >= 2:
            self._sd_tief = 0
            self.log("Verstärker war stumm, obwohl der Lautsprecher spielen soll – wieder an.")
            self.verstaerker(True, log=self.log)

    @property
    def status(self):
        t = self.jetzt()
        return {"pegel": self.pegel, "eingesteckt": self.eingesteckt, "ausgang": self.aktuell,
                "umstellung": self.folgt_bis is not None, "fehler": self.fehler, "weg": self.weg,
                "gesperrt_s": round(self.gesperrt_bis - t) if self.gesperrt_bis and self.gesperrt_bis > t else None,
                "ausgabe": self.rueck.ausgabe_ziel if self.rueck else None}
