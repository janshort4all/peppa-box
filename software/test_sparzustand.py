"""Tests für den Sparzustand (sparzustand.py: Wache, sparen.sh: Root-Helfer) ohne Hardware: Taste, Uhr,
sudo/systemd und Akku sind nachgebaut. Aufruf: cd software && python3 -m unittest -v test_sparzustand
"""
import os
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

import sparzustand

HIER = os.path.dirname(os.path.abspath(__file__))


class Uhr:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def schlaf(self, s):
        self.t += s


class Basis(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.t0 = self.uhr.t
        self.gedrueckt = []                  # Liste (von, bis) in Sekunden seit Beginn, in denen die Taste gedrückt ist
        self.nicht_lesbar = False
        self.aufwecken_ok = [True]           # Ergebnisse der Reihe nach, der letzte gilt weiter
        self.ereignisse = []
        self.akku = {"spannung": 3.9, "prozent": 64, "richtung": "akku"}
        self.meldungen = []

    def pegel(self):
        if self.nicht_lesbar:
            return None
        s = self.uhr.t - self.t0
        return 0 if any(a <= s < b for a, b in self.gedrueckt) else 1       # gedrückt = tief

    def aufwecken(self):
        self.ereignisse.append("aufwecken")
        ok = self.aufwecken_ok.pop(0) if len(self.aufwecken_ok) > 1 else self.aufwecken_ok[0]
        return ok, "" if ok else "sudo: Passwort nötig"

    def wache(self, aus_nach=3600 * 6, **kw):
        return sparzustand.Wache(
            self.pegel, aufwecken=self.aufwecken, ton=lambda: self.ereignisse.append("ton"),
            ausschalten=lambda: (self.ereignisse.append("ausschalten") or (True, "")),
            neustart=lambda: (self.ereignisse.append("neustart") or (True, "")),
            akku_lesen=lambda: dict(self.akku), aus_nach=aus_nach, jetzt=self.uhr, schlaf=self.uhr.schlaf,
            log=self.meldungen.append, **kw)


class Taste(Basis):
    def test_taste_weckt_mit_ton_und_dienst(self):
        self.gedrueckt = [(2.0, 3.0)]
        w = self.wache()
        self.assertEqual(w.lauf(), "aufgewacht")
        self.assertEqual(self.ereignisse, ["aufwecken", "ton"])
        self.assertLess(self.uhr.t - self.t0, 2.5)                     # sofort nach dem Druck (150 ms Entprellung)

    def test_taste_vom_eintritt_weckt_nicht(self):
        # man hält die Taste noch, als der Sparzustand beginnt: erst loslassen, dann zählt ein neuer Druck
        self.gedrueckt = [(0.0, 1.0), (4.0, 5.0)]
        w = self.wache()
        self.assertEqual(w.lauf(), "aufgewacht")
        self.assertGreaterEqual(self.uhr.t - self.t0, 4.0)
        self.assertLess(self.uhr.t - self.t0, 4.5)

    def test_kurzer_stoerimpuls_weckt_nicht(self):
        self.gedrueckt = [(2.0, 2.08), (3.0, 3.07), (5.0, 5.5)]       # zwei Störungen unter 150 ms, dann ein Druck
        w = self.wache()
        self.assertEqual(w.lauf(), "aufgewacht")
        self.assertGreaterEqual(self.uhr.t - self.t0, 5.0)

    def test_taste_nicht_lesbar_weckt_nie_zeit_laeuft_weiter(self):
        self.nicht_lesbar = True
        w = self.wache(aus_nach=60)
        self.assertEqual(w.lauf(), "aus_zeit")
        self.assertEqual(self.ereignisse, ["ausschalten"])

    def test_klemmende_taste_weckt_nie_dann_aus_nach_zeit(self):
        self.gedrueckt = [(0.0, 1e9)]
        w = self.wache(aus_nach=60)
        self.assertEqual(w.lauf(), "aus_zeit")
        self.assertNotIn("aufwecken", self.ereignisse)


class Aufwecken(Basis):
    def test_aufwecken_klappt_erst_beim_zweiten_versuch(self):
        self.gedrueckt = [(1.0, 2.0)]
        self.aufwecken_ok = [False, True]
        w = self.wache()
        self.assertEqual(w.lauf(), "aufgewacht")
        self.assertEqual(self.ereignisse, ["aufwecken", "aufwecken", "ton"])
        self.assertNotIn("neustart", self.ereignisse)

    def test_aufwecken_scheitert_ganz_dann_neustart_aber_ton(self):
        self.gedrueckt = [(1.0, 2.0)]
        self.aufwecken_ok = [False]
        w = self.wache()
        self.assertEqual(w.lauf(), "aufgewacht")
        self.assertEqual(self.ereignisse.count("aufwecken"), sparzustand.AUFWECKEN_VERSUCHE)
        self.assertEqual(self.ereignisse[-2:], ["ton", "neustart"])      # nie tot im Sparzustand hängen

    def test_fehler_im_ton_haelt_das_aufwecken_nicht_auf(self):
        self.gedrueckt = [(1.0, 2.0)]
        w = self.wache()
        w.ton = mock.Mock(side_effect=OSError("aplay kaputt"))
        self.assertEqual(w.lauf(), "aufgewacht")
        self.assertEqual(self.ereignisse, ["aufwecken"])
        self.assertTrue(any("Startton" in m for m in self.meldungen))


class GanzAus(Basis):
    def test_nach_der_eingestellten_zeit_ganz_aus(self):
        w = self.wache(aus_nach=3600 * 6)
        self.assertEqual(w.lauf(), "aus_zeit")
        self.assertGreaterEqual(self.uhr.t - self.t0, 3600 * 6)
        self.assertLess(self.uhr.t - self.t0, 3600 * 6 + 1)
        self.assertEqual(self.ereignisse, ["ausschalten"])

    def test_ausschalten_scheitert_neuer_versuch(self):
        antworten = [(False, "sudo"), (True, "")]
        w = self.wache(aus_nach=10)
        w.ausschalten_befehl = lambda: (self.ereignisse.append("ausschalten") or antworten.pop(0))
        self.assertEqual(w.lauf(), "aus_zeit")
        self.assertEqual(self.ereignisse, ["ausschalten", "ausschalten"])

    def test_akku_leer_schaltet_sauber_aus(self):
        self.akku = {"spannung": 3.20, "prozent": 0, "richtung": "akku"}
        w = self.wache()
        self.assertEqual(w.lauf(), "aus_akku")
        self.assertEqual(self.ereignisse, ["ausschalten"])
        self.assertLess(self.uhr.t - self.t0, 60)                       # 3 Messungen im Abstand von 15 s

    def test_am_netzteil_wird_nicht_ausgeschaltet(self):
        self.akku = {"spannung": 3.20, "prozent": None, "richtung": "laedt"}
        w = self.wache(aus_nach=200)
        self.assertEqual(w.lauf(), "aus_zeit")
        self.assertEqual(self.meldungen.count("Sparzustand: Box wird ganz ausgeschaltet (akku)"), 0)

    def test_aus_nach_aus_den_einstellungen(self):
        einst = mock.Mock()
        einst.laden.return_value = {"sparzustand": {"aus_nach_h": 2}}
        self.assertEqual(sparzustand.aus_nach_s(einst), 7200)
        einst.laden.side_effect = OSError
        self.assertEqual(sparzustand.aus_nach_s(einst), 6 * 3600)         # kaputt: Standard


class Hauptprogramm(Basis):
    def test_gpio_nicht_lesbar_box_wird_geweckt(self):
        with mock.patch.object(sparzustand.gpio, "oeffnen", side_effect=OSError("kein gpiomem")), \
                mock.patch.object(sparzustand, "befehl_aufwecken", return_value=(True, "")) as aufw:
            self.assertEqual(sparzustand.main(), 1)
            aufw.assert_called_once()

    def test_unerwarteter_fehler_weckt_die_box(self):
        leser = mock.Mock()
        with mock.patch.object(sparzustand.gpio, "oeffnen", return_value=leser), \
                mock.patch.object(sparzustand.Wache, "lauf", side_effect=RuntimeError("kaputt")), \
                mock.patch.object(sparzustand, "befehl_aufwecken", return_value=(True, "")) as aufw, \
                mock.patch.object(sparzustand, "befehl_neustart") as neu:
            self.assertEqual(sparzustand.main(), 1)
            aufw.assert_called_once()
            neu.assert_not_called()
            leser.close.assert_called_once()

    def test_unerwarteter_fehler_und_aufwecken_scheitert_neustart(self):
        with mock.patch.object(sparzustand.gpio, "oeffnen", return_value=mock.Mock()), \
                mock.patch.object(sparzustand.Wache, "lauf", side_effect=RuntimeError("kaputt")), \
                mock.patch.object(sparzustand, "befehl_aufwecken", return_value=(False, "sudo")), \
                mock.patch.object(sparzustand, "befehl_neustart") as neu:
            sparzustand.main()
            neu.assert_called_once()

    def test_befehle_mit_sudo_und_no_block(self):
        with mock.patch.object(sparzustand.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            self.assertEqual(sparzustand.befehl_aufwecken(), (True, ""))
            cmd = run.call_args[0][0]
            self.assertEqual(cmd[:2], ["sudo", "-n"])
            self.assertEqual(cmd[-3:], ["start", "--no-block", "peppa-aufwachen.service"])


class Helfer(unittest.TestCase):
    """sparen.sh mit nachgebauten systemctl/nmcli/nm-online (schreiben ihre Aufrufe in eine Datei)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = os.path.join(self.tmp.name, "log")
        self.scheitert = ""

    def fake(self, name, inhalt=""):
        p = os.path.join(self.tmp.name, name)
        with open(p, "w") as f:
            f.write(f'#!/bin/sh\necho "{name} $*" >> "{self.log}"\n{inhalt}\n')
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
        return p

    def lauf(self, arg, systemctl_fehler="", nmonline_fehler=False, nmcli_fehler=False):
        env = dict(os.environ,
                   PEPPA_SYSTEMCTL=self.fake("systemctl", f'case "$*" in *{systemctl_fehler}*) exit 5;; esac' if systemctl_fehler else ""),
                   PEPPA_NMCLI=self.fake("nmcli", "exit 1" if nmcli_fehler else ""),
                   PEPPA_NMONLINE=self.fake("nm-online", "exit 1" if nmonline_fehler else ""))
        if os.path.exists(self.log):
            os.remove(self.log)
        r = subprocess.run(["sh", os.path.join(HIER, "sparen.sh"), arg], env=env, capture_output=True, text=True)
        try:
            with open(self.log) as f:
                zeilen = f.read().splitlines()
        except OSError:
            zeilen = []
        return r, zeilen

    def test_ein_beendet_betrieb_dann_wlan_aus(self):
        r, z = self.lauf("ein")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(z, ["systemctl stop peppa-player.service", "systemctl stop peppa-web.service",
                             "systemctl stop raspotify.service", "systemctl stop peppa-wlan-suche.service",
                             "nmcli radio wifi off"])

    def test_ein_ein_fehler_haelt_die_anderen_nicht_auf(self):
        r, z = self.lauf("ein", systemctl_fehler="raspotify")
        self.assertEqual(r.returncode, 0)
        self.assertIn("nmcli radio wifi off", z)
        self.assertIn("systemctl stop peppa-wlan-suche.service", z)
        self.assertIn("raspotify", r.stdout)

    def test_aus_wlan_an_player_sofort_raspotify_nach_dem_netz(self):
        r, z = self.lauf("aus")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(z, ["nmcli radio wifi on",
                             "systemctl start --no-block peppa-player.service peppa-web.service peppa-wlan-suche.service",
                             "nm-online -q -t 25",
                             "systemctl start --no-block raspotify.service"])

    def test_aus_ohne_wlan_startet_raspotify_trotzdem(self):
        r, z = self.lauf("aus", nmonline_fehler=True)
        self.assertEqual(z[-1], "systemctl start --no-block raspotify.service")
        self.assertIn("kein WLAN nach 25 s", r.stdout)

    def test_wlan_an(self):
        r, z = self.lauf("wlan-an")
        self.assertEqual((r.returncode, z), (0, ["nmcli radio wifi on"]))
        r, z = self.lauf("wlan-an", nmcli_fehler=True)
        self.assertEqual(r.returncode, 1)

    def test_unbekannt(self):
        r, z = self.lauf("quatsch")
        self.assertEqual((r.returncode, z), (2, []))


if __name__ == "__main__":
    unittest.main()
