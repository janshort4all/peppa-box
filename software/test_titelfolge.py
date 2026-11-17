"""Titelfolge (17.11.2026): librespot springt beim Titelende 2–3 Titel weiter (#1848), und der Start an der
gemerkten Stelle landet auf einem anderen Titel ("using fallback index"). Aufruf:
cd software && python3 -m unittest -v test_titelfolge
"""
import os
import tempfile
import unittest

import rueckmeldung
import titelfolge
import titelliste
from steuerung import Steuerung
from test_steuerung import FakeDienste, FakeSpotify, Uhr

K = "spotify:playlist:HOERSPIEL"
T = [f"spotify:track:k{i}" for i in range(1, 9)]


class Liste(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pfad = os.path.join(self.tmp.name, "titellisten.json")
        self.aufrufe = []

    def listen(self, antworten):
        def api(methode, pfad, params=None):
            self.aufrufe.append((pfad, dict(params or {})))
            return antworten.pop(0)
        return titelliste.Titellisten(api=api, pfad=self.pfad, uhr=lambda: 1000.0, log=lambda t: None)

    def test_playlist_neue_felder_mehrere_seiten(self):
        l = self.listen([(200, {"items": [{"item": {"uri": u}} for u in T[:5]], "next": "x"}),
                         (200, {"items": [{"track": {"uri": u}} for u in T[5:]], "next": None})])
        self.assertEqual(l.holen(K), T)
        self.assertEqual(self.aufrufe[0][0], "/playlists/HOERSPIEL/items")
        self.assertEqual(self.aufrufe[1][1]["offset"], 50)
        self.assertEqual(l.liste(K), T)
        self.assertEqual(l.holen(K), T)                   # gespeichert: keine weitere Anfrage
        self.assertEqual(len(self.aufrufe), 2)
        neu = titelliste.Titellisten(api=None, pfad=self.pfad, log=lambda t: None)
        self.assertEqual(neu.liste(K), T)                 # übersteht einen Neustart

    def test_fremde_playlist_ohne_inhalt(self):
        l = self.listen([(403, None)])
        self.assertIsNone(l.holen(K))
        self.assertIsNone(l.holen(K))                     # Fehlschlag wird gemerkt, keine zweite Anfrage
        self.assertEqual(len(self.aufrufe), 1)

    def test_album(self):
        l = self.listen([(200, {"items": [{"uri": u} for u in T[:3]], "next": None})])
        self.assertEqual(l.holen("spotify:album:ALB"), T[:3])
        self.assertEqual(self.aufrufe[0][0], "/albums/ALB/tracks")

    def test_nachfolger_mit_doppeltem_titel(self):
        liste = [T[0], T[1], T[0], T[2]]
        self.assertEqual(titelliste.nachfolger(liste, T[0]), {T[1], T[2]})
        self.assertIsNone(titelliste.nachfolger(liste, T[5]))


class Uebergang(unittest.TestCase):
    def ereignis(self, r, **n):
        r.verarbeiten(dict(q="ereignis", **n))

    def test_natuerlich_und_taste(self):
        uhr = Uhr()
        r = rueckmeldung.Rueckmeldung(jetzt=uhr, log=lambda t: None)
        self.ereignis(r, player_event="track_changed", uri=T[0], track_id="k1")
        self.ereignis(r, player_event="playing", track_id="k1")
        uhr.t += 100
        self.ereignis(r, player_event="end_of_track", track_id="k1")
        self.ereignis(r, player_event="track_changed", uri=T[3], track_id="k4")
        self.assertEqual(r.uebergang[1:4], (T[0], T[3], True))
        uhr.t += 30
        self.ereignis(r, player_event="track_changed", uri=T[4], track_id="k5")   # Taste "vor"
        self.assertEqual(r.uebergang[1:4], (T[3], T[4], False))
        self.assertEqual(r.uebergang[0], 3)                # auch der erste Titel zählt (vorher None)


class FakeSt:
    def __init__(self):
        self.ist = ("spielt", K)
        self.korrekturen = []

    def titel_korrigieren(self, uri, titel, index=None):
        self.korrekturen.append((uri, titel, index))


class FakeListen:
    def __init__(self, liste):
        self._l, self.geholt = liste, []

    def liste(self, uri):
        return self._l

    def im_hintergrund(self, uri):
        self.geholt.append(uri)


class Wache(unittest.TestCase):
    def setUp(self):
        self.st, self.uhr, self.log = FakeSt(), Uhr(), []
        self.listen = FakeListen(T)
        self.w = titelfolge.Titelfolge(self.st, None, self.listen, log=self.log.append, jetzt=self.uhr)

    def test_sprung_wird_korrigiert(self):
        self.assertEqual(self.w.pruefen(K, T[1], T[4], True), T[2])
        self.assertEqual(self.st.korrekturen, [(K, T[2], 2)])
        self.assertTrue(any("übersprungen: 2" in t for t in self.log))

    def test_normaler_uebergang_rueckwaerts_taste_unbekannt(self):
        self.assertIsNone(self.w.pruefen(K, T[1], T[2], True))
        self.assertIsNone(self.w.pruefen(K, T[4], T[1], True))
        self.assertIsNone(self.w.pruefen(K, T[1], T[4], False))
        self.assertIsNone(self.w.pruefen(K, T[1], "spotify:track:fremd", True))
        self.assertIsNone(self.w.pruefen(K, T[7], T[0], True))     # Listenende, Wiederholung
        self.assertEqual(self.st.korrekturen, [])

    def test_ohne_liste_nichts(self):
        self.listen._l = None
        self.assertIsNone(self.w.pruefen(K, T[1], T[4], True))
        self.assertTrue(any("keine Titelliste" in t for t in self.log))

    def test_hoechstens_drei_in_zehn_minuten(self):
        for _ in range(5):
            self.w.pruefen(K, T[1], T[4], True)
        self.assertEqual(len(self.st.korrekturen), 3)
        self.uhr.t += 601
        self.w.pruefen(K, T[1], T[4], True)
        self.assertEqual(len(self.st.korrekturen), 4)

    def test_tick_holt_liste_und_wertet_jeden_uebergang_einmal(self):
        class R:
            uebergang = (1, T[1], T[4], True, 0)
        self.w.rueck = R()
        self.w.tick()
        self.w.tick()
        self.assertEqual(self.listen.geholt, [K])
        self.assertEqual(len(self.st.korrekturen), 1)


class SpotifyMitTiteln(FakeSpotify):
    """Kennt Titel: Start mit Titel-URI landet (wie am 17.11. 18:42) auf Titel 1, mit Nummer richtig."""

    def __init__(self, uhr):
        super().__init__(uhr)
        self.titel_jetzt, self.shuffle, self.aufrufe = None, False, []
        self.uri_geht = False

    def abspielen(self, dev, uri, titel=None, position_ms=0, index=None):
        self.aufrufe.append((titel, index, position_ms))
        st, d = super().abspielen(dev, uri, titel, position_ms)
        if index is not None:
            self.titel_jetzt = T[index]
        else:
            self.titel_jetzt = titel if (self.uri_geht or not titel) else T[0]
        return st, d

    def zustand(self):
        z = super().zustand()
        if z and not z.get("leer"):
            z.update(titel_uri=self.titel_jetzt, kontext=K, shuffle=self.shuffle)
        return z


class Fortschritt:
    def __init__(self, stelle):
        self._s, self.gemerkt = stelle, []

    def stelle(self, uri):
        return self._s

    def merken(self, karte, titel, pos):
        self.gemerkt.append(titel)

    def vergessen(self, uri):
        pass


class MitSteuerung(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.sp = SpotifyMitTiteln(self.uhr)
        self.di = FakeDienste(self.sp)
        self.log = []
        self.fs = Fortschritt({"titel": T[4], "position_ms": 90000})
        ton = lambda: self.sp.spielend and self.sp.modus == "gut"
        self.st = Steuerung(self.sp, self.di, jetzt=self.uhr, log=self.log.append, lokal=ton, ton=ton,
                            zu_ende=lambda: False, fortschritt=self.fs, titelliste=lambda uri: T)
        self.lauf(3)

    def lauf(self, s):
        ende = self.uhr.t + s
        while self.uhr.t < ende:
            self.st.tick()
            self.uhr.t += 0.25

    def test_falscher_titel_nach_start_wird_ueber_nummer_korrigiert(self):
        self.st.karte_auf(K)
        self.lauf(20)
        self.assertEqual(self.st.ist, ("spielt", K))
        self.assertEqual(self.sp.titel_jetzt, T[4])
        self.assertEqual(self.sp.aufrufe, [(T[4], None, 90000), (T[4], 4, 90000)])
        self.assertNotIn(T[0], self.fs.gemerkt)           # die falsche Stelle wurde nie gemerkt
        self.assertTrue(any("Falscher Titel nach dem Start" in t for t in self.log))

    def test_richtiger_titel_keine_korrektur(self):
        self.sp.uri_geht = True
        self.st.karte_auf(K)
        self.lauf(20)
        self.assertEqual(self.sp.aufrufe, [(T[4], None, 90000)])

    def test_titelfolge_korrektur_und_zufall(self):
        self.sp.uri_geht = True
        self.st.karte_auf(K)
        self.lauf(15)
        self.st.titel_korrigieren(K, T[2], 2)
        self.lauf(2)
        self.assertEqual(self.sp.aufrufe[-1], (T[2], 2, 0))
        self.sp.shuffle = True
        n = len(self.sp.aufrufe)
        self.st.titel_korrigieren(K, T[3], 3)
        self.lauf(2)
        self.assertEqual(len(self.sp.aufrufe), n)        # Zufallswiedergabe: keine Korrektur
        self.assertTrue(any("Zufallswiedergabe" in t for t in self.log))


if __name__ == "__main__":
    unittest.main()
