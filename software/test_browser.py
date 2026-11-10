"""Browser-Test der Eltern-Seite: echte Seite (peppa_web) mit simuliertem Kartenleser, bedient von Chrome.
Prüft den Ablauf "Karte bespielen" von der Link-Eingabe bis zum Etikett-Download, die Rückfrage bei belegten
Karten, die Kartenliste und die Seiten beider Bereiche (keine Fehler in der Konsole).
Braucht Playwright für Python und Chrome/Chromium; fehlt eins davon, wird der Test übersprungen.
Aufruf: cd software && python3 -m unittest -v test_browser
"""
import http.server
import io
import json
import os
import re
import shutil
import tempfile
import threading
import time
import unittest
from unittest import mock

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:                                        # ohne Playwright kein Browser-Test
    sync_playwright = None

import cover
import einstellungen
import karten
import peppa_web

CHROME = next((p for p in (os.environ.get("PEPPA_CHROME"), shutil.which("google-chrome"), shutil.which("chromium"),
                           "/usr/bin/google-chrome") if p and os.path.exists(p)), None)
PL = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
AL = "https://open.spotify.com/album/4aawyAB9vmqN3uQ7FjRGTy"


def bild(farbe):
    from PIL import Image, ImageDraw
    b = Image.new("RGB", (640, 640), farbe)
    ImageDraw.Draw(b).ellipse((120, 120, 520, 520), fill=(255, 255, 255))
    p = io.BytesIO()
    b.save(p, "JPEG")
    return p.getvalue()


