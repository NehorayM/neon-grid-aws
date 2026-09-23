#!/usr/bin/env python3
"""Exam history: every submitted exam is kept, and can be redone without a timer.

  - Every submit keeps the exam — paper, date, every answer, flags, the SAA score, right/total —
    in P.examHist (30 most recent). Finishing an exam later updates the same entry.
  - The Exam screen lists them. Redo opens one with its answers filled in, NO clock of any kind,
    every answer changeable, and the score recomputed live as you edit. "Show answer" opens the
    explanation for the question in front of you without locking it.
  - Crash-safe: a redo is saved like any paper (it is in Running exams and comes back on reload),
    and every edit also writes straight into the history entry, so the entry is current even if
    the redo is never closed properly. History is synced and merged by entry.
  - A redo is review, not an attempt: closing it updates the entry's answers and score, but pays
    no coins or XP and does not count as another exam or touch the subject statistics.

Exams finished before this build cannot be listed: their answers were never kept.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new,count=1):
    global s
    n=s.count(old); assert n>=count, "NOT FOUND (%d): %s"%(n,old[:90]); s=s.replace(old,new,count)

# ---- the mode --------------------------------------------------------------------------
sub("""const isPractice=()=>!!(sim&&sim.mode==='practice');""",
"""// A redo of a past exam: no clock at all, answers changeable, leaving is free.
const isRedo=()=>!!(sim&&sim.mode==='redo');
const isPractice=()=>!!(sim&&(sim.mode==='practice'||sim.mode==='redo'));""")
sub("""const simTeaches=()=>!!sim;""", """const simTeaches=()=>!!sim&&!isRedo();   // a redo lets you change answers, so it does not lock them""")

# ---- no clock in a redo --------------------------------------------------------------------
sub("""function simQStart(){
  simQStop();
  if(!sim||!sim.running) return;""",
"""function simQStart(){
  simQStop();
  if(!sim||!sim.running) return;
  if(isRedo()){ simQLeft=SIM_QSEC; sim.qEndAt=0; renderSimQ(); return; }   // no timer in a redo""")
sub("""function simQSync(){
  if(!sim||!sim.running){ simQStop(); return; }""",
"""function simQSync(){
  if(!sim||!sim.running){ simQStop(); return; }
  if(isRedo()) return;""")
sub("""function simQTick(by){
  if(!sim||!sim.running){ simQStop(); return; }""",
"""function simQTick(by){
  if(!sim||!sim.running){ simQStop(); return; }
  if(isRedo()) return;""")
sub("""function simCheckTime(){
  if(brkOn()) return;                       // a paused paper cannot expire""",
"""function simCheckTime(){
  if(brkOn()) return;                       // a paused paper cannot expire
  if(isRedo()) return;                      // nor one with no clock""")
sub("""  if(!sim||!sim.running){ wrap.classList.add('hidden'); return; }
  wrap.classList.remove('hidden');
  const f=Math.max(0,Math.min(1,simQLeft/SIM_QSEC));""",
"""  if(!sim||!sim.running){ wrap.classList.add('hidden'); return; }
  if(isRedo()){ wrap.classList.add('hidden'); renderSimTotal(); renderClock(); return; }
  wrap.classList.remove('hidden');
  const f=Math.max(0,Math.min(1,simQLeft/SIM_QSEC));""")
sub("""  const left=simTotalLeft(), full=simTotalFull(), qs=simQsLeft();
  // One clock. This number is the one the paper ends on.""",
"""  if(isRedo()){
    $('simTotalVal').textContent='no timer';
    $('simTotalFill').style.width='100%';
    $('simTotalSub').textContent='Redo \\u00b7 change any answer \\u00b7 the score updates as you go';
    box.classList.remove('tight');
    renderSimLive();
    return;
  }
  const left=simTotalLeft(), full=simTotalFull(), qs=simQsLeft();
  // One clock. This number is the one the paper ends on.""")
sub("""  if(sim&&sim.running){
    // A frozen countdown reads as a broken one, so during a break the clock says so and""",
"""  if(sim&&sim.running&&isRedo()){
    el.textContent='\\u270e Redo'; el.classList.remove('warn','crit');
    const sb=$('clockSub'); if(sb) sb.textContent='no timer';
    return;
  }
  if(sim&&sim.running){
    // A frozen countdown reads as a broken one, so during a break the clock says so and""")

