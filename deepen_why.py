#!/usr/bin/env python3
"""Make the explanation substantial instead of a sentence per option.

"more than a few sentences — this isn't enough". Fair: each option carried one
line from the write-up and that was it, with the service definitions off in their
own block underneath where they were not attached to anything.

Everything needed for a fuller answer was already in the page and not being used
at the point of the question:

  * the per-option reasoning from the write-up (in, one line each)
  * the Hebrew glossary — what each named service actually IS (was in a separate
    block, now inline under the option that names it, so reading one option tells
    you what it proposes as well as why that fails)
  * the sector's **decision rules** from the course recap — how to tell questions
    of this shape apart in general. 1,800 characters per sector, used only as a
    fallback when nothing else matched, now always shown.
  * the exam cue and the verified-answer note, as before

So an option goes from one sentence to: what it proposes, why it stands or
falls, and what the services in it do — followed by the rule that separates this
family of questions, and a way into the full chapter.

The two old Hebrew blocks are gone: their content is what now sits under each
option, and leaving them would print every definition twice.

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


# ------------------------------------------- each option carries its own services
sub("""    bits.push('<div class="exlbl">Why each answer</div>');
    bits.push('<div class="exwhy exeach">'+q.o.map(([ltr,txt])=>{
      const right=q.a.includes(ltr);
      const line=e.why.byLetter[ltr]||'';
      return '<div class="exitem exopt '+(right?'good':'bad')+'">'+
        '<span class="k">'+ltr+(right?' \\u2713':' \\u2717')+'</span>'+
        '<span><b>'+esc(txt.length>86?txt.slice(0,86)+'\\u2026':txt)+'</b>'+
        (line?'<i>'+esc(line)+'</i>'
             :'<i class="dim">'+(right?'The answer this question is testing.'
                                      :'Wrong, but the write-up does not single this one out.')+'</i>')+
        '</span></div>';
    }).join('')+'</div>');
    if(e.why.rest) bits.push('<div class="exnote exrest">'+esc(e.why.rest)+'</div>');
  }""",
"""    bits.push('<div class="exlbl">Why each answer</div>');
    const seenTerm=new Set();
    bits.push('<div class="exwhy exeach">'+q.o.map(([ltr,txt])=>{
      const right=q.a.includes(ltr);
      const line=e.why.byLetter[ltr]||'';
      // What this option actually proposes, not just whether it is wrong. A definition is
      // printed against the first option that names it, so nothing repeats down the list.
      const terms=exFind(txt,3).filter(t=>{
        const k=t.t.toLowerCase();
        if(seenTerm.has(k)) return false;
        seenTerm.add(k); return true;
      });
      return '<div class="exitem exopt '+(right?'good':'bad')+'">'+
        '<span class="k">'+ltr+(right?' \\u2713':' \\u2717')+'</span>'+
        '<span><b>'+esc(txt)+'</b>'+
        (line?'<i>'+esc(line)+'</i>'
             :'<i class="dim">'+(right?'The answer this question is testing.'
                                      :'Wrong, but the write-up does not single this one out.')+'</i>')+
        (terms.length?'<u class="exsvc">'+terms.map(t=>
          '<span class="svcline"><b>'+esc(t.t)+'</b><span dir="rtl">'+esc(t.d)+'</span></span>'
        ).join('')+'</u>':'')+
        '</span></div>';
    }).join('')+'</div>');
    if(e.why.rest) bits.push('<div class="exnote exrest">'+esc(e.why.rest)+'</div>');
  }

  // How to tell questions of this shape apart in general — the sector's own decision rules.
  // These were only ever shown when nothing else matched; they are the most transferable thing
  // on the page and belong on every question.
  const rules=exFallback(e.sec);
  if(rules.length){
    bits.push('<div class="exlbl">How to decide questions like this</div>');
    bits.push('<div class="exwhy exrules">'+rules.map(r=>
      '<div class="exitem exopt"><span class="k">\\u2192</span><span><i>'+mdInline(r)+'</i></span></div>'
    ).join('')+'</div>');
  }""")

# ------------------------------- the old standalone glossary blocks are now inline
sub("""  if(e.correctTerms.length){
    bits.push('<div class="exlbl heb" dir="rtl">\u05dc\u05de\u05d4 \u05d6\u05d5 \u05d4\u05ea\u05e9\u05d5\u05d1\u05d4</div>');
    bits.push('<div class="exwhy">'+e.correctTerms.map(t=>
      '<div class="exitem"><span class="k">'+esc(t.t)+'</span><span>'+esc(t.d)+'</span></div>').join('')+'</div>');
  }
  const named=e.distractors.filter(d=>d.terms.length);
  if(named.length){
    bits.push('<div class="exlbl heb" dir="rtl">\u05dc\u05de\u05d4 \u05d4\u05d0\u05d7\u05e8\u05d5\u05ea \u05dc\u05d0</div>');
    bits.push('<div class="exwhy">'+named.map(d=>
      '<div class="exitem"><span class="k">'+d.ltr+(d.picked?' \u2190':'')+'</span><span><b>'+esc(d.terms[0].t)+'</b> \u2014 '+
      esc(d.terms[0].d)+'</span></div>').join('')+'</div>');
  }""",
"""  // The service definitions used to live in two blocks here. They now sit under the option
  // that names them, where they explain what that option is proposing — printing them again
  // would just be the same Hebrew twice. They are still shown this way when there is no
  // written explanation to hang them from.
  if(!e.full&&e.correctTerms.length){
    bits.push('<div class="exlbl heb" dir="rtl">\u05dc\u05de\u05d4 \u05d6\u05d5 \u05d4\u05ea\u05e9\u05d5\u05d1\u05d4</div>');
    bits.push('<div class="exwhy">'+e.correctTerms.map(t=>
      '<div class="exitem"><span class="k">'+esc(t.t)+'</span><span>'+esc(t.d)+'</span></div>').join('')+'</div>');
  }
  const named=e.full?[]:e.distractors.filter(d=>d.terms.length);
  if(named.length){
    bits.push('<div class="exlbl heb" dir="rtl">\u05dc\u05de\u05d4 \u05d4\u05d0\u05d7\u05e8\u05d5\u05ea \u05dc\u05d0</div>');
    bits.push('<div class="exwhy">'+named.map(d=>
      '<div class="exitem"><span class="k">'+d.ltr+(d.picked?' \u2190':'')+'</span><span><b>'+esc(d.terms[0].t)+'</b> \u2014 '+
      esc(d.terms[0].d)+'</span></div>').join('')+'</div>');
  }""")

# the fallback block is now redundant with the always-on rules
sub("""  if(!e.correctTerms.length&&!named.length&&!e.cue){
    const rules=exFallback(e.sec);
    if(rules.length){
      bits.push('<div class="exlbl">Decision rules for this sector</div>');
      bits.push('<div class="exwhy">'+rules.map(r=>'<div class="exitem ltr"><span>'+mdInline(r)+'</span></div>').join('')+'</div>');
    }
  }""",
"""""")

# ------------------------------------------------------------------ styling
sub(""".exeach .exopt{align-items:flex-start;gap:10px}""",
""".exeach .exopt{align-items:flex-start;gap:10px}
.exeach .exopt .exsvc{display:block;margin-top:7px;border-top:1px solid var(--line);padding-top:7px}
.exeach .exopt .svcline{display:block;margin-top:5px}
.exeach .exopt .svcline>b{display:inline-block;font-family:var(--mono);font-size:10px;
  letter-spacing:.4px;color:var(--cyan);margin:0 0 2px;text-transform:uppercase}
.exeach .exopt .svcline>span{display:block;direction:rtl;unicode-bidi:isolate;text-align:right;
  font-size:11.5px;line-height:1.55;color:var(--dim)}
.exrules .exopt{align-items:flex-start}
.exrules .exopt .k{color:var(--gold);border-color:var(--gold)}
.exrules .exopt i{font-size:12.5px;line-height:1.6}""")

PAGE.write_text(s, encoding="utf-8")
print("the explanation carries what each option proposes, why, and the rule \u00b7 %.2f MB" % (len(s)/1e6))
