#!/usr/bin/env python3
"""Tests für Einstellungen und Automatik, ohne Hardware und ohne Spotify (alles simuliert, eigene Uhr).
Aufruf:  python3 -m unittest -v test_automatik   (im Ordner software/)
"""
import datetime
import os
import shutil
import tempfile
import unittest

import automatik
import einstellungen as einst


def zeit(stunde, minute=0, sekunde=0, tag=27):
    return datetime.datetime(2026, 10, tag, stunde, minute, sekunde).timestamp()


class Uhr:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


class FakeSpotify:
    def __init__(self):
        self.spielt_jetzt, self.pausen, self.pause_status, self.wirft = False, 0, 204, False

    def spielt(self, dev):
        if self.wirft:
            raise OSError("kein Netz")
        return self.spielt_jetzt

    def pause(self, dev):
        self.pausen += 1
        if self.pause_status < 300:
            self.spielt_jetzt = False
        return self.pause_status, None


class FakeLaut:
    def __init__(self, v=40):
        self.v = {"kopfhoerer": v}
        self.verlauf = []

    def aktive_ausgabe(self):
        return "kopfhoerer"

    def lesen(self, a):
        return self.v.get(a)

    def setzen(self, a, p):
        self.v[a] = int(round(p))
        self.verlauf.append(self.v[a])
        return True


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.alt = (os.environ.get("HOME"), einst.LAUF)
        os.environ["HOME"] = self.tmp
        einst.LAUF = os.path.join(self.tmp, "lauf")
        os.makedirs(einst.LAUF)
        einst._cache.update(mtime=None, daten=None)
        self.uhr, self.sp, self.laut = Uhr(zeit(12)), FakeSpotify(), FakeLaut()
        self.aus_aufrufe, self.meldungen = [], []
        self.a = automatik.Automatik(self.sp, self.laut, einst, jetzt=self.uhr, schlaf=lambda s: None,
                                     ausschalten=lambda: self.aus_aufrufe.append(self.uhr.t),
                                     log=self.meldungen.append)

    def tearDown(self):
        os.environ["HOME"] = self.alt[0] or ""
        einst.LAUF = self.alt[1]
        shutil.rmtree(self.tmp, ignore_errors=True)

    def laufen(self, sekunden, schritt=1):
        for _ in range(int(sekunden / schritt)):
            self.uhr.t += schritt
            self.a.tick("dev")


