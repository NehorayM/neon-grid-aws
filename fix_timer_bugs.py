#!/usr/bin/env python3
"""Three things: a hole in the break guard, a strip that outlived its paper, and
a build stamp so "is it cached?" stops being guesswork.

1. **Leaving from the review screen skipped the break check entirely.** The guard
   asked for `route==='quizScreen'`, so pressing Home from the review grid walked
   straight out of a running paper with no break taken and both clocks running.
   The condition is now "anywhere inside the paper", which is what it always
   meant.

2. **The paper-remaining strip survived submitting.** simSubmit() tore down the
   exam bar but not the strip, so it sat on the result screen showing the time a
   finished paper had left.

3. **A build stamp.** A screenshot arrived showing a bug that was already fixed
   and deployed — the page was a cached copy, and there was no way to tell that
   from the outside. The Records screen now shows which build is running, and it
   is the first thing to check when a fixed bug reappears.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# ---------------------------------------- 1. leaving the paper from ANY of its screens
sub("""  if(typeof sim!=='undefined'&&sim&&sim.running&&!IN_PAPER[id]&&!brkOn()
     &&route==='quizScreen'&&typeof brkAsk==='function'){""",
"""  // This used to ask for route==='quizScreen', which meant pressing Home from the review
  // grid walked straight out of a running paper with no break and both clocks running.
  // Leaving means leaving from anywhere the paper owns.
  if(typeof sim!=='undefined'&&sim&&sim.running&&!IN_PAPER[id]&&!brkOn()
     &&IN_PAPER[route]&&typeof brkAsk==='function'){""")

# --------------------------------------------- 2. the strip goes when the paper does
sub("""  sim.running=false;
  ttsStop(); hideExplain(); simClearSave();""",
"""  sim.running=false;
  simQStop();
  { const stb=$('simTotal'); if(stb) stb.classList.add('hidden'); }
  { const bb=$('brkBar'); if(bb) bb.classList.add('hidden'); }
  ttsStop(); hideExplain(); simClearSave();""")

# ------------------------------------------------------------- 3. the build stamp
try:
    rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE,
                         capture_output=True, text=True).stdout.strip() or "dev"
except Exception:
    rev = "dev"
stamp = subprocess.run(["date", "-u", "+%Y-%m-%d %H:%M"], capture_output=True,
                       text=True).stdout.strip()

sub("""const BANKV=""",
"""// A screenshot arrived showing a bug that was already fixed and deployed: the page was a
// cached copy and nothing on it said so. This is the first thing to check when a fixed bug
// comes back. It is also on the Records screen.
const BUILD='%s · %s';
const BANKV=""" % (rev, stamp))

sub("""    syncQBar, leaveExam, pctW, plural, accPct,""",
"""    syncQBar, leaveExam, pctW, plural, accPct, BUILD,""")

PAGE.write_text(s, encoding="utf-8")
print("guard widened, strip cleared, build stamped as %s" % rev)
