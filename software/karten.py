"""Zuordnung Karte -> Spotify. Liegt auf dem Pi unter ~/.config/peppa-box/karten.json (nicht im Repository)."""
import json
import os

DATEI = os.path.expanduser("~/.config/peppa-box/karten.json")


def laden():
    try:
        with open(DATEI) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def speichern(karten):
    os.makedirs(os.path.dirname(DATEI), mode=0o700, exist_ok=True)
    tmp = DATEI + ".tmp"
    with open(tmp, "w") as f:
        json.dump(karten, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATEI)
