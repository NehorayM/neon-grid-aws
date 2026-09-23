#!/usr/bin/env python3
"""Round 5: tapping a third option on a "Select 2" question did nothing, silently.

With the required number already picked, a further tap returned early in all three places
answers are picked — the practice quiz, the exam, and the duel. Nothing moved, nothing
sounded, nothing said why, which reads as a dead button in the middle of a timed question.
The real exam tells you when you are at the limit, and so does this now: the option you
tapped gives a short shake, and a toast says how many the question takes and how to change.

(Checked the bank while here: all 125 multi-answer questions have exactly as many letters
in their key as their stem says to choose, so the cap itself is always the right number.)

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

# one helper, used by all three
sub("""function toggleOpt(ltr,btn){""",
"""// At the limit on a multi-answer question, a further tap used to vanish without a trace.
function pickFull(need,el){
  if(el){ el.classList.remove('nope'); void el.offsetWidth; el.classList.add('nope'); }
  if(typeof sfx!=='undefined'&&sfx.nope) sfx.nope();
  toast('This one takes '+need+' \\u2014 tap a picked answer to drop it first');
}
function toggleOpt(ltr,btn){""")

sub("""  else { if(need===1) chosen.clear(); if(chosen.size>=need) return; chosen.add(ltr); }
  sfx.tap();""",
"""  else {
    if(need===1) chosen.clear();
    if(chosen.size>=need){ pickFull(need,btn||[...$('qOpts').children].find(e=>e.dataset.ltr===ltr)); return; }
    chosen.add(ltr);
  }
  sfx.tap();""")

sub("""  else { if(need===1) cur.clear(); if(cur.size>=need) return; cur.add(ltr); }""",
"""  else {
    if(need===1) cur.clear();
    if(cur.size>=need){ pickFull(need,[...$('qOpts').children].find(e=>e.dataset.ltr===ltr)); return; }
    cur.add(ltr);
  }""")

sub("""      else { if(need===1) duelPicked.clear(); if(duelPicked.size>=need) return; duelPicked.add(ltr); }""",
"""      else {
        if(need===1) duelPicked.clear();
        if(duelPicked.size>=need){ pickFull(need,b); return; }
        duelPicked.add(ltr);
      }""")

sub("""@keyframes pillPop{""",
"""@keyframes nope{0%,100%{transform:none}20%{transform:translateX(-5px)}40%{transform:translateX(5px)}60%{transform:translateX(-3px)}80%{transform:translateX(3px)}}
.opt.nope{animation:nope .32s ease}
@media (prefers-reduced-motion:reduce){.opt.nope{animation:none;outline:2px solid var(--red)}}
@keyframes pillPop{""")

PAGE.write_text(s, encoding="utf-8")
print("a tap past the limit says so")
