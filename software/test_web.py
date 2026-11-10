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

import cover
import einstellungen
import karten
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
        peppa_web._COVER_VERSUCH.clear()
        # kein echtes Netz in den Tests: die Cover-Suche liefert nichts, außer ein Test setzt sie selbst
        p = mock.patch.object(peppa_web.cover, "suchen", return_value={"titel": None, "bild": None, "quelle": None,
                                                                         "meldung": "Zu diesem Link wurde kein Cover gefunden."})
        self.suchen = p.start()
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

    # ---- Karten, Cover, Etiketten

    PL = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
    LINK = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

    def bild(self, farbe=(200, 30, 30), format="PNG"):
        import io
        from PIL import Image
        puffer = io.BytesIO()
        Image.new("RGB", (400, 400), farbe).save(puffer, format)
        return puffer.getvalue()

    def cover_da(self, titel="Kinderlieder"):
        self.suchen.return_value = {"titel": titel, "bild": cover._bild_normal(self.bild()), "quelle": "oembed", "meldung": None}

    def roh(self, pfad, daten, kopf=True):
        req = urllib.request.Request(self.url + pfad, data=daten, method="POST",
                                     headers={"X-Peppa-Box": "1", "Content-Type": "image/png"} if kopf else {})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def datei(self, pfad):
        with urllib.request.urlopen(self.url + pfad, timeout=10) as r:
            return r.status, r.headers, r.read()

    def warten_bis(self, bedingung, s=3):
        ende = time.time() + s
        while time.time() < ende:
            if bedingung():
                return True
            time.sleep(0.02)
        return False

    def test_link_pruefen_findet_titel_und_cover(self):
        self.cover_da()
        st, erg = self.senden("/api/karten/pruefen", {"text": "Schau mal: " + self.LINK + "?si=abc"})
        self.assertTrue(erg["ok"], erg)
        self.assertEqual((erg["uri"], erg["titel"], erg["hat_cover"]), (self.PL, "Kinderlieder", True))
        self.assertTrue(erg["cover"].startswith("/cover/playlist_37i9dQZF1DXcBWIGoYBM5M.jpg"))
        s, kopf, daten = self.datei(erg["cover"])
        self.assertEqual((s, kopf["Content-Type"]), (200, "image/jpeg"))
        self.assertEqual(daten[:3], b"\xff\xd8\xff")

    def test_link_pruefen_unsinn_und_leer(self):
        for text in ("", "   ", "hallo", "https://example.com/x"):
            st, erg = self.senden("/api/karten/pruefen", {"text": text})
            self.assertFalse(erg["ok"], text)
            self.assertTrue(erg["meldung"])
        self.assertFalse(self.senden("/api/karten/pruefen", {"text": 5})[1]["ok"])

    def test_link_ohne_cover_ist_trotzdem_gueltig(self):
        st, erg = self.senden("/api/karten/pruefen", {"text": self.LINK})
        self.assertTrue(erg["ok"])
        self.assertFalse(erg["hat_cover"])
        self.assertIsNone(erg["cover"])

    def test_bespielen_stellt_auftrag_und_prueft_den_leser(self):
        st, erg = self.senden("/api/karten/bespielen", {"uri": self.PL})
        self.assertFalse(erg["ok"])
        self.assertIn("läuft gerade nicht", erg["meldung"])                  # Player aus
        self.player_status(leser="Kartenleser nicht bereit: Version 0x00")
        self.assertIn("Kartenleser nicht bereit", self.senden("/api/karten/bespielen", {"uri": self.PL})[1]["meldung"])
        self.player_status()
        self.assertFalse(self.senden("/api/karten/bespielen", {"uri": "spotify:playlist:x"})[1]["ok"])
        st, erg = self.senden("/api/karten/bespielen", {"uri": self.PL})
        self.assertTrue(erg["ok"], erg)
        self.assertEqual(erg["auftrag"]["status"], "wartet")
        self.assertEqual(self.holen("/api/karte")["auftrag"]["status"], "wartet")
        self.assertEqual(karten.auftrag_offen()["link"], self.LINK)
        self.senden("/api/karten/abbrechen", {})
        self.assertEqual(self.holen("/api/karte")["auftrag"]["status"], "keiner")

    def test_auftragsstand_enthaelt_titel_und_cover(self):
        alt = "spotify:album:4aawyAB9vmqN3uQ7FjRGTy"
        karten.meta_schreiben(self.PL, titel="Neue Lieder", bild=cover._bild_normal(self.bild()), quelle="oembed")
        karten.meta_schreiben(alt, titel="Alte Lieder")
        self.player_status()
        self.senden("/api/karten/bespielen", {"uri": self.PL})
        a = self.holen("/api/karte")["auftrag"]
        self.assertEqual((a["status"], a["titel"]), ("wartet", "Neue Lieder"))
        self.assertTrue(a["cover"].startswith("/cover/playlist_"))
        karten.auftrag_ergebnis(karten.auftrag_offen(), status="belegt", uid="04:AA:BB:CC", vorher_uri=alt,
                                vorher_link="https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy", meldung="belegt")
        a = self.holen("/api/karte")["auftrag"]
        self.assertEqual((a["status"], a["vorher_titel"], a["vorher_cover"]), ("belegt", "Alte Lieder", None))
        karten.auftrag_ergebnis(karten.auftrag_offen() or karten.auftrag_stellen(self.PL), status="fehler", vorher_uri="kaputt")
        self.assertEqual(self.holen("/api/karte")["auftrag"]["status"], "fehler")   # kaputte Adresse stört nicht

    def test_ueberschreiben_wird_weitergegeben(self):
        self.player_status()
        self.senden("/api/karten/bespielen", {"uri": self.PL, "ueberschreiben": True})
        self.assertTrue(karten.auftrag_offen()["ueberschreiben"])

    def test_karte_im_fach_wird_aufgenommen_und_zeigt_cover(self):
        self.cover_da("Peppa Wutz")
        self.player_status(karte="04:AA:BB:CC", link=self.LINK)
        k = self.holen("/api/karte")["kartendaten"]
        self.assertEqual((k["uid"], k["uri"], k["bekannt"]), ("04:AA:BB:CC", self.PL, True))
        self.assertTrue(self.warten_bis(lambda: (karten.meta_lesen(self.PL) or {}).get("hat_cover")))
        k = self.holen("/api/karte")["kartendaten"]
        self.assertEqual(k["titel"], "Peppa Wutz")
        self.assertTrue(k["cover"].startswith("/cover/"))
        self.assertEqual(karten.laden()["04:AA:BB:CC"]["uri"], self.PL)
        self.assertEqual(self.holen("/api/karten")["karten"][0]["titel"], "Peppa Wutz")

    def test_karte_ohne_link_nutzt_zuordnung_der_box(self):
        karten.eintragen("19:81:15:20", self.PL, titel="Gute Nacht")
        self.player_status(karte="19:81:15:20", link=None)
        k = self.holen("/api/karte")["kartendaten"]
        self.assertEqual((k["uri"], k["titel"], k["link_auf_karte"]), (self.PL, "Gute Nacht", False))

    def test_unbekannte_karte_ohne_link(self):
        self.player_status(karte="11:22:33:44", link=None)
        k = self.holen("/api/karte")["kartendaten"]
        self.assertEqual((k["bekannt"], k["uri"], k["cover"]), (False, None, None))
        self.assertEqual(karten.laden(), {})

    def test_ohne_karte_keine_kartendaten(self):
        self.player_status()
        self.assertIsNone(self.holen("/api/karte")["kartendaten"])

    def test_cover_suche_im_netz_wird_gebremst(self):
        self.player_status(karte="04:AA:BB:CC", link=self.LINK)
        self.holen("/api/karte")
        self.assertTrue(self.warten_bis(lambda: not peppa_web._COVER_LAEUFT))
        for _ in range(3):
            self.holen("/api/karte")
        self.assertEqual(self.suchen.call_count, 1, "nicht bei jeder Abfrage neu suchen")

    def test_kartenliste_umbenennen_entfernen_gedruckt(self):
        karten.eintragen("04:AA:BB:CC", self.PL, jetzt=100)
        karten.eintragen("04:DD:EE:FF", "spotify:album:4aawyAB9vmqN3uQ7FjRGTy", jetzt=200)
        erg = self.holen("/api/karten")
        self.assertEqual([k["uid"] for k in erg["karten"]], ["04:DD:EE:FF", "04:AA:BB:CC"])     # neueste zuerst
        self.assertEqual(erg["etikett"]["offen"], 2)
        self.assertEqual((erg["etikett"]["spalten"], erg["etikett"]["zeilen"], erg["etikett"]["plaetze"]), (2, 3, 6))
        self.assertEqual(erg["etikett"]["naechster_bogen"], ["04:AA:BB:CC", "04:DD:EE:FF"])     # älteste zuerst
        self.assertTrue(self.senden("/api/karten/umbenennen", {"uid": "04:AA:BB:CC", "titel": "  Schlaflieder "})[1]["ok"])
        self.assertTrue(self.senden("/api/karten/umbenennen", {"uid": "04aabbcc", "titel": "Lieder"})[1]["ok"])    # Kurzform
        self.assertEqual(karten.laden()["04:AA:BB:CC"]["titel"], "Lieder")
        self.assertFalse(self.senden("/api/karten/umbenennen", {"uid": "ZZ", "titel": "x"})[1]["ok"])
        self.assertFalse(self.senden("/api/karten/umbenennen", {"uid": "04:00:00:00", "titel": "x"})[1]["ok"])
        self.assertTrue(self.senden("/api/karten/gedruckt", {"uids": ["04:AA:BB:CC"]})[1]["ok"])
        self.assertEqual(self.holen("/api/karten")["etikett"]["offen"], 1)
        self.assertTrue(self.senden("/api/karten/gedruckt", {"uids": ["04:AA:BB:CC"], "wert": False})[1]["ok"])
        self.assertEqual(self.holen("/api/karten")["etikett"]["offen"], 2)
        self.assertTrue(self.senden("/api/karten/entfernen", {"uid": "04:AA:BB:CC"})[1]["ok"])
        self.assertEqual([k["uid"] for k in self.holen("/api/karten")["karten"]], ["04:DD:EE:FF"])
        self.assertFalse(self.senden("/api/karten/entfernen", {"uid": "04:AA:BB:CC"})[1]["ok"])

    def test_dieselbe_playlist_auf_zwei_karten_gibt_ein_etikett(self):
        karten.eintragen("04:AA:BB:CC", self.PL, jetzt=1)
        karten.eintragen("04:DD:EE:FF", self.PL, jetzt=2)
        self.assertEqual(self.holen("/api/karten")["etikett"]["offen"], 1)

    def test_etikett_einzeln_ist_40mm_png_mit_300dpi(self):
        import io
        from PIL import Image
        self.cover_da()
        karten.meta_schreiben(self.PL, titel="Kinderlieder", bild=cover._bild_normal(self.bild()), quelle="oembed")
        s, kopf, daten = self.datei("/etikett/playlist_37i9dQZF1DXcBWIGoYBM5M.png")
        self.assertEqual((s, kopf["Content-Type"]), (200, "image/png"))
        self.assertIsNone(kopf["Content-Disposition"])
        b = Image.open(io.BytesIO(daten))
        self.assertEqual(b.size, (472, 472))                                  # 40 mm bei 300 dpi
        self.assertAlmostEqual(b.info["dpi"][0], 300, delta=1)
        self.assertEqual(b.getpixel((0, 0))[3], 0, "Ecke ist durchsichtig (Freiform-Kontur)")
        self.assertEqual(b.getpixel((236, 236))[3], 255)
        s, kopf, _ = self.datei("/etikett/playlist_37i9dQZF1DXcBWIGoYBM5M.png?laden=1")
        self.assertEqual(kopf["Content-Disposition"], 'attachment; filename="etikett-kinderlieder.png"')

    def test_etikett_ohne_cover_wird_namensschild(self):
        import io
        from PIL import Image
        s, _, daten = self.datei("/etikett/playlist_37i9dQZF1DXcBWIGoYBM5M.png")
        self.assertEqual(Image.open(io.BytesIO(daten)).size, (472, 472))

    def test_bogen_mit_offenen_karten_und_testbogen(self):
        import io
        from PIL import Image
        karten.eintragen("04:AA:BB:CC", self.PL, jetzt=1)
        s, kopf, daten = self.datei("/etikett/bogen.png?laden=1")
        b = Image.open(io.BytesIO(daten))
        self.assertEqual(b.size, (1063, 1654))                                # 90 × 140 mm bei 300 dpi
        self.assertEqual(kopf["Content-Disposition"], 'attachment; filename="peppa-box-etiketten.png"')
        s, kopf, daten = self.datei("/etikett/testbogen.png")
        self.assertEqual(Image.open(io.BytesIO(daten)).size, (1063, 1654))

    def test_bogen_ohne_karten_und_unsinn(self):
        for pfad in ("/etikett/bogen.png", "/etikett/playlist_x.png", "/etikett/../zustand.png", "/etikett/a/b.png",
                     "/cover/playlist_37i9dQZF1DXcBWIGoYBM5M.jpg", "/cover/x.jpg", "/etikett/playlist_37i9dQZF1DXcBWIGoYBM5M.jpg"):
            with self.assertRaises(urllib.error.HTTPError, msg=pfad) as e:
                self.datei(pfad)
            self.assertEqual(e.exception.code, 404, pfad)

    def test_etikett_ohne_pillow_gibt_hinweis(self):
        with mock.patch.object(peppa_web.etikett, "verfuegbar", return_value=False):
            with self.assertRaises(urllib.error.HTTPError) as e:
                self.datei("/etikett/testbogen.png")
            self.assertEqual(e.exception.code, 503)
            self.assertIn("Pillow", json.load(e.exception)["meldung"])
            self.assertFalse(self.holen("/api/karten")["etikett"]["verfuegbar"])

    def test_eigenes_bild_hochladen_und_cover_neu(self):
        st, erg = self.roh("/api/cover/hochladen?s=playlist_37i9dQZF1DXcBWIGoYBM5M", self.bild((10, 120, 200)))
        self.assertTrue(erg["ok"], erg)
        self.assertTrue(erg["eigenes_bild"])
        self.assertTrue(erg["cover"].startswith("/cover/"))
        st, erg = self.roh("/api/cover/hochladen?s=playlist_37i9dQZF1DXcBWIGoYBM5M", b"das ist kein Bild")
        self.assertFalse(erg["ok"])
        self.assertIn("kein brauchbares Bild", erg["meldung"])
        self.assertFalse(self.roh("/api/cover/hochladen?s=playlist_x", self.bild())[1]["ok"])
        self.assertFalse(self.roh("/api/cover/hochladen", self.bild())[1]["ok"])
        self.assertEqual(self.roh("/api/cover/hochladen?s=playlist_37i9dQZF1DXcBWIGoYBM5M", self.bild(), kopf=False)[0], 403)
        # "Cover neu suchen" ersetzt auch das eigene Bild
        self.cover_da("Neu")
        st, erg = self.senden("/api/cover/neu", {"uri": self.PL})
        self.assertTrue(erg["ok"], erg)
        self.assertFalse(erg["eigenes_bild"])
        self.assertEqual(erg["titel"], "Neu")

    def test_titel_von_hand_eintragen(self):
        st, erg = self.senden("/api/cover/titel", {"schluessel": "playlist_37i9dQZF1DXcBWIGoYBM5M", "titel": "Folge 103"})
        self.assertTrue(erg["ok"], erg)
        self.assertEqual(erg["titel"], "Folge 103")
        self.assertFalse(self.senden("/api/cover/titel", {"schluessel": "playlist_37i9dQZF1DXcBWIGoYBM5M", "titel": " "})[1]["ok"])
        self.assertFalse(self.senden("/api/cover/titel", {"schluessel": "../x", "titel": "a"})[1]["ok"])
        self.assertFalse(self.senden("/api/cover/titel", {"titel": "a"})[1]["ok"])

    def test_zu_grosse_dateien_werden_abgelehnt(self):
        req = urllib.request.Request(self.url + "/api/cover/hochladen?s=playlist_37i9dQZF1DXcBWIGoYBM5M", data=b"x", method="POST",
                                     headers={"X-Peppa-Box": "1", "Content-Length": str(peppa_web.BILD_MAX + 1)})
        with self.assertRaises((urllib.error.HTTPError, ConnectionError)) as e:
            urllib.request.urlopen(req, timeout=5)
        if isinstance(e.exception, urllib.error.HTTPError):
            self.assertEqual(e.exception.code, 413)
        st, erg = self.senden("/api/karten/pruefen", {"text": "x" * 5000})
        self.assertEqual(st, 413)

    def test_neue_routen_brauchen_den_kopfeintrag(self):
        for pfad in ("/api/karten/pruefen", "/api/karten/bespielen", "/api/karten/abbrechen", "/api/karten/umbenennen",
                     "/api/karten/entfernen", "/api/karten/gedruckt", "/api/cover/neu"):
            self.assertEqual(self.senden(pfad, {}, kopf=False)[0], 403, pfad)

    def test_etiketten_einstellungen_werden_geprueft_und_wirken(self):
        st, erg = self.senden("/api/einstellungen", {"etikett": {"groesse_mm": 30}})
        self.assertTrue(erg["ok"], erg)
        self.assertEqual(self.holen("/api/karten")["etikett"]["groesse_mm"], 30)
        self.assertFalse(self.senden("/api/einstellungen", {"etikett": {"groesse_mm": 500}})[1]["ok"])

    # ---- Oberfläche: alle Dateien werden ausgeliefert, nichts Fremdes

    def test_oberflaeche_dateien_werden_ausgeliefert(self):
        erwartet = {"index.html": "text/html", "app.css": "text/css", "app.js": "text/javascript", "kern.js": "text/javascript",
                    "alltag.js": "text/javascript", "karten.js": "text/javascript", "entwickler.js": "text/javascript",
                    "klang.js": "text/javascript", "logo.png": "image/png", "favicon.png": "image/png",
                    "apple-touch-icon.png": "image/png", "icon-192.png": "image/png", "icon-512.png": "image/png",
                    "manifest.webmanifest": "application/manifest+json"}
        for name, typ in erwartet.items():
            s, kopf, daten = self.datei("/" + name)
            self.assertEqual(s, 200, name)
            self.assertTrue(kopf["Content-Type"].startswith(typ), name)
            self.assertGreater(len(daten), 100, name)
        s, kopf, daten = self.datei("/")
        self.assertIn(b"/app.js", daten)

    def test_alle_dateien_im_web_ordner_sind_erreichbar_und_verwiesen(self):
        """Jede Datei, auf die Seite oder Module verweisen, gibt es; jedes Modul wird irgendwo eingebunden."""
        import re
        web = peppa_web.WEB
        quelle = {}
        for n in os.listdir(web):
            if n.endswith((".js", ".html", ".css", ".webmanifest")):
                with open(os.path.join(web, n), encoding="utf-8") as f:
                    quelle[n] = f.read()
        for n, text in quelle.items():
            for ziel in re.findall(r"""(?:from|import\()\s*['"]\./([\w.-]+)['"]""", text):
                self.assertIn(ziel, os.listdir(web), f"{n} bindet {ziel} ein, die Datei fehlt")
            for ziel in re.findall(r"""(?:src|href)="/([\w.-]+)\"""", text):
                self.assertIn(ziel, os.listdir(web), f"{n} verweist auf /{ziel}, die Datei fehlt")
        module = [n for n in quelle if n.endswith(".js")]
        for n in module:
            if n not in ("app.js", "sw.js"):                                   # app.js lädt index.html, sw.js der Browser
                self.assertTrue(any(f"./{n}" in t for t in quelle.values()), f"{n} wird nirgends eingebunden")
        manifest = json.loads(quelle["manifest.webmanifest"])
        for ikone in manifest["icons"]:
            self.assertIn(ikone["src"].lstrip("/"), os.listdir(web))

    def test_keine_fremden_adressen_in_der_oberflaeche(self):
        """Kein CDN, keine Schriften oder Skripte aus dem Netz: Die Seite läuft im Heimnetz ohne Internet."""
        import re
        for n in os.listdir(peppa_web.WEB):
            if n.endswith((".js", ".html", ".css")):
                with open(os.path.join(peppa_web.WEB, n), encoding="utf-8") as f:
                    text = f.read()
                self.assertEqual(re.findall(r"https?://(?!open\.spotify\.com)[\w.-]+", text), [], n)

    def test_static_ordner_ausbruch_und_unbekannte_endungen(self):
        for pfad in ("/../peppa_web.py", "/%2e%2e/peppa_web.py", "/karten.py", "/web/app.js", "/app.js.map", "/etikett"):
            with self.assertRaises(urllib.error.HTTPError, msg=pfad) as e:
                self.datei(pfad)
            self.assertEqual(e.exception.code, 404, pfad)

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

    def test_diagnose_nur_lesen_mit_allen_abschnitten(self):
        self.player_status(problem=None, raspotify={"relais": True, "fliesst": True})
        aufrufe = []

        def befehl(args, zeit=15, cwd=None):
            aufrufe.append(args)
            if args[0] == "journalctl" and "-1" in args:
                return 0, "-- No entries --"
            return 0, f"Ausgabe von {args[0]}"
        with mock.patch.object(peppa_web, "befehl", befehl):
            d = self.holen("/api/diagnose")
        self.assertTrue(d["ok"])
        for teil in ("== Dienste ==", "== Tonweg (Helfer) ==", "== Player ==", '"fliesst": true',
                     "== Ausgabe gerade (Kernel) ==", "== Kopfhörer-Regler ==", "== Verstärker SD (P16) ==",
                     "== Protokoll seit dem Einschalten ==", "überstand den Neustart nicht"):
            self.assertIn(teil, d["text"])
        verboten = {"restart", "stop", "start", "reboot", "poweroff", "sset", "set"}
        for args in aufrufe:                                     # nur lesen
            self.assertFalse(verboten & set(args), args)
        journale = [a for a in aufrufe if a[0] == "journalctl"]
        self.assertTrue(all("raspotify" in a and "peppa-stille" in a for a in journale))

    def test_musik_neu_mit_ton_neustart_und_rueckfall(self):
        aufrufe = []

        def root(*args):
            aufrufe.append(args)
            return (1, "sudo: a password is required") if args[-1] == "neustart" and self.alt else (0, "")
        with mock.patch.object(peppa_web, "mit_root", root):
            self.alt = False
            self.assertTrue(peppa_web.musik_neu()["ok"])
            self.assertEqual(aufrufe, [(peppa_web.HELFER, "neustart"), (peppa_web.SYSTEMCTL, "restart", "peppa-player")])
            aufrufe.clear()
            self.alt = True                                      # alter Helfer: wie früher nur Raspotify
            self.assertTrue(peppa_web.musik_neu()["ok"])
            self.assertEqual(aufrufe[1:], [(peppa_web.SYSTEMCTL, "restart", "raspotify"),
                                           (peppa_web.SYSTEMCTL, "restart", "peppa-player")])

    def test_klang_lesen_und_setzen(self):
        with mock.patch.object(peppa_web.klang, "eingerichtet", return_value=True):
            k = self.holen("/api/klang")
        self.assertTrue(k["da"])
        self.assertEqual((k["baender"], len(k["namen"]), k["min"], k["max"]), ([0] * 10, 10, -24, 6))
        st, erg = self.senden("/api/klang", {"vorlage": "klein"})
        self.assertTrue(erg["ok"], erg)
        self.assertEqual(einstellungen.laden()["klang"]["baender"], peppa_web.klang.VORLAGEN["klein"])
        st, erg = self.senden("/api/klang", {"baender": [-3] * 10})
        self.assertTrue(erg["ok"])
        self.assertEqual(einstellungen.laden()["klang"]["baender"], [-3] * 10)
        st, erg = self.senden("/api/klang", {"baender": [50] * 10})
        self.assertFalse(erg["ok"])
        st, erg = self.senden("/api/klang", {"vorlage": "disco"})
        self.assertFalse(erg["ok"])
        self.assertEqual(einstellungen.laden()["klang"]["baender"], [-3] * 10)

    def test_klang_wird_angewendet(self):
        with mock.patch.object(peppa_web, "TROCKEN", False), \
                mock.patch.object(peppa_web.klang, "anwenden", return_value=False) as anwenden:
            erg = peppa_web.klang_setzen({"vorlage": "weich"})
        anwenden.assert_called_once()
        self.assertFalse(erg["ok"])
        self.assertIn("dienst_einrichten.sh", erg["meldung"])

    def test_tonausgabe_gilt_als_einrichtung(self):
        self.assertTrue({"software/ausgabe.py", "software/ereignis.py"} <= peppa_web.EINRICHTUNG)

    def test_belegung_mit_doppelbelegung_und_einstellungen(self):
        b = self.holen("/api/belegung")
        el = {e["id"]: e for e in b["elemente"]}
        self.assertEqual(list(el), ["zurueck", "play", "vor", "schlaf", "drehknopf", "taste", "karte", "klinke"])
        doppelt = {i: [g["wie"] for g in e["gesten"] if g["doppelt"]] for i, e in el.items()}
        self.assertEqual(doppelt["play"], ["2 s halten"])
        self.assertEqual(doppelt["schlaf"], ["5 s halten"])
        self.assertEqual(doppelt["taste"], ["2 s halten"])
        self.assertEqual(doppelt["vor"], ["halten (ab 0,7 s)"])
        self.assertEqual(doppelt["drehknopf"], [])
        self.assertIn("15 → 30 → 45 → 60 Min → aus", el["schlaf"]["gesten"][0]["was"])
        self.assertTrue(el["play"]["klick"] and not el["schlaf"]["klick"] and not el["taste"]["klick"])
        self.assertEqual(el["play"]["ort"], "Deckel, Touchfeld E1")
        self.assertIn("2 % je Raste", el["drehknopf"]["gesten"][0]["was"])
        # Einstellungen wirken: Felder getauscht, Klick aus, 5 % je Raste
        st, erg = self.senden("/api/einstellungen", {"bedienung": {"felder": {"play": 3, "schlaf": 1},
                                                                   "klick": 0, "drehknopf_schritt": 5}})
        self.assertTrue(erg["ok"], erg)
        el = {e["id"]: e for e in self.holen("/api/belegung")["elemente"]}
        self.assertEqual((el["play"]["ort"], el["schlaf"]["ort"]), ("Deckel, Touchfeld E3", "Deckel, Touchfeld E1"))
        self.assertFalse(any(e["klick"] for e in el.values()))
        self.assertIn("5 % je Raste", el["drehknopf"]["gesten"][0]["was"])

    def test_belegung_folgt_den_zeiten_der_gesten(self):
        import bedienung
        with mock.patch.object(bedienung, "VON_VORN_S", 3.0), mock.patch.object(bedienung, "LANG_SPRUNG_S", 0.5):
            el = {e["id"]: e for e in bedienung.belegung()["elemente"]}
        self.assertEqual(el["play"]["gesten"][1]["wie"], "3 s halten")
        self.assertEqual(el["zurueck"]["gesten"][1]["wie"], "halten (ab 0,5 s)")

    def test_seite_enthaelt_alle_bisherigen_funktionen(self):
        """Der Funktionsumfang der alten Seite ist in der neuen Oberfläche vollständig (Alltag + Entwickler)."""
        def modul(name):
            with urllib.request.urlopen(self.url + "/" + name, timeout=5) as r:
                return r.read().decode()
        alltag, entw, karten_js, kern, klang_js = (modul(n) for n in ("alltag.js", "entwickler.js", "karten.js", "kern.js", "klang.js"))
        alles = alltag + entw + karten_js + kern + klang_js
        for pfad in ("/api/lautstaerke", "/api/timer/starten", "/api/timer/abbrechen", "/api/ruhezeit/", "aussetzen", "wieder",
                     "/api/einstellungen", "/api/klang", "/api/bedienung", "/api/belegung", "/api/ansagen", "/api/ansage",
                     "/api/diagnose", "/api/meldungen", "/api/update/pruefen", "/api/update/starten", "/api/update/zurueck",
                     "/api/musik-neustart", "/api/neustart", "/api/ausschalten", "/api/karte", "/api/zustand",
                     "/api/karten/pruefen", "/api/karten/bespielen", "/api/karten/abbrechen", "/api/karten/umbenennen",
                     "/api/karten/entfernen", "/api/karten/gedruckt", "/api/cover/neu", "/api/cover/hochladen"):
            self.assertTrue(pfad in alles, pfad)                  # (kein assertIn: bei Fehler nicht den ganzen Text ausgeben)
        # Alltag: Start, Karten, Zeiten, Hilfe; Entwickler: Ton, Bedienung, Etiketten, System
        _, _, js = self.datei("/app.js")
        for seite in (b"'start'", b"'karten'", b"'karten/neu'", b"'zeiten'", b"'hilfe'", b"'dev/ton'", b"'dev/bedienung'",
                      b"'dev/etiketten'", b"'dev/system'"):
            self.assertIn(seite, js)
        # Teile, die es vorher gab
        for teil in ("Schlummer-Timer", "Ruhezeit", "Automatisch ausschalten", "Höchstlautstärke", "Equalizer", "Prüfen und einstellen",
                     "Was die Tasten können", "Ansagen anhören", "Letzte Meldungen der Box", "Diagnose", "Nach Updates suchen",
                     "Zurück zur vorherigen Version", "Musik neu starten", "Box neu starten", "Ausschalten"):
            self.assertTrue(teil in alles, teil)
        self.assertTrue("logo.png" in alles + modul("index.html") + modul("app.js"))


if __name__ == "__main__":
    unittest.main()
