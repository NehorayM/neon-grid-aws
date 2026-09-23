#!/usr/bin/env python3
"""Coming back to a Simulation paper after a while found it finished, with no way back in.

Time away was charged in full: the question you were on first, the rest off the end of the
paper. Three hours away is more than a whole paper holds, so every clock ran out, resuming
found nothing left and submitted it — "20 / 65, 45 blank", and nothing to return to.

  - Time away now costs only the question you were on. Leaving still cannot be used to think
    about that question for free — it runs out while you are gone and is shown as timed out —
    but the rest of the paper waits, and a paper is never submitted just because you were away.
  - Safety net: "Finish later" reopens every unanswered question whose answer you have not been
    shown, with fresh time if its clock is empty. (A question that timed out while you were on
    it was revealed, so it stays closed.)

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

sub("""  if(away>onThis) simChargeEnd(away-onThis,at);""",
"""  // Only the question you were on pays for the time away. Taking the rest off the end of the
  // paper meant a few hours away drained everything and the paper submitted itself.""")

sub("""  if(sim&&sim.running&&!isPractice()&&!brkOn()){
    // on a question, it ran down first and only the overflow is left to charge; left from the
    // review grid, no question clock was running, so all of it comes off the end
    const onQ=route==='quizScreen';
    const over=Math.round(gone/1000)-(onQ?simAwayQ:0);
    if(over>0) simChargeEnd(over,onQ?sim.i:-1);
  }""",
"""  // (A simulation's question you were on has already run down — its deadline was not moved.
  // Nothing more is charged: taking the rest off the end of the paper let a long absence drain
  // every question and submit the paper while you were gone.)""")

sub("""    const blank=!((lp.ans||{})[i]||[]).length;
    const v=(lp.qt||{})[i], t=(typeof v==='number')?v:SIM_QSEC;
    if(blank&&t>0) out.push(i);""",
"""    const blank=!((lp.ans||{})[i]||[]).length;
    // unanswered, and its answer not yet shown to you — whatever its clock says
    const shown=!!((lp.rev||{})[i]);
    if(blank&&!shown) out.push(i);""")

# a reopened question with an empty clock gets its time back
sub("""  const locked={}, blank={};
  lp.qs.forEach((qi,i)=>{ if(((lp.ans||{})[i]||[]).length) locked[i]=1; else blank[i]=1; });""",
"""  const locked={}, blank={};
  lp.qs.forEach((qi,i)=>{ if(((lp.ans||{})[i]||[]).length) locked[i]=1; else blank[i]=1; });
  const qt=Object.assign({},lp.qt||{});
  open.forEach(i=>{ if(!(Number(qt[i])>0)) qt[i]=SIM_QSEC; });""")
sub("""       rev:Object.assign({},lp.rev||{}), qt:Object.assign({},lp.qt||{}),""",
    """       rev:Object.assign({},lp.rev||{}), qt,""")

PAGE.write_text(s, encoding="utf-8"); print("away costs only the open question")
