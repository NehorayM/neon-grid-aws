#!/usr/bin/env python3
"""Match the short distinctive names — io2, gp3 — and differentiate shared lines.

The guard that keeps the answer's evidence with the answer compared whole phrases, so
option D's key was "provisioned iops" and the sentence "io2 supports up to 64,000 IOPS"
did not match it. The keys now include each capitalised word on its own and the short
alphanumeric names AWS uses for volume and instance types (io2, gp3, t3, m5), which are the
most distinctive tokens in an option and were the ones being missed.

Separately, 759 options are shown a line identical to another option's, because a verdict
like "Provisioned RDS (B) and EC2 (D) mean paying for peak capacity" really is about both.
That is accurate but reads as filler twice over, so a shared line is now supplemented with
what THAT option proposes, the same way a too-short line is.

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


sub("""    const keyOf=t=>{
      const set=new Set();
      (String(t).match(/\\b(?:Amazon|AWS)\\s+[A-Z][A-Za-z0-9]*(?:\\s+[A-Z][A-Za-z0-9]*)?|\\b[A-Z][A-Za-z0-9]{3,}(?:\\s+[A-Z][A-Za-z0-9]+)?/g)||[])
        .forEach(x=>{ const k=x.replace(/^(?:Amazon|AWS)\\s+/,'').trim().toLowerCase();
                      if(k.length>3) set.add(k); });
      return set;
    };""",
"""    const keyOf=t=>{
      const set=new Set();
      const add=k=>{ k=String(k).replace(/^(?:Amazon|AWS)\\s+/,'').trim().toLowerCase();
                     if(k.length>3) set.add(k); };
      (String(t).match(/\\b(?:Amazon|AWS)\\s+[A-Z][A-Za-z0-9]*(?:\\s+[A-Z][A-Za-z0-9]*)?|\\b[A-Z][A-Za-z0-9]{3,}(?:\\s+[A-Z][A-Za-z0-9]+)?/g)||[])
        .forEach(x=>{ add(x); x.split(/\\s+/).forEach(add); });
      // io2, gp3, t3, m5 — the shortest names in an option and the most distinctive, and
      // the ones the phrase match was missing
      (String(t).match(/\\b[a-z]{1,3}[0-9][a-z0-9]*\\b/g)||[]).forEach(x=>set.add(x.toLowerCase()));
      return set;
    };""")

# a line true of two options is supplemented with what THIS option proposes
sub("""function optionLine(q,ltr,txt,line,pivot){
  const right=q.a.includes(ltr);
  if(!line) return {text:noLine(q,ltr,txt,right,pivot,false),dim:true};
  if(line.length<THIN){""",
"""function optionLine(q,ltr,txt,line,pivot,shared){
  const right=q.a.includes(ltr);
  if(!line) return {text:noLine(q,ltr,txt,right,pivot,false),dim:true};
  if(line.length<THIN||shared){""")

sub("""    bits.push('<div class="exwhy exeach">'+q.o.map(([ltr,txt])=>{
      const right=q.a.includes(ltr);
      const line=e.why.byLetter[ltr]||'';""",
"""    // a verdict that covers two options is printed against both; say what each one proposes
    // so the reader is not handed the same sentence twice with nothing to tell them apart
    const lineCount={};
    q.o.forEach(([l])=>{ const v=e.why.byLetter[l]||''; if(v) lineCount[v]=(lineCount[v]||0)+1; });
    bits.push('<div class="exwhy exeach">'+q.o.map(([ltr,txt])=>{
      const right=q.a.includes(ltr);
      const line=e.why.byLetter[ltr]||'';""")

sub("""        (function(){ const s=optionLine(q,ltr,txt,line,pivot);""",
    """        (function(){ const s=optionLine(q,ltr,txt,line,pivot,lineCount[line]>1);""")

PAGE.write_text(s, encoding="utf-8")
print("short names count, shared lines differ · page %.2f MB" % (len(s) / 1e6))
