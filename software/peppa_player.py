#!/usr/bin/env python3
"""Peppa Box – Player: Karte auflegen = Spotify-Link auf der Karte spielt, Karte weg = Pause,
dieselbe Karte wieder auflegen = weiter, andere Karte = neue Playlist.
Den Link schreibt man mit einer Handy-App (z. B. NFC Tools: Schreiben -> URL) auf die Karte.

Im Player laufen (je ein Faden, alle überwacht und bei Ausfall neu gestartet):
  Kartenleser     Hauptschleife, 1 × je Sekunde (rc522.py); liest der Leser wiederholt falsch oder
                  fehlt er beim Start, wird er immer wieder neu eingerichtet – alles andere läuft weiter
  Steuerung       Spotify-Befehle mit Selbstreparatur (steuerung.py)
  Bedienung       Touchfelder, Ein-Taste, Kopfhörer, Akku (bedienung.py, ausgang.py, akku.py), 20 ms
  Drehknopf       Kernel-Eingabegerät des Overlays rotary-encoder (drehgeber.py)
  Lautstärke      Drehknopf -> amixer (bedienung.Regler)
  Ansagen         toene.Ansager: „bereit“, Akkustand, Timer, „Einen Moment …“, „Tschüss“ …
  Automatik       Schlummer-Timer, Ruhezeit, Auto-Aus, Grenzen (automatik.py), in der Hauptschleife
Zustand für die Eltern-Seite: /dev/shm/peppa-box-status.json (jede Sekunde) und
/dev/shm/peppa-box-bedienung.json (Bedienelemente live).
Hängt ein Faden über 30 s, beendet sich der Player; systemd startet ihn neu (Restart=always). Hängt
die Hauptschleife, startet ihn der systemd-Watchdog neu (WatchdogSec=30).
Ausschalten (Ein-Taste, Auto-Aus, Akku leer): Musik pausieren, ggf. Ansage, Touch-Chip und
Kartenleser schlafen legen, dann systemctl poweroff.

Start von Hand: python3 ~/peppa-box/software/peppa_player.py   (läuft sonst als Dienst peppa-player)
"""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time

import akku
import ausgang
import automatik
import bedienung
import drehgeber
import einstellungen
import fortschritt
import i2c
import klang
import lautstaerke
import rueckmeldung
import spotify
import toene
from steuerung import LibrespotLast, Steuerung

GERAET = "Peppa Box"          # Name in /etc/raspotify/conf (LIBRESPOT_NAME)
ABFRAGE = 1.0                 # Sekunden zwischen zwei Abfragen des Lesers
WEG_NACH = 1.5                # Sekunden ohne Karte, bis "entfernt" gilt (= zwei verpasste Abfragen)
LESER_NEU_NACH = 5            # so viele Lesefehler in Folge -> Leser neu einrichten
LESER_NEU_VERSUCH_S = 10      # fehlt der Leser: so oft neu versuchen
MOMENT_NACH_S = 8             # Karte wartet so lange auf Musik -> „Einen Moment …“
KEIN_NETZ_NACH_S = 25         # … und so lange bei Netz-/Anmeldefehler -> „kein Internet“ / „Anmeldung“
FADEN_HAENGT_S = 30
STATUS_DATEI = einstellungen.lauf_pfad("status")    # im Arbeitsspeicher, schont die SD-Karte
SYSTEMCTL = shutil.which("systemctl") or "/usr/bin/systemctl"


def log(text):
    print(time.strftime("%H:%M:%S"), text, flush=True)


def status_schreiben(zustand):
    """Zustand fuer die Eltern-Seite ablegen (atomar: erst temporaere Datei, dann umbenennen)."""
    try:
        tmp = STATUS_DATEI + ".tmp"
        with open(tmp, "w") as f:
            json.dump(dict(zustand, zeit=time.time()), f, default=str)
        os.replace(tmp, STATUS_DATEI)
    except OSError:
        pass


