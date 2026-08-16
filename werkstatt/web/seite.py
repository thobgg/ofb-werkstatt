"""HTML der Korrekturmaske. Ausgelagert, damit app.py lesbar bleibt."""

SEITE = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>OFB-Werkstatt</title><style>
*{box-sizing:border-box}
body{margin:0;font:15px/1.45 system-ui,sans-serif;background:#14161a;color:#e6e8ec}
header{position:sticky;top:0;background:#1b1e24;border-bottom:1px solid #2c313a;
 padding:.55rem 1rem;display:flex;gap:1rem;align-items:center;z-index:9}
header b{font-size:1rem}
.zaehler{color:#9aa3b2;font-size:.86rem}
kbd{background:#2b313b;border:1px solid #3a424f;border-bottom-width:2px;border-radius:4px;
 padding:0 .3rem;font:inherit;font-size:.8rem;color:#c3c9d4}
main{padding:1rem;max-width:1500px;margin:0 auto}
.eintrag{background:#1b1e24;border:1px solid #2c313a;border-radius:10px;
 margin-bottom:1rem;overflow:hidden}
.eintrag.fokus{border-color:#4b7bec;box-shadow:0 0 0 1px #4b7bec}
.eintrag.fertig{opacity:.55}
.kopf{padding:.45rem .9rem;background:#20242c;display:flex;gap:.8rem;
 align-items:center;font-size:.9rem}
.kopf .q{font-weight:600}
.bildbox{overflow-x:auto;background:#fff;cursor:zoom-in;position:relative}
/* Die gedruckten Spaltenueberschriften als Text. Sie stehen nicht ueber
   "ihrer" Spalte - dafuer braeuchte es das Spaltenraster, und das traegt
   die Messung nicht. In Leserichtung aufgezaehlt helfen sie trotzdem:
   Bei blassem Druck steht hier, was die Spalte ueberhaupt verlangt. */
.warnung{padding:.4rem .9rem;background:#2c2113;color:#f0d089;
 font-size:.82rem;border-top:1px solid #4a3a13}
.spalten{display:flex;flex-wrap:wrap;gap:.3rem;padding:.35rem .9rem;
 background:#161a20;border-top:1px solid #262b34}
.spalten span{font-size:.72rem;color:#8b93a3;background:#1d222a;
 border-radius:3px;padding:.1rem .4rem}
.spalten span:nth-child(odd){color:#a7b0c0}

/* Vergroessert bekommt der Kasten eine feste Hoehe, sonst waechst er ins
   Endlose und es gibt gar nichts zu verschieben – nur eine sehr lange
   Seite. */
.bildbox.gross{cursor:grab;max-height:70vh;overflow:auto}
.bildbox.gross.zieht{cursor:grabbing}
.bildbox.gross img{user-select:none;-webkit-user-drag:none}
.bildbox img{width:100%;display:block}
/* Der gedruckte Kopf ueber jedem Streifen, gleich breit geschnitten –
   damit Ueberschrift und Zelle uebereinanderstehen. Ohne ihn sieht man ab
   dem zweiten Eintrag nur Zellen: rechts liegen "Zeit der Geburt" und
   "Ort und Tag der Taufe" nebeneinander, beide mit einem Datum darin. */
.bildbox .kopfband{border-bottom:2px solid #2f6fdd;opacity:.85}
.bildbox.gross .kopfband{position:sticky;top:0;z-index:2;background:#fff}
.bildbox.gross img{width:auto;max-width:none}
.zh{position:absolute;top:.3rem;right:.5rem;background:#0009;color:#fff;
 font-size:.7rem;padding:.1rem .4rem;border-radius:4px;pointer-events:none}
.zh a{pointer-events:auto}
.person{display:grid;grid-template-columns:5.5rem 15rem 1fr auto;gap:.6rem;
 align-items:center;padding:.4rem .9rem;border-bottom:1px solid #23272f}
.person.aktiv{background:#182031}
.feldbox{position:relative}
/* Vorname fett, Nachname dahinter - so, wie die Ausgabe es trennt. */
.teilung{display:block;font-size:.72rem;color:#7d8798;padding:.15rem .1rem 0;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.teilung b{color:#9aa3b2;font-weight:600}
.vorschlag{position:absolute;top:100%;left:0;right:0;z-index:20;background:#20242c;
 border:1px solid #3a424f;border-radius:0 0 8px 8px;max-height:17rem;overflow:auto;
 box-shadow:0 8px 22px #0008}
.vorschlag div{padding:.32rem .55rem;cursor:pointer;font-size:.85rem;
 border-bottom:1px solid #262b33;display:flex;gap:.5rem;align-items:baseline}
.vorschlag div:last-child{border-bottom:0}
.vorschlag div.an,.vorschlag div:hover{background:#2f6fdd;color:#fff}
.vorschlag .id{font-family:ui-monospace,monospace;font-size:.76rem;opacity:.85}
.vorschlag .neb{color:#8b93a3;font-size:.78rem;margin-left:auto;text-align:right}
.vorschlag div.an .neb{color:#dbe6ff}
.vorschlag .kopfz{background:#191d24;color:#8b93a3;font-size:.72rem;
 text-transform:uppercase;letter-spacing:.05em;cursor:default}
.vorschlag .kopfz:hover{background:#191d24;color:#8b93a3}
.rolle{color:#8b93a3;font-size:.78rem;letter-spacing:.04em;text-transform:uppercase}
.pkt{width:.6rem;height:.6rem;border-radius:50%;display:inline-block;margin-right:.15rem}
.gruen{background:#3ecf8e}.gelb{background:#e0b341}.rot{background:#e06c5f}
.grau{background:#4a515c}
.person.gruen-zeile{opacity:.72}
.treffer{font-size:.86rem;color:#8fe3b4}
.treffer .id{font-family:ui-monospace,monospace;background:#1d4231;padding:.05rem .35rem;
 border-radius:4px}
.treffer .warum{color:#7d8798;margin-left:.4rem}
.neu{font-size:.86rem;color:#d4a72c}
input{background:#12141a;border:1px solid #333a45;color:#e6e8ec;border-radius:6px;
 padding:.32rem .5rem;font:inherit;width:100%}
input:focus{outline:2px solid #4b7bec;border-color:transparent}
input.geaendert{border-color:#d4a72c;background:#1e1a10}
.knopf{display:flex;gap:.3rem}
button{background:#333a45;color:#e6e8ec;border:0;border-radius:6px;padding:.3rem .6rem;
 font:inherit;font-size:.85rem;cursor:pointer}
button.ja{background:#2f6fdd;color:#fff}
button.an{outline:2px solid #8fe3b4}
button:hover{filter:brightness(1.15)}
.daten{display:flex;gap:.6rem;align-items:center;padding:.5rem .9rem;flex-wrap:wrap}
.daten label{color:#8b93a3;font-size:.78rem}
.daten input{width:9rem}
.mehr{padding:0 .9rem .7rem}
details summary{cursor:pointer;color:#8b93a3;font-size:.84rem;padding:.3rem 0}
.zeile{display:grid;grid-template-columns:10rem 1fr 1fr;gap:.4rem;padding:.15rem 0}
.zeile label{color:#8b93a3;font-size:.8rem;align-self:center}
.fuss{padding:.5rem .9rem;background:#191d24;display:flex;gap:.5rem;align-items:center}
.zweite{padding:.5rem .9rem;border-bottom:1px solid #23272f;font-size:.88rem}
.zweite .zkopf{color:#9aa3b2;margin-bottom:.4rem}
.ztab{width:100%;border-collapse:collapse;font-size:.86rem}
.ztab th{text-align:left;color:#8b93a3;font-weight:500;font-size:.76rem;
 text-transform:uppercase;letter-spacing:.04em;padding:.2rem .4rem}
.ztab td{padding:.22rem .4rem;border-top:1px solid #23272f;vertical-align:top}
.ztab td:nth-child(3){color:#e0b341}
.seitenschau{position:fixed;inset:0;background:#0b0d10ee;z-index:50;
 display:flex;flex-direction:column;padding:1rem;gap:.6rem}
.seitenschau .leiste{display:flex;gap:.6rem;align-items:center;
 font-size:.9rem;flex-wrap:wrap}
.seitenschau .blatt{position:relative;flex:1;overflow:auto;background:#fff}
.seitenschau img{width:100%;display:block;max-width:none}
.seitenschau i{position:absolute;border:3px solid #4b7bec;
 background:#4b7bec22;pointer-events:none;border-radius:2px}
.gespraech{padding:.6rem .9rem .7rem;border-top:1px solid #23272f}
.gespraech .reihe{display:flex;gap:.5rem;align-items:center}
.gespraech .frage{flex:1;background:#12141a;border:1px solid #333a45;
 color:#e6e8ec;border-radius:6px;padding:.4rem .6rem;font:inherit}
.verlauf{max-height:22rem;overflow-y:auto}
.verlauf:not(:empty){margin-bottom:.55rem}
.sagt{display:flex;gap:.5rem;margin-bottom:.5rem;font-size:.89rem;
 line-height:1.5}
.sagt .wer{flex:none;width:1.4rem;height:1.4rem;border-radius:50%;
 display:grid;place-items:center;font-size:.72rem;background:#333a45;
 color:#c3c9d4}
.sagt.modell .wer{background:#1d4231;color:#8fe3b4}
.sagt .txt{white-space:pre-wrap;color:#c3c9d4}
.sagt.mensch .txt{color:#e6e8ec}
.sagt.wartet .txt{color:#8b93a3;font-style:italic}
.anbind{padding:.45rem .9rem;font-size:.86rem;border-bottom:1px solid #23272f;
 display:flex;gap:.6rem;align-items:center;flex-wrap:wrap}
.anbind .lbl{color:#8b93a3;font-size:.78rem;text-transform:uppercase;
 letter-spacing:.04em;min-width:5.5rem}
.anbind.ok{background:#132a1f}
.anbind.warn{background:#2c2113}
.anbind .fid{font-family:ui-monospace,monospace;background:#1d4231;padding:.05rem .35rem;
 border-radius:4px;color:#8fe3b4}
.anbind.warn .fid{background:#4a3a13;color:#f0d089}
.anbind .hinw{color:#9aa3b2}
.leer{padding:3rem;text-align:center;color:#9aa3b2}
.fortschritt{height:.3rem;background:#262b33;position:sticky;top:2.6rem;z-index:8}
.fortschritt i{display:block;height:100%;background:#2f6fdd;transition:width .25s}
.tasten{display:flex;gap:.5rem;align-items:center;padding:.6rem .9rem;
 background:#191d24;border-top:1px solid #23272f;flex-wrap:wrap}
.tasten kbd{background:#2b313b;border:1px solid #3a424f;border-bottom-width:2px;
 border-radius:4px;padding:.05rem .35rem;font:inherit;font-size:.8rem;color:#c3c9d4}
.still{padding:.35rem .9rem;font-size:.88rem;color:#9aa3b2;
 border-bottom:1px solid #23272f;display:flex;gap:.5rem;flex-wrap:wrap}
.still b{color:#c3c9d4;font-weight:600}
.frage{background:#1a2130;border-left:3px solid #4b7bec}
.vorschlag2{padding:.4rem .9rem .6rem;font-size:.9rem}
.vorschlag2 .kand{display:flex;gap:.6rem;align-items:baseline;padding:.25rem 0}
.vorschlag2 .id{font-family:ui-monospace,monospace;font-size:.78rem;
 background:#1d4231;color:#8fe3b4;padding:.05rem .35rem;border-radius:4px}
</style></head><body>
<header><a href="/" style="color:#9aa3b2;text-decoration:none">&larr;</a>
<b>OFB-Werkstatt</b><span class=zaehler id=runde></span>
<span class=zaehler id=z></span>
<span style=flex:1></span>
<span class=zaehler id=tasten></span>
<button id=alle onclick=umschalten() title="alle Einträge auf einer Seite">Liste</button>
<button onclick=beenden() title="Werkstatt beenden">⏻</button>
</header>
<div class=fortschritt><i id=bal style=width:0></i></div>
<main id=app class=leer>lade…</main>
<script>
let daten=[],fokus=0;
const esc=s=>(s??'').toString().replace(/[&<>"]/g,c=>
 ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

let runde=null, i=0, liste=false;

// ------------------------------------------------------------- Aufwand
// Der ehrlichere Massstab als eine Trefferquote: Eine Quote misst das
// Buch, diese Zahlen messen das Werkzeug. Bei schwerer Hand wird viel
// getippt, bei klarer Schrift nur bestaetigt – beides brauchbar, die
// Frage ist, wie viel Arbeit uebrig bleibt.
//
// Gezaehlt wird still im Hintergrund und nur je Eintrag: Zeichen, Klicks,
// Sekunden. Keine Tastenfolgen, kein Inhalt.
const aufwand = {};
function zaehle(id, was, n) {
 if (!id) return;
 const a = aufwand[id] || (aufwand[id] = {tasten:0, klicks:0, seit:Date.now()});
 a[was] = (a[was]||0) + (n||1);
}
function eintragUnter(el){
 const e = el && el.closest && el.closest('.eintrag');
 return e ? +e.dataset.id : null;
}
document.addEventListener('keydown', ev => {
 // Nur Zeichen zaehlen, nicht Umschalt- und Pfeiltasten.
 if (ev.key && ev.key.length === 1) zaehle(eintragUnter(ev.target), 'tasten');
}, true);
document.addEventListener('click', ev => {
 zaehle(eintragUnter(ev.target), 'klicks');
}, true);

async function laden(){
 const stand=await (await fetch('/api/stand')).json();
 runde=stand.runde;
 // Die Maske zeigt die gerade gelesene Tranche, nicht den ganzen Bestand.
 const q=runde?('?runde='+runde.id):'';
 daten=await (await fetch('/api/eintraege'+q)).json();
 const r=document.getElementById('runde');
 if(runde) r.textContent=`Runde ${runde.nr} · ${runde.register}`;
 if(!daten.length){document.getElementById('app').className='leer';
  document.getElementById('app').innerHTML=
   'Nichts zu korrigieren. <a href="/lesen" style=color:#7fb0ff>Runde lesen</a>';
  return}
 document.getElementById('app').className='';
 // Beim Öffnen dort weitermachen, wo noch etwas offen ist.
 const offen=daten.findIndex(e=>e.status!=='bestaetigt');
 i = offen>=0 ? offen : 0;
 zeichne();
}

function zeichne(){
 const app=document.getElementById('app');
 if(liste){
  app.innerHTML=daten.map((e,k)=>karte(e,k)).join('');
  document.querySelectorAll('.eintrag').forEach(el=>anbindung(el));
 } else {
  app.innerHTML=karte(daten[i], i);
  const el=app.querySelector('.eintrag'); if(el) anbindung(el);
  const erste=app.querySelector('.person.frage input');
  if(erste) setTimeout(()=>erste.focus(), 60);
 }
 document.querySelectorAll('.gespraech').forEach(el=>verlaufHolen(el));
 zaehler();
 document.getElementById('alle').textContent = liste ? 'Einzeln' : 'Liste';
 document.getElementById('tasten').innerHTML = liste ? '' :
  '<kbd>Enter</kbd> übernehmen · <kbd>N</kbd> neu · <kbd>↓</kbd><kbd>↑</kbd> blättern'
  +' · <kbd>Strg</kbd>+<kbd>Enter</kbd> fertig';
}

function umschalten(){ liste=!liste; zeichne();
 if(!liste) window.scrollTo(0,0); }

function karte(e,k){
 // Was der Abgleich getragen hat, steht still da. Was er nicht trägt,
 // bekommt den Platz – und den Fokus.
 const pers=e.felder.filter(f=>f.rolle);
 const still=pers.filter(f=>f.ampel==='gruen');
 const frage=pers.filter(f=>f.ampel!=='gruen');
 const rest=e.felder.filter(f=>!f.rolle&&f.wert);
 return `<div class="eintrag${liste?'':' fokus'}" data-i=${k} data-id=${e.id}>
  <div class=kopf><span class=q>Nr. ${esc(e.nr)}</span>
   <span>${e.jahr||''}</span><span style=color:#6f7787>${esc(e.bild||'')}</span>
   <span style=flex:1></span>
   ${e.seite?`<button onclick="ganzeSeite(${k})"
     title="die ganze Buchöffnung, mit dieser Zeile markiert">ganze Seite</button>`:''}
   <button onclick="nochmalLesen(${k},this)"
     title="dieselbe Zeile ein zweites Mal lesen lassen und vergleichen"
     >nochmal lesen</button>
   <span class=zaehler>${liste?esc(e.status):`Eintrag ${k+1} von ${daten.length}`}</span></div>
  ${e.bemerkung?`<div class=warnung>⚠ ${esc(e.bemerkung)} – die
    Zeilengrenzen sind hier nicht gemessen, sondern gleichmäßig geteilt.
    Der Streifen kann zu früh oder zu spät anfangen.</div>`:''}
  ${e.spalten&&e.spalten.length?`<div class=spalten title="die gedruckten
    Überschriften dieses Formulars, einmal je Formularperiode gelesen"
    >${e.spalten.map(s=>`<span>${esc(s)}</span>`).join('')}</div>`:''}
  ${e.ausschnitt?`<div class=bildbox onpointerdown="greifen(event,this)">
    ${e.kopf?`<img class=kopfband src="/bild/${encodeURI(e.kopf)}"
      loading=lazy alt="Spaltenüberschriften">`:''}
    <img src="/bild/${encodeURI(e.ausschnitt)}" loading=lazy alt="">
    <span class=zh>klicken zum Vergrößern, dann ziehen</span></div>`:''}
  ${still.length?`<div class=still><span class=dim>gesichert:</span>
    ${still.map(f=>`<span><i class="pkt gruen"></i> ${esc(f.rolle)}
      <b>${esc(f.wert||'')}</b></span>`).join('')}</div>`:''}
  ${rest.length?`<div class=still><span class=dim>gelesen:</span>
    ${rest.map(f=>`<span>${esc(beschriftung(f))}
      <b>${esc(String(f.wert).slice(0,40))}</b></span>`).join('')}</div>`:''}
  ${frage.map(f=>zeilePerson(e,f)).join('')}
  <div class=anbind data-anbind><span class=lbl>Familie</span>
   <span class=hinw>wird ermittelt…</span></div>
  <div class=daten>
   ${datumsfeld(e,'geburt_datum','geb.')}
   ${datumsfeld(e,'tauf_datum','get.')}
   ${datumsfeld(e,'trauung_datum','kop.')}
   ${datumsfeld(e,'sterbe_datum','gest.')}
  </div>
  <div class=mehr>
   <div class=nachtrag>
    ${zeilen(e).map(f=>zeileFeld(f)).join('')}
   </div>
   ${leere(e).length?`<div class=reihe style="margin-top:.3rem">
     <button onclick="feldDazu(this)" title="ein Feld nachtragen">+ Feld</button>
     <select class=feldwahl onchange="feldDazu(this)"
       style="display:none;background:#12141a;border:1px solid #333a45;
              color:#e6e8ec;border-radius:6px;padding:.3rem .5rem;font:inherit">
      <option value="">– welches Feld? –</option>
      ${leere(e).map(f=>`<option value="${esc(f.name)}">${
        esc(beschriftung(f))}</option>`).join('')}
     </select>
     <span class=zaehler>${leere(e).length} Felder sind leer</span>
    </div>`:''}
  </div>
  <div class=gespraech data-eintrag=${e.id}>
   <div class=verlauf></div>
   <div class=reihe>
    <input class=frage placeholder="Nachfragen – z. B. „steht da Möß oder Wöß?“"
      onkeydown="if(event.key==='Enter'){event.stopPropagation();fragen(this)}">
    <button onclick="fragen(this)">fragen</button>
   </div>
   <div class=zh>Antwortet mit Eintrag, Bildausschnitt und Bestandstreffern
    vor Augen. Ändert nichts – eintragen tust du selbst.</div>
  </div>
  <div class=fuss><button class=ja onclick="fertig(${k})">Fertig · weiter</button>
   <span class=zaehler>Strg+Enter</span>
   ${liste?'':`<span style=flex:1></span>
     <button onclick="blaettern(-1)">zurück</button>
     <button onclick="blaettern(1)">überspringen</button>`}</div>
 </div>`;
}

function blaettern(d){
 const n=i+d;
 if(n<0||n>=daten.length) return;
 i=n; zeichne(); window.scrollTo(0,0);
}

// ------------------------------------------------------------- Gespräch
function zeigeVerlauf(box,g){
 box.querySelector('.verlauf').innerHTML = g.map(x=>
  `<div class="sagt ${x.wer}"><span class=wer>${x.wer==='mensch'?'du':'?'}</span>
    <div class=txt>${esc(x.text)}</div></div>`).join('');
}

async function verlaufHolen(box){
 const id=box.dataset.eintrag;
 const g=await (await fetch('/api/gespraech?eintrag='+id)).json();
 zeigeVerlauf(box,g);
}

async function fragen(el){
 const box=el.closest('.gespraech');
 const inp=box.querySelector('.frage');
 const text=inp.value.trim();
 if(!text) return;
 const knopf=box.querySelector('button');
 inp.disabled=knopf.disabled=true;
 // Sofort anzeigen, was gefragt wurde – sonst sieht es aus, als sei nichts
 // passiert, und die Antwort kann eine halbe Minute brauchen.
 const v=box.querySelector('.verlauf');
 v.insertAdjacentHTML('beforeend',
  `<div class="sagt mensch"><span class=wer>du</span>
    <div class=txt>${esc(text)}</div></div>
   <div class="sagt modell wartet"><span class=wer>?</span>
    <div class=txt>denkt nach …</div></div>`);
 inp.value='';
 const a=await (await fetch('/api/frage',{method:'POST',
   body:JSON.stringify({eintrag:box.dataset.eintrag, frage:text})})).json();
 v.querySelector('.wartet').remove();
 v.insertAdjacentHTML('beforeend',
  `<div class="sagt modell"><span class=wer>?</span>
    <div class=txt>${esc(a.antwort||'')}</div></div>`);
 inp.disabled=knopf.disabled=false; inp.focus();
 v.scrollTop=v.scrollHeight;
}

async function beenden(){
 if(!confirm('Werkstatt beenden?\n\nDer Server hört auf zu laufen; nichts '
  +'geht verloren. Zum Weiterarbeiten das Startskript erneut aufrufen.')) return;
 try{ await fetch('/api/beenden',{method:'POST'}); }catch(e){}
 document.body.innerHTML='<main class=leer style="padding:4rem">'
  +'<div style="font-size:1.2rem;margin-bottom:.6rem">Werkstatt beendet.</div>'
  +'<div class=dim>Dieses Fenster kann zu.</div></main>';
}

// Wer einen Buchstaben nicht entziffert, sucht ihn anderswo auf derselben
// Buchoeffnung – in einer Formel, die dieselbe Hand zehnmal geschrieben
// hat. Der Streifen allein nimmt diese Eichung weg; das ist keine
// Schoenheitsfrage, sondern die Regel „Kontext ist Teil der Information".
// Wie der Name in die Ausgabe geht. Das Register schreibt ihn in einem
// Stueck, GEDCOM trennt Vor- und Nachnamen, und geraten wird dabei nach
// dem letzten Wort. Das geht bei "Johann Georg Kröneck" gut und bei
// "Hans von der Au" schief - deshalb steht die Teilung sichtbar unter dem
// Feld, und wer es besser weiss, klammert den Nachnamen: /von der Au/.
// `rolle` entscheidet bei einem einzelnen Wort: Bei Kind und Mutter ist
// es der Vorname (ihr Nachname kommt vom Vater oder aus dem
// Geburtsnamen), beim Braeutigam der Nachname. Dieselbe Regel wie in
// uebergabe.NUR_VORNAME - sonst zeigt die Maske etwas anderes an, als
// hinterher in der Ausgabe steht.
const NUR_VORNAME = ['kind', 'mutter'];
function teileName(wert, rolle){
  const w = (wert||'').trim();
  if(!w) return null;
  if(NUR_VORNAME.includes(rolle) && !w.includes('/') && w.split(/\s+/).length === 1)
    return {vor: w, nach: ''};
  if(w.includes('/')){
    const i = w.indexOf('/'), r = w.slice(i+1), j = r.indexOf('/');
    const nach = (j<0?r:r.slice(0,j)).trim();
    const vor = (w.slice(0,i) + ' ' + (j<0?'':r.slice(j+1))).trim();
    return {vor, nach};
  }
  const t = w.split(/\s+/);
  return t.length>1 ? {vor:t.slice(0,-1).join(' '), nach:t[t.length-1]}
                    : {vor:'', nach:t[0]};
}
function teilungText(wert, rolle){
  const t = teileName(wert, rolle);
  if(!t) return '';
  return `<b>${esc(t.vor||'–')}</b> · ${esc(t.nach||'–')}`;
}
function teilung(inp){
  const z = inp.parentElement.querySelector('.teilung');
  if(z) z.innerHTML = teilungText(inp.value, z.dataset.rolle||'');
}

// Klicken vergroessert, Ziehen verschiebt. Beides an einem Zeiger, also
// entscheidet die zurueckgelegte Strecke: unter fuenf Pixeln war es ein
// Klick. Vorher liess sich der vergroesserte Streifen nur ueber die
// Bildlaufleiste bewegen, und jeder Versuch, ihn zu fassen, schaltete
// die Vergroesserung wieder ab.
function greifen(ev, box){
  if(ev.button) return;
  const start = {x:ev.clientX, y:ev.clientY,
                 l:box.scrollLeft, t:box.scrollTop};
  let weit = 0;
  box.setPointerCapture(ev.pointerId);
  const zieh = e => {
    const dx = e.clientX - start.x, dy = e.clientY - start.y;
    weit = Math.max(weit, Math.abs(dx) + Math.abs(dy));
    if(!box.classList.contains('gross')) return;
    if(weit > 4) box.classList.add('zieht');
    box.scrollLeft = start.l - dx;
    box.scrollTop  = start.t - dy;
  };
  const los = e => {
    box.removeEventListener('pointermove', zieh);
    box.removeEventListener('pointerup', los);
    box.removeEventListener('pointercancel', los);
    box.classList.remove('zieht');
    if(weit <= 4){
      const vorher = box.classList.toggle('gross');
      // Beim Vergroessern dorthin springen, wo geklickt wurde – sonst
      // steht man am linken Rand und sucht die Stelle wieder.
      if(vorher){
        const r = box.getBoundingClientRect();
        const anteil = (ev.clientX - r.left) / r.width;
        box.scrollLeft = Math.max(0,
          anteil * box.scrollWidth - box.clientWidth / 2);
      }
    }
  };
  box.addEventListener('pointermove', zieh);
  box.addEventListener('pointerup', los);
  box.addEventListener('pointercancel', los);
}

function ganzeSeite(k){
 const e=daten[k]; if(!e||!e.seite) return;
 // x,y,w,h im Original, dahinter die Seitengroesse – die Marke wird
 // gegen die Originalbreite umgerechnet, nicht gegen die des
 // ausgelieferten (verkleinerten) Bildes.
 const [x,y,w,h,SB,SH]=(e.kasten||'0,0,0,0,0,0').split(',').map(Number);
 if(!SB) return;
 const d=document.createElement('div');
 d.className='seitenschau';
 d.onclick=ev=>{ if(ev.target===d||ev.target.classList.contains('zu')) d.remove(); };
 d.innerHTML=`<div class=leiste>
   <b>Nr. ${esc(e.nr)}</b> auf ${esc(e.bild)}
   <span class=dim>– die Zeile ist markiert; dieselbe Hand schreibt ihre
    Formeln auf der ganzen Seite gleich</span>
   <span style=flex:1></span><button class=zu>schließen</button></div>
  <div class=blatt><img src="/bild/${encodeURI(e.seite)}?kante=1600" alt="">
   <i style="left:0;top:0;width:0;height:0"></i></div>`;
 document.body.appendChild(d);
 const img=d.querySelector('img'), mark=d.querySelector('i');
 const setzen=()=>{
  const f=img.clientWidth/SB;
  Object.assign(mark.style,{left:(x*f)+'px', top:(y*f)+'px',
                            width:(w*f)+'px', height:(h*f)+'px'});
  mark.scrollIntoView({block:'center'});
 };
 if(img.complete) setzen(); else img.onload=setzen;
}

// Zwei unabhaengige Lesungen derselben Zeile: Wo sie auseinandergehen,
// liegt der Zweifel. Dieselbe Zeile ergab einmal Wöß / Weingärtner /
// 11. Februar und einmal Möß / Wagner / 4. Februar – drei Unterschiede,
// alle drei vorher unauffaellig.
async function nochmalLesen(k,btn){
 const e=daten[k];
 const box=btn.closest('.eintrag');
 let feld=box.querySelector('.zweite');
 if(!feld){ feld=document.createElement('div'); feld.className='zweite';
            box.querySelector('.still, .person, .daten').before(feld); }
 btn.disabled=true;
 feld.innerHTML='<span class=dim>liest – das dauert eine Weile …</span>';
 const a=await (await fetch('/api/nachlesen',{method:'POST',
   body:JSON.stringify({eintrag:e.id})})).json();
 btn.disabled=false;
 if(!a.ok){ feld.innerHTML=`<span class=dim>${esc(a.meldung||'')}</span>`; return; }
 const anders=a.felder.filter(f=>!f.gleich);
 feld.innerHTML = `<div class=zkopf>Zweite Lesung: ${a.gleich} gleich,
   <b>${a.anders} anders</b>. Geändert wird nichts – was gilt, entscheiden
   Sie am Bild.</div>`
  + (anders.length ? `<table class=ztab>
      <tr><th>Feld</th><th>steht da</th><th>zweite Lesung</th></tr>
      ${anders.map(f=>`<tr>
        <td>${esc(beschriftung(f))}${f.eigen
          ?' <span class=dim>(von Ihnen)</span>':''}</td>
        <td>${esc(f.alt)||'<span class=dim>–</span>'}</td>
        <td>${esc(f.neu)||'<span class=dim>–</span>'}</td></tr>`).join('')}
     </table>` : '');
}

function feld(e,n){return e.felder.find(f=>f.name===n)||{}}

// Beschriftung eines Feldes: der Titel aus der Aktkarte, sonst der
// Feldname mit grossen Anfangsbuchstaben. Vorher stand in der Maske
// "tauf ort" und "geburt zeit" - der Programmname, klein und mit
// Unterstrichen, den niemand ausser dem Code kennt.
function beschriftung(f){
  if(f.titel) return f.titel;
  return (f.name||'').split('_')
    .map(w=>w ? w[0].toUpperCase()+w.slice(1) : w).join(' ');
}

// Welche Felder in den Nachtragsblock gehoeren: alles, was kein
// Personenfeld und kein Datum ist. Gefuellte immer, leere erst wenn der
// Bearbeiter sie ueber "+ Feld" holt – sonst stuenden 16 leere Zeilen da,
// durch die niemand scrollen will.
function passt(f){ return !f.rolle && !/_datum$/.test(f.name); }
function zeilen(e){ return e.felder.filter(f=>passt(f) && (f.wert||f.kb_form||f.offen)); }
function leere(e){ return e.felder.filter(f=>passt(f) && !f.wert && !f.kb_form && !f.offen); }

function zeileFeld(f){
 return `<div class=zeile><label>${esc(beschriftung(f))}</label>
   <input data-feld="${esc(f.name)}" value="${esc(f.wert||'')}"
    oninput="this.classList.add('geaendert')">
   <input data-kb="${esc(f.name)}" value="${esc(f.kb_form||'')}"
    placeholder="Kirchenbuchform" oninput="this.classList.add('geaendert')">
  </div>`;
}

// Der Knopf holt genau ein Feld dazu – kein Aufklappen von 35 Zeilen.
function feldDazu(el){
 const box=el.closest('.mehr');
 const wahl=box.querySelector('.feldwahl');
 if(el.tagName==='BUTTON'){ wahl.style.display=''; wahl.focus(); return; }
 const n=wahl.value; if(!n) return;
 const e=daten[liste?[...document.querySelectorAll('.eintrag')]
   .indexOf(box.closest('.eintrag')):i];
 const f=e.felder.find(x=>x.name===n); if(!f) return;
 f.offen=true;                       // ab jetzt sichtbar, auch leer
 box.querySelector('.nachtrag').insertAdjacentHTML('beforeend', zeileFeld(f));
 wahl.querySelector(`option[value="${n}"]`).remove();
 wahl.value='';
 const neu=box.querySelector(`.nachtrag input[data-feld="${n}"]`);
 if(neu) neu.focus();
}

function zeilePerson(e,f){
 const v=f.entscheidung;
 const treffer = f.person
   ? `<span class=treffer><span class=id>${esc(f.person)}</span>
       <span class=warum>${esc(f.beleg||'')}</span></span>`
   : `<span class=neu>○ ${esc(f.beleg||'kein Treffer')}</span>`;
 return `<div class="person frage" data-feld="${esc(f.name)}"
  ${f.person?`data-person="${esc(f.person)}"`:''}>
  <span class=rolle><i class="pkt ${esc(f.ampel||'grau')}"></i> ${esc(f.rolle)}</span>
  <span class=feldbox><input data-feld="${esc(f.name)}" value="${esc(f.wert||'')}"
   autocomplete=off
   oninput="this.classList.add('geaendert');vorschlagen(this);teilung(this)"
   onkeydown="navVorschlag(event,this)"
   onblur="setTimeout(()=>schliesse(this),180)">
   ${f.name.endsWith('_name')||f.name==='verstorbener_name'
     ?`<span class=teilung data-rolle="${esc(f.rolle||'')}"
        >${teilungText(f.wert, f.rolle)}</span>`:''}</span>
  <span>${v==='neu'?`<span class=neu>● wird neu angelegt</span>`:treffer}</span>
  <span class=knopf>
   <button class="${v==='verknuepft'?'ja an':''}" title="übernehmen (Enter)"
    onclick="setze(this,'verknuepft')" ${f.person?'':'disabled'}>übernehmen</button>
   <button class="${v==='neu'?'ja an':''}" title="neu anlegen (N)"
    onclick="setze(this,'neu')">neu</button>
  </span></div>`;
}

function datumsfeld(e,n,lbl){
 const f=feld(e,n); if(!f.name) return '';
 return `<label>${lbl}</label><input data-feld="${esc(n)}" value="${esc(f.wert||'')}"
  placeholder="TT.MM.JJJJ" oninput="this.classList.add('geaendert')">`;
}
function setze(btn,wert){
 const z=btn.closest('.person');
 z.querySelectorAll('.knopf button').forEach(b=>b.classList.remove('ja','an'));
 btn.classList.add('ja','an');
 z.dataset.entscheidung=wert;
}
async function anbindung(el){
 const box=el.querySelector('[data-anbind]'); if(!box)return;
 const hole=r=>{const p=[...el.querySelectorAll('.person')]
   .find(x=>x.querySelector('.rolle').textContent.toLowerCase()===r);
  return p?(p.dataset.person||''):''};
 const v=hole('vater')||hole('braeutigam'), m=hole('mutter')||hole('braut');
 if(!v&&!m){box.className='anbind';
  box.innerHTML='<span class=lbl>Familie</span><span class=hinw>beide neu</span>';return}
 const d=await(await fetch(`/api/anbindung?vater=${v}&mutter=${m}`)).json();
 let k='anbind',inhalt='';
 if(d.art==='anbinden'){k+=' ok';
  inhalt=`<span class=fid>${d.familie.id}</span><span>${esc(d.familie.text)}</span>
   <span class=hinw>· Kind hier einhängen</span>`;
  box.dataset.fam=d.familie.id;
 } else if(d.art==='neu_pruefen'){k+=' warn';
  inhalt=`<span class=hinw>⚠ ${esc(d.hinweis)}</span>`+
   d.weitere.map(f=>`<span class=fid>${f.id}</span> <span>${esc(f.text)}</span>`).join(' ');
  box.dataset.fam='';
 } else {
  inhalt=`<span class=hinw>${esc(d.hinweis)} – neue Familie</span>`;
  box.dataset.fam='';
 }
 const hv=d.herkunft_vater[0], hm=d.herkunft_mutter[0];
 if(hv)inhalt+=`<span class=hinw>· Eltern Vater: ${esc(hv.vater)} ⚭ ${esc(hv.mutter)}</span>`;
 if(hm)inhalt+=`<span class=hinw>· Eltern Mutter: ${esc(hm.vater)} ⚭ ${esc(hm.mutter)}</span>`;
 box.className=k;
 box.innerHTML='<span class=lbl>Familie</span>'+inhalt;
}
function markiere(){
 document.querySelectorAll('.eintrag').forEach((el,i)=>
   el.classList.toggle('fokus',i===fokus));
}
function zaehler(){
 const fix=daten.filter(e=>e.status==='bestaetigt').length;
 const b=document.getElementById('bal');
 if(b) b.style.width = daten.length ? (100*fix/daten.length)+'%' : '0';
 document.getElementById('z').textContent=`${fix} von ${daten.length} bestätigt`;
 if(fix===daten.length&&daten.length)
  document.getElementById('z').innerHTML+=
   ' · <a href="/uebergabe" style=color:#8fe3b4>übergeben</a>';
}
async function fertig(k){
 const el=document.querySelector(`.eintrag[data-i="${k}"]`);
 if(!el) return;
 const felder={};
 el.querySelectorAll('input[data-feld]').forEach(inp=>{
  const n=inp.dataset.feld;
  const kb=el.querySelector(`input[data-kb="${n}"]`);
  const p=inp.closest('.person');
  felder[n]={wert:inp.value,kb:kb?kb.value:null,
             entscheidung:p?(p.dataset.entscheidung||null):null,
             person:p?(p.dataset.person??undefined):undefined};
 });
 const a=aufwand[daten[k].id]||{};
 const r=await fetch('/api/speichern',{method:'POST',
  headers:{'content-type':'application/json'},
  body:JSON.stringify({id:daten[k].id,felder,bestaetigt:true,
   aufwand:{tasten:a.tasten||0, klicks:a.klicks||0,
            sekunden: a.seit ? Math.round((Date.now()-a.seit)/1000) : 0}})});
 if(!r.ok){alert('Speichern fehlgeschlagen');return}
 daten[k].status='bestaetigt';
 daten[k].felder.forEach(f=>{ if(f.rolle) f.ampel='gruen'; });
 const naechst=daten.findIndex((e,x)=>x>k&&e.status!=='bestaetigt');
 if(liste){
  el.classList.add('fertig'); zaehler();
  if(naechst>=0) document.querySelector(`.eintrag[data-i="${naechst}"]`)
    ?.scrollIntoView({behavior:'smooth',block:'start'});
  return;
 }
 if(naechst>=0){ i=naechst; zeichne(); window.scrollTo(0,0); return; }
 const rest=daten.findIndex(e=>e.status!=='bestaetigt');
 if(rest>=0){ i=rest; zeichne(); window.scrollTo(0,0); return; }
 // Alles bestätigt – weiter zur Übergabe.
 document.getElementById('app').className='leer';
 document.getElementById('app').innerHTML=
  `<p><b>${daten.length} Einträge bestätigt.</b></p>
   <p><a href="/uebergabe" style=color:#7fb0ff>Weiter zur Übergabe →</a></p>`;
 zaehler();
}

// ---- Autovervollständigung: Vokabular + find-and-use ----
let sucheTimer=null;
function schliesse(inp){const b=inp.closest('.feldbox');
 const v=b&&b.querySelector('.vorschlag'); if(v)v.remove()}
function vorschlagen(inp){
 clearTimeout(sucheTimer);
 const q=inp.value.trim();
 if(q.length<2){schliesse(inp);return}
 sucheTimer=setTimeout(async()=>{
  const rolle=inp.closest('.person')?.querySelector('.rolle')?.textContent||'';
  const sex=/mutter|braut/i.test(rolle)?'F':/vater|braeutigam/i.test(rolle)?'M':'';
  const r=await fetch(`/api/suche?q=${encodeURIComponent(q)}&sex=${sex}`);
  const d=await r.json();
  zeige(inp,d);
 },140);
}
function zeige(inp,d){
 schliesse(inp);
 if(!d.namen.length&&!d.personen.length)return;
 const box=document.createElement('div'); box.className='vorschlag';
 let html='';
 if(d.personen.length){
  html+='<div class=kopfz>Person übernehmen – find &amp; use</div>';
  html+=d.personen.map(p=>`<div data-typ=person data-id="${esc(p.id)}"
    data-name="${esc(p.surn)}"><span class=id>${esc(p.id)}</span>
    <span>${esc(p.name)}</span>
    <span class=neb>${esc(p.leben)}${p.ehe?' · '+esc(p.ehe):''}</span></div>`).join('');
 }
 if(d.namen.length){
  html+='<div class=kopfz>Nur Namensform</div>';
  html+=d.namen.map(n=>`<div data-typ=name data-name="${esc(n.name)}">
    <span>${esc(n.name)}</span>
    <span class=neb>${n.anzahl}×${n.kanonisch&&n.kanonisch!==n.name
      ?' · Klasse '+esc(n.kanonisch)+' ('+n.klasse+')':''}</span></div>`).join('');
 }
 box.innerHTML=html;
 box.querySelectorAll('div[data-typ]').forEach(el=>
   el.addEventListener('mousedown',ev=>{ev.preventDefault();waehle(inp,el)}));
 inp.closest('.feldbox').appendChild(box);
}
function waehle(inp,el){
 inp.value=el.dataset.name||inp.value;
 inp.classList.add('geaendert');
 const p=inp.closest('.person');
 if(p){
  if(el.dataset.typ==='person'){
   p.dataset.person=el.dataset.id; p.dataset.entscheidung='verknuepft';
   const b=p.querySelector('.knopf button'); b.disabled=false;
   setze(b,'verknuepft');
   p.querySelector('.treffer,.neu').outerHTML=
    `<span class=treffer><span class=id>${el.dataset.id}</span>
      <span class=warum>von Hand zugeordnet</span></span>`;
  }
  anbindung(p.closest('.eintrag'));
 }
 schliesse(inp);
}
function navVorschlag(ev,inp){
 const b=inp.closest('.feldbox').querySelector('.vorschlag');
 if(!b)return;
 const opt=[...b.querySelectorAll('div[data-typ]')];
 let i=opt.findIndex(o=>o.classList.contains('an'));
 if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){
  ev.preventDefault();
  if(i>=0)opt[i].classList.remove('an');
  i=ev.key==='ArrowDown'?(i+1)%opt.length:(i<=0?opt.length-1:i-1);
  opt[i].classList.add('an'); opt[i].scrollIntoView({block:'nearest'});
 } else if(ev.key==='Enter'&&i>=0){ ev.preventDefault(); ev.stopPropagation();
  waehle(inp,opt[i]);
 } else if(ev.key==='Escape'){ schliesse(inp) }
}

document.addEventListener('keydown',ev=>{
 const inp = ev.target.tagName==='INPUT';
 const vorschlagOffen = inp && ev.target.closest('.feldbox')?.querySelector('.vorschlag');
 const el = ev.target.closest?.('.eintrag') || document.querySelector('.eintrag');

 // Strg+Enter: Eintrag fertig – gilt immer.
 if(ev.key==='Enter' && ev.ctrlKey && el){
  ev.preventDefault(); fertig(+el.dataset.i); return; }

 // Solange eine Vorschlagsliste offen ist, gehört die Tastatur ihr.
 if(vorschlagOffen) return;

 if(inp){
  // Enter im Feld: den grün vorgeschlagenen Treffer übernehmen, sonst
  // ins nächste Feld. Ein Tastendruck je Entscheidung.
  if(ev.key==='Enter'){
   ev.preventDefault();
   const p=ev.target.closest('.person');
   const b=p?.querySelector('.knopf button:not([disabled])');
   if(p && b && !p.dataset.entscheidung){ setze(b,'verknuepft'); }
   const alle=[...el.querySelectorAll('.person.frage input, .daten input')];
   const k=alle.indexOf(ev.target);
   if(k>=0 && k+1<alle.length) alle[k+1].focus(); else fertig(+el.dataset.i);
   return;
  }
  if(ev.altKey && (ev.key==='n'||ev.key==='N')){
   const p=ev.target.closest('.person');
   if(p){ev.preventDefault();
    setze(p.querySelector('.knopf button:last-child'),'neu');}
   return;
  }
  return;   // sonst tippt der Mensch, und das lassen wir ihn
 }

 // Außerhalb eines Feldes: blättern und entscheiden mit einer Taste.
 if(liste) return;
 if(ev.key==='ArrowDown'||ev.key==='j'){ ev.preventDefault(); blaettern(1); }
 else if(ev.key==='ArrowUp'||ev.key==='k'){ ev.preventDefault(); blaettern(-1); }
 else if(ev.key==='Enter'){ ev.preventDefault(); if(el) fertig(+el.dataset.i); }
 else if(ev.key==='n'||ev.key==='N'){
  const p=document.querySelector('.person.frage');
  if(p){ev.preventDefault(); setze(p.querySelector('.knopf button:last-child'),'neu');}
 }
});

laden();
</script></body></html>"""
