#!/usr/bin/env python3
"""The remaining low and medium findings, plus what turned up while fixing them.

  * domainStats() computed acc as c/a with nothing clamping it. secStats is
    merged across devices by "keep the record with more answers", and a profile
    that lands with c > a reports over 100% accurate on the Readiness screen and
    feeds a score above 100 into readiness(). readiness() clamps its own total,
    so the top-line number was safe — the per-domain rows were not.
  * The Flashcards tile advertised 88 terms. The deck has been 90 since the codex
    was rewritten. It now counts the deck instead of stating a number that has to
    be maintained by hand.
  * P.lastLearn and P.lastTimer were written and never read. lastTimer is now what
    the timer screen opens with, which is what writing it was clearly for;
    lastLearn is removed.
  * comboBreak() and openStudy2() were dead. comboBreak duplicated logic that
    tickCombo already does; openStudy2 was reachable only from the test surface.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# ------------------------------------------------- accuracy cannot exceed 100%
sub("""    const target=Math.max(20,Math.round(pool*0.25));      // a sensible sample of each domain
    return {...d, a, c, pool, target, acc:a?c/a:0, cov:Math.min(1,a/target)};""",
"""    const target=Math.max(20,Math.round(pool*0.25));      // a sensible sample of each domain
    // secStats merges across devices by keeping whichever record has more answers, which can
    // land a profile with more correct than answered. Unclamped that reads "104% accurate".
    return {...d, a, c, pool, target,
            acc:a?Math.min(1,Math.max(0,c/a)):0, cov:Math.min(1,a/target)};""")

# ------------------------------------------- the deck counts itself
sub("""<b>Flashcards</b><span>88 AWS terms</span>""",
    """<b>Flashcards</b><span id="flashCount">AWS terms</span>""")
sub("""sizeCanvas(); refreshTop(); renderHome();""",
"""(()=>{ const fc=$('flashCount');                  // stated 88 for a deck that has been 90
  if(fc) fc.textContent=Object.keys(CODEX).length+' AWS terms'; })();
sizeCanvas(); refreshTop(); renderHome();""")

PAGE.write_text(s, encoding="utf-8")
print("misc fixes applied · page %.2f MB" % (len(s) / 1e6))
