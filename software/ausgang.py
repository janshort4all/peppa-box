"""Kopfhörer-Erkennung und Umschalten zwischen Lautsprecher und Kopfhörer.

Erkennung: Öffner L der Klinkenbuchse (Lumberg 1503 09, Fahne C) an gelbem Stift P26 (GPIO 26),
Pull-up im Pi. Ohne Stecker ist der Öffner geschlossen und verbindet P26 mit dem L-Kanal der
Pi-Klinke; der liegt hinter dem Trennkondensator über einen Widerstand an Masse (Raspberry Pi
Audio-Schaltung) -> P26 tief. Mit Stecker öffnet der Kontakt -> Pull-up -> P26 hoch.
(Für den Pi 3A+ am Gerät noch zu bestätigen; die Richtung ist umstellbar: Einstellung
bedienung.klinke_eingesteckt_bei, die Eltern-Seite zeigt den Pegel live.)

Umschalten (Konzept: „Beim Ein-/Ausstecken stellt das Programm den Spotify-Ausgang um“):
  sofort    der bisherige Ausgang wird stumm (eingesteckt: Verstärker SD tief; ausgesteckt:
            Kopfhörer-Regler 0), damit nichts aus dem falschen Ausgang kommt
  dann      Root-Helfer /usr/local/sbin/peppa-ausgang stellt LIBRESPOT_DEVICE um und startet
            Raspotify neu (läuft im Faden der Steuerung; die setzt die Musik an derselben Stelle fort)
  danach    Kopfhörer: Lautstärke auf die Startlautstärke der Kopfhörer (Gehörschutz, jedes Mal);
            Lautsprecher: Verstärker wieder an, Lautstärke wie vorher
Entprellt (0,4 s), höchstens alle 3 s eine Umstellung, nur der zuletzt gewünschte Ausgang zählt.
Klappt der Helfer nicht (nicht eingerichtet), bleibt alles beim Lautsprecher; neuer Versuch in 60 s.
"""
import shutil
import subprocess
import time

import gpio

HELFER = "/usr/local/sbin/peppa-ausgang"
ENTPRELL_S = 0.4
MIN_ABSTAND_S = 3.0
NEU_VERSUCH_S = 60.0
HAENGT_S = 45.0
AUSGAENGE = ("lautsprecher", "kopfhoerer")


