#!/usr/bin/env python3
"""Two row checks now have to answer the picker, because starting a paper asks.

paperRowChecks drove the Start and restart buttons and then read t.sim straight away. Those
buttons no longer start anything on their own — they raise the mode sheet and wait — so the
reads hit null. The checks now answer the sheet, which also pins down that both paths
actually reach it rather than starting a paper behind it.

Run once; qa_bank.js is the source of truth afterwards.
"""
import pathlib

QA = pathlib.Path(__file__).resolve().parent / "qa_bank.js"
s = QA.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


sub("""  other.click(); await sleep(20); other.click(); await sleep(40);
  eq(t.sim.paper,6,'the second tap starts the other paper');""",
"""  other.click(); await sleep(20); other.click(); await sleep(40);
  ok(!$('modeAsk').classList.contains('hidden'),
     'confirming the discard asks which kind of run the new one is');
  $('modeAskExam').click(); await sleep(40);
  eq(t.sim.paper,6,'and answering it starts the other paper');
  eq(t.sim.mode,'exam','in the mode that was picked');""")

sub("""  again.click(); await sleep(40);
  eq(t.sim.i,0,'the second tap starts it from question one');""",
"""  again.click(); await sleep(40);
  ok(!$('modeAsk').classList.contains('hidden'),'restarting asks the same question');
  $('modeAskPractice').click(); await sleep(40);
  eq(t.sim.i,0,'and then starts it from question one');
  eq(t.sim.mode,'practice','in the mode that was picked');""")

QA.write_text(s, encoding="utf-8")
print("row checks answer the picker")
