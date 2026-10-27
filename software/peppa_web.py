#!/usr/bin/env python3
"""Peppa Box – Eltern-Seite: Zustand ansehen, Lautstärke und Zeiten einstellen, Musik/Box neu starten,
ausschalten, Software-Update von GitHub.

Laeuft als eigener Dienst peppa-web (nicht im Player), damit Updates und Neustarts des Players
die Seite nicht mitreissen. Port 8080, zusaetzlich Port 80, wenn erlaubt (systemd gibt das Recht).
Nur Standardbibliothek. Kein Passwort: jeder im selben Netz kann die Seite bedienen.

Rechte: Ausschalten, Neustart und Dienst-Neustarts laufen ueber sudo, freigegeben nur fuer genau
diese Befehle in /etc/sudoers.d/peppa-box (richtet dienst_einrichten.sh ein).

Start von Hand:     python3 ~/peppa-box/software/peppa_web.py
Probelauf ohne Wirkung (sudo-Befehle werden nur angezeigt):  PEPPA_WEB_TROCKEN=1 python3 peppa_web.py
"""
import datetime
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import akku
import einstellungen
import lautstaerke

ORDNER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ORDNER)
WEB = os.path.join(ORDNER, "web")
STATUS_DATEI = einstellungen.lauf_pfad("status")           # schreibt der Player jede Sekunde
KONFIG = os.path.expanduser("~/.config/peppa-box")
VORHER_DATEI = os.path.join(KONFIG, "vorherige_version.txt")
TROCKEN = os.environ.get("PEPPA_WEB_TROCKEN") == "1"
PORTS = [int(p) for p in os.environ.get("PEPPA_WEB_PORTS", "8080,80").split(",")]
SYSTEMCTL = shutil.which("systemctl") or "/usr/bin/systemctl"

SPERRE = threading.Lock()          # immer nur eine Aktion (Update, Neustart ...) gleichzeitig

