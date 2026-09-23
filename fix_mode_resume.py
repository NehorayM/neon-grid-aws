#!/usr/bin/env python3
"""A refresh during a practice pause must not pay the pause twice.

Pausing a practice paper for thirty minutes and refreshing brought it back with 128 minutes
on a 98-minute clock. The pause was being credited twice over: simAwayCost correctly charges
nothing for time inside an open pause, and then simResume carried brkFrom across the refresh,
so walking back into the paper ran brkEnd, which pushed both deadlines out by the same thirty
minutes a second time.

The saved `left` already has the pause excluded from it. So the resume is where the pause
ends: brkOpen and brkFrom are dropped rather than carried, and the clocks are restored to
exactly what was saved.

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


sub("""       brkUsed:sv.brkUsed||0, brkUntil:sv.brkUntil||0,
       brkOpen:sv.brkOpen?1:0, brkFrom:sv.brkFrom||0,""",
"""       brkUsed:sv.brkUsed||0, brkUntil:sv.brkUntil||0,
       // An open-ended pause ends here, and it ends free. `left` was written with the pause
       // already excluded, so carrying brkFrom across would have brkEnd credit the same time
       // a second time — thirty minutes away came back as thirty minutes gained.
       brkOpen:0, brkFrom:0,""")

PAGE.write_text(s, encoding="utf-8")
print("a pause is paid once · page %.2f MB" % (len(s) / 1e6))
