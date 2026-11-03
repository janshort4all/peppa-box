"""Tests der Spotify-Steuerung mit simuliertem Spotify, simulierten Diensten und simulierter Uhr.
Aufruf: cd software && python3 -m unittest -v test_steuerung
"""
import unittest

import steuerung
from steuerung import Steuerung


class Uhr:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class AnmeldungFehlt(RuntimeError):
    pass


class FakeSpotify:
    """Spotify samt Raspotify. Modi: gut, 502 (Befehle scheitern), zombie (Befehl ok, spielt nicht),
    springt (Titel wechseln jede Sekunde, Audio-Key-Fehler), weg (Gerät fehlt), netz (Ausnahme)."""

    def __init__(self, uhr):
        self.uhr = uhr
        self.modus = "gut"
        self.heilt_bei_neustart = True
        self.befehle = []
        self.spielt_uri = None
        self.spielend = False
        self.start_t = 0.0
        self.pos_basis = 0
        self.token_verworfen = 0
        self.antwort_429 = 0
        self.verzoegerung = 0.0                         # langsames WLAN: Ton kommt erst nach x s

    # Web API
    def geraet_id(self, name):
        if self.modus == "netz":
            raise OSError("Netz weg")
        if self.modus == "anmeldung":
            raise AnmeldungFehlt("abgelaufen")
        return None if self.modus == "weg" else "D"

    def _befehl(self, art, uri=None):
        self.befehle.append((art, uri))
        if self.modus == "netz":
            raise OSError("Netz weg")
        if self.antwort_429:
            self.antwort_429 -= 1
            return 429, {"retry_after": 3}
        if self.modus == "502":
            return 502, {"error": {"status": 502, "message": "Bad gateway."}}
        if self.modus == "weg":
            return 404, {"error": {"status": 404}}
        return 204, None

    def abspielen(self, dev, uri):
        st, d = self._befehl("spielen", uri)
        if st < 300:
            self._starte(uri, neu=True)
        return st, d

    def fortsetzen(self, dev):
        st, d = self._befehl("weiter")
        if st < 300 and self.spielt_uri:
            self._starte(self.spielt_uri, neu=False)
        return st, d

    def uebertragen(self, dev, spielen=True):
        st, d = self._befehl("uebertragen")
        if st < 300 and self.spielt_uri:
            self._starte(self.spielt_uri, neu=False)
        return st, d

    def pause(self, dev):
        st, d = self._befehl("pause")
        if st < 300:
            if self.spielend:
                self.pos_basis += int((self.uhr.t - self.start_t) * 1000)
            self.spielend = False
        return st, d

    def _starte(self, uri, neu):
        if neu or uri != self.spielt_uri:
            self.pos_basis = 0
        self.spielt_uri = uri
        self.spielend = True
        self.start_t = self.uhr.t + self.verzoegerung

    def zustand(self):
        if self.modus == "netz":
            raise OSError("Netz weg")
        if not self.spielt_uri:
            return {"leer": True}
        if self.modus == "zombie":
            return {"geraet": "D", "spielt": False, "titel": "t1", "position": 0}
        if self.modus == "springt":                     # Position rückt vor, aber jede Sekunde neuer Titel
            return {"geraet": "D", "spielt": True, "titel": f"t{int(self.uhr.t)}",
                    "position": int((self.uhr.t % 1) * 1000) + int(self.uhr.t) * 1000}
        if self.modus == "haengt":                      # meldet "spielt", Position steht still
            return {"geraet": "D", "spielt": True, "titel": "t1", "position": 4711}
        laeuft = self.spielend and self.uhr.t >= self.start_t
        pos = self.pos_basis + (int((self.uhr.t - self.start_t) * 1000) if laeuft else 0)
        return {"geraet": "D", "spielt": laeuft, "titel": "t1", "position": pos}

    def token_verwerfen(self):
        self.token_verworfen += 1


