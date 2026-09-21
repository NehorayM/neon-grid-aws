/* Runtime audit: drive everything and record what breaks.
   eval(await (await fetch('/audit_runtime.js')).text()); await AUDIT();
   Findings only — it changes nothing on purpose. */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let F=[];
const add=(sev,area,what,ev)=>F.push({sev,area,what,ev:ev||''});
const T=()=>window.__t;

// every uncaught error during the audit is a finding
const errs=[];
addEventListener('error',e=>errs.push(String(e.message||e.error)));
addEventListener('unhandledrejection',e=>errs.push('promise: '+String(e.reason)));

const SCREENS=()=>[...document.querySelectorAll('.screen')].map(s=>s.id);

// ---------- 1. click every control on every screen, catch what throws ----------
async function clickEverything(){
  const t=T();
  const before=JSON.stringify(t.P).length;
  for(const id of SCREENS()){
    t.go(id); await sleep(12);
    const sc=$(id);
    if(!sc||sc.classList.contains('hidden')) continue;
    const btns=[...sc.querySelectorAll('button,[role="button"],summary,input,select')];
    for(const b of btns){
      if(b.disabled) continue;
      const label=(b.id||b.className||b.tagName)+' on '+id;
      const n=errs.length;
      try{
        if(b.tagName==='INPUT'&&/text|number|date/.test(b.type||'')){
          b.focus(); b.value=b.type==='number'?'999999':'zzz'; b.dispatchEvent(new Event('input',{bubbles:true}));
          b.dispatchEvent(new Event('change',{bubbles:true}));
        } else b.click();
      }catch(e){ add('HIGH','crash',label+' threw on click',String(e.message)); }
      await sleep(6);
      if(errs.length>n) add('HIGH','crash',label+' raised an uncaught error',errs[errs.length-1]);
      // a click must never leave the app with no visible screen
      if(![...document.querySelectorAll('.screen')].some(x=>!x.classList.contains('hidden')))
        add('HIGH','nav',label+' left no screen visible');
      t.go(id); await sleep(6);
    }
  }
  const after=JSON.stringify(t.P).length;
  if(after>before*3) add('MED','state','clicking through the app tripled the saved profile size',
    before+' -> '+after+' bytes');
}

// ---------- 2. state leaks between modes ----------
async function modeLeaks(){
  const t=T();
  const modes=[
    ['practice', ()=>t.startSession(3)],
    ['review',   ()=>{ t.P.wrong=[1,2,3]; t.startReview(); }],
    ['bookmarks',()=>{ t.P.marks=[4,5]; t.startBookmarks(); }],
    ['mock',     ()=>t.startMock()],
    ['paper',    ()=>t.startPaper(2)],
    ['sim',      ()=>t.startSim()],
    ['study drill',()=>t.startStudyMode(2)],
  ];
  for(const [nmA,openA] of modes){
    for(const [nmB,openB] of modes){
      if(nmA===nmB) continue;
      try{ openA(); }catch(e){ add('HIGH','crash','opening '+nmA+' threw',String(e.message)); continue; }
      await sleep(12);
      try{ openB(); }catch(e){ add('HIGH','crash',nmA+' -> '+nmB+' threw',String(e.message)); continue; }
      await sleep(12);
      // only one of sim/mock may be live at a time
      const live=[t.sim?'sim':null, t.mock?'mock':null].filter(Boolean);
      if(live.length>1) add('HIGH','state',nmA+' -> '+nmB+' left two exam engines running',live.join('+'));
      // the exam bar must not be showing outside an exam
      if(!t.sim&&$('simBar').classList.contains('show'))
        add('MED','ui',nmA+' -> '+nmB+' left the exam bar on screen');
      // the briefing must not survive into a mode that has none
      if(!t.sim&&!$('exBrief').classList.contains('hidden'))
        add('MED','ui',nmA+' -> '+nmB+' left the exam briefing on screen');
      if(!t.sim&&!t.mock&&$('explain').classList.contains('show')&&t.route==='quizScreen')
        add('MED','ui',nmA+' -> '+nmB+' left an explanation panel open');
    }
  }
  t.simClearSave&&t.simClearSave(); t.simAbandon&&t.simAbandon();
}

