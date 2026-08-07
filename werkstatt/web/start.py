"""HTML des Startbildschirms, der Leseseite und der Übergabe.

Eine Datei, drei Ansichten — welche gezeigt wird, entscheidet der Pfad.
Ausgelagert, damit app.py lesbar bleibt.
"""

STARTSEITE = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>OFB-Werkstatt</title><style>
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 system-ui,sans-serif;background:#14161a;color:#e6e8ec}
header{position:sticky;top:0;background:#1b1e24;border-bottom:1px solid #2c313a;
 padding:.55rem 1rem;display:flex;gap:1rem;align-items:center;z-index:9}
header b{font-size:1rem}
.logo{display:flex;align-items:center;gap:.45rem;color:#e6e8ec}
.logo svg{flex:none;color:#9aa3b2}
.spruch{font-style:normal;font-size:.76rem;color:#6f7887;letter-spacing:.02em;
 border-left:1px solid #2c313a;padding-left:.5rem;margin-left:.15rem}
@media(max-width:820px){.spruch{display:none}}
header a{color:#9aa3b2;text-decoration:none;font-size:.88rem;padding:.2rem .5rem;
 border-radius:6px}
header a:hover{background:#262b33;color:#e6e8ec}
header a.an{background:#2f6fdd;color:#fff}
main{padding:1.2rem;max-width:1100px;margin:0 auto}
h2{font-size:1.05rem;margin:1.6rem 0 .6rem;color:#c3c9d4;font-weight:600}
h2:first-child{margin-top:0}
.karte{background:#1b1e24;border:1px solid #2c313a;border-radius:10px;
 padding:.9rem 1.1rem;margin-bottom:.9rem}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th{text-align:left;color:#8b93a3;font-weight:500;font-size:.78rem;
 text-transform:uppercase;letter-spacing:.04em;padding:.3rem .5rem;
 border-bottom:1px solid #2c313a}
td{padding:.42rem .5rem;border-bottom:1px solid #23272f}
tr:last-child td{border-bottom:0}
td.z{text-align:right;font-variant-numeric:tabular-nums}
.dim{color:#8b93a3}
.gross{font-size:1.5rem;font-weight:600}
button{background:#333a45;color:#e6e8ec;border:0;border-radius:7px;
 padding:.45rem .9rem;font:inherit;cursor:pointer}
button.ja{background:#2f6fdd;color:#fff;font-weight:600}
button:disabled{opacity:.4;cursor:not-allowed}
button:hover:not(:disabled){filter:brightness(1.15)}
select,input[type=number]{background:#12141a;border:1px solid #333a45;color:#e6e8ec;
 border-radius:6px;padding:.35rem .5rem;font:inherit}
.reihe{display:flex;gap:.7rem;align-items:center;flex-wrap:wrap}
.schritt{background:linear-gradient(180deg,#1e2836,#1b1e24);
 border:1px solid #2f4260;border-radius:10px;padding:1.1rem;margin-bottom:1.2rem}
.schritt .was{font-size:1.15rem;font-weight:600;margin-bottom:.15rem}
.schritt .warum{color:#9aa3b2;font-size:.88rem;margin-bottom:.8rem}
.marke{display:inline-block;font-size:.72rem;padding:.1rem .45rem;border-radius:4px;
 text-transform:uppercase;letter-spacing:.04em}
.beleg{background:#1d4231;color:#8fe3b4}
.vokabular{background:#3a3320;color:#e0c98a}
.ampel{display:inline-flex;gap:.15rem;align-items:center}
.pkt{width:.62rem;height:.62rem;border-radius:50%;display:inline-block}
.gruen{background:#3ecf8e}.gelb{background:#e0b341}.rot{background:#e06c5f}
.grau{background:#4a515c}
.balken{height:.5rem;background:#262b33;border-radius:99px;overflow:hidden;
 margin:.5rem 0}
.balken i{display:block;height:100%;background:#2f6fdd;transition:width .3s}
.seiten{font-size:.85rem;margin-top:.6rem}
.seiten div{display:flex;gap:.6rem;padding:.16rem 0;align-items:center}
.seiten .st{width:5.2rem;font-size:.76rem;text-transform:uppercase;
 letter-spacing:.04em;color:#8b93a3}
.seiten .fertig .st{color:#8fe3b4}
.seiten .fehler .st{color:#e06c5f}
.seiten .laeuft .st{color:#7fb0ff}
.warn{background:#2c2113;border:1px solid #4a3a13;color:#f0d089;
 border-radius:8px;padding:.6rem .9rem;font-size:.88rem;margin-bottom:.9rem}
.leer{padding:2.5rem;text-align:center;color:#9aa3b2}
code{font-family:ui-monospace,monospace;font-size:.86em;background:#12141a;
 padding:.08rem .35rem;border-radius:4px}
.chip{display:inline-flex;gap:.3rem;align-items:center;background:#262b33;
 border:1px solid #333a45;border-radius:99px;padding:.15rem .5rem;font-size:.9rem}
.chip button{padding:0 .25rem;background:transparent;font-size:.9rem;line-height:1}
input{background:#12141a;border:1px solid #333a45;color:#e6e8ec;border-radius:6px;
 padding:.35rem .5rem;font:inherit}
label input[type=radio]{margin-right:.4rem}
</style></head><body>
<header><span class=logo title="Was grün ist, ist belegt.">
 <svg viewBox="0 0 24 24" width=22 height=22 aria-hidden=true>
  <!-- Die aufgeschlagene Doppelseite: links das Kirchenbuch mit seinen
       Zeilen, rechts der Bestand. Der grüne Punkt sitzt auf der Naht —
       da entsteht der Beleg. -->
  <path d="M2 5.4c3.1-1.1 6-1.1 9 .3v13c-3-1.4-5.9-1.4-9-.3z"
        fill=none stroke=currentColor stroke-width=1.4 stroke-linejoin=round/>
  <path d="M22 5.4c-3.1-1.1-6-1.1-9 .3v13c3-1.4 5.9-1.4 9-.3z"
        fill=none stroke=currentColor stroke-width=1.4 stroke-linejoin=round/>
  <path d="M4.4 8.6h4.2M4.4 11.2h4.2M4.4 13.8h2.8" stroke=currentColor
        stroke-width=1.1 stroke-linecap=round opacity=.55/>
  <circle cx=12 cy=12 r=2.5 fill=#3ecf8e/>
 </svg>
 <b>OFB-Werkstatt</b><i class=spruch>Was grün ist, ist belegt.</i></span>
 <a href="/" data-p="/">Stand</a>
 <a href="/lesen" data-p="/lesen">Lesen</a>
 <a href="/korrektur" data-p="/korrektur">Korrigieren</a>
 <a href="/uebergabe" data-p="/uebergabe">Übergeben</a>
 <a href="/ausgabe" data-p="/ausgabe">Ausgeben</a>
 <a href="/formular" data-p="/formular" title="Aktkarten und Formularperioden">Formular</a>
 <span style=flex:1></span><span class=dim id=gem></span>
 <a href="/einstellungen" data-p="/einstellungen" title="Einstellungen">⚙</a>
 <a href="#" onclick="beenden();return false" title="Werkstatt beenden"
    style="font-size:1.05rem">⏻</a></header>
<main id=app class=leer>lade…</main>
<script>
const esc=s=>(s??'').toString().replace(/[&<>"]/g,c=>
 ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const P=location.pathname;
let S=null, ticker=null;

document.querySelectorAll('header a').forEach(a=>
 a.classList.toggle('an', a.dataset.p===P));

async function beenden(){
 if(!confirm('Werkstatt beenden?\n\nDer Server hört auf zu laufen; '
  +'nichts geht verloren. Zum Weiterarbeiten das Startskript erneut '
  +'aufrufen.')) return;
 try{ await fetch('/api/beenden',{method:'POST'}); }catch(e){}
 document.body.innerHTML='<main class=leer style="padding:4rem">'
  +'<div style="font-size:1.2rem;margin-bottom:.6rem">Werkstatt beendet.</div>'
  +'<div class=dim>Dieses Fenster kann zu. Zum Weiterarbeiten das '
  +'Startskript erneut aufrufen.</div></main>';
}

async function laden(){
 S=await (await fetch('/api/stand')).json();
 document.getElementById('gem').textContent=S.gemeinde;
 const m=sessionStorage.getItem('meldung');
 if(m){sessionStorage.removeItem('meldung');
  const d=document.createElement('div'); d.className='warn';
  d.style.background='#13291d'; d.style.borderColor='#1d4231';
  d.style.color='#8fe3b4'; d.textContent=m;
  document.getElementById('app').before(d);
  setTimeout(()=>d.remove(),12000);}
 const app=document.getElementById('app');
 app.className='';
 app.innerHTML = P==='/lesen' ? ansichtLesen()
               : P==='/uebergabe' ? ansichtUebergabe()
               : P==='/ausgabe' ? ansichtAusgabe()
               : P==='/einstellungen' || P==='/formular'
                 ? '<div class=leer>lade…</div>'
               : ansichtStand();
 if(P==='/lesen' && S.runde &&
    (S.runde.stand==='liest' ||
     (S.runde.quelle==='datei' && S.vorlage && S.vorlage.fertig<S.vorlage.gesamt)))
  takt();
 if(P==='/lesen' && !S.runde && document.getElementById('reg')){
  document.getElementById('reg').onchange=quelleGewaehlt; quelleGewaehlt();}
}

// ----------------------------------------------------------- Einrichtung
function ansichtEinrichtung(){
 return `
 <div class=schritt>
  <div class=was>Willkommen in der Werkstatt</div>
  <div class=warum>Drei Angaben, dann kann es losgehen. Alles davon lässt
   sich später im Zahnrad ändern.</div>

  <div style="margin:.9rem 0 .3rem"><b>Wie heißt die Gemeinde?</b></div>
  <div class=dim style="font-size:.86rem;margin-bottom:.4rem">
   Der Name der Pfarrei, deren Kirchenbücher Sie bearbeiten. Er steht später
   als Ortsangabe in jedem Eintrag.</div>
  <input id=egem placeholder="z. B. Musterhausen" style="width:22rem"
    onkeydown="if(event.key==='Enter')einrichten(this)">

  <div style="margin:1.2rem 0 .3rem"><b>Welche Register, und wo liegen die
   Scans?</b></div>
  <div class=dim style="font-size:.86rem;margin-bottom:.5rem">
   Ankreuzen, was Sie bearbeiten wollen; die Ordner werden angelegt. Ein
   Register ohne Bilder wird nie vorgeschlagen, also stört es auch nicht,
   wenn Sie eines zu viel ankreuzen. Ein Pfad ohne <code>/</code> am Anfang
   gilt vom Projektordner aus, <code>~</code> ist Ihr Benutzerordner.</div>
  ${S.einrichtung.map((r,i)=>`<div class=reihe style="margin-bottom:.4rem">
    <label style="width:11rem;cursor:pointer">
     <input type=checkbox class=ereg data-art="${esc(r.art)}"
       ${i<3?'checked':''}> ${esc(r.titel)}</label>
    <input class=eord data-art="${esc(r.art)}" value="${esc(r.ordner)}"
      style="flex:1;min-width:14rem">
   </div>`).join('')}

  <div class=reihe style="margin-top:1.1rem">
   <button class=ja onclick=einrichten(this)>Projekt anlegen</button>
   <span class=dim id=ehinweis>Geschrieben wird eine Datei
    <code>konfig.local.toml</code> im Projektordner. Sonst nichts.</span>
  </div>
 </div>

 <div class=karte>
  <div style="font-weight:600;margin-bottom:.3rem">Eine zweite Pfarrei?</div>
  <p class=dim style="font-size:.88rem;margin:0">
   Ein Projekt ist ein Ordner. Für eine weitere Pfarrei packen Sie die
   Werkstatt ein zweites Mal aus — eigene Datenbank, eigene Bilder, eigene
   Einstellungen. Das hält zwei Bestände sauber getrennt: nichts kann
   versehentlich vom einen in den anderen wandern.</p>
 </div>`;
}

async function einrichten(btn){
 const h=document.getElementById('ehinweis');
 const gem=document.getElementById('egem').value.trim();
 if(!gem){h.textContent='Erst den Namen der Gemeinde eintragen.';return;}
 const reg=[...document.querySelectorAll('.ereg')].filter(c=>c.checked)
   .map(c=>({art:c.dataset.art,
     ordner:(document.querySelector(`.eord[data-art="${c.dataset.art}"]`)||{}).value}));
 if(!reg.length){h.textContent='Mindestens ein Register ankreuzen.';return;}
 btn.disabled=true; h.textContent='lege an …';
 const a=await (await fetch('/api/einrichten',{method:'POST',
   body:JSON.stringify({gemeinde:gem, register:reg})})).json();
 if(a.fehler){btn.disabled=false; h.textContent=a.fehler; return;}
 location.href='/';
}

// ---------------------------------------------------------------- Stand
function ansichtStand(){
 if(!S.eingerichtet) return ansichtEinrichtung();
 const b=S.bestand;
 return `
 ${schrittKarte()}
 <h2>Register</h2>
 <div class=karte><table>
  <tr><th>Register</th><th class=z>Bilder</th><th class=z>gelesen</th>
      <th class=z>Einträge</th><th class=z>bestätigt</th><th>Ordner</th></tr>
  ${S.register.map(r=>`<tr>
    <td>${esc(r.titel)}</td>
    <td class=z>${r.bilder}</td>
    <td class="z ${r.gelesen?'':'dim'}">${r.gelesen}</td>
    <td class="z ${r.eintraege?'':'dim'}">${r.eintraege}</td>
    <td class="z ${r.bestaetigt?'':'dim'}">${r.bestaetigt}</td>
    <td class=dim><code>${esc(r.ordner)}</code></td></tr>`).join('')}
 </table></div>

 <h2>Kontextquellen — was darf bestätigen</h2>
 ${S.quellen.some(q=>q.gilt==='beleg')?'':`<div class=warn>
   Keine Quelle darf bestätigen. Das ist der <b>Nullstart</b>: Der Abgleich
   findet nichts, jedes Feld bleibt gelb und wird vorgelegt. Nicht falsch,
   nur langsam. Quellen samt Rang trägt man in <code>konfig.toml</code>
   unter <code>[[kontext]]</code> ein.</div>`}
 <div class=karte><table>
  <tr><th>Quelle</th><th>Rang</th><th>Parochien</th><th class=z>Personen</th></tr>
  ${S.quellen.map(q=>`<tr>
    <td>${esc(q.name||q.datei||q.art)}</td>
    <td><span class="marke ${q.gilt}">${q.gilt==='beleg'
       ?'darf bestätigen':'rankt nur'}</span></td>
    <td class=dim>${esc(q.parochien||'—')}</td>
    <td class="z ${q.n?'':'dim'}">${q.n}</td></tr>`).join('')}
 </table></div>
 <p class=dim style="font-size:.86rem">
  Ein Treffer macht grün, wenn die Herkunft des getroffenen Datensatzes
  <b>beleg</b> ist. Vokabular rankt die Vorschlagsliste und bestätigt nie —
  <code>Roth</code> kommt 59-mal im Bestand vor und stand doch für
  <code>Koch</code>.</p>

 ${(S.quellen_fehlend||[]).length?`<div class=warn>
   <b>Eingetragen, aber nicht eingelesen.</b> Diese Quellen stehen in
   <code>konfig.toml</code> und liegen nicht in der Datenbank — sie wirken
   also nicht:
   <ul style="margin:.4rem 0 0 1.1rem;padding:0">
    ${S.quellen_fehlend.map(q=>`<li>${esc(q.name)}
      <code>${esc(q.datei)}</code> — ${q.liest_wer
       ? `einlesen mit <code>python3 -m werkstatt.${esc(q.liest_wer)} --aus-konfig</code>`
       : `Format <b>${esc(q.art)}</b> kennt kein Einleser. Für Wortlisten
          <code>art = "wortschatz"</code> setzen`}</li>`).join('')}
   </ul></div>`:''}

 <p class=dim style="font-size:.86rem">
  <b>Zwei Arten, fremde Arbeit einzubinden.</b>
  <code>art = "gedcom"</code> bringt einen ganzen Bestand mit Personen,
  Familien und Daten — das Einzige, was <i>bestätigen</i> darf.
  <code>art = "wortschatz"</code> nimmt alles, was Schreibweisen kennt, aber
  keine Lebensdaten hat: Namenslisten, Ortsverzeichnisse, abgetippte
  Register, in <code>.csv .tsv .txt .xlsx .ods .docx</code> oder als ganzer
  Ordner. Die Spalten erkennt der Einleser an der Kopfzeile; wo das nicht
  reicht, ordnet man sie in <code>konfig.toml</code> zu. Solche Quellen
  bleiben immer <code>vokabular</code> — ohne Daten lässt sich ein Treffer
  nicht prüfen.</p>

 <h2>Bestand</h2>
 <div class=karte><div class=reihe>
  ${[['Personen',b.person],['Familien',b.familie],['Ereignisse',b.ereignis],
     ['Einträge',b.eintrag],['Felder',b.feld]].map(([k,v])=>
   `<div style="min-width:8rem"><div class=gross>${v}</div>
     <div class=dim style="font-size:.82rem">${k}</div></div>`).join('')}
 </div></div>`;
}

function schrittKarte(){
 const r=S.runde, v=S.vorschlag;
 if(!r) return `<div class=schritt>
   <div class=was>Runde ${v.register?'beginnen':'—'}</div>
   <div class=warum>${v.register
     ?`Als Nächstes: <b>${esc(v.register)}</b> — ${esc(v.grund)}`
     :esc(v.grund)}</div>
   ${v.register?`<a href="/lesen"><button class=ja>Weiter zum Lesen</button></a>`:''}
  </div>`;
 const a=S.offen?S.offen.ampel:{};
 const ziel={liest:'/lesen',korrigieren:'/korrektur',uebergeben:'/uebergabe'}[r.stand]||'/lesen';
 const text={liest:'Wird gelesen',korrigieren:'Korrigieren',
             uebergeben:'Übergeben',geplant:'Lesen starten'}[r.stand]||r.stand;
 return `<div class=schritt>
  <div class=was>Runde ${r.nr} · ${esc(r.register)} · ${r.seiten} Seiten</div>
  <div class=warum>${esc(r.von_bild)} – ${esc(r.bis_bild)} ·
   Quelle ${esc(r.quelle)} · Stand <b>${esc(r.stand)}</b>
   ${S.offen?` · ${S.offen.bestaetigt}/${S.offen.eintraege} Einträge bestätigt`:''}</div>
  ${S.offen?`<div class=reihe style="margin-bottom:.7rem">${ampelReihe(a)}</div>`:''}
  <a href="${ziel}"><button class=ja>${text}</button></a>
 </div>`;
}
function ampelReihe(a){
 return ['gruen','gelb','rot','grau'].map(k=>a[k]
  ?`<span class=ampel><i class="pkt ${k}"></i> ${a[k]}</span>`:'').join(' ');
}

// ---------------------------------------------------------------- Lesen
function dublettenKarte(){
 const d=(S.dubletten||[]);
 const offen=d.filter(x=>x.stand==='verdacht');
 const weg=d.filter(x=>x.stand==='dublette');
 if(!d.length) return `
 <div class=karte>
  <div class=reihe>
   <button onclick=dublettenPruefen(this)>Auf doppelte Aufnahmen prüfen</button>
   <span class=dim style="font-size:.86rem;flex:1">Archion- und
    Ancestry-Bände enthalten oft zwei Aufnahmen derselben Buchöffnung. Wer
    sie beide liest, zahlt zweimal und bekommt jeden Eintrag doppelt.</span>
  </div>
  <div id=dubhinweis class=dim style="margin-top:.5rem;font-size:.86rem"></div>
 </div>`;
 return `
 ${offen.length?`<div class=warn>
   <b>${offen.length} verdächtige Aufnahme${offen.length>1?'n':''}.</b>
   Deutlich ähnlicher als der Rest der Strecke — vermutlich dieselbe
   Buchöffnung zweimal. Bitte einmal ansehen und entscheiden.
   <table style="margin-top:.5rem">
    ${offen.map(x=>`<tr>
      <td><code>${esc(x.bild)}</code> gleicht <code>${esc(x.gleich_wie)}</code></td>
      <td class=z title="Abstand gegen Median der Nachbarpaare">
        ${x.abstand} von ${Math.round(x.median)}</td>
      <td class=z>
        <button onclick="dublettenUrteil('${esc(x.bild)}',true,this)">Dublette</button>
        <button onclick="dublettenUrteil('${esc(x.bild)}',false,this)">eigene Seite</button>
      </td></tr>`).join('')}
   </table></div>`:''}
 ${weg.length?`<p class=dim style="font-size:.86rem">
   ${weg.length} Aufnahme${weg.length>1?'n werden':' wird'} übersprungen:
   ${weg.map(x=>`<code>${esc(x.bild)}</code>`).join(' ')}</p>`:''}`;
}

async function dublettenPruefen(btn){
 const h=document.getElementById('dubhinweis');
 btn.disabled=true; h.textContent='messe die Strecke …';
 const reg=(S.vorschlag&&S.vorschlag.register)||S.register[0].register;
 const a=await (await fetch('/api/dubletten',{method:'POST',
   body:JSON.stringify({register:reg})})).json();
 S=await (await fetch('/api/stand')).json();
 document.getElementById('app').innerHTML=ansichtLesen();
 const h2=document.getElementById('dubhinweis');
 if(h2) h2.textContent=`${a.bilder} Bilder geprüft, `
   +(a.verdacht.length?`${a.verdacht.length} verdächtig.`:'keine Dublette.');
}

async function dublettenUrteil(bild,ist,btn){
 btn.disabled=true;
 await fetch('/api/dubletten',{method:'POST',
   body:JSON.stringify({bild, dublette:ist})});
 S=await (await fetch('/api/stand')).json();
 document.getElementById('app').innerHTML=ansichtLesen();
}

function ansichtLesen(){
 const r=S.runde;
 if(r && r.quelle==='datei' && S.vorlage) return vorlageKarte();
 if(r && r.stand!=='geplant' && r.stand!=='liest')
  return `<div class=schritt><div class=was>Runde ${r.nr} ist gelesen</div>
   <div class=warum>Stand <b>${esc(r.stand)}</b> — weiter in der Korrekturmaske.</div>
   <a href="/korrektur"><button class=ja>Korrigieren</button></a></div>`;
 if(r) return fortschrittKarte();
 const v=S.vorschlag;
 const arten=S.register.map(x=>`<option value="${esc(x.register)}"
   data-test="${x.offen_test}" data-api="${x.offen_api}"
   ${x.register===v.register?'selected':''}>${esc(x.titel)}
   — ${x.offen_api} Seiten offen${x.offen_test?`, davon ${x.offen_test} als Testdaten`:''}</option>`).join('');
 return `${dublettenKarte()}
 <div class=schritt>
  <div class=was>Tranche planen</div>
  <div class=warum>${esc(v.grund)}. Die Reihenfolge Ehen → Taufen → Tode ist
   keine Empfehlung: Der Elternehe-Anker trägt im Taufjahr 1808 noch 94 %,
   1820 nur 18 % — es sei denn, die Ehen sind vorher übergeben.</div>
  <div class=reihe>
   <label class=dim>Register</label><select id=reg>${arten}</select>
   <label class=dim>Seiten</label>
   <input type=number id=anz value="${S.testdaten?4:20}" min=1 max=200 style=width:5rem>
   <label class=dim>Quelle</label>
   <select id=q onchange=quelleGewaehlt()>
    ${S.claude_code
      ?`<option value=datei>Claude Code — über Ihr Abo, kein API-Schlüssel</option>`:''}
    <option value=api>API — braucht ANTHROPIC_API_KEY</option>
    ${S.register.some(x=>x.offen_test)
      ?`<option value=testdaten>Testdaten — zum Ausprobieren, kostet nichts</option>`:''}
   </select>
   <button class=ja onclick=starten()>Lesen starten</button>
  </div>
  <div id=hinweis class=dim style="margin-top:.5rem;font-size:.86rem"></div>
  <div id=fehler class=dim style="margin-top:.6rem"></div>
 </div>
 <p class=dim style="font-size:.86rem">Der Läufer arbeitet im Hintergrund
  weiter, auch wenn dieses Fenster zugeht. Fehler gelten je Seite, nicht je
  Lauf — bricht Seite 7 ab, laufen 8 bis 20 trotzdem durch.</p>`;
}

function fortschrittKarte(){
 const f=S.fortschritt||{}, r=S.runde;
 if(r.quelle==='datei' && S.vorlage) return vorlageKarte();
 const p=f.seiten_gesamt?Math.round(100*f.seiten_fertig/f.seiten_gesamt):0;
 return `<div class=schritt>
  <div class=was>Runde ${r.nr} · ${esc(r.register)} wird gelesen</div>
  <div class=warum>${f.seiten_fertig||0} von ${f.seiten_gesamt||0} Seiten
   ${f.aktuell?`· gerade <b>${esc(f.aktuell)}</b>`:''}
   ${f.tokens_ein?`· ${f.tokens_ein} Token hinein, ${f.tokens_aus} heraus`:''}</div>
  <div class=balken><i style="width:${p}%"></i></div>
  <div class=seiten>${(f.seiten||[]).map(s=>`<div class="${esc(s.stand)}">
    <span class=st>${esc(s.stand)}</span><span>${esc(s.bild)}</span>
    <span class=dim>${s.eintraege?s.eintraege+' Einträge':''}</span>
    <span class=dim>${esc(s.meldung||'')}</span></div>`).join('')}</div>
  ${f.stand==='fertig'||f.stand==='fehler'
    ?`<div style="margin-top:.9rem">
       <a href="/korrektur"><button class=ja>Weiter zum Korrigieren</button></a></div>`:''}
 </div>`;
}

function quelleGewaehlt(){
 const reg=document.getElementById('reg');
 const o=reg.options[reg.selectedIndex];
 const q=document.getElementById('q').value;
 const rest=+(q==='testdaten'?o.dataset.test:o.dataset.api);
 const anz=document.getElementById('anz');
 anz.max=Math.max(1,rest);
 if(+anz.value>rest) anz.value=Math.max(1,rest);
 document.getElementById('hinweis').textContent = rest
  ? `${rest} Seite(n) verfügbar aus dieser Quelle.`
  : (q==='testdaten'
     ? 'Die Testquelle deckt dieses Register nicht ab — dafür braucht es die API.'
     : 'Keine ungelesenen Bilder in diesem Register.');
 document.querySelector('#app button.ja').disabled = !rest;
}

function vorlageKarte(){
 const r=S.runde, v=S.vorlage, f=S.fortschritt||{};
 const p=v.gesamt?Math.round(100*v.fertig/v.gesamt):0;
 return `<div class=schritt>
  <div class=was>Runde ${r.nr} · ${esc(r.register)} · über Claude Code</div>
  <div class=warum>${v.fertig} von ${v.gesamt} Seiten beantwortet.
   Das Lesen läuft über Ihr Abonnement — kein API-Schlüssel, keine zweite
   Rechnung. Die Werkstatt hält dabei keine Anmeldedaten.</div>
  <div class=balken><i style="width:${p}%"></i></div>
  <div class=seiten>${v.seiten.map(s=>`<div class="${s.da?'fertig':''}">
    <span class=st>${s.da?'gelesen':'offen'}</span><span>${esc(s.bild)}</span>
    <span class=dim>${s.eintraege>0?s.eintraege+' Einträge'
      :s.eintraege<0?'⚠ Antwort unlesbar':''}</span></div>`).join('')}</div>
  <div class=reihe style="margin-top:.9rem">
   ${v.fertig<v.gesamt
     ?`<button class=ja onclick=lesenLassen()>Lesen lassen</button>
       <button onclick=einlesen()>Antworten einlesen</button>`
     :`<a href="/korrektur"><button class=ja>Weiter zum Korrigieren</button></a>`}
   <span class=dim>Ordner <code>${esc(v.ordner)}</code></span>
  </div>
  <p class=dim style="font-size:.86rem;margin:.7rem 0 0">
   <b>Lesen lassen</b> startet eine Claude-Code-Sitzung im Rundenordner, die
   die Seiten liest und die Antworten schreibt. Das kann je Seite eine Minute
   dauern; das Fenster darf zugehen. <b>Antworten einlesen</b> nimmt auf, was
   schon dasteht — auch wenn Sie selbst in einer eigenen Sitzung gelesen
   haben.</p>
  <div id=meldung class=dim style="margin-top:.6rem"></div>
 </div>`;
}

async function lesenLassen(){
 document.getElementById('meldung').textContent='Sitzung läuft — das dauert.';
 await fetch('/api/lesen-lassen',{method:'POST',
  headers:{'content-type':'application/json'},
  body:JSON.stringify({runde:S.runde.id})});
 takt();
}
async function einlesen(){
 document.getElementById('meldung').textContent='wird eingelesen…';
 await fetch('/api/einlesen',{method:'POST',
  headers:{'content-type':'application/json'},
  body:JSON.stringify({runde:S.runde.id})});
 setTimeout(laden, 1500);
}

async function starten(){
 const d={register:document.getElementById('reg').value,
          seiten:+document.getElementById('anz').value,
          quelle:document.getElementById('q').value};
 const r=await fetch('/api/runde/plane',{method:'POST',
   headers:{'content-type':'application/json'},body:JSON.stringify(d)});
 const j=await r.json();
 if(j.fehler){document.getElementById('fehler').textContent='⚠ '+j.fehler;return}
 laden();
}
function takt(){
 clearInterval(ticker);
 ticker=setInterval(async()=>{
  S=await (await fetch('/api/stand')).json();
  const el=document.getElementById('app');
  el.innerHTML=ansichtLesen();
  const weiter = S.runde && (S.runde.stand==='liest' ||
    (S.runde.quelle==='datei' && S.vorlage && S.vorlage.fertig<S.vorlage.gesamt));
  if(!weiter) clearInterval(ticker);
 },1000);
}

// ------------------------------------------------------------- Übergabe
function ansichtUebergabe(){
 const r=S.runde;
 if(!r) return `<div class=leer>Keine offene Runde.</div>`;
 const o=S.offen||{ampel:{}};
 const rest=o.eintraege-o.bestaetigt;
 return `<div class=schritt>
  <div class=was>Runde ${r.nr} übergeben</div>
  <div class=warum>Bestätigte Einträge werden zu Personen und Familien.
   Erst danach kann die nächste Tranche gegen sie ankern — das ist der
   Mechanismus „die ersten hundert tragen die nächsten tausend".</div>
  <div class=reihe style="margin-bottom:.8rem">
   <div><div class=gross>${o.bestaetigt}</div>
    <div class=dim style="font-size:.82rem">bestätigt</div></div>
   <div><div class=gross>${rest}</div>
    <div class=dim style="font-size:.82rem">noch offen</div></div>
   <div style="margin-left:1rem">${ampelReihe(o.ampel)}</div>
  </div>
  ${rest>0?`<div class=warn>${rest} Eintrag/Einträge sind noch nicht bestätigt.
    Sie bleiben zurück — was niemand geprüft hat, wird nicht zum Anker für
    die nächste Tranche, sonst verfestigen sich Lesefehler stillschweigend.
    <a href="/korrektur" style=color:inherit>Jetzt korrigieren</a></div>`:''}
  <div id=probe class=dim>Probelauf wird geholt…</div>
  <div style="margin-top:.9rem">
   <button class=ja id=knopf disabled onclick=uebergeben()>Übernehmen</button>
   <span class=dim style="margin-left:.6rem">schreibt in den Bestand</span></div>
 </div>`;
}

async function probeHolen(){
 if(P!=='/uebergabe'||!S.runde) return;
 const d=await (await fetch('/api/uebergabe?runde='+S.runde.id)).json();
 const z=d.probe||{};
 const el=document.getElementById('probe'); if(!el) return;
 if(z.uebersprungen){el.textContent='⚠ '+z.uebersprungen;return}
 const zeilen=[['Einträge','eintraege'],['Personen neu','personen_neu'],
   ['Personen verknüpft','personen_verknuepft'],['Familien','familien'],
   ['Kinder eingehängt','kinder'],['Ereignisse','ereignisse']];
 el.innerHTML='<b style=color:#e6e8ec>Was entsteht</b><table style=margin-top:.4rem>'
  +zeilen.map(([k,v])=>`<tr><td>${k}</td><td class=z>${z[v]||0}</td></tr>`).join('')
  +'</table>';
 const k=document.getElementById('knopf');
 if(k) k.disabled = !(z.eintraege>0);
}

async function uebergeben(){
 const r=await fetch('/api/runde/uebergib',{method:'POST',
  headers:{'content-type':'application/json'},
  body:JSON.stringify({runde:S.runde.id})});
 const j=await r.json();
 if(!j.ok){alert('Übergabe fehlgeschlagen');return}
 // Die Arbeitskopie ist der eigentliche Ertrag der Runde — sie zu
 // erwähnen, gehört zur Übergabe, nicht in ein Protokoll.
 const z=j.zahlen||{};
 if(z.arbeitskopie_fehler)
  alert('Übergeben — aber die Arbeitskopie ließ sich nicht schreiben:\n'
        +z.arbeitskopie_fehler);
 else if(z.arbeitskopie)
  sessionStorage.setItem('meldung','Übergeben. Arbeitskopie neu geschrieben: '
        +z.arbeitskopie);
 location.href='/';
}

// -------------------------------------------------------------- Ausgabe
function ansichtAusgabe(){
 return `<div class=schritt>
  <div class=was>GEDCOM ausgeben</div>
  <div class=warum>Der Weg nach draußen. Wird geladen…</div>
  <div id=aus></div>
 </div>`;
}

async function ausgabeHolen(){
 const d=await (await fetch('/api/ausgabe')).json();
 const el=document.getElementById('aus'); if(!el) return;
 const z=d.zahlen||{};
 const fort = d.art==='fort';
 const ampel = d.leerlauf===true ? ['gruen','✓']
             : d.leerlauf===false ? ['rot','✗'] : ['gelb','·'];
 el.innerHTML = `
  <div class=karte style="margin-bottom:.9rem">
   <b>${fort?'Fortschreibung':'Neuausgabe'}</b>
   <div class=dim style="font-size:.88rem;margin:.3rem 0 .6rem">
    ${fort
      ? `Die Vorlage <code>${esc(d.vorlage)}</code> läuft Record für Record
         durch. Unberührte Records gehen <b>zeichengleich</b> hindurch —
         Quellenangaben, Notizen, Ortsdefinitionen und Paten bleiben, wie sie
         sind. Nur was ein Vorgang anfasst, wird neu geschrieben.`
      : `Keine Vorlage vorhanden — alles wird aus den eigenen Tabellen
         geschrieben.`}
   </div>
   ${fort?`<div class=reihe style="margin-bottom:.6rem">
     <span class=ampel><i class="pkt ${ampel[0]}"></i>
      <b>Leerlauftest ${ampel[1]}</b></span>
     <span class=dim>${esc(d.leerlauf_text||'')}</span></div>
    <div class=dim style="font-size:.84rem;margin-bottom:.6rem">
     Der Test schreibt die Vorlage aus der Datenbank zurück und vergleicht
     Byte für Byte. Schlägt er fehl, ist beim Einlesen etwas verloren
     gegangen — und man sieht, an welcher Stelle.</div>`:''}
   <table>
    ${Object.entries(z).map(([k,v])=>
      `<tr><td>${esc(k.replace(/_/g,' '))}</td><td class=z>${v}</td></tr>`).join('')}
    <tr><td class=dim>Dateigröße</td>
        <td class="z dim">${(d.bytes/1024).toFixed(0)} kB</td></tr>
   </table>
  </div>
  <div class=reihe>
   <button class=ja onclick="schreiben('${fort?'fort':'neu'}')">
    ${fort?'Fortschreibung':'Neuausgabe'} schreiben</button>
   ${fort?`<button onclick="schreiben('neu')">stattdessen neu aufbauen</button>`:''}
   <span class=dim>nach <code>ausgabe/</code></span>
  </div>
  <div id=ergebnis style="margin-top:.7rem"></div>`;
}

async function schreiben(art){
 if(art==='neu' && !confirm(
   'Die Neuausgabe schreibt alles aus den eigenen Tabellen neu.\n\n'
  +'Was die Werkstatt nicht kennt, geht dabei verloren: Quellenangaben, '
  +'Notizen, Paten, Ortsdefinitionen, Bilder.\n\nTrotzdem fortfahren?')) return;
 const r=await fetch('/api/ausgabe',{method:'POST',
  headers:{'content-type':'application/json'},body:JSON.stringify({art})});
 const j=await r.json();
 const el=document.getElementById('ergebnis');
 el.innerHTML = j.ok
  ? `<span style=color:#8fe3b4>✓ geschrieben:</span>
     <code>${esc(j.datei)}</code> <span class=dim>${(j.bytes/1024).toFixed(0)} kB</span>`
  : `<span style=color:#e06c5f>✗ fehlgeschlagen</span>`;
}

// --------------------------------------------------------- Einstellungen
let E=null;
async function einstellungenHolen(){
 E=await (await fetch('/api/einstellungen')).json();
 document.getElementById('app').innerHTML =
   P==='/formular' ? ansichtFormular() : ansichtEinstellungen();
 quelleArt();
}

// ------------------------------------------------------------- Formular
// Aktkarten und Formularperioden sind keine Einstellungen — man schaut
// hin, wenn ein Feld fehlt oder das Buch das Formular wechselt. Deshalb
// eine eigene Seite statt zweier weiterer Abschnitte im Zahnrad, das
// zuletzt zehn davon hatte.
function ansichtFormular(){
 return `
 ${periodenKarte()}
 ${aktkarten()}`;
}

function anmeldeblock(c){
 if(c.angemeldet===null) return `<div class=warn>${esc(c.meldung||'')}
   <div class=reihe style="margin-top:.6rem">
    <button onclick=anmeldenStarten(this)>Trotzdem anmelden</button>
    <span class=dim id=anmeldetext>Falls das Lesen scheitert, ist die
     Anmeldung der erste Verdacht.</span></div></div>`;
 if(c.angemeldet) return `<div class=reihe style="margin-bottom:.6rem">
   <span class=ampel><i class="pkt gruen"></i>
   <b>Angemeldet${c.abo?' — '+esc(c.abo)+'-Abonnement':''}</b></span>
   <span class=dim>${esc(c.konto||'')} · ${esc(c.weg||'')}
    · Claude Code ${esc(c.version||'')}</span></div>`;
 if(!c.da) return `<div class=warn>${esc(c.meldung||'')}
   <div style="margin-top:.5rem">Claude Code zuerst installieren —
   <code>claude.com/download</code>, unter Windows das
   Installationsprogramm. Danach diese Seite neu laden; der Knopf zum
   Anmelden erscheint dann hier.</div></div>`;
 return `<div class=warn>${esc(c.meldung||'')}
   <div style="margin-top:.5rem">Einmal anmelden, dann nie wieder.</div>
   <div class=reihe style="margin-top:.6rem">
    <button class=ja onclick=anmeldenStarten(this)>Jetzt anmelden</button>
    <span class=dim id=anmeldetext>Es geht ein Fenster auf und schickt Sie
     in den Browser. Diese Seite merkt von selbst, wenn es geklappt hat.</span>
   </div></div>`;
}

let anmeldeTakt=null;

async function anmeldenStarten(btn){
 btn.disabled=true;
 const t=document.getElementById('anmeldetext');
 const a=await (await fetch('/api/anmelden',{method:'POST'})).json();
 if(!a.ok){
  btn.disabled=false;
  t.innerHTML=`${esc(a.meldung||'')} Bitte ein Terminal öffnen und
   <code>${esc(a.befehl||'claude auth login')}</code> eingeben.`;
  return;
 }
 t.textContent='Warte auf die Anmeldung im anderen Fenster …';
 let versuche=0;
 clearInterval(anmeldeTakt);
 anmeldeTakt=setInterval(async()=>{
  const c=await (await fetch('/api/anmeldestand')).json();
  if(c.angemeldet){
   clearInterval(anmeldeTakt);
   document.getElementById('anmeldung').innerHTML=anmeldeblock(c);
   E.ki.cli=c;
  }else if(++versuche>150){         // fünf Minuten
   clearInterval(anmeldeTakt);
   btn.disabled=false;
   t.textContent='Nichts angekommen. Noch einmal versuchen?';
  }
 },2000);
}

function quellenKarte(){
 const q=(S&&S.quellen)||[];
 return `
 <h2>Kontextquellen — was darf bestätigen</h2>
 <div class=karte>
  <table>
   <tr><th>Quelle</th><th>Art</th><th>Rang</th><th class=z>Personen</th>
       <th class=z>Wörter</th><th></th></tr>
   ${q.length?q.map(x=>`<tr>
     <td>${esc(x.name||x.datei||x.art)}<div class=dim
       style="font-size:.78rem">${esc(x.datei||'')}</div></td>
     <td class=dim>${esc(x.art)}</td>
     <td><span class="marke ${x.gilt}">${x.gilt==='beleg'
        ?'darf bestätigen':'rankt nur'}</span></td>
     <td class="z ${x.n?'':'dim'}">${x.n||0}</td>
     <td class="z ${x.woerter?'':'dim'}">${x.woerter||0}</td>
     <td class=z>${x.art==='erfassung'?'<span class=dim>bleibt</span>'
       :`<button onclick="quelleWeg(${x.id},this)">entfernen</button>`}</td>
    </tr>`).join('')
    :'<tr><td colspan=6 class=dim>Noch keine Quelle — Nullstart.</td></tr>'}
  </table>
 </div>

 <div class=karte>
  <div class=was style="font-weight:600;margin-bottom:.15rem">Quelle hinzufügen</div>
  <p class=dim style="font-size:.86rem;margin:0 0 .7rem">
   Pfad zu einer Datei oder einem Ordner auf diesem Rechner. Nichts wird
   kopiert oder verschoben; gelesen wird einmal, danach liegt der Inhalt in
   der Datenbank.</p>
  <div class=reihe>
   <input id=qdatei placeholder="~/bestaende/ofb.ged" style="flex:1;min-width:16rem">
   <select id=qart onchange=quelleArt()>
    <option value=gedcom>GEDCOM — Bestand mit Personen</option>
    <option value=wortschatz>Wortschatz — Liste, Tabelle, Text</option>
   </select>
  </div>
  <div class=reihe style="margin-top:.6rem">
   <input id=qname placeholder="Name, wie er angezeigt werden soll"
     style="flex:1;min-width:14rem">
   <span id=qrang><label class=dim><input type=radio name=qgilt value=beleg
     checked> darf bestätigen</label>
    <label class=dim style="margin-left:.6rem"><input type=radio name=qgilt
     value=vokabular> rankt nur</label></span>
   <button class=ja onclick=quelleDazu(this)>Einlesen</button>
  </div>
  <div id=qhinweis class=dim style="margin-top:.6rem;font-size:.86rem"></div>
 </div>

 <p class=dim style="font-size:.86rem">
  <b>GEDCOM</b> bringt Personen mit Daten — das Einzige, was <i>bestätigen</i>
  darf, weil ein Treffer sich an Datum und Ort prüfen lässt.
  <b>Wortschatz</b> nimmt alles, was Schreibweisen kennt, aber keine
  Lebensdaten hat: Namenslisten, Ortsverzeichnisse, abgetippte Register, in
  <code>.csv .tsv .txt .xlsx .ods .docx</code> oder als ganzer Ordner. Die
  Spalten erkennt der Einleser an der Kopfzeile. Solche Quellen bleiben
  immer <code>vokabular</code> — <code>Roth</code> kommt 59-mal im Bestand
  vor und stand doch für <code>Koch</code>.</p>`;
}

function quelleArt(){
 // Wortschatz kann nicht bestaetigen — die Wahl waere eine Luege.
 document.getElementById('qrang').style.visibility =
   document.getElementById('qart').value==='gedcom' ? 'visible' : 'hidden';
}

async function quelleDazu(btn){
 const h=document.getElementById('qhinweis');
 const datei=document.getElementById('qdatei').value.trim();
 if(!datei){h.textContent='Erst einen Pfad angeben.';return;}
 btn.disabled=true; h.textContent='liest …';
 const gilt=(document.querySelector('input[name=qgilt]:checked')||{}).value;
 const a=await (await fetch('/api/quelle',{method:'POST',
   body:JSON.stringify({datei, art:document.getElementById('qart').value,
    name:document.getElementById('qname').value, gilt})})).json();
 btn.disabled=false;
 if(a.fehler){h.textContent=a.fehler;return;}
 document.getElementById('qdatei').value='';
 document.getElementById('qname').value='';
 const z=a.neu_geprueft||{};
 const n=(z.gruen||0)+(z.gelb||0)+(z.rot||0);
 h.textContent = n
  ? `eingelesen. ${n} noch offene Einträge neu abgeglichen — ${z.gruen||0} grün.`
  : 'eingelesen.';
 S=await (await fetch('/api/stand')).json();
 document.getElementById('app').innerHTML=ansichtEinstellungen();
}

async function quelleWeg(id,btn){
 const h=document.getElementById('qhinweis');
 btn.disabled=true;
 const a=await (await fetch('/api/quelle-weg',{method:'POST',
   body:JSON.stringify({herkunft:id})})).json();
 if(a.fehler){btn.disabled=false; h.textContent=a.fehler; return;}
 S=await (await fetch('/api/stand')).json();
 document.getElementById('app').innerHTML=ansichtEinstellungen();
}

// ------------------------------------------------------------- Aktkarten
let karteArt='taufe';
// 35 Felder mal drei Aktarten sind 105 Tabellenzeilen. Gezeigt wird, was
// dieses Buch fuehrt; der ganze Vorrat auf Knopfdruck.
let vorratZeigen=false;

const AMTFARBE={offiziell:'#8fe3b4', verbreitet:'#e0c98a',
                hauseigen:'#e0a06c', unbekannt:'#e06c5f'};

function tagMarke(ziel,amt){
 if(!ziel) return '<span class=dim>—</span>';
 return `<code style="color:${AMTFARBE[amt]||'#c3c9d4'}"
   title="${esc((E.tag_amt||{})[amt]||'')}">${esc(ziel)}</code>`;
}

function periodenKarte(){
 return `
 <h2>Formularperioden — was das Buch selbst sagt</h2>
 <div class=karte>
  <p class=dim style="font-size:.86rem;margin:0 0 .7rem">
   Ein Kirchenbuch wechselt im Lauf der Jahrzehnte das gedruckte Formular.
   Gelesen wird dafür nicht die Seite, sondern nur der <b>gedruckte Kopf</b>
   jeder fünften Seite — daraus entstehen die Abschnitte. Geometrisch geht
   das nicht: Die senkrechte Linienerkennung schwankt auf demselben
   Formular zwischen 2 und 11 Linien.</p>
  ${Object.keys(E.aktkarten||{}).map(a=>{
    const ps=(S&&S.perioden||[]).filter(p=>p.register===a);
    const hs=((S&&S.haende)||{})[a]||[];
    return `<div style="margin-bottom:.9rem">
     <div class=reihe>
      <b>${esc(a)}</b>
      <button onclick="periodenPruefen('${esc(a)}',this)">Köpfe lesen</button>
      <span class=dim style="font-size:.84rem">${ps.length
        ? ps.length+' Periode'+(ps.length>1?'n':'') : 'noch nicht geprüft'}</span>
     </div>
     ${ps.map(p=>`<div class=dim style="font-size:.85rem;margin:.35rem 0 0 .6rem">
       <code>${esc(p.von_bild)}</code> – <code>${esc(p.bis_bild)}</code>
       (${p.seiten} Seiten) · ${p.spalten.length} Spalten
       <div style="margin-left:.6rem">${p.spalten.map(esc).join(' | ')}</div>
      </div>`).join('')}
     ${hs.length?`<div class=dim style="font-size:.85rem;margin:.35rem 0 0 .6rem">
       <b>Schreiber</b> (aus den erfassten Einträgen, kostet nichts):
       ${hs.map(h=>`${esc(h.wer)} <span style=opacity:.7>(${h.n})</span>`).join(' · ')}
      </div>`:''}
    </div>`;}).join('')}
  <div id=perhinweis class=dim style="font-size:.86rem"></div>
 </div>`;
}

function aktkarten(){
 const felder=(E.aktkarten||{})[karteArt]||[];
 const z={offiziell:0,verbreitet:0,hauseigen:0,ohne:0};
 felder.filter(f=>f.aktiv).forEach(f=>{
  [[f.ziel,f.ziel_amt],[f.kb?f.ziel_kb:null,f.ziel_kb_amt]].forEach(([t,a])=>{
   if(t) z[a]=(z[a]||0)+1;});
  if(!f.ziel&&!f.ziel_kb) z.ohne++;});
 return `
 <h2>Aktkarten — welche Felder eine Registerart führt</h2>
 <div class=karte>
  <div class=reihe style="margin-bottom:.8rem">
   ${Object.keys(E.aktkarten||{}).map(a=>`<button
     class="${a===karteArt?'ja':''}" onclick="karteArt='${a}';neuZeichnen()"
     >${esc(a)}</button>`).join('')}
   <span style=flex:1></span>
   <span class=dim style="font-size:.84rem">
    ${felder.filter(f=>f.aktiv).length} aktiv, ${felder.length} im Vorrat</span>
   <button onclick="vorratZeigen=!vorratZeigen;neuZeichnen()">${
     vorratZeigen?'nur aktive':'ganzen Vorrat'}</button>
  </div>

  <p class=dim style="font-size:.86rem;margin:0 0 .8rem">
   Der Vorrat steht fest — das ist der Schutz gegen Wildwuchs. Was Sie
   hier tun, ist auswählen: abschalten, was Ihre Bücher nicht führen,
   Ziele umhängen, im Notfall ein eigenes Feld ergänzen. Ein Feld
   abzuschalten löscht nichts; bereits erfasste Werte bleiben stehen.</p>

  <div class=reihe style="margin-bottom:.7rem;font-size:.85rem">
   <b>Beim Weitergeben des Bestands:</b>
   ${[['offiziell','Ziele in GEDCOM 5.5.1'],
      ['verbreitet','eigene Tags, gebräuchlich'],
      ['hauseigen','eigene Tags, nur hier']].map(([k,t])=>
    `<span><i class=pkt style="background:${AMTFARBE[k]}"></i>
      ${z[k]||0} ${t}</span>`).join(' · ')}
   ${z.ohne?`<span class=dim>· ${z.ohne} ohne Ziel</span>`:''}
  </div>

  <table>
   <tr><th></th><th>Feld</th><th>Rolle</th><th>Ziel kanonisch</th>
       <th>Ziel Kirchenbuchform</th><th></th></tr>
   ${(vorratZeigen?felder:felder.filter(f=>f.aktiv)).map(f=>`<tr style="${f.aktiv?'':'opacity:.45'}">
     <td><input type=checkbox ${f.aktiv?'checked':''}
       onchange="feldSchalten('${esc(f.name)}',this.checked)"></td>
     <td><code>${esc(f.name)}</code>
       <div class=dim style="font-size:.78rem">${esc(f.titel||'')}${
        f.eigen?' <b style=color:#e0a06c>eigenes Feld</b>':''}</div></td>
     <td class=dim>${esc(f.rolle||'—')}</td>
     <td>${tagMarke(f.ziel,f.ziel_amt)}</td>
     <td>${f.kb?tagMarke(f.ziel_kb,f.ziel_kb_amt)
        :'<span class=dim>keine</span>'}</td>
     <td class=z><button onclick="feldAendern('${esc(f.name)}')"
       title="Ziel ändern">ändern</button></td>
    </tr>`).join('')}
  </table>
 </div>

 <div class=karte>
  <div style="font-weight:600;margin-bottom:.3rem">Eigenes Feld ergänzen</div>
  <p class=dim style="font-size:.86rem;margin:0 0 .7rem">
   Nur wenn Ihre Bücher etwas führen, das der Vorrat nicht kennt. Der Name
   wird zum Schlüssel — Kleinbuchstaben, Ziffern, Unterstrich.</p>
  <div class=reihe>
   <input id=fname placeholder="z. B. hausnummer" style=width:12rem>
   <input id=ftitel placeholder="Beschriftung in der Maske" style="flex:1;min-width:12rem">
   <input id=fziel placeholder="GEDCOM-Ziel, z. B. ADDR" style=width:11rem>
   <button class=ja onclick=feldDazu(this)>anlegen</button>
  </div>
  <div id=fhinweis class=dim style="margin-top:.5rem;font-size:.86rem"></div>
 </div>

 <p class=dim style="font-size:.86rem">
  <b>Warum die Farben zählen.</b> GEDCOM gibt den Unterstrich für eigene
  Erweiterungen frei und sagt nichts darüber, was sie bedeuten. Ein Tag wie
  <code>_TODURSACHE</code> versteht nur, wer dieselbe Erweiterung kennt —
  beim Wechsel zu einem anderen Programm geht er still verloren.
  Deshalb steht der Wortlaut zusätzlich im <code>volltext</code>: was kein
  Programm versteht, ist wenigstens lesbar geblieben.</p>`;
}

async function periodenPruefen(reg,btn){
 btn.disabled=true;
 document.getElementById('perhinweis').textContent =
  `liest die Formularköpfe von ${reg} — das dauert ein paar Minuten, `
  +'die Seite kann inzwischen zu.';
 await fetch('/api/perioden',{method:'POST',
   body:JSON.stringify({register:reg})});
}

async function feldSchalten(name,an){
 await fetch('/api/feld',{method:'POST',
  body:JSON.stringify({art:karteArt, name, aktiv:an?1:0})});
 await einstellungenHolen();
}

async function feldAendern(name){
 const f=((E.aktkarten||{})[karteArt]||[]).find(x=>x.name===name);
 const ziel=prompt(`Ziel für „${name}“ (kanonisch)\n\n`
  +'Leer = kein Ziel. Punkt trennt Ebenen: BIRT.DATE',  f&&f.ziel||'');
 if(ziel===null) return;
 const d={art:karteArt, name, ziel:ziel.trim()};
 if(f&&f.kb){
  const kb=prompt(`Ziel für die Kirchenbuchform von „${name}“`, f.ziel_kb||'');
  if(kb!==null) d.ziel_kb=kb.trim();
 }
 await fetch('/api/feld',{method:'POST',body:JSON.stringify(d)});
 await einstellungenHolen();
}

async function feldDazu(btn){
 const h=document.getElementById('fhinweis');
 const name=document.getElementById('fname').value.trim();
 if(!name){h.textContent='Erst einen Namen angeben.';return;}
 btn.disabled=true;
 const a=await (await fetch('/api/feld',{method:'POST',body:JSON.stringify({
   art:karteArt, name, titel:document.getElementById('ftitel').value.trim(),
   ziel:document.getElementById('fziel').value.trim()||null,
   feldart:'text', aktiv:1, eigen:1})})).json();
 btn.disabled=false;
 if(a.fehler){h.textContent=a.fehler;return;}
 document.getElementById('fname').value='';
 document.getElementById('ftitel').value='';
 document.getElementById('fziel').value='';
 await einstellungenHolen();
}

function neuZeichnen(){
 document.getElementById('app').innerHTML =
   P==='/formular' ? ansichtFormular() : ansichtEinstellungen();
 quelleArt();
}

// Zehn Abschnitte untereinander waren unbedienbar. Was ein
// Arbeitsschritt ist — Dubletten, Formularperioden, Aktkarten — steht
// jetzt dort, wo man es braucht; der Rest liegt hinter Reitern, einer
// sichtbar.
let zahnradReiter = sessionStorage.getItem('zahnrad') || 'Bestand';

const ZAHNRAD = { "Bestand": () => `
 ${quellenKarte()}
`, "Bücher": () => ` <h2>Reihenfolge der Register</h2>
 <div class=karte>
  <div class=reihe id=reihe>
   ${E.reihenfolge.map((x,i)=>`<span class=chip data-r="${esc(x)}">
     ${i?`<button title="nach vorn" onclick="schieben(${i},-1)">↑</button>`:''}
     ${esc(x)}
     ${i<E.reihenfolge.length-1?`<button title="nach hinten"
        onclick="schieben(${i},1)">↓</button>`:''}
    </span>${i<E.reihenfolge.length-1?'<span class=dim>→</span>':''}`).join('')}
   <span class=dim style="margin-left:.6rem">→ wieder von vorn</span>
  </div>
  <p class=dim style="font-size:.86rem;margin:.7rem 0 0">
   <b>Ehen zuerst ist keine Geschmacksfrage.</b> Der Elternehe-Anker trägt im
   Taufjahr 1808 noch 94 %, 1813 noch 53 %, 1820 nur 18 % — es sei denn, die
   Ehen ab 1808 sind vorher übergeben, dann wächst er mit. Tode zuletzt, weil
   sie beide vorigen Register als Anker nutzen.</p>
 </div>

 <h2>Seiten je Runde und Bildordner</h2>
 <div class=karte><table>
  <tr><th>Register</th><th>Seiten je Runde</th><th>Ordner</th>
      <th class=z>Bilder</th><th class=z>PDFs</th><th></th></tr>
  ${E.register.map(x=>`<tr>
   <td>${esc(x.titel)}</td>
   <td><input type=number min=1 max=200 value="${x.seiten}" style=width:4.5rem
        onchange="merken('seiten.${esc(x.register)}',this.value)"></td>
   <td><input value="${esc(x.ordner)}" style="width:100%;min-width:18rem"
        onchange="merken('ordner.${esc(x.register)}',this.value)">
       ${x.da?'':'<span style=color:#e06c5f>⚠ Ordner fehlt</span>'}</td>
   <td class="z ${x.bilder?'':'dim'}">${x.bilder}</td>
   <td class="z ${x.pdfs?'':'dim'}">${x.pdfs}</td>
   <td>${x.pdfs?`<button onclick="entpacken('${esc(x.register)}',this)"
     ${E.pdf_werkzeug?'':'disabled'}>PDFs zerlegen</button>`:''}</td>
  </tr>`).join('')}
 </table>
 <p class=dim style="font-size:.86rem;margin:.7rem 0 0">
  Ungleiche Seitenzahlen mit Absicht: Ein Eheeintrag nennt <b>sechs</b>
  Personen, ein Taufeintrag drei. Zehn Ehe-Seiten sind ungefähr so viel
  Arbeit wie zwanzig Taufseiten.<br>
  <b>PDFs</b> sind Behälter, keine Bilder — sie werden einmal in Einzelseiten
  zerlegt (300 dpi, nach <code>entpackt/</code>) und danach wie gewöhnliche
  Bilder behandelt. ${E.pdf_werkzeug
   ? '<span style=color:#8fe3b4>pdftoppm gefunden.</span>'
   : '<span style=color:#e06c5f>pdftoppm fehlt — Paket poppler-utils.</span>'}</p>
 </div>

`, "KI": () => ` <h2>KI-Anbindung</h2>
 <div class=karte>
  <h3 style="margin:0 0 .5rem">Über Claude Code — das eigene Abonnement</h3>
  <div id=anmeldung>${anmeldeblock(E.ki.cli)}</div>
  <p class=dim style="font-size:.86rem;margin:.2rem 0 0">
   Die Werkstatt speichert <b>keine Anmeldedaten</b> und hängt sich an
   <b>keinen laufenden Chat</b>. Sie ruft für jede Runde einmal
   <code>claude&nbsp;-p</code> auf; das ist eine eigene, kurze Sitzung ohne
   Verlauf. Wer angemeldet ist, entscheidet allein die Anmeldung im
   Benutzerprofil — dieselbe, mit der Sie Claude Code sonst auch bedienen.
   Über diesen Weg zählt das Lesen auf das Abonnement, nicht auf eine
   zweite Rechnung.</p>

  <h3 style="margin:1.2rem 0 .5rem">Über die API — mit Schlüssel</h3>
  ${E.ki.schluessel
    ? `<div class=reihe style="margin-bottom:.7rem">
        <span class=ampel><i class="pkt gruen"></i>
        <b>ANTHROPIC_API_KEY ist gesetzt</b></span>
        <span class=dim>der Schlüssel selbst wird nirgends angezeigt</span></div>`
    : `<div class=warn>Kein <code>ANTHROPIC_API_KEY</code> in der Umgebung.
        Lesen läuft nur mit der Testquelle. Zum Setzen:
        <code>export ANTHROPIC_API_KEY=…</code> vor <code>python3 start.py</code>.</div>`}
  <table>
   <tr><th>Modell</th><th class=z>ein $/Mio</th><th class=z>aus $/Mio</th>
       <th class=z>Bildkante</th><th class=z>je Seite*</th></tr>
   ${Object.entries(E.ki.modelle).map(([id,m])=>`<tr>
     <td><label style=cursor:pointer><input type=radio name=modell value="${esc(id)}"
       ${E.ki.modell===id?'checked':''} onchange="merken('ki.modell',this.value)">
      ${esc(m.name)} <code>${esc(id)}</code></label></td>
     <td class=z>${m.ein.toFixed(2)}</td><td class=z>${m.aus.toFixed(2)}</td>
     <td class=z>${m.kante} px</td>
     <td class=z>${(5000/1e6*m.ein + 3000/1e6*m.aus).toFixed(3)}</td>
   </tr>`).join('')}
  </table>
  <p class=dim style="font-size:.84rem;margin:.5rem 0 0">
   * grobe Schätzung bei 5.000 Token hinein und 3.000 heraus. Mit Batch halbiert
   sich beides — das ist bei seitenweiser Verarbeitung der natürliche Modus und
   noch nicht gebaut.</p>

  <div class=reihe style="margin-top:.9rem">
   <label class=dim>Bildkante</label>
   <input type=number value="${E.ki.max_kante}" min=512 max=2576 step=8
    style=width:6rem onchange="merken('ki.max_kante',this.value)">
   <span class=dim>px auf der langen Seite</span>
   <label class=dim style=margin-left:1rem>Antwort höchstens</label>
   <input type=number value="${E.ki.max_tokens}" min=1000 max=64000 step=1000
    style=width:6.5rem onchange="merken('ki.max_tokens',this.value)">
   <span class=dim>Token</span>
  </div>
  <p class=dim style="font-size:.84rem;margin:.5rem 0 0">
   <b>Die Bildkante ist der Hebel für die Lesequalität.</b> Sie stand auf
   1568 px mit dem Vermerk „größer bringt nichts" — das galt für ältere
   Modelle; Opus 5 und Sonnet 5 nehmen 2576 px. Bei Kurrentschrift zählt das:
   Ancestry-JPG mit 24 MP löste einen Eheeintrag auf, den das Archion-PDF mit
   14 MP unlesbar ließ. Der Preis dafür ist klein — 1.600 statt 4.784 Bildtoken
   sind bei Opus 5 rund zwei Cent je Seite.</p>

  ${(E.ki.verbrauch.wege||[]).length
    ? `<table style="margin-top:.9rem">
        <tr><th>Weg</th><th class=z>Seiten</th><th class=z>Token ein</th>
            <th class=z>davon Zwischenspeicher</th><th class=z>Token aus</th>
            <th class=z>Dauer</th><th class=z>je Seite</th><th class=z>gesamt</th></tr>
        ${E.ki.verbrauch.wege.map(w=>`<tr>
          <td>${w.quelle==='api'?'API':'Abonnement'}
            <div class=dim style=font-size:.78rem>${w.bezahlt
              ?'wird berechnet':'kostet nichts extra — was es über die API gekostet hätte'}</div></td>
          <td class=z>${w.seiten}</td>
          <td class=z>${w.tokens_ein.toLocaleString('de')}</td>
          <td class=z>${(w.tokens_cache||0).toLocaleString('de')}</td>
          <td class=z>${w.tokens_aus.toLocaleString('de')}</td>
          <td class=z>${w.minuten!=null?w.minuten+' min':'—'}</td>
          <td class=z>${w.je_seite!=null?w.je_seite.toFixed(3)+' $':'—'}</td>
          <td class=z><b>${w.dollar.toFixed(2)} $</b></td></tr>`).join('')}
       </table>
       <p class=dim style="font-size:.86rem;margin:.6rem 0 0">
        Beide Zeilen sind <b>gemessen</b>, nicht geschätzt: über die API aus
        Token und Preisliste, über das Abonnement aus dem, was
        <code>claude -p</code> selbst meldet. Der Zwischenspeicher ist der
        Grund, warum eine zweite Seite viel weniger kostet als die erste —
        Prompt und Bestand werden nur einmal bezahlt.</p>`
    : `<p class=dim style="font-size:.86rem;margin:.9rem 0 0">
        Noch nichts gelesen — sobald ein Lauf durch ist, steht hier der
        <b>gemessene</b> Verbrauch statt einer Schätzung. Auch der Weg über
        das Abonnement wird beziffert: Er kostet nichts extra, aber die Zahl
        beantwortet die Frage, ob sich das für andere lohnt.</p>`}
 </div>

 <h2>Beim Starten</h2>
 <div class=karte>
  <label style="display:block;cursor:pointer">
   <input type=checkbox ${(E.eigen||{})['browser.oeffnen']!=='0'?'checked':''}
    onchange="merken('browser.oeffnen', this.checked?'1':'0')">
   <b>Browserfenster öffnen</b></label>
  <p class=dim style="font-size:.86rem;margin:.5rem 0 0">
   Gehen beim Start <b>zwei</b> Tabs auf, liegt das am Browser, nicht an
   der Werkstatt: Er stellt die letzte Sitzung wieder her — die Werkstatt
   war beim Schließen ja offen — und bekommt unseren Aufruf zusätzlich.
   Entweder hier abschalten und das Lesezeichen benutzen, oder den
   Werkstatt-Tab vor dem Beenden des Browsers schließen.</p>
 </div>

`, "Arbeitsweise": () => ` <h2>Wie viel läuft ohne Rückfrage durch</h2>
 <div class=karte>
  ${Object.entries(E.autopilot_text).map(([k,v])=>`
   <label style="display:block;padding:.3rem 0;cursor:pointer">
    <input type=radio name=ap value="${esc(k)}" ${E.autopilot===k?'checked':''}
     onchange="merken('autopilot',this.value)">
    <b>${esc(k)}</b> <span class=dim>— ${esc(v)}</span></label>`).join('')}
  <p class=dim style="font-size:.86rem;margin:.7rem 0 0">
   Jede Stufe höher tauscht Tempo gegen stille Fehler. Eine Grenze bleibt auf
   jeder Stufe fest: <b>Die Selbsteinschätzung des Modells macht nie grün.</b>
   Sie darf bestimmen, was zuerst gezeigt wird — nicht, was als bestätigt
   gilt. Bei <code>Koch</code>/<code>Roth</code> war das Modell viermal sicher
   und viermal falsch.</p>
 </div>

 <h2>Plausibilität</h2>
 <div class=karte>
  <p class=dim style="margin:0 0 .8rem;font-size:.88rem">
   Zwei Sätze, und das ist Absicht: Der <b>Abgleich</b> entscheidet, ob ein
   Zuordnungsvorschlag überhaupt möglich ist — er darf nur Unmögliches
   ausschließen, sonst verwirft er richtige Treffer. Die
   <b>Bestandsprüfung</b> sucht Widersprüche in dem, was schon dasteht — sie
   darf enger sein, weil sie nur meldet.</p>

  <h3 style="font-size:.95rem;margin:.4rem 0 .5rem">Was der Abgleich
   ausschließt <span class=dim style=font-weight:400>— weit gefasst</span></h3>
  <div class=reihe>
   <label class=dim>Mutter</label>
   <input type=number value="${E.grenzen.mutter[0]}" style=width:4rem
    onchange="merken('mutter_alter_min',this.value)">
   <span class=dim>bis</span>
   <input type=number value="${E.grenzen.mutter[1]}" style=width:4rem
    onchange="merken('mutter_alter_max',this.value)">
   <span class=dim style=margin-left:1rem>Vater</span>
   <input type=number value="${E.grenzen.vater[0]}" style=width:4rem
    onchange="merken('vater_alter_min',this.value)">
   <span class=dim>bis</span>
   <input type=number value="${E.grenzen.vater[1]}" style=width:4rem
    onchange="merken('vater_alter_max',this.value)">
   <span class=dim>Jahre bei der Geburt eines Kindes</span>
  </div>
  <p class=dim style="font-size:.86rem;margin:.5rem 0 1.2rem">
   Ohne diese Prüfung ordnete der Abgleich einer Taufe von <b>1809</b> ein
   Paar zu, das 1699 und 1703 geboren wurde und dessen Frau 1767 starb — und
   machte es grün.</p>

  <h3 style="font-size:.95rem;margin:1rem 0 .3rem">Was die Bestandsprüfung
   meldet <span class=dim style=font-weight:400>— nach Gramps und
   Ahnenblatt</span></h3>
  <p class=dim style="font-size:.86rem;margin:0 0 .6rem">
   Übernommen aus <b>Gramps</b> („Verify the Data", 43 Regeln, 15 Grenzwerte)
   und <b>Ahnenblatt</b> (Plausibilitätsprüfung, sieben Altersgrenzen), damit
   hier nichts neu erfunden wird, was seit Jahren funktioniert. Aufruf:
   <code>python3 -m werkstatt.pruefung</code></p>
  <table>
   <tr><th>Grenze</th><th class=z>Wert</th><th></th><th>Herkunft</th></tr>
   ${E.pruefgrenzen.map(g=>`<tr>
    <td>${esc(g.beschriftung)}
     ${g.erlaeuterung?`<div class=dim style="font-size:.82rem">${esc(g.erlaeuterung)}</div>`:''}</td>
    <td class=z><input type=number value="${g.wert}" style=width:4.5rem
      onchange="merken('pruef.${esc(g.schluessel)}',this.value)"></td>
    <td class=dim>${esc(g.einheit)}</td>
    <td class=dim style=font-size:.82rem>${esc(g.quelle)}
     ${g.wert!==g.vorgabe?`<br><span style=color:#e0b341>Vorgabe ${g.vorgabe}</span>`:''}</td>
   </tr>`).join('')}
  </table>
  <details style=margin-top:.8rem>
   <summary class=dim style="cursor:pointer;font-size:.88rem">
    ${E.regeln.length} Regeln, die daraus folgen</summary>
   <table style=margin-top:.5rem>
    ${E.regeln.map(r=>`<tr>
     <td><span class="marke ${r.schwere==='fehler'?'vokabular':'beleg'}"
       style="${r.schwere==='fehler'?'background:#4a2318;color:#f0a89a':''}">
       ${r.schwere}</span></td>
     <td>${esc(r.titel)}</td>
     <td class=dim style=font-size:.8rem><code>${esc(r.schluessel)}</code></td>
    </tr>`).join('')}
   </table>
  </details>
 </div>

 <div class=reihe style="margin:1.2rem 0">
  <button class=ja id=speichern onclick=einstellungenSpeichern() disabled>
   Speichern</button>
  <span class=dim id=espeichert></span>
 </div>

`, "Über": () => ` <h2>Struktur — steht in der Datei, nicht hier</h2>
 <div class=karte><p class=dim style="font-size:.88rem;margin:0">
  Registerarten, Felder, Rollen und Kontextquellen stehen in
  <code>konfig.toml</code>, eigene Pfade in <code>konfig.local.toml</code>
  (in <code>.gitignore</code>). Das ist Struktur — sie ändert man beim
  Einrichten, nicht beim Arbeiten. Sie hier bearbeitbar zu machen hieße, die
  Datei bei jedem Klick neu zu schreiben und dabei ihre Kommentare zu
  verlieren; die machen den halben Erklärwert aus.</p></div>

 
 ${ansichtUeber(E.ueber)}
`,};
function ansichtEinstellungen(){
 const r=E.register;
 const namen=Object.keys(ZAHNRAD);
 if(!namen.includes(zahnradReiter)) zahnradReiter=namen[0];
 return `
 <div class=reihe style="margin-bottom:1rem">
  ${namen.map(n=>`<button class="${n===zahnradReiter?'ja':''}"
    onclick="zahnradWaehlen('${n}')">${esc(n)}</button>`).join('')}
 </div>
 ${ZAHNRAD[zahnradReiter]()}`;
}

function zahnradWaehlen(n){
 zahnradReiter=n; sessionStorage.setItem('zahnrad',n);
 document.getElementById('app').innerHTML=ansichtEinstellungen();
 quelleArt();
}

function merken(k,v){
 geaendert[k]=v;
 const b=document.getElementById('speichern');
 if(b){b.disabled=false; b.textContent=`Speichern (${Object.keys(geaendert).length})`}
 document.getElementById('espeichert').textContent='';
}
function schieben(i,d){
 const r=[...E.reihenfolge]; const [x]=r.splice(i,1); r.splice(i+d,0,x);
 E.reihenfolge=r; merken('reihenfolge',r.join(','));
 document.getElementById('app').innerHTML=ansichtEinstellungen();
 const b=document.getElementById('speichern');
 b.disabled=false; b.textContent=`Speichern (${Object.keys(geaendert).length})`;
}
async function einstellungenSpeichern(){
 await fetch('/api/einstellungen',{method:'POST',
  headers:{'content-type':'application/json'},
  body:JSON.stringify({werte:geaendert})});
 geaendert={};
 await einstellungenHolen();
 const s=document.getElementById('espeichert');
 if(s) s.textContent='gespeichert';
}
async function entpacken(reg,btn){
 btn.disabled=true; btn.textContent='zerlege…';
 const r=await fetch('/api/entpacken',{method:'POST',
  headers:{'content-type':'application/json'},
  body:JSON.stringify({register:reg})});
 const j=await r.json();
 await einstellungenHolen();
 alert(j.ok?`fertig: ${JSON.stringify(j.zahlen)}`:`Fehler: ${j.zahlen.fehler}`);
}

// ---------------------------------------------------------------- Über
function ansichtUeber(U){
 const b=U.bestand, f=U.fassung||{};
 return `
 <h2 style=margin-top:2.2rem>Über die Werkstatt</h2>
 <div class=schritt>
  <div class=was>${esc(U.name)}</div>
  <div class=warum>${esc(U.zweck)}</div>
  <div class=reihe>
   ${f.commit?`<span class=dim>Fassung <code>${esc(f.commit)}</code>
     vom ${esc(f.datum)} · ${esc(f.anzahl)} Commits</span>`:''}
   <span class=dim>${esc(U.lizenz)}-Lizenz · ${esc(U.autor)}</span>
  </div>
  ${f.betreff?`<div class=dim style="font-size:.86rem;margin-top:.3rem">
    zuletzt: ${esc(f.betreff)}</div>`:''}
 </div>

 <h2>Wohin Daten gehen — bitte lesen</h2>
 <div class=warn style="line-height:1.5">
  <b>Beim Lesen verlassen Ihre Kirchenbuchbilder diesen Rechner.</b>
  Sie werden an die Anthropic-API geschickt. Scans von Archion, Ancestry
  oder einem Archiv unterliegen deren Nutzungsbedingungen — ob die eine
  Übermittlung an einen Dienstleister decken, muss jeder für seine eigenen
  Quellen klären. Die Werkstatt kann das nicht für Sie entscheiden.
  <br><br>
  Alles Übrige bleibt hier: Der Bestand, die Erfassung und die Ausgabe
  liegen ausschließlich in <code>${esc(U.datenbank)}</code> und
  <code>ausgabe/</code>. Kein Login, kein Hosting, kein Upload. Der Server
  hört nur auf <code>127.0.0.1</code>.
  <br><br>
  Mit der Quelle <b>Testdaten</b> (${U.testdaten} Seiten) läuft der ganze
  Ablauf ohne Netz und ohne Kosten.
 </div>

 <h2>Was das Werkzeug kann — und was nicht</h2>
 <div class=karte style="line-height:1.55">
  <p style=margin-top:0><b>Es ist ein Abgleichsverfahren, kein
  Leseverfahren.</b> Im Pilotlauf waren 42 % der gelesenen Familiennamen
  falsch; auf 13,4 % markierte Felder kam das Verfahren erst durch den
  Abgleich gegen den vorhandenen Bestand. Was gut lesbar ist — Datum,
  Vornamen, Beruf, Ort — trägt den Abgleich; die Nachnamen werden
  <i>durch</i> ihn bestimmt.</p>
  <p><b>Grün wird nur, was ein Anker bestätigt.</b> Weder die
  Selbsteinschätzung des Modells noch die Häufigkeit im Bestand machen
  grün: Bei <code>Koch</code>/<code>Roth</code> war das Modell viermal
  sicher und viermal falsch, und <code>Roth</code> kommt 59-mal vor.</p>
  <p style=margin-bottom:0><b>Ungeprüft geblieben ist die Lesequalität
  selbst.</b> Alle bisherigen Zahlen messen die Verknüpfung, nicht das
  Lesen — die Testdaten enthalten bereits korrigierte Lesungen. Dafür
  braucht es einen Lauf über die API gegen eine Seite mit bekannter
  Wahrheit.</p>
 </div>

 <h2>Nachlesen</h2>
 <div class=karte>
  <p class=dim style="margin:0 0 .5rem">Alle Entwurfsentscheidungen stehen
   mit ihren Messwerten in <code>doku/</code> — nichts davon ist behauptet,
   ohne dass daneben steht, woran es gemessen wurde.</p>
  <table>${U.doku.map(d=>`<tr><td><code>doku/${esc(d)}</code></td></tr>`).join('')}
   <tr><td><code>CLAUDE.md</code></td></tr>
   <tr><td><code>ROADMAP.md</code></td></tr>
  </table>
  <p class=dim style="font-size:.86rem;margin:.6rem 0 0">
   Projektwurzel: <code>${esc(U.wurzel)}</code><br>
   PDF-Aufbereitung: ${U.pdf_werkzeug
     ? '<span style=color:#8fe3b4>pdftoppm gefunden</span>'
     : '<span style=color:#e06c5f>pdftoppm fehlt (Paket poppler-utils)</span>'}</p>
 </div>`;
}

laden().then(()=>{
 if(P==='/uebergabe') probeHolen();
 if(P==='/ausgabe') ausgabeHolen();
 if(P==='/einstellungen'||P==='/formular') einstellungenHolen();
});
</script></body></html>"""
