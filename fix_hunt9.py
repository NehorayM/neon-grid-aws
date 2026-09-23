#!/usr/bin/env python3
"""Bug-hunting round: three confirmed bugs.

1. A question whose 90 seconds had run out could still be answered. The clock hit 0:00 and
   moved you on, but going back from the review grid let you pick an answer anyway — so the
   limit could be sidestepped by letting a question expire, thinking elsewhere, and returning.
   A question with no time left is now read-only, and says so.

2. A timed break that ran out while the tab was in the background was charged as time away.
   Twenty minutes away, six of them a legitimate break, cost the paper twenty minutes. The
   break's own span is now covered, as it already was for a closed tab (simAwayCost).

3. Chests only paid out from practice answers — checkChest() had one caller. A 65-question
   exam added 65 to the answer count without looking, so the home screen sat on "Next chest in
   0 questions" until the next practice answer, and then paid one chest where the exam had
   crossed two or three. It now runs after an exam too, and pays every threshold crossed.

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

# 1 -----------------------------------------------------------------------------------------
sub("""  if(sim.locked&&sim.locked[sim.i]){ toast('Answered in the first sitting \\u2014 locked'); return; }""",
"""  if(sim.locked&&sim.locked[sim.i]){ toast('Answered in the first sitting \\u2014 locked'); return; }
  // Out of time is out of time. Going back from the review grid used to let you answer a
  // question whose clock had already run out — the limit, sidestepped.
  if(simQLeft<=0&&!brkOn()){ toast('\\u23f1 Time ran out on this question \\u2014 it can be read, not answered'); return; }""")

# 2 -----------------------------------------------------------------------------------------
sub("""let simAwayAt=0, simAwayQ=0;
function simAway(){ if(!simAwayAt){ simAwayAt=Date.now(); simAwayQ=Math.max(0,simQLeft|0); } }""",
"""let simAwayAt=0, simAwayQ=0, simAwayBrk=0;
function simAway(){ if(!simAwayAt){ simAwayAt=Date.now(); simAwayQ=Math.max(0,simQLeft|0);
  // a timed break already running covers its own span, however long we are gone
  simAwayBrk=(sim&&brkOn()&&!brkOpen())?Number(sim.brkUntil)||0:0; } }""")

sub("""  const gone=Date.now()-simAwayAt; simAwayAt=0;""",
"""  const now=Date.now(), cover=Math.max(0,Math.min(now,simAwayBrk)-simAwayAt);
  const gone=Math.max(0,now-simAwayAt-cover); simAwayAt=0; simAwayBrk=0;""")

# 3 -----------------------------------------------------------------------------------------
sub("""  if(P.answered>=P.nextChest){
    const reward=35+Math.floor(P.nextChest/25)*5;
    P.nextChest+=25; addCoins(reward); saveProfile();""",
"""  // Every threshold crossed pays — an exam adds 65 answers at once and crossed two or three.
  let paid=0, total=0;
  while(P.answered>=P.nextChest&&paid<40){
    const reward=35+Math.floor(P.nextChest/25)*5;
    P.nextChest+=25; total+=reward; paid++;
  }
  if(paid){
    addCoins(total); saveProfile();""")

PAGE.write_text(s, encoding="utf-8")
print("three fixed (chest needs its tail checked)")
