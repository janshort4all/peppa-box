"""Tests für toene.py (Ansagen), ohne Hardware: aplay, pico2wave, Lautstärke und Laufzeit-Dateien
werden nachgebaut. Aufruf: cd software && python3 -m unittest -v test_toene
"""
import array
import os
import stat
import subprocess
import tempfile
import threading
import time
import unittest
import wave
from unittest import mock

import einstellungen
import toene


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(einstellungen, "lauf_pfad", lambda n: os.path.join(self.tmp.name, n))
        p.start()
        self.addCleanup(p.stop)
        self.cache = os.path.join(self.tmp.name, "cache")
        p = mock.patch.object(toene, "CACHE", self.cache)
        p.start()
        self.addCleanup(p.stop)
        self.bin = os.path.join(self.tmp.name, "bin")
        os.mkdir(self.bin)

    def programm(self, name, inhalt):
        p = os.path.join(self.bin, name)
        with open(p, "w") as f:
            f.write("#!/bin/sh\n" + inhalt + "\n")
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
        return p

    def nur(self, *namen):
        """shutil.which findet nur diese Programme (aus self.bin)."""
        def which(n):
            p = os.path.join(self.bin, n)
            return p if n in namen and os.path.exists(p) else None
        return mock.patch.object(toene.shutil, "which", side_effect=which)


class Katalog(Basis):
    def test_aufnahme_bereit_vorhanden_und_abspielbar(self):
        with wave.open(toene.datei("bereit")) as w:
            self.assertEqual((w.getnchannels(), w.getsampwidth()), (1, 2))
            self.assertIn(w.getframerate(), (22050, 44100, 48000))
            self.assertTrue(1.0 < w.getnframes() / w.getframerate() < 5.0)

    def test_alle_ansagen_haben_text_und_akku_stufen(self):
        for p in range(10, 101, 10):
            self.assertIn(f"akku_{p}", toene.ANSAGEN)
        for m in (15, 30, 45, 60):
            self.assertIn(f"timer_{m}", toene.ANSAGEN)
        for n in ("tschuess", "karte_leer", "karte_auflegen", "ruhezeit", "moment", "kein_internet",
                  "anmeldung", "timer_aus", "akku_laedt", "akku_voll", "akku_schwach", "akku_leer", "akku_unbekannt"):
            self.assertTrue(toene.ANSAGEN[n].strip(), n)

    def test_texte_datei_vollstaendig(self):
        with open(os.path.join(toene.ORDNER, "TEXTE.md"), encoding="utf-8") as f:
            texte = f.read()
        for n, t in toene.ANSAGEN.items():
            self.assertIn(os.path.basename(toene.datei(n)), texte, n)
            self.assertIn(t, texte, n)

    def test_geraet_nach_ausgang(self):
        with mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="lautsprecher"):
            self.assertEqual(toene.geraet(), "lautsprecher")
        asound = os.path.join(self.tmp.name, "asound.conf")
        with mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="kopfhoerer"), \
                mock.patch.object(toene, "ASOUND", asound):
            self.assertEqual(toene.geraet(), "plughw:CARD=Headphones,DEV=0")       # Mischer fehlt
            with open(asound, "w") as f:
                f.write("pcm.kopfhoerer {\n    type plug\n}\n")
            self.assertEqual(toene.geraet(), "kopfhoerer")


