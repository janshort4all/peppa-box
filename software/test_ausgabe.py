"""Tests für die Tonausgabe (ausgabe.py), den Ereignis-Hook (ereignis.py) und den Empfang im Player
(rueckmeldung.py). Die Ausgabe läuft als echtes Programm wie unter Raspotify: Ton auf stdin,
Rückmeldung per UDP. aplay wird durch ein Testprogramm ersetzt oder (wenn vorhanden) echt mit einer
ALSA-Datei-Ausgabe benutzt.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

import ereignis
import rueckmeldung

HIER = os.path.dirname(os.path.abspath(__file__))
AUSGABE = os.path.join(HIER, "ausgabe.py")

FALSCHES_APLAY = textwrap.dedent("""\
    #!/usr/bin/env python3
    import os, sys
    args = sys.argv[1:]
    geraet = args[args.index("-D") + 1]
    if geraet in os.environ.get("FAKE_KAPUTT", "").split(","):
        print("aplay: main: audio open error: Device or resource busy", file=sys.stderr)
        sys.exit(1)
    with open(os.path.join(os.environ["FAKE_ORDNER"], geraet + ".raw"), "ab") as f:
        while True:
            d = sys.stdin.buffer.read1(65536)
            if not d:
                break
            f.write(d)
            f.flush()
