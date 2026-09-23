#!/usr/bin/env python3
"""Show which mode you are in, and mark which scores were earned under exam conditions.

A mode you cannot see is a mode you will forget you picked, so the paper header says which
one this is, and the row in the exam list marks a best score that was set in practice.

Scores still count the same either way — XP, coins, the history, readiness. The mark is there
so that a 78% you paused your way through is not mistaken later for a 78% you sat straight
through, which is the only difference that matters when you are deciding whether you are ready.

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


# the header says which kind of run this is
sub("""  $('qSector').textContent=sim.paper?('EXAM '+sim.paper):'EXAM SIM';""",
"""  $('qSector').textContent=(sim.paper?('EXAM '+sim.paper):'EXAM SIM')+
    (isPractice()?' \\u00b7 PRACTICE':'');""")

# the record remembers how the score was earned
sub("""function recordPaper(n,pct){
  P.papers=P.papers||{};
  const r=P.papers[n]||{best:0,tries:0,last:''};
  r.best=Math.max(r.best,pct); r.tries++; r.last=pct+'%'; r.d=dayKey();
  P.papers[n]=r;
}""",
"""function recordPaper(n,pct,practice){
  P.papers=P.papers||{};
  const r=P.papers[n]||{best:0,tries:0,last:''};
  // Which conditions a best score was set under is the thing worth keeping. A score you
  // paused your way through and one you sat straight through are not the same evidence.
  if(pct>=r.best){ r.best=pct; r.bestMode=practice?'practice':'exam'; }
  r.tries++; r.last=pct+'%'; r.lastMode=practice?'practice':'exam'; r.d=dayKey();
  if(practice) r.ptries=(r.ptries||0)+1;
  P.papers[n]=r;
}""")

sub("""  if(paper) recordPaper(paper,pct);""",
    """  if(paper) recordPaper(paper,pct,isPractice());""")

sub("""  P.simLog.unshift({d:dayKey(),p:pct,pass:passed?1:0,mins,""",
    """  P.simLog.unshift({d:dayKey(),p:pct,pass:passed?1:0,mins,pr:isPractice()?1:0,""")

# and the row says so, next to the score it qualifies
sub("""      ((rec&&!here)?'<div class="pscore" style="color:'+col+'">'+rec.best+'%</div>':'');""",
"""      ((rec&&!here)?'<div class="pscore" style="color:'+col+'">'+rec.best+'%'+
        (rec.bestMode==='practice'?'<i class="pmode">practice</i>':'')+'</div>':'');""")

sub(""".brkfacts{display:flex;gap:10px;margin-top:12px}""",
""".pscore .pmode{display:block;font-style:normal;font-family:var(--mono);font-size:8.5px;
  letter-spacing:.6px;text-transform:uppercase;color:var(--dim);margin-top:1px}
.brkfacts{display:flex;gap:10px;margin-top:12px}""")

PAGE.write_text(s, encoding="utf-8")
print("the mode is visible and recorded · page %.2f MB" % (len(s) / 1e6))
