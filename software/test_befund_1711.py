"""Befund 17.11.2026: Nach einem WLAN-Ausfall meldete librespot "Connection to server closed" und blieb
still tot. Eine 25 min später aufgelegte Karte spielte nicht. Außerdem: WLAN-Meldungen in der Diagnose.
Aufruf: cd software && python3 -m unittest -v test_befund_1711
"""
import unittest
from unittest import mock

import peppa_web
import sitzungswache
from steuerung import NEUSTART_ABSTAND, VORBEUGEND_S, Steuerung
from test_steuerung import FakeDienste, FakeSpotify, Uhr

A = "spotify:playlist:AAAAAAAAAA"


class Verloren(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.sp = FakeSpotify(self.uhr)
        self.di = FakeDienste(self.sp)
        self.log = []
        self.ton = lambda: self.sp.spielend and self.sp.modus == "gut"
        self.st = Steuerung(self.sp, self.di, jetzt=self.uhr, log=self.log.append, lokal=lambda: self.ton(),
                            ton=lambda: self.ton(), zu_ende=lambda: False)
        self.lauf(3)
        self.assertTrue(self.st.bereit)
        self.uhr.t += NEUSTART_ABSTAND                    # kein Neustart in den letzten Minuten

    def lauf(self, sekunden):
        ende = self.uhr.t + sekunden
        while self.uhr.t < ende:
            self.st.tick()
            self.uhr.t += 0.25

    def test_leerlauf_neustart_nach_gnade(self):
        self.st.verbindung_verloren("Connection to server closed")
        self.lauf(5)
        self.assertEqual(self.di.neustarts, [])           # erst die Gnadenfrist
        self.lauf(10)
        self.assertEqual(self.di.neustarts, ["raspotify"])
        self.assertTrue(any("Connection to server closed" in t for t in self.log))
        self.lauf(60)
        self.assertEqual(self.di.neustarts, ["raspotify"])  # nur einmal

    def test_karte_danach_spielt(self):
        self.st.verbindung_verloren("Connection to server closed")
        self.lauf(20)
        self.st.karte_auf(A)
        self.lauf(15)
        self.assertEqual(self.st.ist, ("spielt", A))

    def test_waehrend_musik_kein_neustart(self):
        self.st.karte_auf(A)
        self.lauf(12)
        self.assertEqual(self.st.ist, ("spielt", A))
        self.st.verbindung_verloren("Spirc shut down unexpectedly")
        self.lauf(15)
        self.assertEqual(self.di.neustarts, [])           # Musik läuft weiter: der Wächter passt auf
        self.assertIsNone(self.st.verloren)

    def test_abschiedszeilen_nach_eigenem_neustart_zaehlen_nicht(self):
        self.st.verbindung_verloren("Connection to server closed")
        self.lauf(15)
        self.st.verbindung_verloren("Connection to server closed")   # gleich nach dem eigenen Neustart
        self.lauf(30)
        self.assertEqual(self.di.neustarts, ["raspotify"])

    def test_wiederholt_mit_mindestabstand(self):
        for _ in range(4):                                # Netz wackelt: librespot verliert immer wieder
            self.st.verbindung_verloren("Connection to server closed")
            self.lauf(30)
        self.assertLessEqual(len(self.di.neustarts), 2)   # Neustarts höchstens alle 2 min
        self.lauf(NEUSTART_ABSTAND)
        self.assertIsNone(self.st.verloren)               # die Meldung wird aber nicht vergessen

    def test_fremder_neustart_erledigt_meldung(self):
        self.st.verbindung_verloren("Connection to server closed")
        self.di.absturz()                                 # systemd hat Raspotify selbst neu gestartet
        self.lauf(20)
        self.assertEqual(self.di.neustarts, [])
        self.assertIsNone(self.st.verloren)


class SchluesselWeg(Verloren):
    """18:38: librespot bekommt keine Schlüssel mehr, jeder Titel "nicht abspielbar". Neu anspielen allein half
    nicht; der Wächter muss Raspotify neu starten und soll nicht erst 12 s Stille abwarten."""

    def spielen(self):
        self.st.karte_auf(A)
        self.lauf(12)
        self.assertEqual(self.st.ist, ("spielt", A))

    def test_zwei_stoerungen_sofort_mit_neustart(self):
        self.spielen()
        self.sp.modus = "zombie"                          # Befehle angenommen, aber keine Musik
        self.sp.spielend = False
        self.st.verbindung_verloren("Audio key response timeout")
        self.lauf(1)
        self.st.verbindung_verloren("Audio key response timeout")
        self.lauf(3)                                      # ohne 12 s Stille
        self.assertEqual(self.di.neustarts, ["raspotify"])
        self.assertTrue(any("librespot meldet Störungen" in t and "Raspotify-Neustart" in t for t in self.log))
        self.lauf(20)
        self.assertEqual(self.st.ist, ("spielt", A))
        self.assertTrue(self.sp.spielend)
        self.assertEqual(self.st.waechter_versuche, 1)    # zählt als Versuch (höchstens 2, Entscheidung Jan)

    def test_eine_stoerung_dann_stille_mit_neustart(self):
        self.spielen()
        self.sp.modus = "zombie"
        self.sp.spielend = False
        self.st.verbindung_verloren("Audio key response timeout")
        self.lauf(20)
        self.assertEqual(self.di.neustarts, ["raspotify"])
        self.lauf(20)
        self.assertEqual(self.st.ist, ("spielt", A))

    def test_ohne_librespot_stoerung_wie_bisher(self):
        self.spielen()
        self.sp.spielend = False                          # Musik weg, librespot meldet nichts
        self.lauf(20)
        self.assertEqual(self.di.neustarts, [])           # erst neu anspielen (wie bisher)
        self.assertTrue(self.sp.spielend)

    def test_start_scheitert_nach_stoerung_gleich_neustart(self):
        self.sp.modus = "zombie"                          # 18:19: Karte auf tote Verbindung
        self.st.verbindung_verloren("Spirc shut down unexpectedly")
        self.st.karte_auf(A)
        self.lauf(12)
        self.assertEqual(self.di.neustarts, ["raspotify"])
        self.lauf(20)
        self.assertEqual(self.st.ist, ("spielt", A))


class PauseDannPlay(Verloren):
    """19:04: Karte in Pause, librespot verliert die Verbindung ("Websocket peer does not respond"). Play um
    19:12 traf auf das tote librespot. Jetzt: in der Pause neu starten, Play spielt danach frisch."""

    def test_pause_stoerung_play(self):
        self.st.karte_auf(A)
        self.lauf(12)
        self.st.taste_play()                              # Pause
        self.lauf(5)
        self.st.verbindung_verloren("Websocket peer does not respond")
        self.lauf(15)
        self.assertEqual(self.di.neustarts, ["raspotify"])
        self.st.taste_play()
        self.lauf(15)
        self.assertEqual(self.st.ist, ("spielt", A))
        self.assertEqual(self.di.neustarts, ["raspotify"])


class Vorbeugend(unittest.TestCase):
    """Ohne Musik alle 30 min Raspotify neu (nur Raspotify, nicht der Mischer), damit jede Karte auf eine
    frische Verbindung trifft (librespot 0.8.0 erholt sich nach Verbindungsverlust nicht)."""

    def setUp(self):
        self.uhr = Uhr()
        self.sp = FakeSpotify(self.uhr)
        self.di = FakeDienste(self.sp)
        self.di.ton_neu = mock.Mock(return_value=(True, ""))
        self.log = []
        self.ton = lambda: self.sp.spielend and self.sp.modus == "gut"
        self.st = Steuerung(self.sp, self.di, jetzt=self.uhr, log=self.log.append, lokal=lambda: self.ton(),
                            ton=lambda: self.ton(), zu_ende=lambda: False)
        self.lauf(3)

    def lauf(self, sekunden):
        ende = self.uhr.t + sekunden
        while self.uhr.t < ende:
            self.st.tick()
            self.uhr.t += 0.25 if sekunden < 120 else 2.0

    def test_leerlauf_alle_30_min(self):
        self.lauf(VORBEUGEND_S - 60)
        self.assertEqual(self.di.neustarts, [])
        self.lauf(120)
        self.assertEqual(self.di.neustarts, ["raspotify"])
        self.di.ton_neu.assert_not_called()               # Mischer bleibt (kein Knacken)
        self.assertTrue(any(t.startswith("Vorbeugend: Raspotify neu") for t in self.log))
        self.lauf(VORBEUGEND_S)
        self.assertEqual(self.di.neustarts, ["raspotify", "raspotify"])
        self.assertEqual(self.st.neustarts, 0)            # keine wachsenden Reparatur-Abstände

    def test_nicht_waehrend_musik(self):
        self.st.karte_auf(A)
        self.lauf(12)
        self.lauf(2 * VORBEUGEND_S)
        self.assertEqual(self.di.neustarts, [])
        self.assertEqual(self.st.ist, ("spielt", A))

    def test_nach_musik_zaehlt_neu(self):
        self.st.karte_auf(A)
        self.lauf(12)
        self.lauf(600)
        self.st.karte_weg()
        self.lauf(VORBEUGEND_S - 120)
        self.assertEqual(self.di.neustarts, [])
        self.lauf(240)
        self.assertEqual(self.di.neustarts, ["raspotify"])

    def test_karte_in_pause_spielt_danach_frisch(self):
        self.st.karte_auf(A)
        self.lauf(12)
        self.st.taste_play()                              # Pause, Karte bleibt liegen
        self.lauf(VORBEUGEND_S + 120)
        self.assertEqual(self.di.neustarts, ["raspotify"])
        self.st.taste_play()
        self.lauf(15)
        self.assertEqual(self.st.ist, ("spielt", A))
        self.assertTrue(self.sp.spielend)

    def test_karte_nach_vorbeugendem_neustart_spielt(self):
        self.lauf(VORBEUGEND_S + 60)
        self.st.karte_auf(A)
        self.lauf(15)
        self.assertEqual(self.st.ist, ("spielt", A))


class Wache(unittest.TestCase):
    def test_muster(self):
        gemeldet = []
        w = sitzungswache.Sitzungswache(gemeldet.append, log=lambda t: None)
        zeilen = [
            "[2026-11-17T16:54:15Z ERROR librespot_core::session] Connection to server closed.",
            "[2026-11-17T17:19:54Z WARN  librespot] Spirc shut down unexpectedly",
            "[2026-11-17T16:50:43Z ERROR librespot] could not initialize spirc: Service unavailable",
            "[2026-11-17T17:19:54Z WARN  librespot_connect::state::context] couldn't load context info",
        ]
        for z in zeilen:
            w.zeile(z)
        w.zeile("[2026-11-17T17:38:26Z ERROR librespot_core::audio_key] Audio key response timeout")
        w.zeile("[2026-11-17T18:04:21Z WARN  librespot_core::dealer] Websocket peer does not respond.")
        self.assertEqual(gemeldet, ["Connection to server closed", "Spirc shut down unexpectedly",
                                    "Audio key response timeout", "Websocket peer does not respond"])

    def test_echter_lauf_mit_ersatzbefehl(self):
        gemeldet = []
        w = sitzungswache.Sitzungswache(gemeldet.append, log=lambda t: None,
                                        befehl=["printf", "a\\nConnection to server closed.\\nb\\n"])
        w._einmal()
        self.assertEqual(gemeldet, ["Connection to server closed"])

    def test_fehler_beim_melden_toetet_nicht(self):
        def boom(_):
            raise RuntimeError("x")
        log = []
        w = sitzungswache.Sitzungswache(boom, log=log.append)
        w.zeile("Connection to server closed")
        self.assertTrue(log)


class Diagnose(unittest.TestCase):
    def test_wlan_abschnitte(self):
        aufrufe = []

        def befehl(args, zeit=10):
            aufrufe.append(args)
            if args[:2] == ["nmcli", "-t"] and "wifi" in args:
                return 0, "*:72:6:2437 MHz\n :40:11:2462 MHz\n"
            return 0, "ok"
        with mock.patch.object(peppa_web, "befehl", befehl), mock.patch.object(peppa_web, "mit_root",
                                                                             lambda *a: (0, "")), \
                mock.patch.object(peppa_web, "player_zustand", lambda: {}):
            text = peppa_web.diagnose()["text"]
        self.assertIn("== WLAN jetzt ==", text)
        self.assertIn("== WLAN-Protokoll seit dem Einschalten ==", text)
        self.assertIn("== WLAN-Protokoll vom vorigen Lauf ==", text)
        self.assertIn("Signal 72 %, Kanal 6", text)
        self.assertNotIn("Kanal 11", text)               # Nachbar-WLANs nicht
        wlan = [a for a in aufrufe if a and a[0] == "journalctl" and "NetworkManager" in a]
        self.assertTrue(wlan)
        for a in wlan:
            for d in ("NetworkManager", "wpa_supplicant", "peppa-wlan-suche"):
                self.assertIn(d, a)


if __name__ == "__main__":
    unittest.main()
