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
.bildbox.gross{cursor:zoom-out}
.bildbox img{width:100%;display:block}
.bildbox.gross img{width:auto;max-width:none}
.zh{position:absolute;top:.3rem;right:.5rem;background:#0009;color:#fff;
 font-size:.7rem;padding:.1rem .4rem;border-radius:4px;pointer-events:none}
.person{display:grid;grid-template-columns:5.5rem 15rem 1fr auto;gap:.6rem;
 align-items:center;padding:.4rem .9rem;border-bottom:1px solid #23272f}
.person.aktiv{background:#182031}
.feldbox{position:relative}
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
</style></head><body>
<header><a href="/" style="color:#9aa3b2;text-decoration:none">&larr;</a>
<b>OFB-Werkstatt</b><span class=zaehler id=runde></span>
<span class=zaehler id=z></span>
<span style=flex:1></span>
<span class=zaehler><kbd>Enter</kbd> nächstes Feld · <kbd>Strg</kbd>+<kbd>Enter</kbd> Eintrag fertig
 · <kbd>Alt</kbd>+<kbd>N</kbd> neu anlegen</span></header>
<main id=app class=leer>lade…</main>
<script>
let daten=[],fokus=0;
const esc=s=>(s??'').toString().replace(/[&<>"]/g,c=>
 ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

let runde=null;
async function laden(){
 const stand=await (await fetch('/api/stand')).json();
 runde=stand.runde;
 // Die Maske zeigt die gerade gelesene Tranche, nicht den ganzen Bestand.
 // Ohne diese Einschraenkung waechst sie mit jeder Runde weiter, und der
 // Bearbeiter sucht das Neue zwischen dem laengst Erledigten.
 const q=runde?('?runde='+runde.id):'';
 daten=await (await fetch('/api/eintraege'+q)).json();
 const r=document.getElementById('runde');
 if(runde) r.textContent=`Runde ${runde.nr} · ${runde.register} · `
   +`${runde.von_bild} – ${runde.bis_bild}`;
 const app=document.getElementById('app');
 if(!daten.length){app.className='leer';
  app.innerHTML='Nichts zu korrigieren. <a href="/lesen" style=color:#7fb0ff>Runde lesen</a>';
  return}
 app.className='';
 app.innerHTML=daten.map((e,i)=>karte(e,i)).join('');
 zaehler(); markiere();
 document.querySelectorAll('.eintrag').forEach(el=>anbindung(el));
}
function feld(e,n){return e.felder.find(f=>f.name===n)||{}}
function karte(e,i){
 const pers=e.felder.filter(f=>f.rolle);
 return `<div class=eintrag data-i=${i} data-id=${e.id}>
  <div class=kopf><span class=q>Nr. ${esc(e.nr)}</span>
   <span>${e.jahr||''}</span><span style=color:#6f7787>${esc(e.bild||'')}</span>
   <span style=flex:1></span><span class=zaehler>${esc(e.status)}</span></div>
  ${e.ausschnitt?`<div class=bildbox onclick="this.classList.toggle('gross')">
    <img src="/bild/${encodeURI(e.ausschnitt)}" loading=lazy alt="">
    <span class=zh>klicken zum Vergrößern</span></div>`:''}
  ${pers.map(f=>zeilePerson(e,f)).join('')}
  <div class=anbind data-anbind><span class=lbl>Familie</span>
   <span class=hinw>wird ermittelt…</span></div>
  <div class=daten>
   ${datumsfeld(e,'geburt_datum','geb.')}
   ${datumsfeld(e,'tauf_datum','get.')}
   ${datumsfeld(e,'trauung_datum','kop.')}
   ${datumsfeld(e,'sterbe_datum','gest.')}
  </div>
  <div class=mehr><details><summary>weitere Felder</summary>
   ${e.felder.filter(f=>!f.rolle&&!/_datum$/.test(f.name)).map(f=>`
    <div class=zeile><label>${esc(f.name.replace(/_/g,' '))}</label>
     <input data-feld="${esc(f.name)}" value="${esc(f.wert||'')}"
      oninput="this.classList.add('geaendert')">
     <input data-kb="${esc(f.name)}" value="${esc(f.kb_form||'')}"
      placeholder="Kirchenbuchform" oninput="this.classList.add('geaendert')">
    </div>`).join('')}
  </details></div>
  <div class=fuss><button class=ja onclick="fertig(${i})">Fertig · weiter</button>
   <span class=zaehler>Strg+Enter</span></div>
 </div>`;
}
function zeilePerson(e,f){
 const v=f.entscheidung;
 return `<div class="person" data-feld="${esc(f.name)}"
  ${f.person?`data-person="${esc(f.person)}"`:''}>
  <span class=rolle><i class="pkt ${esc(f.ampel||'grau')}"></i> ${esc(f.rolle)}</span>
  <span class=feldbox><input data-feld="${esc(f.name)}" value="${esc(f.wert||'')}"
   autocomplete=off
   oninput="this.classList.add('geaendert');vorschlagen(this)"
   onkeydown="navVorschlag(event,this)"
   onblur="setTimeout(()=>schliesse(this),180)"></span>
  <span>${v==='neu'
    ?`<span class=neu>● wird neu angelegt</span>`
    :f.person
      ?`<span class=treffer><span class=id>${esc(f.person)}</span>
         <span class=warum>${esc(f.beleg||'')}</span></span>`
      :`<span class=neu>○ kein Treffer${f.beleg?' — '+esc(f.beleg):''}</span>`}</span>
  <span class=knopf>
   <button class="${v==='verknuepft'?'ja an':''}" title="find and use"
    onclick="setze(this,'verknuepft')" ${f.person?'':'disabled'}>übernehmen</button>
   <button class="${v==='neu'?'ja an':''}" title="create (Alt+N)"
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
  inhalt=`<span class=hinw>${esc(d.hinweis)} — neue Familie</span>`;
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
 document.getElementById('z').textContent=`${fix} von ${daten.length} bestätigt`;
 if(fix===daten.length&&daten.length)
  document.getElementById('z').innerHTML+=
   ' · <a href="/uebergabe" style=color:#8fe3b4>übergeben</a>';
}
async function fertig(i){
 const el=document.querySelector(`.eintrag[data-i="${i}"]`);
 const felder={};
 el.querySelectorAll('input[data-feld]').forEach(inp=>{
  const n=inp.dataset.feld;
  const kb=el.querySelector(`input[data-kb="${n}"]`);
  const p=inp.closest('.person');
  felder[n]={wert:inp.value,kb:kb?kb.value:null,
             entscheidung:p?(p.dataset.entscheidung||null):null,
             person:p?(p.dataset.person??undefined):undefined};
 });
 const r=await fetch('/api/speichern',{method:'POST',
  headers:{'content-type':'application/json'},
  body:JSON.stringify({id:daten[i].id,felder,bestaetigt:true})});
 if(!r.ok){alert('Speichern fehlgeschlagen');return}
 el.classList.add('fertig');
 daten[i].status='bestaetigt'; zaehler();
 const naechst=daten.findIndex((e,k)=>k>i&&e.status!=='bestaetigt');
 if(naechst>=0){fokus=naechst;markiere();
  document.querySelector(`.eintrag[data-i="${naechst}"]`)
   .scrollIntoView({behavior:'smooth',block:'start'});
  setTimeout(()=>{const f=document.querySelector(
    `.eintrag[data-i="${naechst}"] input`); if(f)f.focus();},350);}
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
  html+='<div class=kopfz>Person übernehmen — find &amp; use</div>';
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
 const el=ev.target.closest?.('.eintrag');
 if(ev.key==='Enter'&&ev.ctrlKey&&el){ev.preventDefault();fertig(+el.dataset.i);return}
 if(ev.key==='Enter'&&el&&ev.target.tagName==='INPUT'){
  ev.preventDefault();
  const alle=[...el.querySelectorAll('input')];
  const k=alle.indexOf(ev.target);
  if(k>=0&&k+1<alle.length) alle[k+1].focus(); else fertig(+el.dataset.i);
  return}
 if(ev.altKey&&(ev.key==='n'||ev.key==='N')){
  const p=ev.target.closest?.('.person');
  if(p){ev.preventDefault();setze(p.querySelector('.knopf button:last-child'),'neu')}}
});
laden();
</script></body></html>"""
