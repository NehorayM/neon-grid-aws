#!/usr/bin/env python3
"""Show what is left of the whole paper, not just of this question.

The clock showed 1:30 for the current question and nothing about the paper. The
budget is the sum of every question's ninety seconds — 65 x 90s = 97:30 at the
start, 64 x 90s = 96:00 once the first is done — and that number is the one that
tells you whether you are ahead or behind.

It is a real sum rather than a multiplication: a question you left with thirty
seconds on it still has thirty seconds, and going back to it gives them back. So
simTotalLeft() adds up what each question actually has, using the live counter
for the one you are on.

Two places show it:

  * the top clock's second line, so it is on screen the whole time
  * a strip under the question: the remaining time, how many questions it covers,
    and a bar ticked once per question so "65 x 90 seconds" is something you can
    see rather than work out

The strip turns amber when the time left drops below what the questions left
would need at full price, which is the moment you have started spending other
questions' time.

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


# ------------------------------------------------------------------- markup
sub("""      <div id="qTimerWrap" class="hidden"><i id="qTimerFill"></i></div>""",
"""      <div id="qTimerWrap" class="hidden"><i id="qTimerFill"></i></div>
      <div id="simTotal" class="simtotal hidden">
        <div class="stline">
          <span class="stlbl">Paper remaining</span>
          <span class="stval" id="simTotalVal">—</span>
        </div>
        <div class="sttrack"><i id="simTotalFill"></i></div>
        <div class="stsub" id="simTotalSub"></div>
      </div>""")

# ------------------------------------------------------------------ styling
sub("""#qTimerWrap{height:5px;""",
"""/* The paper's own budget, under the question's five-pixel bar. The track is ticked once per
   question by a repeating gradient, so "65 x 90 seconds" is visible rather than arithmetic. */
.simtotal{margin:6px 0 2px;padding:9px 11px;border-radius:11px;
  background:color-mix(in srgb, var(--cyan) 5%, var(--surface));
  border:1px solid color-mix(in srgb, var(--cyan) 22%, var(--line))}
.simtotal.hidden{display:none}
.simtotal.tight{background:color-mix(in srgb, var(--gold) 6%, var(--surface));
  border-color:color-mix(in srgb, var(--gold) 34%, var(--line))}
.stline{display:flex;align-items:baseline;gap:8px}
.stlbl{font-family:var(--mono);font-size:9.5px;letter-spacing:1px;text-transform:uppercase;
  color:var(--dim);flex:1;min-width:0}
.stval{font-family:var(--mono);font-size:17px;font-weight:700;color:var(--cyan);
  font-variant-numeric:tabular-nums;letter-spacing:.5px}
.simtotal.tight .stval{color:var(--gold)}
.sttrack{position:relative;height:7px;border-radius:4px;margin:7px 0 5px;overflow:hidden;
  background:rgba(255,255,255,.07)}
.sttrack i{display:block;height:100%;border-radius:4px;transition:width .95s linear;
  background:linear-gradient(90deg,
    color-mix(in srgb, var(--cyan) 55%, transparent), var(--cyan))}
.simtotal.tight .sttrack i{background:linear-gradient(90deg,
    color-mix(in srgb, var(--gold) 55%, transparent), var(--gold))}
/* one tick per question, laid over the fill */
.sttrack::after{content:'';position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(90deg,
    transparent 0, transparent calc(var(--tick,4%) - 1px),
    rgba(0,0,0,.45) calc(var(--tick,4%) - 1px), rgba(0,0,0,.45) var(--tick,4%))}
.stsub{font-size:11px;color:var(--dim);line-height:1.4}
#qTimerWrap{height:5px;""")

# -------------------------------------------------------------- the arithmetic
sub("""function renderSimQ(){""",
"""// What the whole paper has left: every question's own remaining seconds added up, with the
// live counter standing in for the one being answered. A question left with thirty seconds on
// it still has thirty, so this is a sum rather than questions-remaining times ninety.
function simTotalLeft(){
  if(!sim) return 0;
  let t=0;
  for(let i=0;i<simLen();i++){
    if(i===sim.i){ t+=Math.max(0,simQLeft); continue; }
    const v=sim.qt?sim.qt[i]:undefined;
    t+=(typeof v==='number')?Math.max(0,v):SIM_QSEC;
  }
  return t;
}
const simTotalFull=()=>simLen()*SIM_QSEC;
// how many questions have any time left on them at all
function simQsLeft(){
  if(!sim) return 0;
  let n=0;
  for(let i=0;i<simLen();i++){
    if(i===sim.i){ if(simQLeft>0) n++; continue; }
    const v=sim.qt?sim.qt[i]:undefined;
    if((typeof v==='number'?v:SIM_QSEC)>0) n++;
  }
  return n;
}
function renderSimTotal(){
  const box=$('simTotal'); if(!box) return;
  if(!sim||!sim.running){ box.classList.add('hidden'); return; }
  box.classList.remove('hidden');
  const left=simTotalLeft(), full=simTotalFull(), qs=simQsLeft();
  $('simTotalVal').textContent=fmtClock(left*1000);
  $('simTotalFill').style.width=pctW(left/Math.max(1,full)*100);
  $('simTotalSub').textContent=plural(qs,'question')+' still open \\u00b7 '+
    SIM_QSEC+'s each \\u00b7 '+fmtClock(full*1000)+' for the paper';
  // ticked once per question, capped so the ticks do not turn into a solid block
  const tick=Math.max(1.6,100/Math.max(1,simLen()));
  $('simTotal').style.setProperty('--tick',tick.toFixed(2)+'%');
  // amber once the time left is under what the open questions would need at full price
  box.classList.toggle('tight',left<qs*SIM_QSEC);
}
function renderSimQ(){""")

sub("""  fill.classList.toggle('low',simQLeft<=20);
  renderClock();
}""",
"""  fill.classList.toggle('low',simQLeft<=20);
  renderSimTotal();
  renderClock();
}""")

# ------------------------------------------- the top clock carries it too
sub("""    const sub0=$('clockSub'); if(sub0) sub0.textContent='this question';""",
"""    const sub0=$('clockSub');
    if(sub0) sub0.textContent=(typeof simTotalLeft==='function')
      ? (fmtClock(simTotalLeft()*1000)+' left')
      : 'this question';""")

# and it is hidden again when the paper ends
sub("""  $('simBar').classList.remove('show');
  $('chargeBar').style.display='';""",
"""  $('simBar').classList.remove('show');
  const stb=$('simTotal'); if(stb) stb.classList.add('hidden');
  $('chargeBar').style.display='';""")

sub("""    SIM_QSEC, simBudget, simQStart, simQStop, simQTick, simQTimeUp, renderSimQ,""",
"""    SIM_QSEC, simBudget, simQStart, simQStop, simQTick, simQTimeUp, renderSimQ,
    simTotalLeft, simTotalFull, simQsLeft, renderSimTotal,""")

PAGE.write_text(s, encoding="utf-8")
print("paper-remaining strip added · page %.2f MB" % (len(s) / 1e6))
