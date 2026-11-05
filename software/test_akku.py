#!/usr/bin/env python3
"""Tests fuer akku.auswerten() mit Rohwerten wie am Geraet gemessen (ohne Hardware)."""
import unittest

import akku


def roh(volt, shunt_mv):
    bus = int(round(volt / 0.004)) << 3
    s = int(round(shunt_mv / 0.01)) & 0xFFFF
    return bus, s


class Auswerten(unittest.TestCase):
    def test_mit_netzteil_negativ_heisst_laden(self):
        # 05.11.: Netzteil steckt, 4,16 V, Rohwert negativ (wie 02.11.: -6,48 mV)
        a = akku.auswerten(*roh(4.16, -6.48))
        self.assertEqual(a["richtung"], "laedt")
        self.assertIsNone(a["prozent"])
        self.assertGreater(a["shunt_mv"], 0)

    def test_ohne_netzteil_positiv_heisst_akkubetrieb(self):
        a = akku.auswerten(*roh(4.04, 3.0))
        self.assertEqual(a["richtung"], "akku")
        self.assertIn(a["prozent"], (83, 84))

    def test_kaum_strom_hoch_ist_voll(self):
        self.assertEqual(akku.auswerten(*roh(4.18, 0.1))["richtung"], "voll")

    def test_kaum_strom_niedrig_bleibt_ruhend(self):
        self.assertEqual(akku.auswerten(*roh(3.80, -0.1))["richtung"], "ruhend")


if __name__ == "__main__":
    unittest.main()
