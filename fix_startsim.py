#!/usr/bin/env python3
"""The random mock exam button has been throwing, not starting.

startSim() read qs.length while building the object that defines qs:

    sim={qs:simBuild(), ..., mins:simBudget(qs.length), ...}

Inside an object literal the property name qs is not a variable, so this is a plain
ReferenceError — "qs is not defined" — thrown before sim is ever assigned. The button is
470x70 and on screen, and every tap on it did nothing at all. It fails silently because the
handler is an inline arrow and nothing was catching or reporting it.

The questions are built first and their length used after, which is what the numbered papers
already do. And since this is a way into an exam, it asks which kind of run it is like the
others do.

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


sub("""function startSim(){
  ensureAudio(); exitStudyMode();
  reviewMode=false; markMode=false; mock=null;
  sim={qs:simBuild(),i:0,ans:{},flag:{},rev:{},running:true,
       paper:0,mins:simBudget(qs.length),qt:{},
       startAt:Date.now(),endAt:Date.now()+simBudget(qs.length)*60000};
  saveProfile();""",
"""function startSim(mode){
  ensureAudio(); exitStudyMode();
  reviewMode=false; markMode=false; mock=null;
  // Built first, then measured. Reading qs.length from inside the object literal that defines
  // the qs PROPERTY is a ReferenceError, and it threw before sim was ever assigned.
  const qs=simBuild();
  const budget=simBudget(qs.length);
  simClearSave();
  sim={qs,i:0,ans:{},flag:{},rev:{},running:true,
       paper:0,mins:budget,qt:{},
       mode:(mode==='practice'?'practice':'exam'),
       startAt:Date.now(),endAt:Date.now()+budget*60000};
  saveProfile();""")

sub("""$('simOpen').onclick=()=>{ startSim(); };""",
    """$('simOpen').onclick=()=>modeAsk('the mock exam',m=>startSim(m));""")

sub("""  else startSim();""",
    """  else startSim((sim&&sim.mode)||'exam');""")

PAGE.write_text(s, encoding="utf-8")
print("the mock exam starts now · page %.2f MB" % (len(s) / 1e6))
