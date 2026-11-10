// Alltag: Start, Zeiten, Hilfe. Einfache Worte, große Knöpfe; alles Technische steht unter "Entwickler".
import {$, NB, S, TYPEN, abo, bedient, boxAktion, coverBild, einstLaden, einstSpeichern, esc, melden, sicher, symbol, toast, zustandLaden, zustandTexte} from './kern.js';

// ------------------------------------------------------------ gemeinsam: Schlummer-Timer

function timerHtml() {
  return `<div id="tknoepfe" class="knoepfe">${[15, 30, 45, 60].map(m => `<button class="btn" data-min="${m}">${m}${NB}Min</button>`).join('')}</div>
    <div id="taktiv" class="versteckt"><div class="wert" id="trest"></div><button class="btn" id="tstopp" style="margin-top:10px">Timer abbrechen</button></div>
    <p class="leise klein">Nach der gewählten Zeit wird die Musik leiser und es ist Pause. Praktisch zum Einschlafen.</p>`;
}
function timerBinden(w, signal) {
  w.addEventListener('click', async e => {
    const b = e.target.closest('[data-min]');
    if (b) { melden(await sicher('/api/timer/starten', {minuten: +b.dataset.min})); zustandLaden(); }
    if (e.target.closest('#tstopp')) { melden(await sicher('/api/timer/abbrechen', {})); zustandLaden(); }
  }, {signal});
  abo(signal, 'zustand', () => {
    const t = S.zustand && S.zustand.zeiten.timer;
    $('#tknoepfe', w).classList.toggle('versteckt', !!t); $('#taktiv', w).classList.toggle('versteckt', !t);
    if (t) $('#trest', w).textContent = t.rest_s > 60 ? `Die Musik endet in ${Math.ceil(t.rest_s / 60)} Min.` : 'Die Musik endet gleich.';
  });
}

// ------------------------------------------------------------ Start

function heroHtml(k) {
  if (!k) return '<p class="leise">Verbinde mit der Box …</p>';
  if (!k.laeuft) return `<div class="hinweis fehler">Die Box-Software läuft gerade nicht. Das ist kurz nach dem Einschalten normal. Bleibt es so, hilft <a href="#/hilfe">die Hilfe</a>.</div>`;
  const d = k.kartendaten;
  const leser = k.leser ? `<div class="hinweis warn">${esc(k.leser)}</div>` : '';
  if (!d) {
    return `${leser}<div class="hero leerfach"><div><div class="fach">${symbol('karten')}</div>
      <div class="titel">Keine Karte im Fach</div>
      <p class="leise">Lege eine Karte auf das Kartenfach der Box, dann spielt die Musik.</p></div></div>`;
  }
  if (!d.uri) {
    return `${leser}<div class="hero leerfach"><div><div class="fach">${symbol('karten')}</div>
      <div class="titel">Diese Karte ist noch leer</div>
      <p class="leise">Auf der Karte steht noch keine Playlist. Mit einem Fingertipp bekommt sie eine.</p>
      <a class="btn haupt" href="#/karten/neu">${symbol('plus')} Jetzt bespielen</a></div></div>`;
  }
  const typ = TYPEN[d.typ] || 'Spotify';
  return `${leser}<div class="hero">
    <div>${coverBild(d.cover, d.cover ? '' : 'suche', d.titel || '')}</div>
    <div><div class="leise klein">Jetzt im Kartenfach</div>
      <div class="titel">${esc(d.titel || typ)}</div>
      <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap"><span class="marke">${esc(typ)}</span>
        ${d.link_auf_karte ? '' : '<span class="marke warn" title="Der Link steht nicht auf der Karte, sondern nur in dieser Box.">nur in dieser Box</span>'}</div>
      ${d.cover ? '' : '<p class="leise klein">Noch kein Cover. Unter „Karten“ kannst du ein eigenes Bild wählen.</p>'}</div></div>`;
}

