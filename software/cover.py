"""Cover und Titel zu einem Spotify-Link finden und speichern.

Reihenfolge (jede Stufe nur, wenn die vorige kein Bild geliefert hat):
  1. oEmbed von Spotify (kein Konto nötig):  https://open.spotify.com/oembed?url=...  ->  title, thumbnail_url
  2. die öffentliche Seite open.spotify.com/<typ>/<id>:  og:image und og:title (Vorschau für Messenger)
  3. die Web API mit der Anmeldung der Box (images[0].url, name)
Danach wird das größte erreichbare Bild geladen (bei Albumbildern die 640-px-Fassung statt 300 px), geprüft
und als JPEG unter ~/.config/peppa-box/cover/ abgelegt (karten.py). Ein eigenes Bild des Benutzers wird
nie von einer Suche überschrieben, außer er verlangt ausdrücklich "neu suchen".

Nur Standardbibliothek (Pillow nur zum Prüfen und Verkleinern, ohne Pillow wird das Bild unverändert gespeichert).
Alle Netzzugriffe laufen über `holen(url, max_bytes)`, damit die Tests ohne Internet auskommen.
"""
import html
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request

import karten

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None

ZEITLIMIT = 8
MAX_SEITE = 600_000
MAX_BILD = 6_000_000
MAX_KANTE = 1200                                     # größer wird nicht gespeichert (Etikett braucht ~470 px)
UA = "Mozilla/5.0 (X11; Linux aarch64; rv:120.0) Gecko/20100101 Firefox/120.0 PeppaBox"

TYPEN = "playlist|album|show|episode|track|artist"
LINK_RE = re.compile(rf"(?:open|play)\.spotify\.com/(?:intl-[a-z-]+/)?(?:embed/)?({TYPEN})/([A-Za-z0-9]{{8,40}})", re.I)
URI_RE = re.compile(rf"spotify:(?:user:[^:\s]+:)?({TYPEN}):([A-Za-z0-9]{{8,40}})")
KURZ_RE = re.compile(r"https?://(?:spotify\.link|spotify\.app\.link)/[A-Za-z0-9_\-]+")


def http_holen(url, max_bytes=MAX_SEITE, zeit=ZEITLIMIT):
    """(Statuscode, Inhalt, endgültige Adresse). Wirft nie: bei Netzfehlern (0, b'', url)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "de,en;q=0.7",
                                                   "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=zeit) as r:
            return r.status, r.read(max_bytes + 1)[:max_bytes], r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, b"", url
    except (OSError, ValueError):
        return 0, b"", url


# ---------------------------------------------------------------- Adresse aus Text

def adresse_aus_text(text, holen=http_holen):
    """Spotify-Adresse (spotify:typ:id) aus einem eingefügten Link, einer Adresse oder einem Text mit Link.
    Wirft ValueError mit verständlichem Text."""
    text = (text or "").strip()
    for muster in (URI_RE, LINK_RE):
        m = muster.search(text)
        if m:
            return f"spotify:{m.group(1).lower()}:{m.group(2)}"
    k = KURZ_RE.search(text)
    if k:                                             # Kurzlink aus "Teilen": einmal folgen
        status, _, ziel = holen(k.group(0), 20_000)
        for muster in (LINK_RE,):
            m = muster.search(ziel or "")
            if m:
                return f"spotify:{m.group(1).lower()}:{m.group(2)}"
        raise ValueError("Der Kurzlink ließ sich nicht öffnen. Bitte den langen Link aus Spotify verwenden "
                         "(Teilen → Link kopieren).")
    if "spotify" in text.lower():
        raise ValueError("Dieser Spotify-Link wird nicht unterstützt. Möglich sind Playlists, Alben, "
                         "Podcasts, Künstler und einzelne Titel.")
    raise ValueError("Das sieht nicht nach einem Spotify-Link aus. In Spotify: Playlist öffnen → ⋯ → Teilen → Link kopieren.")


# ---------------------------------------------------------------- Suche

def _meta(seite, name):
    for m in re.finditer(r"<meta\s[^>]*>", seite, re.I):
        tag = m.group(0)
        if re.search(r"""(?:property|name)\s*=\s*["']""" + re.escape(name) + r"""["']""", tag, re.I):
            c = re.search(r"""content\s*=\s*("([^"]*)"|'([^']*)')""", tag, re.I)
            if c:
                return html.unescape(c.group(2) if c.group(2) is not None else c.group(3)).strip()
    return None


def _titel_putzen(t):
    t = re.sub(r"\s*\|\s*Spotify\s*$", "", t or "").strip()
    return t or None


def groesser(url):
    """Bekannte kleine Spotify-Bildgrößen auf 640 px hochsetzen (Albumcover: 00001e02 = 300, 00004851 = 64)."""
    for klein in ("ab67616d00001e02", "ab67616d00004851"):
        if klein in url:
            return url.replace(klein, "ab67616d0000b273")
    return url


