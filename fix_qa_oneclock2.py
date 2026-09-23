#!/usr/bin/env python3
"""The remaining checks that assumed the hidden clock, or were tripped by the new snapshot.

  - refreshChecks ticked 20 s and never saved, so the save still said 90 on that question. The
    old wall clock charged the paper anyway; with one clock, unsaved seconds are unsaved. The
    app writes every 10 s, so the setup now saves after ticking, as the app would have.
  - "a paper whose budget ran out while away is not offered back" is the behaviour this change
    removes on purpose: that paper was dropped, answers and all. It is kept, and scored.
  - The load door now carries the "finished later" flag, so a real log entry comes back with
    ct:0 on it.
  - The walk-through clicked the FIRST button on paper 1's row. With a finish-later snapshot
    left by an earlier check, that is the Finish button; Start is the last one. It also clears
    the snapshot first, so it walks a fresh paper whatever ran before.

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

sub("""  const setup=async()=>{ t.simClearSave(); t.startPaper(2); await sleep(30);
                         t.simQTick(20); await sleep(10); };""",
"""  // the app saves every ten seconds while a question runs; do what it would have done
  const setup=async()=>{ t.simClearSave(); t.startPaper(2); await sleep(30);
                         t.simQTick(20); t.simPersist(); await sleep(10); };""")

sub("""  // away long enough and the paper is simply over
  await setup();
  t.P.simSave.paused=0; t.P.simSave.at-=3*60*60*1000;
  ok(!t.simSaved(),'a paper whose budget ran out while away is not offered back');
  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave();""",
"""  // away long enough and the paper is over — but it is scored, not thrown away with its answers
  await setup();
  t.P.simSave.paused=0; t.P.simSave.at-=3*60*60*1000;
  ok(!!t.simSaved(),'a paper whose time ran out while away is still there');
  t.simResume(); await sleep(60);
  eq(t.route,'simDoneScreen','and resuming it scores it');
  t.simAbandon&&t.simAbandon(); await sleep(30); t.simClearSave(); delete t.P.lastPaper;""")

sub("""  const good={simLog:[{d:'2026-09-20',p:78,pass:1,mins:88,pr:1,dom:[80,70,90,60]}],""",
    """  const good={simLog:[{d:'2026-09-20',p:78,pass:1,mins:88,pr:1,ct:0,dom:[80,70,90,60]}],""")

sub("""  const btn=rows[n-1].querySelector('button');
  hittable(btn,'Start button on exam '+n);""",
"""  // Start is the row's LAST button: a restart arrow or a finish-later button can sit before it
  const btn=[...rows[n-1].querySelectorAll('button')].pop();
  hittable(btn,'Start button on exam '+n);""")

QA.write_text(s, encoding="utf-8")
print("remaining checks aligned")
