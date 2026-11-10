#!/usr/bin/env python3
"""Peppa Box – Eltern-Seite: Zustand ansehen, Lautstärke und Zeiten einstellen, Musik/Box neu starten,
ausschalten, Software-Update von GitHub, Bedienelemente live prüfen und einstellen, Ansagen anhören.

Laeuft als eigener Dienst peppa-web (nicht im Player), damit Updates und Neustarts des Players
die Seite nicht mitreissen. Port 8080, zusaetzlich Port 80, wenn erlaubt (systemd gibt das Recht).
Nur Standardbibliothek. Kein Passwort: jeder im selben Netz kann die Seite bedienen.

Rechte: Ausschalten, Neustart und Dienst-Neustarts laufen ueber sudo, freigegeben nur fuer genau
diese Befehle in /etc/sudoers.d/peppa-box (richtet dienst_einrichten.sh ein).

Start von Hand:     python3 ~/peppa-box/software/peppa_web.py
Probelauf ohne Wirkung (sudo-Befehle werden nur angezeigt):  PEPPA_WEB_TROCKEN=1 python3 peppa_web.py
"""
import datetime
import glob
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import akku
import automatik
import bedienung
import cover
import einstellungen
import etikett
import karten
import klang
import lautstaerke
import toene

ORDNER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ORDNER)
WEB = os.path.join(ORDNER, "web")
STATUS_DATEI = einstellungen.lauf_pfad("status")           # schreibt der Player jede Sekunde
BEDIENUNG_DATEI = einstellungen.lauf_pfad("bedienung")     # Bedienelemente live (Player, bis 5 × je Sekunde)
EINRICHTUNG = {"software/dienst_einrichten.sh", "software/lautsprecher_einrichten.sh",
               "software/bedienung_einrichten.sh", "software/peppa_ausgang.sh",
               "software/ausgabe.py", "software/ereignis.py"}     # die beiden laufen als installierte Kopie
HELFER = "/usr/local/sbin/peppa-ausgang"
DIENSTE = ("peppa-player", "peppa-web", "raspotify", "peppa-stille")
KONFIG = os.path.expanduser("~/.config/peppa-box")
VORHER_DATEI = os.path.join(KONFIG, "vorherige_version.txt")
TROCKEN = os.environ.get("PEPPA_WEB_TROCKEN") == "1"
PORTS = [int(p) for p in os.environ.get("PEPPA_WEB_PORTS", "8080,80").split(",")]
SYSTEMCTL = shutil.which("systemctl") or "/usr/bin/systemctl"

SPERRE = threading.Lock()          # immer nur eine Aktion (Update, Neustart ...) gleichzeitig

DATEITYPEN = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
              ".css": "text/css; charset=utf-8", ".webmanifest": "application/manifest+json",
              ".png": "image/png", ".svg": "image/svg+xml"}
BILD_MAX = 8_000_000               # größtes Bild, das die Seite als eigenes Cover annimmt (Bytes)
COVER_PAUSE_S = 300                # gleiche Adresse: höchstens alle 5 Minuten neu im Netz suchen
_COVER_LAEUFT, _COVER_VERSUCH, _COVER_SPERRE = set(), {}, threading.Lock()


def log(text):
    print(time.strftime("%H:%M:%S"), text, flush=True)