export function start(w, signal) {
  w.innerHTML = `
    <h1>Peppa Box</h1>
    <p class="leise">Karte auflegen, Musik hören. Hier siehst du, was gerade los ist.</p>
    <section class="k" id="hero"></section>
    <a class="btn haupt gross" href="#/karten/neu" style="margin-bottom:14px">${symbol('plus')} Neue Karte bespielen</a>
    <section class="k"><h2>Lautstärke</h2>
      <div class="laut"><div class="zahl" id="lzahl">–</div>
        <div style="flex:1"><input type="range" id="lregler" min="0" max="100" step="1" disabled aria-label="Lautstärke"><div class="leise klein" id="ltext"></div></div></div></section>
    <section class="k"><h2>Schlummer-Timer</h2>${timerHtml()}</section>
    <section class="k"><h2>Zustand</h2><div id="ampel"></div>
      <div class="raster drei" style="margin-top:12px" id="minis"></div>
      <p class="klein" style="margin-bottom:0"><a href="#/dev/system">Alle Einzelheiten ansehen</a></p></section>`;

  // Karte im Fach: nur neu zeichnen, wenn sich etwas geändert hat (sonst flackern die Bilder)
  let zuletzt = null;
  abo(signal, 'karte', () => {
    const k = S.karte, d = k && k.kartendaten;
    const sig = JSON.stringify([!!k, k && k.laeuft, k && k.leser, d]);
    if (sig === zuletzt) return;
    zuletzt = sig; $('#hero', w).innerHTML = heroHtml(k);
  });

  timerBinden(w, signal);

  // Lautstärke
  const regler = $('#lregler', w);
  let benutzt = 0;
  regler.addEventListener('input', e => { benutzt = Date.now(); $('#lzahl', w).textContent = e.target.value + NB + '%'; }, {signal});
  regler.addEventListener('change', async e => {
    benutzt = Date.now();
    const erg = await sicher('/api/lautstaerke', {prozent: +e.target.value});
    if (!erg.ok) { melden(erg); return; }
    e.target.value = erg.prozent; $('#lzahl', w).textContent = erg.prozent + NB + '%';
    if (erg.begrenzt) toast(`Lauter geht es nicht: Die Höchstlautstärke ist ${erg.prozent}${NB}%.`);
  }, {signal});
  abo(signal, 'zustand', () => {
    const z = S.zustand; if (!z) return;
    const l = z.lautstaerke;
    if (l.prozent == null) {
      regler.disabled = true; $('#lzahl', w).textContent = '–';
      $('#ltext', w).textContent = l.ausgaben[l.aktiv].eingerichtet ? 'Der Lautstärkeregler der Box antwortet nicht.' : 'Dieser Ausgang ist noch nicht eingerichtet.';
    } else {
      regler.disabled = false; regler.max = Math.max(l.max, 5);
      if (Date.now() - benutzt > 2500 && Date.now() - bedient.zeit > 800) { regler.value = l.prozent; $('#lzahl', w).textContent = l.prozent + NB + '%'; }
      $('#ltext', w).textContent = `${l.name} · höchstens ${l.max}${NB}%` + (l.max < l.max_ausgang ? ' (gerade Ruhezeit)' : '');
    }
    // Ampel: alles gut oder was zu tun ist
    const t = zustandTexte(z), probleme = [];
    if (t.musik.art !== 'gut') probleme.push([t.musik.art, 'Musik: ' + t.musik.wert + (t.musik.klein ? ' (' + t.musik.klein + ')' : '')]);
    if (t.akku.art === 'rot') probleme.push(['rot', 'Der Akku ist fast leer. Bitte Netzteil anschließen.']);
    else if (t.akku.art === 'warn' && !t.akku.laedt && t.akku.prozent != null) probleme.push(['warn', 'Der Akku wird leer (' + t.akku.wert + ').']);
    if (t.wlan.art === 'rot') probleme.push(['rot', 'Die Box hat kein WLAN. Ohne WLAN gibt es keine Musik von Spotify.']);
    else if (t.wlan.art === 'warn') probleme.push(['warn', 'Das WLAN ist schwach. Die Box näher an den Router stellen.']);
    if (t.strom.art === 'rot') probleme.push(['rot', 'Die Stromversorgung ist zu schwach. Bitte Netzteil und Kabel prüfen.']);
    $('#ampel', w).innerHTML = probleme.length
      ? probleme.map(p => `<div class="ampel ${p[0] === 'rot' ? 'rot' : 'warn'}" style="margin-bottom:8px">${symbol('hilfe')}<span>${esc(p[1])}</span></div>`).join('')
      : `<div class="ampel">${symbol('haken')}<span>Alles in Ordnung</span></div>`;
    const mini = (name, sym, x) => `<div class="kleinkarte"><div class="leise klein">${symbol(sym)} ${name}</div><div class="wert"><span class="punkt ${x.art}"></span>${esc(x.wert)}</div></div>`;
    $('#minis', w).innerHTML = mini('Akku', 'akku', t.akku) + mini('Musik', 'musik', t.musik) + mini('WLAN', 'wlan', t.wlan);
  });
}

// ------------------------------------------------------------ Zeiten

