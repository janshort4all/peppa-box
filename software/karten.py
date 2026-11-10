"""Kartenverwaltung der Peppa Box: welche Karte spielt was, Titel und Cover, Auftrag "Karte bespielen".

Dateien nur auf dem Pi (nicht im Repository), Ordner ~/.config/peppa-box/:
  karten.json          Karten der Box: Kartennummer -> Spotify-Adresse (uri), Titel, Zeitpunkt, Etikett gedruckt?
  cover/<schluessel>.jpg + .json   Cover und Titel je Spotify-Adresse (schluessel = z. B. playlist_37i9dQZF...)

Die Zuordnung Kartennummer -> Spotify-Adresse gilt zusätzlich zum Link auf der Karte: Hat eine Karte
keinen (lesbaren) Link, nimmt der Player die Adresse aus karten.json. So funktioniert jede Karte, auch
eine, die sich nicht beschreiben lässt (z. B. MIFARE Classic oder schreibgeschützt).

Player (liest karten.json, führt Bespielen-Aufträge aus) und Eltern-Seite (verwaltet, holt Cover) benutzen
dieses Modul gemeinsam; Schreibzugriffe laufen unter einer Dateisperre und ersetzen die Datei atomar.
Nur Standardbibliothek.
"""
import fcntl
import json
import os
import re
import secrets
import time

import einstellungen

AUFTRAG_S = 120                     # so lange wartet ein Bespielen-Auftrag auf eine Karte
SCHLUESSEL = re.compile(r"^(playlist|album|show|episode|track|artist)_[A-Za-z0-9]{8,40}$")
URI = re.compile(r"^spotify:(playlist|album|show|episode|track|artist):([A-Za-z0-9]{8,40})$")
UID_URL = re.compile(r"^[0-9A-Fa-f]{8,20}$")


def ordner():
    return os.path.join(os.path.expanduser("~/.config/peppa-box"))


def _datei():
    return os.path.join(ordner(), "karten.json")


def cover_ordner():
    return os.path.join(ordner(), "cover")


# ---------------------------------------------------------------- Adressen

def uri_pruefen(uri):
    m = URI.match(uri or "")
    if not m:
        raise ValueError("Keine gültige Spotify-Adresse: " + str(uri))
    return m.group(1), m.group(2)


def schluessel(uri):
    typ, nr = uri_pruefen(uri)
    return f"{typ}_{nr}"


def uri_aus_schluessel(s):
    if not SCHLUESSEL.match(s or ""):
        raise ValueError("Ungültiger Schlüssel")
    typ, nr = s.split("_", 1)
    return f"spotify:{typ}:{nr}"


def uri_zu_link(uri):
    typ, nr = uri_pruefen(uri)
    return f"https://open.spotify.com/{typ}/{nr}"


def uid_zu_url(uid):
    return uid.replace(":", "").lower()


def uid_aus_url(text):
    """'1981152 0' -> '19:81:15:20'; wirft ValueError bei Unsinn."""
    if not UID_URL.match(text or "") or len(text) % 2:
        raise ValueError("Ungültige Kartennummer")
    t = text.upper()
    return ":".join(t[i:i + 2] for i in range(0, len(t), 2))


# ---------------------------------------------------------------- karten.json

class _Sperre:
    def __enter__(self):
        os.makedirs(ordner(), mode=0o700, exist_ok=True)
        self.f = open(os.path.join(ordner(), "karten.lock"), "a")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, *a):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


_cache = {"mtime": None, "daten": None}


def laden():
    """{uid: eintrag}; fehlt die Datei oder ist sie kaputt, ist die Liste leer. Wird nur bei Änderung neu gelesen."""
    p = _datei()
    try:
        mtime = os.stat(p).st_mtime_ns
    except OSError:
        return {}
    if _cache["mtime"] == mtime and _cache["daten"] is not None:
        return json.loads(json.dumps(_cache["daten"]))
    try:
        with open(p, encoding="utf-8") as f:
            roh = json.load(f).get("karten", {})
        daten = {u: e for u, e in roh.items() if isinstance(e, dict) and URI.match(str(e.get("uri", "")))}
    except (OSError, ValueError, AttributeError):
        daten = {}
    _cache.update(mtime=mtime, daten=daten)
    return json.loads(json.dumps(daten))


def _schreiben(daten):
    p = _datei()
    os.makedirs(os.path.dirname(p), mode=0o700, exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"karten": daten}, f, indent=1, ensure_ascii=False)
    os.replace(tmp, p)
    _cache["mtime"] = None


def link_fuer_uid(uid):
    """Link (open.spotify.com) der Karte laut Box, None wenn die Box die Karte nicht kennt. Für den Player."""
    e = laden().get(uid)
    return uri_zu_link(e["uri"]) if e else None


def eintragen(uid, uri, titel=None, auf_karte=None, typ=None, jetzt=None):
    """Karte der Box bekannt machen oder ändern. Etikett-Status bleibt, wenn sich die Adresse nicht ändert."""
    uri_pruefen(uri)
    with _Sperre():
        daten = laden()
        alt = daten.get(uid) or {}
        neu = {"uri": uri, "angelegt": alt.get("angelegt") or int(jetzt or time.time()),
               "gedruckt": bool(alt.get("gedruckt")) and alt.get("uri") == uri}
        if titel or alt.get("titel"):
            neu["titel"] = titel or alt.get("titel")
        for k, v in (("auf_karte", auf_karte), ("typ", typ)):
            if v is not None:
                neu[k] = v
            elif k in alt:
                neu[k] = alt[k]
        daten[uid] = neu
        _schreiben(daten)
    return neu


def entfernen(uid):
    with _Sperre():
        daten = laden()
        ok = daten.pop(uid, None) is not None
        if ok:
            _schreiben(daten)
    return ok


