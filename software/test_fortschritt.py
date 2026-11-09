"""Tests für das Weiterspielen an der gemerkten Stelle (fortschritt.py) und die Stelle aus den
librespot-Ereignissen (rueckmeldung.py). Wunsch Jan 09.11.2026: nach Unterbrechungen nie von vorn."""
import json
import os
import tempfile
import unittest

import fortschritt
import rueckmeldung


class Uhr:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class Merken(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.datei = os.path.join(self.tmp.name, "sub", "fortschritt.json")
        self.wand, self.mono = Uhr(1_800_000_000.0), Uhr()
        self.f = fortschritt.Fortschritt(self.datei, uhr=self.wand, jetzt=self.mono, log=lambda t: None)

    def neu(self):
        return fortschritt.Fortschritt(self.datei, uhr=self.wand, jetzt=self.mono, log=lambda t: None)

    def test_stelle_3_s_zurueck_und_ueber_neustart(self):
        self.f.merken("spotify:album:A", "spotify:track:t1", 65000)
        self.assertEqual(self.f.stelle("spotify:album:A"), {"titel": "spotify:track:t1", "position_ms": 62000})
        self.assertEqual(self.neu().stelle("spotify:album:A")["titel"], "spotify:track:t1")   # Titelwechsel: sofort

    def test_position_spart_sd_karte(self):
        self.f.merken("k", "spotify:track:t1", 1000)
        self.mono.t += 5
        self.f.merken("k", "spotify:track:t1", 6000)           # gleicher Titel: erst nach 15 s auf die Karte
        self.assertEqual(self.neu().stelle("k")["position_ms"], 0)
        self.mono.t += 11
        self.f.merken("k", "spotify:track:t1", 17000)
        self.assertEqual(self.neu().stelle("k")["position_ms"], 14000)
        self.f.merken("k", "spotify:track:t1", 18000)
        self.f.sichern(sofort=True)                             # Pause/Ende: sofort
        self.assertEqual(self.neu().stelle("k")["position_ms"], 15000)

    def test_vergessen_und_veraltet(self):
        self.f.merken("a", "spotify:track:x", 50000)
        self.f.vergessen("a")
        self.assertIsNone(self.neu().stelle("a"))
        self.f.merken("b", "spotify:track:y", 50000)
        self.wand.t += 31 * 86400
        self.assertIsNone(self.f.stelle("b"))

    def test_unsinn_wird_nicht_gemerkt_und_kaputte_datei_stoert_nicht(self):
        self.f.merken("a", None, 1)
        self.f.merken("a", "kein-link", 1)
        self.f.merken(None, "spotify:track:x", 1)
        self.assertIsNone(self.f.stelle("a"))
        os.makedirs(os.path.dirname(self.datei), exist_ok=True)
        with open(self.datei, "w") as f:
            f.write("{kaputt")
        self.assertIsNone(self.neu().stelle("a"))
        with open(self.datei, "w") as f:
            json.dump({"x": "falsch", "y": {"titel": 3}}, f)
        self.assertEqual(self.neu()._daten, {})


class StelleAusEreignissen(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.r = rueckmeldung.Rueckmeldung(jetzt=self.uhr, log=lambda t: None)

    def e(self, name, **k):
        self.r.verarbeiten(dict({"q": "ereignis", "player_event": name}, **k))

    def test_position_laeuft_mit(self):
        self.e("track_changed", track_id="t1", uri="spotify:track:t1", duration_ms="200000")
        self.e("playing", track_id="t1", position_ms="30000")
        self.uhr.t += 10
        self.assertEqual(self.r.stelle(), ("spotify:track:t1", 40000))
        self.e("paused", track_id="t1", position_ms="41000")
        self.uhr.t += 100
        self.assertIsNone(self.r.stelle())                     # in Pause nichts merken (Stelle bleibt)
        self.assertEqual(self.r.position(), 41000)
        self.e("playing", track_id="t1", position_ms="41000")
        self.uhr.t += 500
        self.assertEqual(self.r.stelle(), ("spotify:track:t1", 200000))   # nie über das Titelende

    def test_neuer_titel_beginnt_bei_null(self):
        self.e("track_changed", track_id="t1", uri="spotify:track:t1", duration_ms="100000")
        self.e("playing", track_id="t1", position_ms="90000")
        self.e("track_changed", track_id="t2", uri="spotify:track:t2", duration_ms="100000")
        self.e("playing", track_id="t2", position_ms="0")
        self.uhr.t += 2
        self.assertEqual(self.r.stelle(), ("spotify:track:t2", 2000))


if __name__ == "__main__":
    unittest.main()
