#!/usr/bin/env python3
"""Round 3: switching tabs was a free break in a simulation.

simBack() pushed the question's deadline out by however long the tab or window had been in
the background. Measured: three minutes in another tab gave the question 180 free seconds,
while the paper's own clock was charged normally. So in a simulation — two breaks, then the
clock keeps running — the way round both the 90-second rule and the break limit was to
switch tabs, look the answer up, and come back to an untouched question.

That also contradicted the rest of the clock: a refresh or a closed tab is charged to the
question (simAwayCost), and leaving through the app's own navigation costs a break. Only
the browser's tab bar was free.

So background time now counts in a simulation, the same as it does for a closed tab. In
practice it is still not spent on the question — practice pauses whenever you leave, and a
glance at another tab is the same kind of thing. When the question runs out while you are
gone, coming back finds it at zero and moves on, exactly as if you had watched it run down.

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

sub("""function simBack(){
  if(!simAwayAt) return;
  const gone=Date.now()-simAwayAt; simAwayAt=0;
  if(sim&&sim.running&&sim.qEndAt&&gone>0) sim.qEndAt+=gone;
  if(sim&&sim.running) simQSync();
}""",
"""function simBack(){
  if(!simAwayAt) return;
  const gone=Date.now()-simAwayAt; simAwayAt=0;
  // Only practice gets the time back. In a simulation another tab is not a free break: a
  // closed tab is charged, leaving through the app costs one of two breaks, and pushing the
  // deadline here made the browser's tab bar the one exit that cost nothing.
  if(sim&&sim.running&&sim.qEndAt&&gone>0&&isPractice()) sim.qEndAt+=gone;
  if(sim&&sim.running) simQSync();
}""")

PAGE.write_text(s, encoding="utf-8")
print("tab-away is charged in a simulation, free in practice")
