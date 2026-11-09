"""Wo war die Musik? Merkt sich je Karte (Spotify-Link der Karte) den Titel und die Stelle.

Wunsch Jan (09.11.2026): Nach einer Unterbrechung (Störung, Neustart von Raspotify oder des Players,
Box aus und wieder an, Karte kurz weg) darf es nicht von vorn losgehen. Die Steuerung startet eine
Karte darum an der gemerkten Stelle (Titel + Position, 3 s zurück, damit man wieder hineinfindet).
  Von vorn      Play-Feld 2 s halten, oder die Karte wurde zu Ende gehört (letzter Titel lief aus)
  Veraltet      Stellen älter als 30 Tage gelten nicht mehr
Quelle der Stelle: die Ereignisse von librespot (rueckmeldung.py: Titel, Position, spielt), sonst
die Abfrage bei Spotify während der Prüfung. Gespeichert in ~/.config/peppa-box/fortschritt.json,
höchstens alle 15 s (schont die SD-Karte) und sofort bei Titelwechsel oder Pause.
"""
import json
import os
import threading
import time

ZURUECK_MS = 3000
MAX_ALTER_S = 30 * 86400
SICHERN_S = 15.0
MAX_KARTEN = 200


def pfad():
    return os.path.join(os.path.expanduser("~/.config/peppa-box"), "fortschritt.json")


class Fortschritt:
    def __init__(self, datei=None, uhr=time.time, jetzt=time.monotonic, log=print):
        self.datei = datei or pfad()
        self.uhr, self.jetzt, self.log = uhr, jetzt, log
        self._sperre = threading.Lock()
        self._daten = self._laden()
        self._geaendert = False
        self._gesichert = -1e9

    def _laden(self):
        try:
            with open(self.datei, encoding="utf-8") as f:
                d = json.load(f)
            return {k: v for k, v in d.items() if isinstance(v, dict) and isinstance(v.get("titel"), str)}
        except (OSError, ValueError, AttributeError):
            return {}

    def merken(self, karte, titel, position_ms, sofort=False):
        """Stelle für die Karte merken (Titel-URI, Position in ms)."""
        if not karte or not titel or not str(titel).startswith("spotify:"):
            return
        with self._sperre:
            alt = self._daten.get(karte)
            neu = {"titel": titel, "position": int(max(0, position_ms or 0)), "zeit": int(self.uhr())}
            titel_neu = not alt or alt.get("titel") != titel
            self._daten[karte] = neu
            self._geaendert = True
        self.sichern(sofort=sofort or titel_neu)

    def stelle(self, karte):
        """{"titel": URI, "position_ms": ms} zum Weiterspielen, oder None (von vorn)."""
        with self._sperre:
            s = self._daten.get(karte)
        if not s or self.uhr() - s.get("zeit", 0) > MAX_ALTER_S:
            return None
        return {"titel": s["titel"], "position_ms": max(0, s["position"] - ZURUECK_MS)}

    def vergessen(self, karte):
        with self._sperre:
            if self._daten.pop(karte, None) is None:
                return
            self._geaendert = True
        self.sichern(sofort=True)

    def sichern(self, sofort=False):
        t = self.jetzt()
        with self._sperre:
            if not self._geaendert or (not sofort and t - self._gesichert < SICHERN_S):
                return
            neueste = sorted(self._daten.items(), key=lambda kv: kv[1].get("zeit", 0))[-MAX_KARTEN:]
            self._daten = dict(neueste)
            text = json.dumps(self._daten, ensure_ascii=False)
            self._geaendert, self._gesichert = False, t
        try:
            os.makedirs(os.path.dirname(self.datei), exist_ok=True)
            tmp = self.datei + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, self.datei)
        except OSError as e:
            self.log(f"Fortschritt nicht gespeichert: {e!r}")