// ---------- 3. empty and first-run states ----------
async function emptyStates(){
  const t=T();
  const P=t.P;
  const keep=JSON.stringify(P);
  Object.keys(P).forEach(k=>{ if(!['coins','xp'].includes(k)) delete P[k]; });
  P.seen={}; P.wrong=[]; P.marks=[]; P.secStats={}; P.study={}; P.papers={};
  const renders=[
    ['renderHome',()=>t.renderHome&&t.renderHome()],
    ['renderPapers',()=>t.renderPapers()],
    ['renderStudyPick',()=>t.STUDY_T.renderStudyPick()],
    ['renderBank',()=>t.renderBank()],
    ['renderRecords',()=>t.renderRecords()],
    ['renderBadges',()=>t.renderBadges()],
    ['renderShop',()=>t.renderShop()],
    ['renderThemes',()=>t.renderThemes()],
    ['renderReadiness',()=>t.renderReadiness()],
    ['renderPath',()=>t.renderPath()],
    ['renderSimLog',()=>t.renderSimLog()],
    ['renderExamLog',()=>t.renderExamLog&&t.renderExamLog()],
    ['renderQuests',()=>t.renderQuests()],
    ['renderBankStats',()=>t.renderBankStats()],
  ];
  for(const [nm,fn] of renders){
    const n=errs.length;
    try{ fn(); }catch(e){ add('HIGH','empty',nm+' throws on a brand-new profile',String(e.message)); }
    await sleep(6);
    if(errs.length>n) add('HIGH','empty',nm+' raised an error on a new profile',errs[errs.length-1]);
  }
  // the modes that need data must refuse politely, not throw
  for(const [nm,fn] of [['startReview',()=>t.startReview()],['startBookmarks',()=>t.startBookmarks()],
                        ['startWeakDrill',()=>t.startWeakDrill()]]){
    const n=errs.length;
    try{ fn(); }catch(e){ add('HIGH','empty',nm+' throws with nothing to show',String(e.message)); }
    await sleep(8);
    if(errs.length>n) add('HIGH','empty',nm+' errored with nothing to show',errs[errs.length-1]);
  }
  Object.assign(P,JSON.parse(keep));
}

// ---------- 4. a corrupted or foreign profile ----------
async function badProfile(){
  const t=T(), P=t.P;
  const keep=JSON.stringify(P);
  const poisons=[
    ['seen as an array',()=>{ P.seen=[]; }],
    ['wrong holding out-of-range indices',()=>{ P.wrong=[999999,-3,'x']; }],
    ['marks holding out-of-range indices',()=>{ P.marks=[999999]; }],
    ['secStats with a bogus sector',()=>{ P.secStats={99:{a:5,c:2}}; }],
    ['papers with a bogus number',()=>{ P.papers={99:{best:50,tries:1,last:'50%'}}; }],
    ['study with a bogus chapter',()=>{ P.study={99:{read:1,best:100}}; }],
    ['a saved exam pointing at dead indices',()=>{ P.simSave={paper:1,qs:[999999],i:0,ans:{},flag:{},left:1000,mins:170}; }],
    ['negative coins',()=>{ P.coins=-50; }],
    ['a huge streak',()=>{ P.streak=1e9; }],
  ];
  for(const [nm,poison] of poisons){
    Object.assign(P,JSON.parse(keep));
    poison();
    const n=errs.length;
    try{
      t.renderHome&&t.renderHome(); t.renderPapers(); t.STUDY_T.renderStudyPick();
      t.renderBank(); t.renderReadiness(); t.renderRecords();
      if(t.simSaved&&t.simSaved()) t.simResume();
    }catch(e){ add('HIGH','robust','a profile with '+nm+' throws',String(e.message)); }
    await sleep(10);
    if(errs.length>n) add('HIGH','robust','a profile with '+nm+' raised an error',errs[errs.length-1]);
    if(t.sim){ t.simAbandon(); await sleep(8); }
  }
  Object.assign(P,JSON.parse(keep));
  t.simClearSave&&t.simClearSave();
}

