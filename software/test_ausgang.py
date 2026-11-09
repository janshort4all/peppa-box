"""Tests der Kopfhörer-Erkennung und Umschaltung (ausgang.py) und des Root-Helfers peppa_ausgang.sh.
Ohne Hardware: Helfer, Verstärker, Lautstärke, Steuerung und Rückmeldung der Tonausgabe werden
nachgebaut. Seit 09.11.2026 schaltet der Player ohne Raspotify-Neustart um (ausgabe.py folgt der
Vorgabe in /dev/shm/peppa-box-ausgang.json).
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
    def __init__(self, geraet="relais"):
        self.geraet, self.aufrufe = geraet, []

    def zeigen(self):
        return self.geraet

    def umstellen(self, ziel):
        self.aufrufe.append(ziel)
        self.geraet = ziel
        return True, f"Spotify-Ausgang: {ziel}"


class FakeSt:
    def __init__(self):
        self.reparaturen = []

    def reparatur_anfordern(self, grund):
        self.reparaturen.append(grund)


class FakeRueck:
    """Rückmeldung der Tonausgabe (ausgabe.py): folgt der Vorgabe, wenn folgen=True."""

    def __init__(self, lauf_lesen):
        self.lauf_lesen = lauf_lesen
        self.bei_fehler = None
        self.fluss = False
        self.folgen = True
        self._ziel = "lautsprecher"

    @property
    def ausgabe_ziel(self):
        if self.folgen:
            z = self.lauf_lesen("ausgang")
            self._ziel = z["ausgang"] if z else "lautsprecher"
        return self._ziel

    def fliesst(self):
        return self.fluss


class FakeLaut:
    def __init__(self):
        self.v = {"lautsprecher": 50, "kopfhoerer": 45}
        self.verlauf = []
        self.da = {"lautsprecher": True, "kopfhoerer": True}

    def eingerichtet(self, a):
        return self.da[a]

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
        self.rueck = FakeRueck(einstellungen.lauf_lesen)
        self.verst = []
        self.log = []
        self.neu()

    def neu(self, geraet="relais"):
        self.helfer.geraet = geraet
        self.verst.clear()
        self.a = ausgang.Ausgang(self.st, self.laut, einstellungen, rueck=self.rueck, helfer=self.helfer,
                                 verstaerker=lambda an, log=None: self.verst.append(an),
                                 jetzt=self.uhr, uhr=lambda: 1_800_000_000.0, log=self.log.append)
        self.a.start()

    def lauf(self, s, pegel):
        ende = self.uhr.t + s
        while self.uhr.t < ende:
            self.uhr.t += 0.05
            self.a.tick(pegel, self.uhr.t)

    def vorgabe(self):
        return einstellungen.lauf_lesen("ausgang")["ausgang"]

    def test_start_mit_tonausgabe(self):
        self.assertEqual((self.a.weg, self.a.aktuell, self.a.fehler), ("relais", "lautsprecher", None))
        self.assertEqual(self.vorgabe(), "lautsprecher")
        self.assertIs(self.rueck.bei_fehler.__self__, self.a)          # Fehler der Ausgabe kommen hier an

    def test_einstecken_und_ausstecken_ohne_neustart(self):
        self.lauf(1, 0)
        self.assertEqual(self.verst, [])
        self.lauf(1, 1)                                                 # eingesteckt (Pull-up hoch)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.assertEqual(self.vorgabe(), "kopfhoerer")                  # ausgabe.py folgt dieser Datei
        self.assertEqual(self.verst, [False])                           # Lautsprecher sofort stumm
        self.assertEqual(self.laut.v["kopfhoerer"], 30)                 # Startlautstärke Kopfhörer
        self.assertEqual(self.helfer.aufrufe, [])                       # kein Raspotify-Neustart
        self.lauf(4, 0)
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertEqual(self.vorgabe(), "lautsprecher")
        self.assertEqual(self.laut.v["kopfhoerer"], 0)
        self.assertEqual(self.verst, [False, True])
        self.assertEqual(self.st.reparaturen, [])
        self.assertIsNone(self.a.fehler)

    def test_kopfhoerer_startlautstaerke_nie_ueber_hoechstwert(self):
        cfg = einstellungen.laden()
        cfg["lautstaerke"]["kopfhoerer"].update(start=55, max=40)
        einstellungen.speichern(cfg)
        self.lauf(1, 1)
        self.assertEqual(self.laut.v["kopfhoerer"], 40)

    def test_entprellen(self):
        self.lauf(1, 0)
        self.lauf(0.3, 1)
        self.lauf(1, 0)
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertEqual(self.verst, [])

    def test_hoechstens_alle_3_s_und_nur_letzter_wunsch(self):
        self.lauf(1, 1)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.lauf(0.6, 0)
        self.lauf(0.6, 1)
        self.lauf(0.6, 0)
        self.assertEqual(self.a.aktuell, "kopfhoerer")                  # noch gesperrt (3 s)
        self.lauf(2, 0)
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertEqual(self.verst, [False, True])

    def test_polung_umgekehrt_und_erkennung_aus(self):
        cfg = einstellungen.laden()
        cfg["bedienung"]["klinke_eingesteckt_bei"] = "tief"
        einstellungen.speichern(cfg)
        self.lauf(1, 0)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        cfg["bedienung"]["kopfhoerer_erkennung"] = False
        einstellungen.speichern(cfg)
        self.lauf(4, 0)
        self.assertEqual(self.a.aktuell, "lautsprecher")

    def test_alte_einrichtung_schaltet_nie_um(self):
        self.neu("lautsprecher")                                        # Raspotify noch direkt auf ALSA
        self.assertEqual(self.a.weg, "alt")
        self.assertIn("dienst_einrichten.sh", self.a.fehler)
        self.lauf(5, 1)
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertEqual((self.verst, self.helfer.aufrufe), ([], []))

    def test_alte_einrichtung_auf_kopfhoerern_zurueck_auf_lautsprecher(self):
        self.neu("kopfhoerer")                                          # vom alten Umschalten geblieben
        self.assertEqual(self.helfer.aufrufe, ["lautsprecher"])
        self.assertEqual(self.vorgabe(), "lautsprecher")

    def test_ohne_helfer_nichts_umschalten(self):
        self.neu(None)
        self.assertIsNone(self.a.weg)
        self.lauf(5, 1)
        self.assertEqual((self.a.aktuell, self.verst), ("lautsprecher", []))

    def test_kopfhoerer_nicht_eingerichtet(self):
        self.laut.da["kopfhoerer"] = False
        self.lauf(5, 1)
        self.assertEqual((self.a.aktuell, self.verst), ("lautsprecher", []))
        self.assertIn("nicht eingerichtet", self.a.fehler)

    def test_kaputter_kopfhoerer_zurueck_auf_lautsprecher_und_gesperrt(self):
        self.lauf(1, 1)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.rueck.bei_fehler("kopfhoerer", "Device or resource busy", "lautsprecher")   # aus dem Empfangsfaden
        self.lauf(0.1, 1)
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertEqual(self.vorgabe(), "lautsprecher")
        self.assertEqual(self.verst, [False, True])                     # Verstärker wieder an
        self.assertEqual(self.laut.v["kopfhoerer"], 0)
        self.assertIn("busy", self.a.fehler)
        self.assertEqual(self.a.status["gesperrt_s"], 600)
        self.lauf(590, 1)                                               # bleibt eingesteckt: gesperrt
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.lauf(15, 1)                                                # nach 10 min neuer Versuch
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.assertIsNone(self.a.fehler)
        self.rueck.bei_fehler("kopfhoerer", "busy", "lautsprecher")     # wieder kaputt: länger gesperrt
        self.lauf(0.1, 1)
        self.assertEqual(self.a.status["gesperrt_s"], 1200)

    def test_fehler_vom_lautsprecher_sperrt_nicht(self):
        self.rueck.bei_fehler("lautsprecher", "x", None)
        self.lauf(2, 1)
        self.assertEqual(self.a.aktuell, "kopfhoerer")

    def test_tonausgabe_folgt_nicht_zurueck_auf_lautsprecher(self):
        self.rueck.fluss, self.rueck.folgen = True, False               # Musik läuft, Ausgabe hängt
        self.lauf(1, 1)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.lauf(3.5, 1)
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertIn("blieb auf lautsprecher", self.a.fehler)
        self.assertEqual(self.verst[-1], True)

    def test_tonausgabe_folgt(self):
        self.rueck.fluss = True
        self.lauf(5, 1)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.assertIsNone(self.a.fehler)
        self.assertFalse(self.a.status["umstellung"])

    def test_ohne_musik_nichts_zu_pruefen(self):
        self.rueck.folgen = False                                       # Ausgabe läuft gerade nicht
        self.lauf(6, 1)
        self.assertEqual(self.a.aktuell, "kopfhoerer")
        self.assertIsNone(self.a.fehler)

    def test_haengt_auf_kopfhoerern_raspotify_neu(self):
        self.rueck.fluss = True
        self.lauf(4, 1)
        self.rueck.folgen = False                                       # bleibt auf den Kopfhörern
        self.lauf(4, 0)
        self.assertEqual(self.a.aktuell, "lautsprecher")
        self.assertEqual(self.st.reparaturen, ["Tonausgabe folgt dem Ausgang nicht"])

    def test_stumm_halten(self):
        class Leser:
            sd = 1

            def pegel(self, pin):
                assert pin == ausgang.gpio.VERSTAERKER_SD
                return self.sd
        leser = Leser()
        self.a.stumm_halten(leser)                                      # Lautsprecher, SD hoch: gut
        self.assertEqual(self.verst, [])
        self.lauf(1, 1)                                                 # Kopfhörer
        self.verst.clear()
        self.a.stumm_halten(leser)                                      # z. B. peppa-stille neu: SD hoch
        self.assertEqual(self.verst, [False])
        self.lauf(4, 0)                                                 # Lautsprecher
        self.verst.clear()
        leser.sd = 0
        self.a.stumm_halten(leser)                                      # einmal tief: peppa-stille startet
        self.assertEqual(self.verst, [])
        self.a.stumm_halten(leser)                                      # zweimal: wieder an
        self.assertEqual(self.verst, [True])
        self.assertTrue(any("wieder an" in z for z in self.log))

    def test_stumm_halten_leser_kaputt(self):
        class Kaputt:
            def pegel(self, pin):
                raise OSError("weg")
        self.a.stumm_halten(Kaputt())
        self.assertEqual(self.verst, [])


RELAIS_CONF = 'LIBRESPOT_NAME="Peppa Box"\nLIBRESPOT_BACKEND="subprocess"\n' \
              'LIBRESPOT_DEVICE="/usr/local/lib/peppa-box/ausgabe"\n'


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
        self.schreiben('LIBRESPOT_NAME="Peppa Box"\nLIBRESPOT_DEVICE="lautsprecher"\n')
        self.env = {k: v for k, v in os.environ.items() if k != "SUDO_USER"}
        self.env.update(PEPPA_RASPOTIFY=self.conf, PEPPA_ASOUND=self.asound, PEPPA_SYSTEMCTL=sysctl)

    def schreiben(self, text):
        with open(self.conf, "w") as f:
            f.write(text)

    def systemctl(self):
        if not os.path.exists(self.log):
            return ""
        with open(self.log) as f:
            return f.read()

    def lauf(self, *args, **env):
        return subprocess.run(["sh", os.path.join(HIER, "peppa_ausgang.sh"), *args],
                              env=dict(self.env, **env), capture_output=True, text=True)

    def test_zeigen_relais(self):
        self.schreiben(RELAIS_CONF)
        self.assertEqual(self.lauf("zeigen").stdout.strip(), "relais")
        self.schreiben(RELAIS_CONF.replace("subprocess", "alsa"))      # Backend nicht umgestellt
        self.assertEqual(self.lauf("zeigen").stdout.strip(), "/usr/local/lib/peppa-box/ausgabe")

    def test_mit_relais_kein_neustart_beim_umschalten(self):
        self.schreiben(RELAIS_CONF)
        for ziel in ("kopfhoerer", "lautsprecher"):
            r = self.lauf(ziel)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.systemctl(), "")
        with open(self.conf) as f:
            self.assertEqual(f.read(), RELAIS_CONF)

    def test_neustart_reihenfolge(self):
        r = self.lauf("neustart")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.systemctl(), "stop raspotify\nrestart peppa-stille\nstart raspotify\n")

    def test_alter_weg_zeigen_umstellen_neustart(self):
        self.assertEqual(self.lauf("zeigen").stdout.strip(), "lautsprecher")
        r = self.lauf("kopfhoerer")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.lauf("zeigen").stdout.strip(), "kopfhoerer")
        self.assertEqual(self.systemctl(), "restart raspotify\n")
        with open(self.conf) as f:
            self.assertEqual(f.read().count("LIBRESPOT_DEVICE="), 1)

    def test_ohne_device_zeile_wird_ergaenzt(self):
        self.schreiben('LIBRESPOT_NAME="Peppa Box"\n#LIBRESPOT_DEVICE="default"\n')
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
        self.assertEqual(self.systemctl(), "")                # kein Neustart

    @unittest.skipIf(os.path.exists("/etc/raspotify/conf"), "nur ohne echte Raspotify-Einstellungen")
    def test_ueber_sudo_keine_umgelenkten_pfade(self):
        r = self.lauf("zeigen", SUDO_USER="jan")             # Pfade aus der Umgebung gelten dann nicht
        self.assertEqual(r.stdout.strip(), "")
        r = self.lauf("kopfhoerer", SUDO_USER="jan")
        self.assertEqual(r.returncode, 3)                    # /etc/raspotify/conf fehlt hier
        self.assertEqual(self.systemctl(), "")


if __name__ == "__main__":
    unittest.main()
