#!/usr/bin/env python3
"""Finish the last exam, from the exam list too — and keep the door from eating the flag.

  - The paper's own row in the exam list gets a "Finish" button while it has questions left,
    which is where you would look for it.
  - normaliseProfile rebuilds simulation-log entries from typed fields, and dropped the new
    "finished later" flag on every load.
  - The snapshot stores question indices, so a bank change discards it along with seen/wrong.

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

sub("""    d:dstr(m.d), p:n0(m.p), pass:m.pass?1:0, mins:n0(m.mins), pr:m.pr?1:0,""",
    """    d:dstr(m.d), p:n0(m.p), pass:m.pass?1:0, mins:n0(m.mins), pr:m.pr?1:0, ct:m.ct?1:0,""")

sub("""  if(P.bank!==BANKV){
    P.bank=BANKV; P.seen={}; P.wrong=[]; P.marks=[]; P.sr={};
  }
  loaded=true;""",
"""  if(P.bank!==BANKV){
    P.bank=BANKV; P.seen={}; P.wrong=[]; P.marks=[]; P.sr={};
    delete P.lastPaper;        // it stores question indices too
  }
  loaded=true;""")

sub("""    const b=document.createElement('button');
    b.className='buy';
    b.textContent=savedHere?'Resume':(rec?'Retake':'Start');""",
"""    // the last paper, if it still has questions nobody got to, can be finished from its row
    const lp=P.lastPaper, lpOpen=(lp&&(lp.paper||0)===n&&!savedHere)?lastOpen(lp).length:0;
    if(lpOpen){
      const fin=document.createElement('button');
      fin.className='buy pstart';
      fin.textContent='\\u21a9 '+lpOpen;
      fin.title='Finish Exam '+n+' \\u2014 '+plural(lpOpen,'question')+' you did not reach';
      fin.setAttribute('aria-label',fin.title);
      fin.onclick=()=>simContinueAsk(fin);
      row.appendChild(fin);
    }
    const b=document.createElement('button');
    b.className='buy';
    b.textContent=savedHere?'Resume':(rec?'Retake':'Start');""")

PAGE.write_text(s, encoding="utf-8")
print("finish from the row; flag survives the door; bank change clears it")
