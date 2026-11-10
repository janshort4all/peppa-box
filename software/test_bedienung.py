"""Tests der Bedienung (Touchfelder, Ein-Taste, Drehknopf) und der Hardware-Abfrage mit simulierter
Uhr und nachgebauter Hardware. Aufruf: cd software && python3 -m unittest -v test_bedienung
"""
import json
import os
import tempfile
import unittest
from unittest import mock

import bedienung
import einstellungen
import gpio
import mpr121
from bedienung import Bedienung, Hardware, Regler


class Uhr:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class FakeSteuerung:
    def __init__(self):
        self.aufrufe = []
        self.antwort_play = "pause"
        self.laeuft = True

    def taste_play(self):
        self.aufrufe.append(("play",))
        return self.antwort_play

    def taste_springen(self, r):
        self.aufrufe.append(("springen", r))
        return self.laeuft

    def taste_spulen(self, ms):
        self.aufrufe.append(("spulen", ms))
        return self.laeuft

    def pausieren(self):
        self.aufrufe.append(("pausieren",))
        return True

    def von_vorn(self):
        self.aufrufe.append(("von_vorn",))
        return True


class FakeAuto:
    def __init__(self):
        self.gesperrt = False

    def sperrt(self):
        return self.gesperrt


class FakeLaut:
    def __init__(self, v=40):
        self.v = {"lautsprecher": v, "kopfhoerer": 30}
        self.aus = "lautsprecher"

    def aktive_ausgabe(self):
        return self.aus

    def lesen(self, a):
        return self.v.get(a)

    def setzen(self, a, p):
        self.v[a] = int(round(p))
        return True

    def eingerichtet(self, a):
        return True


class FakeTimer:
    def __init__(self, einst):
        self.einst = einst

    def timer_starten(self, minuten, laut, einst, jetzt=None):
        self.einst.lauf_schreiben("timer", {"ende": jetzt + minuten * 60, "minuten": minuten, "vorher": None})

    def timer_abbrechen(self, laut, einst):
        had = self.einst.lauf_lesen("timer") is not None
        self.einst.lauf_loeschen("timer")
        return had


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name, wert in (("LAUF", self.tmp.name),):
            p = mock.patch.object(einstellungen, name, wert)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.dict(os.environ, {"HOME": self.tmp.name})
        p.start()
        self.addCleanup(p.stop)
        einstellungen._cache["mtime"] = None
        self.uhr = Uhr()
        self.wand = Uhr(1_800_000_000.0)
        self.st = FakeSteuerung()
        self.auto = FakeAuto()
        self.laut = FakeLaut()
        self.regler = mock.Mock()
        self.gesagt = []
        self.aus = []
        self.spar = []
        self.karte_liegt = (False, None)
        self.akku = {"spannung": 3.9, "prozent": 64, "richtung": "akku"}
        self.b = Bedienung(self.st, self.auto, self.regler, einstellungen, self.gesagt.append,
                           akku_info=lambda: self.akku, herunterfahren=lambda g, a: self.aus.append((g, a)),
                           karte=lambda: self.karte_liegt, jetzt=self.uhr, uhr=self.wand,
                           log=lambda t: None, timer=FakeTimer(einstellungen), laut=self.laut)

    def tippen(self, feld, dauer=0.2):
        self.b.felder({feld}, self.uhr.t)
        self.lauf(dauer, felder={feld})
        self.b.felder(set(), self.uhr.t)

    def lauf(self, s, felder=None, taste=None):
        ende = self.uhr.t + s
        while self.uhr.t < ende:
            self.uhr.t += 0.02
            if felder is not None:
                self.b.felder(felder, self.uhr.t)
            if taste is not None:
                self.b.ein_taste(taste, self.uhr.t)
            self.b.tick(self.uhr.t)