class Quelle(Basis):
    def test_aufnahme_vor_sprache(self):
        self.assertEqual(toene.quelle("bereit")[1], "aufnahme")

    def test_sprache_mit_pico_erzeugt_und_angehoben(self):
        # nachgebautes pico2wave: schreibt leise Sinus-WAV (16 kHz) an den Pfad nach -w
        self.programm("pico2wave", """
ziel=""; while [ $# -gt 0 ]; do [ "$1" = -w ] && ziel="$2"; shift; done
python3 - "$ziel" <<'E'
import sys, wave, math, array
w = wave.open(sys.argv[1], "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
w.writeframes(array.array("h", (int(3000 * math.sin(i / 5)) for i in range(8000))).tobytes()); w.close()
E""")
        with self.nur("pico2wave"):
            pfad, art = toene.quelle("tschuess")
            self.assertEqual(art, "sprache")
            self.assertEqual(toene.quelle("tschuess")[0], pfad)                     # aus dem Zwischenspeicher
        with wave.open(pfad) as w:
            rate, n = w.getframerate(), w.getnframes()
            werte = array.array("h", w.readframes(n))
        self.assertEqual(rate, 16000)
        self.assertEqual(max(abs(v) for v in werte[:int(rate * 0.14)]), 0)            # Stille vorne
        self.assertAlmostEqual(max(abs(v) for v in werte) / 32767, toene.SPITZE, delta=0.01)
        self.assertEqual([f for f in os.listdir(self.cache) if "roh" in f], [])

    def test_text_geaendert_neu_erzeugen(self):
        self.programm("pico2wave", 'ziel=""; while [ $# -gt 0 ]; do [ "$1" = -w ] && ziel="$2"; shift; done\n'
                      'cp "' + toene.datei("bereit") + '" "$ziel"')
        with self.nur("pico2wave"):
            p1, _ = toene.quelle("tschuess")
            with mock.patch.dict(toene.ANSAGEN, {"tschuess": "Bis morgen!"}):
                p2, _ = toene.quelle("tschuess")
        self.assertNotEqual(p1, p2)

    def test_sprache_scheitert_dann_espeak_dann_ton(self):
        self.programm("pico2wave", "exit 1")
        with self.nur("pico2wave"):
            log = []
            pfad, art = toene.quelle("tschuess", log=log.append)
        self.assertEqual(art, "ton")
        self.assertIn("fehlgeschlagen", log[0])
        with wave.open(pfad) as w:
            self.assertEqual((w.getframerate(), w.getnchannels()), (44100, 1))
            self.assertGreater(w.getnframes(), 44100 * 0.5)

    def test_ohne_sprachausgabe_toene_je_stufe(self):
        with self.nur():
            for name, toene_anzahl in (("akku_60", 3), ("akku_100", 5), ("timer_45", 3)):
                pfad, art = toene.quelle(name)
                self.assertEqual(art, "ton")
                with wave.open(pfad) as w:
                    werte = array.array("h", w.readframes(w.getnframes()))
                # Töne zählen: Übergänge von Stille zu Ton
                an, zaehler, stille = False, 0, 0
                for v in werte:
                    if abs(v) > 500:
                        if not an and stille > 2000:
                            zaehler += 1
                        an, stille = True, 0
                    else:
                        stille += 1
                        if stille > 2000:
                            an = False
                self.assertEqual(zaehler, toene_anzahl, name)

    def test_quelle_ohne_erzeugen(self):
        with self.nur():
            self.assertEqual(toene.quelle_ohne_erzeugen("bereit"), "aufnahme")
            self.assertEqual(toene.quelle_ohne_erzeugen("tschuess"), "ton")
        self.programm("pico2wave", "exit 0")
        with self.nur("pico2wave"):
            self.assertEqual(toene.quelle_ohne_erzeugen("tschuess"), "sprache")
        self.assertFalse(os.path.exists(self.cache))                                 # nichts erzeugt


class Abspielen(Basis):
    def test_nur_einmal_je_einschalten(self):
        gespielt = []
        with mock.patch.object(toene, "spielen", side_effect=lambda n, log=None: gespielt.append(n) or True):
            self.assertTrue(toene.einmal_je_einschalten("bereit", log=lambda t: None))
            self.assertFalse(toene.einmal_je_einschalten("bereit", log=lambda t: None))
        self.assertEqual(gespielt, ["bereit"])
        andere = []
        os.remove(einstellungen.lauf_pfad("ansage-bereit"))
        self.assertTrue(toene.einmal_je_einschalten("bereit", spieler=andere.append))
        self.assertEqual(andere, ["bereit"])

    def test_ohne_aplay_haelt_nicht_auf(self):
        meld = []
        with mock.patch.object(toene.shutil, "which", return_value=None):
            self.assertFalse(toene.spielen("bereit", log=meld.append))
        self.assertIn("aplay fehlt", meld[0])

    def test_aufruf_und_fehlermeldung(self):
        meld = []
        r = mock.Mock(returncode=1, stderr="audio open error: Device or resource busy")
        with mock.patch.object(toene.shutil, "which", return_value="/usr/bin/aplay"), \
                mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="lautsprecher"), \
                mock.patch.object(toene.subprocess, "run", return_value=r) as run:
            self.assertFalse(toene.spielen("bereit", warten=True, log=meld.append))
        self.assertEqual(run.call_args[0][0], ["/usr/bin/aplay", "-q", "-D", "lautsprecher", toene.datei("bereit")])
        self.assertIn("busy", meld[0])


