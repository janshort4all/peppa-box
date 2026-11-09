"""Tests: leiser Klick beim Antippen von zurück, Play und vor (Wunsch Jan 09.11.2026).
Nicht beim Mond (Schlummer), nicht bei der Ein-Taste. Aufruf: cd software && python3 -m unittest -v test_klick
"""
import array
import json
import os
import tempfile
import time
import unittest
import wave
from unittest import mock

import ausgabe
import einstellungen
import test_bedienung
import toene


class Bedienung(test_bedienung.Basis):
    def setUp(self):
        super().setUp()
        self.klicks = 0

        def klick():
            self.klicks += 1
        self.b.klick_roh = klick

    def test_drei_felder_klicken_einmal_je_beruehrung(self):
        for f in ("zurueck", "play", "vor"):
            self.tippen(f)
        self.assertEqual(self.klicks, 3)

    def test_mond_klickt_nie(self):
        self.tippen("schlaf")
        self.lauf(1)
        self.b.felder({"schlaf"}, self.uhr.t)
        self.lauf(6, felder={"schlaf"})          # 5 s halten = Akku-Ansage
        self.b.felder(set(), self.uhr.t)
        self.assertEqual(self.klicks, 0)

    def test_ein_taste_klickt_nie(self):
        self.lauf(0.1, taste=False)
        self.lauf(0.3, taste=True)
        self.lauf(0.3, taste=False)
        self.assertEqual(self.klicks, 0)

    def test_klick_schon_beim_beruehren_nicht_erst_beim_loslassen(self):
        self.b.felder({"vor"}, self.uhr.t)
        self.lauf(0.1, felder={"vor"})
        self.assertEqual(self.klicks, 1)
        self.lauf(2.0, felder={"vor"})            # halten = spulen: trotzdem nur ein Klick
        self.b.felder(set(), self.uhr.t)
        self.assertEqual(self.klicks, 1)

    def test_play_halten_ein_klick(self):
        self.b.felder({"play"}, self.uhr.t)
        self.lauf(2.5, felder={"play"})
        self.b.felder(set(), self.uhr.t)
        self.assertEqual(self.klicks, 1)

    def test_rauschen_unter_70_ms_klickt_nicht(self):
        self.b.felder({"play"}, self.uhr.t)
        self.uhr.t += 0.04
        self.b.felder(set(), self.uhr.t)
        self.b.tick(self.uhr.t)
        self.assertEqual(self.klicks, 0)

    def test_loslassen_vor_dem_naechsten_durchlauf_klickt_trotzdem(self):
        self.b.felder({"zurueck"}, self.uhr.t)
        self.uhr.t += 0.09                        # kein tick dazwischen
        self.b.felder(set(), self.uhr.t)
        self.assertEqual(self.klicks, 1)

    def test_mehrere_felder_klicken_nicht(self):
        self.b.felder({"play", "vor"}, self.uhr.t)
        self.lauf(0.3, felder={"play", "vor"})
        self.b.felder(set(), self.uhr.t)
        self.assertEqual(self.klicks, 0)

    def test_klick_fehler_haelt_nichts_auf(self):
        def kaputt():
            raise OSError("weg")
        self.b.klick_roh = kaputt
        self.tippen("vor")                        # darf nicht werfen


class Klicker(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        p = mock.patch.object(einstellungen, "LAUF", self.d)
        p.start()
        self.addCleanup(p.stop)
        for name, wert in (("KLICK_AUFTRAG", os.path.join(self.d, "klick.json")),
                           ("KLICK_PCM", os.path.join(self.d, "klick.raw")),
                           ("MISCH_STATUS", os.path.join(self.d, "status.json"))):
            p = mock.patch.object(toene, name, wert)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.object(toene, "kopfhoerer_geraet", lambda: "kopfhoerer")
        p.start()
        self.addCleanup(p.stop)
        self.aufrufe = []

        class P:
            def __init__(s, cmd, **kw):
                self.aufrufe.append(cmd)
                s.beendet = False

            def poll(s):
                return 0 if s.beendet else None

            def terminate(s):
                s.beendet = True

            def wait(s, timeout=None):
                return 0
        self.P = P

    def klicker(self, ausgang="lautsprecher", pegel=15):
        return toene.Klicker(log=lambda t: None, popen=self.P, pegel=lambda: pegel, ausgang=lambda: ausgang)

    def test_datei_ist_jans_klick(self):
        with wave.open(toene.KLICK_DATEI) as w:
            self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (2, 2, 44100))
            self.assertLess(w.getnframes() / 44100, 0.4)
            roh = array.array("h", w.readframes(w.getnframes()))
        anfang = next(i for i, v in enumerate(roh) if abs(v) > 0.002 * 32768) / 2 / 44100
        self.assertLess(anfang, 0.005)            # keine Stille vorne: klickt sofort
        self.assertGreater(max(abs(v) for v in roh), 25000)

    def test_lautsprecher_in_den_mischer_leise(self):
        weg = self.klicker().spielen()
        self.assertEqual(weg, "lautsprecher")
        cmd = self.aufrufe[0]
        self.assertEqual(cmd[cmd.index("-D") + 1], "lautsprecher")
        with wave.open(toene.KLICK_DATEI) as w:
            voll = max(abs(v) for v in array.array("h", w.readframes(w.getnframes())))
        with wave.open(cmd[-1]) as w:
            leise = max(abs(v) for v in array.array("h", w.readframes(w.getnframes())))
        self.assertAlmostEqual(leise / voll, 0.15, delta=0.002)

    def test_aus_bei_null(self):
        self.assertIsNone(self.klicker(pegel=0).spielen())
        self.assertEqual(self.aufrufe, [])

    def test_kopfhoerer_ohne_musik_direkt_und_vorigen_beenden(self):
        k = self.klicker("kopfhoerer")
        k.spielen()
        erster = toene._klick_proc
        k.spielen()
        self.assertTrue(erster.beendet)
        self.assertEqual(self.aufrufe[-1][self.aufrufe[-1].index("-D") + 1], "kopfhoerer")
        toene.klick_freigeben()                   # Ansage bekommt die Pi-Klinke
        self.assertIsNone(toene._klick_proc)

    def test_kopfhoerer_mit_musik_in_den_strom(self):
        with open(toene.MISCH_STATUS, "w") as f:
            json.dump({"pid": os.getpid(), "t": time.time(), "klick": True}, f)
        weg = self.klicker("kopfhoerer").spielen()
        self.assertEqual(weg, "gemischt")
        self.assertEqual(self.aufrufe, [])
        with open(toene.KLICK_AUFTRAG) as f:
            a = json.load(f)
        self.assertEqual(a["pcm"], toene.KLICK_PCM)

    def test_alte_tonausgabe_ohne_klick_direkt(self):
        with open(toene.MISCH_STATUS, "w") as f:
            json.dump({"pid": os.getpid(), "t": time.time()}, f)
        self.assertEqual(self.klicker("kopfhoerer").spielen(), "kopfhoerer")

    def test_faden_klickt(self):
        k = self.klicker()
        k.starten()
        k.klick()
        for _ in range(100):
            if self.aufrufe:
                break
            time.sleep(0.01)
        self.assertEqual(len(self.aufrufe), 1)


