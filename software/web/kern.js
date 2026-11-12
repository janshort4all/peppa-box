// Kern der Eltern-App: Zugriff auf die Box, gemeinsamer Zustand, kleine Helfer.
// Alle Seiten (alltag.js, karten.js, entwickler.js) benutzen nur das, was hier steht.

export const $ = (sel, el = document) => el.querySelector(sel);
export const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
export const NB = ' ';                                    // geschütztes Leerzeichen (Zahl und Einheit zusammenhalten)

export function esc(t) {
  return String(t ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}

// ------------------------------------------------------------ gemeinsamer Zustand

// karte: /api/karte (jede Sekunde), zustand: /api/zustand (alle 5 s), einst: Einstellungen,
// karten: Kartenliste samt Etikett-Angaben, offline: Box gerade nicht erreichbar
export const S = {karte: null, zustand: null, einst: null, ausgaenge: {}, karten: null, offline: false, stand: 0};
export const bus = new EventTarget();
const melde = name => bus.dispatchEvent(new Event(name));

/** Auf Änderungen hören (und einmal sofort aufrufen); endet mit `signal`, wenn die Seite verlassen wird. */
export function abo(signal, name, fn, sofort = true) {
  bus.addEventListener(name, fn, {signal});
  if (sofort) fn();
}

// ------------------------------------------------------------ Verbindung zur Box

export async function holen(pfad) {
  const r = await fetch(pfad, {cache: 'no-store'});
  return r.json();
}
export async function senden(pfad, daten) {
  const kopf = {'X-Peppa-Box': '1'};
  if (daten !== undefined) kopf['Content-Type'] = 'application/json';
  const r = await fetch(pfad, {method: 'POST', headers: kopf, body: daten !== undefined ? JSON.stringify(daten) : undefined});
  return r.json();
}
export const KEINE_VERBINDUNG = {ok: false, meldung: 'Keine Verbindung zur Box. Ist sie an und im WLAN?'};
/** Wie senden, aber ohne Ausnahme bei Verbindungsfehlern. */
export async function sicher(pfad, daten) {
  try { return await senden(pfad, daten); } catch (x) { return KEINE_VERBINDUNG; }
}
/** Eine Datei als Anfragetext hochladen (eigenes Cover). */
export async function hochladen(pfad, datei) {
  try {
    const r = await fetch(pfad, {method: 'POST', headers: {'X-Peppa-Box': '1', 'Content-Type': datei.type || 'application/octet-stream'}, body: datei});
    return await r.json();
  } catch (x) { return KEINE_VERBINDUNG; }
}

let laeuft = {};
async function einmal(name, tun) {                             // nie zwei gleiche Abfragen gleichzeitig
  if (laeuft[name]) return;
  laeuft[name] = true;
  try { await tun(); } finally { laeuft[name] = false; }
}
function offline(wert) {
  if (S.offline !== wert) { S.offline = wert; melde('verbindung'); }
}
export function karteLaden() {
  return einmal('karte', async () => {
    try { S.karte = await holen('/api/karte'); offline(false); } catch (e) { offline(true); }
    melde('karte');
  });
}
export function zustandLaden() {
  return einmal('zustand', async () => {
    try { S.zustand = await holen('/api/zustand'); offline(false); melde('zustand'); } catch (e) { offline(true); }
  });
}
export async function einstLaden() {
  const stand = S.stand;
  try {
    const e = await holen('/api/einstellungen');
    if (stand !== S.stand) return;                             // inzwischen gespeichert: diese Antwort ist veraltet
    S.einst = e.einstellungen; S.ausgaenge = e.ausgaben; melde('einst');
  } catch (x) { /* beim nächsten Öffnen erneut */ }
}
export async function kartenLaden() {
  try { S.karten = await holen('/api/karten'); melde('karten'); } catch (x) { /* nächste Runde */ }
}
/** Einstellungen speichern, z. B. {ruhezeit: {...}}. Bei Erfolg gilt die Antwort der Box sofort überall. */
export async function einstSpeichern(teil) {
  S.stand++;
  const erg = await sicher('/api/einstellungen', teil);
  S.stand++;
  if (erg.ok) { S.einst = erg.einstellungen; melde('einst'); }
  return erg;
}

export function starten() {
  karteLaden(); zustandLaden(); einstLaden();
  const sichtbar = () => document.visibilityState === 'visible';
  setInterval(() => { if (sichtbar()) karteLaden(); }, 1000);
  setInterval(() => { if (sichtbar()) zustandLaden(); }, 5000);
  document.addEventListener('visibilitychange', () => { if (sichtbar()) { karteLaden(); zustandLaden(); } });
}

// Zeitpunkt der letzten Bedienung: kurz danach keine Werte von der Box in Regler schreiben
export const bedient = {zeit: 0};
['input', 'change', 'click'].forEach(ev => document.addEventListener(ev, () => { bedient.zeit = Date.now(); }, true));

// ------------------------------------------------------------ Rückmeldungen

let toastZeit = 0;
/** Kurze Meldung unten im Bild (verschwindet von selbst). */
export function toast(text, art = 'ok', ms) {
  const feld = $('#toasts');
  if (!feld) return;
  feld.innerHTML = '';
  const t = document.createElement('div');
  t.className = 'toast ' + art;
  t.textContent = text;
  feld.appendChild(t);
  clearTimeout(toastZeit);
  toastZeit = setTimeout(() => { t.remove(); }, ms || (art === 'ok' ? 3500 : 7000));
}
/** Text in die Zwischenablage. Im Heimnetz läuft die Seite über http (kein navigator.clipboard),
 *  darum der alte Weg über ein unsichtbares Textfeld; muss direkt im Klick aufgerufen werden. */
export async function kopieren(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try { await navigator.clipboard.writeText(text); return true; } catch (e) { /* alter Weg */ }
  }
  const feld = document.createElement('textarea');
  feld.value = text;
  feld.setAttribute('readonly', '');
  feld.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;font-size:16px';
  document.body.appendChild(feld);
  feld.select();
  feld.setSelectionRange(0, text.length);
  let ok = false;
  try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
  feld.remove();
  return ok;
}

