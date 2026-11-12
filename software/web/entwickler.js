// Entwickler-Einstellungen: Ton, Bedienung, Etiketten, System. Alles, was nicht zum Alltag gehört.
import {$, NB, S, abo, bedient, boxAktion, datum, kopieren, einstLaden, einstSpeichern, esc, holen, kartenLaden, melden, sicher, symbol, toast, zustandLaden, zustandTexte} from './kern.js';
import {equalizer} from './klang.js';

const QUELLE = {aufnahme: 'Aufnahme', sprache: 'Sprachausgabe', ton: 'nur Töne'};
const AUSGAENGE = [['kopfhoerer', 'Kopfhörer (Klinke)'], ['lautsprecher', 'Lautsprecher']];
const proz = v => v + NB + '%';
/** Wert rechts neben einem Regler mitführen. */
function regler(w, id, text = v => v) { const r = $('#' + id, w), a = $('#' + id + 'w', w); const f = () => { a.textContent = text(r.value); }; r.addEventListener('input', f); f(); return f; }

// ------------------------------------------------------------ Ton: Grenzen, Klang, Ansagen

export function ton(w, signal) {
  w.innerHTML = `
    <h1>Ton</h1><p class="leise">Höchstlautstärke, Klang und die Ansagen der Box.</p>
    <section class="k"><h2>Lautstärke-Grenzen</h2>
      <p class="leise klein" style="margin-top:0">Die Höchstlautstärke schützt die Ohren. Die Startlautstärke gilt beim Einschalten und ist nie höher als die Höchstlautstärke.</p>
      ${AUSGAENGE.map(([a, name]) => `<div class="trenner"><b>${name}</b>
        <div class="leise klein versteckt" id="g-${a}-hinweis">Noch nicht angeschlossen. Die Werte gelten, sobald er läuft.</div>
        <div class="grenze"><div class="kopfzeile"><span>Höchstlautstärke</span><b id="g-${a}-maxw"></b></div><input type="range" id="g-${a}-max" min="5" max="100" step="5"></div>
        <div class="grenze"><div class="kopfzeile"><span>Beim Einschalten</span><b id="g-${a}-startw"></b></div><input type="range" id="g-${a}-start" min="5" max="100" step="5"></div></div>`).join('')}
      <button class="btn haupt" id="gspeichern" style="margin-top:14px;width:100%">Speichern</button></section>
    <section class="k"><h2>Klang (Equalizer)</h2><div id="klang"></div></section>
    <section class="k"><h2>Ansagen anhören</h2>
      <p class="leise klein" style="margin-top:0">Aufnahme = eigene Datei in software/ansagen, Sprachausgabe = vom Pi gesprochen (Ersatz, bis es eine Aufnahme gibt).</p>
      <div id="aliste">wird geladen …</div></section>`;
  einstLaden();
  equalizer($('#klang', w), signal);

  let geaendert = false;
  const anzeigen = a => {
    const max = $(`#g-${a}-max`, w), start = $(`#g-${a}-start`, w);
    if (+start.value > +max.value) start.value = max.value;                      // Start nie über dem Maximum
    $(`#g-${a}-maxw`, w).textContent = proz(max.value); $(`#g-${a}-startw`, w).textContent = proz(start.value);
  };
  AUSGAENGE.forEach(([a]) => ['max', 'start'].forEach(x => $(`#g-${a}-${x}`, w).addEventListener('input', () => { geaendert = true; anzeigen(a); }, {signal})));
  abo(signal, 'einst', () => {
    if (!S.einst) return;
    AUSGAENGE.forEach(([a]) => {
      $(`#g-${a}-hinweis`, w).classList.toggle('versteckt', !!S.ausgaenge[a]);
      if (geaendert) return;
      $(`#g-${a}-max`, w).value = S.einst.lautstaerke[a].max; $(`#g-${a}-start`, w).value = S.einst.lautstaerke[a].start; anzeigen(a);
    });
  });
  $('#gspeichern', w).addEventListener('click', async () => {
    const l = {}; AUSGAENGE.forEach(([a]) => { l[a] = {max: +$(`#g-${a}-max`, w).value, start: +$(`#g-${a}-start`, w).value}; });
    const erg = await einstSpeichern({lautstaerke: l});
    if (erg.ok) geaendert = false;
    melden(erg, 'Gespeichert.'); if (erg.ok) zustandLaden();
  }, {signal});

  holen('/api/ansagen').then(a => {
    $('#aliste', w).innerHTML = a.ansagen.map(x => `<div class="ansage"><button class="btn" data-name="${esc(x.name)}" aria-label="Anhören: ${esc(x.text)}">▶</button>
      <span>${esc(x.text)}<br><span class="q">${QUELLE[x.quelle] || x.quelle} · ${esc(x.name)}</span></span></div>`).join('');
  }).catch(() => { $('#aliste', w).textContent = 'Keine Verbindung zur Box.'; });
  $('#aliste', w).addEventListener('click', async e => { const b = e.target.closest('[data-name]'); if (b) melden(await sicher('/api/ansage', {name: b.dataset.name})); }, {signal});
}