@unittest.skipUnless(sync_playwright and CHROME, "Playwright oder Chrome fehlt")
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.patches = [mock.patch.object(einstellungen, "LAUF", cls.tmp.name),
                       mock.patch.object(peppa_web, "STATUS_DATEI", os.path.join(cls.tmp.name, "status.json")),
                       mock.patch.object(peppa_web, "BEDIENUNG_DATEI", os.path.join(cls.tmp.name, "bedienung.json")),
                       mock.patch.object(peppa_web, "TROCKEN", True),
                       mock.patch.dict(os.environ, {"HOME": cls.tmp.name}),
                       mock.patch.object(cover, "suchen", side_effect=cls.suchen)]
        for p in cls.patches:
            p.start()
        einstellungen._cache["mtime"] = None
        cls.karte = {"uid": None, "link": None}
        cls.laeuft = True
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), peppa_web.Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        threading.Thread(target=cls.spieler, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.pw = sync_playwright().start()
        cls.chrome = cls.pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

    @classmethod
    def tearDownClass(cls):
        cls.laeuft = False
        cls.chrome.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        for p in cls.patches:
            p.stop()
        cls.tmp.cleanup()

    @staticmethod
    def suchen(uri, holen=None, api=None):
        nr = uri.split(":")[2]
        h = sum(map(ord, nr))
        return {"titel": f"Peppa Lieder {nr[:4]}", "bild": cover._bild_normal(bild(((h * 37) % 200 + 30, (h * 91) % 180 + 40, 90))),
                "quelle": "oembed", "meldung": None}

    @classmethod
    def spieler(cls):
        """Ersatz für peppa_player: schreibt den Status und führt Bespielen-Aufträge wie der echte Player aus."""
        while cls.laeuft:
            try:
                with open(peppa_web.STATUS_DATEI, "w") as f:
                    json.dump({"zeit": time.time(), "karte": cls.karte["uid"], "link": cls.karte["link"], "spotify_bereit": True,
                               "akku": {"prozent": 64, "spannung": 3.9, "richtung": "akku", "prozent_ohne_netzteil": 64}}, f)
                a, uid = karten.auftrag_offen(), cls.karte["uid"]
                if a and uid:
                    vorher = cls.karte["link"] or karten.link_fuer_uid(uid)
                    if vorher and vorher.rstrip("/") != a["link"] and not a.get("ueberschreiben"):
                        m = cover.LINK_RE.search(vorher)
                        karten.auftrag_ergebnis(a, status="belegt", uid=uid, vorher_link=vorher, vorher_uri=f"spotify:{m.group(1)}:{m.group(2)}", meldung="belegt")
                    else:
                        cls.karte["link"] = a["link"]
                        karten.eintragen(uid, a["uri"], titel=(karten.meta_lesen(a["uri"]) or {}).get("titel"), auf_karte=True, typ="ntag")
                        karten.auftrag_ergebnis(a, status="fertig", uid=uid, auf_karte=True, typ="ntag", grund="ok", meldung="Der Link steht jetzt auf der Karte.")
            except Exception:
                pass
            time.sleep(0.2)

    def setUp(self):
        self.karte.update(uid=None, link=None)
        for uid in list(karten.laden()):
            karten.entfernen(uid)
        karten.auftrag_abbrechen()
        peppa_web._COVER_VERSUCH.clear()
        self.fehler = []
        self.ctx = self.chrome.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        self.addCleanup(self.ctx.close)
        self.pg = self.ctx.new_page()
        self.pg.on("console", lambda m: self.fehler.append(m.text) if m.type == "error" else None)
        self.pg.on("pageerror", lambda e: self.fehler.append(str(e)))
        self.pg.set_default_timeout(8000)

    def test_alle_seiten_laden_ohne_fehler(self):
        for seite in ("start", "karten", "karten/neu", "zeiten", "hilfe", "dev/ton", "dev/bedienung", "dev/etiketten", "dev/system"):
            self.pg.goto(f"{self.url}/#/{seite}")
            expect(self.pg.locator("#inhalt h1")).to_be_visible()
            time.sleep(0.4)
        self.assertEqual(self.fehler, [])

    def test_zwei_bereiche_und_navigation(self):
        pg = self.pg
        pg.goto(self.url + "/#/start")
        expect(pg.locator(".leiste a")).to_have_count(4)
        self.assertEqual(pg.locator(".leiste a").all_inner_texts(), ["Start", "Karten", "Zeiten", "Hilfe"])
        pg.click(".kopf .bereich a >> text=Entwickler")
        expect(pg.locator("#inhalt h1")).to_have_text("Ton")
        self.assertEqual(pg.locator(".leiste a").all_inner_texts(), ["Ton", "Bedienung", "Etiketten", "System"])
        expect(pg.locator(".dev-hinweis")).to_be_visible()
        pg.click(".kopf .bereich a >> text=Alltag")
        expect(pg.locator("#inhalt h1")).to_have_text("Peppa Box")

    def test_karte_bespielen_vom_link_bis_zum_etikett(self):
        pg = self.pg
        pg.goto(self.url + "/#/karten/neu")
        pg.fill("#link", PL + "?si=abc")                                        # Cover und Titel werden von allein gesucht
        expect(pg.locator("#pruefung .titel")).to_contain_text("Peppa Lieder 37i9")
        expect(pg.locator("#pruefung img.cover")).to_be_visible()
        expect(pg.locator("#pruefung img.etikettvorschau")).to_be_visible()
        self.assertEqual(pg.evaluate("() => new Promise(r => { const i = document.querySelector('#pruefung img.etikettvorschau'); "
                                     "const f = () => r(i.naturalWidth); i.complete ? f() : i.addEventListener('load', f); })"), 472)
        pg.click("#weiter")
        expect(pg.locator("#wtitel")).to_have_text("Lege jetzt die Karte auf das Kartenfach")
        self.karte.update(uid="04:11:22:33", link=None)                         # leere Karte kommt ins Fach
        expect(pg.locator(".erfolg h2").first).to_have_text("Fertig! Die Karte ist bespielt.")
        self.assertEqual(self.karte["link"], PL)
        with pg.expect_download() as d:
            pg.click("text=Etikett laden")
        self.assertTrue(d.value.suggested_filename.startswith("etikett-peppa-lieder"))
        expect(pg.locator(".kopf .chip-karte")).to_be_visible()                 # Cover der aufliegenden Karte in der Kopfzeile
        self.assertEqual(self.fehler, [])

    def test_belegte_karte_wird_erst_nach_rueckfrage_ueberschrieben(self):
        pg = self.pg
        self.karte.update(uid="04:AA:BB:CC", link=PL)
        pg.goto(self.url + "/#/karten/neu")
        pg.fill("#link", AL)
        expect(pg.locator("#weiter")).to_be_enabled()
        pg.click("#weiter")
        expect(pg.locator("h2", has_text="Auf dieser Karte ist schon etwas")).to_be_visible()
        self.assertEqual(self.karte["link"], PL, "ohne Bestätigung bleibt die Karte unverändert")
        pg.click("#ueber")
        expect(pg.locator(".erfolg h2").first).to_have_text("Fertig! Die Karte ist bespielt.")
        self.assertEqual(self.karte["link"], AL)

    def test_ungueltiger_link_zeigt_verstaendliche_meldung(self):
        pg = self.pg
        pg.goto(self.url + "/#/karten/neu")
        pg.fill("#link", "https://example.com/hallo")
        expect(pg.locator("#pruefung .hinweis.fehler")).to_be_visible()
        expect(pg.locator("#weiter")).to_be_disabled()

    def test_kartenliste_detail_und_etikettenbogen(self):
        pg = self.pg
        karten.eintragen("04:11:22:33", "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M", jetzt=1)
        karten.eintragen("04:AA:BB:CC", "spotify:album:4aawyAB9vmqN3uQ7FjRGTy", jetzt=2)
        pg.goto(self.url + "/#/karten")
        expect(pg.locator(".kachel")).to_have_count(2)
        with pg.expect_download() as d:
            pg.click("text=Bogen laden")
        self.assertEqual(d.value.suggested_filename, "peppa-box-etiketten.png")
        pg.locator(".kachel").first.click()
        pg.fill("#d-name", "Gute-Nacht-Lieder")
        pg.keyboard.press("Enter")
        pg.click("[data-a=zu]")
        expect(pg.locator(".kachel .t", has_text="Gute-Nacht-Lieder")).to_be_visible()
        pg.click("#gedruckt")
        expect(pg.locator("text=Alle Etiketten sind gedruckt")).to_be_visible()
        self.assertEqual(self.fehler, [])

    def test_start_zeigt_karte_im_fach_mit_titel_und_cover(self):
        pg = self.pg
        self.karte.update(uid="04:11:22:33", link=PL)
        pg.goto(self.url + "/#/start")
        expect(pg.locator("#hero .titel")).to_contain_text("Peppa Lieder 37i9")
        expect(pg.locator("#hero img.cover")).to_be_visible()
        self.karte.update(uid="19:81:15:20", link=None)                         # Karte ohne Playlist
        expect(pg.locator("#hero .titel")).to_have_text("Diese Karte ist noch leer")
        self.karte.update(uid=None, link=None)
        expect(pg.locator("#hero .titel")).to_have_text("Keine Karte im Fach")

    def test_keine_verbindung_zeigt_hinweis(self):
        pg = self.pg
        pg.goto(self.url + "/#/start")
        expect(pg.locator("#hero")).to_be_visible()
        self.ctx.set_offline(True)
        expect(pg.locator("#banner")).to_be_visible(timeout=6000)
        self.ctx.set_offline(False)
        expect(pg.locator("#banner")).to_be_hidden(timeout=6000)


if __name__ == "__main__":
    unittest.main()
