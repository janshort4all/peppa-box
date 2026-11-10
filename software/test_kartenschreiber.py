"""Tests: Link auf eine (simulierte) NFC-Karte schreiben. Ohne Hardware.
Aufruf: cd software && python3 -m unittest -v test_kartenschreiber
"""
import sys
import types
import unittest

import kartenschreiber
import ndef

LINK = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"


class FakeNtag:
    """Simulierte Typ-2-Karte: Seiten à 4 Byte, wie NTAG213 (45 Seiten, 144 Byte Nutzerbereich)."""

    def __init__(self, cc=(0xE1, 0x10, 0x12, 0x00), seiten=45, gesperrt=(), stumm=False, lesefehler_nach=None):
        self.seiten = [bytearray(4) for _ in range(seiten)]
        self.seiten[0][:] = bytes([0x04, 0xAA, 0xBB, 0xCC])
        self.seiten[3][:] = bytes(cc)
        self.seiten[4][:] = bytes([0x03, 0x00, 0xFE, 0x00])         # leere Nachricht ab Werk
        self.gesperrt, self.stumm = set(gesperrt), stumm
        self.geschrieben, self.lesefehler_nach, self.lesungen = [], lesefehler_nach, 0

    def lese16(self, seite):
        self.lesungen += 1
        if self.lesefehler_nach is not None and self.lesungen > self.lesefehler_nach:
            return None
        return bytes(b for i in range(4) for b in self.seiten[(seite + i) % len(self.seiten)])

    def schreibe4(self, seite, daten):
        self.geschrieben.append(seite)
        if self.stumm or seite in self.gesperrt or seite >= len(self.seiten):
            return False
        self.seiten[seite][:] = daten
        return True


class NdefBauen(unittest.TestCase):
    def test_spotify_link_mit_kuerzel_https(self):
        satz = ndef.uri_datensatz(LINK)
        self.assertEqual(satz[:4], bytes([0xD1, 0x01, len(satz) - 4, 0x55]))
        self.assertEqual(satz[4], 0x04)                           # "https://"
        self.assertEqual(satz[5:].decode(), LINK[len("https://"):])

    def test_rundreise(self):
        for link in (LINK, "spotify:playlist:abc", "http://www.x.de/a?b=ä"):
            tlv = ndef.tlv_fuer_link(link)
            self.assertEqual(tlv[0], 0x03)
            self.assertEqual(tlv[-1], 0xFE)
            self.assertEqual(ndef.uri_aus_ndef(ndef.ndef_aus_tlv(list(tlv))), link)

    def test_langer_link_ist_fehler(self):
        with self.assertRaises(ValueError):
            ndef.uri_datensatz("https://x.de/" + "a" * 300)