class FakeProc:
    def __init__(self, cmd, dauer, protokoll):
        self.cmd, self.dauer, self.protokoll = cmd, dauer, protokoll
        self.ende = time.monotonic() + dauer
        self.returncode = None
        protokoll.append(("start", os.path.basename(cmd[-1])))

    def poll(self):
        if self.returncode is None and time.monotonic() >= self.ende:
            self.returncode = 0
        return self.returncode

    def terminate(self):
        if self.returncode is None:
            self.returncode = -15
            self.protokoll.append(("abbruch", os.path.basename(self.cmd[-1])))

    kill = terminate

    def wait(self, timeout=None):
        while self.poll() is None:
            time.sleep(0.01)
        return self.returncode

    def communicate(self, timeout=None):
        self.wait()
        return b"", b""


class Ansager(Basis):
    def setUp(self):
        super().setUp()
        self.protokoll = []
        self.a = toene.Ansager(log=lambda t: None,
                               popen=lambda cmd, **k: FakeProc(cmd, 0.3, self.protokoll))
        p = mock.patch.object(toene.shutil, "which", side_effect=lambda n: "/usr/bin/" + n if n == "aplay" else None)
        p.start()
        self.addCleanup(p.stop)
        p = mock.patch.object(toene.lautstaerke, "aktive_ausgabe", return_value="lautsprecher")
        p.start()
        self.addCleanup(p.stop)
        self.a.starten()

    def test_neueste_ansage_gewinnt(self):
        self.a.sagen("timer_15")
        time.sleep(0.1)
        self.a.sagen("timer_30")
        time.sleep(0.05)
        self.a.sagen("timer_45")
        self.assertTrue(self.a.warten(3))
        gestartet = [n for art, n in self.protokoll if art == "start"]
        self.assertEqual(gestartet[0].split("-")[0], "timer_15")
        self.assertEqual(gestartet[-1].split("-")[0], "timer_45")
        self.assertIn("abbruch", [art for art, n in self.protokoll])
        self.assertEqual(self.a.zuletzt, ("timer_45", "ton"))

    def test_warten_bis_still(self):
        self.a.sagen("tschuess")
        t0 = time.monotonic()
        self.assertTrue(self.a.warten(3))
        self.assertGreaterEqual(time.monotonic() - t0, 0.25)

    def test_sagen_und_warten(self):
        t0 = time.monotonic()
        self.assertTrue(self.a.sagen_und_warten("akku_leer", 3))
        self.assertGreaterEqual(time.monotonic() - t0, 0.25)

    def test_unbekannte_ansage_und_faden_lebt(self):
        self.a.sagen("gibt_es_nicht")
        self.assertTrue(self.a.lebt())
        self.a.popen = lambda cmd, **k: (_ for _ in ()).throw(OSError("aplay kaputt"))
        self.a.sagen("moment")
        self.assertTrue(self.a.warten(2))
        self.assertTrue(self.a.lebt())


