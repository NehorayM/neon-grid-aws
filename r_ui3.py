#!/usr/bin/env python3
"""Exam round 3 — the result screen leads with what you do next.

Round 3 first drove 2,600 random steps through every exam flow — start, answer, skip, time out,
leave, pause, resume, crash, two hours away, submit, finish later, redo, show answer, continue
from Running exams — checking after each step that clocks never go negative, picks stay legal,
a redo is never paused, the pause bar never shows without a pause, the result screen and the
history agree on the score, a redo's live score is its real score, and the review screen counts
what is really blank. Clean. The same walk against the build before the pause-bar fix finds both
of those bugs within 500 steps, so the clean result means something.

What it did find was the result screen: 1,827px on a phone, with the buttons for what to do
next at the very bottom under a copy of the whole exam history (1,038px, which now also lives in
the Redo tab), and a meta line that wrapped into a paragraph.

  - Next exam / Review this exam (opens the redo) / CSV / Home sit right under the score.
  - The meta line is "26 / 65 correct · 12 min · +26 🪙"; the weighted percentage moves to the
    breakdown heading, where it explains the scaled score.
  - History shows the last three, with a link to the Redo tab for the rest.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

sub("""      <button class="btn wide hidden" id="simCont" style="margin:14px auto 0;max-width:420px"></button>
      <div class="sechead">Domain breakdown</div>
      <div class="card" id="simDomList"></div>
      <div class="sechead">History</div>
      <div class="list" id="simLogList"></div>
      <div class="row" style="margin:16px 0 0">
        <button class="btn" id="simAgain">Run another</button>
        <button class="btn ghost sm" id="simCsv">⬇ CSV</button>
        <button class="btn ghost sm" id="simHome">Home</button>
      </div>""",
"""      <div class="row simacts">
        <button class="btn" id="simAgain">Run another</button>
        <button class="btn ghost" id="simRedoThis">✎ Review this exam</button>
      </div>
      <div class="row simacts2">
        <button class="btn ghost sm" id="simCsv">⬇ CSV</button>
        <button class="btn ghost sm" id="simHome">Home</button>
      </div>
      <button class="btn wide hidden" id="simCont" style="margin:14px auto 0;max-width:420px"></button>
      <div class="sechead" id="simDomHead">Domain breakdown</div>
      <div class="card" id="simDomList"></div>
      <div class="sechead">Recent</div>
      <div class="list" id="simLogList"></div>
      <button class="minichip" id="simAllRedo" style="margin:8px auto 0">All your exams are in the Redo tab ›</button>""")

sub(""".opt.locked{opacity:.62;cursor:default}""",
""".opt.locked{opacity:.62;cursor:default}
.simacts{margin:16px 0 0;gap:8px;justify-content:center;flex-wrap:wrap}
.simacts2{margin:8px 0 4px;gap:8px;justify-content:center}""")

sub("""  $('simMeta').textContent=correct+' / '+len+' correct ('+S.raw+'%) \\u00b7 '+
    pct+'% weighted by the exam\\u2019s domain mix \\u00b7 '+mins+' min · +'+coins+' 🪙'+
    (cont?' · finished later':'')+
    (csv.length?' · '+csv.length+' to export':'');""",
"""  $('simMeta').textContent=correct+' / '+len+' correct \\u00b7 '+mins+' min \\u00b7 +'+coins+' 🪙'+
    (cont?' \\u00b7 finished later':'');
  $('simDomHead').textContent='Domain breakdown \\u00b7 weighted '+pct+'%';
  { const hid=(P.lastPaper&&P.lastPaper.hid)||Object.keys(P.examHist||{}).sort((a,b)=>(P.examHist[b].at||0)-(P.examHist[a].at||0))[0];
    const rb=$('simRedoThis'); rb.dataset.hid=hid||''; rb.classList.toggle('hidden',!hid); }""")

# only the last three here
sub("""  const log=P.simLog||[];
  if(!log.length){ const d=document.createElement('div'); d.className='item';
    d.innerHTML='<div class="em">📝</div><div style="flex:1"><div class="ds">No full simulations yet.</div></div>';
    L.appendChild(d); return; }
  log.forEach(m=>{""",
"""  // the result screen shows the last three; the Redo tab has them all
  const log=(P.simLog||[]).slice(0,3);
  if(!log.length){ const d=document.createElement('div'); d.className='item';
    d.innerHTML='<div class="em">📝</div><div style="flex:1"><div class="ds">No full simulations yet.</div></div>';
    L.appendChild(d); return; }
  log.forEach(m=>{""")

sub("""$('simCsv').onclick=exportLastExam;""",
"""$('simCsv').onclick=exportLastExam;
$('simRedoThis').onclick=()=>{ const h=$('simRedoThis').dataset.hid; if(h) histOpen(h,$('simRedoThis')); };
$('simAllRedo').onclick=()=>{ renderRedoScreen(); go('redoScreen'); syncNav(); };""")
PAGE.write_text(s, encoding="utf-8"); print("result screen leads with actions")
