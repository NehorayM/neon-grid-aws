#!/usr/bin/env python3
"""Choose the mode at the start, keep it across a refresh, and let practice back in.

Three pieces the behaviour needs to actually hold together.

The picker. Every Start and every Retake asks; Resume does not, because a paper that is
already running has already been answered for. The choice reaches startPaper as an argument
rather than a global, so a test can start either kind directly.

Persistence. sim.mode, brkOpen and brkFrom go into the save alongside brkUsed, or a refresh
during a practice pause would come back as a simulation with the clock running — which is
precisely the exploit that was closed for the timer.

And the guard. During a simulation break the paper is not somewhere you can be, because both
clocks are frozen and it would show a dead countdown. In practice, walking back into the paper
is HOW the break ends, so the same guard would lock you out of your own paper.

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


# ---- startPaper takes the mode ---------------------------------------------------
sub("""function startPaper(n){
  if(n<1||n>PAPER_COUNT) return;""",
"""function startPaper(n,mode){
  if(n<1||n>PAPER_COUNT) return;""")

sub("""  sim={qs,i:0,ans:{},flag:{},rev:{},qt:{},running:true,paper:n,mins:budget,
       startAt:Date.now(),endAt:Date.now()+budget*60000};""",
"""  sim={qs,i:0,ans:{},flag:{},rev:{},qt:{},running:true,paper:n,mins:budget,
       mode:(mode==='practice'?'practice':'exam'),
       startAt:Date.now(),endAt:Date.now()+budget*60000};""")

# ---- the picker ------------------------------------------------------------------
sub("""function brkAskClose(){""",
"""// Which kind of run this is, asked once at the start. Resume never asks: a paper already
// under way was answered for when it began.
let modePending=null;
function modeAsk(label,then){
  modePending=then||null;
  $('modeAskTitle').textContent='How do you want to sit '+label+'?';
  $('modeAskSub').textContent='Same 65 questions and the same clock either way. What changes '+
    'is whether you can stop.';
  $('modeAsk').classList.remove('hidden');
  if(document.body) document.body.classList.add('asking');
}
function modeAskClose(){
  $('modeAsk').classList.add('hidden');
  if(document.body) document.body.classList.remove('asking');
  modePending=null;
}
function modePick(m){
  const then=modePending;
  modeAskClose();
  if(then) then(m);
}
function brkAskClose(){""")

# ---- persistence -----------------------------------------------------------------
sub("""             brkUsed:sim.brkUsed||0, brkUntil:sim.brkUntil||0,""",
"""             mode:sim.mode||'exam', brkUsed:sim.brkUsed||0, brkUntil:sim.brkUntil||0,
             brkOpen:sim.brkOpen?1:0, brkFrom:sim.brkFrom||0,""")

sub("""       rev:sv.rev||{}, qt:qt, brkUsed:sv.brkUsed||0, brkUntil:sv.brkUntil||0,""",
"""       rev:sv.rev||{}, qt:qt, mode:sv.mode==='practice'?'practice':'exam',
       brkUsed:sv.brkUsed||0, brkUntil:sv.brkUntil||0,
       brkOpen:sv.brkOpen?1:0, brkFrom:sv.brkFrom||0,""")

# A paper paused open-endedly owes nothing for the time away — that is what the pause is.
sub("""  const cover=Math.max(0,Math.min(now,Number(sv.brkUntil||0))-at);
  return Math.max(0,Math.round(((now-at)-cover)/1000));""",
"""  if(sv.brkOpen) return 0;   // an open-ended pause covers all of it, however long it ran
  const cover=Math.max(0,Math.min(now,Number(sv.brkUntil||0))-at);
  return Math.max(0,Math.round(((now-at)-cover)/1000));""")

# ---- the guard ------------------------------------------------------------------
sub("""  if(typeof brkOn==='function'&&brkOn()&&IN_PAPER[id]){
    toast('☕ Break — the paper comes back in '+fmtClock(brkRemain()*1000));
    return;
  }""",
"""  if(typeof brkOn==='function'&&brkOn()&&IN_PAPER[id]){
    // A practice pause ends by coming back to the paper, so this is the way in, not a wall.
    if(typeof brkOpen==='function'&&brkOpen()){ brkEnd(false); }
    else {
      toast('☕ Break — the paper comes back in '+fmtClock(brkRemain()*1000));
      return;
    }
  }""")

PAGE.write_text(s, encoding="utf-8")
print("mode chosen, kept and honoured · page %.2f MB" % (len(s) / 1e6))