class Felder(Basis):
    def test_play_antippen(self):
        self.tippen("play")
        self.assertEqual(self.st.aufrufe, [("play",)])

    def test_play_ohne_karte_bleibt_still(self):
        self.st.antwort_play = "keine_karte"                    # Wunsch Jan 08.11.: keine Ansage
        self.tippen("play")
        self.uhr.t += 9
        self.tippen("play")
        self.assertEqual(self.gesagt, [])

    def test_play_bei_leerer_karte(self):
        self.st.antwort_play = "keine_karte"
        self.karte_liegt = (True, None)
        self.tippen("play")
        self.assertEqual(self.gesagt, ["karte_leer"])

    def test_play_in_ruhezeit(self):
        self.auto.gesperrt = True
        self.tippen("play")
        self.assertEqual(self.st.aufrufe, [])
        self.assertEqual(self.gesagt, ["ruhezeit"])

    def test_play_lange_gehalten_nichts(self):
        self.tippen("play", dauer=1.8)
        self.assertEqual(self.st.aufrufe, [])

    def test_play_2_s_halten_von_vorn(self):
        self.tippen("play", dauer=4.0)
        self.assertEqual(self.st.aufrufe, [("von_vorn",)])          # einmal, kein Pause/Weiter

    def test_phantom_beruehrung_loest_nichts_aus(self):
        # Befund 09.11.2026: Play-Feld meldete ohne Finger ständig kurze Berührungen
        log = []
        self.b.log = log.append
        for feld in ("play", "vor", "zurueck", "schlaf", "play"):
            self.tippen(feld, dauer=0.04)
            self.uhr.t += 1
        self.assertEqual(self.st.aufrufe, [])
        self.assertEqual(self.gesagt, [])
        self.assertEqual(self.b.kurz_gesamt, 5)
        self.assertEqual(len([z for z in log if "zu kurze" in z]), 1)     # nur einmal je Minute gemeldet
        self.lauf(61)
        self.assertEqual(len([z for z in log if "zu kurze" in z]), 2)     # Rest zusammengefasst
        self.assertIn("play 1×", log[-1])
        self.lauf(120)
        self.assertEqual(len([z for z in log if "zu kurze" in z]), 2)     # nichts Neues, keine Meldung

    def test_echtes_antippen_ab_70_ms(self):
        self.tippen("play", dauer=0.08)
        self.tippen("vor", dauer=0.08)
        self.assertEqual(self.st.aufrufe, [("play",), ("springen", 1)])

    def test_vor_zurueck_antippen(self):
        self.tippen("vor")
        self.tippen("zurueck")
        self.assertEqual(self.st.aufrufe, [("springen", 1), ("springen", -1)])

    def test_vor_halten_spult_wiederholt_ohne_sprung(self):
        self.tippen("vor", dauer=2.4)                       # 0,7 s, dann alle 0,8 s: 0,7 1,5 2,3
        self.assertEqual(self.st.aufrufe, [("spulen", 15000)] * 3)
        self.st.aufrufe.clear()
        self.tippen("zurueck", dauer=0.9)
        self.assertEqual(self.st.aufrufe, [("spulen", -15000)])

    def test_mehrere_felder_loesen_nichts_aus(self):
        self.b.felder({"play"}, self.uhr.t)
        self.lauf(0.05, felder={"play"})
        self.lauf(0.3, felder={"play", "vor"})
        self.lauf(0.1, felder={"vor"})
        self.b.felder(set(), self.uhr.t)
        self.lauf(1.0, felder={"vor", "zurueck"})          # auch kein Spulen
        self.b.felder(set(), self.uhr.t)
        self.assertEqual(self.st.aufrufe, [])
        self.tippen("play")                                 # danach wieder normal
        self.assertEqual(self.st.aufrufe, [("play",)])

    def test_abbrechen_loest_nichts_aus(self):
        self.b.felder({"play"}, self.uhr.t)
        self.lauf(0.2, felder={"play"})
        self.b.felder_abbrechen()
        self.b.felder(set(), self.uhr.t)
        self.assertEqual(self.st.aufrufe, [])

    def test_mond_stufen_und_aus(self):
        for erwartet in ("timer_15", "timer_30", "timer_45", "timer_60", "timer_aus", "timer_15"):
            self.tippen("schlaf")
            self.assertEqual(self.gesagt[-1], erwartet)
        t = einstellungen.lauf_lesen("timer")
        self.assertEqual(t["minuten"], 15)
        self.assertAlmostEqual(t["ende"], self.wand.t + 900)

    def test_mond_nach_seiten_timer_naechste_stufe(self):
        einstellungen.lauf_schreiben("timer", {"ende": self.wand.t + 1200, "minuten": 20, "vorher": None})
        self.tippen("schlaf")
        self.assertEqual(self.gesagt, ["timer_30"])

    def test_mond_5s_akku_und_kein_timer(self):
        self.tippen("schlaf", dauer=5.3)
        self.assertEqual(self.gesagt, ["akku_60"])
        self.assertIsNone(einstellungen.lauf_lesen("timer"))
        self.tippen("schlaf", dauer=3.0)                    # zwischen 1,5 und 5 s: nichts
        self.assertEqual(self.gesagt, ["akku_60"])

    def test_akku_ansage_varianten(self):
        for info, name in (({"richtung": "laedt", "prozent": None}, "akku_laedt"),
                           ({"richtung": "voll", "prozent": 99}, "akku_voll"),
                           ({"richtung": "akku", "prozent": 3}, "akku_10"),
                           ({"richtung": "akku", "prozent": 96}, "akku_100"),
                           ({"fehler": "x"}, "akku_unbekannt"), (None, "akku_unbekannt")):
            self.akku = info
            self.gesagt.clear()
            self.b._angesagt.clear()
            self.b.akku_ansagen()
            self.assertEqual(self.gesagt, [name], info)


