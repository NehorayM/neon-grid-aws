#!/usr/bin/env python3
"""Exam round 2 — the explanation says each thing once.

After answering, the panel was 1,744px on a phone, and every option's full text appeared three
times: in the options themselves, again under "You picked" / "Correct answer", and a third time
under "Why each answer". Most of the rest was the Hebrew service glossary and the sector's
decision rules, open, every time.

  - The heading names the answer: "Not quite — the answer is C".
  - "You picked" / "Correct answer" are gone when there is a written explanation; the options
    above are already marked right and wrong.
  - "Why each answer" keeps its reasoning per option, with a one-line reminder of the option
    instead of its whole text, and "your pick" on the one you chose.
  - The service definitions (Hebrew) and "How to decide questions like this" are one tap away,
    folded, rather than always open.

Nothing is removed that was not duplicated.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

sub("""  bits.push('<div class="exhead '+(ok?'ok':'no')+'">'+(timedOut?'\\u23f1 Time ran out \\u2014 the answer':ok?'✅ Correct':'❌ Not quite')+
            '<span class="tag" style="margin-left:auto">'+esc(e.sector)+'</span></div>');

  if(!ok&&e.wrongPicked.length){""",
"""  const ansL=e.correct.map(x=>x[0]).join(' + ');
  bits.push('<div class="exhead '+(ok?'ok':'no')+'">'+
            (timedOut?'\\u23f1 Time ran out \\u2014 the answer is '+ansL:ok?'\\u2705 Correct \\u2014 '+ansL:'\\u274c Not quite \\u2014 the answer is '+ansL)+
            '<span class="tag" style="margin-left:auto">'+esc(e.sector)+'</span></div>');

  // With a written explanation below, these two boxes only repeated the options already marked
  // right and wrong above; they stay for the few questions that have none.
  if(!e.full&&!ok&&e.wrongPicked.length){""")
sub("""  bits.push('<div class="exlbl">'+(ok?'Your answer':'Correct answer')+'</div>');
  e.correct.forEach(x=>bits.push('<div class="exrow good"><span class="exl">'+x[0]+'</span><span>'+esc(x[1])+'</span></div>'));""",
"""  if(!e.full){
    bits.push('<div class="exlbl">'+(ok?'Your answer':'Correct answer')+'</div>');
    e.correct.forEach(x=>bits.push('<div class="exrow good"><span class="exl">'+x[0]+'</span><span>'+esc(x[1])+'</span></div>'));
  }""")

# each option: a reminder line instead of its whole text; definitions collected, folded
sub("""    const lineCount={};
    q.o.forEach(([l])=>{ const v=e.why.byLetter[l]||''; if(v) lineCount[v]=(lineCount[v]||0)+1; });""",
"""    const lineCount={};
    q.o.forEach(([l])=>{ const v=e.why.byLetter[l]||''; if(v) lineCount[v]=(lineCount[v]||0)+1; });
    const defs=[];                 // the Hebrew definitions, gathered into one folded block
    const brief=txt=>{ const w=String(txt).split(/\\s+/); return w.length>9?w.slice(0,9).join(' ')+'\\u2026':txt; };""")
sub("""      return '<div class="exitem exopt '+(right?'good':'bad')+'">'+
        '<span class="k">'+ltr+(right?' \\u2713':' \\u2717')+'</span>'+
        '<span><b>'+esc(txt)+'</b>'+
        (function(){ const s=optionLine(q,ltr,txt,line,pivot,lineCount[line]>1);
          return '<i'+(s.dim?' class="dim"':'')+'>'+esc(s.text)+'</i>'; })()+
        (terms.length?'<u class="exsvc">'+terms.map(t=>
          '<span class="svcline"><b>'+esc(asWritten(txt,t.t))+'</b><span dir="rtl">'+esc(t.d)+'</span></span>'
        ).join('')+'</u>':'')+
        '</span></div>';
    }).join('')+'</div>');""",
"""      terms.forEach(t=>defs.push('<span class="svcline"><b>'+esc(asWritten(txt,t.t))+'</b><span dir="rtl">'+esc(t.d)+'</span></span>'));
      const mine=picked&&picked.has&&picked.has(ltr);
      return '<div class="exitem exopt '+(right?'good':'bad')+(mine?' mine':'')+'">'+
        '<span class="k">'+ltr+(right?' \\u2713':' \\u2717')+'</span>'+
        '<span><b class="exbrief1" title="'+esc(txt)+'">'+esc(brief(txt))+'</b>'+
        (mine?'<em class="expick">your pick</em>':'')+
        (function(){ const s=optionLine(q,ltr,txt,line,pivot,lineCount[line]>1);
          return '<i'+(s.dim?' class="dim"':'')+'>'+esc(s.text)+'</i>'; })()+
        '</span></div>';
    }).join('')+'</div>');
    if(defs.length) bits.push('<details class="exmore"><summary>\\u{1f4da} The services in this question</summary>'+
      '<u class="exsvc">'+defs.join('')+'</u></details>');""")

sub("""  if(rules.length){
    bits.push('<div class="exlbl">How to decide questions like this</div>');
    bits.push('<div class="exwhy exrules">'+rules.map(r=>
      '<div class="exitem exopt"><span class="k">\\u2192</span><span><i>'+mdInline(r)+'</i></span></div>'
    ).join('')+'</div>');
  }""",
"""  if(rules.length){
    bits.push('<details class="exmore"><summary>\\u{1f9ed} How to decide questions like this</summary>'+
      '<div class="exwhy exrules">'+rules.map(r=>
      '<div class="exitem exopt"><span class="k">\\u2192</span><span><i>'+mdInline(r)+'</i></span></div>'
    ).join('')+'</div></details>');
  }""")

sub(""".opt.locked{opacity:.62;cursor:default}""",
""".opt.locked{opacity:.62;cursor:default}
/* the explanation, said once */
.exbrief1{display:block;font-weight:600;opacity:.75;font-size:.92em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.expick{display:inline-block;font-style:normal;font-size:10px;font-family:var(--mono);letter-spacing:.5px;
  text-transform:uppercase;color:var(--gold);border:1px solid color-mix(in srgb, var(--gold) 45%, transparent);
  border-radius:6px;padding:0 5px;margin:3px 0 1px}
.exopt.mine{box-shadow:inset 3px 0 0 var(--gold)}
.exmore{margin-top:10px;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
.exmore>summary{cursor:pointer;list-style:none;padding:10px 12px;font-size:12.5px;font-weight:600;color:var(--dim)}
.exmore>summary::-webkit-details-marker{display:none}
.exmore>summary::after{content:' \\203a';opacity:.6}
.exmore[open]>summary::after{content:' \\2039'}
.exmore>.exwhy,.exmore>.exsvc{display:block;padding:0 12px 10px}""")
PAGE.write_text(s, encoding="utf-8"); print("said once")
