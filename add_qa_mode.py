#!/usr/bin/env python3
"""Standing checks for the two ways to sit a paper.

Every rule the mode picker introduces, and every bug found while building it:

  - a practice pause is free, open-ended and unlimited; a simulation gets two of six minutes
  - coming back to the paper is what ends a practice pause, so the break guard must not treat
    it as a wall the way it does during a simulation break
  - the paper clock gets back exactly what the pause ran, and the question keeps its seconds
  - a refresh mid-pause keeps the mode and pays the pause ONCE. Carrying brkFrom across the
    resume credited the same thirty minutes twice and handed back a 128-minute clock on a
    98-minute paper.
  - a closed tab still costs a simulation its time, which is the exploit that was closed
    before this and must stay closed

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


sub("""async function breakChecks(){""",
"""// A paper is sat either under exam conditions or as practice, and the difference is entirely
// in the breaks. Everything below is a rule the picker introduced or a bug found building it.
async function modeChecks(){
  const t=T(), $=id=>document.getElementById(id);

  // the picker asks, and asks before anything starts
  t.simClearSave();
  let picked=null;
  t.modeAsk('Exam 1',m=>{ picked=m; });
  ok(!$('modeAsk').classList.contains('hidden'),'starting a paper asks which kind it is');
  ok(/Exam 1/.test($('modeAskTitle').textContent),'and names the paper being started');
  t.modePick('practice');
  eq(picked,'practice','the choice reaches the caller');
  ok($('modeAsk').classList.contains('hidden'),'and the sheet closes behind it');
  t.modeAsk('Exam 1',()=>{}); t.modeAskClose();
  ok($('modeAsk').classList.contains('hidden'),'backing out closes it without starting anything');

  // ---- practice: stop as often as you like, for as long as you like ----
  t.simClearSave(); t.startPaper(1,'practice'); await sleep(30);
  ok(t.isPractice(),'a practice paper knows it is one');
  eq(t.brkLeft(),Infinity,'and is not rationed to two breaks');
  eq($('qSector').textContent.indexOf('PRACTICE')>0,true,'the header says so, so you cannot forget');

  t.simQTick(20);
  const qBefore=t.simQLeft, paperBefore=t.sim.endAt-Date.now();
  $('navHome').click(); await sleep(20);
  ok($('brkAsk').classList.contains('hidden'),'leaving practice does not ask \\u2014 the pause is free');
  eq(t.route,'homeScreen','and it lets you go');
  ok(t.brkOn()&&t.brkOpen(),'the paper is paused, open-endedly');

  t.sim.brkFrom-=20*60*1000;                       // twenty minutes away
  t.go('quizScreen'); await sleep(20);
  eq(t.route,'quizScreen','coming back to the paper is how the pause ends');
  ok(!t.brkOn(),'and it does end');
  eq(t.simQLeft,qBefore,'the question keeps the seconds it had');
  const gained=(t.sim.endAt-Date.now())-paperBefore;
  ok(Math.abs(gained-20*60*1000)<5000,
     'and the paper gets back what the pause ran, not a fixed six minutes');

  // as many as you like
  for(let k=0;k<4;k++){ t.go('homeScreen'); await sleep(5); t.go('quizScreen'); await sleep(5); }
  ok(t.sim.brkUsed>=5,'five pauses is not a problem in practice');
  eq(t.brkLeft(),Infinity,'and there are still no limits');

  // ---- a refresh mid-pause pays the pause once, not twice ----
  t.simClearSave(); t.startPaper(2,'practice'); await sleep(20);
  t.simQTick(20);
  t.go('homeScreen'); await sleep(10);
  t.sim.brkFrom-=30*60*1000;
  t.simPersist();
  const sv=JSON.parse(JSON.stringify(t.P.simSave));
  eq(sv.mode,'practice','the save remembers which kind of paper it is');
  eq(sv.brkOpen,1,'and that it was paused when it was written');
  eq(t.simAwayCost(sv),0,'time inside an open pause is not charged');
  const savedMin=Math.round(sv.left/60000), savedQ=sv.qt[sv.i];
  t.simResume(); await sleep(20);
  ok(t.isPractice(),'a resumed practice paper is still practice');
  ok(Math.abs(Math.round((t.sim.endAt-Date.now())/60000)-savedMin)<=1,
     'and comes back on the clock it was saved with \\u2014 not credited the pause a second time');
  eq(t.simQLeft,savedQ,'with the question where it was left');

  // ---- simulation: the old rules, unchanged ----
  t.simClearSave(); t.startPaper(3,'exam'); await sleep(20);
  ok(!t.isPractice(),'an exam paper is not practice');
  eq(t.brkLeft(),2,'two breaks');
  $('navHome').click(); await sleep(20);
  ok(!$('brkAsk').classList.contains('hidden'),'and leaving one still asks, because it costs');
  eq(t.route,'quizScreen','and does not leave until you say so');
  $('brkAskGo').click(); await sleep(20);
  ok(t.brkOn()&&!t.brkOpen(),'a simulation break is timed, not open-ended');
  ok(t.brkRemain()>300,'and runs the full six minutes');
  t.go('quizScreen');
  eq(t.route,'homeScreen','the paper is not somewhere you can be during a timed break');
  t.brkEnd(true); await sleep(10);
  $('navHome').click(); await sleep(20);
  $('brkAskGo').click(); await sleep(20);
  t.brkEnd(true); await sleep(10);
  eq(t.brkLeft(),0,'two breaks is two');
  $('navHome').click(); await sleep(20);
  ok($('brkAsk').classList.contains('hidden'),'a third is not offered');
  eq(t.route,'quizScreen','and the paper keeps you');

  // ---- a closed tab still costs a simulation, which is the exploit that stays closed ----
  t.simClearSave(); t.startPaper(4,'exam'); await sleep(20);
  t.simPersist();
  const sv2=JSON.parse(JSON.stringify(t.P.simSave));
  sv2.at-=12*60*1000;
  ok(t.simAwayCost(sv2)>700,'twelve minutes with the tab shut is twelve minutes charged');

  // ---- the record says which conditions a score was set under ----
  t.P.papers={};
  t.recordPaper(9,80,true);
  eq((t.P.papers[9]||{}).bestMode,'practice','a practice best is marked as one');
  t.recordPaper(9,85,false);
  eq(t.P.papers[9].bestMode,'exam','and a better one sat properly replaces it');
  eq(t.P.papers[9].ptries,1,'the practice attempts are counted separately');
  t.P.papers={};
  t.simClearSave();
}
async function breakChecks(){""")

sub("await breakChecks();", "await breakChecks(); await modeChecks();")

QA.write_text(s, encoding="utf-8")
print("mode rules are standing checks now")