class Mischer(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.ka = os.path.join(self.d, "k.json")
        self.m = ausgabe.Mischer(auftrag=os.path.join(self.d, "a.json"), status=os.path.join(self.d, "s.json"),
                                 klick_auftrag=self.ka)

    def klick(self, werte, kennung="1"):
        pcm = os.path.join(self.d, "k.raw")
        with open(pcm, "wb") as f:
            f.write(array.array("h", werte).tobytes())
        with open(self.ka, "w") as f:
            json.dump({"id": kennung, "pcm": pcm, "bis": time.time() + 1}, f)
        return self.m.klick_pruefen()

    def test_klick_ohne_absenken_dazugemischt(self):
        self.assertTrue(self.klick([1000, 1000] * 100))
        musik = array.array("h", [5000, 5000] * 300).tobytes()
        aus = array.array("h", self.m.verarbeiten(musik))
        self.assertEqual(aus[0], 6000)            # Musik bleibt voll, Klick obendrauf
        self.assertEqual(aus[2 * 100], 5000)      # danach unverändert
        self.assertIsNone(self.m.klick)
        self.assertEqual(self.m.verarbeiten(musik), musik)

    def test_klick_ueber_mehrere_stuecke_und_begrenzt(self):
        self.klick([30000, 30000] * 300)
        musik = array.array("h", [10000, 10000] * 200).tobytes()
        a = array.array("h", self.m.verarbeiten(musik))
        self.assertEqual(max(a), 32767)
        self.assertIsNotNone(self.m.klick)
        self.m.verarbeiten(musik)
        self.assertIsNone(self.m.klick)

    def test_gleicher_auftrag_nur_einmal_abgelaufener_nie(self):
        self.assertTrue(self.klick([1, 1]))
        self.assertFalse(self.m.klick_pruefen())
        with open(self.ka, "w") as f:
            json.dump({"id": "2", "pcm": os.path.join(self.d, "k.raw"), "bis": time.time() - 1}, f)
        self.assertFalse(self.m.klick_pruefen())

    def test_klick_waehrend_ansage(self):
        pcm = os.path.join(self.d, "a.raw")
        with open(pcm, "wb") as f:
            f.write(array.array("h", [0, 0] * 44100).tobytes())
        with open(os.path.join(self.d, "a.json"), "w") as f:
            json.dump({"id": "x", "pcm": pcm, "bis": time.time() + 1}, f)
        self.m.auftrag_pruefen()
        self.klick([500, 500] * 10)
        aus = array.array("h", self.m.verarbeiten(array.array("h", [0, 0] * 512).tobytes()))
        self.assertEqual(aus[0], 500)

    def test_status_meldet_klick(self):
        self.m.status_schreiben()
        with open(os.path.join(self.d, "s.json")) as f:
            self.assertTrue(json.load(f)["klick"])


class Einstellung(unittest.TestCase):
    def test_standard_und_grenzen(self):
        self.assertEqual(einstellungen.STANDARD["bedienung"]["klick"], 30)
        self.assertEqual(einstellungen.bereinigen({"bedienung": {"klick": 0}}, einstellungen.STANDARD)["bedienung"]["klick"], 0)
        with self.assertRaises(ValueError):
            einstellungen.bereinigen({"bedienung": {"klick": 101}}, einstellungen.STANDARD)


if __name__ == "__main__":
    unittest.main()
