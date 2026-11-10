// Karten: Liste mit Covern, Etiketten (40 × 40 mm) zum Herunterladen und der Assistent "Karte bespielen".
import {$, S, TYPEN, abo, coverBild, esc, frage, hochladen, karteLaden, kartenLaden, melden, sicher, symbol, toast} from './kern.js';

const schl = uri => uri.split(':').slice(1).join('_');           // spotify:playlist:ABC -> playlist_ABC
const typName = t => TYPEN[t] || 'Spotify';
const NBS = '\u00a0';
let vorbelegt = null;                                              // Link, mit dem der Assistent beginnt ("Karte neu bespielen")

/** Bild für das Cover vor dem Hochladen verkleinern (Handyfotos sind groß; die Box nimmt höchstens 8 MB). */
async function verkleinern(datei) {
  try {
    const bmp = await createImageBitmap(datei);
    const f = Math.min(1, 1200 / Math.max(bmp.width, bmp.height));
    const c = document.createElement('canvas');
    c.width = Math.round(bmp.width * f); c.height = Math.round(bmp.height * f);
    c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
    return await new Promise(r => c.toBlob(b => r(b || datei), 'image/jpeg', 0.9));
  } catch (e) { return datei; }
}
async function bildHochladen(datei, schluessel) {
  const klein = await verkleinern(datei);
  if (klein.size > 8_000_000) return {ok: false, meldung: 'Das Bild ist zu groß (höchstens 8 MB).'};
  return hochladen('/api/cover/hochladen?s=' + encodeURIComponent(schluessel), klein);
}

// ------------------------------------------------------------ Liste

function kachel(k, imFach) {
  const marken = [
    imFach ? '<span class="marke">Im Fach</span>' : '',
    k.gedruckt ? '<span class="marke gut">Etikett gedruckt</span>' : '<span class="marke warn">Etikett offen</span>',
    k.auf_karte === false ? '<span class="marke" title="Der Link steht nicht auf der Karte, sondern nur in dieser Box.">nur in dieser Box</span>' : '',
  ].join('');
  return `<button class="kachel ${imFach ? 'imfach' : ''}" data-uid="${esc(k.uid)}">${coverBild(k.cover, '', k.titel)}
    <div class="t">${esc(k.titel)}</div><div class="marken">${marken}</div></button>`;
}

function etikettbox(e, liste) {
  if (!e) return '';
  if (!e.verfuegbar) {
    return `<h2>Etiketten (${e.groesse_mm} × ${e.groesse_mm} mm)</h2><div class="hinweis warn">Für die Etiketten fehlt auf der Box das Bildprogramm.
      Einmal am Pi eingeben: <b>sh ~/peppa-box/software/dienst_einrichten.sh</b></div>`;
  }
  if (!liste.length) return `<h2>Etiketten (${e.groesse_mm} × ${e.groesse_mm} mm)</h2><p class="leise" style="margin:0">Sobald du eine Karte bespielt hast, kannst du hier das Etikett dazu herunterladen.</p>`;
  const tipp = e.offen > 0 && e.offen < e.plaetze
    ? `<p class="leise klein"><b>Spartipp:</b> Auf einen Bogen passen ${e.plaetze} Etiketten. Mit ${e.plaetze - e.offen} weiteren Karten ist er voll, dann lohnt sich der Druck am meisten.</p>` : '';
  return `<h2>Etiketten (${e.groesse_mm} × ${e.groesse_mm} mm)</h2>
    <p style="margin-top:0">${e.offen === 0 ? 'Alle Etiketten sind gedruckt.' : e.offen === 1 ? '<b>1 Etikett</b> ist noch nicht gedruckt.' : `<b>${e.offen} Etiketten</b> sind noch nicht gedruckt.`}</p>
    ${e.offen ? `<div class="reihe"><a class="btn haupt" href="/etikett/bogen.png?laden=1" download>${symbol('laden')} Bogen laden (${Math.min(e.offen, e.plaetze)} ${Math.min(e.offen, e.plaetze) === 1 ? 'Etikett' : 'Etiketten'})</a>
      <button class="btn" id="gedruckt">${symbol('haken')} Als gedruckt markieren</button></div>${tipp}` : ''}
    <details id="druckhilfe"><summary>So kommen die Etiketten auf die Karten</summary>
      <ol class="schritte"><li><span><b>Bogen laden</b> und das Bild aufs Handy oder auf einen Stick legen.</span></li>
        <li><span>Am Foto-Automaten im dm als <b>Freiform-Sticker</b> drucken. Die Etiketten sind schon freigestellt (runde Ecken, durchsichtiger Hintergrund), der Automat schneidet an der Kontur.</span></li>
        <li><span>Etiketten aufkleben und hier <b>Als gedruckt markieren</b> tippen.</span></li></ol>
      <p class="leise klein">Hinweis: Wie genau der Automat druckt und schneidet, hängt vom Gerät ab. Vor dem ersten großen Druck lohnt ein Testbogen (Entwickler → Etiketten).</p>
      <img class="etikettvorschau" id="bogenbild" alt="" style="width:auto;max-height:260px;background:none" hidden></details>`;
}