DATEITYPEN = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
              ".webmanifest": "application/manifest+json", ".png": "image/png",
              ".svg": "image/svg+xml"}


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
    for name in ("peppa-player", "raspotify"):
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
    mem = {}
    for zeile in (lies("/proc/meminfo", "") or "").splitlines():
        k, _, v = zeile.partition(":")
        mem[k] = int(v.split()[0]) if v.split() else 0
    return {
        "rechner": socket.gethostname(),
        "player": player_zustand(),
        "dienste": dienste(),
        "akku": akku.lesen(),
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
    code, aus = befehl(["journalctl", "-u", "peppa-player", "-u", "peppa-web", "-n", "60",
                        "--no-pager", "-o", "short-iso"], zeit=10)
    return {"ok": code == 0, "text": aus}


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
    if "software/dienst_einrichten.sh" in geaendert.split():
        meldung += (" Hinweis: Die Einrichtung hat sich geändert. Einmal am Pi "
                    "'sh ~/peppa-box/software/dienst_einrichten.sh' ausführen.")
    selbst_neu_starten()
    return {"ok": code == 0, "meldung": meldung, "neustart_seite": True}


def musik_neu():
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
    t = einstellungen.lauf_lesen("timer")
    if not t:
        return False
    einstellungen.lauf_loeschen("timer")
    if t.get("vorher") is not None:
        lautstaerke.setzen(lautstaerke.aktive_ausgabe(), t["vorher"])
    return True


def timer_starten(daten):
    try:
        minuten = _prozent(daten.get("minuten"), "Minuten", 5, 180)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    timer_abbrechen_intern()
    einstellungen.lauf_schreiben("timer", {"ende": time.time() + minuten * 60, "minuten": minuten, "vorher": None})
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


AKTIONEN = {"/api/update/pruefen": update_pruefen, "/api/update/starten": update_starten,
            "/api/update/zurueck": zurueck, "/api/musik-neustart": musik_neu,
            "/api/neustart": box_neu, "/api/ausschalten": ausschalten}
# Aktionen mit Eingabewerten (JSON im Anfragetext). Sie sind schnell und dürfen neben einem
# laufenden Update ausgeführt werden (z. B. Lautstärke ändern).
SCHNELL = {"/api/lautstaerke": lautstaerke_setzen, "/api/einstellungen": einstellungen_speichern,
           "/api/timer/starten": timer_starten, "/api/timer/abbrechen": timer_abbrechen,
           "/api/ruhezeit/aussetzen": ruhe_aussetzen, "/api/ruhezeit/wieder": ruhe_wieder}


# ---------------------------------------------------------------- Webserver

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _antwort(self, code, daten, typ="application/json; charset=utf-8", cache=False):
        body = daten if isinstance(daten, bytes) else json.dumps(daten, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        pfad = self.path.split("?")[0]
        if pfad in ("/api/karte", "/api/zustand"):
            einstellungen.lauf_beruehren("seite")        # Eltern-Seite ist offen: Auto-Aus wartet
        if pfad == "/api/karte":
            z = player_zustand()
            return self._antwort(200, {k: z.get(k) for k in ("karte", "link", "laeuft", "spotify_bereit")})
        if pfad == "/api/zustand":
            return self._antwort(200, zustand())
        if pfad == "/api/einstellungen":
            return self._antwort(200, einstellungen_lesen())
        if pfad == "/api/meldungen":
            return self._antwort(200, meldungen())
        name = "index.html" if pfad in ("/", "/index.html") else pfad.lstrip("/")
        datei = os.path.join(WEB, name)
        endung = os.path.splitext(name)[1]
        if "/" in name or endung not in DATEITYPEN or not os.path.isfile(datei):
            return self._antwort(404, {"fehler": "nicht gefunden"})
        with open(datei, "rb") as f:
            self._antwort(200, f.read(), DATEITYPEN[endung], cache=endung == ".png")

    def do_POST(self):
        schnell = self.path in SCHNELL
        aktion = SCHNELL.get(self.path) or AKTIONEN.get(self.path)
        if not aktion:
            return self._antwort(404, {"fehler": "nicht gefunden"})
        # Eigener Kopfeintrag: fremde Webseiten im Browser koennen ihn nicht setzen (Schutz vor
        # untergeschobenen Klicks, z. B. "Ausschalten" ueber einen Link auf einer anderen Seite).
        if self.headers.get("X-Peppa-Box") != "1":
            return self._antwort(403, {"ok": False, "meldung": "Nur über die Peppa-Box-Seite."})
        daten = {}
        laenge = int(self.headers.get("Content-Length") or 0)
        if laenge > 4096:
            return self._antwort(413, {"ok": False, "meldung": "Anfrage zu groß."})
        if laenge:
            try:
                daten = json.loads(self.rfile.read(laenge))
            except ValueError:
                return self._antwort(400, {"ok": False, "meldung": "Ungültige Anfrage."})
        if not schnell and not SPERRE.acquire(blocking=False):
            return self._antwort(409, {"ok": False, "meldung": "Es läuft schon eine Aktion, bitte kurz warten."})
        try:
            if not schnell or self.path != "/api/lautstaerke":      # Regler-Ziehen nicht im Protokoll
                log(f"Aktion {self.path}")
            erg = aktion(daten) if schnell else aktion()
        except Exception as e:                      # nie die Seite abstuerzen lassen
            erg = {"ok": False, "meldung": f"Interner Fehler: {e!r}"}
        finally:
            if not schnell:
                SPERRE.release()
        if not schnell or self.path != "/api/lautstaerke":
            log(f"  -> {erg.get('meldung', erg.get('ok'))}")
        self._antwort(200, erg)


def main():
    server = []
    for port in PORTS:
        try:
            s = ThreadingHTTPServer(("0.0.0.0", port), Handler)
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
