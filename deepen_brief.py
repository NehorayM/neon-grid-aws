#!/usr/bin/env python3
"""The briefing tells you what the services are. It should also tell you how to choose.

"Before you answer" listed the services in play with their definitions and a note
on the exam's phrasing. Useful, but it is all vocabulary — nothing about how to
pick between them, which is the actual skill the question is testing.

Two things added, both already in the page and both general rather than
answer-revealing, which matters for a panel shown BEFORE answering:

  * **How to choose here** — the sector's decision rules from the course recap.
    "Service-to-service or cross-account access → IAM role, not a user, not
    shared keys." These are the transferable part of the whole course and were
    only ever shown after the fact, as a fallback.
  * **What people get wrong here** — the traps recorded for the sector in
    #subjectdata, each already phrased as a mistake rather than an answer.

Neither names the correct option; they describe the family of questions. The
briefing stays collapsible, and the caps keep it shorter than the question.

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


# ---------------------------------------------- the briefing carries the rules
sub("""function buildBriefing(qi){
  const q=QS[qi];
  return { sector:SHORT[q.s]||SECTIONS[q.s], concepts:conceptsFor(q),
           distractors:distractorConcepts(q), tips:hintsFor(q), multi:q.a.length>1 };
}""",
"""// The traps recorded for a sector, phrased as mistakes rather than as answers — safe to show
// before the question is answered, because they describe the family, not this one.
function trapsFor(sec){
  try{
    const d=subjectData(sec);
    return ((d&&d.traps)||[]).map(t=>t.trap).filter(Boolean).slice(0,3);
  }catch(e){ return []; }
}
function buildBriefing(qi){
  const q=QS[qi];
  return { sector:SHORT[q.s]||SECTIONS[q.s], concepts:conceptsFor(q),
           distractors:distractorConcepts(q), tips:hintsFor(q), multi:q.a.length>1,
           // how to choose, not just what the words mean — the part the question tests
           rules:exFallback(q.s).slice(0,3), traps:trapsFor(q.s) };
}""")

sub("""  if(b.tips.length){ label('How the exam phrases it');
    b.tips.forEach(t=>{ const d=document.createElement('div'); d.className='tip';
      d.textContent='\U0001f4a1 '+t; body.appendChild(d); }); }
  if(b.multi){ const d=document.createElement('div'); d.className='tip warn';
    d.textContent='⚠ More than one answer is required here.'; body.appendChild(d); }""",
"""  // Definitions tell you what the services are; these tell you how to pick between them,
  // which is what the question is actually testing. Neither names the answer.
  if(b.rules.length){ label('How to choose in this area');
    b.rules.forEach(r=>{ const d=document.createElement('div'); d.className='brule';
      d.innerHTML='<span class="ba">→</span><span>'+mdInline(r)+'</span>';
      body.appendChild(d); }); }
  if(b.traps.length){ label('What people get wrong here');
    b.traps.forEach(tp=>{ const d=document.createElement('div'); d.className='brule trap';
      d.innerHTML='<span class="ba">✗</span><span>'+esc(tp)+'</span>';
      body.appendChild(d); }); }
  if(b.tips.length){ label('How the exam phrases it');
    b.tips.forEach(t=>{ const d=document.createElement('div'); d.className='tip';
      d.textContent='\U0001f4a1 '+t; body.appendChild(d); }); }
  if(b.multi){ const d=document.createElement('div'); d.className='tip warn';
    d.textContent='⚠ More than one answer is required here.'; body.appendChild(d); }""")

# the briefed drill panel gets the same
sub("""  if(b.tips.length){
    section('How the exam phrases it');""",
"""  if(b.rules.length){
    section('How to choose in this area');
    b.rules.forEach(r=>{ const d=document.createElement('div'); d.className='brule';
      d.innerHTML='<span class="ba">→</span><span>'+mdInline(r)+'</span>';
      box.appendChild(d); });
  }
  if(b.traps.length){
    section('What people get wrong here');
    b.traps.forEach(tp=>{ const d=document.createElement('div'); d.className='brule trap';
      d.innerHTML='<span class="ba">✗</span><span>'+esc(tp)+'</span>';
      box.appendChild(d); });
  }
  if(b.tips.length){
    section('How the exam phrases it');""")

# ------------------------------------------------------------------ styling
sub(""".exbrief .tip,.sheet .tip{direction:rtl;unicode-bidi:isolate;text-align:right}""",
""".exbrief .tip,.sheet .tip{direction:rtl;unicode-bidi:isolate;text-align:right}
/* The rules and traps are English; the briefing's Hebrew cards sit beside them, so these
   have to state their own direction rather than inherit the panel's. */
.brule{display:flex;gap:9px;align-items:flex-start;padding:9px 11px;margin-top:6px;
  border-radius:10px;background:var(--surface);border:1px solid var(--line);
  direction:ltr;unicode-bidi:isolate;text-align:left}
.brule>span:last-child{flex:1;min-width:0;font-size:12.5px;line-height:1.6;color:var(--txt)}
.brule .ba{flex:none;font-family:var(--mono);font-size:12px;font-weight:700;color:var(--gold)}
.brule.trap{background:color-mix(in srgb, var(--red) 6%, var(--surface));
  border-color:color-mix(in srgb, var(--red) 28%, var(--line))}
.brule.trap .ba{color:var(--red)}
.brule.trap>span:last-child{color:var(--dim)}""")

sub("""    simSpeak, ttsToggle, renderTtsBtn, renderExamBrief, BRIEF_PAPERS, buildBriefing,""",
"""    simSpeak, ttsToggle, renderTtsBtn, renderExamBrief, BRIEF_PAPERS, buildBriefing, trapsFor,""")

PAGE.write_text(s, encoding="utf-8")
print("the briefing now says how to choose · page %.2f MB" % (len(s) / 1e6))