export function liste(w, signal) {
  w.innerHTML = `
    <h1>Karten</h1>
    <p class="leise">Alle Karten, die die Box kennt, mit Cover. Tippe eine Karte an für Etikett, Name und mehr.</p>
    <a class="btn haupt gross" href="#/karten/neu" style="margin-bottom:14px">${symbol('plus')} Neue Karte bespielen</a>
    <section class="k" id="etikettbox"></section>
    <div id="raster"></div>`;
  kartenLaden();
  const takt = setInterval(() => { if (document.visibilityState === 'visible') kartenLaden(); }, 4000);
  signal.addEventListener('abort', () => clearInterval(takt));

  let zuletzt = null;
  const zeichnen = () => {
    const d = S.karten; if (!d) return;
    const kd = S.karte && S.karte.laeuft ? S.karte.kartendaten : null;
    const uid = kd ? kd.uid : null;
    const sig = JSON.stringify([d, uid]);
    if (sig === zuletzt) return;
    zuletzt = sig;
    const offen = $('#druckhilfe', w) && $('#druckhilfe', w).open;
    $('#etikettbox', w).innerHTML = etikettbox(d.etikett, d.karten);
    if (offen && $('#druckhilfe', w)) $('#druckhilfe', w).open = true;
    $('#raster', w).innerHTML = d.karten.length
      ? `<div class="kachelraster">${d.karten.map(k => kachel(k, k.uid === uid)).join('')}</div>`
      : `<div class="k leerzustand"><div class="fach">${symbol('karten')}</div><h2>Noch keine Karten</h2>
         <p class="leise">Lege eine Karte auf das Fach, damit die Box sie kennenlernt, oder bespiele gleich eine neue.</p></div>`;
  };
  abo(signal, 'karten', zeichnen); abo(signal, 'karte', zeichnen, false);

  w.addEventListener('click', async e => {
    const kk = e.target.closest('.kachel');
    if (kk) { detail(kk.dataset.uid, signal); return; }
    if (e.target.closest('#gedruckt')) {
      const d = S.karten, uris = new Set(d.karten.filter(k => d.etikett.naechster_bogen.includes(k.uid)).map(k => k.uri));
      const uids = d.karten.filter(k => uris.has(k.uri)).map(k => k.uid);       // alle Karten dieser Playlisten
      const erg = await sicher('/api/karten/gedruckt', {uids, wert: true});
      melden(erg, 'Als gedruckt markiert.'); kartenLaden();
    }
  }, {signal});
  w.addEventListener('toggle', e => {                                            // Vorschau des Bogens erst beim Öffnen laden (Pi rechnet)
    if (e.target.id === 'druckhilfe' && e.target.open) { const b = $('#bogenbild', w); if (b && !b.src) { b.hidden = false; b.src = '/etikett/bogen.png?t=' + Date.now(); b.onerror = () => { b.hidden = true; }; } }
  }, {signal, capture: true});
}

// ------------------------------------------------------------ Karte im Detail

