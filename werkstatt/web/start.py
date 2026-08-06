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
.chip{display:inline-flex;gap:.3rem;align-items:center;background:#262b33;
 border:1px solid #333a45;border-radius:99px;padding:.15rem .5rem;font-size:.9rem}
.chip button{padding:0 .25rem;background:transparent;font-size:.9rem;line-height:1}
input{background:#12141a;border:1px solid #333a45;color:#e6e8ec;border-radius:6px;
 padding:.35rem .5rem;font:inherit}
label input[type=radio]{margin-right:.4rem}
</style></head><body>
<header><b>OFB-Werkstatt</b>
 <a href="/" data-p="/">Stand</a>
 <a href="/lesen" data-p="/lesen">Lesen</a>
 <a href="/korrektur" data-p="/korrektur">Korrigieren</a>
 <a href="/uebergabe" data-p="/uebergabe">Übergeben</a>
 <a href="/ausgabe" data-p="/ausgabe">Ausgeben</a>
 <span style=flex:1></span><span class=dim id=gem></span>
 <a href="/einstellungen" data-p="/einstellungen" title="Einstellungen">⚙</a></header>
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
               : P==='/ausgabe' ? ansichtAusgabe()
               : P==='/einstellungen' ? '<div class=leer>lade…</div>'
               : ansichtStand();
 if(P==='/lesen' && S.runde &&
    (S.runde.stand==='liest' ||
     (S.runde.quelle==='datei' && S.vorlage && S.vorlage.fertig<S.vorlage.gesamt)))
  takt();
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
 document.getElementById('app').innerHTML=ansichtEinstellungen();
}

function ansichtEinstellungen(){
 const r=E.register;
 return `
 <h2>Reihenfolge der Register</h2>
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
  ${r.map(x=>`<tr>
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

 <h2>KI-Anbindung</h2>
 <div class=karte>
  <h3 style="margin:0 0 .5rem">Über Claude Code — das eigene Abonnement</h3>
  ${!E.ki.cli.da
   ? `<div class=warn>${esc(E.ki.cli.meldung||'')}
       <div style="margin-top:.5rem">Einrichten in drei Schritten:</div>
       <ol style="margin:.3rem 0 0 1.1rem;padding:0">
        <li>Claude Code installieren — <code>claude.com/download</code>,
            unter Windows das Installationsprogramm.</li>
        <li>Ein Terminal öffnen (Windows: <b>Eingabeaufforderung</b>) und
            <code>claude auth login</code> eingeben. Es öffnet sich der
            Browser, dort wie gewohnt anmelden. Das ist einmalig.</li>
        <li>Diese Seite neu laden — hier muss dann das Konto stehen.</li>
       </ol></div>`
   : E.ki.cli.angemeldet
   ? `<div class=reihe style="margin-bottom:.6rem">
       <span class=ampel><i class="pkt gruen"></i>
       <b>Angemeldet${E.ki.cli.abo?' — '+esc(E.ki.cli.abo)+'-Abonnement':''}</b></span>
       <span class=dim>${esc(E.ki.cli.konto||'')} · ${esc(E.ki.cli.weg||'')}
        · Claude Code ${esc(E.ki.cli.version||'')}</span></div>`
   : `<div class=warn>${esc(E.ki.cli.meldung||'')}
       Ein Terminal öffnen und <code>claude auth login</code> eingeben,
       dann diese Seite neu laden.</div>`}
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

  ${E.ki.verbrauch.tokens_ein
    ? `<div class=reihe style="margin-top:.9rem">
        <div><div class=gross>${E.ki.verbrauch.dollar.toFixed(2)} $</div>
         <div class=dim style=font-size:.82rem>bisher verbraucht</div></div>
        <div><div class=gross>${E.ki.verbrauch.seiten}</div>
         <div class=dim style=font-size:.82rem>Seiten gelesen</div></div>
        ${E.ki.verbrauch.je_seite!=null
          ? `<div><div class=gross>${E.ki.verbrauch.je_seite.toFixed(3)} $</div>
             <div class=dim style=font-size:.82rem>je Seite, gemessen</div></div>`:''}
       </div>`
    : `<p class=dim style="font-size:.86rem;margin:.9rem 0 0">
        Noch nichts über die API gelesen — sobald ein Lauf durch ist, steht
        hier der <b>gemessene</b> Verbrauch statt einer Schätzung.</p>`}
 </div>

 <h2>Wie viel läuft ohne Rückfrage durch</h2>
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

 <h2>Struktur — steht in der Datei, nicht hier</h2>
 <div class=karte><p class=dim style="font-size:.88rem;margin:0">
  Registerarten, Felder, Rollen und Kontextquellen stehen in
  <code>konfig.toml</code>, eigene Pfade in <code>konfig.local.toml</code>
  (in <code>.gitignore</code>). Das ist Struktur — sie ändert man beim
  Einrichten, nicht beim Arbeiten. Sie hier bearbeitbar zu machen hieße, die
  Datei bei jedem Klick neu zu schreiben und dabei ihre Kommentare zu
  verlieren; die machen den halben Erklärwert aus.</p></div>

 ${ansichtUeber(E.ueber)}`;
}

let geaendert={};
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
 if(P==='/einstellungen') einstellungenHolen();
});
</script></body></html>"""
