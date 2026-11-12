"""Regressionstests zum Audit vom 12.11.2026, Paket A „Musik zuverlässig“ (Befunde 1, 3, 4, 5, 6, 8, 9, 10, 11).
Jeder Test stellt den Fehler aus dem Audit nach; vor der Korrektur schlug er fehl.
Aufruf: cd software && python3 -m unittest -v test_audit_a
"""
import os
import tempfile
import unittest
from unittest import mock

import ausgang
import automatik
import einstellungen
import peppa_player
import spotify
import steuerung
from steuerung import Steuerung
from test_player import FakeAnsager, FakeHardware, FakeLeser, FakeSp
from test_player import Uhr as PlayerUhr
from test_steuerung import FakeDienste, FakeSpotify, Uhr

A, B = "spotify:playlist:AAAAAAAAAA", "spotify:playlist:BBBBBBBBBB"


class MitSteuerung(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.sp = FakeSpotify(self.uhr)
        self.di = FakeDienste(self.sp)
        self.log = []
        self.ende = False
        self.stumm = []
        self.ton = lambda: self.sp.spielend and self.sp.modus == "gut"
        self.st = Steuerung(self.sp, self.di, jetzt=self.uhr, log=self.log.append, lokal=lambda: self.ton(),
                            ton=lambda: self.ton(), zu_ende=lambda: self.ende, stumm=self.stumm.append)
        self.lauf(3)

    def lauf(self, sekunden):
        ende = self.uhr.t + sekunden
        while self.uhr.t < ende:
            self.st.tick()
            self.uhr.t += 0.25

    def starts(self):
        return [b for b in self.sp.befehle if b[0] in ("spielen", "weiter", "uebertragen")]

    def spielen(self, uri=A):
        self.st.karte_auf(uri)
        self.lauf(12)
        self.assertEqual(self.st.ist, ("spielt", uri))


class Befund1Waechter(MitSteuerung):
    def test_musik_bricht_ab_und_wird_zurueckgeholt(self):
        self.spielen()
        self.sp.spielend = False                          # z. B. Raspotify hat die Verbindung verloren
        self.lauf(40)
        self.assertTrue(self.sp.spielend)
        self.assertEqual(self.st.ist, ("spielt", A))
        self.assertEqual(self.starts()[-1], ("spielen", A))   # frisch (an der gemerkten Stelle), nicht „weiter“
        self.assertTrue(any("zurückgeholt" in t for t in self.log))

    def test_geraet_verschwindet_beim_spielen(self):
        self.spielen()
        self.sp.modus, self.sp.spielend = "weg", False
        self.lauf(120)                                    # Karte wartet -> Raspotify neu (heilt im Test)
        self.lauf(60)
        self.assertTrue(self.sp.spielend)
        self.assertEqual(self.st.ist, ("spielt", A))

    def test_hoechstens_zwei_mal_dann_hinweis_und_play_startet_wieder(self):
        self.spielen()
        for _ in range(2):
            self.sp.spielend = False
            self.lauf(40)
            self.assertTrue(self.sp.spielend)
        n = len(self.starts())
        self.sp.spielend = False                          # drittes Mal: z. B. das Handy holt sich die Musik
        self.lauf(120)
        self.assertFalse(self.sp.spielend)
        self.assertEqual(len(self.starts()), n)
        self.assertIn("zurückgeholt", self.st.problem)
        self.assertIsNone(self.st.wartezeit())            # keine Ansage „Einen Moment …“
        self.assertEqual(self.st.taste_play(), "weiter")  # ein Tipp auf Play genügt
        self.lauf(15)
        self.assertTrue(self.sp.spielend)
        self.assertEqual(self.starts()[-1], ("spielen", A))

    def test_versuche_zaehlen_neu_nach_langer_musik(self):
        self.spielen()
        for _ in range(4):
            self.sp.spielend = False
            self.lauf(40)
            self.assertTrue(self.sp.spielend)
            self.lauf(steuerung.WAECHTER_RUHE_S + 10)

    def test_gewollte_pausen_bleiben(self):
        self.spielen()
        self.assertEqual(self.st.taste_play(), "pause")
        self.lauf(120)
        self.assertFalse(self.sp.spielend)
        self.st.taste_play()
        self.lauf(15)
        self.st.extern_pausiert()                         # Schlummer-Timer / Ruhezeit
        self.sp.spielend = False
        n = len(self.starts())
        self.lauf(120)
        self.assertEqual(len(self.starts()), n)

    def test_karte_zu_ende_gehoert_wird_nicht_neu_gestartet(self):
        self.spielen()
        self.ende = True
        self.sp.spielend = False
        n = len(self.starts())
        self.lauf(120)
        self.assertEqual(len(self.starts()), n)
        self.assertIsNone(self.st.problem)
        self.assertEqual(self.st.taste_play(), "weiter")  # noch einmal hören: Play
        self.lauf(15)
        self.assertEqual(self.starts()[-1], ("spielen", A))

    def test_kurze_luecke_und_unbekannter_tonfluss_loesen_nichts_aus(self):
        self.spielen()
        n = len(self.starts())
        self.sp.spielend = False
        self.lauf(steuerung.STILL_NACH_S - 4)             # Titelwechsel, Kopfhörer umstecken
        self.sp.spielend = True
        self.lauf(60)
        self.ton = lambda: None                           # Tonausgabe meldet sich nicht: nichts annehmen
        self.sp.spielend = False
        self.lauf(120)
        self.assertEqual(len(self.starts()), n)


class Befund8KarteWegMusikLaeuft(MitSteuerung):
    def test_karte_nur_kurz_erkannt_langsamer_start_wird_pausiert(self):
        echt = self.sp.abspielen

        def langsam(dev, uri, titel=None, position_ms=0):
            r = echt(dev, uri, titel, position_ms)
            self.uhr.t += 3                               # Antwort von Spotify dauert
            self.st.karte_weg()                           # ... die Karte ist inzwischen wieder weg
            return r
        self.sp.abspielen = langsam
        self.st.karte_auf(A)
        self.lauf(20)
        self.assertFalse(self.sp.spielend)
        self.assertIn(("pause", None), self.sp.befehle)

    def test_pause_kommt_nicht_an_box_schaltet_selbst_stumm_und_wieder_frei(self):
        self.spielen()
        self.sp.modus = "netz"
        self.st.karte_weg()
        self.lauf(5)
        self.assertEqual(self.stumm, [True])
        self.lauf(60)
        self.sp.modus = "gut"                             # Netz wieder da: Pause kommt an
        self.lauf(steuerung.NETZ_WARTEN_MAX + 5)
        self.assertFalse(self.sp.spielend)
        self.assertEqual(self.stumm, [True, False])

    def test_stumm_endet_sobald_wieder_gespielt_werden_soll(self):
        self.spielen()
        self.sp.modus = "502"
        self.st.karte_weg()
        self.lauf(5)
        self.assertEqual(self.stumm, [True])
        self.st.karte_auf(A)                              # Karte wieder da, Musik lief die ganze Zeit
        self.lauf(2)
        self.assertEqual(self.stumm, [True, False])

    def test_ausgang_haelt_den_verstaerker_stumm_und_gibt_ihn_wieder_frei(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.object(einstellungen, "LAUF", tmp.name):
            sd = []
            laut = mock.Mock()
            aus = ausgang.Ausgang(mock.Mock(), laut, einstellungen, helfer=mock.Mock(zeigen=lambda: "relais"),
                                  verstaerker=lambda an, log=None: sd.append(an), log=lambda t: None)
            aus.start()
            aus.zwangsstumm(True)
            aus.tick(0, 1.0)
            self.assertEqual(sd[-1], False)
            leser = mock.Mock(pegel=lambda pin: 1)        # SD steht (wieder) hoch
            aus.stumm_halten(leser)
            self.assertEqual(sd[-1], False)               # bleibt stumm, kein „wieder an“
            aus.zwangsstumm(False)
            aus.tick(0, 2.0)
            self.assertEqual(sd[-1], True)
            self.assertFalse(aus.status["zwangsstumm"])


class Befund9Netz(MitSteuerung):
    def test_nach_langem_wlan_ausfall_kommt_die_musik_schnell(self):
        self.sp.modus = "netz"
        self.st.karte_auf(A)
        self.lauf(600)
        self.sp.modus = "gut"
        t0 = self.uhr.t
        while not self.sp.spielend and self.uhr.t - t0 < 300:
            self.st.tick()
            self.uhr.t += 0.25
        self.assertLessEqual(self.uhr.t - t0, steuerung.NETZ_WARTEN_MAX + 2)
        self.assertEqual(self.di.neustarts, [])           # Netzfehler lösen weiter keinen Neustart aus


class Befund10FremderInhalt(MitSteuerung):
    def setUp(self):
        super().setUp()
        echt = self.sp.zustand

        def zustand():
            z = echt()
            if not z.get("leer"):
                z["kontext"] = self.sp.spielt_uri
            return z
        self.sp.zustand = zustand

    def test_gleiche_karte_wieder_auflegen_spielt_die_karte_nicht_den_podcast(self):
        self.spielen()
        self.st.karte_weg()
        self.lauf(5)
        self.sp.spielt_uri = "spotify:show:PODCASTELTERN"  # das Konto hat inzwischen am Handy etwas anderes gespielt
        self.st.karte_auf(A)
        self.lauf(20)
        self.assertEqual((self.sp.spielt_uri, self.sp.spielend), (A, True))
        self.assertEqual(self.st.ist, ("spielt", A))
        self.assertEqual(self.starts()[-2:], [("weiter", None), ("spielen", A)])

    def test_normales_weiter_bleibt_weiter(self):
        self.spielen()
        self.st.karte_weg()
        self.lauf(5)
        self.st.karte_auf(A)
        self.lauf(20)
        self.assertEqual(self.starts()[-1], ("weiter", None))
        self.assertEqual(self.st.ist, ("spielt", A))


class Befund11Fehlerantworten(MitSteuerung):
    def test_fehlerantwort_auf_die_geraeteliste_ist_kein_fehlendes_geraet(self):
        fragen = []

        def geraet_id(name):
            fragen.append(self.uhr.t)
            raise spotify.ApiFehler(502, None)
        self.sp.geraet_id = geraet_id
        self.st.dev_zeit = -1e9
        self.st.karte_auf(A)
        self.lauf(600)
        self.assertEqual(self.di.neustarts, [])
        self.assertIn("502", self.st.problem)
        self.assertLess(len(fragen), 60)                  # vorher 294 Abfragen in 10 Minuten

    def test_429_haelt_die_verlangte_wartezeit_ein(self):
        fragen = []

        def geraet_id(name):
            fragen.append(self.uhr.t)
            raise spotify.ApiFehler(429, {"retry_after": 120})
        self.sp.geraet_id = geraet_id
        self.st.dev_zeit = -1e9
        self.st.karte_auf(A)
        self.lauf(300)
        self.assertLessEqual(len(fragen), 3)
        self.assertEqual(self.di.neustarts, [])

    def test_spotify_modul_401_erneuert_den_zugang_und_wiederholt(self):
        antworten = [(401, None), (200, {"devices": [{"name": "Peppa Box", "id": "D"}]})]
        with mock.patch.object(spotify, "_api_einmal", lambda *a, **k: antworten.pop(0)), \
                mock.patch.object(spotify, "token_verwerfen") as verwerfen:
            self.assertEqual(spotify.geraet_id("peppa box"), "D")
            verwerfen.assert_called_once()

    def test_spotify_modul_fehler_wird_gemeldet_statt_leere_liste(self):
        with mock.patch.object(spotify, "_api_einmal", lambda *a, **k: (502, None)):
            with self.assertRaises(spotify.ApiFehler):
                spotify.geraet_id("Peppa Box")
            self.assertEqual(spotify.geraete(), [])       # Hilfsskripte: wie bisher


class Laut:
    def __init__(self):
        self.w = 40

    def aktive_ausgabe(self):
        return "lautsprecher"

    def lesen(self, a):
        return self.w

    def setzen(self, a, p):
        self.w = int(p)
        return True


class MitAutomatik(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for p in (mock.patch.object(einstellungen, "LAUF", self.tmp.name),
                  mock.patch.dict(os.environ, {"HOME": self.tmp.name})):
            p.start()
            self.addCleanup(p.stop)
        einstellungen._cache["mtime"] = None
        self.uhr = Uhr()
        self.ton = True                                   # es ist Musik zu hören
        self.api_spielt = False                           # ... Spotify behauptet das Gegenteil (Fall 08.11.)
        self.pausen, self.aus, self.erzwungen = [], [], []
        self.pause_wirkt = True
        self.warten = None
        test = self

        class Sp:
            def spielt(self, dev):
                return test.api_spielt

            def pause(self, dev):
                test.pausen.append(dev)
                if not dev:
                    return 0, None
                if test.pause_wirkt:
                    test.ton = False
                return 204, None

            def stopp_erzwingen(self):
                test.erzwungen.append(test.uhr.t)
                test.ton = False
        self.laut = Laut()
        self.auto = automatik.Automatik(Sp(), self.laut, einstellungen, jetzt=self.uhr, schlaf=lambda s: None,
                                        log=lambda t: None, ausschalten=lambda: self.aus.append(self.uhr.t),
                                        ton=lambda: self.ton, wartet=lambda: self.warten)

    def lauf(self, sekunden, dev="D"):
        for _ in range(int(sekunden)):
            self.auto.tick(dev(self.uhr.t) if callable(dev) else dev)
            self.uhr.t += 1


class Befund3SchlummerTimer(MitAutomatik):
    def test_timer_pausiert_auch_wenn_spotify_meint_es_spielt_nichts(self):
        automatik.timer_starten(15, self.laut, einstellungen, jetzt=self.uhr.t)
        self.lauf(15 * 60 + 10)
        self.assertTrue(self.pausen)
        self.assertFalse(self.ton)
        self.assertIsNone(einstellungen.lauf_lesen("timer"))
        self.assertEqual(self.laut.w, 40)                 # Lautstärke nach dem Ausblenden wieder wie vorher

    def test_timer_wartet_auf_die_geraetekennung_statt_aufzugeben(self):
        ende = self.uhr.t + 15 * 60
        automatik.timer_starten(15, self.laut, einstellungen, jetzt=self.uhr.t)
        self.lauf(15 * 60 + 40, dev=lambda t: None if ende - 30 <= t <= ende + 20 else "D")
        self.assertIn("D", self.pausen)
        self.assertFalse(self.ton)

    def test_pause_wirkt_nicht_dann_wird_der_ton_beendet(self):
        self.pause_wirkt = False
        automatik.timer_starten(15, self.laut, einstellungen, jetzt=self.uhr.t)
        self.lauf(15 * 60 + automatik.TIMER_GNADE_S + 10)
        self.assertEqual(len(self.erzwungen), 1)
        self.assertFalse(self.ton)
        self.assertIsNone(einstellungen.lauf_lesen("timer"))

    def test_nichts_spielt_dann_keine_pause(self):
        self.ton = False
        automatik.timer_starten(15, self.laut, einstellungen, jetzt=self.uhr.t)
        self.lauf(15 * 60 + 10)
        self.assertEqual(self.pausen, [])
        self.assertIsNone(einstellungen.lauf_lesen("timer"))

    def test_huelle_des_players_sucht_das_geraet_selbst(self):
        st, sp = mock.Mock(), mock.Mock()
        sp.geraet_id.return_value = "D"
        sp.pause.return_value = (204, None)
        h = peppa_player.SpotifyFuerAutomatik(st, sp, "Peppa Box")
        self.assertEqual(h.pause(None), (204, None))
        sp.pause.assert_called_once_with("D")
        sp.geraet_id.side_effect = OSError("Netz")
        self.assertEqual(h.pause(None)[0], 0)             # nicht gesendet: die Automatik versucht es weiter
        h.stopp_erzwingen()
        st.reparatur_anfordern.assert_called_once()


class Befund4AutoAus(MitAutomatik):
    def setUp(self):
        super().setUp()
        einstellungen.speichern({"auto_aus": {"an": True, "minuten": 30}})

    def test_kein_auto_aus_solange_ton_fliesst(self):
        self.lauf(90 * 60)
        self.assertEqual(self.aus, [])

    def test_auto_aus_wenn_wirklich_nichts_laeuft(self):
        self.ton = False
        self.lauf(31 * 60)
        self.assertEqual(len(self.aus), 1)

    def test_kein_auto_aus_waehrend_die_box_die_musik_repariert(self):
        self.ton = False
        t0 = self.uhr.t
        self.warten = 5.0                                 # Karte liegt und wartet auf Musik
        for _ in range(29 * 60):
            self.warten += 1
            self.auto.tick("D")
            self.uhr.t += 1
        self.assertEqual(self.aus, [])
        self.lauf(31 * 60)                                # wartet sie über 10 Minuten, läuft die Frist wieder
        self.assertEqual(len(self.aus), 1)
        self.assertGreater(self.aus[0] - t0, 39 * 60)


class MitPlayer(unittest.TestCase):
    LINK = "https://open.spotify.com/playlist/37i9dQZF1DXaaaaaaaaaaa"

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
        self.uhr, self.leser, self.ansager = PlayerUhr(), FakeLeser(), FakeAnsager()
        self.pl = peppa_player.Player(sp=FakeSp(), leser_fabrik=lambda: self.leser, ansager=self.ansager,
                                      hardware=FakeHardware(), ausschalten=lambda: (True, ""),
                                      sparen=lambda: (True, ""), jetzt=self.uhr, schlaf=lambda s: None,
                                      log=lambda t: None)
        self.pl.st.karte_auf = mock.Mock(wraps=self.pl.st.karte_auf)
        self.pl.st.karte_weg = mock.Mock(wraps=self.pl.st.karte_weg)
        self.pl._faeden_pruefen = lambda: None

    def runde(self, n=1):
        for _ in range(n):
            self.pl.durchlauf()
            self.uhr.t += 1.0


class TonflussNurWennSicher(MitPlayer):
    def test_ohne_empfang_oder_ohne_tonausgabe_ist_der_tonfluss_unbekannt(self):
        r = self.pl.rueck
        self.assertIsNone(self.pl._tonfluss())            # Empfang läuft nicht
        r.empfang_ok = True
        self.assertIsNone(self.pl._tonfluss())            # Tonausgabe hat sich nie gemeldet (alte Einrichtung)
        r.verarbeiten({"q": "ausgabe", "art": "fluss", "ziel": "lautsprecher", "bytes": 1000})
        self.assertIs(self.pl._tonfluss(), True)
        r.fluss_zeit -= 10
        self.assertIs(self.pl._tonfluss(), False)


class Befund5LinkErneutLesen(MitPlayer):
    def test_link_beim_einschieben_nicht_lesbar_danach_schon(self):
        self.leser.karte = ("AA:BB", None)                # am Rand des Funkfelds: nur die Nummer
        self.runde()
        self.leser.karte = ("AA:BB", self.LINK)           # Karte sitzt
        self.runde(2)
        self.assertEqual(self.ansager.gesagt, [])
        self.pl.st.karte_auf.assert_called_once()

    def test_wirklich_leere_karte_wird_nach_kurzer_geduld_angesagt_und_nur_einmal(self):
        self.leser.karte = ("AA:BB", None)
        self.runde(2)
        self.assertEqual(self.ansager.gesagt, [])
        self.runde(20)
        self.assertEqual(self.ansager.gesagt, ["karte_leer"])
        self.pl.st.karte_auf.assert_not_called()

    def test_leere_karte_ersetzt_die_spielende_sofort(self):
        self.leser.karte = ("AA:BB", self.LINK)
        self.runde(2)
        self.leser.karte = ("CC:DD", None)
        self.runde()
        self.assertEqual(self.pl.st.wunsch, ("pause", None))


class Befund6Lesefehler(MitPlayer):
    def test_einzelne_fehlversuche_unterbrechen_die_musik_nicht(self):
        self.leser.karte = ("AA:BB", self.LINK)
        self.runde(2)
        echt = self.leser.read_uid
        aussetzer = {"n": 0}

        def wackelt():
            aussetzer["n"] += 1
            return None if aussetzer["n"] % 3 else echt()   # zwei von drei Versuchen scheitern
        self.leser.read_uid = wackelt
        self.runde(60)
        self.pl.st.karte_weg.assert_not_called()
        self.pl.st.karte_auf.assert_called_once()

    def test_zwei_verpasste_abfragen_sind_noch_kein_karte_weg(self):
        self.leser.karte = ("AA:BB", self.LINK)
        self.runde(2)
        karte, self.leser.karte = self.leser.karte, None
        self.runde(2)                                     # vorher: Pause nach zwei verpassten Abfragen
        self.leser.karte = karte
        self.runde(3)
        self.pl.st.karte_weg.assert_not_called()

    def test_karte_wirklich_weg_pausiert_nach_gut_drei_sekunden(self):
        self.leser.karte = ("AA:BB", self.LINK)
        self.runde(2)
        self.leser.karte = None
        self.runde(4)
        self.pl.st.karte_weg.assert_called()
        self.assertIsNone(self.pl.aktuell)


if __name__ == "__main__":
    unittest.main()