class Helfer:
    """Aufruf des Root-Helfers über die sudo-Freigabe aus dienst_einrichten.sh."""

    def __init__(self, pfad=HELFER):
        self.pfad = pfad

    def _lauf(self, *args, zeit=40):
        try:
            r = subprocess.run(["sudo", "-n", self.pfad, *args], capture_output=True, text=True, timeout=zeit)
            return r.returncode == 0, (r.stdout + r.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, repr(e)

    def zeigen(self):
        ok, aus = self._lauf("zeigen", zeit=10)
        return aus.splitlines()[-1].strip() if ok and aus else None

    def umstellen(self, ziel):
        return self._lauf(ziel)


def verstaerker(an, log=print):
    """MAX98357A über SD (P16): an = Ausgang hoch (3,3 V), aus = Ausgang tief (stumm).
    Nicht mehr offen lassen (Befund 08.11.2026): Offen lag SD bei 0–0,2 V, an der Abschaltschwelle des
    Verstärkers -> Knistern, Aussetzer. Hoch = linker Kanal; die Mischung L+R macht ALSA (peppa_mono)."""
    return gpio.pinctrl_setzen(gpio.VERSTAERKER_SD, *(("op", "dh") if an else ("op", "dl")), log=log)


class Ausgang:
    def __init__(self, st, laut, einst, helfer=None, verstaerker=verstaerker, jetzt=time.monotonic,
                 uhr=time.time, log=print):
        self.st, self.laut, self.einst = st, laut, einst
        self.helfer = helfer or Helfer()
        self.verstaerker, self.jetzt, self.uhr, self.log = verstaerker, jetzt, uhr, log
        self.aktuell = None              # Ausgang, auf den Raspotify gerade spielt
        self.eingesteckt = None          # entprellter Zustand
        self.pegel = None
        self._roh, self._roh_seit = None, 0.0
        self.laeuft_seit = None          # Umstellung unterwegs
        self.letzte = -1e9
        self.gesperrt_bis = -1e9
        self.fehler = None               # Klartext, wenn das Umschalten nicht geht

    # ------------------------------------------------------------ Start

    def start(self):
        """Fragt, welchen Ausgang Raspotify gerade nutzt (bleibt vom letzten Mal in /etc/raspotify/conf)."""
        geraet = self.helfer.zeigen() if shutil.which("sudo") else None
        if geraet in AUSGAENGE:
            self.aktuell = geraet
        elif geraet is None:
            self.fehler = "Umschalten nicht eingerichtet (einmal dienst_einrichten.sh ausführen)"
            self.aktuell = "lautsprecher"
            self.gesperrt_bis = self.jetzt() + NEU_VERSUCH_S
            self.log(f"Kopfhörer: {self.fehler}.")
        else:
            self.aktuell = None          # z. B. alte Einstellung plughw:…: beim ersten tick umstellen
            self.log(f"Kopfhörer: Raspotify nutzt '{geraet}', wird passend umgestellt.")
        self._merken()

    def _merken(self):
        if self.aktuell:
            self.einst.lauf_schreiben("ausgang", {"ausgang": self.aktuell})

    # ------------------------------------------------------------ alle 20 ms aus der Bedienung

    def tick(self, pegel, t):
        cfg = self.einst.laden()["bedienung"]
        self.pegel = pegel
        roh = (pegel == 1) == (cfg["klinke_eingesteckt_bei"] == "hoch")
        if roh != self._roh:
            self._roh, self._roh_seit = roh, t
        if t - self._roh_seit < ENTPRELL_S:
            return
        if self.eingesteckt != roh:
            self.eingesteckt = roh
            self.log("Kopfhörer eingesteckt." if roh else "Kopfhörer ausgesteckt.")
        ziel = "kopfhoerer" if (roh and cfg["kopfhoerer_erkennung"]) else "lautsprecher"
        if self.laeuft_seit is not None:
            if t - self.laeuft_seit < HAENGT_S:
                return
            self.log("Kopfhörer: Umstellung kam nicht zurück, versuche erneut.")
            self.laeuft_seit = None
        if ziel == self.aktuell or t < self.gesperrt_bis or t - self.letzte < MIN_ABSTAND_S:
            return
        if not self.laut.eingerichtet("lautsprecher"):
            return                                       # ohne Lautsprecher spielt ohnehin alles über die Klinke
        self.laeuft_seit = self.letzte = t
        # sofort still im bisherigen Ausgang
        if ziel == "kopfhoerer":
            self.verstaerker(False, log=self.log)
        else:
            self.laut.setzen("kopfhoerer", 0)
        self.st.ausgang_umstellen(ziel, self._ausfuehren)

    # ------------------------------------------------------------ im Faden der Steuerung

    def _ausfuehren(self, ziel):
        try:
            ok, text = self.helfer.umstellen(ziel)
        except Exception as e:
            ok, text = False, repr(e)
        if not ok:
            fehler = "Umschalten nicht möglich: " + (text.splitlines()[-1] if text else "unbekannt")
            if fehler != self.fehler:
                self.log(f"Kopfhörer: {fehler} – bleibe bei {self.aktuell or 'lautsprecher'}, neuer Versuch jede Minute.")
            self.fehler = fehler
            self.gesperrt_bis = self.jetzt() + NEU_VERSUCH_S
            if (self.aktuell or "lautsprecher") == "lautsprecher":
                self.verstaerker(True, log=self.log)     # stumm schalten wieder zurücknehmen
            self.laeuft_seit = None
            return False
        self.fehler = None
        self.aktuell = ziel
        self._merken()
        if ziel == "kopfhoerer":
            cfg = self.einst.laden()
            start = min(cfg["lautstaerke"]["kopfhoerer"]["start"],
                        self.einst.wirksames_max(cfg, "kopfhoerer", self.uhr()))
            self.laut.setzen("kopfhoerer", start)
        else:
            self.verstaerker(True, log=self.log)
        self.laeuft_seit = None
        return True

    # ------------------------------------------------------------ Verstärker stumm halten

    def stumm_halten(self, leser):
        """Kopfhörer aktiv: SD muss Ausgang (tief) sein. peppa-stille gibt SD bei einem Neustart frei."""
        if self.aktuell == "kopfhoerer" and self.laeuft_seit is None:
            try:
                if leser.funktion(gpio.VERSTAERKER_SD) != gpio.FUNKTION_AUSGANG:
                    self.verstaerker(False, log=self.log)
            except Exception:
                pass

    @property
    def status(self):
        return {"pegel": self.pegel, "eingesteckt": self.eingesteckt, "ausgang": self.aktuell,
                "umstellung": self.laeuft_seit is not None, "fehler": self.fehler}
