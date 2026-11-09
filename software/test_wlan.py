"""Tests für wlan_beschleunigen.sh, wlan_rueckfall.sh, wlan_hinzufuegen.sh und wlan_suche.sh, ohne echten NetworkManager:
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
        self.assertIn("\nautoconnect-priority=10\nautoconnect-retries=0\n", k)  # nie aufgeben
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


HEIM = """[connection]
id=peppa-wlan
uuid=11111111-2222-3333-4444-555555555555
type=wifi
autoconnect=true
autoconnect-priority=10

[wifi]
ssid=WLAN-567C6T_2_4
"""


class Hinzufuegen(unittest.TestCase):
    """wlan_hinzufuegen.sh direkt auf Dateien im Temp-Ordner (PEPPA_OHNE_SUDO, PEPPA_TROCKEN)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.nm = os.path.join(self.tmp.name, "nm")
        os.mkdir(self.nm)
        with open(os.path.join(self.nm, "peppa-wlan.nmconnection"), "w") as f:
            f.write(HEIM)
        self.env = dict(os.environ, PEPPA_NM_CONNECTIONS=self.nm, PEPPA_OHNE_SUDO="1", PEPPA_TROCKEN="1")

    def lauf(self, eingabe="", *args):
        return subprocess.run(["sh", os.path.join(HIER, "wlan_hinzufuegen.sh"), *args], input=eingabe,
                              env=self.env, capture_output=True, text=True)

    def lesen(self, name):
        with open(os.path.join(self.nm, name)) as f:
            return f.read()

    def test_hotspot_eintragen(self):
        r = self.lauf("JanHandy\nsuper\\geheim 1\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("geheim", r.stdout + r.stderr)                  # Passwort nie ausgeben
        datei = os.path.join(self.nm, "peppa-wlan-JanHandy.nmconnection")
        self.assertEqual(stat.S_IMODE(os.stat(datei).st_mode), 0o600)
        k = self.lesen("peppa-wlan-JanHandy.nmconnection")
        for zeile in ("id=peppa-wlan-JanHandy", "autoconnect-priority=5", "autoconnect-retries=0",
                      "ssid=JanHandy", "psk=super\\\\geheim 1", "key-mgmt=wpa-psk", "powersave=2"):
            self.assertIn("\n" + zeile + "\n", k)
        self.assertRegex(k, r"\nuuid=[0-9a-f-]{36}\n")
        heim = self.lesen("peppa-wlan.nmconnection")                     # Heim-WLAN: nie aufgeben
        self.assertIn("\nautoconnect-priority=10\nautoconnect-retries=0\n", heim)
        self.assertEqual(heim.count("autoconnect-retries"), 1)

    def test_zweimal_gleicher_name_ersetzt_und_behaelt_uuid(self):
        self.lauf("JanHandy\npasswort1\n")
        alt = self.lesen("peppa-wlan-JanHandy.nmconnection")
        r = self.lauf("JanHandy\npasswort2\n", "--prioritaet", "6")
        self.assertIn("aktualisiert", r.stdout)
        neu = self.lesen("peppa-wlan-JanHandy.nmconnection")
        self.assertIn("psk=passwort2", neu)
        self.assertIn("autoconnect-priority=6", neu)
        uuid = [z for z in alt.splitlines() if z.startswith("uuid=")]
        self.assertIn(uuid[0], neu)
        self.assertEqual(self.lesen("peppa-wlan.nmconnection").count("autoconnect-retries"), 1)

    def test_falsche_eingaben_aendern_nichts(self):
        for eingabe, args in (("JanHandy\nkurz\n", ()),                         # Passwort < 8
                              ("\npasswort1\n", ()),                           # kein Name
                              ("A" * 33 + "\npasswort1\n", ()),                # Name zu lang
                              ("WLAN-567C6T_2_4\npasswort1\n", ()),            # Heim-WLAN
                              ("JanHandy\npasswort1\n", ("--prioritaet", "10"))):
            r = self.lauf(eingabe, *args)
            self.assertNotEqual(r.returncode, 0, eingabe)
            self.assertNotIn("passwort1", r.stdout + r.stderr)
        self.assertEqual(os.listdir(self.nm), ["peppa-wlan.nmconnection"])

    def test_sonderzeichen_hinweis(self):
        r = self.lauf("Jan’s Handy\npasswort1\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Sonderzeichen", r.stdout)
        self.assertIn("\nssid=Jan’s Handy\n", self.lesen("peppa-wlan-Jan___s_Handy.nmconnection"))

    def test_liste_und_entfernen(self):
        self.lauf("JanHandy\npasswort1\n")
        self.lauf("Handy Frau\npasswort2\n")
        r = self.lauf("", "--liste")
        self.assertRegex(r.stdout, r"WLAN-567C6T_2_4 +Prioritaet 10")
        self.assertRegex(r.stdout, r"JanHandy +Prioritaet 5")
        self.assertRegex(r.stdout, r"Handy Frau +Prioritaet 5")
        self.assertNotIn("passwort", r.stdout)
        r = self.lauf("", "--entfernen", "Handy Frau")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(sorted(os.listdir(self.nm)), ["peppa-wlan-JanHandy.nmconnection", "peppa-wlan.nmconnection"])
        self.assertNotEqual(self.lauf("", "--entfernen", "Gibtsnicht").returncode, 0)


class Suche(unittest.TestCase):
    """wlan_suche.sh: neue Suche nur, wenn das WLAN wirklich getrennt ist."""

    def lauf(self, zustand):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "log")
            p = os.path.join(d, "nmcli")
            with open(p, "w") as f:
                f.write(f"""#!/bin/sh
echo "nmcli $*" >> {log}
case "$*" in
  *"-f TYPE,STATE device"*) printf 'wifi:{zustand}\\nloopback:connected (externally)\\n' ;;
  *"device show wlan0"*) echo peppa-wlan-JanHandy ;;
esac
""")
            os.chmod(p, 0o755)
            env = dict(os.environ, PATH=d + ":" + os.environ["PATH"], PEPPA_SUCHE_EINMAL="1")
            r = subprocess.run(["sh", os.path.join(HIER, "wlan_suche.sh")], env=env, capture_output=True,
                               text=True, timeout=10)
            with open(log) as f:
                return r, f.read()

    def test_getrennt_sucht(self):
        r, log = self.lauf("disconnected")
        self.assertIn("nmcli device wifi rescan", log)
        self.assertIn("suche alle 10 s", r.stdout)

    def test_verbunden_sucht_nicht(self):
        r, log = self.lauf("connected")
        self.assertNotIn("rescan", log)
        self.assertIn("verbunden: peppa-wlan-JanHandy", r.stdout)

    def test_waehrend_anmeldung_sucht_nicht(self):
        r, log = self.lauf("connecting (getting IP configuration)")
        self.assertNotIn("rescan", log)


if __name__ == "__main__":
    unittest.main()
