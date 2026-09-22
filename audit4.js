// Fourth pass: the exam clock and the states around it. Every transition that can start,
// stop, freeze or resume a countdown, checked for the invariants that should always hold.
(function(){
const found=[]; const F=(sev,area,what,ev)=>found.push({sev,area,what,ev:ev||''});
const $=id=>document.getElementById(id);
const t=window.__t;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const scr=()=>{const e=document.querySelector('.screen:not(.hidden)');return e?e.id:'(none)';};

// Invariants that must hold at every moment of a paper.
function invariants(tag){
  if(!t.sim||!t.sim.running) return;
  const onBreak=t.brkOn();
  // 1. the top clock must never show a number that is not moving
  const big=$('playClock').textContent;
  if(onBreak&&/⏳/.test(big))
    F('HIGH','clock',tag+': on a break the clock still shows the exam countdown',big);
  if(!onBreak&&/☕/.test(big))
    F('HIGH','clock',tag+': not on a break but the clock shows a break',big);
  // 2. you cannot stand inside the paper while it is paused
  if(onBreak&&/quizScreen|simRevScreen/.test(scr()))
    F('HIGH','break',tag+': standing inside a paused paper — a frozen clock with no explanation',scr());
  // 3. the question clock and the paper total must agree
  const tot=t.simTotalLeft();
  if(tot>t.simTotalFull()) F('HIGH','clock',tag+': the paper has more time left than it started with',tot+' of '+t.simTotalFull());
  if(tot<0) F('HIGH','clock',tag+': negative time remaining',String(tot));
  if(t.simQLeft>t.SIM_QSEC) F('HIGH','clock',tag+': a question has more than its 90 seconds',String(t.simQLeft));
  if(t.simQLeft<0) F('HIGH','clock',tag+': a question has negative time',String(t.simQLeft));
  // 4. the strip on screen must match the sum
  if(scr()==='quizScreen'&&!$('simTotal').classList.contains('hidden')){
    const shown=$('simTotalVal').textContent;
    const want=(()=>{const s=tot,h=Math.floor(s/3600),m=Math.floor(s%3600/60),ss=s%60;
      return h>0?(h+':'+String(m).padStart(2,'0')+':'+String(ss).padStart(2,'0'))
                :(m+':'+String(ss).padStart(2,'0'));})();
    if(shown!==want) F('MED','clock',tag+': the strip disagrees with the sum','shows '+shown+', is '+want);
  }
  // 5. an interval must exist exactly when one is wanted
  if(!onBreak&&scr()==='quizScreen'&&t.simQLeft>0&&!t.simQIv&&!/test=1/.test(location.search))
    F('HIGH','clock',tag+': the question is live with no interval behind it');
  // 6. breaks cannot go out of range
  const used=t.sim.brkUsed||0;
  if(used<0||used>t.BREAK_MAX) F('HIGH','break',tag+': break count out of range',String(used));
  if(t.brkLeft()<0||t.brkLeft()>t.BREAK_MAX) F('HIGH','break',tag+': breaks left out of range',String(t.brkLeft()));
  if(onBreak&&t.brkRemain()>t.BREAK_SECS) F('MED','break',tag+': a break longer than six minutes',String(t.brkRemain()));
}

// Leaving the paper from every screen it owns, not just the question.
async function leavingPaths(){
  for(const from of ['quizScreen','simRevScreen']){
    t.simClearSave(); t.startPaper(2); await sleep(30);
    if(from==='simRevScreen'){ t.simReview(); await sleep(30); }
    if(scr()!==from){ continue; }
    const usedBefore=t.sim.brkUsed||0;
    $('navHome').click(); await sleep(40);
    const askShown=!$('brkAsk').classList.contains('hidden');
    const left=scr()==='homeScreen';
    if(left&&!t.brkOn())
      F('HIGH','break','leaving from '+from+' walks out of a running paper with no break and the clock running');
    if(!askShown&&!left&&from==='quizScreen')
      F('MED','break','leaving from '+from+' neither asked nor moved');
    t.brkAskClose();
    t.simAbandon(); await sleep(30);
  }
  t.simClearSave();
}

// Walk a paper through every transition, checking the invariants after each.
async function walk(){
  t.simClearSave();
  t.startPaper(3); await sleep(40); invariants('after start');
  t.simGo(1); await sleep(20); invariants('after next');
  t.simJump(7); await sleep(20); invariants('after jump');
  t.simReview(); await sleep(20); invariants('on review');
  t.simJump(2); await sleep(20); invariants('back from review');
  t.simQTick(89); await sleep(20); invariants('one second left');
  t.simQTick(1); await sleep(40); invariants('after a question ran out');
  // a break, and back
  $('navHome').click(); await sleep(20);
  if(!$('brkAsk').classList.contains('hidden')){ $('brkAskGo').click(); await sleep(40); }
  invariants('on a break');
  t.brkEnd(true); await sleep(40); invariants('after the break');
  // abandon and resume
  t.simAbandon(); await sleep(40);
  if(t.sim) F('HIGH','state','abandoning left the paper running');
  if(!$('simTotal').classList.contains('hidden')) F('MED','ui','the paper strip outlived the paper');
  if(!$('brkBar').classList.contains('hidden')&&!t.brkOn()) F('MED','ui','the break banner outlived the break');
  t.simResume(); await sleep(40); invariants('after resuming');
  // submit
  t.simSubmit(true); await sleep(60);
  if(t.sim&&t.sim.running) F('HIGH','state','submitting left the paper running');
  if(!$('simTotal').classList.contains('hidden')) F('MED','ui','the strip survived submitting');
  if(t.simQIv) F('MED','clock','the question interval survived submitting');
  t.simClearSave();
}

// The clock must not drift when the deadline and the counter are pushed around.
async function drift(){
  t.simClearSave(); t.startPaper(4); await sleep(40);
  const left0=t.simQLeft;
  t.simQTick(10); await sleep(10);
  const byDeadline=Math.ceil((t.sim.qEndAt-Date.now())/1000);
  if(Math.abs(byDeadline-t.simQLeft)>1)
    F('HIGH','clock','the counter and the deadline disagree','counter '+t.simQLeft+', deadline '+byDeadline);
  // a save round trip must not change the time
  const before=t.simTotalLeft();
  t.simAbandon(); await sleep(30);
  t.simResume(); await sleep(40);
  const after=t.simTotalLeft();
  if(Math.abs(after-before)>2)
    F('HIGH','clock','saving and resuming changed the time left',before+' -> '+after);
  t.simAbandon(); await sleep(30); t.simClearSave();
}

window.AUDIT4=async function(){
  found.length=0;
  if(!t){ F('HIGH','harness','no test surface'); return {total:1,found}; }
  await walk();
  await leavingPaths();
  await drift();
  t.go('homeScreen');
  const by={HIGH:0,MED:0,LOW:0}; found.forEach(f=>by[f.sev]++);
  console.log('AUDIT4:',found.length,by);
  return {total:found.length,by,found};
};
console.log('AUDIT4 ready');
})();