class EinTaste(Basis):
    def drueck(self, dauer):
        self.b.ein_taste(False, self.uhr.t)                 # Startwert: los
        self.lauf(dauer, taste=True)
        self.lauf(0.1, taste=False)

    def test_kurz_akku(self):
        self.drueck(0.3)
        self.assertEqual(self.gesagt, ["akku_60"])
        self.assertEqual(self.aus, [])

    def test_zwei_sekunden_tschuess_und_aus_beim_loslassen(self):
        self.b.ein_taste(False, self.uhr.t)
        self.lauf(2.1, taste=True)
        self.assertEqual(self.gesagt, [])                   # noch gedrückt: kein „Tschüss“
        self.assertIn(("pausieren",), self.st.aufrufe)
        self.assertEqual(self.aus, [])                      # noch gedrückt: nicht ausschalten
        self.lauf(1.0, taste=True)
        self.assertEqual(self.aus, [])
        self.lauf(0.1, taste=False)
        self.assertEqual(self.aus, [("Ein-Taste", "tschuess")])

    def test_klemmt_schaltet_nie_aus(self):
        self.b.ein_taste(False, self.uhr.t)
        self.lauf(16, taste=True)
        self.lauf(0.1, taste=False)
        self.assertEqual(self.aus, [])


class EinTasteSparzustand(Basis):
    """Mit Sparzustand: 2 s halten = Sparzustand, 10 s halten = ganz aus (beides erst beim Loslassen)."""

    def drueck(self, dauer):
        self.b.ein_taste(False, self.uhr.t)                 # Startwert: los
        self.lauf(dauer, taste=True)
        self.lauf(0.1, taste=False)

    def setUp(self):
        super().setUp()
        self.b = Bedienung(self.st, self.auto, self.regler, einstellungen, self.gesagt.append,
                           akku_info=lambda: self.akku, herunterfahren=lambda g, a: self.aus.append((g, a)),
                           karte=lambda: self.karte_liegt, jetzt=self.uhr, uhr=self.wand,
                           log=lambda t: None, timer=FakeTimer(einstellungen), laut=self.laut,
                           sparzustand=lambda g, a: self.spar.append((g, a)))

    def test_zwei_sekunden_sparzustand_beim_loslassen(self):
        self.b.ein_taste(False, self.uhr.t)
        self.lauf(2.1, taste=True)
        self.assertEqual(self.gesagt, [])                                # noch gedrückt: kein „Tschüss“
        self.assertIn(("pausieren",), self.st.aufrufe)
        self.assertEqual((self.spar, self.aus), ([], []))                # noch gedrückt: noch nichts
        self.lauf(3.0, taste=True)                                       # 5 s: immer noch Sparzustand
        self.assertEqual((self.spar, self.aus), ([], []))
        self.assertEqual(self.gesagt, [])
        self.lauf(0.1, taste=False)
        self.assertEqual((self.spar, self.aus), ([("Ein-Taste", "tschuess")], []))   # „Tschüss“ spricht der Player

    def test_zehn_sekunden_ganz_aus_beim_loslassen(self):
        self.b.ein_taste(False, self.uhr.t)
        self.lauf(10.2, taste=True)
        self.assertEqual(self.gesagt, ["ganz_aus"])                      # kein „Tschüss“ unterwegs
        self.assertEqual((self.spar, self.aus), ([], []))
        self.lauf(0.1, taste=False)
        self.assertEqual((self.spar, self.aus), ([], [("Ein-Taste", None)]))

    def test_kurz_bleibt_akkustand(self):
        self.drueck(0.3)
        self.assertEqual(self.gesagt, ["akku_60"])
        self.assertEqual((self.spar, self.aus), ([], []))

    def test_klemmt_weder_sparzustand_noch_aus(self):
        self.b.ein_taste(False, self.uhr.t)
        self.lauf(16, taste=True)
        self.lauf(0.1, taste=False)
        self.assertEqual((self.spar, self.aus), ([], []))

    def test_nach_sparzustand_wieder_normal(self):
        self.b.ein_taste(False, self.uhr.t)
        self.lauf(2.1, taste=True)
        self.lauf(0.1, taste=False)
        self.gesagt.clear()
        self.drueck(0.3)
        self.assertEqual(self.gesagt, ["akku_60"])                       # Merker zurückgesetzt
        self.lauf(10.2, taste=True)

    def test_belegung_nennt_beide_gesten(self):
        import bedienung
        taste = [x for x in bedienung.belegung(einstellungen.laden())["elemente"] if x["id"] == "taste"][0]
        texte = " ".join(g["wie"] + " " + g["was"] for g in taste["gesten"])
        self.assertIn("Sparzustand", texte)
        self.assertIn("ganz aus", texte)

    def test_beim_start_gedrueckt_wird_ignoriert(self):
        self.b.ein_taste(True, self.uhr.t)
        self.lauf(5, taste=True)
        self.lauf(0.1, taste=False)
        self.assertEqual((self.aus, self.gesagt), ([], []))
        self.drueck(0.3)                                    # danach normal
        self.assertEqual(self.gesagt, ["akku_60"])


