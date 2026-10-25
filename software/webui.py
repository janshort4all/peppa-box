"""Einstellungsseite fuer das Handy: Karten anlernen, umbenennen, loeschen.

Laeuft im Player-Prozess (der Player besitzt den Leser) auf Port 8080 im Heimnetz.
Kein Passwort: Jeder im eigenen WLAN kann die Karten aendern.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import karten
import spotify

ZUSTAND = {"karte": None}          # vom Player gesetzt: aktuell aufgelegte Karte
NEU_LADEN = threading.Event()       # vom Web gesetzt: aufgelegte Karte neu auswerten (nach Speichern)
_LOCK = threading.Lock()

SEITE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Peppa Box</title>
<style>
:root { --bg:#fbf6ef; --karte:#fff; --text:#2b2420; --leise:#7a6d63; --orange:#e8792b; --rand:#eadfd3; --rot:#c0392b; }
@media (prefers-color-scheme: dark) { :root { --bg:#1d1a17; --karte:#2a2622; --text:#f3ece4; --leise:#b5a89c; --rand:#3d3731; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:16px/1.45 system-ui, sans-serif; }
main { max-width:560px; margin:0 auto; padding:16px; }
h1 { font-size:22px; margin:8px 0 16px; }
h1 span { color:var(--orange); }
.box { background:var(--karte); border:1px solid var(--rand); border-radius:14px; padding:16px; margin-bottom:16px; }
.leise { color:var(--leise); font-size:14px; }
.uid { font-family:ui-monospace, monospace; font-size:18px; }
label { display:block; font-size:14px; color:var(--leise); margin:12px 0 4px; }
input { width:100%; font:inherit; padding:12px; border:1px solid var(--rand); border-radius:10px; background:var(--bg); color:var(--text); }
button { font:inherit; border:0; border-radius:10px; padding:12px 16px; cursor:pointer; }
.haupt { background:var(--orange); color:#fff; width:100%; margin-top:16px; font-weight:600; }
.haupt:disabled { opacity:.45; }
.klein { background:transparent; color:var(--rot); padding:6px 8px; }
ul { list-style:none; padding:0; margin:0; }
li { display:flex; align-items:center; gap:8px; padding:10px 0; border-top:1px solid var(--rand); }
li:first-child { border-top:0; }
li div { flex:1; min-width:0; }
li b, li small { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.punkt { display:inline-block; width:10px; height:10px; border-radius:50%; background:var(--rand); margin-right:6px; }
.an { background:var(--orange); }
#meldung { min-height:1.4em; margin-top:8px; font-size:14px; }
</style></head>
<body><main>
<h1><span>Peppa</span> Box – Karten</h1>

<div class="box">
  <div class="leise"><span id="punkt" class="punkt"></span>Aufgelegte Karte</div>
  <div class="uid" id="uid">keine – Karte auf den Leser legen</div>
  <div id="zuordnung" class="leise"></div>
  <label for="link">Spotify-Link (Playlist oder Album: Teilen → Link kopieren)</label>
  <input id="link" inputmode="url" placeholder="https://open.spotify.com/playlist/…">
  <label for="name">Name der Karte</label>
  <input id="name" placeholder="z. B. Peppa Folge 1">
  <button class="haupt" id="speichern" disabled>Für diese Karte speichern</button>
  <div id="meldung"></div>
</div>

<div class="box">
  <div class="leise" style="margin-bottom:8px">Angelernte Karten</div>
  <ul id="liste"></ul>
</div>
</main>
<script>
let aufgelegt = null, karten = {};
const $ = id => document.getElementById(id);

async function laden() {
  try {
    const s = await (await fetch('/api/status')).json();
    karten = s.karten;
    if (s.karte !== aufgelegt) {
      aufgelegt = s.karte;
      const e = aufgelegt && karten[aufgelegt];
      $('name').value = e ? (e.name || '') : '';
      $('link').value = '';
    }
    $('uid').textContent = aufgelegt || 'keine – Karte auf den Leser legen';
    $('punkt').className = 'punkt' + (aufgelegt ? ' an' : '');
    const e = aufgelegt && karten[aufgelegt];
    $('zuordnung').textContent = aufgelegt ? (e ? 'Spielt: ' + (e.name || e.uri) : 'Noch nicht zugeordnet') : '';
    $('speichern').disabled = !aufgelegt;
    const ul = $('liste'); ul.replaceChildren();
    const uids = Object.keys(karten).sort((a, b) => (karten[a].name || '').localeCompare(karten[b].name || ''));
    if (!uids.length) { const li = document.createElement('li'); li.textContent = 'Noch keine Karten.'; ul.append(li); }
    for (const u of uids) {
      const li = document.createElement('li'), d = document.createElement('div');
      const b = document.createElement('b'), sm = document.createElement('small');
      b.textContent = karten[u].name || '(ohne Name)'; sm.className = 'leise'; sm.textContent = u + ' · ' + karten[u].uri;
      d.append(b, sm);
      const x = document.createElement('button'); x.className = 'klein'; x.textContent = 'Löschen';
      x.onclick = async () => { if (confirm('Karte „' + (karten[u].name || u) + '“ löschen?')) { await senden('/api/loeschen', {uid: u}); laden(); } };
      li.append(d, x); ul.append(li);
    }
  } catch (err) { $('uid').textContent = 'Keine Verbindung zur Box'; }
}

async function senden(url, daten) {
  const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(daten)});
  return r.json();
}

$('speichern').onclick = async () => {
  const link = $('link').value.trim(), name = $('name').value.trim();
  const alt = karten[aufgelegt];
  if (!link && !alt) { $('meldung').textContent = 'Bitte einen Spotify-Link einfügen.'; return; }
  const a = await senden('/api/karten', {uid: aufgelegt, link: link, name: name});
  $('meldung').textContent = a.ok ? 'Gespeichert.' : a.fehler;
  laden();
};

laden(); setInterval(laden, 1000);
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):          # kein Protokoll jeder Anfrage
        pass

    def _antwort(self, code, daten, typ="application/json; charset=utf-8"):
        body = daten.encode() if isinstance(daten, str) else json.dumps(daten, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._antwort(200, SEITE, "text/html; charset=utf-8")
        elif self.path == "/api/status":
            self._antwort(200, {"karte": ZUSTAND["karte"], "karten": karten.laden()})
        else:
            self._antwort(404, {"fehler": "nicht gefunden"})

    def do_POST(self):
        try:
            laenge = int(self.headers.get("Content-Length", 0))
            daten = json.loads(self.rfile.read(min(laenge, 10000)) or b"{}")
        except ValueError:
            return self._antwort(400, {"ok": False, "fehler": "Ungültige Anfrage"})
        uid = str(daten.get("uid") or "")
        with _LOCK:
            alle = karten.laden()
            if self.path == "/api/karten":
                if not uid:
                    return self._antwort(400, {"ok": False, "fehler": "Keine Karte aufgelegt"})
                link = str(daten.get("link") or "").strip()
                name = str(daten.get("name") or "").strip()[:80]
                if link:
                    try:
                        uri = spotify.link_zu_uri(link)
                    except ValueError:
                        return self._antwort(400, {"ok": False, "fehler": "Das ist kein Spotify-Link."})
                elif uid in alle:
                    uri = alle[uid]["uri"]          # nur umbenennen
                else:
                    return self._antwort(400, {"ok": False, "fehler": "Bitte einen Spotify-Link einfügen."})
                alle[uid] = {"uri": uri, "name": name}
                karten.speichern(alle)
                NEU_LADEN.set()
                return self._antwort(200, {"ok": True})
            if self.path == "/api/loeschen":
                alle.pop(uid, None)
                karten.speichern(alle)
                return self._antwort(200, {"ok": True})
        self._antwort(404, {"ok": False, "fehler": "nicht gefunden"})


def starten(port=8080):
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
