#!/usr/bin/env python3
"""Three more from the fifth audit, all around the break.

1. **The break sheet survives submitting the paper.** simAbandon() closed it;
   simSubmit() did not. So finishing a paper with the sheet open left a dialog
   offering a break on a paper that no longer exists, over a result screen.

2. **The nav stays hidden with it.** `body.asking` is cleared by brkAskClose(),
   which submitting never called — so the tabs were gone and the only way back
   was a reload.

3. **A paused paper still takes answers.** simPick() checked whether the question
   was already revealed but not whether the paper was running, so an answer given
   during a break was recorded against a clock that was not moving. You cannot
   normally reach the question screen during a break any more, but simPick is
   reachable from the test surface and from any future caller, and "the paper is
   paused" should mean paused.

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


# ------------------------------------- 1 & 2: the sheet and the nav go with the paper
sub("""  sim.running=false;
  simQStop();
  { const stb=$('simTotal'); if(stb) stb.classList.add('hidden'); }
  { const bb=$('brkBar'); if(bb) bb.classList.add('hidden'); }
  ttsStop(); hideExplain(); simClearSave();""",
"""  sim.running=false;
  simQStop();
  { const stb=$('simTotal'); if(stb) stb.classList.add('hidden'); }
  { const bb=$('brkBar'); if(bb) bb.classList.add('hidden'); }
  // the sheet offers a break on this paper, so it cannot outlive it — and it is what hides
  // the nav, so leaving it open took the tabs with it
  brkAskClose();
  ttsStop(); hideExplain(); simClearSave();""")

# ---------------------------------------- 3: a paused paper does not take answers
sub("""function simPick(ltr){
  if(!sim) return;
  if(sim.rev&&sim.rev[sim.i]) return;        // a revealed question is settled""",
"""function simPick(ltr){
  if(!sim) return;
  if(brkOn()) return;                        // a paused paper is paused for answering too
  if(sim.rev&&sim.rev[sim.i]) return;        // a revealed question is settled""")

PAGE.write_text(s, encoding="utf-8")
print("break edges closed · page %.2f MB" % (len(s) / 1e6))
