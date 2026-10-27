"""Einstellungen der Peppa Box (Lautstärke-Grenzen, Ruhezeit, Auto-Aus) und kleine Laufzeit-Dateien.

Gemeinsam genutzt vom Player (führt die Automatik aus) und von der Eltern-Seite (ändert die Werte).
Nur Standardbibliothek.

  Einstellungen   ~/.config/peppa-box/einstellungen.json   bleibt bei Updates und Neustarts erhalten,
                  liegt nur auf dem Pi (nicht im Repository)
  Laufzeit        /dev/shm/peppa-box-<name>.json            im Arbeitsspeicher (schont die SD-Karte),
                  nach einem Neustart der Box weg: Schlummer-Timer, "Ruhezeit ausgesetzt", Status

Für Tests lassen sich die Orte umlenken: HOME und PEPPA_LAUF_DIR.
"""
import datetime
import json
import os
import re
import time

LAUF = os.environ.get("PEPPA_LAUF_DIR", "/dev/shm")

AUSGABEN = ("kopfhoerer", "lautsprecher")

STANDARD = {
    # Höchstlautstärke und Startlautstärke je Ausgang, in Prozent des Reglers (wie alsamixer -M)
    "lautstaerke": {
        "kopfhoerer": {"max": 60, "start": 30},
        "lautsprecher": {"max": 70, "start": 40},
    },
    # Ruhezeit (Abendmodus): "leiser" = Lautstärke höchstens leise_max, "aus" = keine Musik
    "ruhezeit": {"an": False, "von": "19:30", "bis": "06:30", "modus": "leiser", "leise_max": 25},
    # Box ausschalten, wenn so lange nichts gespielt wird. Standard aus, damit sie nicht mitten in
    # einer Wartung (Update, Test) von selbst herunterfährt.
    "auto_aus": {"an": False, "minuten": 30},
}

MIN_LAUT = 5                                  # darunter ist die Box praktisch stumm
ZEIT = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_cache = {"mtime": None, "daten": None}


def pfad():
    return os.path.join(os.path.expanduser("~/.config/peppa-box"), "einstellungen.json")


# ---------------------------------------------------------------- Prüfen und Zusammenführen

def _ganzzahl(wert, name, lo, hi):
    if isinstance(wert, bool) or not isinstance(wert, (int, float)) or wert != int(wert):
        raise ValueError(f"{name}: ganze Zahl erwartet")
    wert = int(wert)
    if not lo <= wert <= hi:
        raise ValueError(f"{name}: erlaubt sind {lo} bis {hi}")
    return wert


def _zeit(wert, name):
    if not isinstance(wert, str) or not ZEIT.match(wert):
        raise ValueError(f"{name}: Uhrzeit im Format HH:MM erwartet")
    return wert


def _wahrheit(wert, name):
    if not isinstance(wert, bool):
        raise ValueError(f"{name}: an/aus erwartet")
    return wert


def bereinigen(neu, basis):
    """Legt die Änderungen `neu` (auch nur ein Teil) über `basis`, prüft alles und gibt das Ergebnis
    zurück. Wirft ValueError mit deutschem Text bei ungültigen Werten; `basis` bleibt unverändert."""
    if not isinstance(neu, dict):
        raise ValueError("Einstellungen: Objekt erwartet")
    erg = json.loads(json.dumps(basis))

    laut = neu.get("lautstaerke")
    if laut is not None:
        if not isinstance(laut, dict):
            raise ValueError("lautstaerke: Objekt erwartet")
        for aus, werte in laut.items():
            if aus not in AUSGABEN or not isinstance(werte, dict):
                raise ValueError(f"lautstaerke: unbekannter Ausgang '{aus}'")
            for k, v in werte.items():
                if k not in ("max", "start"):
                    raise ValueError(f"lautstaerke.{aus}: unbekannter Wert '{k}'")
                erg["lautstaerke"][aus][k] = _ganzzahl(v, f"Lautstärke {aus} {k}", MIN_LAUT, 100)
    for aus in AUSGABEN:                      # Start nie über dem Maximum
        z = erg["lautstaerke"][aus]
        z["start"] = min(z["start"], z["max"])

    ruhe = neu.get("ruhezeit")
    if ruhe is not None:
        if not isinstance(ruhe, dict):
            raise ValueError("ruhezeit: Objekt erwartet")
        for k, v in ruhe.items():
            if k == "an":
                erg["ruhezeit"]["an"] = _wahrheit(v, "Ruhezeit an")
            elif k in ("von", "bis"):
                erg["ruhezeit"][k] = _zeit(v, f"Ruhezeit {k}")
            elif k == "modus":
                if v not in ("leiser", "aus"):
                    raise ValueError("Ruhezeit modus: 'leiser' oder 'aus' erwartet")
                erg["ruhezeit"]["modus"] = v
            elif k == "leise_max":
                erg["ruhezeit"]["leise_max"] = _ganzzahl(v, "Ruhezeit leise_max", MIN_LAUT, 100)
            else:
                raise ValueError(f"ruhezeit: unbekannter Wert '{k}'")
    if erg["ruhezeit"]["von"] == erg["ruhezeit"]["bis"]:
        raise ValueError("Ruhezeit: Beginn und Ende dürfen nicht gleich sein")

    auto = neu.get("auto_aus")
    if auto is not None:
        if not isinstance(auto, dict):
            raise ValueError("auto_aus: Objekt erwartet")
        for k, v in auto.items():
            if k == "an":
                erg["auto_aus"]["an"] = _wahrheit(v, "Auto-Aus an")
            elif k == "minuten":
                erg["auto_aus"]["minuten"] = _ganzzahl(v, "Auto-Aus minuten", 5, 240)
            else:
                raise ValueError(f"auto_aus: unbekannter Wert '{k}'")

    unbekannt = set(neu) - {"lautstaerke", "ruhezeit", "auto_aus"}
    if unbekannt:
        raise ValueError("Unbekannte Einstellung: " + ", ".join(sorted(unbekannt)))
    return erg