export function zeiten(w, signal) {
  w.innerHTML = `
    <h1>Zeiten</h1>
    <p class="leise">Wann endet die Musik, wann ist Ruhe? Änderungen gelten sofort.</p>
    <section class="k"><h2>Schlummer-Timer</h2>${timerHtml()}</section>
    <section class="k"><label class="zeile"><span><span class="wert">Ruhezeit</span><br><span class="leise klein" id="rtext">–</span></span>
        <input type="checkbox" class="schalter" id="ran" aria-label="Ruhezeit"></label>
      <p class="leise klein" style="margin-top:0">Zum Beispiel nachts: Dann spielt die Box leiser oder gar nicht.</p>
      <div id="raktiv" class="versteckt"><div class="hinweis" id="rhinweis"></div><button class="btn" id="rknopf"></button></div>
      <details id="rdetails"><summary>Ruhezeit einstellen</summary>
        <label class="zeile"><span>Von</span><input type="time" id="rvon" style="width:auto"></label>
        <label class="zeile"><span>Bis</span><input type="time" id="rbis" style="width:auto"></label>
        <label class="zeile"><span>Dann</span><select id="rmodus"><option value="leiser">leiser spielen</option><option value="aus">keine Musik</option></select></label>
        <div id="rleisewahl" class="grenze"><div class="kopfzeile"><span>Höchstens</span><b id="rleisew"></b></div>
          <input type="range" id="rleise" min="5" max="100" step="5" aria-label="Höchstlautstärke in der Ruhezeit"></div>
        <p class="leise klein" id="ruhr"></p>
        <button class="btn haupt" id="rspeichern">Speichern</button></details></section>
    <section class="k"><label class="zeile"><span><span class="wert">Automatisch ausschalten</span><br><span class="leise klein" id="atext">–</span></span>
        <input type="checkbox" class="schalter" id="aan" aria-label="Automatisch ausschalten"></label>
      <label class="zeile"><span>Ausschalten nach</span><select id="amin"><option value="10">10 Min</option><option value="20">20 Min</option>
        <option value="30">30 Min</option><option value="60">60 Min</option><option value="120">2 Std</option></select></label>
      <p class="leise klein" style="margin-bottom:0">Die Box schaltet sich aus, wenn so lange keine Musik läuft. Solange diese Seite geöffnet ist, bleibt sie an.</p></section>`;
  timerBinden(w, signal);
  einstLaden();

  let geaendert = false;                                       // im Formular verstellt, noch nicht gespeichert: nicht überschreiben
  $('#rdetails', w).addEventListener('input', () => { geaendert = true; }, {signal, capture: true});
  const modus = () => $('#rleisewahl', w).classList.toggle('versteckt', $('#rmodus', w).value !== 'leiser');
  $('#rmodus', w).addEventListener('change', modus, {signal});
  $('#rleise', w).addEventListener('input', e => { $('#rleisew', w).textContent = e.target.value + NB + '%'; }, {signal});
  const speichern = async (teil, ziel) => { const e = await einstSpeichern(teil); if (!e.ok) melden(e); else if (ziel) toast('Gespeichert.'); zustandLaden(); return e; };
  $('#ran', w).addEventListener('change', e => speichern({ruhezeit: {an: e.target.checked}}), {signal});
  $('#aan', w).addEventListener('change', e => speichern({auto_aus: {an: e.target.checked}}), {signal});
  $('#amin', w).addEventListener('change', e => speichern({auto_aus: {minuten: +e.target.value}}), {signal});
  $('#rspeichern', w).addEventListener('click', async () => {
    const e = await speichern({ruhezeit: {von: $('#rvon', w).value, bis: $('#rbis', w).value, modus: $('#rmodus', w).value, leise_max: +$('#rleise', w).value}}, true);
    if (e.ok) geaendert = false;                              // bei Fehler: Eingaben stehen lassen
  }, {signal});
  $('#rknopf', w).addEventListener('click', async e => {
    melden(await sicher('/api/ruhezeit/' + (e.currentTarget.dataset.aktion === 'aussetzen' ? 'aussetzen' : 'wieder'), {})); zustandLaden();
  }, {signal});

  abo(signal, 'einst', () => {
    const r = S.einst && S.einst.ruhezeit; if (!r || geaendert) return;
    $('#rvon', w).value = r.von; $('#rbis', w).value = r.bis; $('#rmodus', w).value = r.modus;
    $('#rleise', w).value = r.leise_max; $('#rleisew', w).textContent = r.leise_max + NB + '%'; modus();
  });
  abo(signal, 'zustand', () => {
    const t = S.zustand && S.zustand.zeiten; if (!t) return;
    const r = t.ruhezeit, a = t.auto_aus, aktiv = document.activeElement;
    if (aktiv !== $('#ran', w)) $('#ran', w).checked = r.an;
    $('#rtext', w).textContent = !r.an ? 'aus' : `${r.von} bis ${r.bis} Uhr · ` + (r.modus === 'leiser' ? `leiser, höchstens ${r.leise_max}${NB}%` : 'keine Musik');
    $('#raktiv', w).classList.toggle('versteckt', !(r.aktiv || r.ausgesetzt));
    if (r.aktiv) { $('#rhinweis', w).textContent = `Jetzt ist Ruhezeit (bis ${r.bis} Uhr).`; $('#rknopf', w).textContent = 'Für heute aussetzen'; }
    else if (r.ausgesetzt) { $('#rhinweis', w).textContent = `Die Ruhezeit ist bis ${r.bis} Uhr ausgesetzt.`; $('#rknopf', w).textContent = 'Ruhezeit wieder einschalten'; }
    $('#rknopf', w).dataset.aktion = r.aktiv ? 'aussetzen' : 'wieder';
    $('#ruhr', w).textContent = `Uhrzeit der Box: ${t.box.uhrzeit} (${t.box.zone})`;
    if (aktiv !== $('#aan', w)) $('#aan', w).checked = a.an;
    if (aktiv !== $('#amin', w)) {
      if (![...$('#amin', w).options].some(o => +o.value === a.minuten)) $('#amin', w).add(new Option(a.minuten + ' Min', a.minuten));
      $('#amin', w).value = a.minuten;
    }
    $('#atext', w).textContent = a.an ? `nach ${a.minuten} Min ohne Musik` : 'aus';
  });
}

