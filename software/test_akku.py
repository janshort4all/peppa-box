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



class Wache(unittest.TestCase):
    def setUp(self):
        self.gesagt, self.aus, self.werte = [], [], []
        self.w = akku.Akkuwache(lesen=lambda: self.werte.pop(0), ansage=self.gesagt.append,
                                ausschalten=lambda g, a: self.aus.append((g, a)), log=lambda t: None)

    def messung(self, volt, richtung="akku"):
        p = None if richtung == "laedt" else akku.prozent(volt)
        return {"spannung": volt, "prozent": p, "richtung": richtung, "shunt_mv": 3.0}

    def lauf(self, *werte):
        self.werte.extend(werte)
        t = 0
        while self.werte:
            self.w.tick(t)
            t += akku.Akkuwache.ABSTAND_S

    def test_gelesen_alle_2_s_ausgewertet_alle_15_s(self):
        self.werte = [self.messung(3.9)] * 20
        self.w.tick(0)
        self.w.tick(1.9)
        self.assertEqual(len(self.werte), 19)
        self.w.tick(2)
        self.assertEqual(len(self.werte), 18)
        # die Auswertung (Warnung/Aus) läuft weiter nur alle 15 s: Messungen dazwischen zählen nicht
        ausgewertet = []
        self.w.verarbeiten = lambda w, t: ausgewertet.append(t)
        for t in range(4, 31, 2):
            self.w.tick(t)
        self.assertEqual(ausgewertet, [16])                              # erster 2-s-Takt ab 15 s

    def test_warnung_einmal_und_nach_laden_wieder(self):
        self.lauf(self.messung(3.6), self.messung(3.49), self.messung(3.45), self.messung(3.44))
        self.assertEqual(self.gesagt, ["akku_schwach"])
        self.lauf(self.messung(4.0, "laedt"), self.messung(3.48))
        self.assertEqual(self.gesagt, ["akku_schwach", "akku_schwach"])
        self.assertEqual(self.aus, [])

    def test_leer_nach_drei_messungen_aus(self):
        self.lauf(self.messung(3.29), self.messung(3.31), self.messung(3.29), self.messung(3.28))
        self.assertEqual(self.aus, [])                                     # Unterbrechung: zählt neu
        self.lauf(self.messung(3.27))
        self.assertEqual(self.aus, [("Akku leer", "akku_leer")])
        self.lauf(self.messung(3.2), self.messung(3.2))
        self.assertEqual(len(self.aus), 1)                                 # nur einmal

    def test_beim_laden_kein_aus_und_fehler_behalten_letzten_wert(self):
        self.lauf(*[self.messung(3.2, "laedt")] * 5)
        self.assertEqual(self.aus, [])
        self.lauf(self.messung(3.8), {"fehler": "Akku-Chip antwortet nicht"})
        self.assertEqual(self.w.status["spannung"], 3.8)
        self.assertEqual(self.w.status["prozent_ohne_netzteil"], akku.prozent(3.8))

    def test_prozent_ohne_netzteil_beim_laden(self):
        self.lauf(self.messung(3.95), self.messung(4.1, "laedt"))
        s = self.w.status
        self.assertIsNone(s["prozent"])
        self.assertEqual(s["prozent_ohne_netzteil"], 72)

    def test_lesefehler_wirft_nicht(self):
        def kaputt():
            raise OSError("bus")
        w = akku.Akkuwache(lesen=kaputt, log=lambda t: None)
        w.tick(0)
        self.assertIn("fehler", w.status)

    def netz(self, *richtungen):
        """Messungen im 2-s-Takt; gibt die Ansagen zurück."""
        self.werte.extend(self.messung(4.0 if r != "akku" else 3.9, r) for r in richtungen)
        t = 0
        while self.werte:
            self.w.tick(t)
            t += akku.Akkuwache.ABSTAND_NETZ_S

    def test_einstecken_sagt_netzteil_nach_zwei_messungen(self):
        self.netz("akku", "akku", "laedt")
        self.assertEqual(self.gesagt, [])                                  # eine Messung allein genügt nicht
        self.netz("laedt")
        self.assertEqual(self.gesagt, ["netzteil"])

    def test_einstecken_auch_wenn_akku_schon_voll(self):
        self.netz("akku", "voll", "voll")
        self.assertEqual(self.gesagt, ["netzteil"])

    def test_beim_start_am_netzteil_keine_ansage(self):
        self.netz("laedt", "laedt", "laedt", "voll")
        self.assertEqual(self.gesagt, [])

    def test_zittern_um_die_schwelle_keine_ansage(self):
        self.netz("akku", "laedt", "akku", "laedt", "akku")
        self.assertEqual(self.gesagt, [])

    def test_ausstecken_still_und_erneutes_einstecken_sagt_wieder(self):
        self.netz("laedt", "laedt", "akku", "akku", "akku")
        self.assertEqual(self.gesagt, [])
        self.netz("laedt", "laedt")
        self.assertEqual(self.gesagt, ["netzteil"])

    def test_lesefehler_aendern_den_netzzustand_nicht(self):
        self.netz("akku", "akku")
        self.werte.extend([{"fehler": "x"}, {"fehler": "x"}, self.messung(4.0, "laedt")])
        t = 100
        while self.werte:
            self.w.tick(t)
            t += akku.Akkuwache.ABSTAND_NETZ_S
        self.assertEqual(self.gesagt, [])                                  # nur eine Messung seit dem Fehler

    def test_ansage_name(self):
        self.assertEqual(akku.ansage_name({"richtung": "akku", "prozent": 64}), "akku_60")
        self.assertEqual(akku.ansage_name({"richtung": "akku", "prozent": 65}), "akku_70")
        self.assertEqual(akku.ansage_name({"richtung": "ruhend", "prozent": 0}), "akku_10")


if __name__ == "__main__":
    unittest.main()
