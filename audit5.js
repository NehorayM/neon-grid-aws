// Fifth pass: the new surfaces under abuse. Rapid taps, states left open across navigation,
// the short paper, and every way the break/voice/resume work can be driven sideways.
(function(){
const found=[]; const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const $=id=>document.getElementById(id);
const t=window.__t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const scr=()=>{const e=document.querySelector('.screen:not(.hidden)');return e?e.id:'(none)';};

// ---------------------------------------------- 1. a sheet must not outlive its context
async function sheetLifetime(){
  t.simClearSave(); t.startPaper(2); await sleep(30);
  $('navHome').click(); await sleep(20);
  if($('brkAsk').classList.contains('hidden')){ F('MED','break','the sheet did not open'); return; }
  // abandoning the paper while the sheet is up
  t.simAbandon(); await sleep(40);
  if(!$('brkAsk').classList.contains('hidden'))
    F('HIGH','break','the break sheet survives the paper being abandoned');
  if(document.body.classList.contains('asking'))
    F('HIGH','ui','the nav stays hidden after the sheet should have closed');
  t.brkAskClose();
  t.simClearSave();

  // and submitting while it is up
  t.startPaper(2); await sleep(30);
  $('navHome').click(); await sleep(20);
  t.simSubmit(true); await sleep(60);
  if(!$('brkAsk').classList.contains('hidden'))
    F('HIGH','break','the break sheet survives the paper being submitted');
  if(document.body.classList.contains('asking'))
    F('HIGH','ui','the nav stays hidden after submitting with the sheet up');
  t.brkAskClose(); t.simClearSave();
}

// ---------------------------------------------- 2. rapid taps must not double anything
async function rapidTaps(){
  t.simClearSave(); t.startPaper(2); await sleep(30);
  $('navHome').click(); await sleep(20);
  // hammering the confirm
  for(let i=0;i<6;i++) $('brkAskGo').click();
  await sleep(60);
  if((t.sim&&t.sim.brkUsed||0)>1)
    F('HIGH','break','hammering the confirm spends more than one break',String(t.sim.brkUsed));
  if(t.brkRemain()>t.BREAK_SECS)
    F('MED','break','a break longer than six minutes after repeated taps',String(t.brkRemain()));
  t.brkEnd(true); await sleep(40);

  // hammering the break request itself
  for(let i=0;i<6;i++){ $('navHome').click(); }
  await sleep(40);
  const open=document.querySelectorAll('#brkAsk:not(.hidden)').length;
  if(open>1) F('MED','ui','more than one sheet at a time',String(open));
  t.brkAskClose();
  t.simAbandon(); await sleep(30); t.simClearSave();
}

// ---------------------------------------------- 3. the short paper, end to end
async function shortPaper(){
  t.simClearSave();
  t.startPaper(t.PAPER_COUNT); await sleep(40);
  const n=t.simLen();
  if(n>=65) F('LOW','paper','the last paper is not short ('+n+')');
  if(t.simTotalLeft()!==n*t.SIM_QSEC)
    F('HIGH','clock','the short paper is budgeted wrong',t.simTotalLeft()+' vs '+n*t.SIM_QSEC);
  // run it to the end by timing out every question
  for(let i=0;i<n+2;i++){ t.simQTick(t.SIM_QSEC); await sleep(4); }
  if(t.sim&&t.sim.running&&t.sim.i>=n)
    F('HIGH','paper','the short paper ran past its last question','i='+t.sim.i);
  if(t.simTotalLeft()<0) F('HIGH','clock','negative time after running it out');
  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave();
}

// ------------------------------------- 4. every question spent, nothing left to do
async function allSpent(){
  t.simClearSave(); t.startPaper(2); await sleep(40);
  const n=t.simLen();
  for(let i=0;i<n;i++){ t.sim.qt[i]=0; }
  t.sim.i=0; t.simQStart&&t.simQStart(); await sleep(20);
  t.renderSimTotal();
  if(t.simQsLeft()!==0) F('MED','clock','questions still count as open with no time on any',String(t.simQsLeft()));
  if(t.simTotalLeft()!==0) F('HIGH','clock','time left with every question spent',String(t.simTotalLeft()));
  const sub=$('simTotalSub').textContent;
  if(/^1 question/.test(sub)&&t.simQsLeft()===0) F('LOW','copy','the strip miscounts at zero',sub);
  if($('simTotalFill').style.width!=='0%') F('MED','ui','the bar is not empty with no time left',$('simTotalFill').style.width);
  t.simAbandon(); await sleep(30); t.simClearSave();
}

// ---------------------------------- 5. the voice screen opened from inside a paper
async function voiceDuringPaper(){
  t.simClearSave(); t.startPaper(2); await sleep(30);
  t.openVoice(); await sleep(30);
  if(scr()==='voiceScreen'&&!t.brkOn()&&t.sim&&t.sim.running)
    F('HIGH','break','the Voice screen walks out of a running paper without a break');
  t.brkAskClose();
  t.simAbandon(); await sleep(30); t.simClearSave();
}

// ---------------------------------- 6. the resume row against a live paper
async function resumeRowStates(){
  t.simClearSave(); t.startPaper(5); await sleep(30);
  t.simGo(1); await sleep(20);
  t.simAbandon(); await sleep(40);
  t.renderPapers(); await sleep(20);
  const rows=[...document.querySelectorAll('#paperScreen .paperrow')];
  const marked=rows.filter(r=>r.classList.contains('resuming'));
  if(marked.length!==1) F('MED','ui','the in-progress row is marked '+marked.length+' times');
  // resume, then check the row no longer offers it while it is running
  const btn=rows[4]&&[...rows[4].querySelectorAll('button')].pop();
  if(btn){ btn.click(); await sleep(50); }
  if(scr()!=='quizScreen') F('MED','ui','resuming from the row did not open the paper',scr());
  t.simAbandon(); await sleep(30); t.simClearSave();
}

// ---------------------------------- 7. answers cannot be given to a paused paper
async function answeringPaused(){
  t.simClearSave(); t.startPaper(2); await sleep(30);
  $('navHome').click(); await sleep(20);
  if(!$('brkAsk').classList.contains('hidden')) $('brkAskGo').click();
  await sleep(40);
  const before=JSON.stringify(t.sim.ans||{});
  const q=t.QS[t.sim.qs[t.sim.i]];
  t.simPick(q.o[0][0]); await sleep(20);
  if(JSON.stringify(t.sim.ans||{})!==before)
    F('MED','break','a paused paper still takes answers');
  t.brkEnd(true); await sleep(40);
  t.simAbandon(); await sleep(30); t.simClearSave();
}

window.AUDIT5=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface'); return {total:1,found}; }
  await sheetLifetime();
  await rapidTaps();
  await shortPaper();
  await allSpent();
  await voiceDuringPaper();
  await resumeRowStates();
  await answeringPaused();
  t.go('homeScreen');
  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT5:',found.length,by);
  return {total:found.length,by,found};
};
console.log('AUDIT5 ready');
})();
