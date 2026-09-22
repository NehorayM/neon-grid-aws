#!/usr/bin/env python3
"""Persist the question clock properly instead of relying on a coincidence.

Measured across a real reload: the save's `qt` was `{}` after 25 seconds on
question one. The resume still landed on roughly the right number, but only
because `at` happened to be stamped at the same moment the question loaded, so
"time since `at`" and "time spent on this question" were the same figure. That is
a coincidence, not a design, and it breaks in two ways:

  * `P.simSave.qt` was assigned `sim.qt` **by reference**. Every later tick
    mutates the saved object too, so any unrelated saveProfile() — answering
    awards XP and coins, which saves — serialises the *current* per-question
    times against a *stale* `at`. The resume then charges the elapsed time a
    second time on top of a figure that had already been reduced.
  * Between persists the stored `qt` and `at` describe different moments, so how
    much of the question you get back depends on which of them last moved.

Now: `qt` is copied into the save, and a running paper persists every ten
seconds. The pair always describes one moment, and a crash loses at most ten
seconds of bookkeeping rather than depending on when the last answer was given.

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


# ------------------------------------------------- the save gets its own copy
sub("""  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},
             qt:sim.qt||{}, brkUsed:sim.brkUsed||0, brkUntil:sim.brkUntil||0,""",
"""  // A copy, not the live object. Sharing the reference meant every tick quietly rewrote the
  // save's per-question times while `at` stayed where it was, so any unrelated saveProfile()
  // wrote a pair describing two different moments — and the resume charged the gap twice.
  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},
             qt:Object.assign({},sim.qt||{},{[sim.i]:Math.max(0,simQLeft)}),
             brkUsed:sim.brkUsed||0, brkUntil:sim.brkUntil||0,""")

# ---------------------------------------- a running paper saves itself every ten seconds
sub("""function simQSync(){
  if(!sim||!sim.running){ simQStop(); return; }
  if(brkOn()) return;                                           // the paper is paused""",
"""let simSaveTick=0;
function simQSync(){
  if(!sim||!sim.running){ simQStop(); return; }
  if(brkOn()) return;                                           // the paper is paused""")

sub("""  simQLeft=left;
  sim.qt=sim.qt||{}; sim.qt[sim.i]=simQLeft;
  renderSimQ();
  if(simQLeft<=0){ sim.qEndAt=0; simQTimeUp(); }
}""",
"""  simQLeft=left;
  sim.qt=sim.qt||{}; sim.qt[sim.i]=simQLeft;
  renderSimQ();
  // Write it down every ten seconds. The `at`-based correction makes a resume exact anyway,
  // but only while the stored qt and at describe the same moment — persisting keeps them
  // together instead of leaving it to whenever an answer last happened to save.
  if(++simSaveTick>=10){ simSaveTick=0; simPersist(); }
  if(simQLeft<=0){ sim.qEndAt=0; simQTimeUp(); }
}""")

sub("""    simAwayCost, simPauseSave,""",
"""    simAwayCost, simPauseSave, get simSaveTick(){return simSaveTick;},""")

PAGE.write_text(s, encoding="utf-8")
print("the question clock is written down now · page %.2f MB" % (len(s) / 1e6))