/** Antwort der Box melden: Erfolg kurz, Fehler lang. */
export function melden(erg, okText) {
  toast(erg.meldung || (erg.ok ? okText || 'Erledigt.' : 'Das hat nicht geklappt.'), erg.ok ? 'ok' : 'fehler');
}

/** Rückfrage mit Dialog. Ergibt true bei Bestätigung. */
export function frage({titel, text = '', ok = 'OK', art = 'haupt', abbrechen = 'Abbrechen'}) {
  return new Promise(fertig => {
    const d = document.createElement('dialog');
    d.className = 'frage';
    d.innerHTML = `<h3>${esc(titel)}</h3><p class="leise">${esc(text)}</p>
      <div class="reihe"><button class="btn" value="nein">${esc(abbrechen)}</button>
      <button class="btn ${art}" value="ja">${esc(ok)}</button></div>`;
    let antwort = false;
    d.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (b) { antwort = b.value === 'ja'; d.close(); }
    });
    d.addEventListener('close', () => { d.remove(); fertig(antwort); });
    document.body.appendChild(d);
    d.showModal();
  });
}

// ------------------------------------------------------------ Darstellung

const SYMBOLE = {
  start: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
  karten: '<rect x="3" y="7" width="14" height="13" rx="2.5"/><path d="M7 4h11a3 3 0 0 1 3 3v10"/><path d="M7.5 13.5a3.5 3.5 0 0 1 3 0"/>',
  zeiten: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  hilfe: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.3c-.7.4-1 .9-1 1.7"/><path d="M12 17h.01"/>',
  ton: '<path d="M4 9v6h4l5 4V5L8 9z"/><path d="M16 9a4 4 0 0 1 0 6"/><path d="M18.5 6.5a8 8 0 0 1 0 11"/>',
  bedienung: '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
  etikett: '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.2"/>',
  system: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  haken: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  kreuz: '<path d="M6 6l12 12M18 6L6 18"/>',
  laden: '<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5"/><path d="M5 19h14"/>',
  neu: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
  bild: '<rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="9" cy="10" r="1.8"/><path d="M4 18l5-5 4 4 3-3 4 4"/>',
  papierkorb: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  einfuegen: '<rect x="6" y="5" width="12" height="16" rx="2"/><path d="M9 5V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1"/>',
  akku: '<rect x="3" y="8" width="16" height="9" rx="2"/><path d="M21 11v3"/>',
  wlan: '<path d="M3 9a14 14 0 0 1 18 0"/><path d="M6 12.5a9.5 9.5 0 0 1 12 0"/><path d="M9 16a5 5 0 0 1 6 0"/><path d="M12 19.5h.01"/>',
  musik: '<path d="M9 18V6l11-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
  schloss: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  kopieren: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
};
export function symbol(name, klasse = '') {
  return `<svg class="sym ${klasse}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${SYMBOLE[name] || ''}</svg>`;
}

