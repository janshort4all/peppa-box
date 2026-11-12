"""Spotify Web API: Anmeldung (Authorization Code mit PKCE) und Wiedergabe-Steuerung.

Zugangsdaten liegen NUR auf dem Pi unter ~/.config/peppa-box/ (nie im Repository):
  config.json         Client-ID der eigenen Spotify-App
  spotify_token.json  Refresh-Token (wird bei jeder Erneuerung ersetzt)
Nur Python-Standardbibliothek, keine Zusatzpakete.
"""
import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

CONF_DIR = os.path.expanduser("~/.config/peppa-box")
CONFIG = os.path.join(CONF_DIR, "config.json")
TOKEN = os.path.join(CONF_DIR, "spotify_token.json")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-playback-state user-modify-playback-state"
API = "https://api.spotify.com/v1"
ZEITLIMIT = 8               # Sekunden je Anfrage; kurz, damit ein haengendes Netz die Box nicht lange blockiert
_TOKEN_SPERRE = threading.Lock()


class AnmeldungFehlt(RuntimeError):
    """Kein gueltiger Refresh-Token: einmal spotify_login.py ausfuehren. Kein SystemExit, damit der
    Player weiterlaeuft (Karte lesen, Eltern-Seite) und die Ursache meldet."""


def _save(path, data):
    os.makedirs(CONF_DIR, mode=0o700, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def client_id():
    cfg = _load(CONFIG, {})
    return cfg.get("client_id")


def _token_request(params):
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request("https://accounts.spotify.com/api/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        tok = json.load(resp)
    old = _load(TOKEN, {})
    tok.setdefault("refresh_token", old.get("refresh_token"))   # bei PKCE kommt meist ein neuer
    tok["expires_at"] = time.time() + tok.get("expires_in", 3600) - 60
    _save(TOKEN, tok)
    return tok


def login_interaktiv():
    """Einmalige Anmeldung. Laeuft im Terminal: Link im Browser oeffnen, Adresse zurueckkopieren."""
    cid = client_id()
    if not cid:
        cid = input("Client-ID deiner Spotify-App einfuegen: ").strip()
        _save(CONFIG, {"client_id": cid})
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(12)
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": cid, "response_type": "code", "redirect_uri": REDIRECT_URI,
        "code_challenge_method": "S256", "code_challenge": challenge,
        "scope": SCOPES, "state": state})
    print("\n1. Diesen Link im Browser am PC oeffnen und bei Spotify zustimmen:\n")
    print(url)
    print("\n2. Danach zeigt der Browser eine Fehlerseite (das ist richtig so).")
    print("   Die komplette Adresse aus der Adresszeile kopieren (beginnt mit http://127.0.0.1:8888/callback?code=)")
    antwort = input("\n3. Adresse hier einfuegen: ").strip()
    q = urllib.parse.parse_qs(urllib.parse.urlparse(antwort).query)
    if q.get("state", [""])[0] != state:
        raise SystemExit("Die Adresse passt nicht zu diesem Anmeldeversuch. Bitte neu starten.")
    if "error" in q:
        raise SystemExit("Spotify meldet: " + q["error"][0])
    _token_request({"grant_type": "authorization_code", "code": q["code"][0],
                    "redirect_uri": REDIRECT_URI, "client_id": cid, "code_verifier": verifier})
    print("\nAnmeldung gespeichert.")


def access_token():
    with _TOKEN_SPERRE:                     # Player und Steuerung erneuern nie gleichzeitig
        tok = _load(TOKEN)
        if not tok or not tok.get("refresh_token"):
            raise AnmeldungFehlt("Noch nicht bei Spotify angemeldet. Bitte: python3 ~/peppa-box/software/spotify_login.py")
        if time.time() < tok.get("expires_at", 0) and tok.get("access_token"):
            return tok["access_token"]
        try:
            tok = _token_request({"grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
                                  "client_id": client_id()})
        except urllib.error.HTTPError as e:
            if e.code in (400, 401):        # Refresh-Token ungueltig (z. B. Zugriff in Spotify entzogen)
                raise AnmeldungFehlt(f"Spotify-Anmeldung abgelaufen ({e.code}). Bitte: "
                                     "python3 ~/peppa-box/software/spotify_login.py") from e
            raise
        return tok["access_token"]


def token_verwerfen():
    """Nach 401: beim naechsten Aufruf neuen Zugangs-Token holen."""
    with _TOKEN_SPERRE:
        tok = _load(TOKEN)
        if tok:
            tok["expires_at"] = 0
            _save(TOKEN, tok)


