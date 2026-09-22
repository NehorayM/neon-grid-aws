#!/usr/bin/env python3
"""Resuming must not strand you on a question with no time, and the big number
must be the one that binds.

Two things visible in the report, both real.

1. **Stranded at 0:00.** Away long enough for the away-charge to drain the
   question you were on, you resume onto it with a dead 0:00 clock. simQStart()
   deliberately does not bounce you out of a spent question — that is right when
   you open one from the review list, and wrong here, because you did not choose
   to be there. A resume now lands on the first question that still has time, and
   on the review screen if none do.

2. **The headline number was not the binding one.** "PAPER REMAINING 1:36:00"
   sat above "the paper clock runs out first — 1:16:12 of wall time". Both true:
   the first is the sum of what each question still holds, the second is the
   paper's own budget. But quoting the larger, less binding figure in the big
   type is the wrong way round. It shows whichever will actually run out first,
   and says which one that is.

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


# --------------------------------------- 1. a resume lands somewhere you can work
sub("""  if(away>30) toast('\u23f1 '+fmtClock(away*1000)+' passed while the paper was open elsewhere');
  renderClock(); simLoad(); simClaim();""",
"""  if(away>30) toast('\u23f1 '+fmtClock(away*1000)+' passed while the paper was open elsewhere');
  // Being away can drain the question you were on. Landing back on it means a dead 0:00 clock
  // and no way forward but Next — and unlike opening a spent question from the review list,
  // this is not somewhere you chose to be. Go to the first one that still has time.
  const spent=k=>{ const v=sim.qt[k]; return (typeof v==='number')&&v<=0; };
  if(spent(sim.i)){
    let n=-1;
    for(let k=0;k<simLen();k++){ if(!spent(k)){ n=k; break; } }
    if(n>=0){
      sim.i=n;
      if(away>30) toast('\U0001f4cd Moved to question '+(n+1)+' — the one you left had no time on it');
    }else{
      // nothing left anywhere: the paper is over, so score what was answered
      renderClock(); simClaim(); simSubmit(true); return;
    }
  }
  renderClock(); simLoad(); simClaim();""")

# ------------------------------------- 2. the headline is whichever binds first
sub("""  const left=simTotalLeft(), full=simTotalFull(), qs=simQsLeft();
  $('simTotalVal').textContent=fmtClock(left*1000);
  $('simTotalFill').style.width=pctW(left/Math.max(1,full)*100);""",
"""  const byQuestion=simTotalLeft(), full=simTotalFull(), qs=simQsLeft();
  const wallMs0=(typeof simTimeLeft==='function')?simTimeLeft():Infinity;
  const byWall=isFinite(wallMs0)?Math.floor(wallMs0/1000):Infinity;
  // Two true numbers: what the questions still hold, and what the paper's own clock has. The
  // big one has to be whichever runs out first, or it reads as a contradiction of its own
  // subtitle — "1:36:00" over "the paper clock runs out first, 1:16:12".
  const left=Math.min(byQuestion,byWall);
  $('simTotalVal').textContent=fmtClock(left*1000);
  $('simTotalFill').style.width=pctW(left/Math.max(1,full)*100);""")

sub("""  const wallMs=(typeof simTimeLeft==='function')?simTimeLeft():Infinity;
  $('simTotalSub').textContent=(isFinite(wallMs)&&wallMs<left*1000)
    ? ('the paper clock runs out first \\u2014 '+fmtClock(wallMs)+' of wall time')
    : (plural(qs,'question')+' still open \\u00b7 '+SIM_QSEC+'s each \\u00b7 '+
       fmtClock(full*1000)+' for the paper');""",
"""  $('simTotalSub').textContent=(byWall<byQuestion)
    ? ('the paper\\u2019s own clock is what runs out \\u2014 the questions still hold '+
       fmtClock(byQuestion*1000))
    : (plural(qs,'question')+' still open \\u00b7 '+SIM_QSEC+'s each \\u00b7 '+
       fmtClock(full*1000)+' for the paper');""")

sub("""  const wall=(typeof simTimeLeft==='function')?Math.floor(simTimeLeft()/1000):Infinity;
  box.classList.toggle('tight',wall<left);""",
"""  box.classList.toggle('tight',byWall<byQuestion);""")

PAGE.write_text(s, encoding="utf-8")
print("resume lands somewhere workable; the headline binds · page %.2f MB" % (len(s) / 1e6))