// ---------- 5. rapid and repeated interaction ----------
async function rapidFire(){
  const t=T();
  t.startPaper(3); await sleep(15);
  const n=errs.length;
  for(let i=0;i<40;i++){ t.simGo(1); }
  await sleep(20);
  if(errs.length>n) add('HIGH','crash','hammering Next inside an exam raised an error',errs[errs.length-1]);
  if(t.sim&&t.sim.i>=t.sim.qs.length) add('HIGH','exam','Next ran past the last question, index '+t.sim.i);
  for(let i=0;i<40;i++){ t.simGo(-1); }
  await sleep(20);
  if(t.sim&&t.sim.i<0) add('HIGH','exam','Prev ran before the first question, index '+t.sim.i);
  // double submit
  const m=errs.length;
  t.simSubmit(true); t.simSubmit(true); await sleep(30);
  if(errs.length>m) add('HIGH','exam','submitting twice raised an error',errs[errs.length-1]);
  const tries=(t.paperRec(3)||{tries:0}).tries;
  if(tries>1) add('HIGH','exam','submitting twice recorded the paper twice, tries='+tries);
  t.simClearSave();

  // double-start
  const k=errs.length;
  t.startPaper(4); t.startPaper(4); await sleep(20);
  if(errs.length>k) add('HIGH','exam','starting a paper twice raised an error',errs[errs.length-1]);
  t.simAbandon(); await sleep(10); t.simClearSave();

  // rapid navigation
  const j=errs.length;
  for(let i=0;i<30;i++){ t.go(SCREENS()[i%SCREENS().length]); }
  await sleep(30);
  if(errs.length>j) add('HIGH','nav','rapid screen switching raised an error',errs[errs.length-1]);
}

// ---------- 6. timers and intervals ----------
async function timerLeaks(){
  const t=T();
  const live=()=>{
    let n=0; const id=setTimeout(()=>{},0); clearTimeout(id);
    return id;          // ids grow monotonically; a jump means many were created
  };
  const a=live();
  t.startPaper(5); await sleep(20);
  t.simAbandon(); await sleep(20);
  t.startPaper(5); await sleep(20);
  t.simAbandon(); await sleep(20);
  const b=live();
  if(b-a>400) add('MED','perf','opening and closing an exam creates a lot of timers',(b-a)+' ids consumed');
  t.simClearSave();
  // the question timer must not keep ticking once you leave the quiz
  t.startSession(1); await sleep(15);
  t.go('homeScreen'); await sleep(15);
  if(typeof t.qLeft==='number'){
    const first=t.qLeft; await sleep(1100);
    if(t.qLeft<first-0.5) add('MED','timer','the question countdown keeps running after leaving the quiz');
  }
}

// ---------- 7. the exam contract ----------
async function examContract(){
  const t=T();
  // a paper must never repeat a question, and papers must not overlap
  const seen=new Set();
  for(let n=1;n<=t.PAPER_COUNT;n++){
    const qs=t.paperQs(n);
    if(new Set(qs).size!==qs.length) add('HIGH','exam','paper '+n+' repeats a question');
    qs.forEach(i=>{ if(seen.has(i)) add('HIGH','exam','question '+i+' is in two papers'); seen.add(i); });
  }
  if(seen.size!==t.QS.length) add('HIGH','exam','the papers do not cover the bank: '+seen.size+' of '+t.QS.length);
  // the timer
  t.startPaper(6); await sleep(15);
  if(Math.abs(t.simTimeLeft()-t.PAPER_MIN*60000)>3000) add('HIGH','exam','a paper does not start at '+t.PAPER_MIN+' minutes');
  // a multi-answer question must not accept more than it needs
  const multi=t.sim.qs.findIndex(qi=>t.QS[qi].a.length>1);
  if(multi>=0){
    t.simJump(multi); await sleep(10);
    const q=t.QS[t.sim.qs[multi]];
    q.o.forEach(o=>t.simPick(o[0]));
    await sleep(10);
    if((t.sim.ans[multi]||[]).length>q.a.length)
      add('HIGH','exam','a multi-answer question accepted '+(t.sim.ans[multi]||[]).length+' of '+q.a.length+' picks');
  } else add('LOW','exam','paper 6 has no multi-answer question to test');
  t.simAbandon(); await sleep(10); t.simClearSave();
}

// ---------- 8. responsive ----------
async function responsive(){
  const t=T();
  const widths=[320,360,375,414,768,1024,1440];
  const realW=innerWidth;
  for(const w of widths){
    // we cannot resize the window from script; measure against the CSS instead
    const probe=document.createElement('div');
    probe.style.cssText='position:fixed;left:0;top:0;width:'+w+'px;height:1px;pointer-events:none;opacity:0';
    document.body.appendChild(probe);
    probe.remove();
  }
  // the only thing we can honestly check here is that nothing hard-codes a width
  // wider than the smallest phone
  const wide=[];
  [...document.querySelectorAll('.screen *')].forEach(el=>{
    const st=getComputedStyle(el);
    const mw=parseFloat(st.minWidth);
    if(mw&&mw>320) wide.push((el.id||el.className)+' min-width:'+st.minWidth);
  });
  [...new Set(wide)].slice(0,8).forEach(w=>add('MED','responsive','a min-width wider than a 320px phone: '+w));
  if(realW) add('LOW','responsive','audited at '+realW+'px; run again at other widths for full coverage');
}