// ------------------------------------------------------------ Bedienung: live ansehen, prüfen, einstellen

const FELDER = [['zurueck', '⏮', 'zurück'], ['play', '⏯', 'Play'], ['vor', '⏭', 'vor'], ['schlaf', '☾', 'Mond']];

export function bedienung(w, signal) {
  w.innerHTML = `
    <h1>Bedienung</h1><p class="leise">Touch-Felder, Drehknopf, Ein-Taste und Kopfhörer-Erkennung: live ansehen und einstellen.</p>
    <section class="k"><h2>Live</h2>
      <div class="felder">${FELDER.map(([f, s, n]) => `<div class="feld" id="f-${f}"><div class="s">${s}</div><div class="nr" id="fn-${f}">${n}</div></div>`).join('')}</div>
      <div class="raster">
        <div><div class="leise klein">Drehknopf</div><div class="wert" id="bdreh">–</div></div>
        <div><div class="leise klein">Ein-Taste</div><div class="wert" id="btaste">–</div></div>
        <div><div class="leise klein">Kopfhörer</div><div class="wert" id="bklinke">–</div></div>
        <div><div class="leise klein">Touch-Chip</div><div class="wert" id="btouch">–</div></div></div>
      <div id="bhinweis"></div></section>
    <section class="k"><details id="belegdetails" style="margin-top:0"><summary>Was die Tasten können</summary>
      <p class="leise klein">Orange = nur durch Halten erreichbar (Doppelbelegung). Die Zeiten kommen direkt von der Box.</p>
      <div id="belegliste">wird geladen …</div><div id="beleghinweise" class="leise klein" style="margin-top:8px"></div></details></section>
    <section class="k"><details id="bdetails" style="margin-top:0"><summary>Prüfen und einstellen</summary>
      <p class="leise klein">Abstand zur Grundlinie je Feld (Strich = Schwelle). Berühren muss deutlich über den Strich gehen, ohne Berührung deutlich darunter bleiben.</p>
      <div id="bdeltas">${FELDER.map(([f, s, n]) => `<div class="delta"><span>${s} ${n}</span><div class="spur"><div id="d-${f}"></div><i id="s-${f}"></i></div><b id="dw-${f}">–</b></div>`).join('')}</div>
      <div class="grenze"><div class="kopfzeile"><span>Touch-Schwelle <small class="leise">(kleiner = empfindlicher)</small></span><b id="bschwellew"></b></div><input type="range" id="bschwelle" min="2" max="30" step="1"></div>
      <div class="trenner"><b>Drehknopf</b>
        <div class="grenze"><div class="kopfzeile"><span>Je Raste</span><b id="bschrittw"></b></div><input type="range" id="bschritt" min="1" max="10" step="1"></div>
        <label class="zeile"><span>Drehrichtung umkehren<br><span class="leise klein">falls rechts herum leiser wird</span></span><input type="checkbox" class="schalter" id="bumkehren"></label></div>
      <div class="trenner"><b>Klick</b> <span class="leise klein">(zurück, Play, vor – nicht Mond, nicht Ein-Taste)</span>
        <div class="grenze"><div class="kopfzeile"><span>Lautstärke <small class="leise">(0 = aus)</small></span><b id="bklickw"></b></div><input type="range" id="bklick" min="0" max="60" step="1"></div></div>
      <div class="trenner"><b>Kopfhörer</b>
        <label class="zeile"><span>Kopfhörer erkennen<br><span class="leise klein">aus: immer Lautsprecher</span></span><input type="checkbox" class="schalter" id="bkerkennung"></label>
        <label class="zeile"><span>Stecker steckt bei Pegel<br><span class="leise klein" id="bpegel">P26: –</span></span><select id="bkpolung"><option value="hoch">hoch</option><option value="tief">tief</option></select></label></div>
      <div class="trenner"><b>Felder</b> <span class="leise klein">(welche Elektrode des Touch-Chips)</span>
        <div id="bzuordnung">${FELDER.map(([f, s, n]) => `<label class="zeile"><span>${s} ${n}</span><select id="z-${f}">${[0, 1, 2, 3].map(i => `<option value="${i}">E${i}</option>`).join('')}</select></label>`).join('')}</div></div>
      <button class="btn haupt" id="bspeichern" style="margin-top:14px;width:100%">Speichern</button></details></section>`;
  einstLaden();
  const setze = (id, html, klasse) => { $('#' + id, w).innerHTML = (klasse ? `<span class="punkt ${klasse}"></span>` : '') + html; };
  const form = $('#bdetails', w);
  let geaendert = false;
  regler(w, 'bschwelle'); regler(w, 'bschritt', proz); regler(w, 'bklick', proz);

  function anzeigen(b) {
    if (!b || !b.laeuft) {
      FELDER.forEach(([f]) => { $('#f-' + f, w).className = 'feld aus'; });
      ['bdreh', 'btaste', 'bklinke', 'btouch'].forEach(id => setze(id, '–'));
      $('#bhinweis', w).innerHTML = '<div class="hinweis">Keine Angaben vom Player (läuft er?).</div>';
      return;
    }
    const t = b.touch, zu = S.einst && S.einst.bedienung ? S.einst.bedienung.felder : null;
    FELDER.forEach(([f]) => {
      $('#f-' + f, w).className = 'feld' + (!t.ok ? ' aus' : t.beruehrt.includes(f) ? ' an' : '');
      if (zu) $('#fn-' + f, w).textContent = 'E' + zu[f];
    });
    setze('btouch', t.ok ? 'bereit' + (t.zu_kurz ? `<br><small>${t.zu_kurz}× Rauschen ignoriert</small>` : '') : 'Fehler', t.ok ? 'gut' : 'rot');
    const d = b.drehknopf;
    if (!d.art) setze('bdreh', 'nicht gefunden', 'rot');
    else setze('bdreh', `${d.schritte} <small>Rasten<br>${d.letzter ? 'zuletzt ' + (d.letzter > 0 ? '+1' : '−1') : ''}${d.art === 'kernel' ? '' : ' · ohne Kernel-Treiber'}</small>`, d.art === 'kernel' ? 'gut' : 'warn');
    if (!b.taste.bekannt) setze('btaste', 'unbekannt', 'warn');
    else setze('btaste', b.taste.gedrueckt ? 'gedrückt' : 'los', b.taste.gedrueckt ? 'an' : 'gut');
    const k = b.klinke;
    setze('bklinke', (k.eingesteckt ? 'eingesteckt' : 'nein') + (k.umstellung ? '<br><small>schaltet um …</small>'
      : `<br><small>${k.ausgang === 'kopfhoerer' ? 'Ton über Kopfhörer' : k.ausgang === 'lautsprecher' ? 'Ton über Lautsprecher' : ''}</small>`), k.fehler ? 'warn' : k.eingesteckt ? 'an' : 'gut');
    $('#bpegel', w).textContent = 'P26 gerade: ' + (k.pegel == null ? '–' : k.pegel ? 'hoch' : 'tief');
    const h = [];
    if (!t.ok && t.fehler) h.push('Touch-Chip: ' + t.fehler);
    if (k.fehler) h.push('Kopfhörer: ' + k.fehler);
    if (!b.gpio) h.push('GPIO nicht lesbar: Ein-Taste und Kopfhörer-Erkennung aus.');
    $('#bhinweis', w).innerHTML = h.map(x => `<div class="hinweis fehler">${esc(x)}</div>`).join('');
    if (t.roh) {
      const schwelle = S.einst ? S.einst.bedienung.touch_schwelle : 8, skala = Math.max(40, schwelle * 3);
      FELDER.forEach(([f], i) => {
        const e = zu ? zu[f] : i, r = t.roh[e]; if (!r) return;
        const delta = Math.max(0, r[2]);
        $('#d-' + f, w).style.width = Math.min(100, delta / skala * 100) + '%';
        $('#d-' + f, w).style.background = delta >= schwelle ? 'var(--orange)' : 'var(--gut)';
        $('#s-' + f, w).style.left = Math.min(100, schwelle / skala * 100) + '%';
        $('#dw-' + f, w).textContent = r[2];
      });
    }
  }
  abo(signal, 'karte', () => { if (!form.open && S.karte) anzeigen(S.karte.bedienung); });

  async function live() {                                                        // Prüfansicht offen: schneller, mit Rohwerten
    while (form.open && !signal.aborted && document.visibilityState === 'visible') {
      try { anzeigen(await holen('/api/bedienung')); } catch (e) { /* weiter */ }
      await new Promise(r => setTimeout(r, 300));
    }
  }
  form.addEventListener('toggle', () => { if (form.open) { einstLaden(); live(); } }, {signal});
  document.addEventListener('visibilitychange', () => { if (form.open && document.visibilityState === 'visible') live(); }, {signal});
  form.addEventListener('input', () => { geaendert = true; }, {signal, capture: true});
  form.addEventListener('change', () => { geaendert = true; }, {signal, capture: true});
  abo(signal, 'einst', () => {
    if (!S.einst || geaendert) return;
    const b = S.einst.bedienung;
    $('#bschwelle', w).value = b.touch_schwelle; $('#bschritt', w).value = b.drehknopf_schritt;
    $('#bumkehren', w).checked = b.drehknopf_umkehren; $('#bkerkennung', w).checked = b.kopfhoerer_erkennung; $('#bkpolung', w).value = b.klinke_eingesteckt_bei;
    $('#bklick', w).value = b.klick === undefined ? 30 : b.klick;
    FELDER.forEach(([f]) => { $('#z-' + f, w).value = b.felder[f]; });
    ['bschwelle', 'bschritt', 'bklick'].forEach(id => $('#' + id, w).dispatchEvent(new Event('input')));
    geaendert = false;                                                           // das Füllen selbst zählt nicht als Änderung
  });
  $('#bspeichern', w).addEventListener('click', async () => {
    const felder = {}; FELDER.forEach(([f]) => { felder[f] = +$('#z-' + f, w).value; });
    const s = +$('#bschwelle', w).value;
    const erg = await einstSpeichern({bedienung: {touch_schwelle: s, touch_loslassen: Math.max(1, Math.floor(s / 2)), drehknopf_schritt: +$('#bschritt', w).value,
      drehknopf_umkehren: $('#bumkehren', w).checked, kopfhoerer_erkennung: $('#bkerkennung', w).checked, klinke_eingesteckt_bei: $('#bkpolung', w).value, felder, klick: +$('#bklick', w).value}});
    if (erg.ok) geaendert = false;
    melden(erg, 'Gespeichert.');
  }, {signal});

  $('#belegdetails', w).addEventListener('toggle', async e => {
    if (!e.target.open) return;
    try {
      const b = await holen('/api/belegung');
      $('#belegliste', w).innerHTML = b.elemente.map(el => {
        const n = el.gesten.filter(x => x.doppelt).length;
        return `<div class="beleg"><div class="bk"><span class="s">${el.symbol}</span><b>${esc(el.name)}</b>${n ? `<span class="marke">${el.gesten.length} Funktionen</span>` : ''}</div>
          <div class="ort">${esc(el.ort)}${el.klick ? ' · klickt' : ''}</div>
          ${el.gesten.map(x => `<div class="geste${x.doppelt ? ' doppelt' : ''}"><span class="wie">${esc(x.wie)}</span><span>${esc(x.was)}</span></div>`).join('')}</div>`;
      }).join('');
      $('#beleghinweise', w).innerHTML = '<b>Schutz gegen Fehlbedienung</b><br>' + b.hinweise.map(esc).join('<br>');
    } catch (x) { $('#belegliste', w).textContent = 'Keine Verbindung zur Box.'; }
  }, {signal});
}

