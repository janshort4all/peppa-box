// Grafischer Equalizer: 10 Bänder als Punkte auf einer Kurve, senkrecht ziehen (Finger oder Maus),
// Pfeiltasten am gewählten Punkt, doppelt tippen = 0 dB.
import {$, esc, holen, melden, sicher, toast} from './kern.js';

const VORLAGE_NAMEN = {neutral: 'Neutral', klein: 'Kleiner Lautsprecher', sprache: 'Hörspiel', weich: 'Weicher'};
const EQ = {B: 360, H: 238, L: 34, R: 10, O: 24, U: 40};                       // Größe und Ränder (SVG-Einheiten)
const dbText = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + ' dB';
const eqKurz = n => n.replace(' kHz', 'k').replace(' Hz', '');

export async function equalizer(w, signal) {
  w.innerHTML = '<div class="leise">wird geladen …</div>';
  let klang, ziehen = null, timer = null;
  try { klang = await holen('/api/klang'); } catch (e) { w.textContent = 'Keine Verbindung zur Box.'; return; }
  if (signal.aborted) return;

  const eqX = i => EQ.L + (EQ.B - EQ.L - EQ.R) * (i + 0.5) / klang.namen.length;
  const eqY = db => EQ.O + (EQ.H - EQ.O - EQ.U) * (klang.max - db) / (klang.max - klang.min);
  const eqDb = y => Math.max(klang.min, Math.min(klang.max, Math.round(klang.max - (y - EQ.O) / (EQ.H - EQ.O - EQ.U) * (klang.max - klang.min))));
  function kurve(p) {                                                           // weiche Kurve durch alle Punkte (Catmull-Rom)
    const q = [[EQ.L, p[0][1]], ...p, [EQ.B - EQ.R, p[p.length - 1][1]]];
    let d = `M${q[0][0]},${q[0][1]}`;
    for (let i = 0; i < q.length - 1; i++) {
      const a = q[Math.max(0, i - 1)], b = q[i], c = q[i + 1], e = q[Math.min(q.length - 1, i + 2)];
      d += ` C${b[0] + (c[0] - a[0]) / 6},${b[1] + (c[1] - a[1]) / 6} ${c[0] - (e[0] - b[0]) / 6},${c[1] - (e[1] - b[1]) / 6} ${c[0]},${c[1]}`;
    }
    return d;
  }
  function zeichnen() {
    const svg = $('#ksvg', w); if (!svg) return;
    const p = klang.baender.map((v, i) => [eqX(i), eqY(v)]), k = kurve(p), y0 = eqY(0);
    svg.querySelector('.kurve').setAttribute('d', k);
    svg.querySelector('.flaeche').setAttribute('d', `${k} L${EQ.B - EQ.R},${y0} L${EQ.L},${y0} Z`);
    klang.baender.forEach((v, i) => {
      const g = $('#kband-' + i, w);
      g.querySelector('.punkt').setAttribute('cy', p[i][1]);
      g.setAttribute('aria-valuenow', v); g.setAttribute('aria-valuetext', dbText(v));
      $('#kw-' + i, w).textContent = (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v);
    });
    const b = $('#kblase', w);
    if (ziehen === null) b.style.display = 'none';
    else {
      const i = ziehen, x = Math.max(EQ.L + 26, Math.min(EQ.B - EQ.R - 26, p[i][0])), y = Math.max(EQ.O + 2, p[i][1] - 36);
      b.style.display = '';
      b.querySelector('rect').setAttribute('x', x - 26); b.querySelector('rect').setAttribute('y', y);
      b.querySelector('text').setAttribute('x', x); b.querySelector('text').setAttribute('y', y + 16);
      b.querySelector('text').textContent = dbText(klang.baender[i]);
    }
    w.querySelectorAll('.vorlagen .btn').forEach(btn => {
      const v = klang.vorlagen[btn.dataset.v];
      btn.classList.toggle('an', !!v && v.every((x, i) => x === klang.baender[i]));
    });
  }
  const zeiger = ev => { const r = $('#ksvg', w).getBoundingClientRect(); return [(ev.clientX - r.left) * EQ.B / r.width, (ev.clientY - r.top) * EQ.H / r.height]; };
  function setzen(i, v) {
    if (klang.baender[i] === v) return;
    klang.baender[i] = v; zeichnen();
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const erg = await sicher('/api/klang', {baender: klang.baender});
      if (!erg.ok) melden(erg);
    }, 150);
  }
  signal.addEventListener('abort', () => clearTimeout(timer));

  function einrichten() {
    const svg = $('#ksvg', w), n = klang.namen.length, breite = (EQ.B - EQ.L - EQ.R) / n;
    let tipp = {i: -1, t: 0};
    svg.addEventListener('pointerdown', ev => {
      const [x, y] = zeiger(ev), i = Math.max(0, Math.min(n - 1, Math.floor((x - EQ.L) / breite)));
      if (x < EQ.L - 6 || y > EQ.H - EQ.U + 14) return;
      ev.preventDefault();
      const jetzt = Date.now();
      if (tipp.i === i && jetzt - tipp.t < 350) { setzen(i, 0); tipp = {i: -1, t: 0}; return; }
      tipp = {i, t: jetzt}; ziehen = i; svg.setPointerCapture(ev.pointerId);
      $('#kband-' + i, w).classList.add('aktiv'); $('#kband-' + i, w).focus({preventScroll: true});
      setzen(i, eqDb(y)); zeichnen();
    });
    svg.addEventListener('pointermove', ev => { if (ziehen !== null) setzen(ziehen, eqDb(zeiger(ev)[1])); });
    const los = () => { if (ziehen === null) return; $('#kband-' + ziehen, w).classList.remove('aktiv'); ziehen = null; zeichnen(); };
    svg.addEventListener('pointerup', los); svg.addEventListener('pointercancel', los);
    svg.querySelectorAll('.band').forEach((g, i) => g.addEventListener('keydown', ev => {
      const s = {ArrowUp: 1, ArrowRight: 1, PageUp: 3, ArrowDown: -1, ArrowLeft: -1, PageDown: -3}[ev.key];
      if (ev.key === 'Home') { ev.preventDefault(); return setzen(i, klang.max); }
      if (ev.key === 'End') { ev.preventDefault(); return setzen(i, klang.min); }
      if (ev.key === '0') { ev.preventDefault(); return setzen(i, 0); }
      if (!s) return;
      ev.preventDefault();
      setzen(i, Math.max(klang.min, Math.min(klang.max, klang.baender[i] + s)));
    }));
  }
  function aufbauen() {
    if (!klang.da) {
      w.innerHTML = '<div class="hinweis fehler">Der Equalizer ist noch nicht eingerichtet: einmal am Pi <b>sh ~/peppa-box/software/dienst_einrichten.sh</b> ausführen.</div>';
      return;
    }
    const gitter = [];
    for (let db = klang.max; db >= klang.min; db -= 6) {
      const y = eqY(db);
      gitter.push(`<line class="${db === 0 ? 'null' : 'gitter'}" x1="${EQ.L}" x2="${EQ.B - EQ.R}" y1="${y}" y2="${y}"/>`,
        `<text class="achse" x="${EQ.L - 6}" y="${y + 4}" text-anchor="end">${db > 0 ? '+' : db < 0 ? '−' : ''}${Math.abs(db)}</text>`);
    }
    const yU = EQ.H - EQ.U;
    const baender = klang.namen.map((nm, i) => {
      const x = eqX(i);
      return `<g class="band" id="kband-${i}" tabindex="0" role="slider" aria-label="${esc(nm)}" aria-valuemin="${klang.min}" aria-valuemax="${klang.max}">
        <line class="schiene" x1="${x}" x2="${x}" y1="${eqY(klang.max)}" y2="${eqY(klang.min)}"/>
        <circle class="punkt" cx="${x}" cy="${eqY(0)}" r="9"/>
        <text class="wertchen" id="kw-${i}" x="${x}" y="${yU + 18}"></text>
        <text class="achse" x="${x}" y="${yU + 34}" text-anchor="middle">${esc(eqKurz(nm))}</text></g>`;
    }).join('');
    w.innerHTML = `<p class="leise klein" style="margin-top:0">Wirkt sofort, am besten bei laufender Musik einstellen. Gilt für den Lautsprecher, nicht für Kopfhörer.
        Kleine Lautsprecher klingen meist besser mit weniger Bass. Punkte nach oben oder unten ziehen, doppelt tippen = 0 dB.</p>
      ${klang.fehler ? `<div class="hinweis fehler">Der Equalizer ging nicht, die Musik lief ohne ihn weiter: ${esc(klang.fehler)}. Beim nächsten Musikstart wird er wieder versucht.</div>` : ''}
      <div class="eq"><svg id="ksvg" viewBox="0 0 ${EQ.B} ${EQ.H}" aria-label="Equalizer">${gitter.join('')}
        <text class="achse" x="${EQ.L - 6}" y="11" text-anchor="end">dB</text><path class="flaeche"/><path class="kurve"/>${baender}
        <g class="blase" id="kblase" style="display:none"><rect width="52" height="22" rx="7"/><text></text></g></svg></div>
      <div class="vorlagen">${Object.keys(klang.vorlagen).map(v => `<button class="btn" data-v="${esc(v)}">${esc(VORLAGE_NAMEN[v] || v)}</button>`).join('')}</div>`;
    einrichten(); zeichnen();
    w.querySelector('.vorlagen').addEventListener('click', async e => {
      const b = e.target.closest('[data-v]'); if (!b) return;
      const erg = await sicher('/api/klang', {vorlage: b.dataset.v});
      if (erg.ok) { klang.baender = erg.baender; zeichnen(); toast((VORLAGE_NAMEN[b.dataset.v] || b.dataset.v) + ' eingestellt.'); } else melden(erg);
    }, {signal});
  }
  aufbauen();
}
