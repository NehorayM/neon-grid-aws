// Third pass: edge-case data, races, and text that does not fit.
(function(){
const found=[]; const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const $=id=>document.getElementById(id);
const t=window.__t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

// -------------------------------------------------- 1. a profile with nothing in it
async function emptyProfile(){
  const keep=JSON.parse(JSON.stringify(t.P));
  Object.keys(t.P).forEach(k=>delete t.P[k]);
  if(t.normaliseProfile) t.normaliseProfile(t.P);   // every real entry path does this
  const screens=['homeScreen','achScreen','shopScreen','readyScreen','recScreen',
                 'pathScreen','bankScreen','themeScreen','sumScreen','logScreen','paperScreen'];
  const rend={achScreen:'renderBadges',shopScreen:'renderShop',bankScreen:'renderBank',
              readyScreen:'renderReadiness',paperScreen:'renderPapers',themeScreen:'renderThemes',
              pathScreen:'renderPath',recScreen:'renderRecords'};
  for(const id of screens){
    try{
      if(rend[id]&&t[rend[id]]) t[rend[id]]();
      t.go(id); await sleep(4);
    }catch(e){ F('HIGH','robust','an empty profile breaks '+id,String(e.message).slice(0,90)); }
  }
  Object.assign(t.P,keep);
}

// -------------------------------------------------- 2. absurd but reachable numbers
async function hugeNumbers(){
  const keep=JSON.parse(JSON.stringify(t.P));
  Object.assign(t.P,{xp:1e15,coins:9e15,answered:1e9,correct:2e9,streak:1e6,bestStreak:1e6,
                     playMs:1e14,gamesPlayed:1e9});
  const draw=()=>['renderDaily','renderChest','renderQuests','renderGoals','renderWeek',
                  'renderSkill','renderReadiness','renderCharge','renderInv']
                  .forEach(fn=>{ if(typeof t[fn]==='function') t[fn](); });
  try{ draw(); }
  catch(e){ F('HIGH','robust','huge counters break the home screen',String(e.message).slice(0,90)); }
  await sleep(10);
  const top=$('topbar').innerText||'';
  if(/e\+\d/.test(top)) F('MED','render','the top bar shows scientific notation',top.slice(0,60));
  if(/NaN|Infinity/.test(top)) F('HIGH','render','the top bar shows NaN or Infinity',top.slice(0,60));
  // more correct than answered
  Object.assign(t.P,{answered:10,correct:40});
  try{ draw(); }catch(e){}
  const body=$('homeScreen').innerText||'';
  const over=/\b(1[0-9][1-9]|1[1-9][0-9]|[2-9][0-9][0-9])%/.exec(body);
  if(over) F('MED','render','an accuracy over 100% reaches the screen',over[0]);
  Object.keys(t.P).forEach(k=>delete t.P[k]); Object.assign(t.P,keep);
  try{ draw(); }catch(e){}
}

// -------------------------------------------------- 3. double taps and spam
async function races(){
  t.simClearSave();
  t.startPaper(6); await sleep(30);
  const q=t.QS[t.sim.qs[0]];
  // spam Next past the end
  for(let i=0;i<80;i++) t.simGo(1);
  await sleep(30);
  if(t.sim&&t.sim.i>=t.simLen()) F('HIGH','exam','spamming Next runs past the last question','i='+t.sim.i);
  t.simClearSave();

  // double submit
  t.startPaper(6); await sleep(30);
  q.a.forEach(l=>t.simPick(l)); await sleep(20);
  const before=t.P.papers?JSON.parse(JSON.stringify(t.P.papers)):{};
  t.simSubmit(true); t.simSubmit(true); t.simSubmit(true); await sleep(60);
  const rec=(t.P.papers||{})[6];
  const was=(before[6]||{tries:0}).tries;
  if(rec&&rec.tries>was+1) F('HIGH','exam','submitting twice records the attempt twice',
                             'tries went '+was+' -> '+rec.tries);
  t.simClearSave();

  // pick more answers than the question wants
  t.startPaper(7); await sleep(30);
  const q2=t.QS[t.sim.qs[0]];
  q2.o.forEach(o=>t.simPick(o[0])); await sleep(20);
  if((t.sim.ans[0]||[]).length>q2.a.length)
    F('HIGH','exam','a question accepts more answers than it asks for',
      (t.sim.ans[0]||[]).length+' picked, needs '+q2.a.length);
  t.simAbandon(); await sleep(20); t.simClearSave();
}

// -------------------------------------------------- 4. text that does not fit
async function overflow(){
  const screens=[...document.querySelectorAll('.screen')].map(e=>e.id);
  const vw=document.documentElement.clientWidth;
  for(const id of screens){
    t.go(id); await sleep(6);
    const el=$(id); if(!el||el.classList.contains('hidden')) continue;
    // A wide table or a chip rail inside a horizontal scroller is SUPPOSED to extend past
    // the viewport — that is what the scroller is for. Only count what nothing can scroll to.
    const scrolled=e=>{
      let p=e.parentElement;
      while(p&&p!==document.body){
        const o=getComputedStyle(p);
        if(/auto|scroll/.test(o.overflowX)&&p.scrollWidth>p.clientWidth+1) return true;
        p=p.parentElement;
      }
      return false;
    };
    el.querySelectorAll('*').forEach(e=>{
      const r=e.getBoundingClientRect();
      if(!r.width||!r.height) return;
      if(r.right>vw+1.5&&!scrolled(e))
        F('MED','layout',id+': '+(e.id||e.className||e.tagName)+' runs past the right edge',
          Math.round(r.right)+' of '+vw);
    });
    if(document.documentElement.scrollWidth>vw+1)
      F('MED','layout',id+' scrolls sideways',document.documentElement.scrollWidth+' of '+vw);
  }
}

// -------------------------------------------------- 5. storage that refuses to write
async function storageFull(){
  const real=localStorage.setItem.bind(localStorage);
  localStorage.setItem=()=>{ const e=new Error('QuotaExceededError'); e.name='QuotaExceededError'; throw e; };
  let threw=null;
  try{ t.P.xp=(t.P.xp||0)+1; t.saveProfile&&t.saveProfile(); await sleep(320); }
  catch(e){ threw=String(e.message); }
  localStorage.setItem=real;
  if(threw) F('MED','robust','a full localStorage throws out of saveProfile',threw.slice(0,70));
}

window.AUDIT3=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface'); return {total:1,found}; }
  await emptyProfile();
  await hugeNumbers();
  await races();
  await overflow();
  await storageFull();
  t.go('homeScreen');
  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT3:',found.length,by);
  return {total:found.length,by,found};
};
console.log('AUDIT3 ready');
})();