def _bild_normal(daten):
    """Bild prüfen und als JPEG (höchstens MAX_KANTE) zurückgeben; None, wenn es kein brauchbares Bild ist."""
    if not daten:
        return None
    if Image is None:
        return daten if daten[:3] == b"\xff\xd8\xff" or daten[:4] == b"\x89PNG" else None
    try:
        b = Image.open(io.BytesIO(daten))
        b.load()
        b = ImageOps.exif_transpose(b)
        if b.mode in ("RGBA", "LA", "P"):
            hinten = Image.new("RGB", b.size, (255, 255, 255))
            b = b.convert("RGBA")
            hinten.paste(b, mask=b.getchannel("A"))
            b = hinten
        b = b.convert("RGB")
    except Exception:
        return None
    if min(b.size) < 32:
        return None
    b.thumbnail((MAX_KANTE, MAX_KANTE), Image.LANCZOS)
    puffer = io.BytesIO()
    b.save(puffer, "JPEG", quality=92, optimize=True)
    return puffer.getvalue()


def _web_api(typ, nr, api):
    pfad = {"playlist": "/playlists/", "album": "/albums/", "show": "/shows/", "episode": "/episodes/",
            "track": "/tracks/", "artist": "/artists/"}[typ] + nr
    status, d = api("GET", pfad)
    if status != 200 or not isinstance(d, dict):
        return None, None
    bilder = d.get("images") or (d.get("album") or {}).get("images") or (d.get("show") or {}).get("images") or []
    url = bilder[0].get("url") if bilder and isinstance(bilder[0], dict) else None
    return _titel_putzen(d.get("name")), url


def suchen(uri, holen=http_holen, api=None):
    """Titel und Cover zu einer Spotify-Adresse. Gibt dict(titel, bild, quelle, meldung) zurück; `bild` sind
    JPEG-Bytes oder None. Wirft nie (Netzfehler werden zu einer Meldung)."""
    typ, nr = karten.uri_pruefen(uri)
    link = karten.uri_zu_link(uri)
    titel, bild_url, quelle, probleme = None, None, None, []

    status, body, _ = holen("https://open.spotify.com/oembed?url=" + urllib.parse.quote(link, safe=""))
    if status == 200:
        try:
            d = json.loads(body)
            titel = _titel_putzen(d.get("title"))
            bild_url = d.get("thumbnail_url") or None
            quelle = "oembed" if bild_url else None
        except ValueError:
            probleme.append("oEmbed unlesbar")
    else:
        probleme.append(f"oEmbed {status or 'keine Verbindung'}")

    if not bild_url:
        status, body, _ = holen(link, MAX_SEITE)
        if status == 200:
            seite = body.decode("utf-8", "replace")
            bild_url = _meta(seite, "og:image")
            titel = titel or _titel_putzen(_meta(seite, "og:title"))
            quelle = "seite" if bild_url else quelle
        else:
            probleme.append(f"Seite {status or 'keine Verbindung'}")

    if not bild_url:
        try:
            if api is None:
                import spotify
                api = spotify.api
            t2, u2 = _web_api(typ, nr, api)
            titel = titel or t2
            bild_url = u2
            quelle = "api" if u2 else quelle
        except Exception as e:                            # keine Anmeldung, kein Netz ...
            probleme.append("Web API: " + str(e)[:80])

    bild = None
    if bild_url:
        for url in dict.fromkeys([groesser(bild_url), bild_url]):
            status, daten, _ = holen(url, MAX_BILD)
            bild = _bild_normal(daten) if status == 200 else None
            if bild:
                break
        if not bild:
            probleme.append("Bild nicht ladbar")
    meldung = None
    if not bild:
        meldung = "Zu diesem Link wurde kein Cover gefunden." + (" (" + "; ".join(probleme) + ")" if probleme else "")
    return {"titel": titel, "bild": bild, "quelle": quelle if bild else None, "meldung": meldung}


# ---------------------------------------------------------------- Zusammenfassung für die Eltern-Seite

def info(uri, extra=None):
    m = karten.meta_lesen(uri) or {}
    typ = uri.split(":")[1]
    return dict({"ok": True, "uri": uri, "link": karten.uri_zu_link(uri), "typ": typ,
                 "schluessel": karten.schluessel(uri), "titel": m.get("titel"),
                 "hat_cover": bool(m.get("hat_cover")), "quelle": m.get("quelle"),
                 "eigenes_bild": bool(m.get("eigen"))}, **(extra or {}))


def aufloesen(text, neu=False, holen=http_holen, api=None):
    """Eingefügten Link prüfen, Cover und Titel suchen (oder aus dem Speicher nehmen) und ablegen."""
    try:
        uri = adresse_aus_text(text, holen)
    except ValueError as e:
        return {"ok": False, "meldung": str(e)}
    return nachschlagen(uri, neu=neu, holen=holen, api=api)


def nachschlagen(uri, neu=False, holen=http_holen, api=None):
    m = karten.meta_lesen(uri)
    if m and not neu and m.get("titel") and (m.get("hat_cover") or m.get("eigen")):
        return info(uri)                                   # schon da: ohne Netz
    erg = suchen(uri, holen, api)
    eigen = bool(m and m.get("eigen")) and not neu
    if erg["titel"] or erg["bild"]:
        karten.meta_schreiben(uri, titel=erg["titel"], bild=None if eigen else erg["bild"],
                              quelle=None if eigen else erg["quelle"], eigen=False if neu else eigen)
    return info(uri, {"meldung": erg["meldung"]})


def eigenes_bild(uri, daten):
    """Vom Benutzer hochgeladenes Bild als Cover dieser Adresse speichern."""
    jpeg = _bild_normal(daten)
    if not jpeg:
        return {"ok": False, "meldung": "Das ist kein brauchbares Bild (JPEG oder PNG)."}
    karten.meta_schreiben(uri, bild=jpeg, quelle="eigen", eigen=True)
    return info(uri)