class EinstellungenTest(Basis):
    def test_standard_wenn_keine_datei(self):
        self.assertEqual(einst.laden(), einst.STANDARD)

    def test_teilweise_aendern_und_behalten(self):
        einst.speichern({"auto_aus": {"an": True}})
        einst.speichern({"lautstaerke": {"kopfhoerer": {"max": 50}}})
        c = einst.laden()
        self.assertTrue(c["auto_aus"]["an"])
        self.assertEqual(c["lautstaerke"]["kopfhoerer"]["max"], 50)
        self.assertEqual(c["lautstaerke"]["lautsprecher"], einst.STANDARD["lautstaerke"]["lautsprecher"])

    def test_start_nie_ueber_maximum(self):
        einst.speichern({"lautstaerke": {"kopfhoerer": {"max": 20}}})   # Start stand auf 30
        self.assertEqual(einst.laden()["lautstaerke"]["kopfhoerer"]["start"], 20)

    def test_ungueltiges_wird_abgelehnt_und_nichts_gespeichert(self):
        schlecht = [{"lautstaerke": {"kopfhoerer": {"max": 150}}}, {"lautstaerke": {"kopfhoerer": {"max": 2}}},
                    {"lautstaerke": {"kopfhoerer": {"max": "laut"}}}, {"lautstaerke": {"kopfhoerer": {"max": True}}},
                    {"lautstaerke": {"radio": {"max": 50}}}, {"ruhezeit": {"von": "25:00"}},
                    {"ruhezeit": {"von": "19:30", "bis": "19:30"}}, {"ruhezeit": {"modus": "stumm"}},
                    {"auto_aus": {"minuten": 1}}, {"auto_aus": {"an": "ja"}}, {"unbekannt": 1}, [], "x"]
        for s in schlecht:
            with self.assertRaises(ValueError, msg=str(s)):
                einst.speichern(s)
        self.assertFalse(os.path.exists(einst.pfad()))

    def test_kaputte_datei_gibt_standard(self):
        os.makedirs(os.path.dirname(einst.pfad()))
        with open(einst.pfad(), "w") as f:
            f.write("{kaputt")
        self.assertEqual(einst.laden(), einst.STANDARD)

    def test_ruhezeit_fenster_ueber_mitternacht(self):
        c = einst.bereinigen({"ruhezeit": {"an": True}}, einst.STANDARD)       # 19:30 bis 06:30
        for h, m, erwartet in [(19, 29, False), (19, 30, True), (23, 59, True), (0, 0, True),
                               (6, 29, True), (6, 30, False), (12, 0, False)]:
            self.assertEqual(einst.in_ruhezeit(c, zeit(h, m)), erwartet, f"{h}:{m}")

    def test_ruhezeit_fenster_am_tag(self):
        c = einst.bereinigen({"ruhezeit": {"an": True, "von": "13:00", "bis": "15:00"}}, einst.STANDARD)
        self.assertTrue(einst.in_ruhezeit(c, zeit(14)))
        self.assertFalse(einst.in_ruhezeit(c, zeit(15)))
        self.assertFalse(einst.in_ruhezeit(c, zeit(23)))

    def test_naechstes_ende(self):
        c = einst.STANDARD
        self.assertEqual(einst.naechstes_ende(c, zeit(22)), zeit(6, 30, tag=28))    # abends: morgen früh
        self.assertEqual(einst.naechstes_ende(c, zeit(5)), zeit(6, 30))             # nachts: heute früh
        self.assertEqual(einst.naechstes_ende(c, zeit(6, 30)), zeit(6, 30, tag=28))


class StartTest(Basis):
    def test_startlautstaerke_nur_einmal_je_einschalten(self):
        self.a.beim_start()
        self.assertEqual(self.laut.v["kopfhoerer"], 30)
        self.laut.v["kopfhoerer"] = 45                    # später von Hand geändert
        automatik.Automatik(self.sp, self.laut, einst, jetzt=self.uhr, log=print).beim_start()   # Player-Neustart
        self.assertEqual(self.laut.v["kopfhoerer"], 45)
        os.remove(einst.lauf_pfad("gestartet"))           # wie nach dem Neustart der Box
        self.a.beim_start()
        self.assertEqual(self.laut.v["kopfhoerer"], 30)

    def test_startlautstaerke_beachtet_ruhezeit(self):
        einst.speichern({"ruhezeit": {"an": True, "leise_max": 15}})
        self.uhr.t = zeit(21)
        self.a.beim_start()
        self.assertEqual(self.laut.v["kopfhoerer"], 15)


class GrenzenTest(Basis):
    def test_zu_laut_wird_begrenzt(self):
        self.laut.v["kopfhoerer"] = 90
        self.laufen(1)
        self.assertEqual(self.laut.v["kopfhoerer"], 60)

    def test_unter_der_grenze_bleibt_unangetastet(self):
        self.laut.v["kopfhoerer"] = 35
        self.laufen(30)
        self.assertEqual(self.laut.verlauf, [])

    def test_ruhezeit_leiser_und_danach_nicht_von_selbst_lauter(self):
        einst.speichern({"ruhezeit": {"an": True}})       # 19:30-06:30, leise_max 25
        self.uhr.t = zeit(19, 29, 50)
        self.laut.v["kopfhoerer"] = 40
        self.laufen(5)
        self.assertEqual(self.laut.v["kopfhoerer"], 40)   # noch keine Ruhezeit
        self.laufen(20)
        self.assertEqual(self.laut.v["kopfhoerer"], 25)   # Ruhezeit hat begonnen
        self.uhr.t = zeit(6, 31, tag=28)
        self.laufen(30)
        self.assertEqual(self.laut.v["kopfhoerer"], 25)   # bleibt leise
        self.assertEqual(einst.wirksames_max(einst.laden(), "kopfhoerer", self.uhr.t), 60)

    def test_ruhezeit_aus_laesst_lautstaerke_in_ruhe(self):
        einst.speichern({"ruhezeit": {"an": True, "modus": "aus"}})
        self.uhr.t = zeit(21)
        self.laut.v["kopfhoerer"] = 40
        self.laufen(30)
        self.assertEqual(self.laut.v["kopfhoerer"], 40)


