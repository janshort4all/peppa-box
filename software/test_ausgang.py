"""Tests der Kopfhörer-Erkennung und Umschaltung (ausgang.py) und des Root-Helfers peppa_ausgang.sh.
Ohne Hardware: Helfer, Verstärker, Lautstärke und Steuerung werden nachgebaut.
Aufruf: cd software && python3 -m unittest -v test_ausgang
"""
import os
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

import ausgang
import einstellungen

HIER = os.path.dirname(os.path.abspath(__file__))


class Uhr:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class FakeHelfer:
    def __init__(self, geraet="lautsprecher"):
        self.geraet, self.aufrufe, self.ok = geraet, [], True

    def zeigen(self):
        return self.geraet

    def umstellen(self, ziel):
        self.aufrufe.append(ziel)
        if not self.ok:
            return False, "sudo: a password is required"
        self.geraet = ziel
        return True, f"Spotify-Ausgang: {ziel}"


class FakeSt:
    """Führt die Umstellung sofort aus (wie der Faden der Steuerung)."""

    def __init__(self):
        self.auftraege = []
        self.sofort = True

    def ausgang_umstellen(self, ziel, ausfuehren):
        self.auftraege.append(ziel)
        if self.sofort:
            ausfuehren(ziel)
        else:
            self.offen = (ziel, ausfuehren)


class FakeLaut:
    def __init__(self):
        self.v = {"lautsprecher": 50, "kopfhoerer": 45}
        self.verlauf = []

    def eingerichtet(self, a):
        return True

    def setzen(self, a, p):
        self.v[a] = p
        self.verlauf.append((a, p))
        return True


