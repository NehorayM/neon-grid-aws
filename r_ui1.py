#!/usr/bin/env python3
"""Exam round 1 — the question comes first.

Measured on a 375px phone: the "Before you answer" panel was 1,081px tall, opened by default,
and sat ABOVE the question, so the first screen of every question was a timer box and a wall
of hints, and the question itself started more than a screen down. The paper-remaining box was
109px on its own.

  - The briefing now sits between the question and its options, and starts closed on every
    question — one line, "Before you answer", to tap when you want it. (It used to remember
    being open, so opening it once meant the wall on every question after.)
  - The paper box is one compact row: time left on the left, the live score on the right, a thin
    bar beneath. The long subtitle is dropped on the question screen; its facts are on the exam
    list and the review screen.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

brief = """      <details class="exbrief hidden" id="exBrief"><summary><span>📘</span>
        <span id="exBriefTitle">Before you answer</span><span class="chev">›</span></summary>
        <div class="bb" id="exBriefBody"></div></details>
"""
sub(brief, "")
sub("""      <div class="qcard">
        <div class="qtext" id="qText"></div>
        <div class="multi hidden" id="qMulti"></div>
      </div>
      <div class="opts" id="qOpts"></div>""",
"""      <div class="qcard">
        <div class="qtext" id="qText"></div>
        <div class="multi hidden" id="qMulti"></div>
      </div>
""" + brief + """      <div class="opts" id="qOpts"></div>""")

sub("""  box.open=P.briefOpen!==0;""",
    """  // Closed on every question: it is a thousand pixels when open, and remembering "open" put
  // that wall between you and every question after the first time you looked.
  box.open=false;""")

sub(""".simtotal.tight .stval{color:var(--gold)}""",
""".simtotal.tight .stval{color:var(--gold)}
/* one compact row: time left | live score, thin bar under both */
.simtotal{display:grid;grid-template-columns:1fr auto;column-gap:12px;align-items:center;padding:7px 11px}
.simtotal .stline{grid-column:1;grid-row:1}
.simtotal .stlive{grid-column:2;grid-row:1;margin:0;padding:0;border:0}
.simtotal .sttrack{grid-column:1 / -1;grid-row:2;margin:6px 0 0;height:4px}
.simtotal .stsub{display:none}
@media (max-width:480px){ .simtotal .stlivesub{display:none} .simtotal .stlbl{letter-spacing:.6px} }""")
PAGE.write_text(s, encoding="utf-8"); print("question first")
