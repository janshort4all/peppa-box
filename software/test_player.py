"""Probelauf des ganzen Players mit nachgebautem Kartenleser, Spotify, Ansager und Hardware.
Aufruf: cd software && python3 -m unittest -v test_player
"""
import json
import os
import tempfile
import time
import unittest
from unittest import mock

import ausgang
import einstellungen
import peppa_player


class Uhr:
    def __init__(self):
        self.t = 500.0

    def __call__(self):
        return self.t


class FakeLeser:
    def __init__(self):
        self.karte = None              # (uid, link)
        self.fehler = 0
        self.schlaeft = False
        self.geschlossen = False

    def read_uid(self):
        if self.fehler:
            self.fehler -= 1
            raise OSError("SPI")
        return self.karte[0] if self.karte else None

    def read_card(self, mit_link=True):
        return self.karte

    def antenne(self, an):
        pass

    def schlafen(self):
        self.schlaeft = True

    def close(self):
        self.geschlossen = True


class FakeAnsager:
    def __init__(self):
        self.gesagt, self.gewartet = [], []
        self.zuletzt = None

    def sagen(self, name):
        self.gesagt.append(name)

    def sagen_und_warten(self, name, zeit=8):
        self.gesagt.append(name)
        self.gewartet.append(name)
        return True

    def warten(self, zeit=5):
        self.gewartet.append(None)
        return True

    def starten(self):
        pass

    def lebt(self):
        return True

    def vorbereiten(self):
        pass


class FakeHardware:
    def __init__(self):
        self.lebenszeichen = time.monotonic()
        self.gpio = None
        self.schlaeft = False

    def starten(self):
        pass

    def lebt(self):
        return True

    def schlafen(self):
        self.schlaeft = True


class FakeSp:
    """Spotify-Modul (nur was der Player selbst braucht; die Steuerung läuft hier nicht als Faden)."""
    link_zu_uri = staticmethod(__import__("spotify").link_zu_uri)

    def __init__(self):
        self.pausen = []

    def pause(self, dev):
        self.pausen.append(dev)
        return 204, None


