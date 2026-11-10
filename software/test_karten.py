"""Tests: Kartenverwaltung, Cover-Suche und Etiketten. Ohne Internet (Netzzugriffe sind nachgebildet).
Aufruf: cd software && python3 -m unittest -v test_karten
"""
import io
import json
import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

from PIL import Image

import cover
import einstellungen
import etikett
import karten

PL = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
PL_LINK = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
AL = "spotify:album:4aawyAB9vmqN3uQ7FjRGTy"


def png(breite=300, hoehe=300, farbe=(200, 30, 30)):
    b = io.BytesIO()
    Image.new("RGB", (breite, hoehe), farbe).save(b, "PNG")
    return b.getvalue()


class Netz:
    """Nachgebildetes Netz: {url-Anfang: (status, inhalt)}; merkt sich alle Aufrufe."""

    def __init__(self, antworten):
        self.antworten, self.aufrufe = antworten, []

    def __call__(self, url, max_bytes=0, zeit=0):
        self.aufrufe.append(url)
        for anfang, (status, inhalt) in self.antworten.items():
            if url.startswith(anfang):
                return status, inhalt, url
        return 0, b"", url


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for p in (mock.patch.dict(os.environ, {"HOME": self.tmp.name}),
                  mock.patch.object(einstellungen, "LAUF", self.tmp.name)):
            p.start()
            self.addCleanup(p.stop)
        karten._cache["mtime"] = None


class Adressen(unittest.TestCase):
    def test_formen(self):
        for text, soll in (
            ("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc", PL),
            ("open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M", PL),
            (PL, PL),
            ("spotify:user:jan:playlist:37i9dQZF1DXcBWIGoYBM5M", PL),
            ("Hör mal: https://open.spotify.com/intl-de/album/4aawyAB9vmqN3uQ7FjRGTy?si=x ok", AL),
        ):
            self.assertEqual(cover.adresse_aus_text(text), soll, text)

    def test_fehler_sind_verstaendlich(self):
        for text in ("", "hallo", "https://example.com/playlist/abc", "https://open.spotify.com/user/abc"):
            with self.assertRaises(ValueError) as f:
                cover.adresse_aus_text(text)
            self.assertIn("Spotify", str(f.exception))

    def test_kurzlink_wird_aufgeloest(self):
        netz = Netz({"https://spotify.link/abc": (200, b"")})
        netz.antworten = {}

        def holen(url, max_bytes=0, zeit=0):
            return 200, b"", "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=1"
        self.assertEqual(cover.adresse_aus_text("https://spotify.link/Ab_1-x", holen), PL)

    def test_schluessel_und_nummern(self):
        self.assertEqual(karten.schluessel(PL), "playlist_37i9dQZF1DXcBWIGoYBM5M")
        self.assertEqual(karten.uri_aus_schluessel("album_4aawyAB9vmqN3uQ7FjRGTy"), AL)
        self.assertEqual(karten.uid_aus_url("19811520"), "19:81:15:20")
        self.assertEqual(karten.uid_zu_url("04:AA:bb:CC"), "04aabbcc")
        for falsch in ("zz", "123", "../etc", "1981152"):
            with self.assertRaises(ValueError):
                karten.uid_aus_url(falsch)
        with self.assertRaises(ValueError):
            karten.uri_aus_schluessel("../../x")