/** Cover als Bild; ohne Cover ein Platzhalter mit dem Peppa-Box-Logo. */
export function coverBild(url, klasse = '', alt = '') {
  if (url) return `<img class="cover ${klasse}" src="${esc(url)}" alt="${esc(alt)}" loading="lazy">`;
  return `<div class="cover leer ${klasse}" role="img" aria-label="Kein Cover"><img src="/logo.png" alt=""></div>`;
}
export const TYPEN = {playlist: 'Playlist', album: 'Album', show: 'Podcast', episode: 'Folge', track: 'Titel', artist: 'Künstler'};

export function datum(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE') + ', ' + d.toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'});
}
export function dauer(s) {
  const t = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60);
  return t ? `${t} T ${h} Std` : h ? `${h} Std ${m} Min` : `${m} Min`;
}

/** Der Zustand der Box in einfachen Worten: Liste von {art: 'gut'|'warn'|'rot'|'', titel, wert, klein}. */
export function zustandTexte(z) {
  const erg = {};
  const a = z.akku;
  if (a.fehler) erg.akku = {art: 'warn', wert: '–', klein: a.fehler};
  else {
    const laedt = a.prozent == null;
    const r = {laedt: 'Netzteil steckt, Akku wird geladen', akku: 'Akkubetrieb', voll: 'Netzteil steckt, Akku voll', ruhend: 'kaum Strom'}[a.richtung] || '';
    erg.akku = {art: laedt ? 'warn' : a.prozent < 15 ? 'rot' : a.prozent < 30 ? 'warn' : 'gut',
                wert: laedt ? 'lädt' : a.prozent + NB + '%', prozent: laedt ? null : a.prozent, laedt,
                klein: `${r} · ${a.spannung.toFixed(2).replace('.', ',')} V · ` + (laedt ? 'Prozent erst ohne Netzteil'
                       + (a.prozent_ohne_netzteil != null ? ` · zuletzt ${a.prozent_ohne_netzteil} % ohne Netzteil` : '') : 'Prozent geschätzt')};
  }
  const p = z.player, sp = z.dienste.raspotify === 'active';
  if (!p.laeuft) erg.musik = {art: 'rot', wert: 'Aus', klein: 'Die Box-Software läuft nicht.'};
  else if (p.problem) erg.musik = {art: 'warn', wert: 'Kümmert sich', klein: String(p.problem)};
  else if (!sp || !p.spotify_bereit) erg.musik = {art: 'warn', wert: 'Wartet auf Spotify', klein: 'Dauert nach dem Einschalten einen Moment.'};
  else erg.musik = {art: 'gut', wert: 'Bereit', klein: ''};
  const w = z.wlan;
  if (w.dbm == null) erg.wlan = {art: 'rot', wert: 'Kein WLAN', klein: ''};
  else {
    const k = w.dbm > -60 ? ['Gut', 'gut'] : w.dbm > -70 ? ['Mittel', 'warn'] : ['Schwach', 'rot'];
    erg.wlan = {art: k[1], wert: k[0], klein: w.name || ''};
  }
  if (z.temperatur != null) erg.temp = {art: z.temperatur < 65 ? 'gut' : z.temperatur < 78 ? 'warn' : 'rot', wert: z.temperatur.toFixed(0) + NB + '°C', klein: ''};
  erg.platte = {art: z.speicher_frei_gb > 2 ? 'gut' : 'warn', wert: String(z.speicher_frei_gb).replace('.', ',') + NB + 'GB', klein: ''};
  const s = z.strom;
  if (!s.bekannt) erg.strom = {art: '', wert: 'Unbekannt', klein: ''};
  else if (s.jetzt) erg.strom = {art: 'rot', wert: 'Unterspannung!', klein: 'Netzteil oder Kabel prüfen.'};
  else if (s.seit_start) erg.strom = {art: 'warn', wert: 'OK', klein: 'kurz zu wenig seit dem Einschalten'};
  else erg.strom = {art: 'gut', wert: 'OK', klein: ''};
  erg.laufzeit = {art: '', wert: dauer(z.laufzeit_s), klein: ''};
  return erg;
}

