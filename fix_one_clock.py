#!/usr/bin/env python3
"""The exam has one clock now: the one on screen.

A paper ran two clocks with the same 97.5-minute budget. The big PAPER REMAINING number was
the sum of the 65 question clocks — but the paper actually ended on a separate wall clock,
started with the paper, that kept running whenever no question clock was: reading the
explanation after answering on a teaching paper, sitting on the review grid, a practice paper
left in a background tab. Measured: answering in 20 s and reading for 40 s, after 20
questions the wall clock had 78 minutes left while the questions still held 90.8. At a slower
pace the wall clock runs out around question 49 with half an hour still showing. That is
Exam 5 ending at 98 minutes part-way through. The practice paper in the history at 872 min
and 2% is the same clock: left in a background tab, the question clock paused (practice) and
the wall clock did not, and it submitted itself overnight.

  - The paper ends when its questions are out of time, or when it is submitted. Time in the
    app but off a question — an explanation, the review grid, a break, a practice pause — is
    not answering time and costs nothing.
  - A simulation still pays for time AWAY from the app in full, so a closed tab is no freeze
    (the refresh fix stands). The question you were on runs while you are gone; anything
    beyond it comes off the END of the paper, unanswered questions last-first — the way a real
    exam's clock leaves you short at the end rather than draining the question you come back
    to. Before, only the current question was charged and the wall clock did the rest.
  - A practice paper is not charged for time away at all — closing the app on a phone is the
    most natural way to stop, and practice is where you are allowed to.
  - A saved paper whose time is spent used to be dropped by simSaved(), answers and all. It is
    kept, and resuming it scores what was answered.
  - "98 min" on the result was wall time since the start, pauses included. It is now the time
    actually spent on questions.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")

def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)

# ---- the clock the paper ends on is the clock on screen ----------------------------
sub("""function simTimeLeft(){ return sim?Math.max(0,sim.endAt-Date.now()):0; }""",
"""// The paper ends when its questions are out of time — the number on screen. It used to end on
// a separate wall clock that kept running whenever no question clock was (an explanation, the
// review grid, a practice paper in a background tab), hit zero with question time still
// showing, and submitted the paper under you.
function simTimeLeft(){ return sim?simTotalLeft()*1000:0; }""")

sub("""  const byQuestion=simTotalLeft(), full=simTotalFull(), qs=simQsLeft();
  const wms=(typeof simTimeLeft==='function')?simTimeLeft():Infinity;
  const byWall=isFinite(wms)?Math.floor(wms/1000):Infinity;
  // Two true numbers: what the questions still hold, and what the paper's own clock has left.
  // The headline has to be whichever runs out first, or it contradicts its own subtitle —
  // "1:36:00" sitting above "the paper clock runs out first, 1:16:12".
  const left=Math.min(byQuestion,byWall);
  $('simTotalVal').textContent=fmtClock(left*1000);
  $('simTotalFill').style.width=pctW(left/Math.max(1,full)*100);
  $('simTotalSub').textContent=(byWall<byQuestion)
    ? ('the paper\\u2019s own clock is what runs out \\u2014 the questions still hold '+
       fmtClock(byQuestion*1000))
    : (plural(qs,'question')+' still open \\u00b7 '+SIM_QSEC+'s each \\u00b7 '+
       fmtClock(full*1000)+' for the paper');""",
"""  const left=simTotalLeft(), full=simTotalFull(), qs=simQsLeft();
  // One clock. This number is the one the paper ends on.
  $('simTotalVal').textContent=fmtClock(left*1000);
  $('simTotalFill').style.width=pctW(left/Math.max(1,full)*100);
  $('simTotalSub').textContent=plural(qs,'question')+' still open \\u00b7 '+SIM_QSEC+'s each \\u00b7 '+
       fmtClock(full*1000)+' for the paper';""")

sub("""  // Amber when the PAPER's wall clock, not the per-question budget, becomes the binding
  // constraint — that is the only way you can be cut off with question time still on the
  // board. Comparing against qs*90 was useless: it goes amber the moment you spend a second.
  box.classList.toggle('tight',byWall<byQuestion);""",
"""  // Amber in the last five minutes, while there is still something unanswered to spend it on.
  // (It used to mark the second, hidden clock taking over — the thing that is gone now.)
  box.classList.toggle('tight',left<300&&simAnsweredCount()<simLen());""")

# ---- the save carries the same number -----------------------------------------------
sub("""             left:Math.max(0,sim.endAt-Date.now()), mins:sim.mins||SIM_MIN, at:Date.now(),""",
    """             left:simTotalLeft()*1000, mins:sim.mins||SIM_MIN, at:Date.now(),""")

# ---- time away: practice free, simulation charged in full ---------------------------
sub("""  if(sv.brkOpen) return 0;   // an open-ended pause covers all of it, however long it ran""",
"""  if(sv.brkOpen) return 0;   // an open-ended pause covers all of it, however long it ran
  // Practice is where you are allowed to stop, and closing the app is the natural way to.
  if(sv.mode==='practice') return 0;""")

