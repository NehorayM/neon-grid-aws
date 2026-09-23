#!/usr/bin/env python3
"""Type the rest of the profile at the door, so a corrupted import cannot leave garbage behind.

A second scan — fuzz, pass the door, then read every screen's TEXT for NaN, undefined or
leftover markup — found fields the door never typed. None became live markup (they are all
drawn as text), but they display as garbage for good and some feed arithmetic: a string in
login.streak made the home screen say "Come back tomorrow for +NaN coins — day <img ...>".

  login        last (a timestamp), streak (a count), claimed (0/1)
  counters     exams, examsPassed, reviewCleared, studyOpened join the numbers list
  badges       badge ids only; known: question indices only
  rHist        the readiness history: a date and a percentage each
  lastTimer    the timer's work/rest/rounds are numbers, its label is text without markup

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

sub("""                 'mocksPassed','bestMock','sims','simsPassed','bestSim','nextChest'];""",
    """                 'mocksPassed','bestMock','sims','simsPassed','bestSim','nextChest',
                 'exams','examsPassed','reviewCleared','studyOpened'];""")

sub("""  // Score records: numbers when the app writes them, anything at all in an imported file.""",
"""  // The login streak is drawn on the home screen and feeds the daily bonus; a string there read
  // "Come back tomorrow for +NaN coins — day <img ...>".
  if(p.login&&typeof p.login==='object'){
    const L=p.login;
    L.last=Math.max(0,Number(L.last)||0);
    L.streak=Math.max(0,Number(L.streak)|0);
    L.claimed=L.claimed?1:0;
  }
  if(Array.isArray(p.badges)) p.badges=[...new Set(p.badges.filter(x=>typeof x==='string'&&/^[a-z0-9_-]{1,40}$/i.test(x)))];
  if(Array.isArray(p.known)) p.known=[...new Set(p.known.map(Number).filter(n=>Number.isInteger(n)&&n>=0))];
  if(Array.isArray(p.rHist)) p.rHist=p.rHist.filter(r=>r&&typeof r==='object').slice(-400).map(r=>
    Object.assign({},r,{d:/^\\d{4}-\\d{1,2}-\\d{1,2}$/.test(String(r.d||''))?String(r.d):'',
                        p:Math.max(0,Math.min(100,Number(r.p)||0))}));
  if(p.lastTimer&&typeof p.lastTimer==='object'){
    const T0=p.lastTimer;
    ['work','rest','rounds'].forEach(k=>{ if(T0[k]!==undefined){ const n=Number(T0[k]); T0[k]=isFinite(n)&&n>0?n:0; } });
    ['mode','nm'].forEach(k=>{ if(T0[k]!==undefined) T0[k]=String(T0[k]).replace(/[<>]/g,'').slice(0,40); });
  }
  // Score records: numbers when the app writes them, anything at all in an imported file.""")

PAGE.write_text(s, encoding="utf-8")
print("rest of the profile typed")
