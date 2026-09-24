#!/usr/bin/env python3
"""Redo, again: "I pressed Save in the redo, and the other device still isn't the same."

Tested signed in, with the account's copy read back after every step. Save worked — after
1.5 s. 0.6 s after "Save & close" the account still held the old answers: the upload waits
1.5 s so a burst of taps becomes one write, and the profile sync waits 4 s. On a phone, Save and
then locking the screen or switching apps suspends the page inside that window, and the save
never leaves the phone.

  1. Save & close uploads the exam straight away, and anything still waiting to go up is sent
     the moment the page is hidden or closed.
  2. An open redo takes the other device's answers by combining, not replacing. The copy on the
     PC was stamped "newest" by every Continue tapped before the last fix, so a phone running a
     redo could otherwise pull 18 answers over its own 37. Now each question keeps the incoming
     answer where there is one and its own where there is not, and whatever only this device had
     goes back up.
  3. Confirming "Put Exam N on hold and redo this one?" no longer waits for another sync first,
     which could outlast the confirm and re-ask.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

# ---- 2. combine into an open redo
sub("""function histRedoRefresh(){
  if(!sim||sim.mode!=='redo'||!sim.hid) return;
  const e=(P.examHist||{})[sim.hid]; if(!e) return;
  if(JSON.stringify(e.ans||{})===JSON.stringify(sim.ans||{})) return;
  sim.ans=JSON.parse(JSON.stringify(e.ans||{})); sim.flag=Object.assign({},e.flag||{});
  simPersist();
  if(route==='quizScreen'){ simLoad(); renderSimStrip(); renderSimLive(); }
}""","""// Combined, not replaced: a copy stamped newer is not always the one with more work in it (every
// Continue before the fix stamped a stale copy newest), and replacing let 18 answers wipe 37.
function histRedoRefresh(){
  if(!sim||sim.mode!=='redo'||!sim.hid) return;
  const e=(P.examHist||{})[sim.hid]; if(!e) return;
  const has=a=>Array.isArray(a)&&a.length>0;
  const inc=e.ans||{}, mine=sim.ans||{}, merged={};
  let extra=false;
  sim.qs.forEach((_,i)=>{
    if(has(inc[i])) merged[i]=inc[i].slice();
    else if(has(mine[i])){ merged[i]=mine[i].slice(); extra=true; }   // only this device has it
  });
  if(JSON.stringify(merged)===JSON.stringify(mine)&&!extra) return;
  sim.ans=merged; sim.flag=Object.assign({},sim.flag||{},e.flag||{});
  simPersist();
  if(extra) histWrite();                     // what only this device had goes back up
  if(route==='quizScreen'){ simLoad(); renderSimStrip(); renderSimLive(); }
}
// Uploads wait a moment so a burst of taps is one write. Save, and a page being put away, do not.
function histFlushNow(){
  if(histTimer){ clearTimeout(histTimer); histTimer=null; }
  if(histDirty.size) histCloudPush();
}
if(typeof document!=='undefined') document.addEventListener('visibilitychange',()=>{
  if(!document.hidden) return;
  histFlushNow();
  if(typeof syncTimer!=='undefined'&&syncTimer&&typeof syncNow==='function'){ clearTimeout(syncTimer); syncTimer=null; syncNow(true); }
});
if(typeof window!=='undefined') window.addEventListener('pagehide',()=>histFlushNow());""")

# ---- 1. Save uploads at once
sub("""function redoFinish(){
  if(!sim) return;
  histWrite();""","""function redoFinish(){
  if(!sim) return;
  histWrite();
  histFlushNow();                            // on a phone, Save then lock must not lose the save""")

# ---- 3. the confirming tap does not sync again
sub("""  if(sbUser&&histTable!=='missing'){
    if(btn){ btn.disabled=true; }""","""  if(sbUser&&histTable!=='missing'&&!(btn&&btn.dataset.armed)){   // the confirming tap already has it
    if(btn){ btn.disabled=true; }""")

sub("""    histAdopt, histRedoRefresh, histCloudPush,""","""    histAdopt, histRedoRefresh, histCloudPush, histFlushNow, get histTimer(){return histTimer;},""")
PAGE.write_text(s, encoding="utf-8"); print("redo save goes up at once; open redo combines")