// ------------------------------------------------------------ Aktionen an der Box (mit Rückfrage und Wartebild)

const FRAGEN = {
  update:   ['Jetzt aktualisieren?', 'Die Musik stoppt kurz und startet neu.', '/api/update/starten', 'Aktualisieren'],
  zurueck:  ['Zurück zur vorherigen Version?', 'Die Musik stoppt kurz und startet neu.', '/api/update/zurueck', 'Zurück'],
  musik:    ['Musik neu starten?', 'Spotify und Player starten neu, das dauert etwa 10 Sekunden. Die Box bleibt an.', '/api/musik-neustart', 'Neu starten'],
  neustart: ['Box neu starten?', 'Die Box ist etwa eine Minute nicht erreichbar. Diese Seite verbindet sich danach von selbst wieder.', '/api/neustart', 'Neu starten'],
  aus:      ['Box ausschalten?', 'Wieder einschalten: Ein-Taste an der Box oder Schalter am Akku-Board.', '/api/ausschalten', 'Ausschalten', 'gefahr'],
};
function vollbild(titel, text) {
  let v = $('#voll');
  if (!v) { v = document.createElement('div'); v.id = 'voll'; v.className = 'voll'; document.body.appendChild(v); }
  v.innerHTML = `<img src="/logo.png" alt="" style="height:90px;margin-bottom:18px"><div class="gross">${esc(titel)}</div><p class="leise">${esc(text)}</p>`;
  v.classList.remove('versteckt');
}
async function warteBisZurueck(neuLaden) {
  await new Promise(r => setTimeout(r, 3000));
  for (let i = 0; i < 90; i++) {
    try {
      await holen('/api/karte');
      if (neuLaden) { location.reload(); return; }              // neue Fassung der Seite holen
      $('#voll').classList.add('versteckt'); zustandLaden(); return;
    } catch (e) { /* noch nicht da */ }
    await new Promise(r => setTimeout(r, 2000));
  }
  const p = $('#voll p'); if (p) p.textContent = 'Die Box meldet sich nicht. Ist sie an und im WLAN?';
}
/** Rückfrage stellen, Aktion ausführen, Ergebnis zeigen. Ergibt die Antwort der Box oder null (abgebrochen). */
export async function boxAktion(was) {
  const [titel, text, pfad, knopf, art] = FRAGEN[was];
  if (!await frage({titel, text, ok: knopf, art: art || 'haupt'})) return null;
  const e = await sicher(pfad);
  if (!e.ok) { melden(e); return e; }
  if (was === 'aus') vollbild('Die Box fährt herunter', 'Nach etwa 20 Sekunden ist sie aus. Erst dann Kabel umstecken oder den Schalter am Akku-Board betätigen.');
  else if (was === 'neustart') { vollbild('Die Box startet neu', 'Diese Seite verbindet sich danach von selbst wieder.'); warteBisZurueck(false); }
  else if (e.neustart_seite) {
    const probe = await holen('/api/zustand').then(z => z.probelauf).catch(() => false);
    if (!probe) { vollbild('Update eingespielt', e.meldung); warteBisZurueck(true); } else { melden(e); zustandLaden(); }
  } else { melden(e); setTimeout(zustandLaden, 4000); }
  return e;
}
