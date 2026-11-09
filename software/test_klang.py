"""Tests für den Equalizer (klang.py), seine Einstellungen und die Eltern-Seite (/api/klang).
Am echten alsaequal geprüft (09.11.2026, Arbeitsumgebung): amixer -s setzt alle Bänder, Änderungen
wirken in einem laufenden Abspielen sofort, Vorlage "klein" senkt 40 Hz gegenüber 1 kHz um ca. 11 dB.
"""
import os
import tempfile
import unittest
from unittest import mock

import einstellungen
import klang


class Werte(unittest.TestCase):
    def test_db_auf_steuerung(self):
        self.assertEqual(klang.wert(0), 67)          # Eq10: 0 … 100 = -48 … +24 dB
        self.assertEqual(klang.wert(-24), 33)
        self.assertEqual(klang.wert(6), 75)
        self.assertEqual(klang.wert(99), 75)         # begrenzt
        self.assertEqual(klang.wert(-99), 33)

    def test_vorlagen_gueltig(self):
        for name, b in klang.VORLAGEN.items():
            self.assertEqual(len(b), 10, name)
            self.assertTrue(all(klang.MIN_DB <= x <= klang.MAX_DB for x in b), name)
        self.assertEqual(klang.VORLAGEN["neutral"], [0] * 10)

    def test_anwenden_ein_aufruf_mit_allen_baendern(self):
        aufrufe = []

        def amixer(*args, eingabe=None):
            aufrufe.append((args, eingabe))
            return ""
        with mock.patch.object(klang, "_amixer", amixer), mock.patch.object(klang.os, "chmod") as chmod:
            self.assertTrue(klang.anwenden([-24, 0, 0, 0, 0, 0, 0, 0, 0, 6]))
        self.assertEqual(len(aufrufe), 1)
        args, text = aufrufe[0]
        self.assertEqual(args, ("-q", "-s"))
        zeilen = text.splitlines()
        self.assertEqual(zeilen[0], "cset numid=1 33,33")
        self.assertEqual(zeilen[9], "cset numid=10 75,75")
        chmod.assert_called_once_with(klang.DATEI, 0o666)

    def test_anwenden_ohne_equalizer_meldet(self):
        log = []
        with mock.patch.object(klang, "_amixer", lambda *a, **k: None):
            self.assertFalse(klang.anwenden([0] * 10, log=log.append))
        self.assertIn("dienst_einrichten.sh", log[0])
        with self.assertRaises(ValueError):
            klang.anwenden([0] * 9)

    def test_eingerichtet(self):
        zehn = "".join(f"numid={i},iface=MIXER,name='{i}. x Playback Volume'\n" for i in range(10))
        with mock.patch.object(klang, "_amixer", lambda *a, **k: zehn):
            self.assertTrue(klang.eingerichtet())
        with mock.patch.object(klang, "_amixer", lambda *a, **k: None):
            self.assertFalse(klang.eingerichtet())


class Einstellungen(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.dict(os.environ, {"HOME": self.tmp.name})
        p.start()
        self.addCleanup(p.stop)
        einstellungen._cache["mtime"] = None

    def test_standard_neutral_und_speichern(self):
        self.assertEqual(einstellungen.laden()["klang"]["baender"], [0] * 10)
        einstellungen.speichern({"klang": {"baender": klang.VORLAGEN["klein"]}})
        self.assertEqual(einstellungen.laden()["klang"]["baender"], klang.VORLAGEN["klein"])
        self.assertEqual(einstellungen.laden()["bedienung"]["touch_schwelle"], 8)    # Rest bleibt

    def test_ungueltig(self):
        for falsch in ({"baender": [0] * 9}, {"baender": [7] + [0] * 9}, {"baender": [-25] + [0] * 9},
                       {"baender": ["laut"] + [0] * 9}, {"andere": 1}, []):
            with self.assertRaises(ValueError, msg=falsch):
                einstellungen.speichern({"klang": falsch})


if __name__ == "__main__":
    unittest.main()
