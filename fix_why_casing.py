#!/usr/bin/env python3
"""Print service names the way the option writes them, and stop repeating the line.

The glossary is keyed in lower case — "aurora", "rds", "dynamodb", "auto scaling" — because
those keys are for lookup. They were being printed raw, so the panel said "It proposes rds"
under an option whose own text says "Amazon RDS for MySQL". The name is now taken from the
option text, matched case-insensitively, so it is shown the way it is written there.

And option C was being told "DynamoDB (C) is not MySQL-compatible. It proposes dynamodb,
where the question turns on aurora instead." — the supplement restating the sentence above
it. A supplement now only mentions services the line has not already named, and says
nothing at all when there is nothing left to add.

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


sub("""function noLine(q,ltr,txt,right,pivot,supp){
  const mine=exFind(txt,4).map(t=>t.t).filter(t=>t.toLowerCase()!==pivot.toLowerCase());""",
"""// The glossary keys are lower case for lookup ("rds", "auto scaling"). Show the name the
// way the option itself writes it — "Amazon RDS", "Auto Scaling" — not the key.
function asWritten(txt,key){
  const m=new RegExp('\\\\b'+String(key).replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&'),'i').exec(txt||'');
  return m?txt.substr(m.index,String(key).length):key;
}
function noLine(q,ltr,txt,right,pivot,supp,line){
  const mine=exFind(txt,4).map(t=>t.t)
    .filter(t=>t.toLowerCase()!==String(pivot).toLowerCase())
    // a supplement that names what the line already named just says it twice
    .filter(t=>!(supp&&line&&line.toLowerCase().indexOf(t.toLowerCase())>=0))
    .map(t=>asWritten(txt,t));""")

sub("""    if(cue) return why+' When a question says '+cue.c+', '+cue.a+' is what is being tested.';""",
    """    if(cue) return why+' When a question says '+cue.c+', '+cue.a+' is what is being tested.';""")

# pivot is shown too, and reads better as the correct option writes it
sub("""    const pivot=(e.correctTerms[0]||{}).t||'';""",
"""    const pivotKey=(e.correctTerms[0]||{}).t||'';
    const pivot=pivotKey?asWritten(e.correct.map(x=>x[1]).join(' '),pivotKey):'';""")

sub("""  if(!line) return {text:noLine(q,ltr,txt,right,pivot,false),dim:true};
  if(line.length<THIN||shared){
    const add=noLine(q,ltr,txt,right,pivot,true);""",
"""  if(!line) return {text:noLine(q,ltr,txt,right,pivot,false,''),dim:true};
  if(line.length<THIN||shared){
    const add=noLine(q,ltr,txt,right,pivot,true,line);""")

# the service lines under each option have the same lower-case problem
sub("""        (terms.length?'<u class="exsvc">'+terms.map(t=>
          '<span class="svcline"><b>'+esc(t.t)+'</b><span dir="rtl">'+esc(t.d)+'</span></span>'
        ).join('')+'</u>':'')+""",
"""        (terms.length?'<u class="exsvc">'+terms.map(t=>
          '<span class="svcline"><b>'+esc(asWritten(txt,t.t))+'</b><span dir="rtl">'+esc(t.d)+'</span></span>'
        ).join('')+'</u>':'')+""")

PAGE.write_text(s, encoding="utf-8")
print("names read as written · page %.2f MB" % (len(s) / 1e6))