// ------------------------------------------------------------ Etiketten

const E_FELDER = [['groesse_mm', 'Größe des Etiketts', 20, 80, 1, 'mm'], ['weiss_mm', 'Weißer Rand ums Cover', 0, 3, 0.5, 'mm'],
                  ['ecke_mm', 'Rundung der Ecken', 0, 12, 0.5, 'mm'], ['rand_mm', 'Abstand zum Bogenrand', 0, 20, 1, 'mm'], ['abstand_mm', 'Abstand zwischen Etiketten', 0, 20, 1, 'mm']];
const mm = v => String(v).replace('.', ',') + NB + 'mm';

export function etiketten(w, signal) {
  w.innerHTML = `
    <h1>Etiketten</h1><p class="leise">Größe und Layout der Etiketten für den Foto-Automaten (Freiform-Sticker, Bogen 90 × 140 mm).</p>
    <section class="k"><h2>Layout</h2><div id="bildhinweis"></div>
      ${E_FELDER.map(([k, name, lo, hi, st]) => `<div class="grenze"><div class="kopfzeile"><span>${name}</span><b id="e-${k}w"></b></div><input type="range" id="e-${k}" min="${lo}" max="${hi}" step="${st}"></div>`).join('')}
      <p class="leise klein" id="eplaetze"></p>
      <div class="reihe"><button class="btn haupt" id="espeichern">Speichern</button><button class="btn" id="estandard">Auf Standard (40 × 40 mm)</button></div></section>
    <section class="k"><h2>Testbogen</h2>
      <p class="leise klein" style="margin-top:0">Ein Bogen mit Messskala. Einmal am Foto-Automaten drucken und nachmessen: Wie groß kommen die Quadrate heraus, wie genau schneidet der Automat, wie viel Abstand braucht er?
        Diese Werte sind bisher Annahmen und noch nicht an einem echten Druck geprüft.</p>
      <a class="btn haupt" href="/etikett/testbogen.png?laden=1" download>${symbol('laden')} Testbogen laden</a>
      <details><summary>Vorschau</summary><img id="testbild" alt="Testbogen" style="max-width:100%;max-height:420px;display:block;margin:8px auto" hidden></details></section>`;
  einstLaden(); kartenLaden();
  let geaendert = false;
  E_FELDER.forEach(([k, , , , , ]) => $('#e-' + k, w).addEventListener('input', () => { geaendert = true; zeigen(); }, {signal}));
  const werte = () => Object.fromEntries(E_FELDER.map(([k]) => [k, +$('#e-' + k, w).value]));
  function zeigen() {
    E_FELDER.forEach(([k]) => { $('#e-' + k + 'w', w).textContent = mm($('#e-' + k, w).value); });
    const e = werte(), b = 90, h = 140;
    const sp = Math.floor((b - 2 * e.rand_mm + e.abstand_mm + 1e-9) / (e.groesse_mm + e.abstand_mm)), ze = Math.floor((h - 2 * e.rand_mm + e.abstand_mm + 1e-9) / (e.groesse_mm + e.abstand_mm));
    $('#eplaetze', w).innerHTML = sp >= 1 && ze >= 1 ? `Auf einen Bogen passen <b>${sp * ze} Etiketten</b> (${sp} × ${ze}).` : '<span style="color:var(--rot)">So groß passt kein Etikett auf den Bogen.</span>';
  }
  abo(signal, 'einst', () => {
    if (!S.einst || geaendert) return;
    E_FELDER.forEach(([k]) => { $('#e-' + k, w).value = S.einst.etikett[k]; }); zeigen();
  });
  abo(signal, 'karten', () => {
    const e = S.karten && S.karten.etikett;
    $('#bildhinweis', w).innerHTML = e && !e.verfuegbar ? '<div class="hinweis warn">Auf der Box fehlt das Bildprogramm (Pillow). Einmal am Pi <b>sh ~/peppa-box/software/dienst_einrichten.sh</b> ausführen.</div>' : '';
  }, false);
  $('#espeichern', w).addEventListener('click', async () => {
    const erg = await einstSpeichern({etikett: werte()});
    if (erg.ok) { geaendert = false; kartenLaden(); }
    melden(erg, 'Gespeichert.');
  }, {signal});
  $('#estandard', w).addEventListener('click', async () => {
    const erg = await einstSpeichern({etikett: {groesse_mm: 40, rand_mm: 3, abstand_mm: 4, weiss_mm: 0.5, ecke_mm: 3}});
    if (erg.ok) { geaendert = false; kartenLaden(); }
    melden(erg, 'Auf Standard gesetzt.');
  }, {signal});
  w.addEventListener('toggle', e => {
    const b = $('#testbild', w);
    if (e.target.tagName === 'DETAILS' && e.target.open && !b.src) { b.hidden = false; b.src = '/etikett/testbogen.png?t=' + Date.now(); b.onerror = () => { b.hidden = true; }; }
  }, {signal, capture: true});
}

