#!/usr/bin/env python3
"""Exam questions get 2:15 each (was 1:45).

Asked for: 2:15 for questions in the exam. SIM_QSEC is the one number every exam clock reads —
numbered papers, the random mock, the mistakes exam — and the paper budget is SIM_QSEC x
questions, so a 65-question paper is now 147 minutes. The two home tiles stated the timing as
fixed text ("105 seconds a question", "130 minutes" — already stale since the move to 105);
they are now written from the constants at start-up.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent
PAGE = ROOT / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)
sub("""const SIM_QSEC=105;   // per exam question (was 90)""",
    """const SIM_QSEC=135;   // per exam question: 2:15 (was 105, and 90 before that)""")
sub("""// Every question is capped at SIM_QSEC (105) seconds, so the budget for a whole paper is""",
    """// Every question is capped at SIM_QSEC (135) seconds, so the budget for a whole paper is""")
sub("""// 65 questions, 130 minutes, domain-weighted — the shape of the real SAA-C03.""",
    """// 65 questions, SIM_QSEC each, domain-weighted — the shape of the real SAA-C03.""")
sub("""   question by a repeating gradient, so "65 x 105 seconds" is visible rather than arithmetic. */""",
    """   question by a repeating gradient, so "65 x 135 seconds" is visible rather than arithmetic. */""")
sub("""<b>Random mock exam</b><span>65 drawn fresh to the real domain weights · 130 minutes</span>""",
    """<b>Random mock exam</b><span id="simOpenSub">65 drawn fresh to the real domain weights</span>""")
sub("""<b>Practice Exams</b><span>The whole bank as numbered papers · 65 questions · 105 seconds a question</span>""",
    """<b>Practice Exams</b><span id="paperOpenSub">The whole bank as numbered papers · 65 questions</span>""")
sub("""// ================= BOOT =================""","""// ================= BOOT =================
// the tiles say what the clock actually is, from the one constant it reads
(()=>{ const m=Math.floor(SIM_QSEC/60), sec=SIM_QSEC%60, per=m+':'+String(sec).padStart(2,'0');
  const a=$('simOpenSub'); if(a) a.textContent='65 drawn fresh to the real domain weights \\u00b7 '+SIM_MIN+' minutes';
  const b=$('paperOpenSub'); if(b) b.textContent='The whole bank as numbered papers \\u00b7 65 questions \\u00b7 '+per+' a question'; })();""")
PAGE.write_text(s, encoding="utf-8")
q = ROOT / "qa_bank.js"; t = q.read_text(encoding="utf-8")
for a,b in [("  eq(t.SIM_QSEC,105,'a question gets 105 seconds');","  eq(t.SIM_QSEC,135,'a question gets 2:15');"),
            ("""    ok(/90 questions/.test($('mistakeStart').textContent)&&/2 h 38 min/.test($('mistakeStart').textContent),
       'the start button says how many and how long (105 s a question)');""",
             """    ok(/90 questions/.test($('mistakeStart').textContent)&&$('mistakeStart').textContent.indexOf(t.fmtMins(t.simBudget(90)))>=0,
       'the start button says how many and how long ('+t.SIM_QSEC+' s a question)');"""),
            ("""    eq(t.sim.mins,158,'on a 158-minute clock');""","""    eq(t.sim.mins,t.simBudget(90),'on a clock of '+t.SIM_QSEC+' s a question');""")]:
    assert t.count(a)==1,(a[:60]); t=t.replace(a,b)
q.write_text(t, encoding="utf-8")
# (the two remaining tests that stated the old timing were updated by hand in qa_bank.js)
print("exam questions: 2:15 each")
