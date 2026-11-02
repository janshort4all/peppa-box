"""Tests für toene.py (Ansage „Peppa Box bereit“), ohne Hardware: aplay, Lautstärke und
Laufzeit-Dateien werden nachgebaut.
Aufruf: cd software && python3 -m unittest -v test_toene
"""
import os
import tempfile
import unittest
import wave
from unittest import mock

import einstellungen
import toene


class Ansage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(einstellungen, "lauf_pfad", lambda n: os.path.join(self.tmp.name, n))
        p.start()
        self.addCleanup(p.stop)

    def test_datei_vorhanden_und_abspielbar(self):
        with wave.open(toene.datei("bereit")) as w:
            self.assertEqual((w.getnchannels(), w.getsampwidth()), (1, 2))
            self.assertIn(w.getframerate(), (22050, 44100, 48000))
            self.assertTrue(1.0 < w.getnframes() / w.getframerate() < 5.0)

    def test_geraet_nach_ausgang(self):
        with mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="lautsprecher"):
            self.assertEqual(toene.geraet(), "lautsprecher")
        with mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="kopfhoerer"):
            self.assertEqual(toene.geraet(), "plughw:CARD=Headphones,DEV=0")

    def test_nur_einmal_je_einschalten(self):
        gespielt = []
        with mock.patch.object(toene, "spielen", side_effect=lambda n, log=None: gespielt.append(n) or True):
            self.assertTrue(toene.einmal_je_einschalten("bereit", log=lambda t: None))
            self.assertFalse(toene.einmal_je_einschalten("bereit", log=lambda t: None))
        self.assertEqual(gespielt, ["bereit"])

    def test_ohne_aplay_haelt_nicht_auf(self):
        meld = []
        with mock.patch.object(toene.shutil, "which", return_value=None):
            self.assertFalse(toene.spielen("bereit", log=meld.append))
        self.assertIn("aplay fehlt", meld[0])

    def test_fehlende_datei_wird_gemeldet(self):
        meld = []
        with mock.patch.object(toene.shutil, "which", return_value="/usr/bin/aplay"), \
                mock.patch.object(toene, "ORDNER", self.tmp.name):
            self.assertFalse(toene.spielen("bereit", log=meld.append))
        self.assertIn("fehlt", meld[0])

    def test_aufruf_und_fehlermeldung(self):
        meld = []
        r = mock.Mock(returncode=1, stderr="audio open error: Device or resource busy")
        with mock.patch.object(toene.shutil, "which", return_value="/usr/bin/aplay"), \
                mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="lautsprecher"), \
                mock.patch.object(toene.subprocess, "run", return_value=r) as run:
            self.assertFalse(toene.spielen("bereit", warten=True, log=meld.append))
        self.assertEqual(run.call_args[0][0], ["/usr/bin/aplay", "-q", "-D", "lautsprecher", toene.datei("bereit")])
        self.assertIn("busy", meld[0])


if __name__ == "__main__":
    unittest.main()
