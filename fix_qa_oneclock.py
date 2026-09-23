#!/usr/bin/env python3
"""Three checks asserted the two-clock rule that ended papers early. They assert the fix.

  timeoutCheck   ended a paper by pushing the hidden wall clock past zero. A paper now ends
                 when its questions are out of time, so that is what it drains.
  breakChecks    required the paper's wall clock to be "paid back" six minutes after a break.
                 With one clock a break costs the paper nothing in the first place.
  the amber strip  went amber when the hidden clock became the binding one — the exact trap.
                 It now goes amber in the last five minutes with something still unanswered.

Plus standing checks for the bug itself and for finishing a paper later.

Run once; qa_bank.js is the source of truth afterwards.
"""
import pathlib
QA = pathlib.Path(__file__).resolve().parent / "qa_bank.js"
s = QA.read_text(encoding="utf-8")

def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)

sub("""  t.sim.endAt=Date.now()-1;            // pretend the clock ran out
  t.simCheckTime(); await sleep(40);""",
"""  // a paper runs out when its questions do — the only clock it has
  t.sim.qs.forEach((q,i)=>{ t.sim.qt[i]=0; });
  t.simQTick(t.SIM_QSEC); await sleep(20);
  t.simCheckTime(); await sleep(40);""")

sub("""  const wallAfter=Math.round(t.simTimeLeft()/1000);
  ok(Math.abs((wallAfter-wallBefore)-360)<5,
     'the paper budget is paid back the full six minutes ('+(wallAfter-wallBefore)+'s)');""",
"""  const wallAfter=Math.round(t.simTimeLeft()/1000);
  // With one clock a break never cost the paper anything to pay back: it is not answering time.
  ok(Math.abs(wallAfter-wallBefore)<3,
     'the break cost the paper nothing ('+(wallAfter-wallBefore)+'s)');""")

sub("""  t.sim.endAt=Date.now()+60*1000; t.renderSimTotal();
  ok(totBox.classList.contains('tight'),'it warns when the paper clock becomes the binding one');
  ok(/own clock is what runs out/.test($('simTotalSub').textContent),'and says why');
  t.sim.endAt=Date.now()+99*60*1000; t.renderSimTotal();
  ok(!totBox.classList.contains('tight'),'and calms down again');""",
"""  // the amber is for the last five minutes, not for a second clock that used to take over
  const qtWas=Object.assign({},t.sim.qt);
  t.sim.qs.forEach((q,i)=>{ if(i!==t.sim.i) t.sim.qt[i]=0; }); t.renderSimTotal();
  ok(totBox.classList.contains('tight'),'it warns in the last five minutes');
  ok(!/own clock/.test($('simTotalSub').textContent),'and there is no second clock to blame');
  t.sim.qt=qtWas; t.renderSimTotal();
  ok(!totBox.classList.contains('tight'),'and calms down again');""")