function detail(uid, signal) {
  const finden = () => (S.karten && S.karten.karten.find(x => x.uid === uid)) || null;
  if (!finden()) return;
  const d = document.createElement('dialog');
  d.className = 'blatt';
  let t = Date.now();                                                           // Bild-Stand, damit Etikett und Cover neu geladen werden
  const fuellen = () => {
    const k = finden(); if (!k) { d.close(); return; }
    $('#d-bilder', d).innerHTML = `<div>${coverBild(k.cover ? k.cover + '&t=' + t : null, '', k.titel)}<div class="leise klein" style="text-align:center;margin-top:4px">Cover</div></div>
      <div><img class="etikettvorschau" src="${esc(k.etikett)}?t=${t}" alt="Etikett" onerror="this.remove()"><div class="leise klein" style="text-align:center">Etikett ${S.karten.etikett.groesse_mm} × ${S.karten.etikett.groesse_mm} mm</div></div>`;
    $('#d-etikett', d).href = k.etikett + '?laden=1';
    $('#d-gedruckt', d).checked = k.gedruckt;
    if (document.activeElement !== $('#d-name', d)) $('#d-name', d).value = k.titel;
    $('#d-info', d).innerHTML = `${esc(typName(k.typ))} · Kartennummer ${esc(k.uid)} · <a href="${esc(k.link)}" target="_blank" rel="noopener">in Spotify öffnen</a>`
      + (k.auf_karte === false ? '<br>Der Link steht nicht auf der Karte, sondern nur in dieser Box. Die Karte spielt nur hier.' : '');
  };
  const neu = async () => { t = Date.now(); await kartenLaden(); fuellen(); };
  d.innerHTML = `
    <div class="kopfzeile"><h3>Karte</h3><button class="btn klein" data-a="zu">${symbol('kreuz')} Schließen</button></div>
    <div class="nebeneinander" id="d-bilder"></div>
    <label class="klein leise" for="d-name">Name (steht auf dem Etikett)</label>
    <input type="text" id="d-name" maxlength="80" autocomplete="off">
    <p class="leise klein" id="d-info"></p>
    <div class="stapel">
      <a class="btn haupt" id="d-etikett" href="#" download>${symbol('laden')} Etikett laden</a>
      <label class="zeile" style="border:0;padding:4px 0"><span>Etikett ist gedruckt</span><input type="checkbox" class="schalter" id="d-gedruckt"></label>
      <button class="btn" data-a="cover">${symbol('neu')} Cover neu suchen</button>
      <label class="btn" for="d-bild">${symbol('bild')} Eigenes Bild wählen</label><input type="file" id="d-bild" accept="image/*" hidden>
      <button class="btn" data-a="neu">${symbol('karten')} Karte neu bespielen</button>
      <button class="btn gefahr" data-a="weg">${symbol('papierkorb')} Aus der Liste entfernen</button>
    </div>`;
  const schliessen = () => d.close();
  d.addEventListener('click', async e => {
    if (e.target === d) return schliessen();
    const b = e.target.closest('[data-a]'); if (!b) return;
    const k = finden(); if (!k) return;
    const a = b.dataset.a;
    if (a === 'zu') schliessen();
    if (a === 'cover') { b.disabled = true; melden(await sicher('/api/cover/neu', {uri: k.uri}), 'Cover aktualisiert.'); b.disabled = false; await neu(); }
    if (a === 'neu') { vorbelegt = k.link; schliessen(); location.hash = '#/karten/neu'; }
    if (a === 'weg') {
      if (await frage({titel: 'Aus der Liste entfernen?', text: 'Die Karte selbst bleibt unverändert. Legst du sie wieder auf, erscheint sie wieder in der Liste.', ok: 'Entfernen', art: 'gefahr'})) {
        melden(await sicher('/api/karten/entfernen', {uid: k.uid})); schliessen(); kartenLaden();
      }
    }
  });
  $('#d-name', d).addEventListener('change', async e => {
    const k = finden(); if (!k) return;
    const erg = await sicher('/api/karten/umbenennen', {uid: k.uid, titel: e.target.value});
    melden(erg, 'Name gespeichert.'); await neu();
  });
  $('#d-name', d).addEventListener('keydown', e => { if (e.key === 'Enter') e.target.blur(); });
  $('#d-gedruckt', d).addEventListener('change', async e => {
    const k = finden(); if (!k) return;
    melden(await sicher('/api/karten/gedruckt', {uids: [k.uid], wert: e.target.checked}), 'Gespeichert.'); kartenLaden();
  });
  $('#d-bild', d).addEventListener('change', async e => {
    const k = finden(), f = e.target.files[0]; e.target.value = '';
    if (!k || !f) return;
    toast('Bild wird hochgeladen …');
    melden(await bildHochladen(f, k.schluessel), 'Eigenes Bild gespeichert.'); await neu();
  });
  d.addEventListener('close', () => { d.remove(); kartenLaden(); });
  signal.addEventListener('abort', () => { if (d.isConnected) d.close(); });
  document.body.appendChild(d);
  fuellen();
  d.showModal();
}

