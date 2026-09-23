#!/usr/bin/env python3
"""Exam round 4 — the exam list gets to the exams.

On a 375px phone the list was 2,038px and the first exam row started 518px down, under a
sentence-long subtitle, a CSV chip, and a whole "Exam history" section that was only a link to
the Redo tab (which has its own button in the bar now). Every exam not yet started repeated
"65 questions · 105s each · 114 min" — nineteen times. And the stats strip said "Best 100%"
while every row beside it showed the same score on the 100–1000 scale.

  - Subtitle: "19 exams · 65 questions · 105 s a question" — the rest was on every row anyway.
  - The history link section is gone; the Redo tab is one tap away in the bar.
  - The CSV export moves below the list: it is an occasional extra, not the way in.
  - A row not yet started says "Not started"; the shared facts are said once, above.
  - "Best" is on the same scale as the rows.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

sub("""  $('paperSub').textContent=QS.length+' questions cut into '+plural(PAPER_COUNT,'paper')+' — '+
    PAPER_LEN+' questions each, '+SIM_QSEC+' seconds a question, nothing repeated inside a paper '+
    'and nothing shared between papers.';""",
"""  $('paperSub').textContent=PAPER_COUNT+' exams \\u00b7 '+PAPER_LEN+' questions \\u00b7 '+SIM_QSEC+' s a question';""")

sub("""    '<div class="stat"><b>'+(best?best+'%':'—')+'</b><span>Best</span></div>';""",
    """    '<div class="stat"><b>'+(best?saaScaled(best/100):'—')+'</b><span>Best / 1000</span></div>';""")

sub("""      : len+' questions \\u00b7 '+SIM_QSEC+'s each \\u00b7 '+simBudget(len)+' min';""",
    """      : (len<PAPER_LEN?plural(len,'question')+' \\u00b7 ':'')+'Not started';""")

# the history-link section: the Redo tab is in the bar
sub("""  renderRuns(); renderHist();""", """  renderRuns();""")

# the CSV chip moves under the list
sub("""    <div class="chiprow" style="justify-content:center;margin-bottom:14px">
      <button class="minichip" id="paperCsv">⬇ Export flagged &amp; missed (CSV)</button>
    </div>
""", "")
sub("""    <div class="list" id="paperList"></div>
  </div>""",
"""    <div class="list" id="paperList"></div>
    <div class="chiprow" style="justify-content:center;margin:14px 0 4px">
      <button class="minichip" id="paperCsv">⬇ Export flagged &amp; missed (CSV)</button>
    </div>
  </div>""")
PAGE.write_text(s, encoding="utf-8"); print("exam list gets to the exams")
