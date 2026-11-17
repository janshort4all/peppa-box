"""Titelfolge-Wache (17.11.2026): librespot 0.8.0 springt beim natürlichen Titelende manchmal 2–3 Titel
weiter (librespot #1848). Bei Hörspielen fehlen dann Kapitel.

Ablauf (vom Player jede Runde aufgerufen, nur lokal, kein Netz im Aufrufer-Faden):
  * Läuft eine Karte, wird ihre Titelliste im Hintergrund geholt (titelliste.py, gespeichert).
  * Meldet librespot einen NATÜRLICHEN Übergang (end_of_track des vorigen Titels, dann track_changed) und
    ist der neue Titel nicht der nächste der Liste, sondern ein späterer, bittet die Wache die Steuerung,
    den richtigen nächsten Titel zu spielen (Steuerung.titel_korrigieren; die prüft dort Zufallswiedergabe).
  * Tasten vor/zurück erzeugen keinen natürlichen Übergang und werden nie korrigiert. Rückwärtssprünge,
    Titel außerhalb der Liste und das Listenende bleiben unangetastet.
  * Höchstens KORREKTUR_MAX Korrekturen je KORREKTUR_FENSTER_S, damit nie ein Hin und Her entsteht.
"""
import time

import titelliste

KORREKTUR_MAX = 3
KORREKTUR_FENSTER_S = 600.0


class Titelfolge:
    def __init__(self, steuerung, rueck, listen, log=print, jetzt=time.monotonic):
        self.st, self.rueck, self.listen, self.log, self.jetzt = steuerung, rueck, listen, log, jetzt
        self._gesehen = 0               # Nummer des zuletzt ausgewerteten Übergangs
        self._karte = None
        self._korrekturen = []
        self._ohne_liste_gemeldet = set()

    def tick(self):
        ist = self.st.ist
        karte = ist[1] if ist and ist[0] in ("spielt", "startet") else None
        if karte and karte != self._karte:
            self.listen.im_hintergrund(karte)
            self._karte = karte
        u = self.rueck.uebergang
        if not u or u[0] == self._gesehen:
            return None
        self._gesehen = u[0]
        if not karte or ist[0] != "spielt":
            return None
        return self.pruefen(karte, u[1], u[2], u[3])

    def pruefen(self, karte, vorher, nachher, natuerlich):
        """Ein Übergang vorher -> nachher. Gibt den korrigierten Titel zurück oder None."""
        if not natuerlich or not vorher:
            return None
        liste = self.listen.liste(karte)
        if not liste:
            if karte not in self._ohne_liste_gemeldet:
                self._ohne_liste_gemeldet.add(karte)
                self.log(f"Titelfolge: keine Titelliste für {karte}, Übergänge werden nicht geprüft.")
            return None
        erwartet = titelliste.nachfolger(liste, vorher)
        if not erwartet or nachher in erwartet:
            return None
        i_vorher, i_nachher = titelliste.index(liste, vorher), titelliste.index(liste, nachher)
        if i_nachher is None or i_vorher is None or i_nachher <= i_vorher + 1:
            return None                             # rückwärts, unbekannt oder Wiederholung: nicht eingreifen
        ziel = liste[i_vorher + 1]
        t = self.jetzt()
        self._korrekturen = [k for k in self._korrekturen if t - k <= KORREKTUR_FENSTER_S]
        if len(self._korrekturen) >= KORREKTUR_MAX:
            self.log(f"Titelfolge: librespot hat wieder Titel übersprungen, schon {KORREKTUR_MAX} Korrekturen in "
                     f"{int(KORREKTUR_FENSTER_S // 60)} min – keine weitere.")
            return None
        self._korrekturen.append(t)
        self.log(f"Titelfolge: librespot sprang von Titel {i_vorher + 1} auf {i_nachher + 1} "
                 f"(übersprungen: {i_nachher - i_vorher - 1}) – zurück auf Titel {i_vorher + 2}.")
        self.st.titel_korrigieren(karte, ziel, i_vorher + 1)
        return ziel
