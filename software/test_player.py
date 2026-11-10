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
import karten
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
        self.schreiben = []            # Links, die auf die Karte geschrieben wurden
        self.schreib_antwort = {"ok": True, "grund": "ok", "typ": "ntag", "meldung": "Der Link steht jetzt auf der Karte."}
        self.schreib_fehler = None

    def beschreiben(self, link):
        if self.schreib_fehler:
            raise self.schreib_fehler
        self.schreiben.append(link)
        erg = dict(self.schreib_antwort)
        if erg["ok"] and self.karte:
            self.karte = (self.karte[0], link)
        return erg

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
        self.spar = []
        self.spar_ok = True

        def fabrik():
            if self.fabrik_fehler:
                self.fabrik_fehler -= 1
                raise OSError("Kartenleser antwortet nicht (Version 0x00)")
            return self.leser
        self.pl = peppa_player.Player(sp=self.sp, leser_fabrik=fabrik, ansager=self.ansager, hardware=self.hw,
                                      ausschalten=lambda: (self.aus.append(1) or (self.aus_ok, "x")),
                                      sparen=lambda: (self.spar.append(1) or (self.spar_ok, "x")),
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

    def test_auto_aus_geht_in_den_sparzustand_ohne_ansage(self):
        einstellungen.speichern({"auto_aus": {"an": True, "minuten": 5}})
        self.pl.auto.letzte_aktivitaet = time.time() - 400
        self.pl.auto.spotify.spielt = lambda dev: False
        self.runde()
        self.assertEqual((self.spar, self.aus), ([1], []))
        self.assertNotIn("tschuess", self.ansager.gesagt)

    def test_sparzustand_einmal_mit_aufraeumen_und_zuruecksetzen(self):
        self.runde()
        self.pl.st.dev = "D"
        einstellungen.lauf_schreiben("gestartet", {"zeit": 1})
        open(einstellungen.lauf_pfad("ansage-bereit"), "w").close()
        self.pl.sparzustand("Ein-Taste", None)
        self.pl.sparzustand("Ein-Taste", None)
        self.assertEqual((self.spar, self.aus), ([1], []))               # nicht ausgeschaltet, nur einmal
        self.assertEqual(self.ansager.gewartet, [None])                  # „Tschüss“ zu Ende abwarten
        self.assertTrue(self.hw.schlaeft and self.leser.schlaeft)
        self.assertEqual(self.sp.pausen, ["D"])
        # wie ein Einschalten: Startlautstärke und „bereit“ gelten nach dem Aufwachen wieder
        self.assertIsNone(einstellungen.lauf_lesen("gestartet"))
        self.assertFalse(os.path.exists(einstellungen.lauf_pfad("ansage-bereit")))

    def test_sparzustand_fehlschlag_neuer_versuch_moeglich(self):
        self.spar_ok = False
        self.pl.sparzustand("Ein-Taste", None)
        self.assertFalse(self.pl.faehrt_runter)
        self.pl.sparzustand("Ein-Taste", None)
        self.assertEqual(len(self.spar), 2)

    def test_akku_leer_schaltet_ganz_aus_nicht_sparzustand(self):
        self.pl.herunterfahren("Akku leer", "akku_leer")
        self.assertEqual((self.aus, self.spar), ([1], []))

    def test_ausschalten_setzt_nichts_zurueck(self):
        einstellungen.lauf_schreiben("gestartet", {"zeit": 1})
        self.pl.herunterfahren("Eltern", None)
        self.assertIsNotNone(einstellungen.lauf_lesen("gestartet"))

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

    # ---- Karte per Kartennummer (karten.json) und Bespielen-Auftrag der Eltern-Seite

    PL = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
    AL = "spotify:album:4aawyAB9vmqN3uQ7FjRGTy"

    def test_karte_ohne_link_spielt_laut_zuordnung_in_der_box(self):
        karten.eintragen("AA:BB:CC:DD", self.PL, auf_karte=False)
        self.leser.karte = ("AA:BB:CC:DD", None)
        self.runde(2)
        self.pl.st.karte_auf.assert_called_once_with(self.PL)
        self.assertEqual(self.ansager.gesagt, [])

    def test_link_auf_der_karte_geht_vor_der_zuordnung(self):
        karten.eintragen("AA:BB:CC:DD", self.AL)
        self.leser.karte = ("AA:BB:CC:DD", "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        self.runde()
        self.pl.st.karte_auf.assert_called_once_with(self.PL)

    def test_unbekannte_karte_ohne_link_sagt_leer(self):
        self.leser.karte = ("11:22:33:44", None)
        self.runde()
        self.assertEqual(self.ansager.gesagt, ["karte_leer"])

    def auftrag(self, uri=None, ueberschreiben=False):
        return karten.auftrag_stellen(uri or self.PL, ueberschreiben=ueberschreiben)

    def test_auftrag_beschreibt_leere_karte_ohne_musik(self):
        a = self.auftrag()
        self.leser.karte = ("04:AA:BB:CC", None)
        self.runde(2)
        self.assertEqual(self.leser.schreiben, ["https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"])
        st = karten.auftrag_status()
        self.assertEqual((st["status"], st["uid"], st["auf_karte"]), ("fertig", "04:AA:BB:CC", True))
        self.assertEqual(karten.liste()[0]["uid"], "04:AA:BB:CC")
        self.pl.st.karte_auf.assert_not_called()                          # beim Bespielen spielt nichts
        self.assertEqual(self.ansager.gesagt, [], "keine Ansage 'Karte leer' beim Bespielen")
        self.assertEqual(len(self.leser.schreiben), 1, "nicht ein zweites Mal schreiben")
        self.assertEqual(self.pl.zustand["link"], "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        # Karte abheben und wieder auflegen: jetzt spielt sie
        self.leser.karte = None
        self.runde(3)
        self.leser.karte = ("04:AA:BB:CC", "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        self.runde(2)
        self.pl.st.karte_auf.assert_called_once_with(self.PL)

    def test_auftrag_wartet_bis_eine_karte_liegt(self):
        self.auftrag()
        self.runde(3)
        self.assertEqual(karten.auftrag_status()["status"], "wartet")
        self.assertEqual(self.leser.schreiben, [])
        self.leser.karte = ("04:AA:BB:CC", None)
        self.runde()
        self.assertEqual(karten.auftrag_status()["status"], "fertig")

    def test_belegte_karte_nur_nach_bestaetigung_ueberschreiben(self):
        self.leser.karte = ("04:AA:BB:CC", "https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy")
        self.auftrag()
        self.runde(2)
        st = karten.auftrag_status()
        self.assertEqual(st["status"], "belegt")
        self.assertEqual(st["vorher_uri"], self.AL)
        self.assertEqual(self.leser.schreiben, [], "ohne Bestätigung nichts überschreiben")
        self.pl.st.karte_auf.assert_not_called()
        self.auftrag(ueberschreiben=True)                                  # Eltern bestätigen
        self.runde()
        self.assertEqual(karten.auftrag_status()["status"], "fertig")
        self.assertEqual(len(self.leser.schreiben), 1)

    def test_schon_richtig_bespielte_karte_wird_nicht_neu_geschrieben(self):
        self.leser.karte = ("04:AA:BB:CC", "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        self.auftrag()
        self.runde()
        st = karten.auftrag_status()
        self.assertEqual((st["status"], st["grund"]), ("fertig", "schon"))
        self.assertEqual(self.leser.schreiben, [])
        self.assertEqual(len(karten.liste()), 1)

    def test_karte_die_sich_nicht_beschreiben_laesst_wird_in_der_box_gemerkt(self):
        self.leser.schreib_antwort = {"ok": False, "grund": "typ", "typ": "classic", "meldung": "Dieser Kartentyp lässt sich hier nicht beschreiben."}
        self.leser.karte = ("19:81:15:20", None)
        self.auftrag()
        self.runde()
        st = karten.auftrag_status()
        self.assertEqual((st["status"], st["auf_karte"], st["typ"]), ("fertig", False, "classic"))
        self.assertIn("nur an dieser Box", st["meldung"])
        self.assertTrue(karten.link_fuer_uid("19:81:15:20"))
        self.leser.karte = None
        self.runde(3)
        self.leser.karte = ("19:81:15:20", None)                           # später: spielt über die Zuordnung
        self.runde(2)
        self.pl.st.karte_auf.assert_called_once_with(self.PL)

    def test_schreibfehler_wird_gemeldet_und_nichts_gemerkt(self):
        self.leser.schreib_antwort = {"ok": False, "grund": "schreibfehler", "typ": "ntag", "meldung": "Karte hat nicht geantwortet."}
        self.leser.karte = ("04:AA:BB:CC", None)
        self.auftrag()
        self.runde()
        st = karten.auftrag_status()
        self.assertEqual((st["status"], st["grund"]), ("fehler", "schreibfehler"))
        self.assertEqual(karten.liste(), [])

    def test_karte_kurz_weg_beim_schreiben_versucht_es_weiter(self):
        self.leser.schreib_antwort = {"ok": False, "grund": "keine_karte", "typ": None, "meldung": "Keine Karte erkannt."}
        self.leser.karte = ("04:AA:BB:CC", None)
        self.auftrag()
        self.runde()
        self.assertEqual(karten.auftrag_status()["status"], "wartet")

    def test_fehler_im_leser_stoppt_den_player_nicht(self):
        self.leser.schreib_fehler = OSError("SPI")
        self.leser.karte = ("04:AA:BB:CC", None)
        self.auftrag()
        self.runde()
        self.assertEqual(karten.auftrag_status()["status"], "fehler")
        self.runde(2)                                                      # Schleife läuft weiter

    def test_laufende_musik_der_karte_wird_beim_bespielen_pausiert(self):
        self.leser.karte = ("04:AA:BB:CC", "https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy")
        self.runde(2)
        self.pl.st.karte_auf.assert_called_once_with(self.AL)
        self.pl.st.karte_weg.reset_mock()
        self.auftrag(ueberschreiben=True)
        self.runde()
        self.pl.st.karte_weg.assert_called()


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