# a redo is never charged for time away
sub("""  if(sv.mode==='practice') return 0;""", """  if(sv.mode==='practice'||sv.mode==='redo') return 0;""")
# and survives a refresh as a redo
sub("""       rev:sv.rev||{}, qt:qt, mode:sv.mode==='practice'?'practice':'exam',""",
    """       rev:sv.rev||{}, qt:qt, mode:(sv.mode==='practice'||sv.mode==='redo')?sv.mode:'exam', hid:sv.hid||null,""")
sub("""             locked:sim.locked||{}, cont:sim.cont?1:0, base:sim.base||null, tout:sim.tout||{},""",
    """             locked:sim.locked||{}, cont:sim.cont?1:0, base:sim.base||null, tout:sim.tout||{}, hid:sim.hid||null,""")

# header
sub("""  $('qSector').textContent=(sim.paper?('EXAM '+sim.paper):'EXAM SIM')+
    (isPractice()?' \\u00b7 PRACTICE':'');""",
"""  $('qSector').textContent=(sim.paper?('EXAM '+sim.paper):'EXAM SIM')+
    (isRedo()?' \\u00b7 REDO':isPractice()?' \\u00b7 PRACTICE':'');
  { const ab=$('simAnsBtn'); if(ab) ab.classList.toggle('hidden',!isRedo()); }
  { const sb=$('simSubmit'); if(sb&&!sb.dataset.armed) sb.textContent=isRedo()?'Save & close':'Submit exam'; }""")

# ---- live score over the whole paper in a redo -----------------------------------------------
sub("""  const pairs=[];
  sim.qs.forEach((qi,i)=>{
    const picked=sim.ans[i]||[];
    if(!picked.length) return;""",
"""  const pairs=[];
  sim.qs.forEach((qi,i)=>{
    const picked=sim.ans[i]||[];
    // a redo is scored like the exam it is: every question counts, blanks wrong
    if(!picked.length){ if(isRedo()) pairs.push({qi,ok:false}); return; }""")

