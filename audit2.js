// A second, harder audit. The first one looked for dead code and damaged data;
// this one drives the app and looks for what it *shows* being wrong.
(function(){
const found=[];
const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const $=id=>document.getElementById(id);
const t=window.__t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

// ---------------------------------------------------------------- 1. bad numbers on screen
const BADNUM=/\b(NaN|Infinity|-Infinity|undefined|null)\b/;
const BADPLURAL=/\b1 (questions|days|attempts|answers|terms|papers|rounds|minutes|parts|chapters|items|points|coins)\b/;
async function screenSweep(){
  const screens=[...document.querySelectorAll('.screen')].map(e=>e.id);
  for(const id of screens){
    try{ t.go(id); }catch(e){ F('HIGH','router','go("'+id+'") throws',String(e.message)); continue; }
    await sleep(6);
    const el=$(id); if(!el) continue;
    const txt=el.innerText||'';
    let m=BADNUM.exec(txt);
    if(m) F('HIGH','render',id+' shows a broken number or an empty value',JSON.stringify(txt.slice(Math.max(0,m.index-50),m.index+50)));
    m=BADPLURAL.exec(txt);
    if(m) F('LOW','copy',id+' says "'+m[0]+'"');
    // a negative count
    const neg=/(^|\s)-\d+ (questions|days|answers|coins|XP|points)/.exec(txt);
    if(neg) F('MED','render',id+' shows a negative count',neg[0]);
  }
}

// ---------------------------------------------------------------- 2. buttons that do nothing
function deadButtons(){
  const skip=new Set(['authSignIn','authSignUp','authSignOut','authReset','authSyncNow','authNameSave']);
  document.querySelectorAll('.screen button').forEach(b=>{
    if(skip.has(b.id)) return;
    if(b.onclick||b.getAttribute('onclick')) return;
    // a button filled in by script later is fine if it is hidden now
    const hidden=b.closest('.hidden')||b.classList.contains('hidden');
    if(hidden) return;
    if(b.closest('#shopList,#achList,#paperList,#stuList,#lrnPickList,#domList,#planList')) return;
    F('MED','a11y','button #'+(b.id||'(no id)')+' ['+b.textContent.trim().slice(0,22)+'] has no click handler');
  });
}

// ---------------------------------------------------------------- 3. names nothing announces
function unnamed(){
  document.querySelectorAll('button,a[href],input,select').forEach(e=>{
    const name=(e.getAttribute('aria-label')||e.getAttribute('title')||e.textContent||'').trim();
    if(name.length>2) return;
    if(e.tagName==='INPUT'&&(e.labels&&e.labels.length)) return;
    if(e.type==='hidden') return;
    F('MED','a11y','<'+e.tagName.toLowerCase()+' id="'+(e.id||'')+'"> announces nothing');
  });
}

// ---------------------------------------------------------------- 4. timers left running
async function timerLeak(){
  const live=[];
  const realI=window.setInterval, realT=window.setTimeout;
  window.setInterval=function(fn,ms){ const id=realI.apply(window,arguments); live.push({id,ms}); return id; };
  const realCI=window.clearInterval;
  window.clearInterval=function(id){ const k=live.findIndex(x=>x.id===id); if(k>=0) live.splice(k,1); return realCI.apply(window,arguments); };
  const before=live.length;
  t.simClearSave(); t.startPaper(4); await sleep(40);
  $('quizBack').click(); await sleep(60);
  const after=live.length;
  if(after>before) F('MED','leak','leaving an exam leaves '+(after-before)+' interval(s) running',
                     JSON.stringify(live.slice(before).map(x=>x.ms)));
  window.setInterval=realI; window.clearInterval=realCI;
}

// ---------------------------------------------------------------- 5. profile data in innerHTML
function injection(){
  const P=t.P;
  const evil='<img src=x onerror="window.__XSS=1">';
  const keep={};
  ['examDate'].forEach(k=>keep[k]=P[k]);
  try{
    t.myName===undefined;
  }catch(e){}
  // the one field a user types that reaches the DOM
  P.papers=P.papers||{}; P.papers[1]={best:50,tries:1,last:evil};
  try{ t.renderPapers(); }catch(e){}
  if(window.__XSS) F('HIGH','security','a value from the profile is written with innerHTML unescaped','P.papers[n].last');
  delete P.papers[1];
  Object.assign(P,keep);
}

// ---------------------------------------------------------------- 6. state left between modes
async function modeLeak(){
  t.simClearSave();
  t.startPaper(5); await sleep(40);
  t.startSession(3); await sleep(40);
  if(t.sim) F('HIGH','state','starting practice leaves the exam running');
  const bar=$('simBar');
  if(bar&&bar.classList.contains('show')) F('MED','state','the exam bar is still showing in practice');
  if(getComputedStyle($('lifeFifty')).display==='none') F('MED','state','practice lost its lifelines to the exam');
  if(getComputedStyle($('qConfirm')).display==='none') F('HIGH','state','practice has no Lock in button after an exam');
  t.simClearSave();
}

// ---------------------------------------------------------------- 7. study / learn content
function content(){
  const sd=JSON.parse($('studydata').textContent.replace(/<\\\//g,'</'));
  sd.chapters.forEach(c=>{
    if(!c.quiz||!c.quiz.length) F('MED','study',c.nm+' has no check questions');
    (c.quiz||[]).forEach((q,k)=>{
      if(!q.o||q.o.length<2) F('HIGH','study',c.nm+' check '+k+' has fewer than two options');
      if(q.a==null||q.a<0||(q.o&&q.a>=q.o.length)) F('HIGH','study',c.nm+' check '+k+' answer index is out of range');
    });
    c.topics.forEach(tp=>{
      (tp.blocks||[]).forEach(b=>{
        if(b.t==='table'&&(b.rows||[]).some(r=>r.length!==b.head.length))
          F('MED','study',tp.nm+': a table row does not match its header width');
      });
    });
  });
}

window.AUDIT2=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface — load with ?test=1'); return found; }
  await screenSweep();
  deadButtons(); unnamed();
  await timerLeak();
  injection();
  await modeLeak();
  content();
  t.go('homeScreen');
  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT2:',found.length,'findings',by);
  return {total:found.length,by,found};
};
console.log('AUDIT2 ready');
})();