def umbenennen(uid, titel):
    titel = (titel or "").strip()[:80]
    with _Sperre():
        daten = laden()
        if uid not in daten:
            return False
        if titel:
            daten[uid]["titel"] = titel
        else:
            daten[uid].pop("titel", None)
        _schreiben(daten)
    return True


def gedruckt_setzen(uids, wert):
    with _Sperre():
        daten = laden()
        for u in uids:
            if u in daten:
                daten[u]["gedruckt"] = bool(wert)
        _schreiben(daten)


# ---------------------------------------------------------------- Cover und Titel je Adresse

def _meta_pfad(uri):
    return os.path.join(cover_ordner(), schluessel(uri) + ".json")


def cover_pfad(uri):
    return os.path.join(cover_ordner(), schluessel(uri) + ".jpg")


def meta_lesen(uri):
    """{'titel', 'quelle', 'eigen', 'hat_cover'} oder None, wenn noch nie gesucht wurde."""
    try:
        with open(_meta_pfad(uri), encoding="utf-8") as f:
            m = json.load(f)
    except (OSError, ValueError):
        return None
    m["hat_cover"] = os.path.isfile(cover_pfad(uri))
    return m


def meta_schreiben(uri, titel=None, bild=None, quelle=None, eigen=False):
    """Titel und/oder Cover (JPEG-Bytes) einer Adresse speichern. Ein eigenes Bild (eigen=True) wird von
    einer späteren Suche nie überschrieben (siehe cover.py)."""
    os.makedirs(cover_ordner(), mode=0o700, exist_ok=True)
    alt = meta_lesen(uri) or {}
    if bild is not None:
        tmp = cover_pfad(uri) + ".tmp"
        with open(tmp, "wb") as f:
            f.write(bild)
        os.replace(tmp, cover_pfad(uri))
    meta = {"titel": titel or alt.get("titel"), "quelle": quelle or alt.get("quelle"),
            "eigen": bool(eigen or (alt.get("eigen") and bild is None)), "zeit": int(time.time())}
    tmp = _meta_pfad(uri) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    os.replace(tmp, _meta_pfad(uri))
    return meta_lesen(uri)


def cover_bytes(uri):
    try:
        with open(cover_pfad(uri), "rb") as f:
            return f.read()
    except OSError:
        return None


def liste():
    """Alle Karten für die Eltern-Seite, neueste zuerst."""
    erg = []
    for uid, e in laden().items():
        m = meta_lesen(e["uri"]) or {}
        erg.append({"uid": uid, "id": uid_zu_url(uid), "uri": e["uri"], "link": uri_zu_link(e["uri"]),
                    "typ": e["uri"].split(":")[1], "titel": e.get("titel") or m.get("titel") or "Ohne Namen",
                    "eigener_titel": bool(e.get("titel")), "schluessel": schluessel(e["uri"]),
                    "hat_cover": bool(m.get("hat_cover")), "gedruckt": bool(e.get("gedruckt")),
                    "auf_karte": e.get("auf_karte"), "angelegt": e.get("angelegt", 0)})
    erg.sort(key=lambda k: (-k["angelegt"], k["uid"]))
    return erg


# ---------------------------------------------------------------- Auftrag "Karte bespielen"
# Die Eltern-Seite stellt den Auftrag (Datei im Arbeitsspeicher), der Player führt ihn aus, sobald eine
# Karte im Kartenfach liegt, und meldet das Ergebnis zurück.

def auftrag_stellen(uri, ueberschreiben=False, jetzt=None):
    uri_pruefen(uri)
    a = {"id": secrets.token_hex(4), "uri": uri, "link": uri_zu_link(uri),
         "ueberschreiben": bool(ueberschreiben), "zeit": jetzt or time.time()}
    einstellungen.lauf_loeschen("beschreiben-ergebnis")
    einstellungen.lauf_schreiben("beschreiben", a)
    return a


def auftrag_offen(jetzt=None):
    """Der Auftrag, den der Player gerade ausführen soll (None = keiner, abgelaufen oder erledigt)."""
    a = einstellungen.lauf_lesen("beschreiben")
    if not a:
        return None
    if (jetzt or time.time()) - a.get("zeit", 0) > AUFTRAG_S:
        return None
    e = einstellungen.lauf_lesen("beschreiben-ergebnis")
    if e and e.get("id") == a.get("id"):
        return None
    return a


def auftrag_ergebnis(auftrag, **daten):
    """Der Player meldet: erledigt (status fertig), belegt, oder Fehler."""
    einstellungen.lauf_schreiben("beschreiben-ergebnis", dict(daten, id=auftrag["id"], zeit=time.time()))


def auftrag_abbrechen():
    einstellungen.lauf_loeschen("beschreiben")
    einstellungen.lauf_loeschen("beschreiben-ergebnis")


def auftrag_status(jetzt=None):
    """Für die Eltern-Seite: {'status': 'keiner'|'wartet'|'fertig'|'belegt'|'fehler'|'abgelaufen', ...}."""
    a = einstellungen.lauf_lesen("beschreiben")
    if not a:
        return {"status": "keiner"}
    e = einstellungen.lauf_lesen("beschreiben-ergebnis")
    if e and e.get("id") == a.get("id"):
        return dict(e, uri=a["uri"], auftrag=a["id"])
    rest = AUFTRAG_S - ((jetzt or time.time()) - a.get("zeit", 0))
    if rest <= 0:
        return {"status": "abgelaufen", "uri": a["uri"], "auftrag": a["id"],
                "meldung": "Die Zeit ist abgelaufen. Es wurde keine Karte bespielt."}
    return {"status": "wartet", "uri": a["uri"], "auftrag": a["id"], "rest_s": int(rest)}