def systemd_melden(text):
    """sd_notify ohne Zusatzpaket (READY=1, WATCHDOG=1). Ohne systemd-Watchdog wirkungslos."""
    adresse = os.environ.get("NOTIFY_SOCKET")
    if not adresse:
        return
    if adresse.startswith("@"):
        adresse = "\0" + adresse[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
            s.connect(adresse)
            s.sendall(text.encode())
    except OSError:
        pass


class SpotifyFuerAutomatik:
    """Automatik (Timer, Ruhezeit) pausiert über diese Hülle: Die Steuerung weiß dann, dass die Pause
    gewollt ist, und „repariert“ sie nicht. Ohne bekanntes Gerät wird nichts pausiert (sonst träfe
    die Pause womöglich das Handy der Eltern)."""

    def __init__(self, st, sp=spotify):
        self.st, self.sp = st, sp

    def spielt(self, dev):
        return self.sp.spielt(dev) if dev else False

    def pause(self, dev):
        self.st.extern_pausiert()
        if not dev:
            return 404, None
        return self.sp.pause(dev)


class GpioDerBedienung:
    """Der Drehknopf-Rückfall liest die Pegel über den GPIO-Zugang des Bedienungs-Fadens."""

    def __init__(self, hw):
        self.hw = hw

    def pegel_alle(self):
        g = self.hw.gpio
        if g is None:
            raise OSError("GPIO nicht offen")
        return g.pegel_alle()


def leser_einrichten():
    from rc522 import RC522                     # spidev erst hier: ohne Leser läuft der Rest trotzdem
    leser = RC522()
    version = leser.version()
    if version in (0x00, 0xFF):
        leser.close()
        raise OSError(f"Kartenleser antwortet nicht (Version 0x{version:02X})")
    log(f"RC522 Version 0x{version:02X}.")
    return leser


def lokaler_beleg(rueck, cpu):
    """Spielt Raspotify wirklich? Zuerst der Tonfluss aus ausgabe.py; ohne die Ausgabe (alte
    Einrichtung) die Rechenzeit von librespot wie bisher."""
    def messen():
        wert = rueck.lokal()
        return wert if wert is not None else cpu()
    return messen


def akku_lesen_gesperrt():
    with i2c.SPERRE:                            # nie gleichzeitig mit dem Touch-Chip
        return akku.lesen()


def poweroff():
    r = subprocess.run(["sudo", "-n", SYSTEMCTL, "poweroff"], capture_output=True, text=True, timeout=60)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


class Player:
    def __init__(self, sp=spotify, leser_fabrik=leser_einrichten, ansager=None, hardware=None,
                 ausschalten=poweroff, jetzt=time.monotonic, schlaf=time.sleep, log=log):
        self.sp, self.leser_fabrik, self.ausschalten_befehl = sp, leser_fabrik, ausschalten
        self.jetzt, self.schlaf, self.log = jetzt, schlaf, log
        self.zustand = {"karte": None, "link": None, "spotify_bereit": False, "problem": None, "leser": None}
        self.ansager = ansager or toene.Ansager(log=log)
        # Rückmeldung der Tonausgabe (ausgabe.py) und der librespot-Ereignisse (ereignis.py)
        self.rueck = rueckmeldung.Rueckmeldung(log=log)
        # Weiterspielen an der unterbrochenen Stelle (Wunsch Jan 09.11.2026)
        self.fortschritt = fortschritt.Fortschritt(log=log) if sp is spotify else None
        self.st = Steuerung(sp, geraet=GERAET, log=log,
                            lokal=lokaler_beleg(self.rueck, LibrespotLast()) if sp is spotify else None,
                            fortschritt=self.fortschritt)
        self._spielte = None                    # Karte, die im letzten Durchlauf lief
        self.auto = automatik.Automatik(SpotifyFuerAutomatik(self.st, sp), lautstaerke, einstellungen, log=log,
                                        ausschalten=lambda: self.herunterfahren("Auto-Aus", None))
        self.regler = bedienung.Regler(lautstaerke, einstellungen, log=log)
        self.akkuwache = akku.Akkuwache(lesen=akku_lesen_gesperrt, ansage=self.ansager.sagen,
                                        ausschalten=self.herunterfahren, log=log)
        self.ausgang = ausgang.Ausgang(self.st, lautstaerke, einstellungen, rueck=self.rueck, log=log,
                                       klang_da=klang.eingerichtet if sp is spotify else None)
        self.bed = bedienung.Bedienung(self.st, self.auto, self.regler, einstellungen, sagen=self.ansager.sagen,
                                       akku_info=lambda: self.akkuwache.status,
                                       herunterfahren=self.herunterfahren, karte=self.karte_info,
                                       log=log, laut=lautstaerke)
        self.drehgeber = drehgeber.Drehgeber(self.bed.drehen, log=log)
        self.hw = hardware or bedienung.Hardware(self.bed, self.ausgang, self.akkuwache, einstellungen,
                                                 drehgeber=self.drehgeber, log=log)
        self.drehgeber.leser = GpioDerBedienung(self.hw)
        self._dreh_faden = None
        self.leser = None
        self._leser_sperre = threading.Lock()
        self._leser_naechster = 0.0
        self.aktuell, self.letzte_sicht, self.lesefehler = None, 0.0, 0
        self._aus_sperre = threading.Lock()
        self.faehrt_runter = False
        self._warte_kennung, self._moment_gesagt, self._netz_gesagt = None, False, False
        self.st.bei_bereit = self._bereit

    # ------------------------------------------------------------ Hilfen für andere Teile

    def karte_info(self):
        """(liegt eine Karte?, Link oder None) – für die Ansage beim Play-Feld ohne Musik."""
        return self.aktuell is not None, self.zustand.get("link")

    def _bereit(self):                          # Ansage, einmal je Einschalten (nicht in der Ruhezeit "keine Musik")
        if not self.auto.sperrt():
            toene.einmal_je_einschalten("bereit", log=self.log, spieler=self.ansager.sagen)

    def _dreh_starten(self):
        self._dreh_faden = threading.Thread(target=self.drehgeber.lauf, name="drehknopf", daemon=True)
        self._dreh_faden.start()

    # ------------------------------------------------------------ Start

    def starten(self):
        if self.sp is spotify:
            self.rueck.starten()                # vor allem anderen: Meldungen von Raspotify nicht verpassen
        self.ausgang.start()                    # Umschalten eingerichtet? Beginnt mit dem Lautsprecher
        try:
            if klang.eingerichtet():            # Klang (Equalizer) wie gespeichert
                klang.anwenden(einstellungen.laden()["klang"]["baender"], log=self.log)
        except Exception as e:
            self.log(f"Klang nicht gesetzt: {e!r}")
        try:
            self.auto.beim_start()              # Startlautstärke, bevor irgendetwas spielt
        except Exception as e:
            self.log(f"Startlautstärke nicht gesetzt: {e!r}")
        self.ansager.starten()
        self.regler.starten()
        self.st.starten()
        self.hw.starten()
        self._dreh_starten()
        self.ansager.vorbereiten()
        self._leser_pruefen(self.jetzt())
        status_schreiben(self.zustand)
        systemd_melden("READY=1")
        self.log("Warte auf Spotify, Karten werden schon gelesen.")

    def _faeden_pruefen(self):
        for name, lebt, starten in (("Spotify-Steuerung", self.st.lebt, self.st.starten),
                                    ("Bedienung", self.hw.lebt, self.hw.starten),
                                    ("Lautstärke", self.regler.lebt, self.regler.starten),
                                    ("Ansagen", self.ansager.lebt, self.ansager.starten),
                                    ("Rückmeldung", lambda: self.sp is not spotify or self.rueck.lebt(),
                                     self.rueck.starten),
                                    ("Drehknopf", lambda: self._dreh_faden is not None and self._dreh_faden.is_alive(),
                                     self._dreh_starten)):
            if not lebt():
                self.log(f"{name} lief nicht mehr, neu gestartet.")
                starten()
        jetzt = self.jetzt()
        for name, zeichen in (("Bedienung", self.hw.lebenszeichen), ("Drehknopf", self.drehgeber.lebenszeichen)):
            if jetzt - zeichen > FADEN_HAENGT_S:
                self.log(f"{name} hängt seit über {FADEN_HAENGT_S} s – Player startet neu.")
                sys.stdout.flush()
                os._exit(1)

    # ------------------------------------------------------------ Kartenleser

    def _leser_pruefen(self, jetzt):
        if self.leser is not None or jetzt < self._leser_naechster:
            return
        try:
            self.leser = self.leser_fabrik()
            self.zustand["leser"] = None
        except Exception as e:
            self.leser = None
            self._leser_naechster = jetzt + LESER_NEU_VERSUCH_S
            text = f"Kartenleser nicht bereit: {e}"
            if self.zustand.get("leser") != text:
                self.log(text + f" – neuer Versuch alle {LESER_NEU_VERSUCH_S} s.")
            self.zustand["leser"] = text

    def _leser_neu(self):
        with self._leser_sperre:
            try:
                self.leser.close()
            except Exception:
                pass
            self.leser = None
        self._leser_naechster = 0.0
        self._leser_pruefen(self.jetzt())
        if self.leser is not None:
            self.log("Kartenleser neu eingerichtet.")

    def _karte_lesen(self):
        if self.leser is None:
            return
        with self._leser_sperre:
            try:
                self.leser.antenne(True)
                self.schritt()
                self.lesefehler = 0
            except Exception as e:                  # Lesefehler: melden, weiterlaufen
                self.lesefehler += 1
                self.log(f"Lesefehler: {e!r} – laufe weiter")
            finally:
                try:
                    self.leser.antenne(False)       # Funkfeld zwischen den Abfragen aus
                except Exception:
                    pass
        if self.lesefehler >= LESER_NEU_NACH:
            self.lesefehler = 0
            self._leser_neu()

    def _link_lesen(self):
        """Link von der aufgelegten Karte, mit ein paar Versuchen (Lesen kann mal haken)."""
        for _ in range(5):
            karte = self.leser.read_card()
            if karte and karte[1]:
                return karte[1]
            self.schlaf(0.05)
        return None

    def schritt(self):
        """Ein Durchlauf: Karte lesen und bei Wechsel der Steuerung den Wunsch melden (wartet nie auf das Netz)."""
        uid = self.leser.read_uid()
        jetzt = self.jetzt()
        if uid:
            self.letzte_sicht = jetzt
            if uid != self.aktuell:
                self.aktuell = uid
                link = self._link_lesen()
                self.zustand["link"] = link
                uri = None
                if not link:
                    self.log(f"Karte {uid}: kein Link gefunden. Mit NFC Tools eine Spotify-URL auf die Karte schreiben.")
                    self.ansager.sagen("karte_leer")
                else:
                    try:
                        uri = self.sp.link_zu_uri(link)
                    except ValueError:
                        self.log(f"Karte {uid}: Link ist kein Spotify-Link: {link}")
                        self.ansager.sagen("karte_leer")
                if uri and self.auto.sperrt():
                    self.log(f"Karte {uid}: Ruhezeit, es wird nicht abgespielt.")
                    self.ansager.sagen("ruhezeit")
                    uri = None
                if uri:
                    self.st.karte_auf(uri)
                else:
                    self.st.karte_weg()             # Karte ohne Link ersetzt eine spielende Karte
        elif self.aktuell and jetzt - self.letzte_sicht > WEG_NACH:
            self.st.karte_weg()
            self.aktuell = None
            self.zustand["link"] = None

    # ------------------------------------------------------------ Rückmeldung, wenn Musik auf sich warten lässt

    def _warten_ansagen(self):
        w = self.st.wartezeit()
        kennung = self.st.wunsch_zeit
        if w is None or kennung != self._warte_kennung:
            self._warte_kennung = kennung
            self._moment_gesagt = self._netz_gesagt = False
            if w is None:
                return
        if self.rueck.fliesst():                   # Musik ist schon zu hören (Tonausgabe meldet Ton), nur die
            self._moment_gesagt = True              # Prüfung bestätigt noch: kein „Einen Moment …“ (Befund 09.11.)
        if w >= MOMENT_NACH_S and not self._moment_gesagt:
            self._moment_gesagt = True
            self.ansager.sagen("moment")
        art = self.st.problem_art
        if w >= KEIN_NETZ_NACH_S and not self._netz_gesagt and art in ("netz", "anmeldung"):
            self._netz_gesagt = True
            self.ansager.sagen("anmeldung" if art == "anmeldung" else "kein_internet")

    # ------------------------------------------------------------ Ausschalten

    def herunterfahren(self, grund, ansage="tschuess"):
        with self._aus_sperre:
            if self.faehrt_runter:
                return
            self.faehrt_runter = True
        self.log(f"Ausschalten ({grund}).")
        self.st.pausieren()
        dev = self.st.dev

        def pause():
            try:
                if dev:
                    self.sp.pause(dev)
            except Exception:
                pass
        p = threading.Thread(target=pause, daemon=True)
        p.start()
        if ansage:
            self.ansager.sagen_und_warten(ansage, 6)
        else:
            self.ansager.warten(5)              # z. B. „Tschüss“ der Ein-Taste zu Ende sprechen lassen
        p.join(3)
        self.aufraeumen()
        ok, aus = self.ausschalten_befehl()
        if not ok:
            self.log(f"Ausschalten fehlgeschlagen: {aus}")
            with self._aus_sperre:
                self.faehrt_runter = False

    def aufraeumen(self):
        """Touch-Chip und Kartenleser schlafen legen (vor dem Ausschalten und beim Beenden)."""
        if getattr(self, "fortschritt", None) is not None:
            self.fortschritt.sichern(sofort=True)   # Stelle der Musik nicht verlieren
        try:
            self.hw.schlafen()
        except Exception:
            pass
        if self._leser_sperre.acquire(timeout=2):
            try:
                if self.leser is not None:
                    self.leser.schlafen()
            except Exception:
                pass
            finally:
                self._leser_sperre.release()

    # ------------------------------------------------------------ Hauptschleife

    def durchlauf(self):
        beginn = self.jetzt()
        self._leser_pruefen(beginn)
        self._karte_lesen()
        self._faeden_pruefen()
        try:
            self.auto.tick(self.st.dev)
        except Exception as e:                      # die Automatik darf die Kartenabfrage nie lahmlegen
            self.log(f"Automatik-Fehler: {e!r} – laufe weiter")
        try:
            self._warten_ansagen()
        except Exception as e:
            self.log(f"Rückmeldung: Fehler {e!r}")
        try:
            self._stelle_merken()
        except Exception as e:                      # Merken darf nie die Kartenabfrage stören
            self.log(f"Stelle merken: Fehler {e!r}")
        self.zustand.update(self.auto.status)
        self.zustand.update(self.st.status)
        self.zustand["karte"] = self.aktuell
        self.zustand["akku"] = self.akkuwache.status
        self.zustand["ausgang"] = self.ausgang.status
        self.zustand["raspotify"] = self.rueck.status
        self.zustand["ansage"] = self.ansager.zuletzt
        self.zustand["faehrt_runter"] = self.faehrt_runter
        status_schreiben(self.zustand)
        systemd_melden("WATCHDOG=1")
        return beginn

    def _stelle_merken(self):
        """Jede Sekunde: Wo ist die Musik der liegenden Karte? (aus den librespot-Ereignissen)"""
        if self.fortschritt is None:
            return
        ist = self.st.ist
        karte = ist[1] if ist and ist[0] == "spielt" else None
        if karte:
            stelle = self.rueck.stelle()
            if stelle:
                self.fortschritt.merken(karte, *stelle)
            ereignis, alter = self.rueck.ereignis, self.rueck.status.get("ereignis_vor_s")
            pos, dauer = self.rueck.position(), self.rueck.dauer_ms
            am_ende = ereignis and (ereignis[0] == "end_of_track" or (
                ereignis[0] == "stopped" and pos is not None and dauer and dauer - pos < 10000))
            if am_ende and alter is not None and alter > 5:
                self.fortschritt.vergessen(karte)   # zu Ende gehört: nächstes Mal von vorn
        elif self._spielte:
            self.fortschritt.sichern(sofort=True)   # Pause/Karte weg: Stelle gleich auf die Karte schreiben
        self._spielte = karte

    def lauf(self):
        self.starten()
        while True:
            beginn = self.durchlauf()
            self.schlaf(max(0.05, ABFRAGE - (self.jetzt() - beginn)))


def main():
    player = Player()

    def beenden(signum, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, beenden)
    try:
        player.lauf()
    finally:
        player.aufraeumen()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
