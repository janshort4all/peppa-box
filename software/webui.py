"""Statusseite fuer das Handy: zeigt die aufgelegte Karte und den Link, der auf ihr steht.

Laeuft im Player-Prozess auf Port 8080 im Heimnetz. Nur Anzeige, keine Einstellungen.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ZUSTAND = {"karte": None, "link": None}     # vom Player gesetzt

SEITE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Peppa Box</title>
<style>
:root { --bg:#fbf6ef; --karte:#fff; --text:#2b2420; --leise:#7a6d63; --orange:#e8792b; --rand:#eadfd3; }
@media (prefers-color-scheme: dark) { :root { --bg:#1d1a17; --karte:#2a2622; --text:#f3ece4; --leise:#b5a89c; --rand:#3d3731; } }
body { margin:0; background:var(--bg); color:var(--text); font:16px/1.45 system-ui, sans-serif; }
main { max-width:560px; margin:0 auto; padding:16px; }
h1 { font-size:22px; margin:8px 0 16px; } h1 span { color:var(--orange); }
.box { background:var(--karte); border:1px solid var(--rand); border-radius:14px; padding:16px; margin-bottom:16px; }
.leise { color:var(--leise); font-size:14px; }
.uid { font-family:ui-monospace, monospace; font-size:18px; }
#link { word-break:break-all; margin-top:8px; }
.punkt { display:inline-block; width:10px; height:10px; border-radius:50%; background:var(--rand); margin-right:6px; }
.an { background:var(--orange); }
ol { padding-left:20px; margin:0; } li { margin:4px 0; }
</style></head>
<body><main>
<h1><span>Peppa</span> Box</h1>
<div class="box">
  <div class="leise"><span id="punkt" class="punkt"></span>Aufgelegte Karte</div>
  <div class="uid" id="uid">keine</div>
  <div id="link" class="leise"></div>
</div>
<div class="box">
  <div class="leise" style="margin-bottom:8px">Karte bespielen (mit dem Handy)</div>
  <ol>
    <li>Spotify: Playlist → ⋯ → Teilen → Link kopieren</li>
    <li>NFC Tools: Schreiben → Datensatz hinzufügen → URL/URI → Link einfügen</li>
    <li>Schreiben tippen, Karte hinten ans Handy halten</li>
  </ol>
</div>
</main>
<script>
const $ = id => document.getElementById(id);
async function laden() {
  try {
    const s = await (await fetch('/api/status')).json();
    $('uid').textContent = s.karte || 'keine';
    $('punkt').className = 'punkt' + (s.karte ? ' an' : '');
    $('link').textContent = s.karte ? (s.link || 'Kein Link auf der Karte') : '';
  } catch (e) { $('uid').textContent = 'Keine Verbindung zur Box'; }
}
laden(); setInterval(laden, 1000);
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
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
            self._antwort(200, dict(ZUSTAND))
        else:
            self._antwort(404, {"fehler": "nicht gefunden"})


def starten(port=8080):
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
