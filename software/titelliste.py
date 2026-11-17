"""Titelliste einer Karte (Playlist, Album, Podcast, Hörbuch) für die Titelfolge-Wache (17.11.2026).

Wozu: librespot 0.8.0 springt beim natürlichen Titelende manchmal 2–3 Titel weiter (librespot #1848), und
der Start an der gemerkten Stelle landet manchmal auf einem anderen Titel ("using fallback index"). Um das
zu erkennen und zu korrigieren, braucht die Box die Reihenfolge der Titel.

Quellen (Spotify Web API, Stand Februar-2026-Änderungen für Apps im Entwicklungsmodus):
  album      GET /albums/{id}/tracks
  playlist   GET /playlists/{id}/items  (nur eigene oder gemeinsame Playlists; sonst kein Inhalt -> None)
  show       GET /shows/{id}/episodes
  audiobook  GET /audiobooks/{id}/chapters
Die Listen werden im Speicher und in ~/.config/peppa-box/titellisten.json gehalten (24 h gültig, ein
Fehlschlag 6 h), damit die Box Spotify nicht mit Anfragen belastet (Kontingent im Entwicklungsmodus).
Ohne Liste prüft die Box die Titelfolge nicht (keine Korrektur, nur eine Protokollzeile je Karte).
"""
import json
import os
import threading
import time

GUELTIG_S = 24 * 3600
FEHLER_GUELTIG_S = 6 * 3600
SEITEN_MAX = 40                     # höchstens 40 × 50 = 2000 Titel
PFADE = {"album": "/albums/{}/tracks", "playlist": "/playlists/{}/items", "show": "/shows/{}/episodes",
         "audiobook": "/audiobooks/{}/chapters"}


def datei():
    return os.path.join(os.path.expanduser("~/.config/peppa-box"), "titellisten.json")


def _uri_aus(eintrag):
    """URI aus einem Eintrag der Antwort (Album/Show/Kapitel: direkt; Playlist: item bzw. früher track)."""
    if not isinstance(eintrag, dict):
        return None
    for feld in ("item", "track"):
        innen = eintrag.get(feld)
        if isinstance(innen, dict) and innen.get("uri"):
            return innen["uri"]
    return eintrag.get("uri")


class Titellisten:
    def __init__(self, api=None, pfad=None, uhr=time.time, log=print):
        self.api, self.uhr, self.log = api, uhr, log
        self.pfad = pfad if pfad is not None else datei()
        self._sperre = threading.Lock()
        self._laeuft = set()
        self._daten = self._laden()

    def _laden(self):
        try:
            with open(self.pfad) as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def _sichern(self):
        if not self.pfad:
            return
        try:
            os.makedirs(os.path.dirname(self.pfad), exist_ok=True)
            tmp = self.pfad + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self._daten, f)
            os.replace(tmp, self.pfad)
        except OSError as e:
            self.log(f"Titellisten nicht gespeichert: {e!r}")

    def liste(self, uri):
        """Gespeicherte Liste (nur Speicher, ohne Netz): [uri, …] oder None."""
        with self._sperre:
            e = self._daten.get(uri)
        return list(e["titel"]) if e and e.get("titel") else None

    def _frisch(self, uri):
        e = self._daten.get(uri)
        if not e:
            return False
        alter = self.uhr() - e.get("zeit", 0)
        return alter < (GUELTIG_S if e.get("titel") else FEHLER_GUELTIG_S)

    def holen(self, uri):
        """Liste von Spotify holen (blockiert), wenn keine frische gespeichert ist. Liefert [uri, …] oder None."""
        teile = uri.split(":")
        if len(teile) != 3 or teile[1] not in PFADE or self.api is None:
            return None
        with self._sperre:
            if self._frisch(uri):
                e = self._daten[uri]
                return list(e["titel"]) if e.get("titel") else None
        titel, grund = [], None
        params = {"limit": 50, "offset": 0}
        for _ in range(SEITEN_MAX):
            status, d = self.api("GET", PFADE[teile[1]].format(teile[2]), params=params)
            if status != 200 or not isinstance(d, dict):
                grund = f"Spotify {status}"
                break
            items = d.get("items")
            if not isinstance(items, list):
                grund = "kein Inhalt"
                break
            titel += [u for u in (_uri_aus(x) for x in items) if u]
            if not d.get("next"):
                break
            params = dict(params, offset=params["offset"] + 50)
        if grund or not titel:
            self.log(f"Titelliste für {uri} nicht verfügbar ({grund or 'leer'}) – Titelfolge wird nicht geprüft.")
            titel = []
        with self._sperre:
            self._daten[uri] = {"zeit": self.uhr(), "titel": titel}
            self._sichern()
        return titel or None

    def im_hintergrund(self, uri):
        """holen() in einem eigenen Faden (die Steuerung darf nie auf Spotify warten)."""
        with self._sperre:
            if uri in self._laeuft or self._frisch(uri):
                return
            self._laeuft.add(uri)

        def lauf():
            try:
                self.holen(uri)
            except Exception as e:
                self.log(f"Titelliste für {uri}: {e!r}")
            finally:
                with self._sperre:
                    self._laeuft.discard(uri)
        threading.Thread(target=lauf, name="titelliste", daemon=True).start()


def nachfolger(liste, titel):
    """Mögliche nächste Titel nach `titel` (bei doppelten Einträgen mehrere). None: Titel nicht in der Liste."""
    stellen = [i for i, u in enumerate(liste) if u == titel]
    if not stellen:
        return None
    return {liste[i + 1] for i in stellen if i + 1 < len(liste)}


def index(liste, titel):
    try:
        return liste.index(titel)
    except ValueError:
        return None