# ---------------------------------------------------------------- Laden und Speichern

def laden():
    """Aktuelle Einstellungen. Fehlt die Datei oder ist sie kaputt, gelten die Standardwerte.
    Wird nur neu gelesen, wenn sich die Datei geändert hat (der Player fragt jede Sekunde)."""
    p = pfad()
    try:
        mtime = os.stat(p).st_mtime_ns
    except OSError:
        return json.loads(json.dumps(STANDARD))
    if _cache["mtime"] == mtime and _cache["daten"] is not None:
        return json.loads(json.dumps(_cache["daten"]))
    try:
        with open(p, encoding="utf-8") as f:
            daten = bereinigen(json.load(f), STANDARD)
    except (OSError, ValueError):
        daten = json.loads(json.dumps(STANDARD))
    _cache.update(mtime=mtime, daten=daten)
    return json.loads(json.dumps(daten))


def speichern(aenderung):
    """Prüft `aenderung` (auch nur ein Teil), führt sie mit den bisherigen Werten zusammen und
    schreibt die Datei. Gibt die gespeicherten Einstellungen zurück, wirft ValueError bei Fehlern."""
    neu = bereinigen(aenderung, laden())
    p = pfad()
    os.makedirs(os.path.dirname(p), mode=0o700, exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(neu, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)
    _cache["mtime"] = None
    return neu


# ---------------------------------------------------------------- Ruhezeit

def _minuten(text):
    h, m = text.split(":")
    return int(h) * 60 + int(m)


def in_ruhezeit(cfg, jetzt):
    """Liegt `jetzt` (Sekunden seit 1970) im Zeitfenster der Ruhezeit? Das Fenster darf über
    Mitternacht gehen (19:30 bis 06:30). Ignoriert, ob die Ruhezeit ein- oder ausgeschaltet ist."""
    r = cfg["ruhezeit"]
    t = datetime.datetime.fromtimestamp(jetzt)
    jetzt_min = t.hour * 60 + t.minute
    von, bis = _minuten(r["von"]), _minuten(r["bis"])
    if von < bis:
        return von <= jetzt_min < bis
    return jetzt_min >= von or jetzt_min < bis


def naechstes_ende(cfg, jetzt):
    """Zeitpunkt (Sekunden seit 1970), zu dem die Ruhezeit das nächste Mal endet."""
    h, m = cfg["ruhezeit"]["bis"].split(":")
    t = datetime.datetime.fromtimestamp(jetzt).replace(hour=int(h), minute=int(m), second=0, microsecond=0)
    if t.timestamp() <= jetzt:
        t += datetime.timedelta(days=1)
    return t.timestamp()


def ruhezeit_aktiv(cfg, jetzt):
    """Ist jetzt Ruhezeit? Nur wenn eingeschaltet, im Zeitfenster und nicht für heute ausgesetzt."""
    if not cfg["ruhezeit"]["an"] or not in_ruhezeit(cfg, jetzt):
        return False
    ausgesetzt = lauf_lesen("ruhe") or {}
    return jetzt >= ausgesetzt.get("bis", 0)


def wirksames_max(cfg, ausgang, jetzt):
    """Höchstlautstärke, die gerade gilt: Grenze des Ausgangs, in der Ruhezeit ('leiser') niedriger."""
    grenze = cfg["lautstaerke"][ausgang]["max"]
    if ruhezeit_aktiv(cfg, jetzt) and cfg["ruhezeit"]["modus"] == "leiser":
        grenze = min(grenze, cfg["ruhezeit"]["leise_max"])
    return grenze


def musik_gesperrt(cfg, jetzt):
    """Ruhezeit mit Modus 'aus': dann wird keine Musik gestartet und laufende Musik pausiert."""
    return ruhezeit_aktiv(cfg, jetzt) and cfg["ruhezeit"]["modus"] == "aus"


# ---------------------------------------------------------------- Laufzeit-Dateien

def lauf_pfad(name):
    return os.path.join(LAUF, f"peppa-box-{name}.json")


def lauf_lesen(name):
    try:
        with open(lauf_pfad(name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def lauf_schreiben(name, daten):
    p = lauf_pfad(name)
    try:
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False)
        os.replace(tmp, p)
    except OSError:
        pass


def lauf_loeschen(name):
    try:
        os.remove(lauf_pfad(name))
    except OSError:
        pass


def lauf_alter(name, jetzt=None):
    """Sekunden seit der letzten Änderung der Laufzeit-Datei, None wenn es sie nicht gibt.
    `jetzt` nur für Tests mit simulierter Uhr."""
    try:
        return max(0.0, (time.time() if jetzt is None else jetzt) - os.stat(lauf_pfad(name)).st_mtime)
    except OSError:
        return None


def lauf_beruehren(name):
    """Legt die Laufzeit-Datei an oder setzt ihre Zeit auf jetzt (z. B. 'Eltern-Seite ist offen')."""
    p = lauf_pfad(name)
    try:
        with open(p, "a"):
            os.utime(p)
    except OSError:
        pass