class Probelauf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for ziel, name, wert in ((einstellungen, "LAUF", self.tmp.name),
                                 (peppa_player, "STATUS_DATEI", os.path.join(self.tmp.name, "status.json")),
                                 (ausgang.Helfer, "zeigen", lambda self: "lautsprecher")):
            p = mock.patch.object(ziel, name, wert)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.dict(os.environ, {"HOME": self.tmp.name})
        p.start()
        self.addCleanup(p.stop)
        einstellungen._cache["mtime"] = None
        self.uhr = Uhr()
        self.leser = FakeLeser()
        self.fabrik_fehler = 0
        self.ansager = FakeAnsager()
        self.hw = FakeHardware()
        self.sp = FakeSp()
        self.aus = []
        self.aus_ok = True

        def fabrik():
            if self.fabrik_fehler:
                self.fabrik_fehler -= 1
                raise OSError("Kartenleser antwortet nicht (Version 0x00)")
            return self.leser
        self.pl = peppa_player.Player(sp=self.sp, leser_fabrik=fabrik, ansager=self.ansager, hardware=self.hw,
                                      ausschalten=lambda: (self.aus.append(1) or (self.aus_ok, "x")),
                                      jetzt=self.uhr, schlaf=lambda s: None, log=lambda t: None)
        self.pl.st.karte_auf = mock.Mock(wraps=self.pl.st.karte_auf)
        self.pl.st.karte_weg = mock.Mock(wraps=self.pl.st.karte_weg)
        self.pl._faeden_pruefen = lambda: None          # Fäden laufen in diesem Test nicht

    def runde(self, n=1):
        for _ in range(n):
            self.pl.durchlauf()
            self.uhr.t += 1.0

    def test_karte_mit_link_startet_und_weg_pausiert(self):
        self.leser.karte = ("AA:BB", "https://open.spotify.com/playlist/37i9dQZF1DX?si=1")
        self.runde(2)
        self.pl.st.karte_auf.assert_called_once_with("spotify:playlist:37i9dQZF1DX")
        self.leser.karte = None
        self.runde(3)
        self.pl.st.karte_weg.assert_called()
        with open(peppa_player.STATUS_DATEI) as f:
            z = json.load(f)
        self.assertIsNone(z["karte"])
        for k in ("akku", "ausgang", "spotify_bereit", "problem_art", "faehrt_runter"):
            self.assertIn(k, z)

    def test_leere_karte_und_fremder_link_sagen_es(self):
        self.leser.karte = ("AA:BB", None)
        self.runde()
        self.leser.karte = ("CC:DD", "https://example.com/")
        self.runde()
        self.assertEqual(self.ansager.gesagt, ["karte_leer", "karte_leer"])
        self.assertEqual(self.pl.karte_info(), (True, "https://example.com/"))

    def test_ruhezeit_karte_sagt_ruhezeit(self):
        self.pl.auto.sperrt = lambda: True
        self.leser.karte = ("AA:BB", "spotify:album:x")
        self.runde()
        self.assertEqual(self.ansager.gesagt, ["ruhezeit"])
        self.pl.st.karte_auf.assert_not_called()

    def test_leser_fehlt_beim_start_rest_laeuft_weiter(self):
        self.fabrik_fehler = 2
        self.runde()
        self.assertIn("Kartenleser nicht bereit", self.pl.zustand["leser"])
        self.assertTrue(os.path.exists(peppa_player.STATUS_DATEI))       # Status trotzdem
        self.runde(9)
        self.assertIsNone(self.pl.leser)                                  # zweiter Versuch nach 10 s scheitert auch
        self.runde(11)
        self.assertIs(self.pl.leser, self.leser)
        self.assertIsNone(self.pl.zustand["leser"])

    def test_lesefehler_richtet_neu_ein(self):
        self.runde()
        self.leser.fehler = 5
        self.runde(5)
        self.assertTrue(self.leser.geschlossen)
        self.assertIs(self.pl.leser, self.leser)

    def test_ausschalten_einmal_mit_aufraeumen(self):
        self.runde()
        self.pl.st.dev = "D"
        self.pl.herunterfahren("Ein-Taste", None)
        self.pl.herunterfahren("Ein-Taste", None)
        self.assertEqual(self.aus, [1])
        self.assertEqual(self.ansager.gewartet, [None])                  # „Tschüss“ zu Ende abwarten
        self.assertTrue(self.hw.schlaeft and self.leser.schlaeft)
        self.assertEqual(self.sp.pausen, ["D"])

    def test_ausschalten_mit_ansage_und_fehlschlag(self):
        self.aus_ok = False
        self.pl.herunterfahren("Akku leer", "akku_leer")
        self.assertEqual(self.ansager.gewartet, ["akku_leer"])
        self.assertFalse(self.pl.faehrt_runter)                           # neuer Versuch möglich
        self.pl.herunterfahren("Akku leer", "akku_leer")
        self.assertEqual(len(self.aus), 2)

    def test_auto_aus_nutzt_herunterfahren_ohne_ansage(self):
        einstellungen.speichern({"auto_aus": {"an": True, "minuten": 5}})
        self.pl.auto.letzte_aktivitaet = time.time() - 400
        self.pl.auto.spotify.spielt = lambda dev: False
        self.runde()
        self.assertEqual(self.aus, [1])
        self.assertNotIn("tschuess", self.ansager.gesagt)

    def test_moment_und_kein_internet(self):
        st = self.pl.st
        st.wartezeit = lambda: self.warte
        st.wunsch_zeit = 1.0
        st.problem_art = "netz"
        for self.warte in (2, 9, 12, 26, 40):
            self.runde()
        self.assertEqual(self.ansager.gesagt, ["moment", "kein_internet"])
        st.wunsch_zeit = 2.0                                              # neue Karte
        for self.warte in (1, 9):
            self.runde()
        self.assertEqual(self.ansager.gesagt, ["moment", "kein_internet", "moment"])
        st.problem_art, st.wunsch_zeit = "anmeldung", 3.0
        for self.warte in (9, 30):
            self.runde()
        self.assertEqual(self.ansager.gesagt[-1], "anmeldung")
        st.problem_art, st.wunsch_zeit = "geraet", 4.0                    # Box startet noch: nur „Moment“
        for self.warte in (9, 30, 60):
            self.runde()
        self.assertEqual(self.ansager.gesagt[-1], "moment")

    def test_kein_moment_wenn_musik_schon_fliesst(self):
        # Befund 09.11.: „Einen Moment …“ kam, obwohl die Musik schon 2–3 s lief (Prüfung bestätigt später)
        st = self.pl.st
        st.wartezeit = lambda: self.warte
        st.wunsch_zeit, st.problem_art = 5.0, None
        self.pl.rueck.verarbeiten({"q": "ausgabe", "art": "fluss", "ziel": "lautsprecher", "bytes": 176400})
        for self.warte in (2, 9, 12):
            self.runde()
        self.assertNotIn("moment", self.ansager.gesagt)

    def test_bereit_ansage_einmal_und_nicht_in_ruhezeit(self):
        self.pl._bereit()
        self.pl._bereit()
        self.assertEqual(self.ansager.gesagt, ["bereit"])
        os.remove(einstellungen.lauf_pfad("ansage-bereit"))
        self.pl.auto.sperrt = lambda: True
        self.pl._bereit()
        self.assertEqual(self.ansager.gesagt, ["bereit"])