class Drehknopf(Basis):
    def test_schritt_und_umkehren(self):
        self.b.drehen(+1)
        self.b.drehen(-3)
        self.assertEqual(self.regler.aendern.call_args_list, [mock.call(2), mock.call(-6)])
        einstellungen.speichern({"bedienung": {"drehknopf_umkehren": True, "drehknopf_schritt": 5}})
        self.regler.aendern.reset_mock()
        self.b.drehen(+1)
        self.regler.aendern.assert_called_once_with(-5)

    def test_regler_grenzen(self):
        r = Regler(self.laut, einstellungen, uhr=self.wand, log=lambda t: None)
        self.laut.v["lautsprecher"] = 66
        self.assertEqual(r.anwenden(+10), 70)               # Höchstlautstärke Lautsprecher 70
        self.assertEqual(r.anwenden(+2), 70)
        self.laut.v["lautsprecher"] = 8
        self.assertEqual(r.anwenden(-10), 5)                # nie unter 5 %
        self.laut.v["lautsprecher"] = 3                     # von der Seite auf 3 % gestellt
        self.assertEqual(r.anwenden(-2), 3)                 # Drehen nach unten hebt nicht an
        self.assertEqual(r.anwenden(+2), 5)
        self.laut.aus = "kopfhoerer"
        self.laut.v["kopfhoerer"] = 58
        self.assertEqual(r.anwenden(+10), 60)               # Grenze Kopfhörer 60

    def test_regler_sammelt_rasten(self):
        r = Regler(self.laut, einstellungen, uhr=self.wand, log=lambda t: None)
        r.aendern(2)
        r.aendern(2)
        r.aendern(-2)
        self.assertEqual(r._offen, 2)


# ====================================================================== Hardware-Abfrage

class FakeGpio:
    def __init__(self):
        self.w = (1 << gpio.SCL) | (1 << gpio.MPR_INT)      # Taste los, INT hoch, Klinke tief
        self.fsel16 = 0

    def pegel_alle(self):
        return self.w

    def funktion(self, pin):
        return self.fsel16

    def setze(self, pin, an):
        self.w = self.w | (1 << pin) if an else self.w & ~(1 << pin)