// ------------------------------------------------------------ Hilfe

const FAQ = [
  ['Wie bespiele ich eine neue Karte?', `<ol class="schritte"><li><span>Tippe auf <b>Neue Karte bespielen</b>.</span></li>
    <li><span>Kopiere in Spotify den Link der Playlist (Playlist öffnen → drei Punkte → Teilen → Link kopieren) und füge ihn hier ein. Titel und Cover werden von allein gesucht.</span></li>
    <li><span>Lege die Karte auf das Kartenfach der Box. Fertig.</span></li></ol>`],
  ['Wie kommen die Etiketten auf die Karten?', `<ol class="schritte"><li><span>Unter <b>Karten</b> den Etikettenbogen (oder ein einzelnes Etikett) herunterladen. Jedes Etikett ist 40 × 40 mm groß und hat runde Ecken.</span></li>
    <li><span>Das Bild aufs Handy oder auf einen Stick legen und am Foto-Automaten im dm als Freiform-Sticker drucken.</span></li>
    <li><span>Etiketten ausschneiden lassen (das macht der Automat), aufkleben. Danach in der App „als gedruckt“ markieren.</span></li></ol>`],
  ['Die Karte spielt nichts', `<p>Schau auf der Startseite, ob die Box die Karte sieht: Dort erscheint der Titel der Playlist. Steht dort „Diese Karte ist noch leer“, muss sie zuerst bespielt werden. Wird die Karte gar nicht erkannt, die Karte mittig auf das Kartenfach legen und kurz warten. Hilft das nicht, unten <b>Musik neu starten</b> versuchen.</p>`],
  ['Die Musik hängt oder bricht ab', `<p>Prüfe auf der Startseite den <b>Zustand</b>: Ohne WLAN oder mit schwachem WLAN gibt es keine Musik von Spotify. Danach hilft meist <b>Musik neu starten</b> (unten). Die Box bleibt dabei an.</p>`],
  ['Was bedeutet „nur in dieser Box“?', `<p>Manche Karten lassen sich nicht beschreiben. Die Box merkt sich dann selbst, welche Playlist zur Karte gehört. Sie spielt wie jede andere Karte, aber nur an dieser Box.</p>`],
];

export function hilfe(w, signal) {
  w.innerHTML = `
    <h1>Hilfe</h1>
    <p class="leise">Antworten auf die häufigsten Fragen und die Schalter für den Notfall.</p>
    <section class="k"><h2>Häufige Fragen</h2>${FAQ.map(([f, a]) => `<details><summary>${esc(f)}</summary><div>${a}</div></details>`).join('')}</section>
    <section class="k"><h2>Wenn etwas nicht klappt</h2>
      <div class="stapel">
        <div><button class="btn gross" data-was="musik">${symbol('neu')} Musik neu starten</button><p class="leise klein">Hilft, wenn Spotify hängt. Die Box bleibt an.</p></div>
        <div class="reihe"><button class="btn" data-was="neustart">${symbol('neu')} Box neu starten</button><button class="btn gefahr" data-was="aus">Ausschalten</button></div>
      </div></section>
    <section class="k"><h2>Für Fortgeschrittene</h2><p class="leise">Lautstärke-Grenzen, Klang, Bedienelemente, Software-Update und Fehlersuche.</p>
      <a class="btn" href="#/dev/ton">${symbol('schloss')} Zu den Entwickler-Einstellungen</a></section>`;
  w.addEventListener('click', e => { const b = e.target.closest('[data-was]'); if (b) boxAktion(b.dataset.was); }, {signal});
}
