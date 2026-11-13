// Peppa Box – Eltern-App: Gerüst, Navigation, Seitenwechsel.
// Zwei Bereiche: "Alltag" (Start, Karten, Zeiten, Hilfe) und "Entwickler" (Ton, Bedienung, Etiketten, System).
import {$, $$, S, abo, bus, coverBild, esc, starten, symbol} from './kern.js';

const SEITEN = [
  {pfad: 'start', name: 'Start', bereich: 'alltag', symbol: 'start', laden: () => import('./alltag.js').then(m => m.start)},
  {pfad: 'karten', name: 'Karten', bereich: 'alltag', symbol: 'karten', laden: () => import('./karten.js').then(m => m.liste)},
  {pfad: 'karten/neu', name: 'Karte bespielen', bereich: 'alltag', symbol: 'karten', versteckt: true, laden: () => import('./karten.js').then(m => m.assistent)},
  {pfad: 'zeiten', name: 'Zeiten', bereich: 'alltag', symbol: 'zeiten', laden: () => import('./alltag.js').then(m => m.zeiten)},
  {pfad: 'wlan', name: 'WLAN', bereich: 'alltag', symbol: 'wlan', laden: () => import('./alltag.js').then(m => m.wlan)},
  {pfad: 'hilfe', name: 'Hilfe', bereich: 'alltag', symbol: 'hilfe', laden: () => import('./alltag.js').then(m => m.hilfe)},
  {pfad: 'dev/ton', name: 'Ton', bereich: 'dev', symbol: 'ton', laden: () => import('./entwickler.js').then(m => m.ton)},
  {pfad: 'dev/bedienung', name: 'Bedienung', bereich: 'dev', symbol: 'bedienung', laden: () => import('./entwickler.js').then(m => m.bedienung)},
  {pfad: 'dev/etiketten', name: 'Etiketten', bereich: 'dev', symbol: 'etikett', laden: () => import('./entwickler.js').then(m => m.etiketten)},
  {pfad: 'dev/system', name: 'System', bereich: 'dev', symbol: 'system', laden: () => import('./entwickler.js').then(m => m.system)},
];
const BEREICHE = {alltag: {name: 'Alltag', start: 'start'}, dev: {name: 'Entwickler', start: 'dev/ton'}};

function merken(bereich, pfad) {                                       // letzte Seite je Bereich (nur eine Annehmlichkeit)
  try { localStorage.setItem('peppa-' + bereich, pfad); } catch (e) { /* ohne Speicher geht es auch */ }
}
function gemerkt(bereich) {
  try { return localStorage.getItem('peppa-' + bereich) || BEREICHE[bereich].start; } catch (e) { return BEREICHE[bereich].start; }
}
function bereichsschalter() {
  return `<div class="bereich" role="group" aria-label="Bereich">` + Object.entries(BEREICHE).map(([b, v]) =>
    `<a href="#/${gemerkt(b)}" class="${b === 'dev' ? 'dev' : ''}" data-bereich="${b}" aria-current="false">${v.name}</a>`).join('') + '</div>';
}

function geruest() {
  $('#app').innerHTML = `
    <div id="banner" class="banner versteckt" role="alert">Keine Verbindung zur Box. Ist sie an und im WLAN?</div>
    <header class="kopf"><img class="logo" src="/logo.png" alt="Peppa Box"><div class="rest" id="chip-kopf"></div>${bereichsschalter()}</header>
    <aside class="seitenleiste" id="seitenleiste">
      <img class="logo" src="/logo.png" alt="Peppa Box">
      ${bereichsschalter()}
      <nav id="nav-seite" aria-label="Seiten"></nav>
      <div class="unten"><div id="chip-seite"></div><div class="leise klein" id="rechner"></div></div>
    </aside>
    <main class="seite" id="seite" tabindex="-1"></main>
    <nav class="leiste" id="leiste" aria-label="Seiten"></nav>
    <div id="toasts" aria-live="polite"></div>`;
}

function navigation(aktuell) {
  const alle = SEITEN.filter(s => s.bereich === aktuell.bereich && !s.versteckt);
  const sichtbar = aktuell.pfad === 'karten/neu' ? 'karten' : aktuell.pfad;
  const html = alle.map(s => `<a href="#/${s.pfad}" ${s.pfad === sichtbar ? 'aria-current="page"' : ''}>${symbol(s.symbol)}<span>${s.name}</span></a>`).join('');
  $('#nav-seite').innerHTML = html; $('#leiste').innerHTML = html;
  $('#seitenleiste').classList.toggle('dev', aktuell.bereich === 'dev');
  $$('.bereich a').forEach(a => a.setAttribute('aria-current', String(a.dataset.bereich === aktuell.bereich)));
  $$('.bereich a').forEach(a => { a.href = '#/' + (a.dataset.bereich === aktuell.bereich ? aktuell.pfad : gemerkt(a.dataset.bereich)); });
}

// ------------------------------------------------------------ Seitenwechsel

let ende = null;                                                       // beendet Abfragen und Zuhörer der verlassenen Seite
let nummer = 0;
async function zeigen() {
  const pfad = (location.hash.replace(/^#\/?/, '').split('?')[0]) || 'start';
  const seite = SEITEN.find(s => s.pfad === pfad) || SEITEN[0];
  if (ende) ende.abort();
  ende = new AbortController();
  const meine = ++nummer;
  merken(seite.bereich, seite.versteckt ? 'karten' : seite.pfad);
  navigation(seite);
  document.title = seite.name + ' · Peppa Box';
  const wurzel = $('#seite');
  wurzel.innerHTML = (seite.bereich === 'dev'
    ? `<div class="dev-hinweis">${symbol('schloss')}<span>Entwickler-Einstellungen: Hier bitte nur etwas ändern, wenn du weißt, was es bewirkt.</span></div>` : '')
    + '<div id="inhalt"></div>';
  try {
    const rendern = await seite.laden();
    if (meine !== nummer) return;                                      // inzwischen woanders
    await rendern($('#inhalt'), ende.signal);
  } catch (e) {
    console.error(e);
    if (meine === nummer) $('#inhalt').innerHTML = `<div class="hinweis fehler">Diese Seite ließ sich nicht laden (${esc(e.message || e)}). Bitte die Seite neu laden.</div>`;
  }
  if (meine === nummer) window.scrollTo(0, 0);
}

// ------------------------------------------------------------ Kopfzeile: Karte im Fach, Verbindung

function kartenchip() {
  const k = S.karte, d = k && k.laeuft ? k.kartendaten : null;
  let html = '';
  if (d) {
    const titel = d.titel || (d.uri ? 'Karte im Fach' : 'Karte ohne Playlist');
    html = `<a class="chip-karte" href="#/start" title="${esc(titel)}">${d.cover ? coverBild(d.cover, '', '') : '<span class="punkt an" style="margin:8px 0 8px 8px"></span>'}<span>${esc(titel)}</span></a>`;
  }
  const sig = html;
  ['#chip-kopf', '#chip-seite'].forEach(id => { const e = $(id); if (e && e.dataset.sig !== sig) { e.innerHTML = html; e.dataset.sig = sig; } });
}

geruest();
abo(new AbortController().signal, 'karte', kartenchip, false);
bus.addEventListener('verbindung', () => $('#banner').classList.toggle('versteckt', !S.offline));
bus.addEventListener('zustand', () => { $('#rechner').textContent = S.zustand ? S.zustand.rechner : ''; });
window.addEventListener('hashchange', zeigen);
starten();
zeigen();
if ('serviceWorker' in navigator && window.isSecureContext) navigator.serviceWorker.register('/sw.js').catch(() => {});
