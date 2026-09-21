#!/usr/bin/env python3
"""Ninety seconds a question, then move on.

The papers ran on one long countdown for the whole exam, which lets you sink
twenty minutes into question three and find out at the end. Now every question
gets 90 seconds — to read it, answer it, and on papers 1-10 to read the feedback
— and when they run out the paper moves to the next question whether or not
anything was answered. An unanswered question stays blank, which scores as
wrong; the timer never waits for you to get it right.

  * SIM_QSEC=90, shown as a countdown in the top clock and as the draining bar
    above the question
  * time left is kept per question in sim.qt, so going back to a question you
    already spent a minute on gives you the thirty seconds you had left, and it
    survives leaving and resuming the paper
  * it does not run while the app is in the background or while you are on the
    review screen — the same rule the practice timer already follows
  * the whole-paper budget becomes 90s x the number of questions, so the two
    clocks agree instead of contradicting each other

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


# ------------------------------------------------------------- 1. the budget
sub("""const SIM_LEN=65, SIM_MIN=130, SIM_PASS=72;""",
"""const SIM_LEN=65, SIM_PASS=72;
// Every question is capped at 90 seconds, so the budget for a whole paper is
// just that times the number of questions — the two clocks cannot disagree.
const SIM_QSEC=90;
const simBudget=n=>Math.ceil(n*SIM_QSEC/60);
const SIM_MIN=simBudget(SIM_LEN);""")

sub("""const PAPER_LEN=65, PAPER_MIN=170;""",
    """const PAPER_LEN=65, PAPER_MIN=simBudget(PAPER_LEN);""")

sub("""       paper:0,mins:SIM_MIN,
       startAt:Date.now(),endAt:Date.now()+SIM_MIN*60000};""",
"""       paper:0,mins:simBudget(qs.length),qt:{},
       startAt:Date.now(),endAt:Date.now()+simBudget(qs.length)*60000};""")

sub("""  sim={qs,i:0,ans:{},flag:{},rev:{},running:true,paper:n,mins:PAPER_MIN,
       startAt:Date.now(),endAt:Date.now()+PAPER_MIN*60000};""",
"""  const budget=simBudget(qs.length);
  sim={qs,i:0,ans:{},flag:{},rev:{},qt:{},running:true,paper:n,mins:budget,
       startAt:Date.now(),endAt:Date.now()+budget*60000};""")

# ------------------------------------------------- 2. the per-question clock
sub("""function simLoad(){
  if(!sim) return;""",
"""// ---------- ninety seconds a question ----------
let simQLeft=0, simQIv=null;
function simQStop(){ if(simQIv){ clearInterval(simQIv); simQIv=null; } }
function simQLeftFor(i){
  const v=sim&&sim.qt?sim.qt[i]:undefined;
  return (typeof v==='number')?Math.max(0,v):SIM_QSEC;
}
function simQStart(){
  simQStop();
  if(!sim||!sim.running) return;
  simQLeft=simQLeftFor(sim.i);
  renderSimQ();
  if(TEST) return;                        // the tests drive it with simQTick()
  simQIv=setInterval(()=>simQTick(1),1000);
}
function simQTick(by){
  if(!sim||!sim.running){ simQStop(); return; }
  if(route!=='quizScreen') return;                              // not on the review screen
  if(typeof document!=='undefined'&&document.hidden) return;    // nor in the background
  simQLeft=Math.max(0,simQLeft-(by||1));
  sim.qt=sim.qt||{}; sim.qt[sim.i]=simQLeft;
  renderSimQ();
  if(simQLeft<=0) simQTimeUp();
}
function simQTimeUp(){
  simQStop();
  if(!sim||!sim.running) return;
  ttsStop();
  // 90 seconds covers reading it, answering it and reading the feedback. When they
  // are gone the paper moves on regardless — a blank question simply scores as wrong,
  // because an exam does not wait for you to get it right.
  const last=sim.i>=simLen()-1;
  toast(last?'⏳ Time — on to the review':'⏳ 90 seconds — next question');
  simGo(1);
}
function renderSimQ(){
  const wrap=$('qTimerWrap'), fill=$('qTimerFill');
  if(!wrap||!fill) return;
  if(!sim||!sim.running){ wrap.classList.add('hidden'); return; }
  wrap.classList.remove('hidden');
  const f=Math.max(0,Math.min(1,simQLeft/SIM_QSEC));
  fill.style.width=(f*100)+'%';
  fill.classList.toggle('low',simQLeft<=20);
  renderClock();
}
function simLoad(){
  if(!sim) return;""")

# the header clock counts this question down, not the whole paper
sub("""  if(sim&&sim.running){
    const left=Math.max(0,sim.endAt-Date.now());
    el.textContent='⏳ '+fmtClock(left);
    el.classList.toggle('warn',left<10*60000);
    el.classList.toggle('crit',left<2*60000);
    const sub0=$('clockSub'); if(sub0) sub0.textContent=sim.paper?('exam '+sim.paper):'exam';
    return;
  }""",
"""  if(sim&&sim.running){
    // the question's own 90 seconds is what governs now, so that is what the clock shows;
    // the paper's remaining budget is on the review screen, where it is actually useful
    const left=simQLeft*1000;
    el.textContent='⏳ '+fmtClock(left);
    el.classList.toggle('warn',simQLeft<=30);
    el.classList.toggle('crit',simQLeft<=10);
    const sub0=$('clockSub');
    if(sub0) sub0.textContent=(sim.paper?('exam '+sim.paper):'exam')+' · this question';
    return;
  }""")

# simLoad: start the question's clock instead of hiding the bar
sub("""  $('chargeBar').style.display='none';
  $('qTimerWrap').classList.add('hidden');
  $('studyBtn').classList.add('hidden');""",
"""  $('chargeBar').style.display='none';
  $('studyBtn').classList.add('hidden');""")

sub("""  renderSimStrip();
  renderClock();
  go('quizScreen');
}
function simPick(ltr){""",
"""  renderSimStrip();
  simQStart();
  go('quizScreen');
}
function simPick(ltr){""")

# ----------------------------------------------- 3. stop it when the exam does
sub("""     !$('simSubmit').dataset.armed){""", """     !$('simSubmit').dataset.armed){""")
sub("""  simPersist();                 // keep it: the Practice Exams screen offers it back
  ttsStop(); hideExplain();""",
"""  simPersist();                 // keep it: the Practice Exams screen offers it back
  simQStop(); ttsStop(); hideExplain();""")

# ------------------------------------------------- 4. it survives a resume
sub("""  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},
             left:Math.max(0,sim.endAt-Date.now()), mins:sim.mins||SIM_MIN, at:Date.now()};""",
"""  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},
             qt:sim.qt||{},
             left:Math.max(0,sim.endAt-Date.now()), mins:sim.mins||SIM_MIN, at:Date.now()};""")

sub("""  sim={qs:sv.qs, i:Math.min(sv.i||0,sv.qs.length-1), ans:sv.ans||{}, flag:sv.flag||{},
       rev:sv.rev||{}, running:true, paper:sv.paper||0, mins:sv.mins,""",
"""  sim={qs:sv.qs, i:Math.min(sv.i||0,sv.qs.length-1), ans:sv.ans||{}, flag:sv.flag||{},
       rev:sv.rev||{}, qt:sv.qt||{}, running:true, paper:sv.paper||0, mins:sv.mins,""")

# --------------------------------------------------------------- 5. the copy
sub("""    PAPER_LEN+' questions each, '+PAPER_MIN+' minutes, nothing repeated inside a paper '+""",
    """    PAPER_LEN+' questions each, '+SIM_QSEC+' seconds a question, nothing repeated inside a paper '+""")
sub("""      : len+' questions · '+PAPER_MIN+' minutes';""",
    """      : len+' questions · '+SIM_QSEC+'s each · '+simBudget(len)+' min';""")

# ------------------------------------------------------------ 6. the harness
sub("""    simAbandon, simTimeLeft, simCheckTime, simAnsweredCount, renderSimLog,""",
"""    simAbandon, simTimeLeft, simCheckTime, simAnsweredCount, renderSimLog,
    SIM_QSEC, simBudget, simQStart, simQStop, simQTick, simQTimeUp, renderSimQ,
    get simQLeft(){return simQLeft;},""")

# the bar is thicker during an exam — it is the exam's clock now, not a hint
sub("""#qTimerWrap{height:5px;border-radius:3px;background:rgba(255,255,255,.1);overflow:hidden;margin-top:2px}""",
"""#qTimerWrap{height:5px;border-radius:3px;background:rgba(255,255,255,.1);overflow:hidden;margin-top:2px}
#qTimerFill{transition:width .95s linear}""")

PAGE.write_text(s, encoding="utf-8")
print("90 seconds a question · page %.2f MB" % (len(s) / 1e6))
