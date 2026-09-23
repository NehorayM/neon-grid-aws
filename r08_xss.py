#!/usr/bin/env python3
"""Round 8: an imported progress file could run code in the page.

Poisoned every free-text field of the profile with
    <img src=x onerror="...">
rendered every screen, and counted what came alive. Two did: the exam log and the full-
simulation log wrote their entries into innerHTML raw — the date, and every number beside
it (score, minutes, domain percentages, correct/total). None of that reaches another player
in a duel; the route is Import. Someone sends a "progress file", it is imported, and its
script runs in a page that holds the signed-in Supabase session.

Two layers:
  - both renderers escape everything they interpolate, and coerce the numbers to numbers
  - normaliseProfile, which every profile passes through on load, cloud merge and import,
    now rebuilds log entries from typed fields, so a string cannot sit where a number goes
    for the NEXT renderer someone writes either

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

sub("""    row.innerHTML='<div class="em">'+(m.pass?'🎓':'📝')+'</div><div style="flex:1">'+
      '<div class="nm">'+m.p+'% '+(m.pass?'— pass':'— below 72%')+'</div>'+
      '<div class="ds">'+m.d+' · '+m.mins+' min · '+DOMAINS.map((d,i)=>d.short+' '+m.dom[i]+'%').join(' · ')+'</div></div>';""",
"""    // Everything interpolated is escaped or forced to a number: an imported profile can put
    // anything in these fields, and this used to write them into innerHTML as they came.
    const num=v=>{ const n=Number(v); return isFinite(n)?Math.round(n):0; };
    const dom=Array.isArray(m.dom)?m.dom:[];
    row.innerHTML='<div class="em">'+(m.pass?'🎓':'📝')+'</div><div style="flex:1">'+
      '<div class="nm">'+num(m.p)+'% '+(m.pass?'— pass':'— below 72%')+(m.pr?' · practice':'')+'</div>'+
      '<div class="ds">'+esc(m.d)+' · '+num(m.mins)+' min · '+DOMAINS.map((d,i)=>esc(d.short)+' '+num(dom[i])+'%').join(' · ')+'</div></div>';""")

sub("""    row.innerHTML='<div class="em">'+(e.p?'🎖':'📋')+'</div><div style="flex:1">'+
      '<div class="nm">'+e.c+' / '+e.t+(e.p?' — passed':' — missed')+'</div>'+
      '<div class="ds">'+e.d+'</div></div>';""",
"""    const num=v=>{ const n=Number(v); return isFinite(n)?Math.round(n):0; };
    row.innerHTML='<div class="em">'+(e.p?'🎖':'📋')+'</div><div style="flex:1">'+
      '<div class="nm">'+num(e.c)+' / '+num(e.t)+(e.p?' — passed':' — missed')+'</div>'+
      '<div class="ds">'+esc(e.d)+'</div></div>';""")

# the entry door: every profile passes through here on load, merge and import
sub("""  if(typeof p.diff!=='string') p.diff='easy';
  // simSave starts life absent""",
"""  if(typeof p.diff!=='string') p.diff='easy';
  // Log entries are rebuilt from typed fields. A string where a number belongs is how the
  // two log screens ended up rendering an imported file's markup.
  const n0=v=>{ const n=Number(v); return isFinite(n)?n:0; };
  const dstr=v=>/^\\d{4}-\\d{1,2}-\\d{1,2}$/.test(String(v||''))?String(v):'';
  if(Array.isArray(p.simLog)) p.simLog=p.simLog.filter(m=>m&&typeof m==='object').slice(0,12).map(m=>({
    d:dstr(m.d), p:n0(m.p), pass:m.pass?1:0, mins:n0(m.mins), pr:m.pr?1:0,
    dom:(Array.isArray(m.dom)?m.dom:[]).slice(0,8).map(n0)}));
  if(Array.isArray(p.examLog)) p.examLog=p.examLog.filter(e=>e&&typeof e==='object').slice(0,200).map(e=>
    Object.assign({},e,{d:dstr(e.d)||String(e.d||'').replace(/[<>&"']/g,'').slice(0,40),
                        c:n0(e.c), t:n0(e.t), p:e.p?1:0}));
  // simSave starts life absent""")

PAGE.write_text(s, encoding="utf-8")
print("logs escaped at render and typed at the door")