class Cover(Basis):
    def test_oembed_liefert_bild_und_titel(self):
        netz = Netz({"https://open.spotify.com/oembed": (200, json.dumps(
            {"title": "Peppa Wutz | Spotify", "thumbnail_url": "https://i.scdn.co/image/abc"}).encode()),
            "https://i.scdn.co/image/abc": (200, png())})
        erg = cover.suchen(PL, netz)
        self.assertEqual((erg["titel"], erg["quelle"]), ("Peppa Wutz", "oembed"))
        self.assertTrue(erg["bild"].startswith(b"\xff\xd8"))            # als JPEG gespeichert
        self.assertIsNone(erg["meldung"])

    def test_albumbild_in_640(self):
        netz = Netz({"https://open.spotify.com/oembed": (200, json.dumps(
            {"title": "X", "thumbnail_url": "https://i.scdn.co/image/ab67616d00001e02ff"}).encode()),
            "https://i.scdn.co/image/ab67616d0000b273ff": (200, png(640, 640))})
        erg = cover.suchen(AL, netz)
        self.assertEqual(Image.open(io.BytesIO(erg["bild"])).size, (640, 640))

    def test_grosses_bild_nicht_da_nimmt_das_kleine(self):
        netz = Netz({"https://open.spotify.com/oembed": (200, json.dumps(
            {"title": "X", "thumbnail_url": "https://i.scdn.co/image/ab67616d00001e02ff"}).encode()),
            "https://i.scdn.co/image/ab67616d00001e02ff": (200, png(300, 300))})
        self.assertEqual(Image.open(io.BytesIO(cover.suchen(AL, netz)["bild"])).size, (300, 300))

    def test_oembed_ohne_bild_dann_seite(self):
        seite = ('<html><head><meta property="og:title" content="Kinderlieder &amp; mehr | Spotify">'
                 '<meta property="og:image" content="https://i.scdn.co/image/seite1"></head></html>').encode()
        netz = Netz({"https://open.spotify.com/oembed": (200, json.dumps({"title": "Kinderlieder & mehr"}).encode()),
                     "https://open.spotify.com/playlist/": (200, seite),
                     "https://i.scdn.co/image/seite1": (200, png())})
        erg = cover.suchen(PL, netz)
        self.assertEqual((erg["quelle"], erg["titel"]), ("seite", "Kinderlieder & mehr"))

    def test_oembed_kaputt_dann_web_api(self):
        netz = Netz({"https://i.scdn.co/image/api1": (200, png())})
        api = mock.Mock(return_value=(200, {"name": "Aus der API", "images": [{"url": "https://i.scdn.co/image/api1"}]}))
        erg = cover.suchen(PL, netz, api)
        self.assertEqual((erg["quelle"], erg["titel"]), ("api", "Aus der API"))
        api.assert_called_once_with("GET", "/playlists/37i9dQZF1DXcBWIGoYBM5M")

    def test_nichts_gefunden_ist_kein_absturz(self):
        api = mock.Mock(side_effect=RuntimeError("keine Anmeldung"))
        erg = cover.suchen(PL, Netz({}), api)
        self.assertIsNone(erg["bild"])
        self.assertIn("kein Cover", erg["meldung"])

    def test_private_playlist_meldung_ist_verstaendlich(self):
        netz = Netz({"https://open.spotify.com/": (404, b"")})
        erg = cover.suchen(PL, netz, mock.Mock(return_value=(404, {})))
        self.assertIsNone(erg["bild"])
        self.assertIn("privat", erg["meldung"])
        self.assertIn("oEmbed 404", erg["meldung"])

    def test_link_mit_zugangsschluessel_wird_zusaetzlich_versucht(self):
        link = PL_LINK + "?si=abc&pt=geheim123"
        self.assertEqual(cover.original_link("Schau: " + link + " ok"), link)
        self.assertIsNone(cover.original_link(PL_LINK))
        netz = Netz({"https://open.spotify.com/oembed?url=" + urllib.parse.quote(link, safe=""): (200, json.dumps(
                        {"title": "Privat", "thumbnail_url": "https://i.scdn.co/image/p1"}).encode()),
                     "https://open.spotify.com/": (404, b""),
                     "https://i.scdn.co/image/p1": (200, png())})
        self.assertIsNone(cover.suchen(PL, netz, mock.Mock(return_value=(404, {})))["bild"])        # ohne Schlüssel: nichts
        erg = cover.suchen(PL, netz, mock.Mock(return_value=(404, {})), original=link)
        self.assertEqual((erg["titel"], erg["quelle"]), ("Privat", "oembed"))
        self.assertIsNotNone(erg["bild"])

    def test_titel_von_hand(self):
        self.assertFalse(cover.titel_setzen(PL, "   ")["ok"])
        erg = cover.titel_setzen(PL, "  Folge 103:   SOS im Bike-Park ")
        self.assertEqual(erg["titel"], "Folge 103: SOS im Bike-Park")
        self.assertEqual(karten.meta_lesen(PL)["titel"], "Folge 103: SOS im Bike-Park")

    def test_kein_bild_unter_der_bildadresse(self):
        netz = Netz({"https://open.spotify.com/oembed": (200, json.dumps(
            {"title": "X", "thumbnail_url": "https://i.scdn.co/image/zz"}).encode()),
            "https://i.scdn.co/image/zz": (200, b"<html>kein Bild</html>")})
        erg = cover.suchen(PL, netz, mock.Mock(side_effect=RuntimeError("x")))
        self.assertIsNone(erg["bild"])
        self.assertEqual(erg["titel"], "X")

    def test_nachschlagen_speichert_und_nutzt_den_speicher(self):
        netz = Netz({"https://open.spotify.com/oembed": (200, json.dumps(
            {"title": "Peppa", "thumbnail_url": "https://i.scdn.co/image/abc"}).encode()),
            "https://i.scdn.co/image/abc": (200, png())})
        erg = cover.aufloesen("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=1", holen=netz)
        self.assertTrue(erg["ok"] and erg["hat_cover"])
        self.assertEqual(erg["titel"], "Peppa")
        self.assertTrue(karten.cover_bytes(PL).startswith(b"\xff\xd8"))
        n = len(netz.aufrufe)
        erg2 = cover.aufloesen(PL, holen=netz)
        self.assertEqual(len(netz.aufrufe), n, "zweites Mal darf nicht ins Netz")
        self.assertTrue(erg2["hat_cover"])

    def test_eigenes_bild_bleibt_bei_neuer_suche_aber_nicht_bei_neu(self):
        netz = Netz({"https://open.spotify.com/oembed": (200, json.dumps(
            {"title": "Peppa", "thumbnail_url": "https://i.scdn.co/image/abc"}).encode()),
            "https://i.scdn.co/image/abc": (200, png(farbe=(0, 255, 0)))})
        self.assertTrue(cover.eigenes_bild(PL, png(farbe=(0, 0, 255)))["eigenes_bild"])
        eigen = karten.cover_bytes(PL)
        cover.nachschlagen(PL, holen=netz)                              # Titel fehlt noch -> sucht, überschreibt Bild nicht
        self.assertEqual(karten.cover_bytes(PL), eigen)
        erg = cover.nachschlagen(PL, neu=True, holen=netz)
        self.assertNotEqual(karten.cover_bytes(PL), eigen)
        self.assertFalse(erg["eigenes_bild"])

    def test_eigenes_bild_muss_ein_bild_sein(self):
        self.assertFalse(cover.eigenes_bild(PL, b"kein bild")["ok"])

    def test_ohne_netz_kein_absturz(self):
        erg = cover.aufloesen(PL, holen=Netz({}), api=mock.Mock(side_effect=RuntimeError("x")))
        self.assertTrue(erg["ok"])
        self.assertFalse(erg["hat_cover"])
        self.assertTrue(erg["meldung"])