class Umschalten(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(einstellungen, "LAUF", self.tmp.name)
        p.start()
        self.addCleanup(p.stop)
        p = mock.patch.dict(os.environ, {"HOME": self.tmp.name})
        p.start()
        self.addCleanup(p.stop)
        einstellungen._cache["mtime"] = None
        self.uhr = Uhr()
        self.helfer = FakeHelfer()
        self.st = FakeSt()
        self.laut = FakeLaut()
        self.verst = []
        self.log = []
        self.a = ausgang.Ausgang(self.st, self.laut, einstellungen, helfer=self.helfer,
                                 verstaerker=lambda an, log=None: self.verst.append(an),
                                 jetzt=self.uhr, uhr=lambda: 1_800_000_000.0, log=self.log.append)
        with mock.patch.object(ausgang.shutil, "which", return_value="/usr/bin/sudo"):
            self.a.start()

    def lauf(self, s, pegel):
        ende = self.uhr.t + s
        while self.uhr.t < ende:
            self.uhr.t += 0.05
            self.a.tick(pegel, self.uhr.t)

    def test_start_merkt_ausgang(self):
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertEqual(einstellungen.lauf_lesen("ausgang"), {"ausgang": "lautsprecher"})

    def test_einstecken_und_ausstecken(self):
        self.lauf(1, 0)
        self.assertEqual(self.st.auftraege, [])
        self.lauf(1, 1)                                      # Stecker rein (Pegel hoch)
        self.assertEqual(self.st.auftraege, ["kopfhoerer"])
        self.assertEqual(self.verst, [False])                # Lautsprecher sofort stumm
        self.assertEqual(self.laut.verlauf[-1], ("kopfhoerer", 30))   # Startlautstärke Kopfhörer
        self.assertEqual(einstellungen.lauf_lesen("ausgang"), {"ausgang": "kopfhoerer"})
        self.lauf(4, 0)                                      # raus
        self.assertEqual(self.st.auftraege, ["kopfhoerer", "lautsprecher"])
        self.assertIn(("kopfhoerer", 0), self.laut.verlauf)  # Kopfhörer sofort still
        self.assertEqual(self.verst, [False, True])
        self.assertEqual(self.a.aktuell, "lautsprecher")

    def test_entprellen(self):
        for _ in range(10):                                  # Wackelkontakt: 0,2 s an, 0,2 s aus
            self.lauf(0.2, 1)
            self.lauf(0.2, 0)
        self.assertEqual(self.st.auftraege, [])

    def test_hoechstens_alle_3_s_und_nur_letzter_wunsch(self):
        self.lauf(0.6, 1)                                    # rein: nach 0,4 s umgestellt
        self.lauf(0.6, 0)                                    # raus: noch innerhalb 3 s -> warten
        self.lauf(0.6, 1)                                    # wieder rein: passt zum aktuellen Ausgang
        self.lauf(5, 1)
        self.assertEqual(self.st.auftraege, ["kopfhoerer"])
        self.lauf(0.6, 0)
        self.assertEqual(self.st.auftraege, ["kopfhoerer", "lautsprecher"])

    def test_ausstecken_kurz_nach_einstecken_wartet_bis_3_s(self):
        self.lauf(0.45, 1)
        start = self.uhr.t
        self.lauf(4, 0)
        self.assertEqual(self.st.auftraege, ["kopfhoerer", "lautsprecher"])
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertGreaterEqual(self.uhr.t - start, 3)

    def test_polung_umgekehrt_und_erkennung_aus(self):
        einstellungen.speichern({"bedienung": {"klinke_eingesteckt_bei": "tief"}})
        self.lauf(1, 0)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.uhr.t += 5
        einstellungen.speichern({"bedienung": {"kopfhoerer_erkennung": False}})
        self.lauf(1, 0)
        self.assertEqual(self.a.aktuell, "lautsprecher")

    def test_helfer_fehlt_lautsprecher_bleibt_an(self):
        self.helfer.ok = False
        self.lauf(1, 1)
        self.assertEqual(self.verst, [False, True])          # stumm zurückgenommen
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertIn("password", self.a.fehler)
        n = len(self.helfer.aufrufe)
        self.lauf(30, 1)
        self.assertEqual(len(self.helfer.aufrufe), n)        # erst nach 60 s wieder
        self.lauf(35, 1)
        self.assertEqual(len(self.helfer.aufrufe), n + 1)
        self.assertEqual(sum("nicht möglich" in z for z in self.log), 1)   # nur einmal gemeldet

    def test_alte_einstellung_wird_umgestellt(self):
        self.helfer.geraet = "plughw:CARD=Headphones,DEV=0"
        with mock.patch.object(ausgang.shutil, "which", return_value="/usr/bin/sudo"):
            self.a.start()
        self.assertIsNone(self.a.aktuell)
        self.uhr.t += 5
        self.lauf(1, 0)
        self.assertEqual(self.helfer.aufrufe, ["lautsprecher"])

    def test_haengende_umstellung_wird_neu_versucht(self):
        self.st.sofort = False
        self.lauf(1, 1)
        self.assertEqual(self.st.auftraege, ["kopfhoerer"])
        self.lauf(30, 1)
        self.assertEqual(self.st.auftraege, ["kopfhoerer"])
        self.lauf(20, 1)
        self.assertEqual(self.st.auftraege, ["kopfhoerer", "kopfhoerer"])

    def test_stumm_halten(self):
        class Leser:
            f = 0

            def funktion(self, pin):
                return self.f
        self.lauf(1, 1)
        self.verst.clear()
        leser = Leser()
        self.a.stumm_halten(leser)                           # SD ist Eingang (peppa-stille neu) -> wieder stumm
        self.assertEqual(self.verst, [False])
        leser.f = 1
        self.a.stumm_halten(leser)
        self.assertEqual(self.verst, [False])


class Helferskript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = self.tmp.name
        self.conf = os.path.join(d, "conf")
        self.asound = os.path.join(d, "asound.conf")
        self.log = os.path.join(d, "systemctl.log")
        sysctl = os.path.join(d, "systemctl")
        with open(sysctl, "w") as f:
            f.write(f'#!/bin/sh\necho "$*" >> {self.log}\n')
        os.chmod(sysctl, os.stat(sysctl).st_mode | stat.S_IEXEC)
        with open(self.asound, "w") as f:
            f.write('pcm.lautsprecher {\n}\npcm.kopfhoerer {\n}\n')
        with open(self.conf, "w") as f:
            f.write('LIBRESPOT_NAME="Peppa Box"\nLIBRESPOT_DEVICE="lautsprecher"\n')
        self.env = {k: v for k, v in os.environ.items() if k != "SUDO_USER"}
        self.env.update(PEPPA_RASPOTIFY=self.conf, PEPPA_ASOUND=self.asound, PEPPA_SYSTEMCTL=sysctl)

    def lauf(self, *args, **env):
        return subprocess.run(["sh", os.path.join(HIER, "peppa_ausgang.sh"), *args],
                              env=dict(self.env, **env), capture_output=True, text=True)

    def test_zeigen_umstellen_neustart(self):
        self.assertEqual(self.lauf("zeigen").stdout.strip(), "lautsprecher")
        r = self.lauf("kopfhoerer")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.lauf("zeigen").stdout.strip(), "kopfhoerer")
        with open(self.log) as f:
            self.assertEqual(f.read(), "restart raspotify\n")
        with open(self.conf) as f:
            self.assertEqual(f.read().count("LIBRESPOT_DEVICE="), 1)

    def test_ohne_device_zeile_wird_ergaenzt(self):
        with open(self.conf, "w") as f:
            f.write('LIBRESPOT_NAME="Peppa Box"\n#LIBRESPOT_DEVICE="default"\n')
        self.assertEqual(self.lauf("zeigen").stdout.strip(), "")
        self.assertEqual(self.lauf("lautsprecher").returncode, 0)
        with open(self.conf) as f:
            self.assertTrue(f.read().endswith('LIBRESPOT_DEVICE="lautsprecher"\n'))

    def test_nur_erlaubte_werte_und_fehlendes_alsa_geraet(self):
        r = self.lauf("hw:0,0; reboot")
        self.assertEqual(r.returncode, 2)
        with open(self.asound, "w") as f:
            f.write('pcm.lautsprecher {\n}\n')
        r = self.lauf("kopfhoerer")
        self.assertEqual(r.returncode, 4)
        self.assertFalse(os.path.exists(self.log))           # kein Neustart

    @unittest.skipIf(os.path.exists("/etc/raspotify/conf"), "nur ohne echte Raspotify-Einstellungen")
    def test_ueber_sudo_keine_umgelenkten_pfade(self):
        r = self.lauf("zeigen", SUDO_USER="jan")             # Pfade aus der Umgebung gelten dann nicht
        self.assertEqual(r.stdout.strip(), "")
        r = self.lauf("kopfhoerer", SUDO_USER="jan")
        self.assertEqual(r.returncode, 3)                    # /etc/raspotify/conf fehlt hier
        self.assertFalse(os.path.exists(self.log))


if __name__ == "__main__":
    unittest.main()