class Startton(Basis):
    """Früher Startton (Dienst peppa-startton): Lautstärke zuerst, nie in unbekannter Lautstärke."""

    def setUp(self):
        super().setUp()
        self.folge = []                                   # Reihenfolge der Schritte
        self.eingerichtet = True
        self.karte = True
        self.regler_da_nach_anlegen = True
        self.gesperrt = False

        def beim_start(_self):
            self.folge.append("lautstaerke")

        def spielen(name, warten=False, log=print):
            self.folge.append(("spielen", name, warten))
            return True

        def anlegen(log=print):
            self.folge.append("anlegen")
            if self.regler_da_nach_anlegen:
                self.eingerichtet = True
            return self.eingerichtet

        for obj, name, ersatz in (
                (toene.einstellungen, "musik_gesperrt", lambda cfg, t: self.gesperrt),
                (toene.einstellungen, "laden", lambda: {}),
                (toene.lautstaerke, "eingerichtet", lambda a: self.eingerichtet),
                (toene.lautstaerke, "karte_da", lambda a: self.karte),
                (toene, "spielen", spielen),
                (toene, "_regler_anlegen", anlegen),
                (toene.automatik.Automatik if hasattr(toene, "automatik") else __import__("automatik").Automatik,
                 "beim_start", beim_start)):
            p = mock.patch.object(obj, name, ersatz)
            p.start()
            self.addCleanup(p.stop)

    def test_erst_lautstaerke_dann_ton(self):
        self.assertTrue(toene.startton(log=lambda m: None))
        self.assertEqual(self.folge, ["lautstaerke", ("spielen", "start", True)])

    def test_regler_fehlt_wird_angelegt_dann_ton(self):
        self.eingerichtet = False
        self.assertTrue(toene.startton(log=lambda m: None))
        self.assertEqual(self.folge, ["anlegen", "lautstaerke", ("spielen", "start", True)])

    def test_regler_nicht_anlegbar_dann_still(self):
        self.eingerichtet = False
        self.regler_da_nach_anlegen = False
        meldungen = []
        self.assertFalse(toene.startton(log=meldungen.append))
        self.assertEqual(self.folge, ["anlegen"])                                  # nichts gespielt
        self.assertTrue(any("kein Startton" in m for m in meldungen))

    def test_ohne_lautsprecherkarte_weiter_mit_klinke(self):
        self.eingerichtet = False
        self.karte = False
        self.regler_da_nach_anlegen = False
        self.assertTrue(toene.startton(log=lambda m: None))
        self.assertEqual(self.folge[-1], ("spielen", "start", True))

    def test_ruhezeit_keine_musik_bleibt_still(self):
        self.gesperrt = True
        self.assertTrue(toene.startton(log=lambda m: None))
        self.assertEqual(self.folge, [])

    def test_start_ist_ansage_mit_text_und_ton(self):
        self.assertIn("start", toene.ANSAGEN)
        self.assertIn("start", toene.TOENE)

    def test_ganz_aus_ist_ansage_ohne_sprachausgabe(self):
        self.assertIn("ganz_aus", toene.ANSAGEN)
        self.assertIn("ganz_aus", toene.TOENE)
        self.assertIn("ganz_aus", toene.NUR_AUFNAHME_ODER_TON)


class StarttonQuelle(Basis):
    def test_ohne_aufnahme_nie_sprachausgabe_sondern_ton(self):
        self.programm("pico2wave", 'echo "darf nicht laufen" >&2; exit 9')
        with self.nur("pico2wave"), mock.patch.object(toene, "datei", lambda n: os.path.join(self.tmp.name, f"{n}.wav")):
            pfad, art = toene.quelle("start")
            self.assertEqual(art, "ton")
            self.assertEqual(toene.quelle_ohne_erzeugen("start"), "ton")
        with wave.open(pfad) as w:
            self.assertEqual((w.getnchannels(), w.getframerate()), (1, 44100))
            self.assertLess(w.getnframes() / w.getframerate(), 1.0)                  # kurz, Kind soll nicht warten

    def test_aufnahme_hat_vorrang(self):
        aufn = os.path.join(self.tmp.name, "start.wav")
        with wave.open(aufn, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(b"\0\0" * 4410)
        with mock.patch.object(toene, "datei", lambda n: aufn):
            self.assertEqual(toene.quelle("start"), (aufn, "aufnahme"))

    def test_andere_ansagen_behalten_die_sprachausgabe(self):
        self.programm("pico2wave", 'ziel=""; while [ $# -gt 0 ]; do [ "$1" = -w ] && ziel="$2"; shift; done\n'
                      'cp "' + toene.datei("bereit") + '" "$ziel"')
        with self.nur("pico2wave"):
            self.assertEqual(toene.quelle("tschuess")[1], "sprache")


if __name__ == "__main__":
    unittest.main()