def api(method, path, body=None, params=None):
    """Aufruf der Web API. Gibt (Statuscode, JSON oder None) zurueck."""
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    data = json.dumps(body).encode() if body is not None else (b"" if method in ("PUT", "POST") else None)
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": "Bearer " + access_token(),
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=ZEITLIMIT) as resp:
            return resp.status, _json_oder_none(resp.read())
    except urllib.error.HTTPError as e:
        data = _json_oder_none(e.read())
        if e.code == 429:                   # zu viele Anfragen: Wartezeit mitgeben
            try:
                warte = int(e.headers.get("Retry-After", "5"))
            except (TypeError, ValueError):
                warte = 5
            data = dict(data if isinstance(data, dict) else {}, retry_after=warte)
        return e.code, data


def _json_oder_none(raw):
    """Spotify antwortet bei manchen Befehlen (z. B. Pause) ohne oder mit Nicht-JSON-Inhalt."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return None


def geraete():
    status, data = api("GET", "/me/player/devices")
    return (data or {}).get("devices", []) if status == 200 else []


def geraet_id(name):
    for d in geraete():
        if d.get("name", "").lower() == name.lower():
            return d["id"]
    return None


def link_zu_uri(text):
    """open.spotify.com-Link oder spotify:-URI -> spotify:<typ>:<id>."""
    text = text.strip()
    if text.startswith("spotify:"):
        return text
    teile = [t for t in urllib.parse.urlparse(text).path.split("/") if t]
    teile = [t for t in teile if not t.startswith("intl-")]         # z. B. /intl-de/playlist/...
    if len(teile) >= 2 and teile[0] in ("playlist", "album", "artist", "track", "show", "episode"):
        return f"spotify:{teile[0]}:{teile[1]}"
    raise ValueError("Das sieht nicht nach einem Spotify-Link aus: " + text)


def abspielen(device_id, uri, titel=None, position_ms=0):
    """Karte abspielen; mit titel/position_ms an einer gemerkten Stelle (fortschritt.py) weiter."""
    if uri.split(":")[1] in ("track", "episode"):
        body = {"uris": [uri]}
    else:
        body = {"context_uri": uri}
        if titel:
            body["offset"] = {"uri": titel}
    if position_ms:
        body["position_ms"] = int(max(0, position_ms))
    status, data = api("PUT", "/me/player/play", body, {"device_id": device_id})
    # Geraet nicht aktiv: erst Wiedergabe uebertragen, dann noch einmal. 404 "kein aktives Geraet", und
    # 12.11.2026: nach einer Nacht antwortete Spotify 502, auch nach Raspotify-Neustarts; erst das
    # Auswaehlen der Box in der Spotify-App (= Uebertragen) half.
    if status == 404 or status >= 500:
        api("PUT", "/me/player", {"device_ids": [device_id], "play": False})
        time.sleep(1)
        status, data = api("PUT", "/me/player/play", body, {"device_id": device_id})
    return status, data


def spielt(device_id):
    """Spielt gerade Musik auf diesem Gerät? True/False, None wenn Spotify nicht antwortet."""
    status, data = api("GET", "/me/player")
    if status == 204:                       # kein aktives Gerät, nichts spielt
        return False
    if status != 200 or not isinstance(data, dict):
        return None
    geraet = data.get("device") or {}
    return bool(data.get("is_playing")) and geraet.get("id") == device_id


def zustand():
    """Wiedergabe-Zustand fuer die Pruefung nach einem Befehl.
    dict(geraet, spielt, titel, position) | {"leer": True} (nichts aktiv) | None (keine Antwort)."""
    status, data = api("GET", "/me/player")
    if status == 204:
        return {"leer": True}
    if status != 200 or not isinstance(data, dict):
        return None
    item = data.get("item") or {}
    return {"geraet": (data.get("device") or {}).get("id"), "spielt": bool(data.get("is_playing")),
            "titel": item.get("id") or item.get("uri"), "position": data.get("progress_ms") or 0,
            "titel_uri": item.get("uri"), "kontext": (data.get("context") or {}).get("uri")}


def uebertragen(device_id, spielen=True):
    """Letzte Wiedergabe (Playlist und Stelle) auf dieses Geraet holen, z. B. nach Neustart von Raspotify."""
    return api("PUT", "/me/player", {"device_ids": [device_id], "play": bool(spielen)})


def fortsetzen(device_id):
    return api("PUT", "/me/player/play", None, {"device_id": device_id})


def pause(device_id):
    return api("PUT", "/me/player/pause", None, {"device_id": device_id})


def naechster(device_id):
    """Nächster Titel (Touchfeld "vor")."""
    return api("POST", "/me/player/next", None, {"device_id": device_id})


def vorheriger(device_id):
    """Vorheriger Titel (Touchfeld "zurück")."""
    return api("POST", "/me/player/previous", None, {"device_id": device_id})


def springen(device_id, position_ms):
    """An eine Stelle im laufenden Titel springen (Spulen, z. B. in Hörbüchern)."""
    return api("PUT", "/me/player/seek", None, {"position_ms": int(max(0, position_ms)), "device_id": device_id})
