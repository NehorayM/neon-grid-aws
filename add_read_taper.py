#!/usr/bin/env python3
"""Take the read-aloud button away gradually, so practice moves toward reading on your own.

  Exams 1-7    on every question
  Exams 8-10   hidden on even-numbered questions (2, 4, 6 ...)
  Exams 11-12  shown once every three questions (1, 4, 7 ...)
  Exams 13+    never

The mock exam (no paper number) keeps it. A question without the button also cannot be read by
anything else that calls simSpeak(), and anything already reading stops when you land on it.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

sub("""function renderTtsBtn(){
  const b=$('simTts'); if(!b) return;""",
"""// Whether this question gets the read-aloud button. It thins out as the papers go on, so the
// later ones are practice at reading the question yourself, as the real exam requires.
function readAllowed(paper,i){
  paper=Number(paper)||0; i=Number(i)||0;       // i is 0-based, questions are numbered from 1
  if(!paper||paper<=7) return true;
  if(paper<=10) return (i+1)%2===1;              // 8-10: not on even questions
  if(paper<=12) return i%3===0;                  // 11-12: once every three (1, 4, 7 ...)
  return false;                                  // 13 on: never
}
function renderTtsBtn(){
  const b=$('simTts'); if(!b) return;
  const allowed=!sim||readAllowed(sim.paper,sim.i);
  b.classList.toggle('hidden',!allowed);
  if(!allowed&&ttsOn) ttsStop();""")

sub("""  if(!ttsOk()){ toast('This browser cannot read aloud'); return; }
  if(ttsOn) ttsStop();""",
"""  if(!ttsOk()){ toast('This browser cannot read aloud'); return; }
  if(sim&&!readAllowed(sim.paper,sim.i)&&!ttsOn){ renderTtsBtn(); return; }
  if(ttsOn) ttsStop();""")

sub("    isPractice, brkOpen, brkElapsed,", "    isPractice, brkOpen, brkElapsed, readAllowed,")
PAGE.write_text(s, encoding="utf-8"); print("read-aloud tapers")
