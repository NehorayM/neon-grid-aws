#!/usr/bin/env python3
"""Opening the app on a second device threw away the exam on the first.

The chain, read from the code:
  1. resumeOnBoot() resumed this device's OWN saved copy of the exam straight away, before the
     cloud had been looked at. A phone last used at question 4 reopened question 4.
  2. Resuming claims the paper (a fresh claimAt) and pushCloud() then wrote the phone's whole
     profile over the cloud's — a plain upsert, no merge. So did every ordinary save after it,
     through cloudTouch(): the cloud was last-writer-wins, merged only when a device pulled.
  3. simSaveNewer() decides between two copies of the exam by who CLAIMED last. The phone's
     stale copy had the newest claim, so it won; the desktop's 30-second ownership check saw the
     paper "picked up on your phone", stopped, and dropped question 34 on the floor.

Fixes:
  - Every exam run carries an id (rid). For two copies of the SAME run, the one with more
    answered questions wins, whoever claimed last. Answers only change when you act, so a stale
    copy can never beat the live one; equal copies still go by claim, so two open devices do not
    ping-pong the paper between them.
  - On boot, the cloud is consulted before anything is resumed (up to six seconds). If the paper
    is running on another device it is not resumed here; a toast says where it is.
  - Claims and ordinary saves go through syncNow() — pull, merge, push — instead of a blind
    upsert, so no device's write replaces another device's progress wholesale.
  - Running exams, as a backup. Every save also records a copy per run per device in P.runs,
    merged by union, so a copy is never lost to a merge: if a device's exam is taken away by
    another, its own copy stays (paused, so restoring it does not charge the time). The Exam
    screen lists them — which exam, which question, how many answered, time left, which device,
    when — and any can be continued here. A run is dropped when it is submitted or deliberately
    discarded, and that is remembered across devices so a stale device cannot bring it back.
  - The paper-record merge rebuilt each record from four fields and dropped the practice/exam
    marks; they are kept.

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

# ---- run identity ------------------------------------------------------------------------
sub("""function simAnsweredIn(sv){ return Object.keys(sv.ans||{}).filter(k=>(sv.ans[k]||[]).length).length; }""",
"""function simAnsweredIn(sv){ return Object.keys(sv.ans||{}).filter(k=>(sv.ans[k]||[]).length).length; }
// Which run of an exam a save belongs to. A save from before run ids falls back to the paper and
// its questions, which is the same thing for any one run.
function newRid(){ return Date.now().toString(36)+Math.random().toString(36).slice(2,8); }
function svRid(sv){
  if(!sv) return '';
  if(sv.rid) return String(sv.rid);
  const qs=sv.qs||[];
  return 'L'+(sv.paper||0)+'-'+qs[0]+'-'+qs.length;
}
// ---------- running exams, kept as a backup ----------
// One copy per run per device, merged by union, so no merge can lose a device's copy.
const RUN_KEEP=8, RUN_DAYS=14;
function runPrune(p){
  p=p||P;
  const done=new Set(p.runsDone||[]), cut=Date.now()-RUN_DAYS*864e5;
  const runs=p.runs&&typeof p.runs==='object'?p.runs:{};
  const ks=Object.keys(runs).filter(k=>{ const r=runs[k];
    return r&&Array.isArray(r.qs)&&r.qs.length&&!done.has(svRid(r))&&(Number(r.at)||0)>cut; });
  ks.sort((a,b)=>(Number(runs[b].at)||0)-(Number(runs[a].at)||0));
  const keep=new Set(ks.slice(0,RUN_KEEP)), out={};
  keep.forEach(k=>{ out[k]=runs[k]; });
  p.runs=out;
}
function runRecord(sv){
  if(!sv||!Array.isArray(sv.qs)||!sv.qs.length) return;
  const rid=svRid(sv);
  if((P.runsDone||[]).includes(rid)) return;
  P.runs=P.runs||{};
  const copy=JSON.parse(JSON.stringify(sv)); copy.rid=rid;
  P.runs[rid+'|'+(sv.dev||DEVICE_ID)]=copy;
  runPrune();
}
// submitted, or deliberately thrown away: gone on every device, and not brought back by one
// that has not heard yet
function runDone(rid){
  if(!rid) return;
  P.runsDone=[...new Set([...(P.runsDone||[]),rid])].slice(-60);
  runPrune();
}""")

sub("""  sim={qs,i:0,ans:{},flag:{},rev:{},qt:{},running:true,paper:n,mins:budget,""",
    """  sim={qs,i:0,ans:{},flag:{},rev:{},qt:{},running:true,paper:n,mins:budget,rid:newRid(),""")
sub("""  sim={qs,i:0,ans:{},flag:{},rev:{},running:true,
       paper:0,mins:budget,qt:{},""",
    """  sim={qs,i:0,ans:{},flag:{},rev:{},running:true,rid:newRid(),
       paper:0,mins:budget,qt:{},""")
sub("""       mode:'practice', running:true, paper:lp.paper||0, mins:lp.mins||SIM_MIN,""",
    """       mode:'practice', running:true, paper:lp.paper||0, mins:lp.mins||SIM_MIN, rid:newRid(),""")

# the save carries it, and every save leaves a copy in the running-exams list
sub("""  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},""",
    """  P.simSave=simSnapshot();
  runRecord(P.simSave);
  saveProfile();
}
function simSnapshot(){
  return {paper:sim.paper||0, rid:sim.rid||svRid({paper:sim.paper,qs:sim.qs}),
             qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},""")
sub("""             paused:0};   // a running paper; Quit overwrites this with 1
  saveProfile();
}""",
"""             paused:0};   // a running paper; Quit overwrites this with 1
}""")

sub("""  sim={qs:sv.qs, i:at, ans:sv.ans||{}, flag:sv.flag||{},""",
    """  sim={qs:sv.qs, i:at, ans:sv.ans||{}, flag:sv.flag||{}, rid:svRid(sv),""")

# submitted or thrown away: the run is done everywhere
sub("""function simClearSave(){ if(P.simSave){ delete P.simSave; saveProfile(); } }""",
    """function simClearSave(){ if(P.simSave){ runDone(svRid(P.simSave)); delete P.simSave; saveProfile(); } }""")

# Quit keeps the run, paused
sub("""function simPauseSave(){
  if(P.simSave) { P.simSave.paused=1; P.simSave.at=Date.now(); saveProfile(); }
}""",
"""function simPauseSave(){
  if(P.simSave) { P.simSave.paused=1; P.simSave.at=Date.now(); runRecord(P.simSave); saveProfile(); }
}""")

# ---- the merge: the copy that got further wins ---------------------------------------------
sub("""function simSaveNewer(x,y){
  if(!x) return y||undefined;
  if(!y) return x;""",
"""function simSaveNewer(x,y){
  if(!x) return y||undefined;
  if(!y) return x;
  // Two copies of the SAME run: the one with more answers is the paper. Going by the latest
  // claim let a phone reopening its own old copy (question 4) beat the desktop at question 34,
  // and the desktop's progress was dropped. Answers only change when you act, so equal copies
  // still go by claim below and two open devices do not ping-pong the paper.
  if(svRid(x)===svRid(y)){
    const ax=simAnsweredIn(x), ay=simAnsweredIn(y);
    if(ax!==ay) return ay>ax?y:x;
  }""")

sub("""  const sv=simSaveNewer(a.simSave,b.simSave);
  if(sv) out.simSave=sv; else delete out.simSave;""",
"""  const sv=simSaveNewer(a.simSave,b.simSave);
  if(sv) out.simSave=sv; else delete out.simSave;
  // running exams: every device's copy of every run, the later of each; nothing is dropped
  out.runsDone=[...new Set([...(a.runsDone||[]),...(b.runsDone||[])])].slice(-60);
  out.runs={};
  new Set([...Object.keys(a.runs||{}),...Object.keys(b.runs||{})]).forEach(k=>{
    const x=(a.runs||{})[k], y=(b.runs||{})[k];
    out.runs[k]=(!x||!y)?(x||y):((Number(y.at)||0)>=(Number(x.at)||0)?y:x);
  });
  runPrune(out);
  // a run finished elsewhere is not left open here
  if(out.simSave&&out.runsDone.includes(svRid(out.simSave))) delete out.simSave;""")

# the paper-record merge kept four fields and dropped the practice/exam marks
sub("""    out.papers[k]={best:Math.max(x.best||0,y.best||0),
                   tries:Math.max(x.tries||0,y.tries||0),
                   last:(aNewer?x.last:y.last)||x.last||y.last,
                   d:(aNewer?x.d:y.d)||x.d||y.d};""",
"""    const hi=(y.best||0)>=(x.best||0)?y:x, nw=aNewer?x:y, od=aNewer?y:x;
    out.papers[k]={best:Math.max(x.best||0,y.best||0),
                   tries:Math.max(x.tries||0,y.tries||0),
                   last:nw.last||od.last,
                   d:nw.d||od.d};
    if(hi.bestMode) out.papers[k].bestMode=hi.bestMode;
    if(nw.lastMode||od.lastMode) out.papers[k].lastMode=nw.lastMode||od.lastMode;
    if(x.ptries||y.ptries) out.papers[k].ptries=Math.max(x.ptries||0,y.ptries||0);""")

# ---- a device whose exam is taken away keeps its own copy ----------------------------------------
sub("""  if(simOwns(sv)) return false;
  simQStop(); ttsStop(); hideExplain();
  sim=null; renderClock(); syncNav();""",
"""  if(simOwns(sv)) return false;
  // Keep what this device had. It is paused — it was taken away, not walked away from — so
  // continuing it later from the running-exams list does not charge the time in between.
  try{ const mine=simSnapshot(); mine.paused=1; runRecord(mine); saveProfile(); }catch(e){}
  simQStop(); ttsStop(); hideExplain();
  sim=null; renderClock(); syncNav();""")

# ---- no blind writes: claims and saves merge first -----------------------------------------------
sub("""  if(typeof pushCloud==='function'&&typeof sb!=='undefined'&&sb&&sbUser) pushCloud();
}""",
"""  // pull, merge, push — a plain upsert here is what wrote a stale copy over the other device
  if(typeof syncNow==='function'&&typeof sb!=='undefined'&&sb&&sbUser) syncNow(true);
}""")

sub("""  syncTimer=setTimeout(()=>{ pushCloud().then(renderAuth); },4000);""",
    """  // merged, not overwritten: a blind push replaced the other device's work wholesale
  syncTimer=setTimeout(()=>{ syncNow(true); },4000);""")

# ---- boot: look at the cloud before resuming anything ------------------------------------------------
sub("""function resumeOnBoot(){
  if(TEST) return;                       // the harness drives resumes itself
  try{
    const sv=simSaved();
    if(!sv||sv.paused) return;           // Quit is a decision; do not undo it
    if(!simOwns(sv)) return;             // another device's paper is that device's to take back
    simResume();""",
"""async function resumeOnBoot(){
  if(TEST) return;                       // the harness drives resumes itself
  // Look at the cloud first. Resuming this device's own copy straight away is how a phone
  // reopened question 4 and, by claiming it, took the paper off a desktop at question 34.
  try{ await Promise.race([authFirst||Promise.resolve(), new Promise(r=>setTimeout(r,6000))]); }catch(e){}
  try{
    if(sim&&sim.running) return;         // something was opened while we waited
    const sv=simSaved();
    if(!sv||sv.paused) return;           // Quit is a decision; do not undo it
    if(!simOwns(sv)){                    // another device's paper is that device's to take back
      toast('\\u{1f4f1} '+(sv.paper?'Exam '+sv.paper:'The mock exam')+' is running on '+otherDevice(sv)+
            ' at question '+((sv.i||0)+1)+' \\u2014 open Exam to continue it here');
      return;
    }
    simResume();""")

sub("""go('homeScreen');
initAuth();""",
"""go('homeScreen');
authFirst=initAuth();""")
sub("""let ownIv=null;""", """let ownIv=null;
let authFirst=null;          // the first cloud sync on this load, so a resume can wait for it""")

# ---- the running-exams list --------------------------------------------------------------------------
sub("""    <div class="list" id="paperList"></div>
  </div>""",
"""    <div id="runBox" class="hidden">
      <div class="sechead">Running exams</div>
      <p class="sub" style="margin:-4px 0 8px">Every exam you have open, on any of your devices. Continue any of them here.</p>
      <div class="list" id="runList"></div>
    </div>
    <div class="list" id="paperList"></div>
  </div>""")

sub("""function renderSimCont(){""",
"""function runAgo(ms){
  const m=Math.max(0,Math.round((Date.now()-ms)/60000));
  return m<1?'just now':m<60?m+' min ago':m<1440?Math.round(m/60)+' h ago':Math.round(m/1440)+' d ago';
}
function renderRuns(){
  const box=$('runBox'), L=$('runList'); if(!box||!L) return;
  runPrune();
  const runs=P.runs||{};
  const ks=Object.keys(runs).filter(k=>runs[k].qs.every(i=>!!QS[i]))
    .sort((a,b)=>(Number(runs[b].at)||0)-(Number(runs[a].at)||0));
  box.classList.toggle('hidden',!ks.length);
  L.innerHTML='';
  // the furthest copy of each run is the one to reach for
  const best={};
  ks.forEach(k=>{ const r=runs[k], rid=svRid(r), n=simAnsweredIn(r);
    if(!(rid in best)||n>best[rid].n) best[rid]={k,n}; });
  ks.forEach(k=>{
    const r=runs[k], n=simAnsweredIn(r), here=(r.dev||'')===DEVICE_ID;
    const live=!!(sim&&sim.running&&sim.rid===svRid(r)&&here);
    const left=Math.max(0,Number(r.left)||0);
    const row=document.createElement('div'); row.className='item runrow';
    const title=(r.paper?'Exam '+(Number(r.paper)|0):'Mock exam')+(r.mode==='practice'?' \\u00b7 practice':'')+
      (best[svRid(r)].k===k&&Object.keys(best).length&&ks.filter(x=>svRid(runs[x])===svRid(r)).length>1?' \\u00b7 furthest':'');
    const meta='question '+((Number(r.i)|0)+1)+' of '+r.qs.length+' \\u00b7 '+n+' answered \\u00b7 '+
      fmtClock(left)+' left \\u00b7 '+(here?'this device':otherDevice(r))+' \\u00b7 '+runAgo(Number(r.at)||0)+
      (r.paused?' \\u00b7 paused':'');
    row.innerHTML='<div class="em">'+(live?'\\u25b6':'\\u23f8')+'</div>'+
      '<div style="flex:1;min-width:0"><div class="nm"></div><div class="ds"></div></div>';
    row.querySelector('.nm').textContent=title;
    row.querySelector('.ds').textContent=meta;
    const b=document.createElement('button'); b.className='buy';
    b.textContent=live?'Open':'Continue';
    b.setAttribute('aria-label',(live?'Open ':'Continue ')+title+', '+meta);
    b.onclick=()=>live?go('quizScreen'):runRestore(k,b);
    row.appendChild(b); L.appendChild(row);
  });
}
function runRestore(k,btn){
  const r=(P.runs||{})[k]; if(!r) return;
  const n=simAnsweredIn(r);
  const go2=()=>{
    if(sim&&sim.running) simAbandon();           // the one open now is kept, paused, in this list
    const sv=JSON.parse(JSON.stringify(r));
    sv.rid=svRid(r); sv.dev=DEVICE_ID; sv.devKind=DEVICE_KIND;
    P.simSave=sv; saveProfile();
    simResume();                                  // claims it here and syncs the claim
    if(sim&&sim.running) toast('\\u21a9 Back at question '+(sim.i+1)+' \\u2014 '+plural(n,'answer')+' kept');
  };
  armed(btn,'Continue from question '+((Number(r.i)|0)+1)+' ('+n+' answered)?',go2);
}
function renderSimCont(){""")

sub("""    const b=document.createElement('button');
    b.className='buy';
    b.textContent=savedHere?'Resume':(rec?'Retake':'Start');""",
    """    const b=document.createElement('button');
    b.className='buy';
    b.textContent=savedHere?'Resume':(rec?'Retake':'Start');""")

# draw it with the exam list
sub("""function renderPapers(){
  const L=$('paperList'); if(!L) return;""",
"""function renderPapers(){
  const L=$('paperList'); if(!L) return;
  renderRuns();""")

# ---- the door, and a bank change ---------------------------------------------------------------
sub("""       'login','day','quests','simSave'],
  arr:['wrong','badges','marks','examLog','mockLog','simLog','rHist','known']""",
"""       'login','day','quests','simSave','runs'],
  arr:['wrong','badges','marks','examLog','mockLog','simLog','rHist','known','runsDone']""")
sub("""  // simSave starts life absent""",
"""  if(p.runs&&typeof p.runs==='object'){
    Object.keys(p.runs).forEach(k=>{ const r=p.runs[k];
      if(!r||typeof r!=='object'||!Array.isArray(r.qs)||!r.qs.every(i=>Number.isInteger(i))) delete p.runs[k]; });
  }
  if(Array.isArray(p.runsDone)) p.runsDone=p.runsDone.filter(x=>typeof x==='string').slice(-60);
  // simSave starts life absent""")
sub("""    delete P.lastPaper;        // it stores question indices too""",
    """    delete P.lastPaper;        // it stores question indices too
    P.runs={}; P.runsDone=[];""")

sub(""".opt.locked{opacity:.62;cursor:default}""",
""".opt.locked{opacity:.62;cursor:default}
#runBox{margin-bottom:14px}
.runrow .ds{white-space:normal}""")

# expose
sub("    isPractice, brkOpen, brkElapsed,",
    "    isPractice, brkOpen, brkElapsed, renderRuns, runRestore, runRecord, runDone, runPrune, svRid, simSnapshot,")

PAGE.write_text(s, encoding="utf-8")
print("multi-device fixed; running exams added")
