// Seventh pass: the modes around the paper, and what repeated use leaves behind.
(function(){
const found=[]; const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const $=id=>document.getElementById(id);
const t=window.__t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const scr=()=>{const e=document.querySelector('.screen:not(.hidden)');return e?e.id:'(none)';};

// ------------------------------------- 1. booting back into a paper that is on a break
async function bootDuringBreak(){
  t.simClearSave(); t.startPaper(2); await sleep(30);
  $('navHome').click(); await sleep(20);
  if(!$('brkAsk').classList.contains('hidden')) $('brkAskGo').click();
  await sleep(40);
  if(!t.brkOn()){ F('MED','break','could not start a break to test the boot path'); return; }
  t.simPersist();
  const sv=JSON.parse(JSON.stringify(t.P.simSave));
  t.simAbandon(); await sleep(30);
  // put the save back exactly as a reload would find it, mid-break
  t.P.simSave=sv; t.P.simSave.paused=0;
  t.simResume(); await sleep(60);
  if(t.brkOn()&&/quizScreen|simRevScreen/.test(scr()))
    F('HIGH','break','booting back in lands inside a paused paper',scr());
  if(t.sim&&t.sim.running&&!t.brkOn()&&scr()!=='quizScreen')
    F('MED','break','the break ended but the paper did not open',scr());
  t.brkEnd&&t.brkEnd(true); await sleep(40);
  t.simAbandon(); await sleep(30); t.simClearSave();
}

// ------------------------------- 2. repeated navigation must not accumulate anything
async function leaks(){
  const live=[];
  const realI=window.setInterval, realCI=window.clearInterval;
  window.setInterval=function(fn,ms){ const id=realI.apply(window,arguments); live.push(id); return id; };
  window.clearInterval=function(id){ const k=live.indexOf(id); if(k>=0) live.splice(k,1); return realCI.apply(window,arguments); };
  const before=live.length;
  for(let i=0;i<6;i++){
    t.simClearSave(); t.startPaper(2); await sleep(20);
    t.simGo(1); await sleep(10);
    t.simAbandon(); await sleep(20);
    t.go('homeScreen'); await sleep(10);
  }
  const after=live.length;
  window.setInterval=realI; window.clearInterval=realCI;
  if(after>before+1)
    F('HIGH','leak','six paper start/quit cycles left '+(after-before)+' intervals running');
  t.simClearSave();
}

// ------------------- 3. the shop and the inventory. Everything is free by design, so the
// question is not whether it charges but whether counts can be driven out of range.
function shop(){
  if(typeof t.buyCons!=='function'||typeof t.usePotion!=='function'){
    F('HIGH','harness','shop internals still not exposed — this probe would do nothing'); return; }
  const keep=JSON.parse(JSON.stringify(t.P));
  t.P.coins=0; t.P.inv={}; t.P.upgrades={};
  (t.STORE_CONS||[]).forEach(it=>{ try{ t.buyCons(it); }catch(e){ F('MED','shop','buying '+it.id+' throws',e.message); } });
  if(t.P.coins<0) F('HIGH','shop','coins went negative',String(t.P.coins));
  (t.STORE_CONS||[]).forEach(it=>{
    const n=t.invCount(it.id);
    if(!isFinite(n)||n<0) F('HIGH','shop',it.id+' has an impossible count',String(n));
  });
  // consuming more than you hold must not go below zero
  t.P.inv={potion:1,freeze:1};
  for(let i=0;i<5;i++){ try{ t.usePotion(); t.useFreeze(); }catch(e){ F('MED','shop','using an item throws',e.message); break; } }
  if(t.invCount('potion')<0) F('HIGH','shop','potions went negative',String(t.invCount('potion')));
  if(t.invCount('freeze')<0) F('HIGH','shop','freezes went negative',String(t.invCount('freeze')));
  if((t.P.potionLeft||0)<0) F('MED','shop','potionLeft went negative',String(t.P.potionLeft));
  // an empty inventory refuses rather than throwing
  t.P.inv={};
  if(t.usePotion()!==false) F('MED','shop','using a potion you do not have does not refuse');
  if(t.useFreeze()!==false) F('MED','shop','using a freeze you do not have does not refuse');
  Object.keys(t.P).forEach(k=>delete t.P[k]); Object.assign(t.P,keep);
}

// ---------------------------------- 4. every mode can be entered and left cleanly
async function modeTour(){
  const modes=[
    ['practice',()=>t.startSession(1)],
    ['review',()=>{ t.P.wrong=[0,1,2]; t.startReview(); }],
    ['bookmarks',()=>{ t.P.marks=[0,1]; t.startBookmarks&&t.startBookmarks(); }],
    ['mock',()=>t.startMock()],
    ['paper',()=>t.startPaper(2)],
  ];
  for(const [nm,go] of modes){
    try{ go(); }catch(e){ F('MED','mode',nm+' will not start',e.message); continue; }
    await sleep(30);
    if(scr()!=='quizScreen'){ F('MED','mode',nm+' did not open the question screen',scr()); continue; }
    // the question screen must be coherent whatever put it there
    if(!$('qText').textContent.trim()) F('HIGH','mode',nm+': the question is blank');
    if(!$('qOpts').children.length) F('HIGH','mode',nm+': no options rendered');
    const lock=getComputedStyle($('qConfirm')).display!=='none';
    const bar=$('simBar').classList.contains('show');
    if(nm==='paper'&&lock) F('MED','mode','a paper still shows Lock in');
    if(nm!=='paper'&&bar) F('HIGH','mode',nm+' shows the exam bar');
    if(nm!=='paper'&&!lock) F('HIGH','mode',nm+' has no way to submit an answer');
    t.go('homeScreen'); await sleep(20);
  }
  t.simClearSave();
}

// --------------------------------- 5. switching theme leaves the page usable
async function themes(){
  if(!t.applyTheme){ F('LOW','harness','applyTheme not exposed'); return; }
  const keep=t.P.theme;
  const ids=(t.THEME_LIST||[]).map(x=>x.id);
  if(!ids.length){ F('HIGH','harness','the theme list is not exposed — this probe would do nothing'); return; }
  const list=ids;
  for(const id of list){
    try{ t.applyTheme(id); }catch(e){ F('MED','theme',id+' throws',e.message); continue; }
    await sleep(8);
    const bg=getComputedStyle(document.body).backgroundColor;
    if(!bg||bg==='rgba(0, 0, 0, 0)') F('MED','theme',id+' leaves the page with no background');
    const txt=getComputedStyle(document.body).color;
    if(txt===bg) F('HIGH','theme',id+' renders text the same colour as the background',bg);
  }
  t.applyTheme(keep||'neon');
}

// ------------------------- 6. the boot resume must not fight the other modes
async function bootVsModes(){
  t.simClearSave(); t.startPaper(3); await sleep(30);
  t.simPersist(); t.P.simSave.paused=0;
  t.simAbandon(); await sleep(30);
  // something else takes the question screen first, then the save is still sitting there
  t.startSession(2); await sleep(30);
  if(t.sim) F('HIGH','state','practice is running with a paper alongside it');
  t.resumeOnBoot&&t.resumeOnBoot();
  await sleep(40);
  if(t.sim&&t.sim.running&&scr()!=='quizScreen')
    F('MED','state','a boot resume left the paper running off-screen',scr());
  t.simAbandon&&t.simAbandon(); await sleep(20); t.simClearSave();
}

window.AUDIT7=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface'); return {total:1,found}; }
  await bootDuringBreak();
  await leaks();
  shop();
  await modeTour();
  await themes();
  await bootVsModes();
  t.go('homeScreen');
  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT7:',found.length,by);
  return {total:found.length,by,found};
};
console.log('AUDIT7 ready');
})();
