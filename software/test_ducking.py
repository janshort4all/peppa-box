"""Tests: Ansage in die Musik mischen, Musik weich absenken (ausgabe.Mischer, toene.mischen)."""
import array
import json
import math
import os
import sys
import tempfile
import threading
import time
import unittest
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ausgabe  # noqa: E402

RATE = 44100


def musik(sek, wert=10000):
    return array.array("h", [wert, wert] * int(RATE * sek)).tobytes()


def werte(b):
    return array.array("h", b)


class Mischer(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.auftrag = os.path.join(self.d, "a.json")
        self.pcm = os.path.join(self.d, "a.raw")
        self.m = ausgabe.Mischer(auftrag=self.auftrag, status=os.path.join(self.d, "s.json"))

    def auftragen(self, ansage, kennung="1"):
        if ansage is not None:
            with open(self.pcm, "wb") as f:
                f.write(ansage)
        with open(self.auftrag, "w") as f:
            json.dump({"id": kennung, "pcm": self.pcm if ansage is not None else None, "bis": time.time() + 1}, f)
        return self.m.auftrag_pruefen()

    def strom(self, sek, stueck=4093):          # krumme Stücke: Frames über Stückgrenzen
        roh = musik(sek)
        return b"".join(self.m.verarbeiten(roh[i:i + stueck]) for i in range(0, len(roh), stueck))

    def test_ohne_ansage_unveraendert(self):
        roh = musik(0.5)
        self.assertEqual(b"".join(self.m.verarbeiten(roh[i:i + 999]) for i in range(0, len(roh), 999)), roh)

    def test_absenken_ansage_zurueck_weich(self):
        ansage = array.array("h", [3000, 3000] * int(RATE * 1.0)).tobytes()
        self.assertTrue(self.auftragen(ansage))
        out = werte(self.strom(4.0))[0::2]
        unten = 10000 * 10 ** (ausgabe.DUCK_DB / 20)
        vor = int(ausgabe.VORLAUF_S * RATE)
        # vor der Ansage schon fast unten, dann Ansage drauf
        self.assertLess(out[vor - 1], 10000 * 0.4)
        self.assertAlmostEqual(out[vor + 1000], unten + 3000, delta=60)
        # nach Ansage + Halten + Auf wieder voll
        self.assertEqual(out[-1], 10000)
        # weich: Musikteil springt nie stark (außer an Beginn/Ende der Ansage selbst)
        sprung = [abs(out[i + 1] - out[i]) for i in range(len(out) - 1)
                  if i not in (vor - 1, vor + RATE - 1)]
        self.assertLess(max(sprung), 40)
        # Halten: kurz nach Ansageende noch unten
        ende = vor + RATE
        self.assertAlmostEqual(out[ende + int(0.2 * RATE)], unten, delta=30)

    def test_stopp_hebt_wieder(self):
        self.auftragen(array.array("h", [1, 1] * RATE * 5).tobytes())
        self.strom(1.0)
        self.assertTrue(self.auftragen(None, "2"))
        out = werte(self.strom(2.0))[0::2]
        self.assertEqual(out[-1], 10000)

    def test_abgelaufen_oder_doppelt_ignoriert(self):
        self.assertTrue(self.auftragen(b"\0" * 400))
        self.assertFalse(self.m.auftrag_pruefen())
        with open(self.auftrag, "w") as f:
            json.dump({"id": "x", "pcm": self.pcm, "bis": time.time() - 1}, f)
        self.assertFalse(self.m.auftrag_pruefen())

    def test_uebersteuern_begrenzt(self):
        self.auftragen(array.array("h", [32000, -32000] * RATE).tobytes())
        roh = array.array("h", [32000, -32000] * RATE).tobytes()
        out = werte(self.m.verarbeiten(roh))
        self.assertLessEqual(max(out), 32767)
        self.assertGreaterEqual(min(out), -32768)


class TonePfad(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.environ.update(PEPPA_ANSAGE_AUFTRAG=os.path.join(self.d, "a.json"),
                          PEPPA_ANSAGE_PCM=os.path.join(self.d, "a.raw"),
                          PEPPA_AUSGABE_STATUS=os.path.join(self.d, "s.json"))
        import importlib
        import toene
        self.t = importlib.reload(toene)
        self.wav = os.path.join(self.d, "x.wav")
        with wave.open(self.wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
            w.writeframes(array.array("h", [int(8000 * math.sin(i / 10)) for i in range(16000)]).tobytes())

    def tearDown(self):
        for k in ("PEPPA_ANSAGE_AUFTRAG", "PEPPA_ANSAGE_PCM", "PEPPA_AUSGABE_STATUS"):
            os.environ.pop(k, None)

    def test_umrechnen_auf_44100_stereo(self):
        pcm = self.t._pcm_stereo(self.wav)
        self.assertAlmostEqual(len(pcm) / 4, 44100, delta=2)
        w = werte(pcm)
        self.assertEqual(w[100], w[101])

    def test_ohne_musik_kein_mischen(self):
        self.assertIsNone(self.t.mischen(self.wav, log=lambda *_: None))

    def test_mit_tonausgabe_gemischt_und_stoppbar(self):
        m = ausgabe.Mischer(auftrag=os.environ["PEPPA_ANSAGE_AUFTRAG"], status=os.environ["PEPPA_AUSGABE_STATUS"])
        m.status_schreiben()
        ende = threading.Event()

        def ausgabe_lauf():
            while not ende.wait(0.05):
                if m.auftrag_pruefen():
                    m.status_schreiben()
        threading.Thread(target=ausgabe_lauf, daemon=True).start()
        try:
            g = self.t.mischen(self.wav, log=print)
            self.assertIsNotNone(g)
            self.assertIsNotNone(m.ansage)
            self.assertIsNone(g.poll())
            g.terminate()
            self.assertEqual(g.wait(1), -15)
            time.sleep(0.2)
            self.assertIsNone(m.ansage)
        finally:
            ende.set()

    def test_ohne_quittung_selbst_spielen(self):
        m = ausgabe.Mischer(auftrag=os.environ["PEPPA_ANSAGE_AUFTRAG"], status=os.environ["PEPPA_AUSGABE_STATUS"])
        m.status_schreiben()                     # lebt, quittiert aber nie
        self.assertIsNone(self.t.mischen(self.wav, log=lambda *_: None))


if __name__ == "__main__":
    unittest.main()
