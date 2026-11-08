"""Tests für den lokalen Beleg "Raspotify spielt wirklich" (LibrespotLast) und seine Nutzung in der
Prüfung nach dem Start. Befund 08.11.2026: Die Web-API meldete bei hörbarer Musik "spielt: nein"
mit stehender Position; die Box startete das Album deshalb immer wieder neu.
Aufruf: cd software && python3 -m unittest -v test_lokal
"""
import os
import tempfile
import unittest

from steuerung import LibrespotLast, Steuerung
from test_steuerung import Basis, FakeDienste, FakeSpotify, Uhr


class SpotifyMeldetFalsch(FakeSpotify):
    """Raspotify spielt (lokal hörbar), die Web-API meldet aber Pause mit stehender Position."""

    def zustand(self):
        z = super().zustand()
        if z and not z.get("leer") and self.spielend:
            return {"geraet": "D", "spielt": False, "titel": "t1", "position": 17994}
        return z


class MitLokalemBeleg(Basis):
    def neu(self, sp_klasse, lokal):
        self.uhr = Uhr()
        self.sp = sp_klasse(self.uhr)
        self.di = FakeDienste(self.sp)
        self.meldungen = []
        self.st = Steuerung(self.sp, self.di, jetzt=self.uhr, log=self.meldungen.append, lokal=lokal)
        self.lauf(3)

    def test_falsche_meldung_mit_lokalem_beleg_kein_neustart(self):
        self.neu(SpotifyMeldetFalsch, lambda: True)
        self.st.karte_auf("spotify:album:A")
        self.lauf(120)
        self.assertEqual(self.st.ist, ("spielt", "spotify:album:A"))
        self.assertEqual(len(self.starts()), 1)                 # genau ein Start, nicht immer wieder
        self.assertEqual(self.di.neustarts, [])

    def test_falsche_meldung_ohne_lokalen_beleg_wie_bisher(self):
        self.neu(SpotifyMeldetFalsch, lambda: False)
        self.st.karte_auf("spotify:album:A")
        self.lauf(60)
        self.assertGreater(len(self.starts()), 1)               # alte Logik: erneuter Versuch

    def test_zombie_bleibt_erkannt_wenn_librespot_nichts_tut(self):
        self.neu(FakeSpotify, lambda: False)
        self.sp.modus = "zombie"
        self.st.karte_auf("spotify:album:A")
        self.lauf(60)
        self.assertTrue(any("spielt nicht" in m for m in self.meldungen))

    def test_springende_titel_bleiben_erkannt_trotz_last(self):
        """Audio-Key-Fehler: Titel wechseln jede Sekunde. Auch mit CPU-Last kein 'läuft'."""
        self.neu(FakeSpotify, lambda: True)
        self.sp.modus = "springt"
        self.st.karte_auf("spotify:album:A")
        self.lauf(12)
        self.assertNotEqual(self.st.ist, ("spielt", "spotify:album:A"))

    def test_messfuehler_mit_fehler_stoert_nicht(self):
        def kaputt():
            raise RuntimeError("proc weg")
        self.neu(FakeSpotify, kaputt)
        self.st.karte_auf("spotify:album:A")
        self.lauf(10)
        self.assertEqual(self.st.ist, ("spielt", "spotify:album:A"))


class Messfuehler(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.t = [0.0]
        self.f = LibrespotLast(proc=self.tmp.name, jetzt=lambda: self.t[0], tick=100)

    def prozess(self, pid, name, ticks):
        d = os.path.join(self.tmp.name, str(pid))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "comm"), "w") as f:
            f.write(name + "\n")
        # Feld 14/15 = utime/stime; Name mit Leerzeichen und Klammer wie im echten /proc
        with open(os.path.join(d, "stat"), "w") as f:
            f.write(f"{pid} ({name} x) S 1 1 1 0 -1 4194304 0 0 0 0 {ticks} 0 0 0 20 0 1 0 1 1 1\n")

    def test_kein_prozess(self):
        self.assertIsNone(self.f())

    def test_spielt_und_pause(self):
        self.prozess(42, "python3", 999)
        self.prozess(1270, "librespot", 1000)
        self.assertIsNone(self.f())                  # erste Messung: kein Vergleich
        self.t[0] = 2.0
        self.prozess(1270, "librespot", 1016)        # 16 Ticks in 2 s = 8 %
        self.assertTrue(self.f())
        self.t[0] = 4.0
        self.prozess(1270, "librespot", 1017)        # 1 Tick in 2 s = 0,5 %
        self.assertFalse(self.f())

    def test_neuer_prozess_zaehlt_neu(self):
        self.prozess(1270, "librespot", 1000)
        self.f()
        os.rename(os.path.join(self.tmp.name, "1270"), os.path.join(self.tmp.name, "1300"))
        self.t[0] = 2.0
        self.assertIsNone(self.f())                  # Raspotify neu gestartet: erst wieder vergleichen


if __name__ == "__main__":
    unittest.main()
