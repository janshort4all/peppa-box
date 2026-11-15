"""Regressionstests zum Befund vom 15.11.2026 (Musik ging morgens aus, Box blieb still).

Ablauf im Protokoll: Musik läuft -> librespot „Spirc shut down unexpectedly“ (session_disconnected) ->
nächster Titel „nicht abspielbar“ (unavailable) -> Ende-Ereignis -> „Karte zu Ende gehört“, obwohl die Playlist
204 Titel hat. Der Wächter holte die Musik nicht zurück, die gemerkte Stelle wurde gelöscht.
Weitere Tests dazu: test_audit_a (Wächter: Ansagen), test_bedienung (Touch-Chip vor dem Ausschalten, Abstände).
Aufruf: cd software && python3 -m unittest -v test_befund_1511
"""
import unittest

import rueckmeldung
import toene
from rueckmeldung import Rueckmeldung


class Uhr:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class AmEnde(unittest.TestCase):
    def setUp(self):
        self.uhr = Uhr()
        self.r = Rueckmeldung(jetzt=self.uhr, log=lambda *a: None)

    def e(self, name, **k):
        self.r.verarbeiten(dict(q="ereignis", player_event=name, **k))

    def titel_laeuft(self, tid="t1", dauer=180000):
        self.e("track_changed", track_id=tid, uri=f"spotify:track:{tid}", duration_ms=str(dauer))
        self.e("playing", track_id=tid, position_ms="0")

    def test_abbruch_wie_am_15_11_ist_kein_ende(self):
        self.e("session_connected")
        self.titel_laeuft("t1")
        self.uhr.t += 60
        self.e("session_disconnected")
        self.uhr.t += 2
        self.e("track_changed", track_id="t2", uri="spotify:track:t2", duration_ms="200000")
        self.e("unavailable", track_id="t2")
        self.e("end_of_track", track_id="t2")
        self.uhr.t += 40
        self.assertFalse(self.r.am_ende())

    def test_nicht_abspielbarer_titel_ohne_trennung_ist_kein_ende(self):
        self.e("session_connected")
        self.titel_laeuft("t1")
        self.e("track_changed", track_id="t2", uri="spotify:track:t2", duration_ms="200000")
        self.e("unavailable", track_id="t2")
        self.e("end_of_track", track_id="t2")
        self.uhr.t += 15
        self.assertFalse(self.r.am_ende())

    def test_letzter_titel_lief_aus_ist_ende(self):
        self.e("session_connected")
        self.titel_laeuft("t9")
        self.uhr.t += 180
        self.e("end_of_track", track_id="t9")
        self.uhr.t += 15
        self.assertTrue(self.r.am_ende())

    def test_ende_nach_ueberstandener_stoerung_zaehlt_wieder(self):
        self.e("session_connected")
        self.e("session_disconnected")
        self.e("session_connected")
        self.uhr.t += rueckmeldung.STOERUNG_FENSTER_S + 1
        self.titel_laeuft("t9")
        self.uhr.t += 180
        self.e("end_of_track", track_id="t9")
        self.assertTrue(self.r.am_ende())

    def test_gestoppt_kurz_vor_titelende_ist_ende(self):
        self.e("session_connected")
        self.titel_laeuft("t9", dauer=100000)
        self.uhr.t += 95
        self.e("stopped", track_id="t9", position_ms="95000")
        self.assertTrue(self.r.am_ende())


class Ansage(unittest.TestCase):
    def test_musik_weg_hat_text(self):
        self.assertIn("musik_weg", toene.ANSAGEN)


if __name__ == "__main__":
    unittest.main()
