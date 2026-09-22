#!/usr/bin/env python3
"""Part two: pull on focus, hand the exam over, and stop the loser's clock.

See device_sync.py for the diagnosis. This is the behaviour half.

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


# ------------------------------------------- 1. losing the exam to another device
sub("""function simAnsweredIn(sv){ return Object.keys(sv.ans||{}).filter(k=>(sv.ans[k]||[]).length).length; }""",
"""function simAnsweredIn(sv){ return Object.keys(sv.ans||{}).filter(k=>(sv.ans[k]||[]).length).length; }

// ---------- one device owns the exam ----------
// The merge has already handed simSave to whichever device wrote it last. So if we are
// mid-exam and the save is no longer ours, the other device picked it up: stop here rather
// than running a second copy of the same paper against a clock nobody agrees on.
function simOwns(sv){ return !sv||!sv.dev||sv.dev===DEVICE_ID; }
function simOwnerCheck(){
  if(!sim||!sim.running) return false;
  const sv=P.simSave;
  if(simOwns(sv)) return false;
  simQStop(); ttsStop(); hideExplain();
  sim=null; renderClock(); syncNav();
  toast('⏸ This exam was picked up on '+otherDevice(sv));
  if(route==='quizScreen'||route==='simRevScreen'){ renderPapers(); go('paperScreen'); }
  return true;
}
// Claiming it: stamp this device on the save and get it to the cloud now rather than
// after the four-second debounce, so the other device finds out on its next look.
function simClaim(){
  if(!sim) return;
  simPersist();
  if(typeof pushCloud==='function'&&typeof sb!=='undefined'&&sb&&sbUser) pushCloud();
}""")

# ------------------------------------- 2. resuming something open somewhere else
sub("""  const sv=simSaved(), rbtn=$('exResume');
  if(sv&&rbtn){
    rbtn.classList.remove('hidden');
    rbtn.innerHTML='<span class="rem">⏸</span><span style="flex:1;min-width:0">'+
      '<div class="rnm">Resume '+(sv.paper?'Exam '+sv.paper:'the mock exam')+'</div>'+
      '<div class="rds">Question '+((sv.i||0)+1)+' of '+sv.qs.length+' · '+
      simAnsweredIn(sv)+' answered · '+fmtClock(sv.left)+' left</div></span>'+
      '<span class="buy">Resume</span>';
    rbtn.onclick=simResume;
  } else if(rbtn) rbtn.classList.add('hidden');""",
"""  const sv=simSaved(), rbtn=$('exResume');
  if(sv&&rbtn){
    const mine=simOwns(sv);
    rbtn.classList.remove('hidden');
    rbtn.dataset.armed='';
    rbtn.innerHTML='<span class="rem">⏸</span><span style="flex:1;min-width:0">'+
      '<div class="rnm">Resume '+(sv.paper?'Exam '+sv.paper:'the mock exam')+
        (mine?'':' <span class="elsewhere">on '+esc(otherDevice(sv))+'</span>')+'</div>'+
      '<div class="rds">Question '+((sv.i||0)+1)+' of '+sv.qs.length+' · '+
      simAnsweredIn(sv)+' answered · '+fmtClock(sv.left)+' left</div></span>'+
      '<span class="buy">'+(mine?'Resume':'Take over')+'</span>';
    rbtn.onclick=()=>simResumeHere(sv);
  } else if(rbtn) rbtn.classList.add('hidden');""")

sub("""function recordPaper(n,pct){""",
"""// Taking an exam off another device is not something to do by accident, so it arms first —
// the same two-tap the Submit button uses when there are blanks left.
function armed(btn,label,then){
  if(btn.dataset.armed){ btn.dataset.armed=''; then(); return; }
  const was=btn.innerHTML;
  btn.dataset.armed='1'; btn.innerHTML='<span class="buy wide">'+esc(label)+'</span>';
  setTimeout(()=>{ if(btn.dataset.armed){ btn.dataset.armed=''; btn.innerHTML=was; } },4000);
}
function simResumeHere(sv){
  const rbtn=$('exResume');
  if(simOwns(sv)){ simResume(); return; }
  armed(rbtn,'Take it over from '+otherDevice(sv)+'?',()=>{
    simResume(); simClaim();
  });
}
function recordPaper(n,pct){""")

# ------------------------------ 3. starting a paper over someone else's live exam
sub("""    const b=document.createElement('button');
    b.className='buy'; b.textContent=rec?'Retake':'Start';
    b.onclick=()=>startPaper(n);""",
"""    const b=document.createElement('button');
    b.className='buy'; b.textContent=rec?'Retake':'Start';
    // startPaper clears the saved run, which would delete an exam still open elsewhere
    b.onclick=()=>{
      const open=simSaved();
      if(open&&!simOwns(open)){
        armed(b,'Discard the exam on '+otherDevice(open)+'?',()=>startPaper(n));
        return;
      }
      startPaper(n);
    };""")

# ------------------------------- 4. the exam is claimed the moment it starts here
sub("""  renderClock();
  simLoad();
}
function paperRec(n){""",
"""  renderClock();
  simLoad();
  simClaim();
}
function paperRec(n){""")

# -------------------------------------------- 5. pull when the tab comes forward
sub("""// every local save schedules a debounced push, so normal play keeps the cloud current
function cloudTouch(){""",
"""// A tab left open all day used to never look at the cloud again. Now every time it comes
// forward it pulls first, which is when the other device's work actually matters.
let lastPull=0, pulling=false;
async function syncOnFocus(){
  if(!sb||!sbUser||pulling||syncing) return;
  if(Date.now()-lastPull<5000) return;       // rapid tab flips are not five round trips
  pulling=true;
  try{ await syncNow(true); }
  catch(e){}
  finally{ pulling=false; lastPull=Date.now(); }
}
if(typeof document!=='undefined'){
  document.addEventListener('visibilitychange',()=>{ if(!document.hidden) syncOnFocus(); });
}
if(typeof window!=='undefined') window.addEventListener('focus',syncOnFocus);

// every local save schedules a debounced push, so normal play keeps the cloud current
function cloudTouch(){""")

# ------------------------------------------- 6. every merge re-checks ownership
sub("""      try{ await window.storage.set('academy_profile',JSON.stringify(P),false); }catch(e){}
      refreshTop(); renderHome(); renderDaily&&renderDaily(); renderInv&&renderInv();
    }""",
"""      try{ await window.storage.set('academy_profile',JSON.stringify(P),false); }catch(e){}
      refreshTop(); renderHome(); renderDaily&&renderDaily(); renderInv&&renderInv();
      // did the merge just hand our exam to the other device?
      if(simOwnerCheck()) { syncing=false; renderAuth(); return; }
      if(route==='paperScreen') renderPapers();
    }""")

# ----------------------------------------------------------------- 7. the styling
sub(""".fsbtn{font-family:var(--mono);font-size:12px;font-weight:600;padding:9px 11px;border-radius:9px;""",
""".elsewhere{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.4px;
  color:var(--gold);border:1px solid var(--gold);border-radius:6px;padding:1px 5px;
  margin-left:6px;white-space:nowrap;vertical-align:1px}
.buy.wide{display:block;width:100%;text-align:center;white-space:normal;line-height:1.35}
.fsbtn{font-family:var(--mono);font-size:12px;font-weight:600;padding:9px 11px;border-radius:9px;""")

# ------------------------------------------------------------------ 8. the harness
sub("""    SUPA, CLOUD_ON, mergeProfiles, renderAuth, authCreds, syncNow, cloudTouch, loadSupabase,""",
"""    get DEVICE_ID(){return DEVICE_ID;}, set DEVICE_ID(v){DEVICE_ID=v;},
    get DEVICE_KIND(){return DEVICE_KIND;}, set DEVICE_KIND(v){DEVICE_KIND=v;},
    otherDevice, simOwns, simOwnerCheck, simClaim, simSaveNewer, simResumeHere,
    syncOnFocus, armed,
    SUPA, CLOUD_ON, mergeProfiles, renderAuth, authCreds, syncNow, cloudTouch, loadSupabase,""")

PAGE.write_text(s, encoding="utf-8")
print("focus pull and exam handover wired · page %.2f MB" % (len(s) / 1e6))