class FakeMPR:
    instanzen = []
    einrichten_fehler = None

    def __init__(self, bus):
        self.maske, self.fehler, self.kalibriert, self.eingerichtet = 0, None, 0, None
        FakeMPR.instanzen.append(self)

    def einrichten(self, s, l):
        if FakeMPR.einrichten_fehler:
            raise FakeMPR.einrichten_fehler
        self.eingerichtet = (s, l)

    def pruefen(self):
        pass

    def beruehrt(self):
        if self.fehler:
            raise self.fehler
        return self.maske

    def rohwerte(self):
        return [(700, 720, 20)] * 4

    def neu_kalibrieren(self):
        self.kalibriert += 1
        self.maske = 0                                      # neue Grundlinie: Feld gilt als frei

    def schlafen(self):
        pass


class FakeAusgang:
    def __init__(self):
        self.pegel = []

    def tick(self, pegel, t):
        self.pegel.append(pegel)

    def stumm_halten(self, leser):
        pass

    status = {"pegel": None}


class FakeAkkuwache:
    def __init__(self):
        self.ticks = 0

    def tick(self, t):
        self.ticks += 1

    status = None


class HardwareAbfrage(Basis):
    def setUp(self):
        super().setUp()
        FakeMPR.instanzen.clear()
        FakeMPR.einrichten_fehler = None
        self.g = FakeGpio()
        self.bed = mock.Mock()
        self.ausg = FakeAusgang()
        self.akkuw = FakeAkkuwache()
        self.befreit = 0
        self.log = []

        def befreien(leser, log=None):
            self.befreit += 1
        self.hw = Hardware(self.bed, self.ausg, self.akkuw, einstellungen, log=self.log.append,
                           gpio_oeffnen=lambda: self.g, bus_oeffnen=lambda: object(), mpr_klasse=FakeMPR,
                           befreien=befreien, pins_setzen=lambda *a, **k: True, jetzt=self.uhr, uhr=self.wand,
                           schlaf=lambda s: None)

    def schritte(self, s):
        ende = self.uhr.t + s
        while self.uhr.t < ende:
            self.uhr.t += 0.02
            self.hw.schritt(self.uhr.t)

    def felder_aufrufe(self):
        return [c.args[0] for c in self.bed.felder.call_args_list]

    def test_touch_ueber_int_mit_zuordnung(self):
        self.schritte(0.1)
        m = FakeMPR.instanzen[-1]
        self.assertEqual(m.eingerichtet, (8, 4))
        m.maske = 0b0010                                    # E1 = Play
        self.g.setze(gpio.MPR_INT, False)
        self.schritte(0.04)
        self.assertEqual(self.felder_aufrufe()[-1], {"play"})
        einstellungen.speichern({"bedienung": {"felder": {"play": 3, "schlaf": 1}}})
        self.schritte(0.04)
        self.assertEqual(self.felder_aufrufe()[-1], {"schlaf"})

    def test_ein_taste_entprellt_und_kein_i2c_solange_gedrueckt(self):
        self.schritte(0.1)
        self.assertEqual(self.bed.ein_taste.call_args.args[0], False)
        m = FakeMPR.instanzen[-1]
        m.fehler = OSError("Zeitüberschreitung")              # SCL tief: I2C scheitert
        self.g.setze(gpio.SCL, False)
        self.schritte(0.04)
        self.assertEqual(self.bed.ein_taste.call_args.args[0], False)    # erst nach 3 Proben
        self.schritte(0.06)
        self.assertEqual(self.bed.ein_taste.call_args.args[0], True)
        ticks = self.akkuw.ticks
        self.schritte(2.0)
        self.assertIs(self.hw.mpr, m)                        # Chip nicht als defekt verworfen
        self.assertEqual(self.akkuw.ticks, ticks)            # kein Akku-Lesen während gedrückt
        self.g.setze(gpio.SCL, True)
        m.fehler = None
        self.schritte(0.1)
        self.assertEqual(self.bed.ein_taste.call_args.args[0], False)

    def test_taste_waehrend_uebertragung_ist_kein_chipfehler(self):
        self.schritte(0.1)
        m = FakeMPR.instanzen[-1]
        g = self.g

        def mitten_drin():
            g.setze(gpio.SCL, False)                         # Taste genau während der Übertragung gedrückt
            raise OSError("Zeitüberschreitung")
        for _ in range(4):
            m.beruehrt = mitten_drin
            self.schritte(0.3)
            g.setze(gpio.SCL, True)
            m.beruehrt = lambda: 0
            self.schritte(0.1)
        self.assertEqual(len(FakeMPR.instanzen), 1)           # Chip nie als defekt neu eingerichtet
        self.assertIs(self.hw.mpr, m)

    def test_kurzer_scl_einbruch_ist_keine_taste(self):
        self.schritte(0.1)
        self.g.setze(gpio.SCL, False)
        self.schritte(0.03)                                  # 1 Probe tief (fremde I2C-Übertragung)
        self.g.setze(gpio.SCL, True)
        self.schritte(0.1)
        self.assertNotIn(True, [c.args[0] for c in self.bed.ein_taste.call_args_list])

    def test_chip_faellt_aus_wird_neu_eingerichtet(self):
        self.schritte(0.1)
        m = FakeMPR.instanzen[-1]
        m.fehler = OSError("Remote I/O error")
        self.schritte(0.8)                                   # 3 Fehler in Folge (alle 0,25 s)
        self.assertIsNot(self.hw.mpr, m)
        self.schritte(1.0)
        self.assertGreaterEqual(len(FakeMPR.instanzen), 2)
        self.assertIsNotNone(self.hw.mpr)
        self.bed.felder_abbrechen.assert_called()

    def test_chip_fehlt_wachsender_abstand_und_bus_befreien(self):
        FakeMPR.einrichten_fehler = OSError("kein Gerät")
        self.schritte(20)
        versuche = len(FakeMPR.instanzen)
        self.assertTrue(3 <= versuche <= 5, versuche)          # 1 + 2 + 5 + 10 s
        self.assertEqual(self.befreit, versuche)
        self.assertIsNotNone(self.hw.touch_fehler)
        FakeMPR.einrichten_fehler = None
        self.schritte(31)
        self.assertIsNotNone(self.hw.mpr)
        self.assertIsNone(self.hw.touch_fehler)

    def test_klemmendes_feld_wird_kalibriert(self):
        self.schritte(0.1)
        m = FakeMPR.instanzen[-1]
        m.maske = 0b0001
        self.schritte(61)
        self.assertEqual(m.kalibriert, 1)
        self.assertEqual(self.felder_aufrufe()[-1], set())

    def test_int_haengt_dann_nur_abfragen(self):
        self.schritte(0.1)
        self.g.setze(gpio.MPR_INT, False)
        self.schritte(3)
        self.assertTrue(self.hw._int_haengt)
        n = len(self.felder_aufrufe())
        self.schritte(1)
        self.assertLessEqual(len(self.felder_aufrufe()) - n, 5)   # nur noch alle 0,25 s

    def test_ohne_gpio_touch_trotzdem(self):
        self.hw.gpio_oeffnen = mock.Mock(side_effect=OSError("kein /dev/gpiomem"))
        self.schritte(0.6)
        self.assertIsNotNone(self.hw.mpr)
        self.bed.ein_taste.assert_not_called()
        self.assertEqual(self.ausg.pegel, [])
        self.assertTrue(any("GPIO nicht lesbar" in z for z in self.log))

    def test_klinke_und_live_datei(self):
        self.schritte(0.3)
        self.assertEqual(set(self.ausg.pegel), {0})
        self.g.setze(gpio.KLINKE, True)
        self.schritte(0.3)
        self.assertEqual(self.ausg.pegel[-1], 1)
        live = einstellungen.lauf_lesen("bedienung")
        self.assertTrue(live["touch"]["ok"])
        self.assertIn("zeit", live)
        self.assertIsNone(live["touch"]["roh"])
        einstellungen.lauf_beruehren("seite-bedienung")
        with mock.patch.object(einstellungen, "lauf_alter", return_value=1.0):
            self.schritte(0.5)
        self.assertEqual(self.hw.roh[0], (700, 720, 20))
        json.dumps(self.hw.live())                            # für die Seite serialisierbar


if __name__ == "__main__":
    unittest.main()
