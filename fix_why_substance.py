#!/usr/bin/env python3
"""Give the right answer enough to learn from, not just enough to be true.

"io2 supports up to 64,000 IOPS." is correct and useless on the next question. The panel
already holds the two things that make a fact transferable — the exam cue for this question
("when a question says X, think Y") and the sector's own decision rule — and it was printing
them in separate blocks further down rather than against the answer they explain.

So the supplement for the correct option now names the cue or the rule. That is the part
the reader carries into the next question.

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


sub("""function noLine(ltr,txt,right,pivot){
  const mine=exFind(txt,4).map(t=>t.t).filter(t=>t.toLowerCase()!==pivot.toLowerCase());
  if(right) return pivot? 'This is the answer: the question turns on '+pivot+'.'
                        : 'This is the answer this question is testing.';""",
"""function noLine(q,ltr,txt,right,pivot){
  const mine=exFind(txt,4).map(t=>t.t).filter(t=>t.toLowerCase()!==pivot.toLowerCase());
  if(right){
    // What makes the fact reusable: the cue that points here, or the sector's own rule.
    const cue=exCue(q), rule=(exFallback(q.s)||[])[0];
    const why=pivot? 'This is the answer: the question turns on '+pivot+'.'
                   : 'This is the answer this question is testing.';
    if(cue) return why+' When a question says '+cue.c+', '+cue.a+' is what is being tested.';
    if(rule) return why+' The rule for this area: '+String(rule).replace(/[*_`]/g,'')+'';
    return why;
  }""")

# every caller hands it the question now
sub("""  if(!line) return {text:noLine(ltr,txt,right,pivot),dim:true};
  if(line.length<THIN){
    const add=noLine(ltr,txt,right,pivot);""",
"""  if(!line) return {text:noLine(q,ltr,txt,right,pivot),dim:true};
  if(line.length<THIN){
    const add=noLine(q,ltr,txt,right,pivot);""")

PAGE.write_text(s, encoding="utf-8")
print("the answer carries the rule, not just the fact · page %.2f MB" % (len(s) / 1e6))