sub("""async function saveFlushChecks(){""",
"""// The paper ended on a hidden wall clock that kept running while no question clock did — an
// explanation, the review grid, a practice paper in a background tab — and cut Exam 5 off part
// way with half an hour still showing. It has one clock now.
async function oneClockChecks(){
  const t=T();
  const realNow=Date.now; let skew=0; Date.now=()=>realNow()+skew;
  try{
    t.simClearSave(); t.startPaper(5,'exam'); await sleep(30);
    ok(t.simTeaches(),'a teaching paper, where an explanation follows every answer');
    let endedAt=-1;
    for(let k=0;k<t.simLen();k++){
      skew+=60000; t.simQTick(60);                        // a minute on the question
      t.QS[t.sim.qs[t.sim.i]].a.forEach(l=>t.simPick(l));
      skew+=60000; t.simCheckTime();                       // a minute reading the explanation
      if(!t.sim||!t.sim.running){ endedAt=k+1; break; }
      if(k<t.simLen()-1) t.simGo(1);
    }
    eq(endedAt,-1,'reading every explanation for a minute does not end the paper early');
    ok(t.sim&&t.simAnsweredCount()===t.simLen(),'all '+t.simLen()+' questions got answered');
    eq(t.simTimeLeft(),t.simTotalLeft()*1000,'the clock the paper ends on is the clock on screen');
    t.simSubmit(true); await sleep(40);
    ok(/ 65 min /.test(' '+document.getElementById('simMeta').textContent+' '),
       'and the result reports time spent answering, not wall time: '+document.getElementById('simMeta').textContent);
  } finally { Date.now=realNow; }
  // a practice paper left in a closed tab is not charged — it is how you stop on a phone
  t.simClearSave(); t.startPaper(6,'practice'); await sleep(30);
  t.simPersist();
  const sv=JSON.parse(JSON.stringify(t.P.simSave)); sv.at-=14*3600*1000;
  eq(t.simAwayCost(sv),0,'fourteen hours away from a practice paper costs nothing');
  t.simAbandon(); await sleep(20); t.simClearSave();
  // a simulation still pays for time away in full, from the question you were on and then the end
  t.startPaper(7,'exam'); await sleep(30);
  t.simQTick(20); t.simPersist();
  const full0=t.simTotalLeft();
  t.P.simSave.at-=10*60*1000;
  t.simResume(); await sleep(30);
  ok(Math.abs((full0-t.simTotalLeft())-600)<5,'ten minutes away from a simulation costs it ten minutes');
  eq(t.sim.qt[t.sim.qs.length-1],0,'taken from the end of the paper');
  ok(t.simQLeft===t.SIM_QSEC,'not from the question you come back to');
  t.simAbandon(); await sleep(20); t.simClearSave();
  // a spent save is scored, not dropped
  t.startPaper(8,'exam'); await sleep(30);
  t.QS[t.sim.qs[0]].a.forEach(l=>t.simPick(l));
  t.simPersist();
  t.P.simSave.at-=10*3600*1000;
  ok(!!t.simSaved(),'a simulation whose time ran out while saved is still there to resume');
  t.simResume(); await sleep(60);
  eq(t.route,'simDoneScreen','and resuming it scores what was answered');
  t.simClearSave(); delete t.P.lastPaper;
}
// Finishing a paper later: the questions nobody reached are answerable, the earlier answers
// are locked, and nothing is counted twice.
async function continueChecks(){
  const t=T(), $=id=>document.getElementById(id);
  delete t.P.lastPaper; t.simClearSave();
  t.startPaper(14,'exam'); await sleep(30);
  for(let k=0;k<6;k++){ t.simJump(k); await sleep(2); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simSubmit(true); await sleep(50);
  ok(!$('simCont').classList.contains('hidden'),'a paper ended with questions left offers to finish them');
  ok(/59 left/.test($('simCont').textContent),'and says how many');
  const was={answered:t.P.answered, exams:t.P.exams, tries:t.P.papers[14].tries, correct:t.P.correct};
  t.renderPapers(); await sleep(10);
  const fin=[...document.querySelectorAll('#paperScreen .paperrow')][13].querySelector('button');
  ok(/59/.test(fin.textContent),'the paper\\u2019s row in the exam list offers it too');
  $('simCont').click(); await sleep(40);
  eq(t.route,'quizScreen','finishing reopens the paper');
  eq(t.sim.i,6,'on the first question nobody reached');
  ok(t.isPractice(),'under practice rules, since the answers have been shown');
  t.simJump(0); await sleep(5);
  const a0=t.sim.ans[0].join(), q0=t.QS[t.sim.qs[0]];
  t.simPick(q0.o.map(x=>x[0]).find(l=>!t.sim.ans[0].includes(l))); await sleep(5);
  eq(t.sim.ans[0].join(),a0,'an answer from the first sitting is locked');
  for(let k=6;k<16;k++){ t.simJump(k); await sleep(2); t.QS[t.sim.qs[k]].a.forEach(l=>t.simPick(l)); }
  t.simPersist();
  eq(JSON.stringify(t.P.simSave.locked),JSON.stringify(t.sim.locked),'the lock survives a refresh');
  t.simSubmit(true); await sleep(50);
  eq(t.P.answered,was.answered,'finishing later is not another sixty-five answered');
  eq(t.P.correct-was.correct,10,'only the newly right answers are added');
  eq(t.P.exams,was.exams,'nor another exam');
  eq(t.P.papers[14].tries,was.tries,'nor another attempt');
  eq(t.P.papers[14].bestMode,'practice','and the score is marked as practice');
  eq((t.P.simLog[0]||{}).ct,1,'the history says it was finished later');
  const g={simLog:[{d:'2026-09-20',p:40,pass:0,mins:30,pr:1,ct:1,dom:[1,2,3,4]}]}; t.normaliseProfile(g);
  eq(g.simLog[0].ct,1,'and that survives the load door');
  delete t.P.lastPaper; t.simClearSave();
}
async function saveFlushChecks(){""")

sub("await saveFlushChecks(); await pickCapChecks();",
    "await saveFlushChecks(); await pickCapChecks(); await oneClockChecks(); await continueChecks();")

QA.write_text(s, encoding="utf-8")
print("tests assert one clock")
