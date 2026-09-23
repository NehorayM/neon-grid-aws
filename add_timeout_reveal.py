#!/usr/bin/env python3
"""When a question's time runs out unanswered, show its answer and the full explanation.

It used to move straight on, so a question you ran out of time on was a question you never
learned anything from. Now, if it is unanswered (or only partly answered) when the clock hits
zero, the paper stays on it, marks the correct option, and opens the whole "why each answer"
panel under a "Time ran out" heading. Next moves on when you are ready; reading costs nothing,
because the question's clock is already spent and the paper only runs on question clocks.

On every paper, including the exam-conditions ones: the question is locked and scores as blank
either way, so showing it cannot change a score. An answered question still moves on as before.
The reveal is saved with the paper (sim.rev / sim.tout), so it survives a refresh.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

sub("""  const last=sim.i>=simLen()-1;
  toast(last?'⏳ Time — on to the review':'⏳ '+SIM_QSEC+' seconds — next question');
  simGo(1);
}""",
"""  const last=sim.i>=simLen()-1;
  // Unanswered when the time ran out: stay, and show the answer and why, instead of moving on
  // past a question you would otherwise learn nothing from. Answered ones move on as before.
  const q=QS[sim.qs[sim.i]], picked=sim.ans[sim.i]||[];
  if(picked.length<q.a.length&&!simRevealed()){
    sim.rev=sim.rev||{}; sim.rev[sim.i]=1;
    sim.tout=sim.tout||{}; sim.tout[sim.i]=1;
    simPersist();
    simLoad();
    toast('\\u23f1 Time ran out \\u2014 here is the answer. Tap Next when you are ready');
    return;
  }
  toast(last?'⏳ Time — on to the review':'⏳ '+SIM_QSEC+' seconds — next question');
  simGo(1);
}""")

# the header says what happened
sub("""function renderExplain(q,picked,ok){
  const e=buildExplain(q,picked,ok);
  const box=$('explain');
  const bits=[];
  bits.push('<div class="exhead '+(ok?'ok':'no')+'">'+(ok?'✅ Correct':'❌ Not quite')+""",
"""function renderExplain(q,picked,ok,timedOut){
  const e=buildExplain(q,picked,ok);
  const box=$('explain');
  const bits=[];
  bits.push('<div class="exhead '+(ok?'ok':'no')+'">'+(timedOut?'\\u23f1 Time ran out \\u2014 the answer':ok?'✅ Correct':'❌ Not quite')+""")

sub("""    simPaintRevealed(q,picked);
    renderExplain(q,picked,okNow);
  } else hideExplain();""",
"""    simPaintRevealed(q,picked);
    renderExplain(q,picked,okNow,!!(sim.tout&&sim.tout[sim.i]));
  } else hideExplain();""")

# saved and restored with the paper
sub("""             locked:sim.locked||{}, cont:sim.cont?1:0, base:sim.base||null,""",
    """             locked:sim.locked||{}, cont:sim.cont?1:0, base:sim.base||null, tout:sim.tout||{},""")
sub("""       locked:sv.locked||{}, cont:sv.cont?1:0, base:sv.base||null,""",
    """       locked:sv.locked||{}, cont:sv.cont?1:0, base:sv.base||null, tout:sv.tout||{},""")

PAGE.write_text(s, encoding="utf-8"); print("timeouts reveal")
