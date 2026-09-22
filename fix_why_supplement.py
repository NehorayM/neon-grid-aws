#!/usr/bin/env python3
"""Make one function decide what an option is told, so the audit can measure what is READ.

Two things were still true after the attribution work: 428 correct answers got a line under
a sentence long ("io2 supports up to 64,000 IOPS."), and 477 options got no line at all.
The second was already being filled at render time by noLine(), but the audit was reading
the raw attribution and so was measuring something the reader never sees.

Both are fixed the same way: optionLine() now decides what every option is told — the
attributed line, supplemented with the contrast when the line is too short to learn from,
or the contrast alone when there is no line. The renderer calls it, and so does the audit,
so the numbers are about the panel rather than about an intermediate.

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


sub("""function renderExplain(q,picked,ok){""",
"""// What an option is actually told, in one place so the panel and the audit agree.
// A line under a sentence long is a true statement the reader cannot generalise from, so it
// is supplemented rather than replaced: "io2 supports up to 64,000 IOPS" keeps its fact and
// gains the comparison that makes the fact matter.
const THIN=60;
function optionLine(q,ltr,txt,line,pivot){
  const right=q.a.includes(ltr);
  if(!line) return {text:noLine(ltr,txt,right,pivot),dim:true};
  if(line.length<THIN){
    const add=noLine(ltr,txt,right,pivot);
    if(add) return {text:line+' '+add,dim:false};
  }
  return {text:line,dim:false};
}
function renderExplain(q,picked,ok){""")

sub("""        (line?'<i>'+esc(line)+'</i>'
             :'<i class="dim">'+esc(noLine(ltr,txt,right,pivot))+'</i>')+""",
"""        (function(){ const s=optionLine(q,ltr,txt,line,pivot);
          return '<i'+(s.dim?' class="dim"':'')+'>'+esc(s.text)+'</i>'; })()+""")

# expose it so the audit measures the panel, not an intermediate
sub("    whyByOption,", "    whyByOption, optionLine, noLine,")

PAGE.write_text(s, encoding="utf-8")
print("one function decides what an option is told · page %.2f MB" % (len(s) / 1e6))