class RuhezeitSperreTest(Basis):
    def setUp(self):
        super().setUp()
        einst.speichern({"ruhezeit": {"an": True, "modus": "aus"}})
        self.uhr.t = zeit(21)

    def test_laufende_musik_wird_pausiert(self):
        self.sp.spielt_jetzt = True
        self.laufen(1)
        self.assertEqual(self.sp.pausen, 1)
        self.assertTrue(self.a.status["ruhezeit"])

    def test_player_darf_nicht_starten(self):
        self.assertTrue(self.a.sperrt())

    def test_ausgesetzt_bis_zum_ende_der_ruhezeit(self):
        einst.lauf_schreiben("ruhe", {"bis": einst.naechstes_ende(einst.laden(), self.uhr.t)})
        self.assertFalse(self.a.sperrt())
        self.sp.spielt_jetzt = True
        self.laufen(30)
        self.assertEqual(self.sp.pausen, 0)
        self.uhr.t = zeit(21, tag=28)                      # am nächsten Abend gilt sie wieder
        self.assertTrue(self.a.sperrt())

    def test_tagsueber_keine_sperre(self):
        self.uhr.t = zeit(12)
        self.assertFalse(self.a.sperrt())

    def test_ausgeschaltete_ruhezeit_sperrt_nie(self):
        einst.speichern({"ruhezeit": {"an": False}})
        self.assertFalse(self.a.sperrt())


class TimerTest(Basis):
    def starte_timer(self, sekunden):
        einst.lauf_schreiben("timer", {"ende": self.uhr.t + sekunden, "minuten": sekunden / 60})

    def test_ausblenden_pause_und_lautstaerke_zurueck(self):
        self.sp.spielt_jetzt = True
        self.laut.v["kopfhoerer"] = 40
        self.starte_timer(60)
        self.laufen(35)                                    # noch 25 s: kein Ausblenden
        self.assertEqual(self.laut.v["kopfhoerer"], 40)
        self.assertEqual(self.sp.pausen, 0)
        self.laufen(15)                                    # noch 10 s: halbe Lautstärke
        self.assertEqual(self.laut.v["kopfhoerer"], 20)
        self.laufen(9)
        self.assertLessEqual(self.laut.v["kopfhoerer"], 2)
        self.assertEqual(self.sp.pausen, 0)
        self.laufen(2)                                     # Ende
        self.assertEqual(self.sp.pausen, 1)
        self.assertEqual(self.laut.v["kopfhoerer"], 40)    # wieder wie vorher
        self.assertIsNone(einst.lauf_lesen("timer"))
        self.laufen(30)
        self.assertEqual(self.sp.pausen, 1)                # nicht nochmal

    def test_nichts_zu_pausieren_wenn_schon_pause(self):
        self.sp.spielt_jetzt = False
        self.laut.v["kopfhoerer"] = 40
        self.starte_timer(30)
        self.laufen(40)
        self.assertEqual(self.sp.pausen, 0)
        self.assertEqual(self.laut.v["kopfhoerer"], 40)
        self.assertIsNone(einst.lauf_lesen("timer"))

    def test_pause_waehrend_ausblenden_stellt_lautstaerke_am_ende_wieder_her(self):
        self.sp.spielt_jetzt = True
        self.laut.v["kopfhoerer"] = 40
        self.starte_timer(25)
        self.laufen(10)                                    # mitten im Ausblenden
        self.assertLess(self.laut.v["kopfhoerer"], 40)
        self.sp.spielt_jetzt = False                       # jemand drückt Pause
        self.laufen(20)
        self.assertEqual(self.laut.v["kopfhoerer"], 40)
        self.assertIsNone(einst.lauf_lesen("timer"))

    def test_pause_fehlgeschlagen_wird_wiederholt_dann_aufgegeben(self):
        self.sp.spielt_jetzt = True
        self.sp.pause_status = 500
        self.starte_timer(5)
        self.laufen(40)
        self.assertGreater(self.sp.pausen, 3)
        self.assertIsNotNone(einst.lauf_lesen("timer"))    # noch in der Gnadenfrist
        self.laufen(40)
        self.assertIsNone(einst.lauf_lesen("timer"))

    def test_kein_aktives_geraet_gilt_als_erledigt(self):
        self.sp.spielt_jetzt = True
        self.sp.pause_status = 404
        self.starte_timer(3)
        self.laufen(15)
        self.assertEqual(self.sp.pausen, 1)
        self.assertIsNone(einst.lauf_lesen("timer"))

    def test_timer_ueberlebt_neustart_des_players(self):
        self.sp.spielt_jetzt = True
        self.laut.v["kopfhoerer"] = 40
        self.starte_timer(30)
        self.laufen(15)                                    # Ausblenden hat begonnen
        self.assertEqual(einst.lauf_lesen("timer")["vorher"], 40)
        neu = automatik.Automatik(self.sp, self.laut, einst, jetzt=self.uhr, schlaf=lambda s: None, log=print)
        self.a = neu                                       # Player startet mitten im Ausblenden neu
        self.laufen(20)
        self.assertEqual(self.sp.pausen, 1)
        self.assertEqual(self.laut.v["kopfhoerer"], 40)


