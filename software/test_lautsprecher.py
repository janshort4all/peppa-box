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
        self.systemd = os.path.join(d, "systemd")
        bin_ = os.path.join(d, "bin")
        os.mkdir(bin_)
        # sudo: Befehl ohne Rechte ausführen; install ohne -o/-g
        self.skript(bin_, "sudo", 'if [ "$1" = install ]; then shift; exec install -m 0644 "$7" "$8"; fi\nexec "$@"')
        self.skript(bin_, "pinctrl", "exit 0")
        self.env = dict(os.environ, PATH=bin_ + ":" + os.environ["PATH"], PEPPA_CONFIG_TXT=self.cfg,
                        PEPPA_ASOUND=self.asound, PEPPA_RASPOTIFY=self.rasp, PEPPA_KARTEN=self.cards,
                        PEPPA_SYSTEMD=self.systemd, PEPPA_TROCKEN="1")

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
        self.assertTrue(cfg.endswith("dtparam=spi=on\ndtoverlay=hifiberry-dac\ngpio=16=op,dl\n"))
        a = self.lesen(self.asound)
        self.assertTrue(a.startswith("# vorhandener Inhalt\n"))
        self.assertIn('pcm "hw:CARD=sndrpihifiberry,DEV=0"', a)
        self.assertIn("type dmix", a)
        self.assertIn("ipc_perm 0666", a)
        self.assertIn('slave.pcm "peppa_plug"', a)
        self.assertIn("card sndrpihifiberry", a)
        dienst = self.lesen(os.path.join(self.systemd, "peppa-stille.service"))
        self.assertIn("-D peppa_dmix", dienst)
        self.assertLess(dienst.index("ExecStartPre=") , dienst.index("ExecStart="))
        self.assertRegex(dienst, r"ExecStartPre=\S*pinctrl set 16 op dl")
        self.assertRegex(dienst, r"ExecStartPost=.*sleep 0\.5; \S*pinctrl set 16 op dh")
        self.assertRegex(dienst, r"ExecStop=\S*pinctrl set 16 op dl")
        self.assertIn("PrivateIPC=no", self.lesen(os.path.join(self.systemd, "raspotify.service.d", "peppa-ipc.conf")))
        rasp = self.lesen(self.rasp)
        self.assertIn('\nLIBRESPOT_DEVICE="lautsprecher"\n', rasp)
        self.assertIn('#LIBRESPOT_DEVICE="default"', rasp)            # Kommentar bleibt
        self.assertNotIn("Headphones", rasp)
        self.assertIn("neu starten", r.stdout)
        vorher = (cfg, a, rasp, dienst)
        r = self.lauf()                                                # zweiter Lauf ändert nichts
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(vorher, (self.lesen(self.cfg), self.lesen(self.asound), self.lesen(self.rasp),
                                  self.lesen(os.path.join(self.systemd, "peppa-stille.service"))))
        self.assertNotIn("eingerichtet", r.stdout)
        self.assertNotIn("neu starten", r.stdout)
        self.assertEqual(self.lesen(self.asound).count("pcm.lautsprecher"), 1)

    def test_alte_sd_zeile_wird_ersetzt(self):
        self.schreiben(self.cfg, CONFIG_TXT + "dtoverlay=hifiberry-dac\ngpio=16=ip,pn\n")
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_MIT)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cfg = self.lesen(self.cfg)
        self.assertIn("gpio=16=op,dl\n", cfg)
        self.assertNotIn("ip,pn", cfg)
        self.assertEqual(cfg.count("gpio=16="), 1)
        self.assertIn("neu starten", r.stdout)

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

    def test_kopfhoerer_mischer_und_alter_kopfhoerer_ausgang_zurueck(self):
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, RASPOTIFY.replace('"plughw:CARD=Headphones,DEV=0"', '"kopfhoerer"'))
        self.schreiben(self.cards, KARTEN_MIT)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        a = self.lesen(self.asound)
        self.assertIn("pcm.kopfhoerer {", a)
        self.assertIn('pcm "hw:CARD=Headphones,DEV=0"', a)
        self.assertIn("ipc_key 5151", a)
        self.assertLess(a.index("pcm.kopfhoerer"), a.index("# <<< peppa-box lautsprecher"))
        rasp = self.lesen(self.rasp)
        self.assertIn('LIBRESPOT_DEVICE="lautsprecher"', rasp)     # ohne Tonausgabe nie auf den Kopfhörern
        self.assertIn('LIBRESPOT_BACKEND="alsa"', rasp)

    def tonausgabe_anlegen(self):
        for name in ("ausgabe", "ereignis"):
            self.skript(self.tmp.name, name, "exit 0")
        self.env.update(PEPPA_RELAIS=os.path.join(self.tmp.name, "ausgabe"),
                        PEPPA_EREIGNIS=os.path.join(self.tmp.name, "ereignis"))

    def test_mit_tonausgabe_und_ereignissen(self):
        self.tonausgabe_anlegen()
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, RASPOTIFY + '#LIBRESPOT_ONEVENT=\nLIBRESPOT_BACKEND="alsa"\n')
        self.schreiben(self.cards, KARTEN_MIT)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rasp = self.lesen(self.rasp)
        self.assertIn('\nLIBRESPOT_BACKEND="subprocess"\n', rasp)
        self.assertIn(f'\nLIBRESPOT_DEVICE="{self.tmp.name}/ausgabe"\n', rasp)
        self.assertIn(f'\nLIBRESPOT_ONEVENT="{self.tmp.name}/ereignis"\n', rasp)
        self.assertIn("#LIBRESPOT_ONEVENT=\n", rasp)                       # Kommentar bleibt
        self.assertEqual(rasp.count("LIBRESPOT_BACKEND="), 1)
        self.assertEqual(rasp.count("\nLIBRESPOT_DEVICE="), 1)
        r = self.lauf()                                                    # wiederholbar, ändert nichts
        self.assertEqual(self.lesen(self.rasp), rasp)

    def test_probe_der_tonausgabe_scheitert_alsa_direkt(self):
        self.tonausgabe_anlegen()
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_MIT)
        self.env["PEPPA_RELAIS_PRUEFUNG"] = "exit 1"
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Probe der Tonausgabe", r.stdout)
        rasp = self.lesen(self.rasp)
        self.assertIn('LIBRESPOT_BACKEND="alsa"', rasp)
        self.assertIn('\nLIBRESPOT_DEVICE="lautsprecher"\n', rasp)

    def test_notfall_rueckweg_alsa_direkt(self):
        self.tonausgabe_anlegen()
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_MIT)
        self.env["PEPPA_ALSA_DIREKT"] = "1"
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rasp = self.lesen(self.rasp)
        self.assertIn('LIBRESPOT_BACKEND="alsa"', rasp)
        self.assertIn('\nLIBRESPOT_DEVICE="lautsprecher"\n', rasp)

    def test_ohne_kopfhoerer_karte_nur_lautsprecher(self):
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, RASPOTIFY)
        self.schreiben(self.cards, KARTEN_MIT.split(" 1 [")[0].replace(" 0 [Headphones     ]", " 0 [Andere         ]") +
                       " 1 [sndrpihifiberry]: RPi-simple - snd_rpi_hifiberry_dac\n")
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("pcm.kopfhoerer", self.lesen(self.asound))
        self.assertIn("Kopfhoerer-Karte (Headphones) nicht gefunden", r.stdout)

    def test_raspotify_ohne_device_zeile(self):
        self.schreiben(self.cfg, CONFIG_TXT)
        self.schreiben(self.rasp, 'LIBRESPOT_NAME="Peppa Box"\n#LIBRESPOT_DEVICE="default"\n')
        self.schreiben(self.cards, KARTEN_MIT)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.lesen(self.rasp).endswith('LIBRESPOT_DEVICE="lautsprecher"\n'))


if __name__ == "__main__":
    unittest.main()