class Verwaltung(Basis):
    def test_eintragen_und_nachschlagen(self):
        self.assertIsNone(karten.link_fuer_uid("04:AA:BB:CC"))
        karten.eintragen("04:AA:BB:CC", PL, titel="Peppa", auf_karte=True, typ="ntag", jetzt=1000)
        self.assertEqual(karten.link_fuer_uid("04:AA:BB:CC"), "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
        k = karten.liste()[0]
        self.assertEqual((k["titel"], k["id"], k["typ"], k["auf_karte"], k["gedruckt"]),
                         ("Peppa", "04aabbcc", "playlist", True, False))

    def test_gedruckt_gilt_nur_fuer_dieselbe_adresse(self):
        karten.eintragen("04:AA:BB:CC", PL)
        karten.gedruckt_setzen(["04:AA:BB:CC"], True)
        karten.eintragen("04:AA:BB:CC", PL, titel="neu")
        self.assertTrue(karten.liste()[0]["gedruckt"])
        karten.eintragen("04:AA:BB:CC", AL)
        self.assertFalse(karten.liste()[0]["gedruckt"], "neue Playlist braucht ein neues Etikett")

    def test_umbenennen_entfernen(self):
        karten.eintragen("04:AA:BB:CC", PL)
        self.assertEqual(karten.liste()[0]["titel"], "Ohne Namen")
        self.assertTrue(karten.umbenennen("04:AA:BB:CC", "  Gute Nacht  "))
        self.assertEqual(karten.liste()[0]["titel"], "Gute Nacht")
        self.assertTrue(karten.umbenennen("04:AA:BB:CC", ""))
        self.assertEqual(karten.liste()[0]["titel"], "Ohne Namen")
        self.assertFalse(karten.umbenennen("FF:FF:FF:FF", "x"))
        self.assertTrue(karten.entfernen("04:AA:BB:CC"))
        self.assertFalse(karten.entfernen("04:AA:BB:CC"))
        self.assertEqual(karten.liste(), [])

    def test_titel_aus_cover_speicher(self):
        karten.meta_schreiben(PL, titel="Aus dem Netz", bild=png(), quelle="oembed")
        karten.eintragen("04:AA:BB:CC", PL)
        k = karten.liste()[0]
        self.assertEqual((k["titel"], k["hat_cover"], k["eigener_titel"]), ("Aus dem Netz", True, False))

    def test_kaputte_datei_ist_leere_liste(self):
        os.makedirs(karten.ordner())
        with open(karten._datei(), "w") as f:
            f.write("{kaputt")
        self.assertEqual(karten.laden(), {})
        karten.eintragen("04:AA:BB:CC", PL)                              # und lässt sich wieder beschreiben
        self.assertEqual(len(karten.liste()), 1)

    def test_eintrag_mit_unsinn_wird_ignoriert(self):
        os.makedirs(karten.ordner())
        with open(karten._datei(), "w") as f:
            json.dump({"karten": {"AA:BB:CC:DD": {"uri": "../../etc/passwd"}, "04:AA:BB:CC": {"uri": PL}}}, f)
        self.assertEqual(list(karten.laden()), ["04:AA:BB:CC"])

    def test_datei_nur_fuer_den_benutzer(self):
        karten.eintragen("04:AA:BB:CC", PL)
        self.assertTrue(os.path.isfile(karten._datei()))
        self.assertEqual(os.stat(karten.ordner()).st_mode & 0o077, 0)


class Auftrag(Basis):
    def test_ablauf(self):
        self.assertEqual(karten.auftrag_status()["status"], "keiner")
        self.assertIsNone(karten.auftrag_offen())
        a = karten.auftrag_stellen(PL, jetzt=1000)
        self.assertEqual(karten.auftrag_offen(1010)["id"], a["id"])
        self.assertEqual(karten.auftrag_status(1010)["status"], "wartet")
        karten.auftrag_ergebnis(a, status="fertig", uid="04:AA:BB:CC", meldung="ok")
        self.assertIsNone(karten.auftrag_offen(1010), "erledigter Auftrag wird nicht wiederholt")
        self.assertEqual(karten.auftrag_status(1010)["status"], "fertig")

    def test_abgelaufen(self):
        karten.auftrag_stellen(PL, jetzt=1000)
        self.assertIsNone(karten.auftrag_offen(1000 + karten.AUFTRAG_S + 1))
        self.assertEqual(karten.auftrag_status(1000 + karten.AUFTRAG_S + 1)["status"], "abgelaufen")

    def test_neuer_auftrag_loescht_altes_ergebnis(self):
        a = karten.auftrag_stellen(PL)
        karten.auftrag_ergebnis(a, status="fehler")
        b = karten.auftrag_stellen(AL)
        self.assertNotEqual(a["id"], b["id"])
        self.assertEqual(karten.auftrag_status()["status"], "wartet")

    def test_abbrechen(self):
        karten.auftrag_stellen(PL)
        karten.auftrag_abbrechen()
        self.assertEqual(karten.auftrag_status()["status"], "keiner")

    def test_falsche_adresse(self):
        with self.assertRaises(ValueError):
            karten.auftrag_stellen("https://x.de")


class EtikettBild(unittest.TestCase):
    E = einstellungen.STANDARD["etikett"]

    def test_groesse_40_mm_bei_300_dpi(self):
        b = etikett.etikett(png(640, 400), "Peppa", self.E)
        self.assertEqual(b.size, (472, 472))                              # 40 mm bei 300 dpi
        p = etikett.png_bytes(b)
        bild = Image.open(io.BytesIO(p))
        self.assertEqual(round(bild.info["dpi"][0]), 300)

    def test_ecken_transparent_mitte_deckend_rand_weiss(self):
        b = etikett.etikett(png(farbe=(200, 30, 30)), "x", self.E)
        self.assertEqual(b.getpixel((0, 0))[3], 0)                       # Ecke frei
        self.assertEqual(b.getpixel((236, 236)), (200, 30, 30, 255))     # Mitte = Cover
        self.assertEqual(b.getpixel((236, 2)), (255, 255, 255, 255))     # Weißrand oben
        self.assertEqual(b.getpixel((2, 236)), (255, 255, 255, 255))

    def test_ohne_weissrand(self):
        e = dict(self.E, weiss_mm=0)
        b = etikett.etikett(png(farbe=(200, 30, 30)), "x", e)
        self.assertEqual(b.getpixel((236, 2)), (200, 30, 30, 255))
        self.assertEqual(b.getpixel((0, 0))[3], 0)

    def test_ohne_cover_namensschild(self):
        b = etikett.etikett(None, "Lieder zum Einschlafen", self.E)
        self.assertEqual(b.size, (472, 472))
        self.assertEqual(b.getpixel((30, 236))[:3], (232, 121, 43))     # orange Fläche
        schluesselfarben = {b.getpixel((x, y))[:3] for x in range(100, 380, 7) for y in range(260, 440, 5)}
        self.assertIn((251, 246, 239), schluesselfarben, "Titel in Beige sichtbar")

    def test_kaputtes_cover_wird_namensschild(self):
        b = etikett.etikett(b"kaputt", "Titel", self.E)
        self.assertEqual(b.getpixel((30, 236))[:3], (232, 121, 43))

    def test_sehr_langer_titel_passt(self):
        etikett.etikett(None, "Ein ganz furchtbar langer Titel " * 8, self.E)

    def test_bogen_90_x_140(self):
        e = self.E
        self.assertEqual(etikett.plaetze(e), (2, 3))
        stuecke = [etikett.etikett(None, str(i), e) for i in range(6)]
        b = etikett.bogen(stuecke, e)
        self.assertEqual(b.size, (1063, 1654))                           # 90 × 140 mm bei 300 dpi
        with self.assertRaises(ValueError):
            etikett.bogen(stuecke + [stuecke[0]], e)

    def test_bogen_je_nach_einstellung(self):
        self.assertEqual(etikett.plaetze(dict(self.E, rand_mm=5, abstand_mm=5)), (1, 3))
        self.assertEqual(etikett.plaetze(dict(self.E, groesse_mm=60)), (1, 2))

    def test_testbogen(self):
        self.assertEqual(etikett.testbogen(self.E).size, (1063, 1654))

    def test_andere_groesse(self):
        self.assertEqual(etikett.etikett(None, "x", dict(self.E, groesse_mm=30)).size, (354, 354))


class EinstellungenEtikett(unittest.TestCase):
    def test_standard_ist_40_mm(self):
        self.assertEqual(einstellungen.STANDARD["etikett"]["groesse_mm"], 40)

    def test_pruefen(self):
        e = einstellungen.bereinigen({"etikett": {"groesse_mm": 38, "weiss_mm": 0.8}}, einstellungen.STANDARD)["etikett"]
        self.assertEqual((e["groesse_mm"], e["weiss_mm"]), (38, 0.8))
        for falsch in ({"groesse_mm": 5}, {"groesse_mm": 85}, {"x": 1}, {"ecke_mm": 25}, {"weiss_mm": "a"},
                       {"groesse_mm": True}, {"rand_mm": 30}):
            with self.assertRaises(ValueError, msg=falsch):
                einstellungen.bereinigen({"etikett": falsch}, einstellungen.STANDARD)


if __name__ == "__main__":
    unittest.main()
