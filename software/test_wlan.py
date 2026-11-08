"""Tests für wlan_beschleunigen.sh und wlan_rueckfall.sh, ohne echten NetworkManager:
nmcli, sudo und systemctl werden nachgebaut, alle Pfade zeigen in einen Temp-Ordner.
Aufruf: cd software && python3 -m unittest -v test_wlan
"""
import os
import stat
import subprocess
import tempfile
import unittest

HIER = os.path.dirname(os.path.abspath(__file__))
SSID = "WLAN-567C6T_2_4"
PSK = r"geheim\pass wort;#1"


class Wlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = self.tmp.name
        self.netplan = os.path.join(d, "netplan")
        self.sicherung = os.path.join(d, "netplan.peppa-sicherung")
        self.nm = os.path.join(d, "nm")
        self.systemd = os.path.join(d, "systemd")
        os.makedirs(self.netplan)
        os.makedirs(self.systemd)
        for n in ("90-NM-a.yaml", "90-NM-b.yaml"):
            with open(os.path.join(self.netplan, n), "w") as f:
                f.write("network: {}\n")
        self.bin = os.path.join(d, "bin")
        os.mkdir(self.bin)
        self.log = os.path.join(d, "aufrufe.log")
        self.skript("sudo", 'if [ "$1" = install ]; then shift; exec install -m "$2" "$7" "$8"; fi\nexec "$@"')
        self.skript("systemctl", f'echo "systemctl $*" >> {self.log}')
        self.verbunden = os.path.join(d, "verbunden")
        self.skript("nmcli", f'''
echo "nmcli $*" >> {self.log}
case "$*" in
  *"connection show --active"*) printf 'netplan-wlan0-{SSID}:802-11-wireless:wlan0\\nlo:loopback:lo\\n' ;;
  *"wireless.ssid connection show netplan-wlan0-{SSID}") echo '{SSID}' ;;
  *"key-mgmt connection show netplan-wlan0-{SSID}") echo 'wpa-psk' ;;
  *"-s -t -g 802-11-wireless-security.psk connection show netplan-wlan0-{SSID}") printf '%s\\n' '{PSK}' ;;
  *"device"*) if [ -f {self.verbunden} ]; then echo 'wlan0:wifi:connected'; else echo 'wlan0:wifi:disconnected'; fi ;;
  *) exit 1 ;;
esac''')
        self.env = dict(os.environ, PATH=self.bin + ":" + os.environ["PATH"], PEPPA_NETPLAN=self.netplan,
                        PEPPA_NETPLAN_SICHERUNG=self.sicherung, PEPPA_NM_CONNECTIONS=self.nm,
                        PEPPA_SYSTEMD=self.systemd, PEPPA_TROCKEN="1")
        self.keyfile = os.path.join(self.nm, "peppa-wlan.nmconnection")

    def skript(self, name, inhalt):
        p = os.path.join(self.bin, name)
        with open(p, "w") as f:
            f.write("#!/bin/sh\n" + inhalt + "\n")
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)

    def lauf(self, skript, *args, **env):
        return subprocess.run(["sh", os.path.join(HIER, skript), *args], env=dict(self.env, **env),
                              capture_output=True, text=True)

    def test_umstellen_rueckweg(self):
        r = self.lauf("wlan_beschleunigen.sh")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("geheim", r.stdout + r.stderr)                     # Passwort nie ausgeben
        with open(self.keyfile) as f:
            k = f.read()
        self.assertEqual(stat.S_IMODE(os.stat(self.keyfile).st_mode), 0o600)
        self.assertIn(f"\nssid={SSID}\n", k)
        self.assertIn("\npsk=geheim\\\\pass wort;#1\n", k)                 # Backslash maskiert
        self.assertIn("key-mgmt=wpa-psk", k)
        self.assertIn("powersave=2", k)
        self.assertRegex(k, r"\nuuid=[0-9a-f-]{36}\n")
        self.assertEqual(os.listdir(self.netplan), [])
        self.assertEqual(sorted(os.listdir(self.sicherung)), ["90-NM-a.yaml", "90-NM-b.yaml"])
        with open(os.path.join(self.systemd, "peppa-wlan-rueckfall.service")) as f:
            dienst = f.read()
        self.assertIn("wlan_rueckfall.sh", dienst)
        r = self.lauf("wlan_beschleunigen.sh")                               # zweiter Lauf: nichts tun
        self.assertIn("Schon umgestellt", r.stdout)
        r = self.lauf("wlan_beschleunigen.sh", "--zurueck")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorted(os.listdir(self.netplan)), ["90-NM-a.yaml", "90-NM-b.yaml"])
        self.assertFalse(os.path.exists(self.sicherung))
        self.assertFalse(os.path.exists(self.keyfile))

    def test_abbruch_ohne_netplan_wlan_aendert_nichts(self):
        self.skript("nmcli", 'case "$*" in *"--active"*) echo "lo:loopback:lo" ;; *) exit 1 ;; esac')
        r = self.lauf("wlan_beschleunigen.sh")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(len(os.listdir(self.netplan)), 2)
        self.assertFalse(os.path.exists(self.keyfile))

    def test_rueckfall_stellt_her_wenn_kein_wlan(self):
        self.assertEqual(self.lauf("wlan_beschleunigen.sh").returncode, 0)
        r = self.lauf("wlan_rueckfall.sh", PEPPA_RUECKFALL_FRIST="0")
        self.assertIn("wieder her", r.stdout)
        self.assertEqual(len(os.listdir(self.netplan)), 2)
        self.assertFalse(os.path.exists(self.keyfile))
        with open(self.log) as f:
            self.assertIn("systemctl restart NetworkManager", f.read())

    def test_rueckfall_tut_nichts_wenn_verbunden(self):
        self.assertEqual(self.lauf("wlan_beschleunigen.sh").returncode, 0)
        open(self.verbunden, "w").close()
        r = self.lauf("wlan_rueckfall.sh", PEPPA_RUECKFALL_FRIST="120")
        self.assertIn("alles gut", r.stdout)
        self.assertTrue(os.path.exists(self.keyfile))
        self.assertEqual(os.listdir(self.netplan), [])

    def test_rueckfall_schaltet_sich_nach_erfolg_ab(self):
        self.assertEqual(self.lauf("wlan_beschleunigen.sh").returncode, 0)
        open(self.verbunden, "w").close()
        r = self.lauf("wlan_rueckfall.sh", PEPPA_RUECKFALL_FRIST="120")
        self.assertIn("abgeschaltet", r.stdout)
        with open(self.log) as f:
            self.assertIn("systemctl disable peppa-wlan-rueckfall.service", f.read())
        self.assertTrue(os.path.isdir(self.sicherung))                   # Rückweg von Hand bleibt

    def test_rueckfall_ohne_sicherung_still(self):
        r = self.lauf("wlan_rueckfall.sh", PEPPA_RUECKFALL_FRIST="0")
        self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.assertEqual(len(os.listdir(self.netplan)), 2)


if __name__ == "__main__":
    unittest.main()