class FakeDienste:
    def __init__(self, sp):
        self.sp = sp
        self.neustarts = []
        self.start = 1
        self.stille_aktiv = True

    def neu_starten(self, name):
        self.neustarts.append(name)
        if name == "raspotify":
            self.start += 1
            self.sp.spielend = False                    # nach Neustart spielt nichts mehr
            if self.sp.heilt_bei_neustart and (name != "raspotify" or self.stille_aktiv):
                self.sp.modus = "gut"
        if name == "peppa-stille":
            self.stille_aktiv = True
        return True, ""

    def aktiv(self, name):
        return self.stille_aktiv if name == "peppa-stille" else True

    def startzeit(self, name):
        return str(self.start)

    def absturz(self):                                  # Raspotify stürzt ab, systemd startet neu
        self.start += 1
        self.sp.spielend = False


class Basis(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.sp = FakeSpotify(self.uhr)
        self.di = FakeDienste(self.sp)
        self.meldungen = []
        self.ansagen = 0
        self.st = Steuerung(self.sp, self.di, jetzt=self.uhr, log=self.meldungen.append,
                            bei_bereit=self._bereit)
        self.lauf(3)                                    # Box wird bereit

    def _bereit(self):
        self.ansagen += 1

    def lauf(self, sekunden):
        ende = self.uhr.t + sekunden
        while self.uhr.t < ende:
            self.st.tick()
            self.uhr.t += 0.25

    def spielt(self, uri=None):
        return self.sp.spielend and self.sp.modus == "gut" and (uri is None or self.sp.spielt_uri == uri)

    def starts(self):
        return [b for b in self.sp.befehle if b[0] in ("spielen", "weiter", "uebertragen")]


class Grundablauf(Basis):
    def test_bereit_und_ansage_einmal(self):
        self.assertTrue(self.st.bereit)
        self.assertEqual(self.ansagen, 1)
        self.lauf(200)
        self.assertEqual(self.ansagen, 1)

    def test_karte_spielt_und_wird_bestaetigt(self):
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(10)
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertEqual(self.st.ist, ("spielt", "spotify:playlist:A"))
        self.assertEqual(self.starts(), [("spielen", "spotify:playlist:A")])
        self.assertEqual(self.di.neustarts, [])
        self.assertIsNone(self.st.problem)

    def test_langsamer_start_kein_neustart(self):
        """Schwaches WLAN: Ton erst nach 5 s. Kein Raspotify-Neustart, höchstens ein erneuter Start."""
        self.sp.verzoegerung = 5.0
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(30)
        self.assertEqual(self.di.neustarts, [])
        self.assertEqual(self.st.ist, ("spielt", "spotify:playlist:A"))
        self.assertLessEqual(len(self.starts()), 1)

    def test_karte_weg_pause_und_wieder_auf_weiter(self):
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(10)
        self.st.karte_weg()
        self.lauf(2)
        self.assertFalse(self.sp.spielend)
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(10)
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertEqual(self.starts()[-1], ("weiter", None))     # an derselben Stelle weiter

    def test_karte_vor_bereit_spielt_sobald_bereit(self):
        uhr = Uhr()
        sp = FakeSpotify(uhr)
        sp.modus = "weg"
        st = Steuerung(sp, FakeDienste(sp), jetzt=uhr, log=lambda t: None)
        st.karte_auf("spotify:playlist:A")
        for _ in range(80):                             # 20 s ohne Gerät (Box startet noch)
            st.tick()
            uhr.t += 0.25
        sp.modus = "gut"
        for _ in range(60):
            st.tick()
            uhr.t += 0.25
        self.assertTrue(sp.spielend)
        self.assertEqual(sp.spielt_uri, "spotify:playlist:A")


class SchnelleWechsel(Basis):
    def test_wechsel_werden_zusammengefasst(self):
        for i, k in enumerate("ABCDEF"):                # sechs Karten im Sekundentakt
            self.st.karte_auf(f"spotify:playlist:{k}")
            self.lauf(0.5)
            self.st.karte_weg()
            self.lauf(0.5)
        self.st.karte_auf("spotify:playlist:G")
        self.lauf(15)
        self.assertTrue(self.spielt("spotify:playlist:G"))
        self.assertLessEqual(len(self.starts()), 4)     # statt 7 Startbefehle
        abst = [b for b in self.sp.befehle]
        self.assertTrue(abst)

    def test_startabstand_eingehalten(self):
        zeiten = []
        orig = self.sp.abspielen

        def merken(dev, uri):
            zeiten.append(self.uhr.t)
            return orig(dev, uri)
        self.sp.abspielen = merken
        for k in "ABCDE":
            self.st.karte_auf(f"spotify:playlist:{k}")
            self.lauf(0.3)
        self.lauf(15)
        self.assertTrue(all(b - a >= steuerung.START_ABSTAND for a, b in zip(zeiten, zeiten[1:])))
        self.assertTrue(self.spielt("spotify:playlist:E"))


class Reparatur(Basis):
    def test_502_wird_mit_neustart_behoben(self):
        """Fall 03.11.2026: Spotify antwortet 502, nach Raspotify-Neustart läuft es."""
        self.sp.modus = "502"
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(40)
        self.assertIn("raspotify", self.di.neustarts)
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertIsNone(self.st.problem)

    def test_zombie_spielt_nicht_wird_erkannt(self):
        """Box nimmt den Befehl an, springt aber sofort auf Pause."""
        self.sp.modus = "zombie"
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(60)
        self.assertEqual(self.di.neustarts.count("raspotify"), 1)
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertEqual(self.st.ist, ("spielt", "spotify:playlist:A"))

    def test_springende_titel_werden_erkannt(self):
        """Audio-Key-Fehler: Titel wechseln jede Sekunde, kein Ton."""
        self.sp.modus = "springt"
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(60)
        self.assertIn("raspotify", self.di.neustarts)
        self.assertTrue(self.spielt("spotify:playlist:A"))

    def test_haengende_wiedergabe_wird_erkannt(self):
        """Spotify meldet 'spielt', die Position bewegt sich aber nicht."""
        self.sp.modus = "haengt"
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(60)
        self.assertIn("raspotify", self.di.neustarts)
        self.assertTrue(self.spielt("spotify:playlist:A"))

    def test_mischer_wird_vor_raspotify_neu_gestartet(self):
        self.sp.modus = "zombie"
        self.di.stille_aktiv = False
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(60)
        self.assertEqual(self.di.neustarts[:2], ["peppa-stille", "raspotify"])
        self.assertTrue(self.spielt("spotify:playlist:A"))

    def test_kein_neustart_dauerfeuer_wenn_nichts_hilft(self):
        self.sp.heilt_bei_neustart = False
        self.sp.modus = "502"
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(600)
        n = self.di.neustarts.count("raspotify")
        self.assertGreaterEqual(n, 2)                   # versucht es weiter ...
        self.assertLessEqual(n, 600 // steuerung.NEUSTART_ABSTAND + 1)   # ... aber mit Abstand
        self.assertLess(len(self.starts()), 40)         # kein Dauerfeuer an Spotify
        self.assertIsNotNone(self.st.problem)
        self.sp.heilt_bei_neustart = True               # später behoben: läuft ohne Zutun wieder
        self.sp.modus = "gut"
        self.lauf(400)
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertIsNone(self.st.problem)

    def test_absturz_waehrend_musik_weiter_an_der_stelle(self):
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(30)
        self.di.absturz()
        self.lauf(15)
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertEqual(self.starts()[-1], ("uebertragen", None))
        self.assertGreater(self.sp.pos_basis + 1, 0)

    def test_absturz_ohne_karte_startet_keine_musik(self):
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(10)
        self.st.karte_weg()
        self.lauf(3)
        n = len(self.starts())
        self.di.absturz()
        self.lauf(20)
        self.assertEqual(len(self.starts()), n)
        self.assertFalse(self.sp.spielend)

    def test_geraet_fehlt_mit_karte_neustart(self):
        self.sp.modus = "weg"
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(steuerung.GERAET_FEHLT_NEUSTART + 30)
        self.assertIn("raspotify", self.di.neustarts)
        self.assertTrue(self.spielt("spotify:playlist:A"))

    def test_geraet_fehlt_im_leerlauf_neustart(self):
        self.sp.modus = "weg"
        self.st.dev_zeit = -1e9
        self.lauf(steuerung.LEERLAUF_FEHLT_NEUSTART + 2 * steuerung.LEERLAUF_PRUEFUNG)
        self.assertIn("raspotify", self.di.neustarts)
        self.assertEqual(self.starts(), [])             # ohne Karte keine Musik

    def test_netz_weg_dann_wieder_da(self):
        self.sp.modus = "netz"
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(30)
        self.assertEqual(self.di.neustarts, [])         # Netz ist nicht Raspotifys Schuld
        self.sp.modus = "gut"
        self.lauf(70)
        self.assertTrue(self.spielt("spotify:playlist:A"))

    def test_429_wartezeit(self):
        zeiten = []
        orig = self.sp._befehl

        def merken(art, uri=None):
            zeiten.append(self.uhr.t)
            return orig(art, uri)
        self.sp._befehl = merken
        self.sp.antwort_429 = 2
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(20)
        self.assertGreaterEqual(zeiten[1] - zeiten[0], 3)          # Retry-After eingehalten
        self.assertGreaterEqual(zeiten[2] - zeiten[1], 3)
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertEqual(self.di.neustarts, [])

    def test_anmeldung_fehlt_meldet_klartext(self):
        self.sp.modus = "anmeldung"
        self.st.dev_zeit = -1e9
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(30)
        self.assertIn("abgelaufen", self.st.problem or "")
        self.assertEqual(self.di.neustarts, [])

    def test_fortsetzen_scheitert_dann_frisch_abspielen(self):
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(10)
        self.st.karte_weg()
        self.lauf(2)
        orig = self.sp.fortsetzen
        self.sp.fortsetzen = lambda dev: (self.sp.befehle.append(("weiter", None)) or (500, None))
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(20)
        self.sp.fortsetzen = orig
        self.assertTrue(self.spielt("spotify:playlist:A"))
        self.assertEqual(self.starts()[-1], ("spielen", "spotify:playlist:A"))


class Automatik(Basis):
    def test_timer_pause_wird_nicht_repariert(self):
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(10)
        self.st.extern_pausiert()
        self.sp.pause("D")
        n = len(self.sp.befehle)
        self.lauf(120)
        self.assertFalse(self.sp.spielend)
        self.assertEqual(len(self.sp.befehle), n)       # weder Neustart der Musik noch Pause beim Abheben
        self.st.karte_weg()
        self.lauf(5)
        self.assertEqual(len(self.sp.befehle), n)
        self.st.karte_auf("spotify:playlist:A")         # Karte neu auflegen: weiter
        self.lauf(10)
        self.assertTrue(self.spielt("spotify:playlist:A"))

    def test_steuerung_faengt_unerwartete_fehler(self):
        self.sp.zustand = lambda: 1 / 0                 # kaputte Antwort
        self.st.karte_auf("spotify:playlist:A")
        self.lauf(30)                                   # darf nicht abstürzen
        self.assertTrue(self.sp.spielend)


class Gegenprobe(unittest.TestCase):
    """Die Prüfung muss echte Fehler erkennen: ohne sie würde der Zombie-Fall durchrutschen."""

    def test_ohne_pruefung_kein_neustart(self):
        uhr = Uhr()
        sp = FakeSpotify(uhr)
        di = FakeDienste(sp)
        st = Steuerung(sp, di, jetzt=uhr, log=lambda t: None)
        st._laeuft_sicher = staticmethod(lambda proben: True)     # Prüfung ausgeschaltet
        sp.modus = "zombie"
        st.karte_auf("spotify:playlist:A")
        for _ in range(240):
            st.tick()
            uhr.t += 0.25
        self.assertEqual(di.neustarts, [])              # Fehler bliebe unbemerkt


if __name__ == "__main__":
    unittest.main()