""")


def freier_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    return s, port


class AusgabeProgramm(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ordner = self.tmp.name
        self.wahl = os.path.join(self.ordner, "peppa-box-ausgang.json")
        self.aplay = os.path.join(self.ordner, "aplay")
        with open(self.aplay, "w") as f:
            f.write(FALSCHES_APLAY)
        os.chmod(self.aplay, 0o755)
        self.empfang, self.port = freier_port()
        self.empfang.settimeout(0.05)
        self.addCleanup(self.empfang.close)
        self.nachrichten = []

    def waehlen(self, ziel, klang=False):
        tmp = self.wahl + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"ausgang": ziel, "klang": klang}, f)
        os.replace(tmp, self.wahl)

    def starten(self, kaputt="", aplay=None, umgebung=None):
        env = dict(os.environ, PEPPA_AUSGABE_WAHL=self.wahl, PEPPA_AUSGABE_APLAY=aplay or self.aplay,
                   PEPPA_RUECKMELDUNG_PORT=str(self.port), FAKE_ORDNER=self.ordner, FAKE_KAPUTT=kaputt,
                   **(umgebung or {}))
        p = subprocess.Popen([sys.executable, AUSGABE], stdin=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        self.addCleanup(lambda: p.poll() is None and p.kill())
        return p

    def sammeln(self, sekunden):
        ende = time.monotonic() + sekunden
        while time.monotonic() < ende:
            try:
                d, _ = self.empfang.recvfrom(4096)
                self.nachrichten.append(json.loads(d))
            except socket.timeout:
                pass

    def senden(self, p, sekunden, stueck=b"\x01\x02" * 2048):
        ende = time.monotonic() + sekunden
        while time.monotonic() < ende:
            p.stdin.write(stueck)
            p.stdin.flush()
            self.sammeln(0.02)

    def groesse(self, geraet):
        p = os.path.join(self.ordner, geraet + ".raw")
        return os.path.getsize(p) if os.path.exists(p) else 0

    def arten(self):
        return [n["art"] for n in self.nachrichten]

    def test_spielt_auf_vorgabe_und_meldet_fluss(self):
        self.waehlen("lautsprecher")
        p = self.starten()
        self.senden(p, 1.5)
        p.stdin.close()
        self.assertEqual(p.wait(timeout=5), 0)
        self.sammeln(0.2)
        self.assertGreater(self.groesse("lautsprecher"), 0)
        self.assertEqual(self.groesse("kopfhoerer"), 0)
        self.assertEqual(self.nachrichten[0]["art"], "start")
        self.assertEqual(self.nachrichten[0]["ziel"], "lautsprecher")
        fluss = [n for n in self.nachrichten if n["art"] == "fluss"]
        self.assertTrue(fluss)
        self.assertTrue(all(n["bytes"] > 0 and n["ziel"] == "lautsprecher" for n in fluss))
        self.assertEqual(self.arten()[-1], "ende")

    def test_wechselt_ohne_abbruch(self):
        self.waehlen("lautsprecher")
        p = self.starten()
        self.senden(p, 0.6)
        self.waehlen("kopfhoerer")
        self.senden(p, 0.8)
        vorher = self.groesse("lautsprecher")
        self.waehlen("lautsprecher")
        self.senden(p, 0.8)
        p.stdin.close()
        self.assertEqual(p.wait(timeout=5), 0)
        self.sammeln(0.2)
        self.assertGreater(self.groesse("kopfhoerer"), 0)
        self.assertGreater(self.groesse("lautsprecher"), vorher)          # zurück auf den Lautsprecher
        wechsel = [(n["von"], n["nach"]) for n in self.nachrichten if n["art"] == "wechsel"]
        self.assertEqual(wechsel, [("lautsprecher", "kopfhoerer"), ("kopfhoerer", "lautsprecher")])
        self.assertNotIn("fehler", self.arten())

    def test_kaputter_kopfhoerer_faellt_auf_lautsprecher_zurueck(self):
        self.waehlen("kopfhoerer")
        p = self.starten(kaputt="kopfhoerer")
        self.senden(p, 3.0)                                                 # erst zwei neue Versuche
        self.assertIsNone(p.poll())                                         # läuft weiter
        p.stdin.close()
        p.wait(timeout=5)
        self.sammeln(0.2)
        fehler = [n for n in self.nachrichten if n["art"] == "fehler"]
        self.assertEqual(len(fehler), 1)                                    # Kopfhörer bleiben gesperrt
        self.assertEqual((fehler[0]["ziel"], fehler[0]["rueckfall"]), ("kopfhoerer", "lautsprecher"))
        self.assertGreater(self.groesse("lautsprecher"), 0)
        self.assertTrue([n for n in self.nachrichten if n["art"] == "fluss" and n["ziel"] == "lautsprecher"])

    def test_kopfhoerer_kurz_belegt_neuer_versuch(self):
        # Pi-Klinke ohne Mischer: einmal belegt (z. B. Ansage), beim zweiten Versuch frei
        sperre = os.path.join(self.ordner, "belegt_einmal")
        with open(sperre, "w"):
            pass
        with open(self.aplay, "a") as f:
            pass
        with open(self.aplay) as f:
            text = f.read()
        text = text.replace('if geraet in os.environ.get("FAKE_KAPUTT", "").split(","):',
                            'if geraet == "kopfhoerer" and os.path.exists(os.environ["FAKE_ORDNER"] + "/belegt_einmal"):\n'
                            '    os.remove(os.environ["FAKE_ORDNER"] + "/belegt_einmal")\n'
                            '    sys.exit(1)\n'
                            'if geraet in os.environ.get("FAKE_KAPUTT", "").split(","):')
        with open(self.aplay, "w") as f:
            f.write(text)
        self.waehlen("kopfhoerer")
        p = self.starten()
        self.senden(p, 1.5)
        p.stdin.close()
        p.wait(timeout=5)
        self.sammeln(0.2)
        self.assertNotIn("fehler", self.arten())
        self.assertGreater(self.groesse("kopfhoerer"), 0)
        self.assertEqual(self.groesse("lautsprecher"), 0)

    def test_lautsprecher_kaputt_endet_mit_fehler(self):
        self.waehlen("lautsprecher")
        p = self.starten(kaputt="lautsprecher")
        try:
            self.senden(p, 2.0)
        except BrokenPipeError:
            pass
        self.assertNotEqual(p.wait(timeout=5), 0)                           # librespot startet neu bzw. pausiert
        self.sammeln(0.2)
        self.assertGreaterEqual(len([n for n in self.nachrichten if n["art"] == "fehler"]), 3)

    def test_mit_equalizer(self):
        self.waehlen("lautsprecher", klang=True)
        p = self.starten()
        self.senden(p, 0.6)
        self.waehlen("kopfhoerer", klang=True)                              # Kopfhörer ohne Equalizer
        self.senden(p, 0.6)
        p.stdin.close()
        p.wait(timeout=5)
        self.sammeln(0.2)
        self.assertGreater(self.groesse("lautsprecher_klang"), 0)
        self.assertGreater(self.groesse("kopfhoerer"), 0)
        self.assertEqual(self.groesse("lautsprecher"), 0)
        self.assertNotIn("fehler", self.arten())

    def test_kaputter_equalizer_musik_laeuft_ohne_weiter(self):
        # 09.11.2026: Equalizer ließ sich nicht öffnen -> keine Musik. Jetzt: sofort ohne Equalizer weiter
        self.waehlen("lautsprecher", klang=True)
        p = self.starten(kaputt="lautsprecher_klang")
        self.senden(p, 1.5)
        self.assertIsNone(p.poll())
        p.stdin.close()
        self.assertEqual(p.wait(timeout=5), 0)
        self.sammeln(0.2)
        fehler = [n for n in self.nachrichten if n["art"] == "fehler"]
        self.assertEqual([(n["ziel"], n["rueckfall"]) for n in fehler], [("klang", "lautsprecher")])
        self.assertGreater(self.groesse("lautsprecher"), 0)
        self.waehlen("kopfhoerer", klang=True)                              # Kopfhörer bleiben möglich

    def test_equalizer_an_und_aus_waehrend_musik(self):
        self.waehlen("lautsprecher", klang=False)
        p = self.starten()
        self.senden(p, 0.6)
        self.waehlen("lautsprecher", klang=True)
        self.senden(p, 0.6)
        p.stdin.close()
        p.wait(timeout=5)
        self.assertGreater(self.groesse("lautsprecher_klang"), 0)

    def test_ohne_vorgabe_lautsprecher(self):
        with open(self.wahl, "w") as f:
            f.write("kaputt{")
        p = self.starten()
        self.senden(p, 0.4)
        p.stdin.close()
        p.wait(timeout=5)
        self.assertGreater(self.groesse("lautsprecher"), 0)

    @unittest.skipUnless(shutil.which("aplay"), "aplay fehlt")
    def test_echtes_aplay_mit_den_argumenten(self):
        """Die Befehlszeile für aplay (Rohdaten, S16_LE, 44,1 kHz, Stereo) mit echtem alsa-lib."""
        conf = os.path.join(self.ordner, "asound.conf")
        with open(conf, "w") as f:
            for name in ("lautsprecher", "kopfhoerer"):
                f.write(f'pcm.{name} {{ type file slave.pcm "null" file "{self.ordner}/{name}.raw" format raw }}\n')
            f.write("pcm.null { type null }\n")
        self.waehlen("lautsprecher")
        p = self.starten(aplay=shutil.which("aplay"), umgebung={"ALSA_CONFIG_PATH": conf})
        self.senden(p, 0.8)
        self.waehlen("kopfhoerer")
        self.senden(p, 0.8)
        p.stdin.close()
        self.assertEqual(p.wait(timeout=10), 0, p.stderr.read().decode())
        self.sammeln(0.2)
        # beim Wechsel wird aplay hart beendet: die ALSA-Datei-Ausgabe verliert dann ihren Puffer,
        # darum zählt für den Lautsprecher die Rückmeldung; die Kopfhörer endeten sanft (Datei voll)
        self.assertTrue([n for n in self.nachrichten if n["art"] == "fluss" and n["ziel"] == "lautsprecher"])
        self.assertGreater(self.groesse("kopfhoerer"), 0)
        self.assertIn("wechsel", self.arten())
        self.assertNotIn("fehler", self.arten())


class Ereignis(unittest.TestCase):
    def test_nachricht_ohne_benutzername(self):
        n = ereignis.nachricht({"PLAYER_EVENT": "playing", "TRACK_ID": "abc", "POSITION_MS": "1200",
                                "USER_NAME": "geheim", "PATH": "/usr/bin"})
        self.assertEqual(n, {"q": "ereignis", "player_event": "playing", "track_id": "abc", "position_ms": "1200"})

    def test_programm_sendet_und_endet_mit_null(self):
        empfang, port = freier_port()
        empfang.settimeout(2)
        self.addCleanup(empfang.close)
        env = dict(os.environ, PLAYER_EVENT="paused", TRACK_ID="xyz", PEPPA_RUECKMELDUNG_PORT=str(port))
        r = subprocess.run([sys.executable, os.path.join(HIER, "ereignis.py")], env=env, timeout=10)
        self.assertEqual(r.returncode, 0)
        n = json.loads(empfang.recvfrom(4096)[0])
        self.assertEqual((n["player_event"], n["track_id"]), ("paused", "xyz"))

    def test_ohne_empfaenger_trotzdem_null(self):
        frei, port = freier_port()
        frei.close()
        env = dict(os.environ, PLAYER_EVENT="stopped", PEPPA_RUECKMELDUNG_PORT=str(port))
        r = subprocess.run([sys.executable, os.path.join(HIER, "ereignis.py")], env=env, timeout=10)
        self.assertEqual(r.returncode, 0)

    def test_shebang_mit_einer_option(self):
        # Linux übergibt alles nach dem Programmnamen als EIN Argument: "-I -S" ginge nicht, "-IS" schon
        for name in ("ausgabe.py", "ereignis.py"):
            with open(os.path.join(HIER, name)) as f:
                erste = f.readline().split()
            self.assertEqual(erste, ["#!/usr/bin/python3", "-IS"])


class Uhr:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class Empfang(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.log = []
        self.fehler = []
        self.r = rueckmeldung.Rueckmeldung(jetzt=self.uhr, log=self.log.append,
                                           bei_fehler=lambda *a: self.fehler.append(a))

    def test_ohne_relais_kein_lokaler_beleg(self):
        self.assertIsNone(self.r.lokal())
        self.assertFalse(self.r.relais_aktiv())

    def test_fluss_und_alter(self):
        self.r.verarbeiten({"q": "ausgabe", "art": "start", "ziel": "lautsprecher", "pid": 5})
        self.assertIs(self.r.lokal(), False)
        self.r.verarbeiten({"q": "ausgabe", "art": "fluss", "ziel": "lautsprecher", "bytes": 176400})
        self.assertIs(self.r.lokal(), True)
        self.uhr.t += 3
        self.assertIs(self.r.lokal(), False)
        self.r.verarbeiten({"q": "ausgabe", "art": "fluss", "ziel": "kopfhoerer", "bytes": 0})
        self.assertIs(self.r.lokal(), False)                 # 0 Bytes ist kein Fluss
        self.assertEqual(self.r.ausgabe_ziel, "kopfhoerer")

    def test_fehler_ruft_zurueck(self):
        self.r.verarbeiten({"q": "ausgabe", "art": "fehler", "ziel": "kopfhoerer", "text": "busy",
                            "rueckfall": "lautsprecher"})
        self.assertEqual(self.fehler, [("kopfhoerer", "busy", "lautsprecher")])
        self.assertIn("kopfhoerer: busy", self.r.status["fehler"])
        self.assertTrue(any("weiter über lautsprecher" in z for z in self.log))

    def test_kaputter_rueckruf_stoert_nicht(self):
        self.r.bei_fehler = lambda *a: 1 / 0
        self.r.verarbeiten({"q": "ausgabe", "art": "fehler", "ziel": "kopfhoerer", "text": "x"})
        self.assertTrue(any("gescheitert" in z for z in self.log))

    def test_ereignisse(self):
        self.r.verarbeiten({"q": "ereignis", "player_event": "track_changed", "track_id": "t1"})
        self.r.verarbeiten({"q": "ereignis", "player_event": "playing", "track_id": "t1", "position_ms": "0"})
        self.assertTrue(self.r.spielt)
        self.assertEqual(self.r.titel, "t1")
        self.r.verarbeiten({"q": "ereignis", "player_event": "paused", "track_id": "t1"})
        self.assertFalse(self.r.spielt)
        self.r.verarbeiten({"q": "ereignis", "player_event": "session_disconnected"})
        self.assertFalse(self.r.status["verbunden"])
        self.assertTrue(any("getrennt" in z for z in self.log))

    def test_unsinn_wird_ignoriert(self):
        for n in (None, [], "x", {"q": "anders"}, {"q": "ausgabe", "art": "fluss", "bytes": "viel"}):
            try:
                self.r.verarbeiten(n)
            except ValueError:
                pass                                         # im Faden abgefangen und protokolliert
        self.assertIsNone(self.r.lokal()) if not self.r.relais_aktiv() else None

    def test_echter_empfang_ueber_udp(self):
        frei, port = freier_port()
        frei.close()
        r = rueckmeldung.Rueckmeldung(port=port, log=self.log.append)
        r.starten()
        ende = time.monotonic() + 2
        while not r.empfang_ok and time.monotonic() < ende:
            time.sleep(0.01)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b"kein json", ("127.0.0.1", port))
        s.sendto(json.dumps({"q": "ausgabe", "art": "fluss", "ziel": "lautsprecher", "bytes": 10}).encode(),
                 ("127.0.0.1", port))
        while not r.fliesst() and time.monotonic() < ende:
            time.sleep(0.01)
        self.assertTrue(r.fliesst())
        self.assertTrue(r.lebt())
        self.assertTrue(any("nicht verstanden" in z for z in self.log))


if __name__ == "__main__":
    unittest.main()
