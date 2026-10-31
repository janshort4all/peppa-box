"""Tests für den Lautsprecher-Ausgang in lautstaerke.py und für lautsprecher_einrichten.sh.
Ohne Hardware: /proc/asound/cards, amixer, sudo und die Systemdateien werden nachgebaut.
Aufruf: cd software && python3 -m unittest -v test_lautsprecher
"""
import os
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

import lautstaerke

KARTEN_MIT = """ 0 [Headphones     ]: bcm2835_headpho - bcm2835 Headphones
                      bcm2835 Headphones
 1 [sndrpihifiberry]: RPi-simple - snd_rpi_hifiberry_dac
                      snd_rpi_hifiberry_dac
"""
KARTEN_OHNE = """ 0 [Headphones     ]: bcm2835_headpho - bcm2835 Headphones
                      bcm2835 Headphones
"""
HIER = os.path.dirname(os.path.abspath(__file__))


class Lautstaerke(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.karten = os.path.join(self.tmp.name, "cards")
        lautstaerke._gefunden.clear()
        lautstaerke._zuletzt_gesucht.clear()
        self.regler_da = True
        self.aufrufe = []
        patcher = mock.patch.object(lautstaerke, "KARTEN_DATEI", self.karten)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(lautstaerke, "_amixer", self.amixer)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def amixer(self, *args):
        self.aufrufe.append(args)
        if "Lautsprecher" in args and not self.regler_da:
            return None
        return "  Mono: Playback 77 [42%]\n"

    def karten_schreiben(self, text):
        with open(self.karten, "w") as f:
            f.write(text)

    def test_karte_gefunden_lautsprecher_aktiv(self):
        self.karten_schreiben(KARTEN_MIT)
        self.assertTrue(lautstaerke.eingerichtet("lautsprecher"))
        self.assertEqual(lautstaerke.aktive_ausgabe(), "lautsprecher")
        self.assertEqual(lautstaerke.lesen("lautsprecher"), 42)
        self.assertTrue(lautstaerke.setzen("lautsprecher", 55))
        self.assertIn(("-M", "-c", "sndrpihifiberry", "sset", "Lautsprecher", "55%"), self.aufrufe)

    def test_ohne_karte_bleibt_kopfhoerer(self):
        self.karten_schreiben(KARTEN_OHNE)
        self.assertFalse(lautstaerke.eingerichtet("lautsprecher"))
        self.assertEqual(lautstaerke.aktive_ausgabe(), "kopfhoerer")
        self.assertIsNone(lautstaerke.lesen("lautsprecher"))
        self.assertFalse(lautstaerke.setzen("lautsprecher", 50))

    def test_karte_ohne_regler_gilt_nicht_als_eingerichtet(self):
        self.karten_schreiben(KARTEN_MIT)
        self.regler_da = False
        self.assertEqual(lautstaerke.aktive_ausgabe(), "kopfhoerer")

    def test_spaeter_eingerichtet_wird_nach_frist_erkannt(self):
        self.karten_schreiben(KARTEN_OHNE)
        with mock.patch.object(lautstaerke.time, "monotonic", return_value=100.0):
            self.assertFalse(lautstaerke.eingerichtet("lautsprecher"))
        self.karten_schreiben(KARTEN_MIT)
        with mock.patch.object(lautstaerke.time, "monotonic", return_value=110.0):
            self.assertFalse(lautstaerke.eingerichtet("lautsprecher"))   # Frist läuft noch
        with mock.patch.object(lautstaerke.time, "monotonic", return_value=131.0):
            self.assertTrue(lautstaerke.eingerichtet("lautsprecher"))

    def test_fehlende_kartendatei(self):
        self.assertFalse(lautstaerke.eingerichtet("lautsprecher"))

    def test_kopfhoerer_unveraendert(self):
        self.karten_schreiben(KARTEN_OHNE)
        self.assertEqual(lautstaerke.lesen("kopfhoerer"), 42)
        self.assertEqual(self.aufrufe[-1], ("-M", "-c", "Headphones", "sget", "PCM"))


CONFIG_TXT = """# config
dtparam=audio=on
[cm4]
otg_mode=1
[all]
dtparam=spi=on
"""
RASPOTIFY = """#LIBRESPOT_NAME="Librespot"
LIBRESPOT_NAME="Peppa Box"
#LIBRESPOT_DEVICE="default"
LIBRESPOT_DEVICE="plughw:CARD=Headphones,DEV=0"
LIBRESPOT_VOLUME_CTRL=fixed
"""


class Einrichtungsskript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = self.tmp.name
        self.cfg = os.path.join(d, "config.txt")
        self.asound = os.path.join(d, "asound.conf")
        self.rasp = os.path.join(d, "raspotify.conf")
        self.cards = os.path.join(d, "cards")
        bin_ = os.path.join(d, "bin")
        os.mkdir(bin_)
        # sudo: Befehl ohne Rechte ausführen; install ohne -o/-g
        self.skript(bin_, "sudo", 'if [ "$1" = install ]; then shift; exec install -m 0644 "$7" "$8"; fi\nexec "$@"')
        self.skript(bin_, "pinctrl", "exit 0")
        self.env = dict(os.environ, PATH=bin_ + ":" + os.environ["PATH"], PEPPA_CONFIG_TXT=self.cfg,
                        PEPPA_ASOUND=self.asound, PEPPA_RASPOTIFY=self.rasp, PEPPA_KARTEN=self.cards,
                        PEPPA_TROCKEN="1")

    @staticmethod
    def skript(ordner, name, inhalt):
        p = os.path.join(ordner, name)
        with open(p, "w") as f:
            f.write("#!/bin/sh\n" + inhalt + "\n")
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)

    def schreiben(self, pfad, text):
        with open(pfad, "w") as f:
            f.write(text)

    def lesen(self, pfad):
        with open(pfad) as f:
            return f.read()

    def lauf(self):
        return subprocess.run(["sh", os.path.join(HIER, "lautsprecher_einrichten.sh")], env=self.env,
                              capture_output=True, text=True)

    def test_vollstaendig_und_wiederholbar(self):
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_MIT)
        self.schreiben(self.asound, "# vorhandener Inhalt\n")
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cfg = self.lesen(self.cfg)
        self.assertTrue(cfg.endswith("dtparam=spi=on\ndtoverlay=hifiberry-dac\ngpio=16=ip,pn\n"))
        a = self.lesen(self.asound)
        self.assertTrue(a.startswith("# vorhandener Inhalt\n"))
        self.assertIn('slave.pcm "plughw:CARD=sndrpihifiberry,DEV=0"', a)
        self.assertIn("card sndrpihifiberry", a)
        rasp = self.lesen(self.rasp)
        self.assertIn('\nLIBRESPOT_DEVICE="lautsprecher"\n', rasp)
        self.assertIn('#LIBRESPOT_DEVICE="default"', rasp)            # Kommentar bleibt
        self.assertNotIn("Headphones", rasp)
        self.assertIn("neu starten", r.stdout)
        vorher = (cfg, a, rasp)
        r = self.lauf()                                                # zweiter Lauf ändert nichts
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(vorher, (self.lesen(self.cfg), self.lesen(self.asound), self.lesen(self.rasp)))
        self.assertNotIn("neu starten", r.stdout)
        self.assertEqual(self.lesen(self.asound).count("pcm.lautsprecher"), 1)

    def test_hifiberry_schon_da_kein_doppel(self):
        self.schreiben(self.cfg, CONFIG_TXT + "dtoverlay=hifiberry-dac\n")
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_MIT)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.lesen(self.cfg).count("hifiberry-dac"), 1)
        self.assertTrue(os.path.exists(self.asound))                   # wird neu angelegt

    def test_ohne_karte_nur_config_und_hinweis(self):
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_OHNE)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nicht gefunden", r.stdout)
        self.assertIn("reboot", r.stdout)
        self.assertFalse(os.path.exists(self.asound))
        self.assertIn("Headphones", self.lesen(self.rasp))             # Raspotify unverändert

    def test_bricht_ab_wenn_config_nicht_mit_all_endet(self):
        self.schreiben(self.cfg, "dtparam=audio=on\n[pi5]\nfoo=1\n")
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_MIT)
        r = self.lauf()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.lesen(self.cfg), "dtparam=audio=on\n[pi5]\nfoo=1\n")

    def test_raspotify_ohne_device_zeile(self):
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, 'LIBRESPOT_NAME="Peppa Box"\n#LIBRESPOT_DEVICE="default"\n')
        self.schreiben(self.cards, KARTEN_MIT)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.lesen(self.rasp).endswith('LIBRESPOT_DEVICE="lautsprecher"\n'))


if __name__ == "__main__":
    unittest.main()