class AutoAusTest(Basis):
    def setUp(self):
        super().setUp()
        einst.speichern({"auto_aus": {"an": True, "minuten": 30}})

    def test_ausschalten_nach_der_frist(self):
        self.laufen(29 * 60 + 50, 10)
        self.assertEqual(self.aus_aufrufe, [])
        self.assertLessEqual(self.a.status["auto_aus_in"], 10)
        self.laufen(20, 10)
        self.assertEqual(len(self.aus_aufrufe), 1)

    def test_musik_haelt_die_box_an(self):
        self.sp.spielt_jetzt = True
        self.laufen(2 * 3600, 10)
        self.assertEqual(self.aus_aufrufe, [])
        self.sp.spielt_jetzt = False
        self.laufen(29 * 60, 10)
        self.assertEqual(self.aus_aufrufe, [])
        self.laufen(90, 10)
        self.assertEqual(len(self.aus_aufrufe), 1)

    def test_offene_eltern_seite_haelt_die_box_an(self):
        for _ in range(60):                                 # Seite ist 60 Minuten lang offen
            einst.lauf_beruehren("seite")
            os.utime(einst.lauf_pfad("seite"), (self.uhr.t, self.uhr.t))
            self.laufen(60, 10)
        self.assertEqual(self.aus_aufrufe, [])
        self.laufen(29 * 60, 10)                            # Seite zu: Frist beginnt erst jetzt
        self.assertEqual(self.aus_aufrufe, [])
        self.laufen(3 * 60, 10)
        self.assertEqual(len(self.aus_aufrufe), 1)

    def test_ausgeschaltet_macht_nichts(self):
        einst.speichern({"auto_aus": {"an": False}})
        self.laufen(5 * 3600, 30)
        self.assertEqual(self.aus_aufrufe, [])
        self.assertIsNone(self.a.status["auto_aus_in"])

    def test_unbekannter_zustand_setzt_die_frist_nicht_zurueck(self):
        self.sp.wirft = True                                # Spotify nicht erreichbar
        self.laufen(31 * 60, 10)
        self.assertEqual(len(self.aus_aufrufe), 1)

    def test_fehlgeschlagenes_ausschalten_wird_nicht_jede_sekunde_versucht(self):
        def kaputt():
            self.aus_aufrufe.append(self.uhr.t)
            raise RuntimeError("sudo: Passwort nötig")
        self.a.ausschalten = kaputt
        self.laufen(31 * 60, 5)
        self.assertEqual(len(self.aus_aufrufe), 1)
        self.assertTrue(any("fehlgeschlagen" in m for m in self.meldungen))
        self.laufen(30 * 60, 5)                             # nach der nächsten Frist noch einmal
        self.assertEqual(len(self.aus_aufrufe), 2)


if __name__ == "__main__":
    unittest.main()
