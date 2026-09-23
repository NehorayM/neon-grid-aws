#!/usr/bin/env python3
"""A practice paper pauses for as long as you want; a simulation gets two six-minute breaks.

The break machinery was built around a deadline — brkUntil is the moment the break ends, and
both clocks are pushed out by exactly BREAK_SECS when it does. That is right for a simulation
and wrong for practice, where a break has no length: the paper stops when you leave and starts
again when you come back, and what the clocks owe is however long you were actually gone.

So an open-ended break is a separate state. sim.brkOpen marks it and sim.brkFrom records when
it began, and brkEnd pays the clocks back the measured elapsed time rather than a fixed six
minutes. Everything that asks "is the paper paused" goes through brkOn() and keeps working.

Two knock-on rules:
  - In a simulation the paper is not somewhere you can be during a break, because both clocks
    are frozen and it would show a dead countdown. In practice, walking back INTO the paper is
    how a break ends, so that guard would lock you out of your own paper.
  - A resume has to charge for time away, minus anything a break covered. An open break covers
    all of it, which is the whole point of it.

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


# ---- the mode itself -------------------------------------------------------------
sub("""const BREAK_MAX=2, BREAK_SECS=360;
const brkLeft=()=>sim?Math.max(0,BREAK_MAX-(sim.brkUsed||0)):0;
const brkOn=()=>!!(sim&&sim.brkUntil&&sim.brkUntil>Date.now());
const brkRemain=()=>brkOn()?Math.max(0,Math.ceil((sim.brkUntil-Date.now())/1000)):0;""",
"""const BREAK_MAX=2, BREAK_SECS=360;
// A paper is sat one of two ways. 'exam' is the real thing and the default; 'practice' trades
// the two-break rule for stopping whenever you like, because a paper you are learning from is
// not a paper you are being timed on.
const isPractice=()=>!!(sim&&sim.mode==='practice');
const brkLeft=()=>!sim?0:isPractice()?Infinity:Math.max(0,BREAK_MAX-(sim.brkUsed||0));
// A practice break has no end time — it lasts until you walk back into the paper.
const brkOpen=()=>!!(sim&&sim.brkOpen);
const brkOn=()=>!!(sim&&(brkOpen()||(sim.brkUntil&&sim.brkUntil>Date.now())));
const brkRemain=()=>(brkOn()&&!brkOpen())?Math.max(0,Math.ceil((sim.brkUntil-Date.now())/1000)):0;
// how long an open break has been running, for the bar
const brkElapsed=()=>brkOpen()?Math.max(0,Date.now()-Number(sim.brkFrom||Date.now())):0;""")

sub("""function brkStart(){
  if(!sim||!sim.running||brkOn()||!brkLeft()) return false;
  sim.brkUsed=(sim.brkUsed||0)+1;
  sim.brkUntil=Date.now()+BREAK_SECS*1000;
  simQStop();                       // the question's own countdown stops dead
  ttsStop();
  simPersist();
  renderBrk(); renderClock();
  toast('\\u2615 Break started \\u2014 6 minutes, the paper is paused');
  return true;
}""",
"""function brkStart(){
  if(!sim||!sim.running||brkOn()||!brkLeft()) return false;
  sim.brkUsed=(sim.brkUsed||0)+1;
  if(isPractice()){ sim.brkOpen=1; sim.brkFrom=Date.now(); sim.brkUntil=0; }
  else sim.brkUntil=Date.now()+BREAK_SECS*1000;
  simQStop();                       // the question's own countdown stops dead
  ttsStop();
  simPersist();
  renderBrk(); renderClock();
  toast(isPractice()?'\\u2615 Paper paused \\u2014 come back whenever you are ready'
                    :'\\u2615 Break started \\u2014 6 minutes, the paper is paused');
  return true;
}""")

sub("""function brkEnd(quiet){
  if(!sim||!sim.brkUntil) return;
  const over=BREAK_SECS*1000;
  sim.brkUntil=0;""",
"""function brkEnd(quiet){
  if(!sim||!brkOn()) return;
  // A timed break always costs its full length; an open one costs however long it actually
  // ran, which is the only number that can be right when it has no length of its own.
  const over=brkOpen()?brkElapsed():BREAK_SECS*1000;
  const wasOpen=brkOpen();
  sim.brkUntil=0; sim.brkOpen=0; sim.brkFrom=0;""")

sub("""  renderBrk(); renderClock();
  if(!quiet) toast('\\u23f0 Break over \\u2014 back to the paper');""",
"""  renderBrk(); renderClock();
  if(!quiet) toast(wasOpen?'\\u25b6 Back to the paper':'\\u23f0 Break over \\u2014 back to the paper');""")

sub("""function brkTick(){
  if(!sim||!sim.brkUntil) return;
  if(brkRemain()<=0){ brkEnd(false); return; }
  renderBrk(); renderClock();
}""",
"""function brkTick(){
  if(!sim||!brkOn()) return;
  // An open break never runs out. It ends when you come back, not when a clock says so.
  if(!brkOpen()&&brkRemain()<=0){ brkEnd(false); return; }
  renderBrk(); renderClock();
}""")

sub("""  const txt=bar.querySelector('.btxt');
  if(txt) txt.textContent='Paper paused — it comes back on its own';
  $('brkClock').textContent=fmtClock(brkRemain()*1000);""",
"""  const txt=bar.querySelector('.btxt');
  if(txt) txt.textContent=brkOpen()?'Paused — tap Exam to pick it back up'
                                   :'Paper paused — it comes back on its own';
  $('brkClock').textContent=brkOpen()?fmtClock(brkElapsed()):fmtClock(brkRemain()*1000);""")

# ---- asking. A practice break costs nothing, so there is nothing to ask about ------
sub("""function brkAsk(go2){
  if(!sim||!sim.running) return false;
  if(brkOn()) return false;
  if(!brkLeft()){""",
"""function brkAsk(go2){
  if(!sim||!sim.running) return false;
  if(brkOn()) return false;
  // Nothing to weigh up in practice: the pause is free and reversible, so asking would only
  // be a dialog between you and the thing you already asked for.
  if(isPractice()){ brkStart(); if(go2) go2(); return true; }
  if(!brkLeft()){""")

PAGE.write_text(s, encoding="utf-8")
print("open-ended breaks wired · page %.2f MB" % (len(s) / 1e6))