# ---- history store -------------------------------------------------------------------------
sub("""// ---------- finish the last exam ----------""",
"""// ---------- exam history ----------
const HIST_KEEP=30;
function histPrune(p){
  p=p||P;
  const h=p.examHist&&typeof p.examHist==='object'?p.examHist:{};
  const ks=Object.keys(h).filter(k=>h[k]&&Array.isArray(h[k].qs)&&h[k].qs.length)
    .sort((a,b)=>(Number(h[b].d0)||Number(h[b].at)||0)-(Number(h[a].d0)||Number(h[a].at)||0));
  const out={}; ks.slice(0,HIST_KEEP).forEach(k=>{ out[k]=h[k]; });
  p.examHist=out;
}
function histScoreOf(qs,ans){
  const pairs=qs.map((qi,i)=>{ const q=QS[qi], set=new Set(ans[i]||[]);
    return {qi, ok:!!q&&q.a.length===set.size&&q.a.every(a=>set.has(a))}; });
  const S=saaScore(pairs)||{scaled:100,pct:0};
  return {sc:S.scaled, pct:S.pct, c:pairs.filter(p=>p.ok).length, n:qs.length};
}
// write (or update) an exam's entry from the paper in front of us
function histWrite(){
  if(!sim||!sim.qs) return;
  const hid=sim.hid||sim.rid||newRid();
  sim.hid=hid;
  P.examHist=P.examHist||{};
  const prev=P.examHist[hid]||{};
  const sc=histScoreOf(sim.qs,sim.ans||{});
  P.examHist[hid]=Object.assign({}, prev, {hid, paper:sim.paper||0, qs:sim.qs.slice(),
    ans:JSON.parse(JSON.stringify(sim.ans||{})), flag:Object.assign({},sim.flag||{}),
    mode:prev.mode||(sim.mode==='redo'?'exam':sim.mode||'exam'),
    d:prev.d||dayKey(), d0:prev.d0||Date.now(), at:Date.now(),
    redos:(prev.redos||0)+(sim.mode==='redo'&&!sim.redoCounted?1:0)}, sc);
  if(sim.mode==='redo') sim.redoCounted=1;
  histPrune();
}
function histOpen(hid,btn){
  const r=(P.examHist||{})[hid]; if(!r) return;
  if(r.qs.some(i=>!QS[i])){ toast('That exam used questions this build no longer has'); return; }
  const go2=()=>{
    if(sim&&sim.running) simAbandon();          // an exam that was open is kept, paused, in Running exams
    ensureAudio(); exitStudyMode();
    reviewMode=false; markMode=false; mock=null;
    sim={qs:r.qs.slice(), i:0, ans:JSON.parse(JSON.stringify(r.ans||{})), flag:Object.assign({},r.flag||{}),
         rev:{}, qt:{}, running:true, paper:r.paper||0, mins:0, mode:'redo', hid, rid:newRid(),
         startAt:Date.now(), endAt:Date.now()};
    const k=sim.qs.findIndex((q,i)=>!((sim.ans[i]||[]).length));
    sim.i=k>=0?k:0;
    saveProfile(); renderClock(); simLoad(); simClaim(); simPersist();
    toast('\\u270e Redo \\u2014 no timer. Change any answer; the score updates as you go');
  };
  const open=simSaved();
  if(open&&!(open.mode==='redo'&&open.hid===hid)){
    armed(btn,'Put '+(open.paper?'Exam '+open.paper:'the mock exam')+' on hold and redo this one?',go2);
    return;
  }
  go2();
}
// closing a redo: the entry keeps the new answers and score; no coins, no stats, not an attempt
function redoFinish(){
  if(!sim) return;
  histWrite();
  const e=P.examHist[sim.hid]||{};
  simQStop(); ttsStop(); hideExplain();
  { const stb=$('simTotal'); if(stb) stb.classList.add('hidden'); }
  simClearSave();
  sim=null; saveProfile(); renderClock();
  renderPapers(); go('paperScreen');
  toast('\\u2714 '+(e.paper?'Exam '+e.paper:'Mock exam')+' saved \\u2014 '+e.sc+' / 1000 ('+e.c+'/'+e.n+' right)');
}
function renderHist(){
  const box=$('histBox'), L=$('histList'); if(!box||!L) return;
  histPrune();
  const h=P.examHist||{};
  const ks=Object.keys(h).filter(k=>h[k].qs.every(i=>!!QS[i]))
    .sort((a,b)=>(Number(h[b].d0)||0)-(Number(h[a].d0)||0));
  box.classList.toggle('hidden',!ks.length);
  L.innerHTML='';
  ks.forEach(k=>{
    const r=h[k], pass=(Number(r.sc)||0)>=SAA_PASS;
    const row=document.createElement('div'); row.className='item histrow';
    row.innerHTML='<div class="em">'+(pass?'\\u{1f393}':'\\u{1f4dd}')+'</div>'+
      '<div style="flex:1;min-width:0"><div class="nm"></div><div class="ds"></div></div>';
    row.querySelector('.nm').textContent=(r.paper?'Exam '+(Number(r.paper)|0):'Mock exam')+' \\u00b7 '+(r.d||'');
    row.querySelector('.ds').textContent=(Number(r.sc)||100)+' / 1000 \\u00b7 '+(Number(r.c)|0)+'/'+(Number(r.n)|0)+
      ' right'+(r.mode==='practice'?' \\u00b7 practice':'')+(r.redos?' \\u00b7 redone '+plural(Number(r.redos)|0,'time'):'');
    const b=document.createElement('button'); b.className='buy';
    b.textContent='\\u25b6 Redo';
    b.setAttribute('aria-label','Redo '+row.querySelector('.nm').textContent+' without a timer');
    b.onclick=()=>histOpen(k,b);
    row.appendChild(b); L.appendChild(row);
  });
}
// ---------- finish the last exam ----------""")

# every submit keeps the exam; a redo's "submit" is save-and-close
sub("""function simSubmit(auto){
  simQStop();
  if(!sim) return;""",
"""function simSubmit(auto){
  simQStop();
  if(!sim) return;
  if(isRedo()){ redoFinish(); return; }""")
sub("""  if(P.lastPaper){ P.lastPaper.pct=pct; P.lastPaper.passed=passed?1:0;""",
"""  histWrite();                             // the exam goes into history, answers and all
  if(P.lastPaper) P.lastPaper.hid=sim.hid;
  if(P.lastPaper){ P.lastPaper.pct=pct; P.lastPaper.passed=passed?1:0;""")
# finishing later updates the same entry
sub("""       mode:'practice', running:true, paper:lp.paper||0, mins:lp.mins||SIM_MIN, rid:newRid(),""",
    """       mode:'practice', running:true, paper:lp.paper||0, mins:lp.mins||SIM_MIN, rid:newRid(), hid:lp.hid||null,""")

