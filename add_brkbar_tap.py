#!/usr/bin/env python3
"""Make the paused bar the way back into a practice paper.

The bar said "tap Exam to pick it back up", which lands on the paper list and needs a second
tap on Resume. The bar is already on screen, already says the paper is paused, and is the
thing you are looking at when you want it back — so it is the button.

Only in practice. A simulation break is timed and the paper genuinely is not somewhere you
can be until it ends, so that bar stays a status line and says so.

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


sub("""  const txt=bar.querySelector('.btxt');
  if(txt) txt.textContent=brkOpen()?'Paused — tap Exam to pick it back up'
                                   :'Paper paused — it comes back on its own';""",
"""  const txt=bar.querySelector('.btxt');
  if(txt) txt.textContent=brkOpen()?'Paused — tap to pick the paper back up'
                                   :'Paper paused — it comes back on its own';
  // A timed break is a status line; an open one is the way back in.
  bar.classList.toggle('tappable',brkOpen());
  bar.setAttribute('role',brkOpen()?'button':'status');
  if(brkOpen()) bar.setAttribute('tabindex','0'); else bar.removeAttribute('tabindex');
  bar.setAttribute('aria-label',brkOpen()
    ?'Paper paused. Activate to go back to question '+((sim&&sim.i||0)+1)
    :'Paper paused, back in '+fmtClock(brkRemain()*1000));""")

sub("""$('brkAskNo').onclick=()=>brkAskClose();""",
"""// the paused bar is the way back into a practice paper
$('brkBar').onclick=()=>{ if(brkOpen()) go('quizScreen'); };
$('brkBar').onkeydown=e=>{
  if(!brkOpen()) return;
  if(e.key==='Enter'||e.key===' '){ e.preventDefault(); go('quizScreen'); }
};
$('brkAskNo').onclick=()=>brkAskClose();""")

sub("""#brkBar.hidden{display:none}""",
"""#brkBar.hidden{display:none}
#brkBar.tappable{cursor:pointer}
#brkBar.tappable:hover,#brkBar.tappable:focus-visible{
  background:color-mix(in srgb, var(--cyan) 22%, var(--bg2));
  border-color:color-mix(in srgb, var(--cyan) 70%, var(--line))}""")

PAGE.write_text(s, encoding="utf-8")
print("the paused bar takes you back · page %.2f MB" % (len(s) / 1e6))