def befehl(args, zeit=15, cwd=None):
    """Fuehrt einen Befehl aus. Gibt (Rueckgabewert, Ausgabe) zurueck, wirft nie."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=zeit, cwd=cwd)
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return 127, f"{args[0]} nicht gefunden"
    except subprocess.TimeoutExpired:
        return 124, "Zeitüberschreitung"


def git(*args, zeit=20):
    return befehl(["git", *args], zeit=zeit, cwd=REPO)


def mit_root(*args):
    """Freigegebene Befehle mit sudo (ohne Passwortabfrage, -n). Im Probelauf nur anzeigen."""
    if TROCKEN:
        log("PROBELAUF, nicht ausgefuehrt: sudo " + " ".join(args))
        return 0, "Probelauf"
    return befehl(["sudo", "-n", *args], zeit=60)


def selbst_neu_starten(nach=1.5):
    """Beendet diesen Prozess kurz nach der Antwort; systemd (Restart=always) startet ihn neu."""
    if TROCKEN:
        log("PROBELAUF: Seite wuerde jetzt neu starten")
        return
    threading.Timer(nach, lambda: os._exit(0)).start()


# ---------------------------------------------------------------- Zustand

def lies(pfad, standard=None):
    try:
        with open(pfad) as f:
            return f.read().strip()
    except OSError:
        return standard


def player_zustand():
    try:
        with open(STATUS_DATEI) as f:
            z = json.load(f)
    except (OSError, ValueError):
        return {"laeuft": False}
    z["laeuft"] = time.time() - z.get("zeit", 0) < 10
    return z


def bedienung_live():
    """Bedienelemente (Touch, Drehknopf, Ein-Taste, Kopfhörer), vom Player geschrieben."""
    try:
        with open(BEDIENUNG_DATEI) as f:
            b = json.load(f)
    except (OSError, ValueError):
        return {"laeuft": False}
    b["laeuft"] = time.time() - b.get("zeit", 0) < 5
    return b


def akku_zustand(p):
    """Akku bevorzugt vom Player (liest alle 15 s, ohne der Ein-Taste an SCL in die Quere zu kommen).
    Läuft der Player nicht, liest die Seite selbst."""
    a = p.get("akku") if p.get("laeuft") else None
    if isinstance(a, dict) and not a.get("fehler"):
        return a
    return akku.lesen()


def wlan():
    erg = {"name": None, "dbm": None}
    for zeile in (lies("/proc/net/wireless", "") or "").splitlines()[2:]:
        teile = zeile.split()
        if teile and teile[0].rstrip(":") == "wlan0" and len(teile) > 3:
            try:
                erg["dbm"] = int(float(teile[3]))
            except ValueError:
                pass
    code, aus = befehl(["nmcli", "-t", "-g", "GENERAL.CONNECTION", "device", "show", "wlan0"], zeit=5)
    if code == 0 and aus:
        erg["name"] = aus.splitlines()[0]
    else:
        code, aus = befehl(["iwgetid", "-r"], zeit=5)
        if code == 0 and aus:
            erg["name"] = aus
    return erg


def stromversorgung():
    """vcgencmd get_throttled: Bit 0 Unterspannung jetzt, Bit 16 seit dem Start aufgetreten."""
    code, aus = befehl(["vcgencmd", "get_throttled"], zeit=5)
    if code != 0 or "=" not in aus:
        return {"bekannt": False}
    try:
        wert = int(aus.split("=")[1], 16)
    except ValueError:
        return {"bekannt": False}
    return {"bekannt": True, "jetzt": bool(wert & 0x1), "seit_start": bool(wert & 0x10000),
            "gedrosselt": bool(wert & 0x4)}


def dienste():
    erg = {}
    for name in ("peppa-player", "raspotify", "peppa-stille"):
        _, aus = befehl([SYSTEMCTL, "is-active", name], zeit=5)
        erg[name] = aus.splitlines()[0] if aus else "unbekannt"
    return erg


def version():
    code, aus = git("log", "-1", "--format=%h%x1f%cI%x1f%s")
    if code != 0:
        return {"fehler": aus}
    kurz, datum, text = aus.split("\x1f")
    return {"kurz": kurz, "datum": datum, "text": text,
            "vorherige": vorherige_version() is not None}


def vorherige_version():
    sha = lies(VORHER_DATEI)
    if sha and git("cat-file", "-e", sha + "^{commit}")[0] == 0:
        return sha
    return None


def box_uhr():
    """Uhrzeit der Box und Zeitzone. Die Ruhezeit richtet sich danach, deshalb zeigt die Seite sie an."""
    jetzt = datetime.datetime.now().astimezone()
    zone = (lies("/etc/timezone") or "").strip() or jetzt.tzname()
    return {"uhrzeit": jetzt.strftime("%H:%M"), "zone": zone}


def lautstaerke_info(cfg, jetzt):
    aus = lautstaerke.aktive_ausgabe()
    return {
        "aktiv": aus, "name": lautstaerke.NAMEN[aus],
        "prozent": lautstaerke.lesen(aus),
        "max": einstellungen.wirksames_max(cfg, aus, jetzt),         # gilt gerade (Ruhezeit eingerechnet)
        "max_ausgang": cfg["lautstaerke"][aus]["max"],
        "ausgaben": {a: {"name": lautstaerke.NAMEN[a], "eingerichtet": lautstaerke.eingerichtet(a)}
                     for a in einstellungen.AUSGABEN},
    }


def zeiten_info(cfg, jetzt):
    t = einstellungen.lauf_lesen("timer")
    r = cfg["ruhezeit"]
    im_fenster = einstellungen.in_ruhezeit(cfg, jetzt)
    aktiv = einstellungen.ruhezeit_aktiv(cfg, jetzt)
    return {
        "timer": {"rest_s": max(0, int(t["ende"] - jetzt)), "minuten": t.get("minuten")} if t else None,
        "ruhezeit": dict(r, aktiv=aktiv, ausgesetzt=r["an"] and im_fenster and not aktiv),
        "auto_aus": cfg["auto_aus"],
        "box": box_uhr(),
    }


def zustand():
    cfg, jetzt = einstellungen.laden(), time.time()
    temp = lies("/sys/class/thermal/thermal_zone0/temp")
    platte = shutil.disk_usage("/")
    p = player_zustand()
    mem = {}
    for zeile in (lies("/proc/meminfo", "") or "").splitlines():
        k, _, v = zeile.partition(":")
        mem[k] = int(v.split()[0]) if v.split() else 0
    return {
        "rechner": socket.gethostname(),
        "player": p,
        "dienste": dienste(),
        "akku": akku_zustand(p),
        "wlan": wlan(),
        "temperatur": round(int(temp) / 1000, 1) if temp else None,
        "speicher_frei_gb": round(platte.free / 1e9, 1),
        "speicher_gesamt_gb": round(platte.total / 1e9, 1),
        "ram_frei_mb": round(mem.get("MemAvailable", 0) / 1024) if mem else None,
        "laufzeit_s": int(float((lies("/proc/uptime", "0") or "0").split()[0])),
        "strom": stromversorgung(),
        "version": version(),
        "lautstaerke": lautstaerke_info(cfg, jetzt),
        "zeiten": zeiten_info(cfg, jetzt),
        "probelauf": TROCKEN,
    }


def meldungen():
    code, aus = befehl(["journalctl", "-u", "peppa-player", "-u", "peppa-web", "-u", "raspotify",
                        "-u", "peppa-stille", "-n", "100",
                        "--no-pager", "-o", "short-iso"], zeit=10)
    return {"ok": code == 0, "text": aus}


def _journal(*extra, n):
    args = ["journalctl", "--no-pager", "-o", "short-iso", "-n", str(n), *extra]
    for d in DIENSTE:
        args += ["-u", d]
    return befehl(args, zeit=15)[1]


def _ausgabe_jetzt():
    """Welche Soundkarte gerade wirklich spielt (Kernel-Sicht)."""
    zeilen = []
    for pfad in sorted(glob.glob("/proc/asound/card*/pcm0p/sub0/status")):
        karte = pfad.split("/")[3]
        try:
            with open(os.path.join("/proc/asound", karte, "id")) as f:
                name = f.read().strip()
            with open(pfad) as f:
                inhalt = f.read().strip().splitlines()
        except OSError:
            continue
        zeilen.append(f"{name}: " + (", ".join(z.strip() for z in inhalt[:2]) if inhalt else "?"))
    return "\n".join(zeilen) or "(keine Angaben)"


def klang_info():
    rasp = player_zustand().get("raspotify") or {}
    fehler = [f for f in rasp.get("fehler") or [] if str(f).startswith("klang")]
    return {"da": klang.eingerichtet(), "baender": einstellungen.laden()["klang"]["baender"],
            "namen": list(klang.BAENDER), "min": klang.MIN_DB, "max": klang.MAX_DB, "vorlagen": klang.VORLAGEN,
            "fehler": fehler[-1] if fehler else None}


def klang_setzen(daten):
    """Equalizer einstellen: {"baender": [10 × dB]} oder {"vorlage": "klein"}; speichern und sofort anwenden."""
    if isinstance(daten, dict) and daten.get("vorlage") is not None:
        if daten["vorlage"] not in klang.VORLAGEN:
            return {"ok": False, "meldung": "Unbekannte Vorlage."}
        baender = klang.VORLAGEN[daten["vorlage"]]
    else:
        baender = daten.get("baender") if isinstance(daten, dict) else None
    try:
        cfg = einstellungen.speichern({"klang": {"baender": baender}})
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    if TROCKEN:
        return {"ok": True, "meldung": "Probelauf.", "baender": cfg["klang"]["baender"]}
    ok = klang.anwenden(cfg["klang"]["baender"], log=log)
    return {"ok": ok, "baender": cfg["klang"]["baender"],
            "meldung": "Klang eingestellt." if ok else "Gespeichert, aber der Equalizer ist nicht eingerichtet "
                                                      "(einmal dienst_einrichten.sh ausführen)."}


def diagnose():
    """Alles, was für die Fehlersuche zählt, auf einer Seite (nur lesen, ändert nichts)."""
    teile = []

    def abschnitt(titel, holen):
        try:
            text = holen()
        except Exception as e:                      # ein kaputter Abschnitt darf die Diagnose nicht verhindern
            text = f"(Fehler: {e!r})"
        teile.append(f"== {titel} ==\n{(text or '').strip() or '(leer)'}")

    def vorheriger_lauf():
        text = _journal("-b", "-1", n=200)
        if any(t in text.lower() for t in ("-- no entries --", "no journal", "no persistent journal")):
            return "(keins: das Protokoll überstand den Neustart nicht; mit dem neuen dienst_einrichten.sh schon)"
        return text

    def player():
        z = player_zustand()
        return json.dumps({k: z.get(k) for k in ("laeuft", "karte", "spotify_bereit", "problem", "ausgang",
                                                 "raspotify", "leser")}, ensure_ascii=False, indent=1)

    abschnitt("Version", lambda: " ".join(str(x) for x in version().values()))
    abschnitt("Dienste", lambda: befehl([SYSTEMCTL, "show", "-p",
                                         "Id,ActiveState,SubState,NRestarts,ActiveEnterTimestamp", *DIENSTE], zeit=10)[1])
    abschnitt("Tonweg (Helfer)", lambda: mit_root(HELFER, "zeigen")[1]
              + "\n(relais = Kopfhörer ohne Raspotify-Neustart)")
    abschnitt("Player", player)
    abschnitt("Soundkarten", lambda: _lesen("/proc/asound/cards"))
    abschnitt("Ausgabe gerade (Kernel)", _ausgabe_jetzt)
    abschnitt("Kopfhörer-Regler", lambda: befehl(["amixer", "-c", "Headphones", "sget", "PCM"], zeit=5)[1])
    abschnitt("Verstärker SD (P16)", lambda: befehl(["pinctrl", "get", "16"], zeit=5)[1])
    abschnitt("Protokoll seit dem Einschalten", lambda: _journal("-b", n=300))
    abschnitt("Protokoll vom vorigen Lauf", vorheriger_lauf)
    return {"ok": True, "text": "\n\n".join(teile)}


def _lesen(pfad):
    try:
        with open(pfad) as f:
            return f.read()
    except OSError as e:
        return repr(e)


# ---------------------------------------------------------------- Karten, Cover, Etiketten

def cover_im_hintergrund(uri):
    """Cover und Titel im Hintergrund holen, ohne die Seite warten zu lassen. Dieselbe Adresse wird
    höchstens alle COVER_PAUSE_S Sekunden gesucht (kein Dauerfeuer bei Fehlern)."""
    jetzt = time.time()
    with _COVER_SPERRE:
        if uri in _COVER_LAEUFT or jetzt - _COVER_VERSUCH.get(uri, 0) < COVER_PAUSE_S:
            return False
        _COVER_LAEUFT.add(uri)
        _COVER_VERSUCH[uri] = jetzt

    def lauf():
        try:
            cover.nachschlagen(uri)
        except Exception as e:                      # Netzfehler dürfen nie bis zur Seite durchschlagen
            log(f"Cover für {uri}: {e!r}")
        finally:
            with _COVER_SPERRE:
                _COVER_LAEUFT.discard(uri)

    threading.Thread(target=lauf, daemon=True).start()
    return True


def _cover_url(uri, meta):
    if not meta or not meta.get("hat_cover"):
        return None
    return f"/cover/{karten.schluessel(uri)}.jpg?v={meta.get('zeit', 0)}"


def kartendaten(z):
    """Die Karte im Kartenfach für die Eltern-Seite: Titel, Cover, ob die Box sie kennt.
    Eine Karte mit lesbarem Spotify-Link, die die Box noch nicht kennt, wird dabei gleich in die
    Kartenliste aufgenommen und ihr Cover im Hintergrund geholt."""
    uid, link = z.get("karte"), z.get("link")
    if not uid:
        return None
    treffer = cover.LINK_RE.search(link) if link else None
    uri = f"spotify:{treffer.group(1).lower()}:{treffer.group(2)}" if treffer else None
    try:
        bekannt = karten.laden().get(uid)
        if uri is None and bekannt:
            uri = bekannt["uri"]
        erg = {"uid": uid, "bekannt": bool(bekannt), "link_auf_karte": bool(link), "uri": uri,
               "titel": None, "cover": None, "schluessel": None}
        if uri is None:
            return erg
        if not bekannt or bekannt["uri"] != uri:
            bekannt = karten.eintragen(uid, uri, auf_karte=bool(treffer) or None)
            erg["bekannt"] = True
        meta = karten.meta_lesen(uri)
        if not meta or not meta.get("titel") or not meta.get("hat_cover"):
            if cover_im_hintergrund(uri):
                meta = karten.meta_lesen(uri)
        erg.update(titel=bekannt.get("titel") or (meta or {}).get("titel"), cover=_cover_url(uri, meta),
                   schluessel=karten.schluessel(uri), typ=uri.split(":")[1])
        return erg
    except Exception as e:                           # die Kartenanzeige darf die Seite nie stören
        log(f"Kartendaten: {e!r}")
        return {"uid": uid, "bekannt": False, "link_auf_karte": bool(link), "uri": uri,
                "titel": None, "cover": None, "schluessel": None}


def auftrag_info():
    """Stand von "Karte bespielen" für die Eltern-Seite, mit Titel und Cover der Playlist (und der bisherigen
    Playlist, wenn die Karte schon belegt war)."""
    a = karten.auftrag_status()
    try:
        for schl, pre in (("uri", ""), ("vorher_uri", "vorher_")):
            uri = a.get(schl)
            if not uri:
                continue
            meta = karten.meta_lesen(uri) or {}
            a[pre + "titel"] = meta.get("titel") or next(
                (k["titel"] for k in karten.liste() if k["uri"] == uri), None)
            a[pre + "cover"] = _cover_url(uri, meta)
    except ValueError:                                  # unlesbare Adresse im Ergebnis: ohne Titel zeigen
        pass
    return a


def _etikett_einst():
    return einstellungen.laden()["etikett"]


def _bogen_plaetze():
    try:
        spalten, zeilen = etikett.plaetze(_etikett_einst())
    except Exception:
        return 0, 0
    return spalten, zeilen


def _offene_etiketten():
    """Karten, deren Etikett noch nicht gedruckt ist (je Spotify-Adresse eine), älteste zuerst."""
    gesehen, erg = set(), []
    for k in sorted(karten.liste(), key=lambda k: (k["angelegt"], k["uid"])):
        if not k["gedruckt"] and k["uri"] not in gesehen:
            gesehen.add(k["uri"])
            erg.append(k)
    return erg


def karten_liste():
    spalten, zeilen = _bogen_plaetze()
    plaetze = spalten * zeilen
    liste = karten.liste()
    for k in liste:
        meta = karten.meta_lesen(k["uri"])
        k["cover"] = _cover_url(k["uri"], meta)
        k["etikett"] = f"/etikett/{k['schluessel']}.png"
    offen = _offene_etiketten()
    return {"ok": True, "karten": liste,
            "etikett": {"verfuegbar": etikett.verfuegbar(), "groesse_mm": _etikett_einst()["groesse_mm"],
                        "spalten": spalten, "zeilen": zeilen, "plaetze": plaetze,
                        "offen": len(offen), "naechster_bogen": [k["uid"] for k in offen[:plaetze]]}}


def _uid(daten):
    """Kartennummer aus der Anfrage: '19:81:15:20' oder '19811520'."""
    wert = daten.get("uid") if isinstance(daten, dict) else None
    if not isinstance(wert, str):
        raise ValueError("Kartennummer fehlt.")
    return wert.upper() if ":" in wert else karten.uid_aus_url(wert)


def karten_pruefen(daten):
    """Eingefügten Spotify-Link prüfen; Titel und Cover suchen (oder aus dem Speicher nehmen)."""
    text = daten.get("text") if isinstance(daten, dict) else None
    if not isinstance(text, str) or not text.strip():
        return {"ok": False, "meldung": "Bitte zuerst einen Spotify-Link einfügen."}
    erg = cover.aufloesen(text.strip()[:600], neu=bool(daten.get("neu")))
    if erg.get("ok"):
        erg["cover"] = _cover_url(erg["uri"], karten.meta_lesen(erg["uri"]))
    return erg


def karten_bespielen(daten):
    """Auftrag an den Player: die nächste Karte im Kartenfach bekommt diese Playlist."""
    uri = daten.get("uri") if isinstance(daten, dict) else None
    try:
        karten.uri_pruefen(uri)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    p = player_zustand()
    if not p.get("laeuft"):
        return {"ok": False, "meldung": "Die Box-Software läuft gerade nicht. Bitte kurz warten oder die Box neu starten."}
    if p.get("leser"):
        return {"ok": False, "meldung": str(p["leser"])}
    karten.auftrag_stellen(uri, ueberschreiben=bool(daten.get("ueberschreiben")))
    cover_im_hintergrund(uri)
    return {"ok": True, "meldung": "Bitte jetzt die Karte in das Kartenfach legen.", "auftrag": auftrag_info()}


def karten_abbrechen(daten=None):
    karten.auftrag_abbrechen()
    return {"ok": True, "meldung": "Abgebrochen."}


def karten_umbenennen(daten):
    try:
        uid = _uid(daten)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    titel = daten.get("titel")
    if not isinstance(titel, str):
        return {"ok": False, "meldung": "Name fehlt."}
    if not karten.umbenennen(uid, titel):
        return {"ok": False, "meldung": "Diese Karte kennt die Box nicht."}
    return {"ok": True, "meldung": "Name gespeichert."}


def karten_entfernen(daten):
    try:
        uid = _uid(daten)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    if not karten.entfernen(uid):
        return {"ok": False, "meldung": "Diese Karte kennt die Box nicht."}
    return {"ok": True, "meldung": "Aus der Liste entfernt. Die Karte selbst bleibt unverändert; "
                                   "liegt sie wieder im Fach, erscheint sie wieder."}


def karten_gedruckt(daten):
    uids = daten.get("uids") if isinstance(daten, dict) else None
    if not isinstance(uids, list) or len(uids) > 500:
        return {"ok": False, "meldung": "Liste der Karten fehlt."}
    try:
        uids = [_uid({"uid": u}) for u in uids]
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    karten.gedruckt_setzen(uids, bool(daten.get("wert", True)))
    return {"ok": True, "meldung": "Gespeichert."}


def cover_neu(daten):
    """Cover und Titel noch einmal bei Spotify suchen (ersetzt auch ein früher gefundenes Cover,
    aber kein selbst hochgeladenes Bild; dafür 'eigenes' zurücksetzen)."""
    uri = daten.get("uri") if isinstance(daten, dict) else None
    try:
        karten.uri_pruefen(uri)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    erg = cover.nachschlagen(uri, neu=True)
    erg["cover"] = _cover_url(uri, karten.meta_lesen(uri))
    return erg


def cover_hochladen(roh, abfrage):
    """Eigenes Bild als Cover: Anfragetext = die Bilddatei, ?s=<schluessel der Playlist>."""
    try:
        uri = karten.uri_aus_schluessel((abfrage.get("s") or [""])[0])
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    erg = cover.eigenes_bild(uri, roh)
    if erg.get("ok"):
        erg["cover"] = _cover_url(uri, karten.meta_lesen(uri))
    return erg


def cover_titel(daten):
    """Titel von Hand eintragen, wenn Spotify keinen herausgibt."""
    try:
        uri = karten.uri_aus_schluessel(str(daten.get("schluessel") or "")) if isinstance(daten, dict) else None
        if not uri:
            raise ValueError("Unbekannte Playlist.")
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    erg = cover.titel_setzen(uri, daten.get("titel"))
    if erg.get("ok"):
        erg["cover"] = _cover_url(uri, karten.meta_lesen(uri))
    return erg


def _titel_zu_uri(uri):
    for k in karten.liste():
        if k["uri"] == uri and k["eigener_titel"]:
            return k["titel"]
    return (karten.meta_lesen(uri) or {}).get("titel") or "Peppa Box"


def _dateiname(text, vorlage="etikett"):
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    t = "".join(c if c.isalnum() else "-" for c in t).strip("-")
    return (t[:40] or vorlage).lower()


def etikett_antwort(name, abfrage):
    """PNG für /etikett/<name>.png; Rückgabe (Bytes, Dateiname). Wirft ValueError bei unbekanntem Namen."""
    einst = _etikett_einst()
    if name == "testbogen":
        return etikett.png_bytes(etikett.testbogen(einst)), "peppa-box-testbogen.png"
    if name == "bogen":
        gewuenscht = [s for s in (abfrage.get("s") or [""])[0].split(",") if s]
        if gewuenscht:
            uris = [karten.uri_aus_schluessel(s) for s in gewuenscht]
        else:
            uris = [k["uri"] for k in _offene_etiketten()]
        spalten, zeilen = _bogen_plaetze()
        uris = uris[:spalten * zeilen]
        if not uris:
            raise ValueError("Keine Karten für den Bogen.")
        bilder = [etikett.etikett(karten.cover_bytes(u), _titel_zu_uri(u), einst) for u in uris]
        return etikett.png_bytes(etikett.bogen(bilder, einst)), "peppa-box-etiketten.png"
    uri = karten.uri_aus_schluessel(name)
    titel = _titel_zu_uri(uri)
    bild = etikett.etikett(karten.cover_bytes(uri), titel, einst)
    return etikett.png_bytes(bild), f"etikett-{_dateiname(titel)}.png"


# ---------------------------------------------------------------- Aktionen

def update_pruefen():
    code, aus = git("fetch", "--quiet", zeit=60)
    if code != 0:
        return {"ok": False, "meldung": "GitHub nicht erreichbar: " + aus[-300:]}
    code, aus = git("log", "--format=%h%x1f%cI%x1f%s", "HEAD..@{u}")
    if code != 0:
        return {"ok": False, "meldung": aus[-300:]}
    neu = [dict(zip(("kurz", "datum", "text"), z.split("\x1f"))) for z in aus.splitlines() if z]
    return {"ok": True, "neu": neu}


def sauber():
    """Keine eigenen Aenderungen an Dateien im Repository auf dem Pi (die wuerden sonst verloren gehen)."""
    code, aus = git("status", "--porcelain", "--untracked-files=no")
    return code == 0 and not aus, aus


def update_starten():
    ok, aus = sauber()
    if not ok:
        return {"ok": False, "meldung": "Auf der Box wurden Dateien geändert, Update abgebrochen:\n" + aus}
    erg = update_pruefen()
    if not erg["ok"]:
        return erg
    if not erg["neu"]:
        return {"ok": True, "meldung": "Die Box ist schon auf dem neuesten Stand."}
    _, alt = git("rev-parse", "HEAD")
    _, geaendert = git("diff", "--name-only", "HEAD", "@{u}")
    code, aus = git("merge", "--ff-only", "@{u}")
    if code != 0:
        return {"ok": False, "meldung": "Update nicht möglich: " + aus[-300:]}
    os.makedirs(KONFIG, exist_ok=True)
    with open(VORHER_DATEI, "w") as f:
        f.write(alt + "\n")
    log(f"Update von {alt[:7]} auf {version()['kurz']}")
    return nach_versionswechsel(geaendert, f"{len(erg['neu'])} Änderung(en) eingespielt.")


def zurueck():
    sha = vorherige_version()
    if not sha:
        return {"ok": False, "meldung": "Keine vorherige Version gespeichert."}
    ok, aus = sauber()
    if not ok:
        return {"ok": False, "meldung": "Auf der Box wurden Dateien geändert, abgebrochen:\n" + aus}
    _, geaendert = git("diff", "--name-only", sha, "HEAD")
    code, aus = git("reset", "--hard", sha)
    if code != 0:
        return {"ok": False, "meldung": aus[-300:]}
    os.remove(VORHER_DATEI)
    log(f"Zurueck auf {sha[:7]}")
    return nach_versionswechsel(geaendert, "Vorherige Version wiederhergestellt.")


def nach_versionswechsel(geaendert, text):
    """Player neu starten, die Seite selbst ebenfalls (sie koennte sich geaendert haben)."""
    code, aus = mit_root(SYSTEMCTL, "restart", "peppa-player")
    meldung = text + " Musik startet neu."
    if code != 0:
        meldung += " Neustart des Players fehlgeschlagen: " + aus
    if EINRICHTUNG & set(geaendert.split()):
        meldung += (" Hinweis: Die Einrichtung hat sich geändert. Einmal am Pi "
                    "'sh ~/peppa-box/software/dienst_einrichten.sh' ausführen.")
    selbst_neu_starten()
    return {"ok": code == 0, "meldung": meldung, "neustart_seite": True}


def musik_neu():
    """Ton ganz neu: Raspotify anhalten, Mischer (peppa-stille) neu, Raspotify starten (Root-Helfer);
    mit alter Einrichtung nur Raspotify. Danach den Player neu."""
    a = mit_root(HELFER, "neustart")
    if a[0] != 0:
        a = mit_root(SYSTEMCTL, "restart", "raspotify")
    b = mit_root(SYSTEMCTL, "restart", "peppa-player")
    ok = a[0] == 0 and b[0] == 0
    return {"ok": ok, "meldung": "Musik startet neu (dauert einige Sekunden)." if ok
            else "Fehlgeschlagen: " + "; ".join(x for c, x in (a, b) if c)}


def box_neu():
    code, aus = mit_root(SYSTEMCTL, "reboot")
    return {"ok": code == 0, "meldung": "Box startet neu." if code == 0 else aus}


def ausschalten():
    code, aus = mit_root(SYSTEMCTL, "poweroff")
    return {"ok": code == 0, "meldung": "Box fährt herunter." if code == 0 else aus}


def _prozent(wert, name, lo, hi):
    if isinstance(wert, bool) or not isinstance(wert, (int, float)) or wert != int(wert) or not lo <= wert <= hi:
        raise ValueError(f"{name}: ganze Zahl von {lo} bis {hi} erwartet")
    return int(wert)


def begrenzen_jetzt():
    """Lautstärke sofort unter die (neue) Grenze bringen, ohne auf die Prüfung des Players zu warten."""
    aus = lautstaerke.aktive_ausgabe()
    aktuell = lautstaerke.lesen(aus)
    grenze = einstellungen.wirksames_max(einstellungen.laden(), aus, time.time())
    if aktuell is not None and aktuell > grenze:
        lautstaerke.setzen(aus, grenze)


def lautstaerke_setzen(daten):
    try:
        wunsch = _prozent(daten.get("prozent"), "Lautstärke", 0, 100)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    aus = lautstaerke.aktive_ausgabe()
    ziel = min(wunsch, einstellungen.wirksames_max(einstellungen.laden(), aus, time.time()))
    if not lautstaerke.setzen(aus, ziel):
        return {"ok": False, "meldung": "Der Lautstärkeregler der Box antwortet nicht."}
    return {"ok": True, "prozent": ziel, "begrenzt": ziel < wunsch}


def einstellungen_lesen():
    return {"ok": True, "einstellungen": einstellungen.laden(),
            "ausgaben": {a: lautstaerke.eingerichtet(a) for a in einstellungen.AUSGABEN}}


def einstellungen_speichern(daten):
    try:
        neu = einstellungen.speichern(daten)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    begrenzen_jetzt()
    return {"ok": True, "einstellungen": neu, "meldung": "Gespeichert."}


def timer_abbrechen_intern():
    """Timer löschen. War er schon beim Ausblenden, die Lautstärke wieder auf den alten Wert."""
    return automatik.timer_abbrechen(lautstaerke, einstellungen)


def timer_starten(daten):
    try:
        minuten = _prozent(daten.get("minuten"), "Minuten", 5, 180)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    automatik.timer_starten(minuten, lautstaerke, einstellungen)
    return {"ok": True, "meldung": f"Die Musik endet in {minuten} Minuten (die letzten Sekunden werden leiser)."}


def timer_abbrechen(daten=None):
    war = timer_abbrechen_intern()
    return {"ok": True, "meldung": "Schlummer-Timer abgebrochen." if war else "Es lief kein Timer."}


def ruhe_aussetzen(daten=None):
    cfg, jetzt = einstellungen.laden(), time.time()
    if not (cfg["ruhezeit"]["an"] and einstellungen.in_ruhezeit(cfg, jetzt)):
        return {"ok": False, "meldung": "Gerade ist keine Ruhezeit."}
    bis = einstellungen.naechstes_ende(cfg, jetzt)
    einstellungen.lauf_schreiben("ruhe", {"bis": bis})
    return {"ok": True, "meldung": "Ruhezeit ausgesetzt bis " + time.strftime("%H:%M", time.localtime(bis)) + " Uhr."}


def ruhe_wieder(daten=None):
    einstellungen.lauf_loeschen("ruhe")
    return {"ok": True, "meldung": "Ruhezeit gilt wieder."}


def ansagen_liste():
    return {"ok": True, "ansagen": [{"name": n, "text": t, "quelle": toene.quelle_ohne_erzeugen(n)}
                                    for n, t in toene.ANSAGEN.items()]}


def ansage_spielen(daten):
    name = daten.get("name")
    if name not in toene.ANSAGEN:
        return {"ok": False, "meldung": "Unbekannte Ansage."}
    ok = toene.spielen(name, warten=False, log=log)
    return {"ok": ok, "meldung": f"„{toene.ANSAGEN[name]}“" if ok else "Ansage ließ sich nicht abspielen (siehe Meldungen)."}


AKTIONEN = {"/api/update/pruefen": update_pruefen, "/api/update/starten": update_starten,
            "/api/update/zurueck": zurueck, "/api/musik-neustart": musik_neu,
            "/api/neustart": box_neu, "/api/ausschalten": ausschalten}
# Aktionen mit Eingabewerten (JSON im Anfragetext). Sie sind schnell und dürfen neben einem
# laufenden Update ausgeführt werden (z. B. Lautstärke ändern).
SCHNELL = {"/api/klang": klang_setzen, "/api/lautstaerke": lautstaerke_setzen, "/api/einstellungen": einstellungen_speichern,
           "/api/timer/starten": timer_starten, "/api/timer/abbrechen": timer_abbrechen,
           "/api/ruhezeit/aussetzen": ruhe_aussetzen, "/api/ruhezeit/wieder": ruhe_wieder,
           "/api/ansage": ansage_spielen,
           "/api/karten/pruefen": karten_pruefen, "/api/karten/bespielen": karten_bespielen,
           "/api/karten/abbrechen": karten_abbrechen, "/api/karten/umbenennen": karten_umbenennen,
           "/api/karten/entfernen": karten_entfernen, "/api/karten/gedruckt": karten_gedruckt,
           "/api/cover/neu": cover_neu, "/api/cover/titel": cover_titel}
# Aktionen, deren Anfragetext eine Datei ist (kein JSON); die Parameter stehen in der Adresse (?s=...)
ROH = {"/api/cover/hochladen": cover_hochladen}
GROESSE = {"/api/cover/hochladen": BILD_MAX}                # sonst gilt 4096 Bytes


# ---------------------------------------------------------------- Webserver

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _antwort(self, code, daten, typ="application/json; charset=utf-8", cache=False, datei=None):
        body = daten if isinstance(daten, bytes) else json.dumps(daten, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
        if datei:
            self.send_header("Content-Disposition", f'attachment; filename="{datei}"')
        self.end_headers()
        self.wfile.write(body)

    def _bild(self, pfad, abfrage):
        """/cover/<schluessel>.jpg und /etikett/<schluessel|bogen|testbogen>.png"""
        teile = pfad.split("/")
        if len(teile) != 3:
            return self._antwort(404, {"fehler": "nicht gefunden"})
        art = teile[1]
        stamm, _, endung = teile[2].rpartition(".")
        try:
            if art == "cover" and endung == "jpg":
                daten = karten.cover_bytes(karten.uri_aus_schluessel(stamm))
                if daten is None:
                    return self._antwort(404, {"fehler": "kein Cover"})
                return self._antwort(200, daten, "image/jpeg", cache=True)
            if art == "etikett" and endung == "png":
                if not etikett.verfuegbar():
                    return self._antwort(503, {"ok": False, "meldung": "Zum Erstellen der Etiketten fehlt auf der Box das "
                                               "Bildprogramm (Pillow). Einmal am Pi 'sh ~/peppa-box/software/dienst_einrichten.sh' ausführen."})
                png, name = etikett_antwort(stamm, abfrage)
                laden = (abfrage.get("laden") or [""])[0] == "1"
                return self._antwort(200, png, "image/png", datei=name if laden else None)
        except ValueError as e:
            return self._antwort(404, {"ok": False, "meldung": str(e)})
        except Exception as e:
            log(f"Bild {pfad}: {e!r}")
            return self._antwort(500, {"ok": False, "meldung": f"Bild ließ sich nicht erstellen: {e!r}"})
        return self._antwort(404, {"fehler": "nicht gefunden"})

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        pfad, abfrage = url.path, urllib.parse.parse_qs(url.query)
        if pfad in ("/api/karte", "/api/zustand", "/api/karten"):
            einstellungen.lauf_beruehren("seite")        # Eltern-Seite ist offen: Auto-Aus wartet
        if pfad == "/api/karte":
            z = player_zustand()
            erg = {k: z.get(k) for k in ("karte", "link", "laeuft", "spotify_bereit", "ausgang", "leser")}
            erg["bedienung"] = bedienung_live()
            erg["kartendaten"] = kartendaten(z)          # Titel und Cover der Karte im Fach
            erg["auftrag"] = auftrag_info()              # läuft gerade "Karte bespielen"?
            return self._antwort(200, erg)
        if pfad == "/api/karten":
            return self._antwort(200, karten_liste())
        if pfad.startswith(("/cover/", "/etikett/")):
            return self._bild(pfad, abfrage)
        if pfad == "/api/bedienung":                    # Prüfansicht offen: Player liest Rohwerte des Touch-Chips
            einstellungen.lauf_beruehren("seite")
            einstellungen.lauf_beruehren("seite-bedienung")
            return self._antwort(200, bedienung_live())
        if pfad == "/api/belegung":                     # was die Tasten können (inkl. Halten)
            try:
                cfg = einstellungen.laden()
            except Exception:
                cfg = None
            return self._antwort(200, bedienung.belegung(cfg))
        if pfad == "/api/ansagen":
            return self._antwort(200, ansagen_liste())
        if pfad == "/api/zustand":
            return self._antwort(200, zustand())
        if pfad == "/api/einstellungen":
            return self._antwort(200, einstellungen_lesen())
        if pfad == "/api/meldungen":
            return self._antwort(200, meldungen())
        if pfad == "/api/klang":
            return self._antwort(200, klang_info())
        if pfad == "/api/diagnose":
            return self._antwort(200, diagnose())
        name = "index.html" if pfad in ("/", "/index.html") else pfad.lstrip("/")
        datei = os.path.join(WEB, name)
        endung = os.path.splitext(name)[1]
        if "/" in name or endung not in DATEITYPEN or not os.path.isfile(datei):
            return self._antwort(404, {"fehler": "nicht gefunden"})
        with open(datei, "rb") as f:
            self._antwort(200, f.read(), DATEITYPEN[endung], cache=endung == ".png")

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        pfad, abfrage = url.path, urllib.parse.parse_qs(url.query)
        roh = ROH.get(pfad)
        schnell = pfad in SCHNELL or roh is not None
        aktion = roh or SCHNELL.get(pfad) or AKTIONEN.get(pfad)
        if not aktion:
            return self._antwort(404, {"fehler": "nicht gefunden"})
        # Eigener Kopfeintrag: fremde Webseiten im Browser koennen ihn nicht setzen (Schutz vor
        # untergeschobenen Klicks, z. B. "Ausschalten" ueber einen Link auf einer anderen Seite).
        if self.headers.get("X-Peppa-Box") != "1":
            return self._antwort(403, {"ok": False, "meldung": "Nur über die Peppa-Box-Seite."})
        daten = b"" if roh else {}
        try:
            laenge = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._antwort(400, {"ok": False, "meldung": "Ungültige Anfrage."})
        if laenge > GROESSE.get(pfad, 4096):
            return self._antwort(413, {"ok": False, "meldung": "Die Datei ist zu groß." if roh else "Anfrage zu groß."})
        if laenge:
            koerper = self.rfile.read(laenge)
            if roh:
                daten = koerper
            else:
                try:
                    daten = json.loads(koerper)
                except ValueError:
                    return self._antwort(400, {"ok": False, "meldung": "Ungültige Anfrage."})
        if not schnell and not SPERRE.acquire(blocking=False):
            return self._antwort(409, {"ok": False, "meldung": "Es läuft schon eine Aktion, bitte kurz warten."})
        try:
            if pfad not in ("/api/lautstaerke", "/api/klang"):  # Regler-Ziehen nicht im Protokoll
                log(f"Aktion {pfad}")
            erg = aktion(daten, abfrage) if roh else aktion(daten) if schnell else aktion()
        except Exception as e:                      # nie die Seite abstuerzen lassen
            erg = {"ok": False, "meldung": f"Interner Fehler: {e!r}"}
        finally:
            if not schnell:
                SPERRE.release()
        if pfad not in ("/api/lautstaerke", "/api/klang"):
            log(f"  -> {erg.get('meldung', erg.get('ok'))}")
        self._antwort(200, erg)


class DoppelServer(ThreadingHTTPServer):
    """Lauscht auf IPv6 und IPv4 zugleich (Windows spricht peppabox.local oft per IPv6 an).
    Nur-IPv4 hatte am 02.11.2026 zur Folge: SSH ging, die Eltern-Seite nicht."""
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def server_starten(port):
    """Erst IPv6+IPv4, falls IPv6 auf dem Geraet fehlt nur IPv4."""
    try:
        return DoppelServer(("::", port), Handler)
    except OSError:
        return ThreadingHTTPServer(("0.0.0.0", port), Handler)


def main():
    server = []
    for port in PORTS:
        try:
            s = server_starten(port)
        except OSError as e:
            log(f"Port {port} nicht moeglich ({e.strerror}), ueberspringe.")
            continue
        threading.Thread(target=s.serve_forever, daemon=True).start()
        server.append(port)
    if not server:
        sys.exit("Kein Port frei.")
    name = socket.gethostname()
    log("Eltern-Seite: " + "  ".join(
        f"http://{name}.local" + ("" if p == 80 else f":{p}") for p in server)
        + ("   (PROBELAUF)" if TROCKEN else ""))
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
