#!/usr/bin/env python3
"""Redo: the PC showed Exam 8 at 342 while the phone, mid-redo, was at 431 on question 37.

An exam in the Redo list is one row per exam, and the newer copy (`at`) wins. Three ways the
older copy won instead:

  1. Opening a redo stamped `at` — it counts the open — before looking at the account. A
     device holding an old copy (the PC) became the "newest" the moment Continue was tapped,
     started the redo from its old answers, and pushed them over the phone's.
  2. The upload was a blind upsert: whatever this device had replaced the account's row,
     newer or not.
  3. A redo already open never took in newer answers from the other device.

Now: opening pulls the account's copy first and does not touch `at` (the open count merges as
the larger of the two); an upload first reads the account's copies and never replaces a newer
one; an edit is always stamped later than the copy it edited, whatever the two clocks say; and a
pulled copy that is newer than the redo on screen is loaded into it.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

# ---- 2. never replace a newer copy on the account
sub("""  const rows=[...histDirty].map(h=>(P.examHist||{})[h]).filter(e=>e&&e.hid)
    .map(e=>({user_id:sbUser.id, hid:String(e.hid), exam:e}));
  histDirty.clear();
  if(!rows.length) return;
  try{""","""  const want=[...histDirty];
  histDirty.clear();
  // The upload used to replace the account's row with whatever this device held. A device with
  // an old copy of an exam then wrote it over the other device's newer answers. Read first.
  let cloud={};
  try{
    const r=await sb.from('exam_history').select('hid,exam').in('hid',want.map(String));
    if(r.error){ if(histMissing(r.error)){ histTable='missing'; return; } want.forEach(h=>histDirty.add(h)); return; }
    (r.data||[]).forEach(row=>{ if(row.exam) cloud[row.hid]=row.exam; });
  }catch(e){ want.forEach(h=>histDirty.add(h)); return; }
  let adopted=false;
  const rows=[];
  want.forEach(h=>{
    const e=(P.examHist||{})[h], c=cloud[h];
    if(!e||!e.hid) return;
    if(c&&(Number(c.at)||0)>(Number(e.at)||0)){          // theirs is newer: take it, send nothing
      P.examHist[h]=histAdopt(e,c); adopted=true; return;
    }
    const redos=Math.max(Number(e.redos)||0,Number(c&&c.redos)||0);
    if(redos!==(Number(e.redos)||0)) e.redos=redos;
    rows.push({user_id:sbUser.id, hid:String(e.hid), exam:e});
  });
  if(adopted){ saveProfile(); histRedoRefresh(); }
  if(!rows.length){ histTable='ok'; histLastSync=Date.now(); if(route==='redoScreen') renderRedoScreen(); return; }
  try{""")

# ---- 3. a pulled copy newer than ours is adopted, including into an open redo
sub("""    const mine=P.examHist[row.hid];
    if(!mine||(Number(e.at)||0)>(Number(mine.at)||0)){ P.examHist[row.hid]=e; changed=true; }
  });""","""    const mine=P.examHist[row.hid];
    if(!mine||(Number(e.at)||0)>(Number(mine.at)||0)){ P.examHist[row.hid]=histAdopt(mine,e); changed=true; }
    else if(mine&&(Number(e.redos)||0)>(Number(mine.redos)||0)) mine.redos=Number(e.redos);
  });""")
sub("""  if(changed){ normaliseProfile(P); histPrune(); saveProfile(); }
  histLastSync=Date.now();""","""  if(changed){ normaliseProfile(P); histPrune(); saveProfile(); histRedoRefresh(); }
  histLastSync=Date.now();""")

# helpers, next to the history code
sub("""// ---------- exam history ----------
const HIST_KEEP=30;""","""// a newer copy from elsewhere, keeping the larger open count of the two
function histAdopt(mine,theirs){
  const e=Object.assign({},theirs);
  e.redos=Math.max(Number(mine&&mine.redos)||0,Number(theirs.redos)||0);
  return e;
}
// The redo on screen was built from the copy this device had when it opened. When a newer copy
// arrives, take its answers: they are the other device's later work on the same exam.
function histRedoRefresh(){
  if(!sim||sim.mode!=='redo'||!sim.hid) return;
  const e=(P.examHist||{})[sim.hid]; if(!e) return;
  if(JSON.stringify(e.ans||{})===JSON.stringify(sim.ans||{})) return;
  sim.ans=JSON.parse(JSON.stringify(e.ans||{})); sim.flag=Object.assign({},e.flag||{});
  simPersist();
  if(route==='quizScreen'){ simLoad(); renderSimStrip(); renderSimLive(); }
}
// ---------- exam history ----------
const HIST_KEEP=30;""")

# ---- an edit is always later than the copy it edited, whatever the clocks say
sub("""    d:prev.d||dayKey(), d0:prev.d0||Date.now(), at:Date.now(),
    redos:prev.redos||0}, sc);""","""    d:prev.d||dayKey(), d0:prev.d0||Date.now(),
    // two devices' clocks disagree; an edit must still beat the copy it was made on
    at:Math.max(Date.now(),(Number(prev.at)||0)+1),
    redos:prev.redos||0}, sc);""")

# ---- 1. opening: fetch the account's copy first, and do not claim to be newer for opening
sub("""function histOpen(hid,btn){
  const r=(P.examHist||{})[hid]; if(!r) return;
  if(r.qs.some(i=>!QS[i])){ toast('That exam used questions this build no longer has'); return; }
  const go2=()=>{""","""async function histOpen(hid,btn){
  if(!(P.examHist||{})[hid]) return;
  // The other device may have gone further with this exam. Start from the account's copy, not
  // the one this device happened to keep — a short wait, and on without it if offline.
  if(sbUser&&histTable!=='missing'){
    if(btn){ btn.disabled=true; }
    try{ await Promise.race([histCloudPull(),new Promise(r=>setTimeout(r,3500))]); }catch(e){}
    if(btn){ btn.disabled=false; }
  }
  const r=(P.examHist||{})[hid]; if(!r) return;
  if(r.qs.some(i=>!QS[i])){ toast('That exam used questions this build no longer has'); return; }
  const go2=()=>{""")
sub("""    r.redos=(Number(r.redos)||0)+1; r.at=Date.now(); histCloudQueue(hid);""",
"""    // Counted, but not stamped newer: stamping made a stale copy win just by being opened.
    r.redos=(Number(r.redos)||0)+1; histCloudQueue(hid);""")

# ---- the profile merge keeps the larger open count too
sub("""    out.examHist[k]=(!x||!y)?(x||y):((Number(y.at)||0)>=(Number(x.at)||0)?y:x);""",
"""    out.examHist[k]=(!x||!y)?(x||y):((Number(y.at)||0)>=(Number(x.at)||0)?histAdopt(x,y):histAdopt(y,x));""")

# test surface
sub("""    duelFind, duelRefresh,""","""    histAdopt, histRedoRefresh, histCloudPush, get histDirty(){return histDirty;},
    duelFind, duelRefresh,""")

PAGE.write_text(s, encoding="utf-8"); print("redo sync: pull before open, no blind overwrite, adopt into open redo")