class Faeden(unittest.TestCase):
    def test_haengender_faden_beendet_den_player(self):
        pl = peppa_player.Player.__new__(peppa_player.Player)
        pl.jetzt, pl.log = time.monotonic, lambda t: None
        ok = mock.Mock(lebt=lambda: True)
        pl.st = pl.regler = pl.ansager = pl.klicker = pl.rueck = ok
        pl.sp = peppa_player.spotify
        pl.hw = mock.Mock(lebt=lambda: True, lebenszeichen=time.monotonic() - 40)
        pl.drehgeber = mock.Mock(lebenszeichen=time.monotonic())
        pl._dreh_faden = mock.Mock(is_alive=lambda: True)
        with mock.patch.object(peppa_player.os, "_exit") as ende:
            pl._faeden_pruefen()
        ende.assert_called_once_with(1)

    def test_toter_faden_wird_neu_gestartet(self):
        pl = peppa_player.Player.__new__(peppa_player.Player)
        pl.jetzt, pl.log = time.monotonic, lambda t: None
        pl.st = mock.Mock(lebt=lambda: False)
        pl.regler = pl.ansager = pl.klicker = mock.Mock(lebt=lambda: True)
        pl.rueck = mock.Mock(lebt=lambda: False)
        pl.sp = peppa_player.spotify
        pl.hw = mock.Mock(lebt=lambda: True, lebenszeichen=time.monotonic())
        pl.drehgeber = mock.Mock(lebenszeichen=time.monotonic())
        pl._dreh_faden = None
        pl._dreh_starten = mock.Mock()
        pl._faeden_pruefen()
        pl.st.starten.assert_called_once()
        pl._dreh_starten.assert_called_once()
        pl.rueck.starten.assert_called_once()                  # Empfang der Rückmeldung auch

    def test_lokaler_beleg_erst_tonfluss_dann_rechenzeit(self):
        rueck = mock.Mock()
        cpu = mock.Mock(return_value=True)
        messen = peppa_player.lokaler_beleg(rueck, cpu)
        rueck.lokal.return_value = False                       # Ausgabe aktiv, kein Ton: zählt
        self.assertIs(messen(), False)
        cpu.assert_not_called()
        rueck.lokal.return_value = None                        # alte Einrichtung: Rechenzeit
        self.assertIs(messen(), True)


if __name__ == "__main__":
    unittest.main()
