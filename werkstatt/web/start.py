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
</style></head><body>
<header><b>OFB-Werkstatt</b>
 <a href="/" data-p="/">Stand</a>
 <a href="/lesen" data-p="/lesen">Lesen</a>
 <a href="/korrektur" data-p="/korrektur">Korrigieren</a>
 <a href="/uebergabe" data-p="/uebergabe">Übergeben</a>
 <span style=flex:1></span><span class=dim id=gem></span></header>
<main id=app class=leer>lade…</main>
<script>
const esc=s=>(s??'').toString().replace(/[&<>"]/g,c=>
 ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const P=location.pathname;
let S=null, ticker=null;

document.querySelectorAll('header a').forEach(a=>
 a.classList.toggle('an', a.dataset.p===P));

async function laden(){
 S=await (await fetch('/api/stand')).json();
 document.getElementById('gem').textContent=S.gemeinde;
 const app=document.getElementById('app');
 app.className='';
 app.innerHTML = P==='/lesen' ? ansichtLesen()
               : P==='/uebergabe' ? ansichtUebergabe()
               : ansichtStand();
 if(P==='/lesen' && S.runde && S.runde.stand==='liest') takt();
 if(P==='/lesen' && !S.runde && document.getElementById('reg')){
  document.getElementById('reg').onchange=quelleGewaehlt; quelleGewaehlt();}
}

// ---------------------------------------------------------------- Stand
function ansichtStand(){
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
function ansichtLesen(){
 const r=S.runde;
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
 return `<div class=schritt>
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
    ${S.register.some(x=>x.offen_test)
      ?`<option value=testdaten>Testdaten — ohne Schlüssel, kostet nichts</option>`:''}
    <option value=api>API — braucht ANTHROPIC_API_KEY</option>
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
  if(!S.runde||S.runde.stand!=='liest') clearInterval(ticker);
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
 location.href='/';
}

laden().then(()=>{ if(P==='/uebergabe') probeHolen(); });
</script></body></html>"""
