// Random walk through every exam flow, checking invariants after each step.
window.FUZZ_EXAM=async function(steps,seed){
  const t=window.__t, $=id=>document.getElementById(id), w=ms=>new Promise(r=>setTimeout(r,ms));
  let s=seed||7; const rnd=n=>{ s=(s*9301+49297)%233280; return Math.floor(s/233280*n); };
  const problems=new Map(), errs=[];
  const bad=(k,v)=>{ if(!problems.has(k)) problems.set(k,v); };
  const onErr=e=>errs.push(String(e.message||e.reason));
  window.addEventListener('error',onErr); window.addEventListener('unhandledrejection',onErr);
  t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.P.examHist={}; delete t.P.lastPaper;
  const log=[];
  const acts=[
    ['start exam',()=>{ if(!(t.sim&&t.sim.running)) t.startPaper(1+rnd(19),rnd(2)?'exam':'practice'); }],
    ['answer',()=>{ if(t.sim&&t.sim.running&&t.route==='quizScreen'){ const o=[...$('qOpts').children]; if(o.length) o[rnd(o.length)].click(); } }],
    ['answer right',()=>{ if(t.sim&&t.sim.running&&t.route==='quizScreen'){ t.QS[t.sim.qs[t.sim.i]].a.forEach(l=>t.simPick(l)); } }],
    ['next',()=>{ if(t.sim&&t.sim.running&&t.route==='quizScreen') t.simGo(1); }],
    ['prev',()=>{ if(t.sim&&t.sim.running&&t.route==='quizScreen') t.simGo(-1); }],
    ['jump',()=>{ if(t.sim&&t.sim.running) t.simJump(rnd(t.simLen())); }],
    ['tick',()=>{ if(t.sim&&t.sim.running) t.simQTick(rnd(120)); }],
    ['time out',()=>{ if(t.sim&&t.sim.running) t.simQTick(200); }],
    ['nav away',()=>{ ['navHome','navPlay','navExam','navRedo'].map($)[rnd(4)].click(); const g=$('brkAskGo'); if(!$('brkAsk').classList.contains('hidden')&&rnd(2)) g.click(); else if(!$('brkAsk').classList.contains('hidden')) $('brkAskNo').click(); }],
    ['back to paper',()=>{ if(t.sim) t.go('quizScreen'); }],
    ['end break',()=>{ if(t.brkOn()&&!t.brkOpen()) t.brkEnd(true); }],
    ['quit',()=>{ if(t.sim&&t.sim.running) t.simAbandon(); }],
    ['resume',()=>{ if(!(t.sim&&t.sim.running)&&t.simSaved()) t.simResume(); }],
    ['crash+resume',()=>{ if(t.sim&&t.sim.running){ t.simPersist(); t.simResume(); } }],
    ['away 2h',()=>{ if(t.sim&&t.sim.running){ t.simPersist(); t.P.simSave.at-=7200e3; t.simResume(); } }],
    ['submit',()=>{ if(t.sim&&t.sim.running) t.simSubmit(true); }],
    ['finish later',()=>{ if(!(t.sim&&t.sim.running)&&t.lastOpen().length){ t.simClearSave(); t.simContinue(); } }],
    ['redo',()=>{ const ks=Object.keys(t.P.examHist||{}); if(ks.length&&!(t.sim&&t.sim.running)){ t.histOpen(ks[rnd(ks.length)],$('navRedo')); } }],
    ['show answer',()=>{ if(t.isRedo&&t.isRedo()&&t.route==='quizScreen') $('simAnsBtn').click(); }],
    ['to review',()=>{ if(t.sim&&t.sim.running){ t.simJump(t.simLen()-1); t.simGo(1); } }],
    ['running list continue',()=>{ t.renderPapers(); t.go('paperScreen'); const b=[...document.querySelectorAll('#runList .runrow button')]; if(b.length){ const x=b[rnd(b.length)]; x.click(); x.click(); } }],
  ];
  for(let i=0;i<steps;i++){
    const [name,fn]=acts[rnd(acts.length)];
    try{ fn(); }catch(e){ bad('threw in '+name, e.message); }
    await w(3);
    log.push(name); if(log.length>8) log.shift();
    const ctx=' after '+log.join(' > ');
    try{
      if(t.sim){
        if(t.simQLeft<0) bad('negative question clock',ctx);
        if(t.simTotalLeft()<0) bad('negative paper clock',ctx);
        t.sim.qs.forEach((qi,k)=>{ const a=t.sim.ans[k]||[], q=t.QS[qi];
          if(a.length>q.a.length) bad('more picks than the question takes',ctx);
          if(a.some(l=>!q.o.some(o=>o[0]===l))) bad('a pick that is not an option',ctx); });
        if(t.isRedo()&&t.brkOn()) bad('a redo is paused',ctx);
        if(t.sim.running&&t.route==='quizScreen'&&t.brkOn()&&!t.brkOpen()) bad('on the question during a timed break',ctx);
        if(t.sim.running&&t.P.simSave&&t.P.simSave.rid&&t.sim.rid&&t.P.simSave.rid!==t.sim.rid&&t.simOwns(t.P.simSave)) bad('the save is a different run from the one running',ctx);
      }
      if(!t.brkOn()&&!$('brkBar').classList.contains('hidden')) bad('pause bar shown with no pause',ctx);
      const sheets=['modeAsk','brkAsk','studyModal'].filter(id=>!$(id).classList.contains('hidden'));
      if(sheets.length>1) bad('two sheets open',ctx);
      Object.values(t.P.examHist||{}).forEach(e=>{
        if(!(e.sc>=100&&e.sc<=1000)) bad('history score off the scale: '+e.sc,ctx);
        if(e.c>e.n) bad('history: more right than questions',ctx);
        if(Object.keys(e.ans||{}).some(k=>+k>=e.qs.length)) bad('history: an answer past the last question',ctx); });
      // the result screen and the history entry agree on the score
      if(t.route==='simDoneScreen'){
        const shown=parseInt($('simScore').textContent,10);
        const latest=Object.values(t.P.examHist||{}).sort((a,b)=>(b.at||0)-(a.at||0))[0];
        if(latest&&shown&&Math.abs(latest.sc-shown)>1) bad('result screen '+shown+' but history says '+latest.sc,ctx);
      }
      // a redo's live score is its real score
      if(t.sim&&t.sim.running&&t.isRedo()&&t.route==='quizScreen'){
        const live=parseInt($('simLiveVal').textContent,10);
        const pairs=t.sim.qs.map((qi,k)=>{ const q=t.QS[qi], set=new Set(t.sim.ans[k]||[]); return {qi, ok:q.a.length===set.size&&q.a.every(a=>set.has(a))}; });
        const real=t.saaScore(pairs).scaled;
        if(live!==real) bad('redo live score '+live+' but the answers score '+real,ctx);
      }
      // the review screen counts what is really there
      if(t.route==='simRevScreen'&&t.sim){
        const txt=$('simRevSub').textContent, blank=t.simLen()-t.simAnsweredCount();
        if(!new RegExp('\\b'+blank+' blank').test(txt)) bad('review says "'+txt+'" but '+blank+' are blank',ctx);
      }
      const done=new Set(t.P.runsDone||[]);
      Object.values(t.P.runs||{}).forEach(r=>{ if(done.has(t.svRid(r))) bad('a finished run still listed',ctx); });
      if(t.sim&&t.sim.running&&!t.isRedo()&&t.route==='quizScreen'&&$('simTotalVal').textContent==='no timer') bad('"no timer" on a timed paper',ctx);
    }catch(e){ bad('invariant check threw',e.message+ctx); }
  }
  window.removeEventListener('error',onErr); window.removeEventListener('unhandledrejection',onErr);
  ['brkAsk','modeAsk'].forEach(id=>$(id).classList.add('hidden')); document.body.classList.remove('asking');
  if(t.sim&&t.sim.running) t.simAbandon();
  t.simClearSave(); t.P.runs={}; t.P.runsDone=[]; t.P.examHist={}; delete t.P.lastPaper; t.go('homeScreen');
  return {steps, problems:[...problems.entries()].map(([k,v])=>k+' — '+v).slice(0,12), errs:[...new Set(errs)].slice(0,6)};
};
