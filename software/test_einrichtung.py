"""Tests für bedienung_einrichten.sh (config.txt) und die Syntax aller Einrichtungsskripte.
Ohne Systemdateien: config.txt liegt in einem Temp-Ordner, sudo wird nachgebaut.
Aufruf: cd software && python3 -m unittest -v test_einrichtung
"""
import os
import stat
import subprocess
import tempfile
import unittest

HIER = os.path.dirname(os.path.abspath(__file__))
CONFIG_TXT = """# Raspberry Pi OS
#dtparam=i2c_arm=on
#dtparam=spi=on
dtparam=audio=on
camera_auto_detect=1

[cm4]
otg_mode=1

[all]
dtparam=spi=on
dtparam=i2c_arm=on
dtoverlay=hifiberry-dac
gpio=16=op,dl
"""
OVERLAY = "dtoverlay=rotary-encoder,pin_a=17,pin_b=27,relative_axis=1,steps-per-period=2"


class Bedienung(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = os.path.join(self.tmp.name, "config.txt")
        bin_ = os.path.join(self.tmp.name, "bin")
        os.mkdir(bin_)
        p = os.path.join(bin_, "sudo")
        with open(p, "w") as f:
            f.write('#!/bin/sh\nexec "$@"\n')
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
        self.env = dict(os.environ, PATH=bin_ + ":" + os.environ["PATH"], PEPPA_CONFIG_TXT=self.cfg,
                        PEPPA_MODULES_LOAD=self.tmp.name)

    def test_i2c_dev_wird_geladen(self):
        with open(self.cfg, "w") as f:
            f.write(CONFIG_TXT)
        self.assertEqual(self.lauf().returncode, 0)
        with open(os.path.join(self.tmp.name, "peppa-i2c.conf")) as f:
            self.assertEqual(f.read().strip(), "i2c-dev")

    def lauf(self):
        return subprocess.run(["sh", os.path.join(HIER, "bedienung_einrichten.sh")], env=self.env,
                              capture_output=True, text=True)

    def lesen(self):
        with open(self.cfg) as f:
            return f.read()

    def test_ergaenzt_und_zweiter_lauf_aendert_nichts(self):
        with open(self.cfg, "w") as f:
            f.write(CONFIG_TXT)
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cfg = self.lesen()
        self.assertTrue(cfg.startswith(CONFIG_TXT))                      # nur angehängt
        self.assertTrue(cfg.endswith(OVERLAY + "\ngpio=5=ip,pu\ngpio=26=ip,pu\n"))
        self.assertEqual(cfg.count("dtparam=spi=on"), 2)                # Kommentar + vorhandene Zeile
        self.assertIn("neu starten", r.stdout)
        r = self.lauf()
        self.assertEqual(self.lesen(), cfg)
        self.assertIn("schon richtig", r.stdout)

    def test_alte_overlay_zeile_wird_ersetzt(self):
        with open(self.cfg, "w") as f:
            f.write(CONFIG_TXT + "dtoverlay=rotary-encoder,pin_a=17,pin_b=27\ngpio=26=ip,pd\n")
        r = self.lauf()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cfg = self.lesen()
        self.assertEqual(cfg.count("dtoverlay=rotary-encoder"), 1)
        self.assertIn(OVERLAY + "\n", cfg)
        self.assertIn("gpio=26=ip,pu\n", cfg)
        self.assertNotIn("ip,pd", cfg)

    def test_fehlende_dtparam_werden_ergaenzt(self):
        with open(self.cfg, "w") as f:
            f.write("#dtparam=i2c_arm=on\n[all]\n")
        self.assertEqual(self.lauf().returncode, 0)
        cfg = self.lesen()
        for z in ("dtparam=i2c_arm=on", "dtparam=spi=on", "dtparam=audio=on"):
            self.assertIn("\n" + z + "\n", cfg)

    def test_bricht_ab_wenn_nicht_all(self):
        with open(self.cfg, "w") as f:
            f.write("dtparam=audio=on\n[pi5]\nfoo=1\n")
        r = self.lauf()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.lesen(), "dtparam=audio=on\n[pi5]\nfoo=1\n")

    def test_ohne_config_txt(self):
        self.assertNotEqual(self.lauf().returncode, 0)


class Syntax(unittest.TestCase):
    def test_alle_skripte_sh_syntax(self):
        for name in sorted(os.listdir(HIER)):
            if name.endswith(".sh"):
                r = subprocess.run(["sh", "-n", os.path.join(HIER, name)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"{name}: {r.stderr}")

    def test_dienst_einrichten_kennt_helfer_und_gruppen(self):
        with open(os.path.join(HIER, "dienst_einrichten.sh")) as f:
            s = f.read()
        for teil in ("$HELFER zeigen, $HELFER neustart, $HELFER lautsprecher, $HELFER kopfhoerer",
                     "/usr/local/lib/peppa-box/ausgabe", "/usr/local/lib/peppa-box/ereignis",
                     "Storage=persistent", "gpio spi input",
                     "bedienung_einrichten.sh", "RuntimeWatchdogSec=15", "libttspico-utils", "TimeoutStopSec=",
                     "/usr/local/lib/peppa-box/wlan_suche", "peppa-wlan-suche", "autoconnect-retries=0"):
            self.assertIn(teil, s)


if __name__ == "__main__":
    unittest.main()