// ---------- 9. content and copy ----------
async function copyChecks(){
  const t=T();
  // numbers in the interface that should match the data
  t.go('homeScreen'); t.renderHome&&t.renderHome(); await sleep(10);
  const flash=$('flashOpen');
  if(flash&&t.CODEX_KEYS){
    const m=flash.textContent.match(/(\d+)\s*AWS terms/);
    if(m&&+m[1]!==t.CODEX_KEYS.length)
      add('MED','copy','the Flashcards tile says '+m[1]+' terms but the deck has '+t.CODEX_KEYS.length);
  }
  const mock=$('mockOpen');
  if(mock&&t.MOCK_LEN){
    const m=mock.textContent.match(/(\d+)\s*Q/);
    if(m&&+m[1]!==t.MOCK_LEN)
      add('MED','copy','the Mock exam tile says '+m[1]+' questions but MOCK_LEN is '+t.MOCK_LEN);
  }
  // sector counts on the home grid must match the bank
  const cards=[...document.querySelectorAll('#secGrid .seccard')].slice(1);
  cards.forEach((c,i)=>{
    const m=c.textContent.match(/(\d+) questions/);
    const real=(t.bySec[i]||[]).length;
    if(m&&+m[1]!==real) add('MED','copy','sector '+i+' card says '+m[1]+' questions, bank has '+real);
  });
}

// ---------- 10. accessibility of what is actually rendered ----------
async function a11y(){
  const t=T();
  const noName=new Set();
  for(const id of SCREENS()){
    t.go(id); await sleep(8);
    const sc=$(id); if(!sc||sc.classList.contains('hidden')) continue;
    sc.querySelectorAll('button').forEach(b=>{
      const txt=(b.textContent||'').trim();
      const name=b.getAttribute('aria-label')||b.getAttribute('title')||txt;
      if(!name) noName.add((b.id||b.className)+' on '+id);
      else if(name.length<=2&&!b.getAttribute('aria-label')&&!b.getAttribute('title'))
        noName.add((b.id||b.className)+' on '+id+' (only "'+name+'")');
    });
    // focus order: a screen with no focusable element traps keyboard users
    if(!sc.querySelector('button,a,input,select,textarea,[tabindex]'))
      add('MED','a11y',id+' has nothing focusable');
  }
  [...noName].slice(0,12).forEach(n=>add('MED','a11y','button with no accessible name: '+n));
  if(noName.size>12) add('MED','a11y',(noName.size-12)+' further buttons with no accessible name');
  if(!document.documentElement.lang) add('MED','a11y','<html> has no lang');
  const h1=document.querySelectorAll('h1').length;
  if(h1!==1) add('LOW','a11y','the page has '+h1+' h1 elements');
}

window.AUDIT=async function(opts){
  opts=opts||{};
  F=[]; errs.length=0;
  const t=T();
  if(!t){ console.error('load with ?test=1'); return; }
  const keep=JSON.stringify(t.P);
  const steps=[['click every control',clickEverything],['mode leaks',modeLeaks],
    ['empty states',emptyStates],['bad profiles',badProfile],['rapid fire',rapidFire],
    ['timer leaks',timerLeaks],['exam contract',examContract],['responsive',responsive],
    ['copy',copyChecks],['a11y',a11y]];
  for(const [nm,fn] of steps){
    if(opts.only&&opts.only!==nm) continue;
    try{ await fn(); }catch(e){ add('HIGH','audit','the "'+nm+'" pass itself threw',String(e.message)); }
  }
  Object.assign(t.P,JSON.parse(keep));
  t.go('homeScreen');
  const by={HIGH:[],MED:[],LOW:[]};
  F.forEach(f=>by[f.sev].push(f));
  console.log('AUDIT:',F.length,'findings —',by.HIGH.length,'high,',by.MED.length,'med,',by.LOW.length,'low');
  return {n:F.length, high:by.HIGH, med:by.MED, low:by.LOW, errors:[...new Set(errs)]};
};
console.log('AUDIT ready');
})();
