#!/usr/bin/env python3
"""Render the full explanation, and mark every option with why it stands or falls.

Two pieces:

  * a **Why each answer** block carrying the whole written explanation, which is
    the thing that was asked for: it says why the right answer wins and what is
    wrong with each of the others.
  * the sentences in it are matched back to their option letters where they name
    one, so each wrong option in the list gets its own line rather than making
    the reader find it in a paragraph. Whatever cannot be attributed stays in the
    block, so nothing is dropped on the floor.

The existing Hebrew service glossary stays: that answers "what is DynamoDB",
which is a different question from "why is B wrong here".

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


# ---------------------------------------------------------------- the splitter
sub("""function buildExplain(q,picked,ok){""",
"""// The written explanation names options by letter. Pull each sentence apart so a line can sit
// against the option it is about, instead of leaving the reader to find it in a paragraph.
// Anything that names no letter stays in the block — nothing is dropped.
function whyByOption(text,letters){
  const out={}, rest=[];
  if(!text) return {byLetter:out,rest:''};
  // split on sentence ends, keeping short clauses joined to what they qualify
  const parts=String(text).split(/(?<=[.;])\\s+/).filter(Boolean);
  parts.forEach(p=>{
    // which letters does this sentence talk about? "A adds", "Option B's", "B and D require"
    const named=[];
    letters.forEach(L=>{
      const re=new RegExp('(^|[^A-Za-z])(?:option\\\\s+)?'+L+
        "(?=['\\u2019]s\\\\b|[ ,.;:)]|$)",'i');
      if(re.test(p)) named.push(L);
    });
    if(named.length&&named.length<=3) named.forEach(L=>{ (out[L]=out[L]||[]).push(p.trim()); });
    else rest.push(p.trim());
  });
  const byLetter={};
  Object.keys(out).forEach(L=>{ byLetter[L]=out[L].join(' '); });
  return {byLetter,rest:rest.join(' ')};
}
function buildExplain(q,picked,ok){""")

sub("""  return {ok, correct, wrongPicked, correctTerms, distractors, cue:exCue(q),
          note:q.x||'', sector:SHORT[q.s]||SECTIONS[q.s], sec:q.s};""",
"""  const why=whyByOption(q.w||'',q.o.map(x=>x[0]));
  return {ok, correct, wrongPicked, correctTerms, distractors, cue:exCue(q),
          note:q.x||'', why, full:q.w||'',
          sector:SHORT[q.s]||SECTIONS[q.s], sec:q.s};""")

# ------------------------------------------------------- render it in the panel
sub("""  // the note written while this question's answer was verified beats anything derived
  if(e.note) bits.push('<div class="exnote"><b>Why</b> '+esc(e.note)+'</div>');""",
"""  // the note written while this question's answer was verified beats anything derived
  if(e.note) bits.push('<div class="exnote"><b>Why</b> '+esc(e.note)+'</div>');

  // Every option, right and wrong, with what is actually wrong with it. This is the written
  // explanation for the question, split so each line sits against the option it is about.
  if(e.full){
    bits.push('<div class="exlbl">Why each answer</div>');
    bits.push('<div class="exwhy exeach">'+q.o.map(([ltr,txt])=>{
      const right=q.a.includes(ltr);
      const line=e.why.byLetter[ltr]||'';
      return '<div class="exitem exopt '+(right?'good':'bad')+'">'+
        '<span class="k">'+ltr+(right?' \\u2713':' \\u2717')+'</span>'+
        '<span><b>'+esc(txt.length>86?txt.slice(0,86)+'\\u2026':txt)+'</b>'+
        (line?'<i>'+esc(line)+'</i>'
             :'<i class="dim">'+(right?'The answer this question is testing.'
                                      :'Not what this question is asking for.')+'</i>')+
        '</span></div>';
    }).join('')+'</div>');
    if(e.why.rest) bits.push('<div class="exnote exrest">'+esc(e.why.rest)+'</div>');
  }""")

# ------------------------------------------------------------------ styling
sub(""".elsewhere{font-family:var(--mono);""",
""".exeach .exopt{align-items:flex-start;gap:10px}
.exeach .exopt .k{flex:none;font-family:var(--mono);font-size:11px;font-weight:700;
  padding:3px 7px;border-radius:6px;border:1px solid var(--line2);color:var(--dim)}
.exeach .exopt.good .k{color:var(--lime);border-color:var(--lime)}
.exeach .exopt.bad .k{color:var(--red);border-color:var(--red)}
.exeach .exopt b{display:block;font-weight:600;font-size:12.5px;line-height:1.45;
  color:var(--txt);margin-bottom:3px}
.exeach .exopt i{display:block;font-style:normal;font-size:12px;line-height:1.55;color:var(--dim)}
.exeach .exopt i.dim{opacity:.6}
.exeach .exopt.good b{color:var(--lime)}
.exrest{margin-top:8px}
.elsewhere{font-family:var(--mono);""")

sub("""    EXPLAIN, EX_TERMS, exFind, exCue, buildExplain, renderExplain, hideExplain, explainMode,""",
"""    EXPLAIN, EX_TERMS, exFind, exCue, buildExplain, renderExplain, hideExplain, explainMode,
    whyByOption,""")

PAGE.write_text(s, encoding="utf-8")
print("every option now carries its own reasoning \u00b7 page %.2f MB" % (len(s) / 1e6))
