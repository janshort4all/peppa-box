"""spotify.abspielen: Box nicht aktiv (404) oder Spotify erreicht sie nicht (5xx) -> erst übertragen, dann
noch einmal (Fall 12.11.2026: 502 trotz Raspotify-Neustarts, Auswählen in der App half)."""
import unittest
from unittest import mock

import spotify


class Start(unittest.TestCase):
    def lauf(self, antworten):
        aufrufe = []

        def api(method, path, body=None, params=None):
            aufrufe.append((method, path))
            if path == "/me/player":
                return 204, None
            return antworten.pop(0)
        with mock.patch.object(spotify, "api", api), mock.patch.object(spotify.time, "sleep"):
            erg = spotify.abspielen("D", "spotify:playlist:A", titel="spotify:track:t", position_ms=5000)
        return erg, aufrufe

    def test_502_erst_uebertragen_dann_spielen(self):
        erg, aufrufe = self.lauf([(502, {"error": {"status": 502}}), (204, None)])
        self.assertEqual(erg[0], 204)
        self.assertEqual(aufrufe, [("PUT", "/me/player/play"), ("PUT", "/me/player"), ("PUT", "/me/player/play")])

    def test_404_wie_bisher(self):
        erg, aufrufe = self.lauf([(404, None), (204, None)])
        self.assertEqual(erg[0], 204)
        self.assertIn(("PUT", "/me/player"), aufrufe)

    def test_ok_ohne_uebertragen(self):
        erg, aufrufe = self.lauf([(204, None)])
        self.assertEqual(aufrufe, [("PUT", "/me/player/play")])

    def test_bleibt_502_meldet_502(self):
        erg, _ = self.lauf([(502, {}), (502, {"error": {"status": 502}})])
        self.assertEqual(erg[0], 502)

    def test_400_wird_nicht_uebertragen(self):
        erg, aufrufe = self.lauf([(400, {})])
        self.assertEqual(aufrufe, [("PUT", "/me/player/play")])


if __name__ == "__main__":
    unittest.main()
