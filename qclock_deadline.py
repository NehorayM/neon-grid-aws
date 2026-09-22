#!/usr/bin/env python3
"""Drive the question clock from a deadline, and heal it if the interval dies.

Reported: neither the big number nor the paper-remaining figure moves. It ticks
correctly in the preview browser here, so this is about the reporting device, and
counting interval fires is the fragile part of the design:

  * a throttled or suspended timer means fewer fires, so the clock either drifts
    slow or stops entirely while the page sits there looking live
  * if the interval is ever lost — a stray simQStop(), a navigation that did not
    re-arm it — nothing brings it back, and the display freezes with no error

Both go away if the clock is a deadline rather than a count. `sim.qEndAt` is when
this question runs out; the remaining seconds are computed from it every tick, so
however many fires arrive, the number shown is the truth. Missing a fire now
means the display updates a moment late rather than losing a second forever.

Pausing is preserved: the question clock still must not run while the app is in
the background or while you are on the review screen, so the deadline is pushed
forward by however long that lasted rather than the tick being skipped.

And clockTick(), which runs once a second for the top bar anyway, now re-arms the
question interval if an exam is running without one. If this was a lost interval,
it fixes itself within a second.

simQTick(n) still works for the harness, and moves the deadline with it so the
two can never disagree.

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


sub("""function simQStart(){
  simQStop();
  if(!sim||!sim.running) return;
  simQLeft=simQLeftFor(sim.i);
  renderSimQ();
  // a question whose time is already gone can still be opened from the review list —
  // it just shows an empty clock instead of bouncing you straight out of it again
  if(simQLeft<=0) return;
  if(TEST) return;                        // the tests drive it with simQTick()
  simQIv=setInterval(()=>simQTick(1),1000);
}
function simQTick(by){
  if(!sim||!sim.running){ simQStop(); return; }
  if(simQLeft<=0){ simQStop(); return; }                        // it only runs out once
  if(route!=='quizScreen') return;                              // not on the review screen
  if(typeof document!=='undefined'&&document.hidden) return;    // nor in the background
  simQLeft=Math.max(0,simQLeft-(by||1));
  sim.qt=sim.qt||{}; sim.qt[sim.i]=simQLeft;
  renderSimQ();
  if(simQLeft<=0) simQTimeUp();
}""",
"""function simQStart(){
  simQStop();
  if(!sim||!sim.running) return;
  simQLeft=simQLeftFor(sim.i);
  sim.qEndAt=Date.now()+simQLeft*1000;    // the clock is a deadline, not a count of ticks
  renderSimQ();
  // a question whose time is already gone can still be opened from the review list —
  // it just shows an empty clock instead of bouncing you straight out of it again
  if(simQLeft<=0){ sim.qEndAt=0; return; }
  if(TEST) return;                        // the tests drive it with simQTick()
  simQIv=setInterval(simQSync,1000);
}
// Counting interval fires meant a throttled or suspended timer either ran slow or stopped
// dead while the page sat there looking live. Reading the deadline instead means a missed
// fire shows up a moment late rather than costing a second that never comes back.
function simQSync(){
  if(!sim||!sim.running){ simQStop(); return; }
  if(!sim.qEndAt) return;
  if(route!=='quizScreen') return;                              // not on the review screen
  if(typeof document!=='undefined'&&document.hidden) return;    // nor in the background
  const left=Math.max(0,Math.ceil((sim.qEndAt-Date.now())/1000));
  if(left===simQLeft&&left>0) return;
  simQLeft=left;
  sim.qt=sim.qt||{}; sim.qt[sim.i]=simQLeft;
  renderSimQ();
  if(simQLeft<=0){ sim.qEndAt=0; simQTimeUp(); }
}
// The harness drives the clock by hand. The deadline moves with it, so the two never disagree.
function simQTick(by){
  if(!sim||!sim.running){ simQStop(); return; }
  if(simQLeft<=0){ simQStop(); return; }                        // it only runs out once
  if(route!=='quizScreen') return;
  if(typeof document!=='undefined'&&document.hidden) return;
  simQLeft=Math.max(0,simQLeft-(by||1));
  sim.qEndAt=Date.now()+simQLeft*1000;
  sim.qt=sim.qt||{}; sim.qt[sim.i]=simQLeft;
  renderSimQ();
  if(simQLeft<=0){ sim.qEndAt=0; simQTimeUp(); }
}
// Time spent in the background or on the review screen is not spent on the question, so the
// deadline is pushed forward by however long that lasted instead of the ticks being skipped.
let simAwayAt=0;
function simAway(){ if(!simAwayAt) simAwayAt=Date.now(); }
function simBack(){
  if(!simAwayAt) return;
  const gone=Date.now()-simAwayAt; simAwayAt=0;
  if(sim&&sim.running&&sim.qEndAt&&gone>0) sim.qEndAt+=gone;
  if(sim&&sim.running) simQSync();
}
if(typeof document!=='undefined'){
  document.addEventListener('visibilitychange',()=>{ document.hidden?simAway():simBack(); });
}
if(typeof window!=='undefined'){
  window.addEventListener('blur',simAway);
  window.addEventListener('focus',simBack);
}""")

# ------------------------------------------- an exam without a clock repairs itself
sub("""  if(typeof timerTick==='function') timerTick();
  if(typeof renderTimer==='function') renderTimer();
  renderClock();
}""",
"""  if(typeof timerTick==='function') timerTick();
  if(typeof renderTimer==='function') renderTimer();
  // If an exam is running with no question interval behind it, the display would sit frozen
  // with nothing to show for it. This runs every second anyway, so it can put it back.
  if(typeof sim!=='undefined'&&sim&&sim.running&&!TEST){
    if(!simQIv&&simQLeft>0&&route==='quizScreen') simQStart();
    else if(typeof simQSync==='function') simQSync();
  }
  renderClock();
}""")

sub("""    simTotalLeft, simTotalFull, simQsLeft, renderSimTotal,""",
"""    simTotalLeft, simTotalFull, simQsLeft, renderSimTotal, simQSync, simAway, simBack,
    get simQIv(){return simQIv;},""")

PAGE.write_text(s, encoding="utf-8")
print("question clock is a deadline now, and repairs itself · page %.2f MB" % (len(s) / 1e6))
