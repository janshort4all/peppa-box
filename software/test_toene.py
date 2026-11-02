"""Tests für toene.py (ohne Hardware: aplay, Lautstärke und Laufzeit-Dateien werden nachgebaut).
Aufruf: cd software && python3 -m unittest -v test_toene
"""
import os
import tempfile
import unittest
import wave
from unittest import mock

import einstellungen
import toene


class Toene(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.gespielt = []
        p = mock.patch.object(einstellungen, "lauf_pfad", lambda n: os.path.join(self.tmp.name, n))
        p.start()
        self.addCleanup(p.stop)

    def test_wav_gueltig(self):
        for name, folge in toene.TOENE.items():
            pfad = toene.datei(name, self.tmp.name)
            with wave.open(pfad) as w:
                self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, toene.RATE))
                dauer = w.getnframes() / toene.RATE
            self.assertAlmostEqual(dauer, sum(d for _, d in folge) + 0.05, delta=0.01)

    def test_pegel_und_weiches_ende(self):
        werte = toene.samples(toene.TOENE["bereit"])
        self.assertLessEqual(max(abs(v) for v in werte), int(toene.PEGEL * 32767) + 1)
        self.assertGreater(max(abs(v) for v in werte), 0.2 * 32767)          # hörbar
        n = int(toene.RATE * toene.TOENE["bereit"][0][1])
        self.assertLess(abs(werte[n - 1]), 200)                               # Notenende ohne Knacken
        self.assertEqual(werte[-1], 0)

    def test_geraet_nach_ausgang(self):
        with mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="lautsprecher"):
            self.assertEqual(toene.geraet(), "lautsprecher")
        with mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="kopfhoerer"):
            self.assertEqual(toene.geraet(), "plughw:CARD=Headphones,DEV=0")

    def test_bereit_nur_einmal_je_einschalten(self):
        with mock.patch.object(toene, "spielen", side_effect=lambda n, log=None: self.gespielt.append(n) or True):
            self.assertTrue(toene.einmal_je_einschalten("bereit", log=lambda t: None))
            self.assertFalse(toene.einmal_je_einschalten("bereit", log=lambda t: None))
        self.assertEqual(self.gespielt, ["bereit"])

    def test_spielen_ohne_aplay_haelt_nicht_auf(self):
        meld = []
        with mock.patch.object(toene.shutil, "which", return_value=None):
            self.assertFalse(toene.spielen("start", log=meld.append))
        self.assertIn("aplay fehlt", meld[0])

    def test_spielen_fehler_wird_gemeldet(self):
        meld = []
        r = mock.Mock(returncode=1, stderr="audio open error: Device or resource busy")
        with mock.patch.object(toene.shutil, "which", return_value="/usr/bin/aplay"), \
                mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="lautsprecher"), \
                mock.patch.object(toene, "datei", return_value="/x.wav"), \
                mock.patch.object(toene.subprocess, "run", return_value=r) as run:
            self.assertFalse(toene.spielen("start", warten=True, log=meld.append))
        self.assertEqual(run.call_args[0][0], ["/usr/bin/aplay", "-q", "-D", "lautsprecher", "/x.wav"])
        self.assertIn("busy", meld[0])

    def test_startton_in_ruhezeit_still(self):
        with mock.patch.object(einstellungen, "musik_gesperrt", return_value=True), \
                mock.patch.object(einstellungen, "laden", return_value={}), \
                mock.patch.object(toene, "spielen") as sp:
            self.assertTrue(toene.startton(log=lambda t: None))
        sp.assert_not_called()

    def test_startton_setzt_startlautstaerke_nur_am_lautsprecher(self):
        import automatik
        for ausgang, erwartet in (("lautsprecher", 1), ("kopfhoerer", 0)):
            with mock.patch.object(einstellungen, "musik_gesperrt", return_value=False), \
                    mock.patch.object(einstellungen, "laden", return_value={}), \
                    mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value=ausgang), \
                    mock.patch.object(automatik.Automatik, "beim_start") as bs, \
                    mock.patch.object(toene, "spielen", return_value=True) as sp:
                self.assertTrue(toene.startton(log=lambda t: None))
            self.assertEqual(bs.call_count, erwartet, ausgang)
            sp.assert_called_once()


if __name__ == "__main__":
    unittest.main()