// ------------------------------------------------------------ Assistent: Karte bespielen

const STUFEN = ['Link einfügen', 'Karte auflegen', 'Fertig'];
const STUFE_VON = {eingabe: 1, warten: 2, belegt: 2, andere: 2, fehler: 2, fertig: 3};

export function assistent(w, signal) {
  const W = {phase: 'eingabe', text: vorbelegt || '', info: null, fehler: null, suche: false, nr: 0, auftrag: null, start: 0, erg: null, danach: null, t: Date.now()};
  vorbelegt = null;
  w.innerHTML = `<h1>Karte bespielen</h1><p class="leise">In drei Schritten bekommt eine Karte ihre Playlist. Cover und Etikett entstehen von allein.</p>
    <ol class="stufen" id="stufen"></ol><div id="b"></div>`;
  kartenLaden();

  const stufen = () => {
    $('#stufen', w).innerHTML = STUFEN.map((s, i) => `<li data-n="${i + 1}" class="${STUFE_VON[W.phase] === i + 1 ? 'jetzt' : STUFE_VON[W.phase] > i + 1 ? 'fertig' : ''}">${s}</li>`).join('');
  };
  const etikettMoeglich = () => !S.karten || !S.karten.etikett || S.karten.etikett.verfuegbar;
  const zeigeEtikett = (uri, titel) => etikettMoeglich() && uri
    ? `<img class="etikettvorschau" src="/etikett/${esc(schl(uri))}.png?t=${W.t}" alt="Etikett: ${esc(titel || '')}" onerror="this.remove()">` : '';

  // ---- Schritt 1: Link einfügen, Cover wird von allein gesucht
  const eingabeZeigen = () => {
    W.phase = 'eingabe'; stufen();
    $('#b', w).innerHTML = `<section class="k"><h2>Spotify-Link der Playlist</h2>
      <p class="leise klein" style="margin-top:0">In Spotify: Playlist öffnen → drei Punkte → <b>Teilen</b> → <b>Link kopieren</b>. Dann hier einfügen.</p>
      <textarea id="link" rows="2" placeholder="https://open.spotify.com/playlist/…" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="Spotify-Link"></textarea>
      <div class="reihe" style="margin-top:8px">${navigator.clipboard && navigator.clipboard.readText ? `<button class="btn" id="einfuegen">${symbol('einfuegen')} Aus Zwischenablage einfügen</button>` : ''}
        <button class="btn hell" id="leeren">Löschen</button></div>
      <div id="pruefung"></div></section>
      <button class="btn haupt gross" id="weiter" disabled>Weiter: Karte bespielen</button>`;
    $('#link', w).value = W.text;
    pruefungZeigen();
  };
  const pruefungZeigen = () => {
    const p = $('#pruefung', w), weiter = $('#weiter', w); if (!p) return;
    const i = W.info;
    weiter.disabled = !(i && i.ok);
    if (W.suche) { p.innerHTML = `<div class="vorschau">${coverBild(null, 'suche')}<div class="leise">Suche Titel und Cover …</div></div>`; return; }
    if (W.fehler) { p.innerHTML = `<div class="hinweis fehler">${esc(W.fehler)}</div>`; return; }
    if (!i || !i.ok) { p.innerHTML = ''; return; }
    p.innerHTML = `<div class="vorschau">${coverBild(i.cover ? i.cover + '&t=' + W.t : null, '', i.titel || '')}
        <div><span class="marke">${esc(typName(i.typ))}</span><div class="titel" style="margin-top:6px">${esc(i.titel || 'Ohne Titel')}</div></div></div>
      ${i.hat_cover ? '' : `<div class="hinweis warn">${esc(i.meldung || 'Zu diesem Link wurde kein Cover gefunden.')} Du kannst es nochmal suchen lassen oder ein eigenes Bild wählen. Ohne Bild bekommt das Etikett ein oranges Namensschild.</div>`}
      <div class="reihe"><button class="btn klein" id="nochmal">${symbol('neu')} Cover nochmal suchen</button>
        <label class="btn klein" for="eigenes">${symbol('bild')} Eigenes Bild wählen</label><input type="file" id="eigenes" accept="image/*" hidden></div>
      ${etikettMoeglich() ? `<div class="trenner" style="margin-top:12px"><div class="leise klein" style="text-align:center">So sieht dein Etikett aus (${S.karten && S.karten.etikett ? S.karten.etikett.groesse_mm : 40} × ${S.karten && S.karten.etikett ? S.karten.etikett.groesse_mm : 40} mm)</div>${zeigeEtikett(i.uri, i.titel)}</div>` : ''}`;
  };
  let tipp = null;
  const pruefen = async (neu = false) => {
    const text = W.text.trim(), n = ++W.nr;
    if (!text) { W.info = null; W.fehler = null; W.suche = false; pruefungZeigen(); return; }
    W.suche = true; W.fehler = null; pruefungZeigen();
    const erg = await sicher('/api/karten/pruefen', {text, neu});
    if (n !== W.nr || W.phase !== 'eingabe') return;                            // inzwischen anderer Text
    W.suche = false; W.t = Date.now();
    if (erg.ok) { W.info = erg; W.fehler = null; } else { W.info = null; W.fehler = erg.meldung; }
    pruefungZeigen();
  };
  const eingabeAendern = text => {
    W.text = text; W.info = null; W.fehler = null; clearTimeout(tipp);
    W.nr++;
    if (!text.trim()) { W.suche = false; pruefungZeigen(); return; }
    W.suche = true; pruefungZeigen();
    tipp = setTimeout(() => pruefen(), 500);                                    // erst prüfen, wenn kurz nicht mehr getippt wird
  };

  // ---- Schritt 2: Karte auflegen
  const bespielen = async (ueberschreiben = false) => {
    if (W.busy) return;                                                          // nie zwei Aufträge gleichzeitig stellen
    W.busy = true;
    try {
      const erg = await sicher('/api/karten/bespielen', {uri: W.info.uri, ueberschreiben});
      if (!erg.ok) { W.erg = {meldung: erg.meldung}; W.phase = 'fehler'; zeigen(); return; }
      W.auftrag = erg.auftrag.auftrag; W.start = Date.now(); W.phase = 'warten'; W.erg = erg.auftrag;
      await karteLaden(); zeigen();
    } finally { W.busy = false; }
  };
  const wartenZeigen = () => {
    const kd = S.karte && S.karte.kartendaten, a = W.erg || {};
    $('#b', w).innerHTML = `<section class="k warten"><div class="fach">${symbol('karten')}</div>
      <h2 id="wtitel"></h2><p class="leise" id="wtext"></p><div class="grosszahl" id="wrest"></div>
      <div class="vorschau" style="grid-template-columns:70px 1fr;text-align:left;max-width:340px;margin:14px auto 0">${coverBild(a.cover, '', a.titel || '')}
        <div><div class="leise klein">bekommt die Playlist</div><div class="titel" style="font-size:17px">${esc(a.titel || (W.info && W.info.titel) || 'Playlist')}</div></div></div></section>
      <button class="btn gross" id="abbrechen">Abbrechen</button>`;
    wartenAktualisieren(kd);
  };
  const wartenAktualisieren = kd => {
    if (!$('#wtitel', w)) return;
    const a = S.karte && S.karte.auftrag;
    $('#wtitel', w).textContent = kd ? 'Karte erkannt, sie wird bespielt …' : 'Lege jetzt die Karte auf das Kartenfach';
    $('#wtext', w).textContent = kd ? 'Bitte die Karte liegen lassen, das dauert nur einen Moment.' : 'Die Box wartet auf die Karte. Sobald sie liegt, geht es von allein weiter.';
    $('#wrest', w).textContent = a && a.status === 'wartet' && !kd ? a.rest_s + NBS + 's' : '';
  };
  const belegtZeigen = () => {
    const a = W.erg, neuTitel = a.titel || (W.info && W.info.titel) || 'diese Playlist';
    $('#b', w).innerHTML = `<section class="k"><h2>Auf dieser Karte ist schon etwas</h2>
      <div class="nebeneinander"><div>${coverBild(a.vorher_cover, '', a.vorher_titel || '')}<div class="leise klein" style="text-align:center;margin-top:4px">${esc(a.vorher_titel || 'eine andere Playlist')}</div></div>
        <div>${coverBild(a.cover, '', neuTitel)}<div class="leise klein" style="text-align:center;margin-top:4px">${esc(neuTitel)}</div></div></div>
      <p>Die Karte spielt bisher <b>${esc(a.vorher_titel || 'eine andere Playlist')}</b>. Soll sie stattdessen <b>${esc(neuTitel)}</b> spielen?</p>
      <div class="stapel"><button class="btn haupt gross" id="ueber">Ja, überschreiben</button><button class="btn gross" id="andere">Nein, andere Karte nehmen</button></div></section>`;
  };
  const andereZeigen = () => {
    $('#b', w).innerHTML = `<section class="k warten"><div class="fach">${symbol('karten')}</div><h2>Bitte die Karte aus dem Fach nehmen</h2>
      <p class="leise">Danach die nächste Karte auflegen. Es geht von allein weiter.</p></section><button class="btn gross" id="abbrechen">Abbrechen</button>`;
  };

  // ---- Schritt 3: Fertig
  const fertigZeigen = () => {
    const a = W.erg, titel = a.titel || (W.info && W.info.titel) || 'Playlist', uri = a.uri;
    const nurBox = a.auf_karte === false;
    $('#b', w).innerHTML = `<section class="k erfolg"><div class="haken">${symbol('haken')}</div>
      <h2>Fertig! Die Karte ist bespielt.</h2>
      ${coverBild(a.cover, '', titel)}<div class="titel" style="font-size:19px;font-weight:800">${esc(titel)}</div>
      ${nurBox ? `<div class="hinweis warn" style="text-align:left">${esc(a.meldung || '')}</div>` : '<p class="leise">Der Link steht jetzt auf der Karte.</p>'}
      <p class="leise klein">Zum Ausprobieren: Karte kurz abheben und wieder auflegen.</p></section>
      ${etikettMoeglich() ? `<section class="k erfolg"><h2>Etikett (${S.karten && S.karten.etikett ? S.karten.etikett.groesse_mm : 40} × ${S.karten && S.karten.etikett ? S.karten.etikett.groesse_mm : 40} mm)</h2>
        ${zeigeEtikett(uri, titel)}
        <div class="stapel"><a class="btn haupt gross" href="/etikett/${esc(schl(uri))}.png?laden=1" download>${symbol('laden')} Etikett laden</a></div>
        <p class="leise klein">Alle noch nicht gedruckten Etiketten gibt es gesammelt als Bogen unter „Karten“.</p></section>` : ''}
      <div class="stapel"><button class="btn gross" id="nochmal">Noch eine Karte mit dieser Playlist</button>
        <button class="btn gross" id="neue">Andere Playlist bespielen</button><a class="btn hell gross" href="#/karten">Zu meinen Karten</a></div>`;
  };
  const fehlerZeigen = () => {
    $('#b', w).innerHTML = `<section class="k"><h2>Das hat nicht geklappt</h2><div class="hinweis fehler">${esc((W.erg && W.erg.meldung) || 'Es ist ein Fehler aufgetreten.')}</div>
      <div class="stapel"><button class="btn haupt gross" id="nochmalversuchen">Nochmal versuchen</button><button class="btn gross" id="zurueck">Zurück zum Link</button></div></section>`;
  };
  function zeigen() {
    stufen();
    ({eingabe: eingabeZeigen, warten: wartenZeigen, belegt: belegtZeigen, andere: andereZeigen, fertig: fertigZeigen, fehler: fehlerZeigen})[W.phase]();
  }

  // ---- Bedienung
  w.addEventListener('input', e => { if (e.target.id === 'link') eingabeAendern(e.target.value); }, {signal});
  w.addEventListener('paste', e => { if (e.target.id === 'link') setTimeout(() => { eingabeAendern(e.target.value); clearTimeout(tipp); pruefen(); }, 0); }, {signal});
  w.addEventListener('change', async e => {
    if (e.target.id !== 'eigenes') return;
    const f = e.target.files[0]; e.target.value = '';
    if (!f || !W.info) return;
    toast('Bild wird hochgeladen …');
    const erg = await bildHochladen(f, W.info.schluessel);
    melden(erg, 'Eigenes Bild gespeichert.');
    if (erg.ok) pruefen();
  }, {signal});
  w.addEventListener('click', async e => {
    const id = (e.target.closest('button') || {}).id;
    if (id === 'einfuegen') {
      try { const t = await navigator.clipboard.readText(); $('#link', w).value = t; eingabeAendern(t); clearTimeout(tipp); pruefen(); }
      catch (x) { toast('Der Browser erlaubt das Einfügen nicht. Bitte den Link ins Feld tippen und „Einfügen“ wählen.', 'fehler'); $('#link', w).focus(); }
    }
    if (id === 'leeren') { $('#link', w).value = ''; eingabeAendern(''); $('#link', w).focus(); }
    if (id === 'nochmal' && W.phase === 'eingabe') pruefen(true);
    if (id === 'weiter' && W.info && W.info.ok) bespielen(false);
    if (id === 'abbrechen') { await sicher('/api/karten/abbrechen', {}); W.phase = 'eingabe'; zeigen(); }
    if (id === 'ueber') bespielen(true);
    if (id === 'andere') { await sicher('/api/karten/abbrechen', {}); W.phase = 'andere'; zeigen(); }
    if (id === 'nochmal' && W.phase === 'fertig') { W.phase = 'andere'; zeigen(); }
    if (id === 'neue') { W.text = ''; W.info = null; W.fehler = null; W.phase = 'eingabe'; zeigen(); }
    if (id === 'nochmalversuchen') { if (W.info) bespielen(false); else { W.phase = 'eingabe'; zeigen(); } }
    if (id === 'zurueck') { W.phase = 'eingabe'; zeigen(); }
  }, {signal});

  // ---- Rückmeldungen der Box (jede Sekunde)
  abo(signal, 'karte', () => {
    const k = S.karte; if (!k) return;
    const a = k.auftrag, kd = k.laeuft ? k.kartendaten : null;
    if (W.phase === 'andere' && !kd) { bespielen(false); return; }               // Karte ist weg: nächste kann kommen
    if (!['warten'].includes(W.phase) || !a || a.auftrag !== W.auftrag) {
      if (W.phase === 'warten' && a && a.status === 'keiner' && Date.now() - W.start > 4000) { W.phase = 'eingabe'; zeigen(); }
      return;
    }
    if (a.status === 'wartet') { W.erg = Object.assign({}, W.erg, a); wartenAktualisieren(kd); }
    else if (a.status === 'belegt') { W.erg = a; W.phase = 'belegt'; zeigen(); }
    else if (a.status === 'fertig') { W.erg = a; W.t = Date.now(); W.phase = 'fertig'; kartenLaden(); zeigen(); }
    else if (a.status === 'fehler' || a.status === 'abgelaufen') { W.erg = a; W.phase = 'fehler'; zeigen(); }
  }, false);
  signal.addEventListener('abort', () => {                                        // Seite verlassen: laufenden Auftrag beenden
    clearTimeout(tipp);
    if (['warten', 'belegt'].includes(W.phase)) sicher('/api/karten/abbrechen', {});
  });

  zeigen();
  if (W.text) pruefen();
}
