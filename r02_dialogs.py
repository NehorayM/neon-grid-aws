#!/usr/bin/env python3
"""Round 2: the sheets were dialogs to the eye and nothing to a keyboard.

Opening the mode picker, the break sheet or the study card left focus on the page behind
it, so Tab walked through controls the sheet was covering. Escape closed none of them. And
none carried dialog semantics, so a screen reader announced nothing when one appeared.

One mechanism for all three, rather than three sets of hooks in three open functions:
a MutationObserver watches each sheet's `hidden` class. When a sheet appears, focus moves to
its first button and the element that had focus is remembered; when it goes, focus goes
back. A single keydown handler closes the open sheet on Escape (through that sheet's own
close function, so its side effects still run) and keeps Tab inside it.

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

# dialog semantics, labelled by each sheet's own heading
sub("""  <div id="modeAsk" class="hidden">
    <div class="sheet">
      <h3 id="modeAskTitle">""",
"""  <div id="modeAsk" class="hidden" role="dialog" aria-modal="true" aria-labelledby="modeAskTitle">
    <div class="sheet">
      <h3 id="modeAskTitle">""")
sub("""  <div id="brkAsk" class="hidden">
    <div class="sheet">
      <h3>""",
"""  <div id="brkAsk" class="hidden" role="dialog" aria-modal="true" aria-labelledby="brkAskTitle">
    <div class="sheet">
      <h3 id="brkAskTitle">""")
sub("""  <div id="studyModal" class="hidden">
    <div class="sheet">
      <h3>""",
"""  <div id="studyModal" class="hidden" role="dialog" aria-modal="true" aria-labelledby="studyTitle">
    <div class="sheet">
      <h3 id="studyTitle">""")

sub("""$('studyClose').onclick=closeStudy;""",
"""$('studyClose').onclick=closeStudy;
// ---------- the sheets behave as dialogs ----------
// Each sheet was a dialog to the eye only: focus stayed on the page it covered, so Tab walked
// through hidden controls, and Escape did nothing. One observer handles focus for all of
// them; one keydown handler handles Escape and keeps Tab inside the open sheet.
const SHEETS=[
  {id:'modeAsk',    close:()=>modeAskClose()},
  {id:'brkAsk',     close:()=>brkAskClose()},
  {id:'studyModal', close:()=>closeStudy()},
];
const sheetReturn={};
const openSheet=()=>SHEETS.find(x=>{ const e=$(x.id); return e&&!e.classList.contains('hidden'); });
const focusables=el=>[...el.querySelectorAll('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])')]
  .filter(x=>!x.disabled&&x.offsetParent!==null);
SHEETS.forEach(sh=>{
  const el=$(sh.id); if(!el||typeof MutationObserver==='undefined') return;
  let wasOpen=!el.classList.contains('hidden');
  new MutationObserver(()=>{
    const open=!el.classList.contains('hidden');
    if(open===wasOpen) return;
    wasOpen=open;
    if(open){
      sheetReturn[sh.id]=document.activeElement;
      const f=focusables(el)[0]; if(f) f.focus({preventScroll:true});
    } else {
      const back=sheetReturn[sh.id]; sheetReturn[sh.id]=null;
      if(back&&document.contains(back)&&typeof back.focus==='function') back.focus({preventScroll:true});
    }
  }).observe(el,{attributes:true,attributeFilter:['class']});
});
document.addEventListener('keydown',e=>{
  const sh=openSheet(); if(!sh) return;
  if(e.key==='Escape'){ e.preventDefault(); sh.close(); return; }
  if(e.key!=='Tab') return;
  const list=focusables($(sh.id)); if(!list.length) return;
  const first=list[0], last=list[list.length-1];
  if(!$(sh.id).contains(document.activeElement)){ e.preventDefault(); first.focus(); return; }
  if(e.shiftKey&&document.activeElement===first){ e.preventDefault(); last.focus(); }
  else if(!e.shiftKey&&document.activeElement===last){ e.preventDefault(); first.focus(); }
});""")

PAGE.write_text(s, encoding="utf-8")
print("sheets are dialogs: focus in, focus back, Escape, Tab kept inside")
