#!/usr/bin/env python3
"""Explain each answer as it is given, on the first ten papers.

Exams 1 to 10 are the teaching papers now: they brief you before the question
(extended here from five papers to ten) and, the moment you commit an answer,
they lock it and explain — whether you were right, what the correct answer is,
why it fits, and what each other option actually does. Papers 11 to 19 stay
silent until you submit, which is what a real exam feels like.

The explanation reuses `renderExplain`, the panel practice mode already had,
and leads with the note written while the answer key was reviewed when that
question has one (174 of them do).

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import sys

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:100])
    s = s.replace(old, new, count)


# ---------------------------------------------- 1. ten briefed papers, not five
sub("""// ---------- the first five papers come with a briefing ----------
const BRIEF_PAPERS=5;""",
    """// ---------- the first ten papers teach rather than test ----------
// They brief you before the question and explain the moment you answer.
const BRIEF_PAPERS=10;
const EXPLAIN_PAPERS=10;
const simTeaches=()=>!!(sim&&sim.paper&&sim.paper<=EXPLAIN_PAPERS);""")

# ------------------------------------------- 2. the authored note leads the panel
sub("""  return {ok, correct, wrongPicked, correctTerms, distractors, cue:exCue(q),
          sector:SHORT[q.s]||SECTIONS[q.s], sec:q.s};""",
    """  return {ok, correct, wrongPicked, correctTerms, distractors, cue:exCue(q),
          note:q.x||'', sector:SHORT[q.s]||SECTIONS[q.s], sec:q.s};""")

sub("""  bits.push('<div class="exlbl">'+(ok?'Your answer':'Correct answer')+'</div>');
  e.correct.forEach(x=>bits.push('<div class="exrow good"><span class="exl">'+x[0]+'</span><span>'+esc(x[1])+'</span></div>'));
""",
"""  bits.push('<div class="exlbl">'+(ok?'Your answer':'Correct answer')+'</div>');
  e.correct.forEach(x=>bits.push('<div class="exrow good"><span class="exl">'+x[0]+'</span><span>'+esc(x[1])+'</span></div>'));

  // the note written while this question's answer was verified beats anything derived
  if(e.note) bits.push('<div class="exnote"><b>Why</b> '+esc(e.note)+'</div>');