// ------------------------------------------------------------ System: Zustand, Software, Meldungen, Diagnose

export function system(w, signal) {
  w.innerHTML = `
    <h1>System</h1><p class="leise">Zustand der Box, Software-Update und Fehlersuche.</p>
    <section class="k"><h2>Zustand</h2>
      <div class="kopfzeile" style="margin-bottom:12px"><div class="wert" id="aproz">–</div><div style="flex:1"><div class="balken"><div id="abalken" style="width:0"></div></div></div></div>
      <div class="leise klein" id="atext" style="margin:-4px 0 12px"></div>
      <div class="raster" id="werte"></div><div class="leise klein" id="probelauf" style="margin-top:10px"></div></section>
    <section class="k"><h2>Software</h2><div class="wert" id="vtext">–</div><div class="leise klein" id="vdatum"></div><div id="uergebnis"></div>
      <div class="stapel" style="margin-top:12px"><button class="btn" id="bpruefen">Nach Updates suchen</button>
        <button class="btn haupt versteckt" id="bupdate">Jetzt aktualisieren</button><button class="btn versteckt" id="bzurueck">Zurück zur vorherigen Version</button></div></section>
    <section class="k"><details id="mdetails" style="margin-top:0"><summary>Letzte Meldungen der Box</summary><pre id="mtext">wird geladen …</pre>
        <button class="btn" id="mkopieren" data-quelle="mtext">${symbol('kopieren')} Meldungen kopieren</button></details>
      <details id="ddetails"><summary>Diagnose (für die Fehlersuche)</summary>
        <p class="leise klein">Zustand von Ton, Diensten und Spotify und das Protokoll, auch vom vorigen Lauf. Nach einem Fehler öffnen, kopieren und in den Chat einfügen.</p><pre id="dtext">wird geladen …</pre>
        <button class="btn" id="dkopieren" data-quelle="dtext">${symbol('kopieren')} Diagnose kopieren</button></details></section>`;
  zustandLaden();
  abo(signal, 'zustand', () => {
    const z = S.zustand; if (!z) return;
    const t = zustandTexte(z), a = t.akku;
    $('#aproz', w).textContent = a.wert; $('#abalken', w).style.width = a.laedt ? '100%' : (a.prozent || 0) + '%';
    $('#abalken', w).style.background = a.art === 'rot' ? 'var(--rot)' : a.art === 'warn' ? '#d9981f' : 'var(--gut)';
    $('#atext', w).textContent = a.klein;
    const z1 = (name, x) => `<div><div class="leise klein">${name}</div><div class="wert">${x.art ? `<span class="punkt ${x.art}"></span>` : ''}${esc(x.wert)}${x.klein ? ` <small>${esc(x.klein)}</small>` : ''}</div></div>`;
    $('#werte', w).innerHTML = z1('Musik', t.musik) + z1('WLAN', t.wlan) + z1('Temperatur', t.temp || {wert: '–'}) + z1('Speicher frei', t.platte) + z1('Stromversorgung', t.strom) + z1('Läuft seit', t.laufzeit);
    $('#probelauf', w).textContent = z.probelauf ? 'Probelauf: Befehle werden nicht ausgeführt.' : '';
    const v = z.version;
    if (v.fehler) { $('#vtext', w).textContent = 'Version unbekannt'; $('#vdatum', w).textContent = v.fehler; }
    else { $('#vtext', w).textContent = v.text; $('#vdatum', w).textContent = `Stand ${datum(v.datum)} · ${v.kurz}`; }
    $('#bzurueck', w).classList.toggle('versteckt', !v.vorherige);
  });

  $('#bpruefen', w).addEventListener('click', async e => {
    const b = e.currentTarget, erg = $('#uergebnis', w);
    b.disabled = true; b.textContent = 'Suche …';
    const r = await sicher('/api/update/pruefen');
    erg.innerHTML = '';
    if (!r.ok) erg.innerHTML = `<div class="hinweis fehler">${esc(r.meldung)}</div>`;
    else if (!r.neu.length) erg.innerHTML = '<div class="hinweis gut">Die Box ist auf dem neuesten Stand.</div>';
    else erg.innerHTML = `<div class="hinweis">${r.neu.length === 1 ? '1 neue Änderung:' : r.neu.length + ' neue Änderungen:'}<ul class="neu">${r.neu.map(n => `<li>${esc(n.text)}</li>`).join('')}</ul></div>`;
    $('#bupdate', w).classList.toggle('versteckt', !(r.ok && r.neu.length > 0));
    b.disabled = false; b.textContent = 'Nach Updates suchen';
  }, {signal});
  $('#bupdate', w).addEventListener('click', async () => { const e = await boxAktion('update'); if (e && e.ok) $('#bupdate', w).classList.add('versteckt'); }, {signal});
  $('#bzurueck', w).addEventListener('click', () => boxAktion('zurueck'), {signal});

  $('#mdetails', w).addEventListener('toggle', async e => {
    if (!e.target.open) return;
    try { const m = await holen('/api/meldungen'); const p = $('#mtext', w); p.textContent = m.text || '(keine Meldungen)'; p.scrollTop = p.scrollHeight; }
    catch (x) { $('#mtext', w).textContent = 'Keine Verbindung zur Box.'; }
  }, {signal});
  ['#mkopieren', '#dkopieren'].forEach(id => $(id, w).addEventListener('click', async e => {
    const text = $('#' + e.currentTarget.dataset.quelle, w).textContent;
    if (!text || text === 'wird geladen …') { toast('Noch nicht geladen, bitte kurz warten.', 'fehler'); return; }
    const ok = await kopieren(text);
    toast(ok ? 'Kopiert – jetzt im Chat einfügen.' : 'Kopieren ging nicht. Text lange drücken und markieren.', ok ? 'ok' : 'fehler');
  }, {signal}));
  $('#ddetails', w).addEventListener('toggle', async e => {
    if (!e.target.open) return;
    $('#dtext', w).textContent = 'wird geladen …';
    try { const d = await holen('/api/diagnose'); $('#dtext', w).textContent = d.text || '(keine Angaben)'; }
    catch (x) { $('#dtext', w).textContent = 'Keine Verbindung zur Box.'; }
  }, {signal});
}