# every edit in a redo lands in history straight away
sub("""  simPersist(); renderSimStrip(); renderSimLive();
}
// ---------- feedback during a teaching paper ----------""",
"""  simPersist(); renderSimStrip(); renderSimLive();
  if(isRedo()){ histWrite(); saveProfile(); }
}
// ---------- feedback during a teaching paper ----------""")

# ---- show answer in a redo ----------------------------------------------------------------------
sub("""          <button class="simbtn" id="simFlag">⚑ Flag</button>""",
"""          <button class="simbtn" id="simFlag">⚑ Flag</button>
          <button class="simbtn hidden" id="simAnsBtn" title="Show the answer and why">\\u{1f4a1} Answer</button>""")
sub("""$('simCsv').onclick=exportLastExam;""",
"""$('simCsv').onclick=exportLastExam;
// In a redo, look at the answer and the reasoning without locking the question.
$('simAnsBtn').onclick=()=>{
  if(!sim||!isRedo()) return;
  const ex=$('explain');
  if(ex&&ex.classList.contains('show')){ hideExplain(); simLoad(); return; }
  const q=QS[sim.qs[sim.i]], picked=new Set(sim.ans[sim.i]||[]);
  const ok=q.a.length===picked.size&&q.a.every(a=>picked.has(a));
  simPaintRevealed(q,picked); renderExplain(q,picked,ok);
};""")

# ---- the list on the Exam screen -----------------------------------------------------------------
sub("""    <div class="list" id="paperList"></div>
  </div>""",
"""    <div id="histBox" class="hidden">
      <div class="sechead">Exam history</div>
      <p class="sub" style="margin:-4px 0 8px">Every exam you have submitted. Redo any of them with no timer \\u2014 change answers and watch the score move.</p>
      <div class="list" id="histList"></div>
    </div>
    <div class="list" id="paperList"></div>
  </div>""")
sub("""function renderPapers(){
  const L=$('paperList'); if(!L) return;
  renderRuns();""",
"""function renderPapers(){
  const L=$('paperList'); if(!L) return;
  renderRuns(); renderHist();""")
sub("""#runBox{margin-bottom:14px}""", """#runBox,#histBox{margin-bottom:14px}
.histrow .ds{white-space:normal}""")

# ---- sync and the door ---------------------------------------------------------------------------
sub("""  runPrune(out);
  // a run finished elsewhere is not left open here""",
"""  runPrune(out);
  // exam history: every exam from either device, the later version of each
  out.examHist={};
  new Set([...Object.keys(a.examHist||{}),...Object.keys(b.examHist||{})]).forEach(k=>{
    const x=(a.examHist||{})[k], y=(b.examHist||{})[k];
    out.examHist[k]=(!x||!y)?(x||y):((Number(y.at)||0)>=(Number(x.at)||0)?y:x);
  });
  histPrune(out);
  // a run finished elsewhere is not left open here""")
sub("""       'login','day','quests','simSave','runs'],""", """       'login','day','quests','simSave','runs','examHist'],""")
sub("""  if(Array.isArray(p.runsDone)) p.runsDone=p.runsDone.filter(x=>typeof x==='string').slice(-60);""",
"""  if(Array.isArray(p.runsDone)) p.runsDone=p.runsDone.filter(x=>typeof x==='string').slice(-60);
  if(p.examHist&&typeof p.examHist==='object'){
    Object.keys(p.examHist).forEach(k=>{ const r=p.examHist[k];
      if(!r||typeof r!=='object'||!Array.isArray(r.qs)||!r.qs.every(i=>Number.isInteger(i))){ delete p.examHist[k]; return; }
      if(!r.ans||typeof r.ans!=='object') r.ans={};
      ['sc','pct','c','n','redos','paper','at','d0'].forEach(f=>{ if(r[f]!==undefined){ const n=Number(r[f]); r[f]=isFinite(n)?n:0; } });
      if(r.d!==undefined&&!/^\\d{4}-\\d{1,2}-\\d{1,2}$/.test(String(r.d))) r.d='';
      r.mode=r.mode==='practice'?'practice':'exam';
    });
  }""")
sub("""    P.runs={}; P.runsDone=[];""", """    P.runs={}; P.runsDone=[]; P.examHist={};""")

sub("    isPractice, brkOpen, brkElapsed,",
    "    isPractice, brkOpen, brkElapsed, isRedo, histOpen, histWrite, redoFinish, renderHist,")
PAGE.write_text(s, encoding="utf-8"); print("exam history in")
