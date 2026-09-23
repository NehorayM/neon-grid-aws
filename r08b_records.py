#!/usr/bin/env python3
"""Round 8, second pass: the score records reached innerHTML raw too.

Widening the probe to every numeric field found one more: papers[n].best — the score chip on
each exam row — and the same pattern in the Learn subject list (courses[sec].best and .runs).
Both are numbers when the app writes them and anything at all when a file is imported.

Same two layers: the renderers force them to numbers, and normaliseProfile types every paper
record and every course record at the door.

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

sub("""      ((rec&&!here)?'<div class="pscore" style="color:'+col+'">'+rec.best+'%'+""",
    """      ((rec&&!here)?'<div class="pscore" style="color:'+col+'">'+(Number(rec.best)|0)+'%'+""")

sub("""      (rec?' · best '+rec.best+'%':'')+'</span></span>'+
      (rec?'<span class="cdone">✓ '+rec.runs+'</span>':'');""",
"""      (rec?' · best '+(Number(rec.best)|0)+'%':'')+'</span></span>'+
      (rec?'<span class="cdone">✓ '+(Number(rec.runs)|0)+'</span>':'');""")

sub("""  // Log entries are rebuilt from typed fields.""",
"""  // Score records: numbers when the app writes them, anything at all in an imported file.
  const n1=v=>{ const n=Number(v); return isFinite(n)?n:0; };
  const MODE=v=>v==='practice'?'practice':'exam';
  if(p.papers&&typeof p.papers==='object'&&!Array.isArray(p.papers)){
    Object.keys(p.papers).forEach(k=>{
      const r=p.papers[k];
      if(!r||typeof r!=='object'){ delete p.papers[k]; return; }
      r.best=Math.max(0,Math.min(100,n1(r.best))); r.tries=Math.max(0,n1(r.tries)|0);
      if(r.ptries!==undefined) r.ptries=Math.max(0,n1(r.ptries)|0);
      r.last=String(r.last==null?'':r.last).replace(/[^0-9%.]/g,'').slice(0,6);
      if(r.bestMode!==undefined) r.bestMode=MODE(r.bestMode);
      if(r.lastMode!==undefined) r.lastMode=MODE(r.lastMode);
    });
  }
  if(p.courses&&typeof p.courses==='object'&&!Array.isArray(p.courses)){
    Object.keys(p.courses).forEach(k=>{
      const r=p.courses[k];
      if(!r||typeof r!=='object'){ delete p.courses[k]; return; }
      if(r.best!==undefined) r.best=Math.max(0,Math.min(100,n1(r.best)));
      if(r.runs!==undefined) r.runs=Math.max(0,n1(r.runs)|0);
    });
  }
  // Log entries are rebuilt from typed fields.""")

PAGE.write_text(s, encoding="utf-8")
print("score records typed at the door and at render")