sub("""function simClearSave(){""",
"""// Time away from a simulation is charged in full. The question you were on ran while you were
// gone; anything beyond it comes off the END of the paper — unanswered questions, last first —
// the way a real exam's clock leaves you short at the end instead of draining the question you
// come back to. Answered questions give up their leftover only once nothing unanswered is left.
function simChargeEnd(sec,except){
  if(!sim||!(sec>0)) return 0;
  sim.qt=sim.qt||{};
  let owe=sec;
  const has=i=>(typeof sim.qt[i]==='number')?Math.max(0,sim.qt[i]):SIM_QSEC;
  const take=i=>{ const v=has(i), d=Math.min(v,owe); sim.qt[i]=v-d; owe-=d; };
  const blank=i=>!(sim.ans[i]||[]).length;
  for(let i=simLen()-1;i>=0&&owe>0;i--) if(i!==except&&blank(i)) take(i);
  for(let i=simLen()-1;i>=0&&owe>0;i--) if(i!==except) take(i);
  return sec-owe;
}
function simClearSave(){""")

sub("""  const away=simAwayCost(sv);
  const left=Math.max(0,Number(sv.left||0)-away*1000);
  const qt=Object.assign({},sv.qt||{});
  const at=Math.min(sv.i||0,sv.qs.length-1);
  if(away>0){
    const had=(typeof qt[at]==='number')?qt[at]:SIM_QSEC;
    qt[at]=Math.max(0,had-away);
  }""",
"""  const away=simAwayCost(sv);
  const qt=Object.assign({},sv.qt||{});
  const at=Math.min(sv.i||0,sv.qs.length-1);
  // the question you were on ran while you were gone; the rest is charged after sim exists
  const had=(typeof qt[at]==='number')?qt[at]:SIM_QSEC;
  const onThis=Math.min(had,away);
  if(away>0) qt[at]=had-onThis;""")

sub("""       running:true, paper:sv.paper||0, mins:sv.mins,
       dev:sv.dev||DEVICE_ID, devKind:sv.devKind||DEVICE_KIND, claimAt:sv.claimAt||0,
       startAt:Date.now()-((sv.mins*60000)-left), endAt:Date.now()+left};""",
"""       running:true, paper:sv.paper||0, mins:sv.mins,
       locked:sv.locked||{}, cont:sv.cont?1:0, base:sv.base||null,
       dev:sv.dev||DEVICE_ID, devKind:sv.devKind||DEVICE_KIND, claimAt:sv.claimAt||0,
       startAt:Date.now(), endAt:Date.now()};
  if(away>onThis) simChargeEnd(away-onThis,at);
  sim.endAt=Date.now()+simTotalLeft()*1000;   // kept only for anything still reading it""")

sub("""  // If that emptied the paper it is not lost — simCheckTime() submits within the second, so
  // the score for whatever was answered still lands.
  if(left<=0) simCheckTime();""",
"""  // If that emptied the paper it is not lost — simCheckTime() submits within the second, so
  // the score for whatever was answered still lands.
  simCheckTime();""")

# a spent save is scored on resume, not silently thrown away
sub("""  if(!sv||!sv.qs||!sv.qs.length||sv.left<=0) return null;
  // a paper left running is still burning time; do not offer one whose budget is already gone
  if(typeof simAwayCost==='function'&&(sv.left-simAwayCost(sv)*1000)<=0) return null;""",
"""  // A paper whose time ran out while it sat here used to be dropped, answers and all. Resuming
  // it scores what was answered, so it stays on offer.
  if(!sv||!sv.qs||!sv.qs.length) return null;""")

# ---- a background tab in a simulation: overflow comes off the end too -----------------
sub("""let simAwayAt=0;
function simAway(){ if(!simAwayAt) simAwayAt=Date.now(); }""",
"""let simAwayAt=0, simAwayQ=0;
function simAway(){ if(!simAwayAt){ simAwayAt=Date.now(); simAwayQ=Math.max(0,simQLeft|0); } }""")

sub("""  if(sim&&sim.running&&sim.qEndAt&&gone>0&&isPractice()) sim.qEndAt+=gone;
  if(sim&&sim.running) simQSync();""",
"""  if(sim&&sim.running&&sim.qEndAt&&gone>0&&isPractice()) sim.qEndAt+=gone;
  // A simulation pays for the whole absence: the question you were on ran down (its deadline
  // was not moved), and whatever is beyond what it had comes off the end of the paper.
  if(sim&&sim.running&&!isPractice()&&!brkOn()&&route==='quizScreen'){
    const over=Math.round(gone/1000)-simAwayQ;
    if(over>0) simChargeEnd(over,sim.i);
  }
  if(sim&&sim.running) simQSync();""")

# ---- minutes on the result are minutes spent answering -------------------------------
sub("""  const mins=Math.round((Date.now()-sim.startAt)/60000);""",
"""  // Minutes actually spent on questions. Wall time since the start counted every pause —
  // a practice paper left overnight reported 872 minutes.
  const mins=Math.max(0,Math.round((simTotalFull()-simTotalLeft())/60));""")

PAGE.write_text(s, encoding="utf-8")
print("one clock")
