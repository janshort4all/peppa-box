"""Tests der Eltern-Seite (peppa_web.py) über echte HTTP-Anfragen an einen Server auf einem freien Port,
dazu die Prüfung der Bedien-Einstellungen. Ohne Hardware, sudo-Befehle im Probelauf.
Aufruf: cd software && python3 -m unittest -v test_web
"""
import http.server
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest import mock

import einstellungen
import peppa_web


class Einstellungen(unittest.TestCase):
    def test_standard_bedienung(self):
        b = einstellungen.bereinigen({}, einstellungen.STANDARD)["bedienung"]
        self.assertEqual(b["felder"], {"zurueck": 0, "play": 1, "vor": 2, "schlaf": 3})
        self.assertEqual((b["touch_schwelle"], b["touch_loslassen"]), (8, 4))

    def test_felder_tauschen_und_pruefen(self):
        b = einstellungen.bereinigen({"bedienung": {"felder": {"play": 3, "schlaf": 1}}}, einstellungen.STANDARD)
        self.assertEqual(b["bedienung"]["felder"]["schlaf"], 1)
        for falsch in ({"felder": {"play": 0}},                       # E0 doppelt
                       {"felder": {"pause": 1}}, {"felder": {"play": 7}}, {"touch_schwelle": 1},
                       {"drehknopf_schritt": 0}, {"klinke_eingesteckt_bei": "links"},
                       {"kopfhoerer_erkennung": "ja"}, {"unbekannt": 1}):
            with self.assertRaises(ValueError, msg=falsch):
                einstellungen.bereinigen({"bedienung": falsch}, einstellungen.STANDARD)

    def test_loslassen_unter_schwelle(self):
        b = einstellungen.bereinigen({"bedienung": {"touch_schwelle": 6, "touch_loslassen": 9}},
                                     einstellungen.STANDARD)["bedienung"]
        self.assertEqual((b["touch_schwelle"], b["touch_loslassen"]), (6, 3))

    def test_alte_datei_ohne_bedienung(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"HOME": d}):
            os.makedirs(os.path.join(d, ".config", "peppa-box"))
            with open(einstellungen.pfad(), "w") as f:
                json.dump({"auto_aus": {"an": True, "minuten": 30}}, f)
            einstellungen._cache["mtime"] = None
            cfg = einstellungen.laden()
            self.assertTrue(cfg["auto_aus"]["an"])
            self.assertEqual(cfg["bedienung"]["drehknopf_schritt"], 2)


class Seite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for ziel, name, wert in ((einstellungen, "LAUF", self.tmp.name),
                                 (peppa_web, "STATUS_DATEI", os.path.join(self.tmp.name, "peppa-box-status.json")),
                                 (peppa_web, "BEDIENUNG_DATEI", os.path.join(self.tmp.name, "peppa-box-bedienung.json")),
                                 (peppa_web, "TROCKEN", True)):
            p = mock.patch.object(ziel, name, wert)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.dict(os.environ, {"HOME": self.tmp.name})
        p.start()
        self.addCleanup(p.stop)
        einstellungen._cache["mtime"] = None
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), peppa_web.Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def holen(self, pfad):
        with urllib.request.urlopen(self.url + pfad, timeout=5) as r:
            return json.load(r)

    def senden(self, pfad, daten=None, kopf=True):
        body = json.dumps(daten).encode() if daten is not None else b""
        req = urllib.request.Request(self.url + pfad, data=body, method="POST",
                                     headers={"X-Peppa-Box": "1", "Content-Type": "application/json"} if kopf else {})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def player_status(self, **z):
        with open(peppa_web.STATUS_DATEI, "w") as f:
            json.dump(dict({"zeit": time.time(), "karte": None, "link": None, "spotify_bereit": True}, **z), f)

    def test_karte_mit_bedienung_und_leser(self):
        self.player_status(leser="Kartenleser nicht bereit: Version 0x00")
        with open(peppa_web.BEDIENUNG_DATEI, "w") as f:
            json.dump({"zeit": time.time(), "touch": {"ok": True, "beruehrt": ["play"]}}, f)
        k = self.holen("/api/karte")
        self.assertTrue(k["laeuft"])
        self.assertEqual(k["leser"], "Kartenleser nicht bereit: Version 0x00")
        self.assertTrue(k["bedienung"]["laeuft"])
        self.assertEqual(k["bedienung"]["touch"]["beruehrt"], ["play"])

    def test_bedienung_alt_gilt_als_aus_und_prueffenster_wird_gemeldet(self):
        with open(peppa_web.BEDIENUNG_DATEI, "w") as f:
            json.dump({"zeit": time.time() - 60}, f)
        self.assertFalse(self.holen("/api/bedienung")["laeuft"])
        self.assertLess(einstellungen.lauf_alter("seite-bedienung"), 5)

    def test_einstellungen_bedienung_speichern(self):
        st, erg = self.senden("/api/einstellungen", {"bedienung": {"touch_schwelle": 5, "felder": {"vor": 0, "zurueck": 2}}})
        self.assertTrue(erg["ok"], erg)
        self.assertEqual(einstellungen.laden()["bedienung"]["felder"]["zurueck"], 2)
        st, erg = self.senden("/api/einstellungen", {"bedienung": {"felder": {"vor": 1}}})
        self.assertFalse(erg["ok"])
        self.assertIn("genau einmal", erg["meldung"])

    def test_ansagen_liste_und_abspielen(self):
        a = self.holen("/api/ansagen")
        namen = [x["name"] for x in a["ansagen"]]
        self.assertIn("bereit", namen)
        self.assertEqual(next(x for x in a["ansagen"] if x["name"] == "bereit")["quelle"], "aufnahme")
        with mock.patch.object(peppa_web.toene, "spielen", return_value=True) as sp:
            st, erg = self.senden("/api/ansage", {"name": "akku_70"})
        self.assertTrue(erg["ok"])
        sp.assert_called_once()
        st, erg = self.senden("/api/ansage", {"name": "rm -rf"})
        self.assertFalse(erg["ok"])

    def test_ohne_kopfeintrag_verboten(self):
        st, erg = self.senden("/api/ansage", {"name": "bereit"}, kopf=False)
        self.assertEqual(st, 403)

    def test_akku_vom_player_bevorzugt(self):
        p = {"laeuft": True, "akku": {"spannung": 3.9, "prozent": 70, "richtung": "akku"}}
        with mock.patch.object(peppa_web.akku, "lesen") as lesen:
            self.assertEqual(peppa_web.akku_zustand(p)["prozent"], 70)
            lesen.assert_not_called()
            peppa_web.akku_zustand({"laeuft": False})
            lesen.assert_called_once()

    def test_seite_enthaelt_bedienung(self):
        with urllib.request.urlopen(self.url + "/", timeout=5) as r:
            html = r.read().decode()
        for teil in ("id=\"bfelder\"", "bedienungSpeichern", "ansagenLaden", "/api/bedienung"):
            self.assertIn(teil, html)


if __name__ == "__main__":
    unittest.main()
