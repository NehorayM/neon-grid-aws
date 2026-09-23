#!/usr/bin/env python3
"""Ask which kind of run this is, every time a paper starts.

Two breaks of exactly six minutes is the real exam's rule, and it is the right default when
the point is to find out whether you would pass. It is the wrong rule when the point is to
learn the material, because stopping to read something costs one of two breaks and then the
clock runs anyway.

So a paper now has a mode, chosen at the start:

  Simulation  two breaks, six minutes each, the paper waits and comes back on its own.
  Practice    stop as often as you like, for as long as you like; the paper waits.

The picker markup and its styling only. The behaviour is in the next script.

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


sub("""  <div id="brkBar" class="hidden">""",
"""  <div id="modeAsk" class="hidden">
    <div class="sheet">
      <h3 id="modeAskTitle">How do you want to sit this paper?</h3>
      <p class="sub" id="modeAskSub"></p>
      <button class="modepick" id="modeAskExam">
        <span class="mem">⏱</span>
        <span class="mbody">
          <b>Simulation</b>
          <i>Exam conditions. Two breaks, six minutes each, and the paper waits for
             them — after that, leaving is not offered and the clock keeps running.</i>
        </span>
      </button>
      <button class="modepick" id="modeAskPractice">
        <span class="mem">☕</span>
        <span class="mbody">
          <b>Practice</b>
          <i>Stop as often as you like, for as long as you like. The paper pauses when
             you leave and picks up where you left it.</i>
        </span>
      </button>
      <p class="sub modenote">Both are the same 65 questions on the same clock. Only
        the breaks differ, and a practice run is marked as one in your records.</p>
      <button class="btn ghost sm" id="modeAskNo" style="width:100%;margin-top:10px">Not now</button>
    </div>
  </div>
  <div id="brkBar" class="hidden">""")

sub("""#brkBar{position:fixed;""",
"""#modeAsk{position:absolute;inset:0;z-index:73;display:flex;flex-direction:column;
  justify-content:flex-end;background:rgba(6,9,13,.72)}
#modeAsk.hidden{display:none}
/* Each choice is one big target with its consequence written on it, rather than a pair of
   words that mean nothing until you have already picked wrong once. */
.modepick{display:flex;gap:12px;width:100%;text-align:left;margin-top:10px;padding:14px;
  border-radius:15px;background:var(--surface);border:1px solid var(--line);color:var(--txt);
  cursor:pointer;transition:border-color .15s,background .15s}
.modepick:hover,.modepick:focus-visible{border-color:color-mix(in srgb, var(--cyan) 55%, var(--line));
  background:color-mix(in srgb, var(--cyan) 8%, var(--surface))}
.modepick .mem{font-size:21px;flex:none;line-height:1.25}
.modepick .mbody{flex:1;min-width:0}
.modepick b{display:block;font-size:13.5px;font-weight:650;letter-spacing:.3px}
.modepick i{display:block;font-style:normal;font-size:11.5px;line-height:1.5;color:var(--dim);
  margin-top:3px}
.modenote{margin-top:12px;font-size:11px}
#brkBar{position:fixed;""")

PAGE.write_text(s, encoding="utf-8")
print("picker markup in · page %.2f MB" % (len(s) / 1e6))