""")

# the closing line and the Continue button belong to practice, not to an exam
sub("""  bits.push('<div class="exfoot">Assembled from the study guide glossary and its scenario table — '+
            'open <b>'+esc(e.sector)+'</b> in Subject Course for the full reasoning.</div>');
  bits.push('<button class="btn" id="exNext" style="width:100%;margin-top:2px">Continue ▸</button>');""",
"""  if(simTeaches()){
    bits.push('<div class="exfoot">Papers 1–'+EXPLAIN_PAPERS+' explain as you go. '+
              'From paper '+(EXPLAIN_PAPERS+1)+' on you will not see this until you submit.</div>');
  } else {
    bits.push('<div class="exfoot">Assembled from the study guide glossary and its scenario table — '+
              'open <b>'+esc(e.sector)+'</b> in Study for the full reasoning.</div>');
    bits.push('<button class="btn" id="exNext" style="width:100%;margin-top:2px">Continue ▸</button>');
  }""")

# ------------------------------------------- 3. reveal the moment an answer is in
sub("""function simPick(ltr){
  if(!sim) return;
  const need=QS[sim.qs[sim.i]].a.length;""",
"""function simPick(ltr){
  if(!sim) return;
  if(sim.rev&&sim.rev[sim.i]) return;        // a revealed question is settled
  const need=QS[sim.qs[sim.i]].a.length;""")

sub("""  sim.ans[sim.i]=[...cur];
  simPersist();
  chosen.clear(); cur.forEach(l=>chosen.add(l));
  [...$('qOpts').children].forEach(el=>el.classList.toggle('sel',cur.has(el.dataset.ltr)));
  sfx.tap(); renderSimStrip();""",
"""  sim.ans[sim.i]=[...cur];
  chosen.clear(); cur.forEach(l=>chosen.add(l));
  [...$('qOpts').children].forEach(el=>el.classList.toggle('sel',cur.has(el.dataset.ltr)));
  sfx.tap();
  // on a teaching paper, committing the last required pick settles the question
  if(simTeaches()&&cur.size===need) simReveal();
  simPersist(); renderSimStrip();""")

sub("""function simGo(d){""",
"""// ---------- feedback during a teaching paper ----------
function simRevealed(i){ return !!(sim&&sim.rev&&sim.rev[(i==null?sim.i:i)]); }
function simReveal(){
  if(!sim) return;
  const q=QS[sim.qs[sim.i]], picked=new Set(sim.ans[sim.i]||[]);
  if(!picked.size) return;
  sim.rev=sim.rev||{}; sim.rev[sim.i]=1;
  const ok=q.a.length===picked.size&&q.a.every(a=>picked.has(a));
  simPaintRevealed(q,picked);
  renderExplain(q,picked,ok);
  if(ok) sfx.right(); else sfx.wrong();
  simPersist();
}
function simPaintRevealed(q,picked){
  [...$('qOpts').children].forEach(el=>{
    const l=el.dataset.ltr;
    el.classList.remove('sel');
    if(q.a.includes(l)) el.classList.add('ok');
    else if(picked.has(l)) el.classList.add('no');
  });
}
function simScore(){
  // how the teaching papers are doing so far, so the strip can say something useful
  if(!sim) return {done:0,right:0};
  let done=0,right=0;
  sim.qs.forEach((qi,i)=>{
    if(!simRevealed(i)) return;
    done++;
    const q=QS[qi], p=new Set(sim.ans[i]||[]);
    if(q.a.length===p.size&&q.a.every(a=>p.has(a))) right++;
  });
  return {done,right};
}
function simGo(d){""")

# reloading a question that was already answered must show its verdict again
sub("""  renderExamBrief(qi);
  renderTtsBtn();""",
"""  if(simRevealed()){
    const picked=new Set(sim.ans[sim.i]||[]);
    const okNow=q.a.length===picked.size&&q.a.every(a=>picked.has(a));
    simPaintRevealed(q,picked);
    renderExplain(q,picked,okNow);
  } else hideExplain();
  renderExamBrief(qi);
  renderTtsBtn();""")

# and a fresh paper starts with nothing revealed
sub("""  simClearSave();
  sim={qs,i:0,ans:{},flag:{},running:true,paper:n,mins:PAPER_MIN,""",
    """  simClearSave();
  sim={qs,i:0,ans:{},flag:{},rev:{},running:true,paper:n,mins:PAPER_MIN,""")
sub("""  sim={qs:simBuild(),i:0,ans:{},flag:{},running:true,""",
    """  sim={qs:simBuild(),i:0,ans:{},flag:{},rev:{},running:true,""")

# the reveal state travels with the save
sub("""  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag,""",
    """  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},""")
sub("""  sim={qs:sv.qs, i:Math.min(sv.i||0,sv.qs.length-1), ans:sv.ans||{}, flag:sv.flag||{},
       running:true, paper:sv.paper||0, mins:sv.mins,""",
    """  sim={qs:sv.qs, i:Math.min(sv.i||0,sv.qs.length-1), ans:sv.ans||{}, flag:sv.flag||{},
       rev:sv.rev||{}, running:true, paper:sv.paper||0, mins:sv.mins,""")

# the running tally on a teaching paper
sub("""  const c=$('simCount');
  if(c) c.textContent=simAnsweredCount()+' / '+simLen()+' answered';""",
"""  const c=$('simCount');
  if(c){
    const sc=simScore();
    c.textContent=simTeaches()&&sc.done
      ? simAnsweredCount()+' / '+simLen()+' answered · '+sc.right+'/'+sc.done+' right so far'
      : simAnsweredCount()+' / '+simLen()+' answered';
  }""")

# leaving the exam clears the panel
sub("""  ttsStop();
  sim=null; renderClock();""",
    """  ttsStop(); hideExplain();
  sim=null; renderClock();""")
sub("""  sim.running=false;
  ttsStop(); simClearSave();""",
    """  sim.running=false;
  ttsStop(); hideExplain(); simClearSave();""")

# ------------------------------------------------------------- 4. the styling
sub(""".simbtn.tts.on{border-color:var(--cyan);color:var(--cyan)}""",
""".simbtn.tts.on{border-color:var(--cyan);color:var(--cyan)}
.exnote{font-size:12.5px;line-height:1.6;padding:11px 13px;border-radius:10px;
  background:color-mix(in srgb, var(--cyan) 9%, transparent);
  border:1px solid color-mix(in srgb, var(--cyan) 26%, transparent);color:var(--txt)}
.exnote b{color:var(--cyan);font-weight:650;margin-right:5px}""")

# ------------------------------------------------------------- 5. test surface
sub("""    simPersist, simClearSave, simSaved, simResume, ttsOk, ttsStop, ttsText, ttsSpeak,""",
    """    EXPLAIN_PAPERS, simTeaches, simReveal, simRevealed, simScore, simPaintRevealed,
    buildExplain, renderExplain, hideExplain,
    simPersist, simClearSave, simSaved, simResume, ttsOk, ttsStop, ttsText, ttsSpeak,""")

PAGE.write_text(s, encoding="utf-8")
print("exam feedback applied · page %.2f MB" % (len(s) / 1e6))
sys.exit(0)
