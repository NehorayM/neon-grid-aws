#!/usr/bin/env python3
"""Finish the last exam: the questions you did not get to are still there to answer.

Submitting a paper deleted its save and kept no per-question answers anywhere — a blank and
a wrong answer both landed in the "wrong" list — so a paper that ended early could not be
reopened. That is also why Exam 5, already submitted, cannot be: the build it ran on threw
that away. From now on:

  - Submitting keeps a snapshot of the paper while any question is unanswered with time left
    on it (P.lastPaper).
  - "Finish the questions you did not reach" on the result screen, and a Finish button on
    that paper's row, reopen it. Answers from the earlier sitting are locked: the result
    screen and the CSV show the correct answers for missed questions, so changing them would
    only be copying. For the same reason a finished-later score is recorded as practice, and
    the paper runs under practice rules.
  - The accounting only counts what is new. The first submit already counted every blank as
    attempted and wrong, so a continuation adds only the questions newly answered right: it
    takes them off the wrong list, credits the subject stats and the spaced-repetition
    schedule, and pays coins and XP for those alone. It is not another exam in the counters,
    and a pass bonus is paid only if this is the sitting that crosses the line.

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

# ---- markup: the offer sits right under the score, where the eye already is ----------
sub("""      <div class="ch-note simheb" id="simHeb"></div>
      <div class="sechead">Domain breakdown</div>""",
"""      <div class="ch-note simheb" id="simHeb"></div>
      <button class="btn wide hidden" id="simCont" style="margin:14px auto 0;max-width:420px"></button>
      <div class="sechead">Domain breakdown</div>""")

# ---- the helpers, next to the rest of the paper lifecycle --------------------------
sub("""function simAbandon(){
  if(!sim) return;""",
"""// ---------- finish the last exam ----------
// What is still answerable in a snapshot: unanswered, and with time left on its own clock.
function lastOpen(lp){
  lp=lp||P.lastPaper;
  if(!lp||!Array.isArray(lp.qs)||lp.qs.some(i=>!QS[i])) return [];
  const out=[];
  lp.qs.forEach((qi,i)=>{
    const blank=!((lp.ans||{})[i]||[]).length;
    const v=(lp.qt||{})[i], t=(typeof v==='number')?v:SIM_QSEC;
    if(blank&&t>0) out.push(i);
  });
  return out;
}
function lastLabel(lp){ return lp&&lp.paper?('Exam '+lp.paper):'the mock exam'; }
function simContinue(){
  const lp=P.lastPaper, open=lastOpen(lp);
  if(!open.length){ toast('Nothing left to answer on that paper'); return; }
  ensureAudio(); exitStudyMode();
  reviewMode=false; markMode=false; mock=null;
  simClearSave();
  const locked={}, blank={};
  lp.qs.forEach((qi,i)=>{ if(((lp.ans||{})[i]||[]).length) locked[i]=1; else blank[i]=1; });
  sim={qs:lp.qs, i:open[0], ans:Object.assign({},lp.ans||{}), flag:Object.assign({},lp.flag||{}),
       rev:Object.assign({},lp.rev||{}), qt:Object.assign({},lp.qt||{}),
       // the correct answers have been on screen since, so this is practice, not an exam
       mode:'practice', running:true, paper:lp.paper||0, mins:lp.mins||SIM_MIN,
       locked, cont:1, base:{blank, pct:lp.pct||0, passed:lp.passed?1:0},
       startAt:Date.now(), endAt:Date.now()};
  sim.endAt=Date.now()+simTotalLeft()*1000;
  saveProfile(); renderClock(); simLoad(); simClaim(); simPersist();
  toast('\\u21a9 '+lastLabel(lp)+' \\u2014 '+plural(open.length,'question')+' left to answer. '+
        'Earlier answers are locked.');
}
// Starting it over the top of another paper in progress loses that one, so say so first —
// the same guard Start uses.
function simContinueAsk(btn){
  const open=simSaved();
  if(open&&!(sim&&sim.cont)){
    const what=(open.paper?'Exam '+open.paper:'the mock exam')+' \\u2014 question '+((open.i||0)+1)+' of '+open.qs.length;
    armed(btn,'Delete your progress on '+what+'?',simContinue);
    return;
  }
  simContinue();
}
function renderSimCont(){
  const b=$('simCont'); if(!b) return;
  const n=lastOpen().length;
  b.classList.toggle('hidden',!n);
  if(n) b.textContent='\\u21a9 Finish the questions you did not reach ('+n+' left)';
}
function simAbandon(){
  if(!sim) return;""")

# ---- a locked answer stays put -------------------------------------------------------
sub("""  if(sim.rev&&sim.rev[sim.i]) return;        // a revealed question is settled""",
"""  if(sim.rev&&sim.rev[sim.i]) return;        // a revealed question is settled
  if(sim.locked&&sim.locked[sim.i]){ toast('Answered in the first sitting \\u2014 locked'); return; }""")

sub("""    b.onclick=()=>simPick(ltr);
    box.appendChild(b);""",
"""    b.onclick=()=>simPick(ltr);
    if(sim.locked&&sim.locked[sim.i]){ b.classList.add('locked'); b.setAttribute('aria-disabled','true'); }
    box.appendChild(b);""")

sub(""".opt.nope{animation:nope .32s ease}""",
""".opt.nope{animation:nope .32s ease}
.opt.locked{opacity:.62;cursor:default}
.opt.locked.sel{opacity:.9}""")

# ---- a continuation survives a refresh like any paper ------------------------------------
sub("""             mode:sim.mode||'exam', brkUsed:sim.brkUsed||0, brkUntil:sim.brkUntil||0,""",
"""             mode:sim.mode||'exam', brkUsed:sim.brkUsed||0, brkUntil:sim.brkUntil||0,
             locked:sim.locked||{}, cont:sim.cont?1:0, base:sim.base||null,""")

# ---- submit: keep the snapshot, and count a continuation honestly ------------------------
sub("""  const paper=sim.paper||0;
  let correct=0; const byDom={0:[0,0],1:[0,0],2:[0,0],3:[0,0]}; const missed=[];
  const csv=[];
  sim.qs.forEach((qi,i)=>{
    const q=QS[qi], picked=new Set(sim.ans[i]||[]);
    const ok=q.a.length===picked.size&&q.a.every(a=>picked.has(a));
    const d=domainOf(q.s);
    byDom[d][1]++; if(ok){ byDom[d][0]++; correct++; } else missed.push(qi);
    // a question flagged during the exam becomes a bookmark, so it survives the
    // exam and shows up in the review export later
    if(sim.flag[i]&&(P.marks||[]).indexOf(qi)<0) (P.marks=P.marks||[]).push(qi);
    if(sim.flag[i]||!ok) csv.push({i:qi,why:sim.flag[i]&&!ok?'Flagged + missed':sim.flag[i]?'Flagged':'Missed'});
    P.seen[qi]=1;
    const st=P.secStats[q.s]=P.secStats[q.s]||{a:0,c:0};
    st.a++; if(ok) st.c++; else if((P.wrong||[]).indexOf(qi)<0) (P.wrong=P.wrong||[]).push(qi);
    srSchedule(qi,ok);
  });""",
"""  const paper=sim.paper||0;
  const cont=!!sim.cont, base=sim.base||{blank:{},pct:0,passed:0};
  let correct=0, gain=0; const byDom={0:[0,0],1:[0,0],2:[0,0],3:[0,0]}; const missed=[];
  const csv=[];
  sim.qs.forEach((qi,i)=>{
    const q=QS[qi], picked=new Set(sim.ans[i]||[]);
    const ok=q.a.length===picked.size&&q.a.every(a=>picked.has(a));
    const d=domainOf(q.s);
    byDom[d][1]++; if(ok){ byDom[d][0]++; correct++; } else missed.push(qi);
    // a question flagged during the exam becomes a bookmark, so it survives the
    // exam and shows up in the review export later
    if(sim.flag[i]&&(P.marks||[]).indexOf(qi)<0) (P.marks=P.marks||[]).push(qi);
    if(sim.flag[i]||!ok) csv.push({i:qi,why:sim.flag[i]&&!ok?'Flagged + missed':sim.flag[i]?'Flagged':'Missed'});
    const st=P.secStats[q.s]=P.secStats[q.s]||{a:0,c:0};
    if(cont){
      // The first sitting already counted this question — a blank as attempted and wrong. Only
      // a blank answered right now changes anything.
      if(base.blank&&base.blank[i]&&ok){
        gain++; st.c++;
        P.wrong=(P.wrong||[]).filter(x=>x!==qi);
        srSchedule(qi,true);
      }
      return;
    }
    P.seen[qi]=1;
    st.a++; if(ok) st.c++; else if((P.wrong||[]).indexOf(qi)<0) (P.wrong=P.wrong||[]).push(qi);
    srSchedule(qi,ok);
  });
  // Keep the paper while anything on it is still answerable, so it can be finished later.
  { const snap={paper, qs:sim.qs.slice(), ans:Object.assign({},sim.ans), flag:Object.assign({},sim.flag),
                rev:Object.assign({},sim.rev||{}),
                qt:Object.assign({},sim.qt||{},{[sim.i]:Math.max(0,simQLeft)}),
                mins:sim.mins, d:dayKey()};
    P.lastPaper=snap; }""")

sub("""  const len=simLen();
  const pct=Math.round(correct/len*100);
  const passed=pct>=SIM_PASS;""",
"""  const len=simLen();
  const pct=Math.round(correct/len*100);
  const passed=pct>=SIM_PASS;
  if(P.lastPaper){ P.lastPaper.pct=pct; P.lastPaper.passed=passed?1:0;
                   if(!lastOpen(P.lastPaper).length) delete P.lastPaper; }
  // a continuation pays the pass bonus only if this is the sitting that crosses the line
  const newPass=passed&&!(cont&&base.passed);""")

sub("""  P.sims=(P.sims||0)+1; if(passed) P.simsPassed=(P.simsPassed||0)+1;
  P.bestSim=Math.max(P.bestSim||0,pct);""",
"""  if(!cont){ P.sims=(P.sims||0)+1; }
  if(newPass) P.simsPassed=(P.simsPassed||0)+1;
  P.bestSim=Math.max(P.bestSim||0,pct);""")

sub("""  P.simLog.unshift({d:dayKey(),p:pct,pass:passed?1:0,mins,pr:isPractice()?1:0,""",
    """  P.simLog.unshift({d:dayKey(),p:pct,pass:passed?1:0,mins,pr:isPractice()?1:0,ct:cont?1:0,""")

sub("""  P.answered+=len; P.correct+=correct;
  // the papers are the exams now, so the exam badges, quest and history track them
  P.exams=(P.exams||0)+1; if(passed) P.examsPassed=(P.examsPassed||0)+1;
  logExam(correct,len,passed);
  if(passed) questProgress('exam',1);
  if(paper) recordPaper(paper,pct,isPractice());""",
"""  if(cont){ P.correct+=gain; }
  else { P.answered+=len; P.correct+=correct; }
  // the papers are the exams now, so the exam badges, quest and history track them
  if(!cont) P.exams=(P.exams||0)+1;
  if(newPass) P.examsPassed=(P.examsPassed||0)+1;
  logExam(correct,len,passed);
  if(newPass) questProgress('exam',1);
  if(paper) recordPaper(paper,pct,isPractice(),cont);""")

sub("""  const coins=correct+(passed?90:0);
  addCoins(coins); addXP(correct*6+(passed?200:0));""",
"""  const earned=cont?gain:correct;
  const coins=earned+(newPass?90:0);
  addCoins(coins); addXP(earned*6+(newPass?200:0));""")

sub("""  $('simMeta').textContent=correct+' / '+len+' correct · '+mins+' min · +'+coins+' 🪙'+
    (csv.length?' · '+csv.length+' to export':'');""",
"""  $('simMeta').textContent=correct+' / '+len+' correct · '+mins+' min · +'+coins+' 🪙'+
    (cont?' · finished later':'')+
    (csv.length?' · '+csv.length+' to export':'');""")

sub("""  sim=null; saveProfile(); logReadiness(); checkBadges(); renderReadiness(); renderClock();
  renderSimLog();          // the History block on this screen was always rendering empty""",
"""  sim=null; saveProfile(); logReadiness(); checkBadges(); renderReadiness(); renderClock();
  renderSimLog();          // the History block on this screen was always rendering empty
  renderSimCont();""")

# recordPaper: a continuation is not another attempt
sub("""function recordPaper(n,pct,practice){
  P.papers=P.papers||{};
  const r=P.papers[n]||{best:0,tries:0,last:''};""",
"""function recordPaper(n,pct,practice,continued){
  P.papers=P.papers||{};
  const r=P.papers[n]||{best:0,tries:0,last:''};
  // Finishing a paper later is the same attempt, and it happened after the answers were shown.
  if(continued){
    if(pct>=r.best){ r.best=pct; r.bestMode='practice'; }
    r.last=pct+'%'; r.lastMode='practice'; r.d=dayKey();
    P.papers[n]=r; return;
  }""")

# history says which entries were finished later
sub("""      '<div class="nm">'+num(m.p)+'% '+(m.pass?'— pass':'— below 72%')+(m.pr?' · practice':'')+'</div>'+""",
    """      '<div class="nm">'+num(m.p)+'% '+(m.pass?'— pass':'— below 72%')+(m.ct?' · finished later':m.pr?' · practice':'')+'</div>'+""")

# wiring
sub("""$('simCsv').onclick=exportLastExam;""",
"""$('simCsv').onclick=exportLastExam;
$('simCont').onclick=()=>simContinueAsk($('simCont'));""")

# expose for the harness
sub("    isPractice, brkOpen, brkElapsed,",
    "    isPractice, brkOpen, brkElapsed, simContinue, lastOpen, renderSimCont, simChargeEnd,")

PAGE.write_text(s, encoding="utf-8")
print("finish-the-last-exam wired")