class Beschreiben(unittest.TestCase):
    def test_schreiben_und_lesen(self):
        k = FakeNtag()
        erg = kartenschreiber.ntag_beschreiben(k, LINK)
        self.assertTrue(erg["ok"], erg)
        self.assertEqual(kartenschreiber.link_lesen(k), LINK)
        self.assertEqual(erg["kapazitaet"], 144)

    def test_fasst_nur_den_nutzerbereich_an(self):
        k = FakeNtag()
        kartenschreiber.ntag_beschreiben(k, LINK)
        self.assertTrue(all(4 <= s < 4 + 144 // 4 for s in k.geschrieben), k.geschrieben)
        self.assertEqual(bytes(k.seiten[0]), bytes([0x04, 0xAA, 0xBB, 0xCC]))      # Nummer unverändert
        self.assertEqual(bytes(k.seiten[3]), bytes([0xE1, 0x10, 0x12, 0x00]))      # Capability Container unverändert

    def test_ueberschreibt_alten_link(self):
        k = FakeNtag()
        kartenschreiber.ntag_beschreiben(k, "https://open.spotify.com/album/" + "A" * 22)
        erg = kartenschreiber.ntag_beschreiben(k, "https://open.spotify.com/show/abc")
        self.assertTrue(erg["ok"])
        self.assertEqual(kartenschreiber.link_lesen(k), "https://open.spotify.com/show/abc")

    def test_karte_ohne_ndef_wird_nicht_beschrieben(self):
        for cc in ((0, 0, 0, 0), (0x00, 0x10, 0x12, 0x00), (0xFF, 0xFF, 0xFF, 0xFF)):
            k = FakeNtag(cc=cc)
            erg = kartenschreiber.ntag_beschreiben(k, LINK)
            self.assertFalse(erg["ok"])
            self.assertEqual(erg["grund"], "nicht_ndef")
            self.assertEqual(k.geschrieben, [], "darf nichts schreiben")

    def test_schreibgeschuetzte_karte(self):
        k = FakeNtag(cc=(0xE1, 0x10, 0x12, 0x0F))
        erg = kartenschreiber.ntag_beschreiben(k, LINK)
        self.assertEqual(erg["grund"], "schreibgeschuetzt")
        self.assertEqual(k.geschrieben, [])

    def test_seiten_gesperrt_ohne_ack(self):
        erg = kartenschreiber.ntag_beschreiben(FakeNtag(gesperrt={5}), LINK)
        self.assertEqual((erg["ok"], erg["grund"]), (False, "schreibfehler"))

    def test_karte_antwortet_nicht(self):
        self.assertEqual(kartenschreiber.ntag_beschreiben(FakeNtag(stumm=True), LINK)["grund"], "schreibfehler")

    def test_lesefehler_vorher_und_nachher(self):
        self.assertEqual(kartenschreiber.ntag_beschreiben(FakeNtag(lesefehler_nach=0), LINK)["grund"], "lesefehler")
        self.assertEqual(kartenschreiber.ntag_beschreiben(FakeNtag(lesefehler_nach=1), LINK)["grund"], "lesefehler")

    def test_pruefung_nach_dem_schreiben_entscheidet(self):
        """ACK vorhanden, aber die Karte behält die Daten nicht (z. B. Karte beim Schreiben bewegt)."""
        k = FakeNtag()
        original = k.schreibe4

        def zerstoert(seite, daten):
            original(seite, daten)
            if seite == 5:
                k.seiten[5][:] = bytes(4)
            return True
        k.schreibe4 = zerstoert
        self.assertEqual(kartenschreiber.ntag_beschreiben(k, LINK)["grund"], "pruefung")

    def test_zu_kleine_karte(self):
        k = FakeNtag(cc=(0xE1, 0x10, 0x06, 0x00))                  # Nutzerbereich 48 Byte
        erg = kartenschreiber.ntag_beschreiben(k, "https://open.spotify.com/playlist/" + "A" * 22 + "?si=" + "b" * 20)
        self.assertEqual(erg["grund"], "zu_gross")
        self.assertEqual(k.geschrieben, [])

    def test_ntag216_gross(self):
        k = FakeNtag(cc=(0xE1, 0x10, 0x6D, 0x00), seiten=231)
        self.assertTrue(kartenschreiber.ntag_beschreiben(k, LINK)["ok"])


class LeserRahmen(unittest.TestCase):
    """RC522.beschreiben/schreibe4 gegen einen gefälschten Funkweg: stimmen Befehl und Prüfsumme?"""

    def setUp(self):
        sys.modules.setdefault("spidev", types.ModuleType("spidev"))
        sys.modules.pop("rc522", None)
        import rc522
        self.rc522 = rc522
        self.karte = FakeNtag()
        self.rahmen = []
        leser = object.__new__(rc522.RC522)

        def funk(daten, bits=0):
            self.rahmen.append(list(daten))
            *nutz, c1, c2 = daten
            assert rc522.crc_a(nutz) == [c1, c2], "falsche Prüfsumme"
            if nutz[0] == 0xA2:
                return [0x0A] if self.karte.schreibe4(nutz[1], bytes(nutz[2:6])) else [0x00]
            if nutz[0] == 0x30:
                erg = self.karte.lese16(nutz[1])
                return list(erg) + [0, 0] if erg else None
            return None
        leser._transceive = funk
        leser._select = lambda: ([0x04, 0xAA, 0xBB, 0xCC], 0x00, [0x04, 0xAA, 0xBB, 0xCC])
        leser._halt = lambda: None
        self.leser = leser

    def tearDown(self):
        sys.modules.pop("rc522", None)

    def test_schreibbefehl_hat_richtigen_aufbau(self):
        self.assertTrue(self.leser.schreibe4(7, b"\x01\x02\x03\x04"))
        self.assertEqual(self.rahmen[0][:6], [0xA2, 7, 1, 2, 3, 4])
        self.assertEqual(len(self.rahmen[0]), 8)

    def test_nak_ist_kein_erfolg(self):
        self.karte.gesperrt = {7}
        self.assertFalse(self.leser.schreibe4(7, bytes(4)))

    def test_beschreiben_ganze_karte(self):
        erg = self.leser.beschreiben(LINK)
        self.assertTrue(erg["ok"], erg)
        self.assertEqual((erg["uid"], erg["typ"]), ("04:AA:BB:CC", "ntag"))
        self.assertEqual(kartenschreiber.link_lesen(self.karte), LINK)

    def test_classic_wird_nicht_beschrieben(self):
        self.leser._select = lambda: ([1, 2, 3, 4], 0x08, [1, 2, 3, 4])
        erg = self.leser.beschreiben(LINK)
        self.assertEqual((erg["ok"], erg["typ"], erg["grund"]), (False, "classic", "typ"))

    def test_keine_karte(self):
        self.leser._select = lambda: None
        self.assertEqual(self.leser.beschreiben(LINK)["grund"], "keine_karte")


if __name__ == "__main__":
    unittest.main()
