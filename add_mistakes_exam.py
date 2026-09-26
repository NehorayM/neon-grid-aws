#!/usr/bin/env python3
"""The mistakes exam: every question you got wrong, as one timed exam, with a study plan first.

Asked for: from the Redo page, an exam made of all the questions answered wrong in the kept
exams — every one of them, even past 65 — with the timer and everything, sat as a simulation or
as practice; and before it starts, statistics on which material has the most of those questions,
so there is time to go back and study it.

  - Which questions. Every question whose most recent recorded answer, across all kept exams,
    is wrong. A question got wrong once and right in a later exam is left out — it is no longer
    a mistake — and the screen says how many were left out that way. Unanswered is not wrong: an
    exam kept half-way through would otherwise pour its blanks in.
  - The screen before it (mistakeScreen, from a card on the Redo page): how many questions, from
    which exams, how long; where the mistakes are by SAA-C03 domain; and every subject area with
    mistakes in it, most first, with your accuracy there and a Study button that opens the
    chapter covering it. Also a CSV of the questions.
  - The exam. All of them, shuffled, 105 s a question — the paper clock is the same arithmetic
    for 47 or 140 questions. Simulation or practice through the usual picker. It resumes,
    backs up, finishes later and syncs like any other exam, and goes into the Redo list as
    "Mistakes exam", where its own answers count toward the next one.
  - An exam that was open is put on hold (kept in Running exams), not deleted.

`sim.kind` = 'mistakes' is carried by every copy of a run: the save, the running-exams backup, the
finish-later copy, the history entry and a redo of it. `examLabel()` names an exam everywhere a
label was built from `paper` alone, which could only say "Exam N" or "the mock exam".

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

# ---------------------------------------------------------------- one name for an exam
sub("""let sim=null;
const simLen=()=>sim?sim.qs.length:SIM_LEN;""","""let sim=null;
// What an exam is called, from anything that describes one (a run, a save, a history entry).
// Labels were built from `paper` alone, which can only say "Exam N" or "the mock exam".
function examLabel(o,the){
  o=o||{};
  if(o.kind==='mistakes') return the?'the mistakes exam':'Mistakes exam';
  if(Number(o.paper)) return 'Exam '+(Number(o.paper)|0);
  return the?'the mock exam':'Mock exam';
}
const capFirst=t=>String(t).charAt(0).toUpperCase()+String(t).slice(1);
const simLen=()=>sim?sim.qs.length:SIM_LEN;""")

LABELS = [
  ("""armed(btn,'Put '+(open.paper?'Exam '+open.paper:'the mock exam')+' on hold and redo this one?',go2);""",
   """armed(btn,'Put '+examLabel(open,1)+' on hold and redo this one?',go2);""", 1),
  ("""toast('\\u2714 '+(e.paper?'Exam '+e.paper:'Mock exam')+' saved \\u2014 '""",
   """toast('\\u2714 '+examLabel(e)+' saved \\u2014 '""", 1),
  ("""(h[k].paper?'Exam '+(Number(h[k].paper)|0):'Mock')+': '+v+'\"></div>'""",
   """examLabel(h[k])+': '+v+'\"></div>'""", 1),
  ("""(r.paper?'Exam '+(Number(r.paper)|0):'Mock exam')""", """examLabel(r)""", 4),
  ("""function lastLabel(lp){ return lp&&lp.paper?('Exam '+lp.paper):'the mock exam'; }""",
   """function lastLabel(lp){ return examLabel(lp,1); }""", 1),
  ("""(open.paper?'Exam '+open.paper:'the mock exam')""", """examLabel(open,1)""", 2),
  ("""(sv.paper?'Exam '+sv.paper:'the mock exam')""", """examLabel(sv,1)""", 1),
  ("""const exam=r.paper?'Exam '+(Number(r.paper)|0):'Mock exam';""", """const exam=examLabel(r);""", 1),
  ("""(sv.paper?'Exam '+sv.paper:'The mock exam')""", """capFirst(examLabel(sv,1))""", 1),
  ("""(sim.paper?'Exam '+sim.paper:'the mock exam')""", """examLabel(sim,1)""", 1),
]
for old, new, n in LABELS:
    sub(old, new, n)

# ---------------------------------------------------------------- kind travels with every copy of a run
sub("""  return {paper:sim.paper||0, rid:sim.rid||svRid({paper:sim.paper,qs:sim.qs}),""",
    """  return {paper:sim.paper||0, kind:sim.kind||'', rid:sim.rid||svRid({paper:sim.paper,qs:sim.qs}),""")
sub("""       running:true, paper:sv.paper||0, mins:sv.mins,""",
    """       running:true, paper:sv.paper||0, kind:sv.kind||'', mins:sv.mins,""")
sub("""       mode:'practice', running:true, paper:lp.paper||0, mins:lp.mins||SIM_MIN, rid:newRid(), hid:lp.hid||null,""",
    """       mode:'practice', running:true, paper:lp.paper||0, kind:lp.kind||'', mins:lp.mins||SIM_MIN, rid:newRid(), hid:lp.hid||null,""")
sub("""  P.examHist[hid]=Object.assign({}, prev, {hid, paper:sim.paper||0, qs:sim.qs.slice(),""",
    """  P.examHist[hid]=Object.assign({}, prev, {hid, paper:sim.paper||0, kind:sim.kind||prev.kind||'', qs:sim.qs.slice(),""")
sub("""         rev:{}, qt:{}, running:true, paper:r.paper||0, mins:0, mode:'redo', hid, rid:newRid(),""",
    """         rev:{}, qt:{}, running:true, paper:r.paper||0, kind:r.kind||'', mins:0, mode:'redo', hid, rid:newRid(),""")
sub("""  { const snap={paper, qs:sim.qs.slice(), ans:Object.assign({},sim.ans), flag:Object.assign({},sim.flag),""",
    """  { const snap={paper, kind:sim.kind||'', qs:sim.qs.slice(), ans:Object.assign({},sim.ans), flag:Object.assign({},sim.flag),""")

# ---------------------------------------------------------------- the results screen knows what it scored
sub("""  const paper=sim.paper||0;
  const cont=!!sim.cont, base=sim.base||{blank:{},pct:0,passed:0};""",
"""  const paper=sim.paper||0, kind=sim.kind||'';
  const cont=!!sim.cont, base=sim.base||{blank:{},pct:0,passed:0};""")
sub("""  lastExamCsv={paper,name:(paper?'skyforge-exam-'+paper:'skyforge-sim')+'-'+dayKey()+'.csv',list:csv};""",
"""  lastExamCsv={paper,kind,name:(kind==='mistakes'?'skyforge-mistakes':paper?'skyforge-exam-'+paper:'skyforge-sim')+'-'+dayKey()+'.csv',list:csv};""")
sub("""  $('simVerdict').textContent=(paper?'Exam '+paper+' — ':'')+""",
"""  $('simVerdict').textContent=(paper||kind?examLabel({paper,kind})+' — ':'')+""")
sub("""  $('simAgain').textContent=paper?(paper<PAPER_COUNT?'Exam '+(paper+1)+' ›':'Back to exams'):'Run another';""",
"""  $('simAgain').textContent=kind==='mistakes'?'New mistakes exam ›':
    paper?(paper<PAPER_COUNT?'Exam '+(paper+1)+' ›':'Back to exams'):'Run another';""")
sub("""$('simAgain').onclick=()=>{
  const n=(lastExamCsv&&lastExamCsv.paper)||0;""","""$('simAgain').onclick=()=>{
  if(lastExamCsv&&lastExamCsv.kind==='mistakes'){ openMistakes(); return; }
  const n=(lastExamCsv&&lastExamCsv.paper)||0;""")

# ---------------------------------------------------------------- the mode picker says how many
sub("""function modeAsk(label,then){
  modePending=then||null;
  $('modeAskTitle').textContent='How do you want to sit '+label+'?';
  $('modeAskSub').textContent='Same 65 questions and the same clock either way. What changes '+
    'is whether you can stop.';""","""function modeAsk(label,then,sub){
  modePending=then||null;
  $('modeAskTitle').textContent='How do you want to sit '+label+'?';
  $('modeAskSub').textContent=sub||('Same 65 questions and the same clock either way. What changes '+
    'is whether you can stop.');""")
sub("""      <p class="sub modenote">Both are the same 65 questions on the same clock. Only""",
    """      <p class="sub modenote">Both are the same questions on the same clock. Only""")

# ---------------------------------------------------------------- the mistakes exam itself
sub("""// ---------- numbered practice exams ----------
// Paper N is always the same 65 questions,""","""// ---------- the mistakes exam ----------
// Every question whose most recent answer, across the kept exams, is wrong. A question missed
// once and answered right in a later exam is not a mistake any more; a blank is not one at all
// (a kept exam stopped half-way would pour its blanks in).
function mistakeSet(){
  const h=P.examHist||{}, last={}, from={}, everWrong=new Set();
  Object.values(h).forEach(e=>{
    if(!e||!Array.isArray(e.qs)) return;
    const at=Number(e.at)||0, label=examLabel(e);
    e.qs.forEach((qi,i)=>{
      const q=QS[qi]; if(!q) return;
      const a=(e.ans||{})[i]; if(!Array.isArray(a)||!a.length) return;
      const ok=a.length===q.a.length&&q.a.every(l=>a.includes(l));
      if(!ok){ everWrong.add(qi); (from[qi]=from[qi]||new Set()).add(label); }
      if(!last[qi]||at>=last[qi].at) last[qi]={ok,at};
    });
  });
  const qs=[...everWrong].filter(qi=>last[qi]&&!last[qi].ok).sort((a,b)=>a-b);
  const exams=new Set(); qs.forEach(qi=>from[qi].forEach(x=>exams.add(x)));
  return {qs, fixed:everWrong.size-qs.length, exams:[...exams], from};
}
// where they are: by SAA-C03 domain, and by subject area (most first)
function mistakeStats(qs){
  const dom=[0,0,0,0], per={};
  qs.forEach(qi=>{ dom[qDom(qi)]++; const sc=QS[qi].s; per[sc]=(per[sc]||0)+1; });
  const secs=Object.keys(per).map(k=>({sec:Number(k),n:per[k]})).sort((a,b)=>b.n-a.n||a.sec-b.sec);
  return {dom, secs};
}
const fmtMins=m=>m>=60?Math.floor(m/60)+' h '+String(m%60).padStart(2,'0')+' min':m+' min';
const stuChapterFor=sc=>(typeof STU_SECS!=='undefined')?STU_SECS.findIndex(a=>a.includes(sc)):-1;
function renderMistakes(){
  const ms=mistakeSet(), n=ms.qs.length;
  $('mistakeEmpty').classList.toggle('hidden',!!n);
  ['mistakeStats','mistakeDomBox','mistakeSecBox','mistakeActs'].forEach(id=>$(id).classList.toggle('hidden',!n));
  if(!n){
    $('mistakeSub').textContent=ms.fixed?'Every question you got wrong has been answered right since. Nothing to practise.':
      'No mistakes in your kept exams yet.';
    return ms;
  }
  const mins=simBudget(n);
  $('mistakeSub').textContent='Every question you got wrong in your kept exams — all '+n+' of them, '+
    'shuffled, '+SIM_QSEC+' s a question like the real thing.'+
    (ms.fixed?' '+plural(ms.fixed,'question')+' you have since answered right '+(ms.fixed===1?'is':'are')+' left out.':'');
  $('mistakeStats').innerHTML=
    '<div class="stat"><b>'+n+'</b><span>questions</span></div>'+
    '<div class="stat"><b>'+ms.exams.length+'</b><span>'+(ms.exams.length===1?'exam':'exams')+'</span></div>'+
    '<div class="stat"><b>'+mins+'</b><span>minutes</span></div>'+
    '<div class="stat"><b>'+mistakeStats(ms.qs).secs.length+'</b><span>subjects</span></div>';
  const st=mistakeStats(ms.qs);
  $('mistakeDoms').innerHTML=DOMAINS.map(d=>{
    const c=st.dom[d.id], p=Math.round(c/n*100);
    return '<div class="bsrow" style="--dcol:'+DOMAIN_COL[d.id]+'">'+
      '<div class="bshead"><span class="bsnm">'+esc(d.nm)+'</span><span class="bspct">'+c+'</span></div>'+
      '<div class="bsbar"><i style="width:'+pctW(p)+'"></i></div>'+
      '<div class="bsmeta">'+p+'% of this exam \\u00b7 '+d.w+'% of the real one</div></div>';
  }).join('');
  const top=st.secs[0]?st.secs[0].n:1;
  const L=$('mistakeSecs'); L.innerHTML='';
  st.secs.forEach((r,k)=>{
    const acc=(P.secStats||{})[r.sec], pct=acc&&acc.a?Math.round(acc.c/acc.a*100):null;
    const row=document.createElement('div'); row.className='bsrow mkrow';
    row.style.setProperty('--dcol',DOMAIN_COL[domainOf(r.sec)]||'var(--cyan)');
    row.innerHTML='<div class="bshead"><span class="bsnm"></span><span class="bspct">'+r.n+'</span></div>'+
      '<div class="bsbar"><i style="width:'+pctW(r.n/top*100)+'"></i></div>'+
      '<div class="mkmeta"><span class="bsmeta"></span></div>';
    row.querySelector('.bsnm').textContent=secEm(r.sec)+' '+(SHORT[r.sec]||SECTIONS[r.sec])+(k<3?'  \\u00b7 study first':'');
    if(k<3) row.classList.add('first');
    row.querySelector('.bsmeta').textContent=plural(r.n,'question')+' \\u00b7 '+Math.round(r.n/n*100)+'% of this exam'+
      (pct===null?'':' \\u00b7 you are '+pct+'% right here overall');
    const ch=stuChapterFor(r.sec);
    if(ch>=0){
      const b=document.createElement('button'); b.className='mkstudy'; b.textContent='\\u{1f4d6} Study';
      b.setAttribute('aria-label','Study '+(SHORT[r.sec]||SECTIONS[r.sec]));
      b.onclick=()=>stuOpen(ch);
      row.querySelector('.mkmeta').appendChild(b);
    }
    L.appendChild(row);
  });
  $('mistakeStart').textContent='Start the mistakes exam \\u2014 '+n+' questions \\u00b7 '+fmtMins(mins)+' \\u25b8';
  return ms;
}
function openMistakes(){ renderMistakes(); go('mistakeScreen'); syncNav(); }
function startMistakes(mode){
  const ms=mistakeSet();
  if(!ms.qs.length){ toast('No mistakes left to practise'); openMistakes(); return; }
  // whatever was open is put on hold in Running exams, not deleted — the way a redo does it
  if(sim&&sim.running) simAbandon();
  if(P.simSave) runRecord(P.simSave);
  ensureAudio(); exitStudyMode();
  reviewMode=false; markMode=false; mock=null;
  const qs=shuffle(ms.qs.slice());
  const budget=simBudget(qs.length);
  sim={qs,i:0,ans:{},flag:{},rev:{},qt:{},running:true,paper:0,kind:'mistakes',mins:budget,rid:newRid(),
       mode:(mode==='practice'?'practice':'exam'),
       startAt:Date.now(),endAt:Date.now()+budget*60000};
  saveProfile(); renderClock(); simLoad(); simClaim(); simPersist();
}
function mistakeAsk(btn){
  const ms=mistakeSet(), n=ms.qs.length; if(!n) return;
  const ask=()=>modeAsk('the mistakes exam',m=>startMistakes(m),
    'Same '+n+' questions and the same clock \\u2014 '+fmtMins(simBudget(n))+' \\u2014 either way. '+
    'What changes is whether you can stop.');
  const open=simSaved();
  if(open&&btn){ armed(btn,'Put '+examLabel(open,1)+' on hold and start?',ask); return; }
  ask();
}
function mistakeCsv(){
  const ms=mistakeSet();
  if(!ms.qs.length){ toast('No mistakes to export'); return false; }
  const list=ms.qs.map(qi=>({i:qi, why:'Wrong in '+[...ms.from[qi]].join(', ')}));
  const ok=downloadCsv('skyforge-mistakes-'+dayKey()+'.csv',csvRows(list));
  toast(ok?'\\u2b07 '+plural(list.length,'question')+' exported':'Export blocked by the browser');
  return ok;
}
// ---------- numbered practice exams ----------
// Paper N is always the same 65 questions,""")

# ---------------------------------------------------------------- the card on the Redo page
sub("""    <div class="rdtools"><button class="btn ghost sm hidden" id="redoCsvAll">⬇ All exams (CSV)</button></div>""",
"""    <div class="card mkentry hidden" id="redoMistakes">
      <div class="mkentry-in"><span class="mkic">🎯</span>
        <div class="mkentry-t"><b id="redoMkTitle">Mistakes exam</b><span id="redoMkSub"></span></div></div>
      <button class="btn sm" id="redoMkGo">See what to study ▸</button>
    </div>
    <div class="rdtools"><button class="btn ghost sm hidden" id="redoCsvAll">⬇ All exams (CSV)</button></div>""")
sub("""  $('redoEmpty').classList.toggle('hidden',!!ks.length);
  $('redoCsvAll').classList.toggle('hidden',!ks.length);""","""  $('redoEmpty').classList.toggle('hidden',!!ks.length);
  $('redoCsvAll').classList.toggle('hidden',!ks.length);
  { const ms=mistakeSet(), n=ms.qs.length;
    $('redoMistakes').classList.toggle('hidden',!n);
    if(n){
      $('redoMkTitle').textContent='Mistakes exam \\u2014 '+plural(n,'question');
      $('redoMkSub').textContent='Everything you got wrong, from '+plural(ms.exams.length,'exam')+
        ' \\u00b7 '+fmtMins(simBudget(n))+' on the clock';
    } }""")

# ---------------------------------------------------------------- its screen
sub("""  <div id="paperScreen" class="screen hidden">""","""  <div id="mistakeScreen" class="screen hidden">
    <button class="backbtn" id="mistakeBack" aria-label="Back to Exam Redo">‹</button>
    <div style="text-align:center;margin-bottom:12px">
      <h2 class="head">🎯 Mistakes exam</h2>
      <p class="sub" id="mistakeSub"></p>
    </div>
    <div class="statstrip" id="mistakeStats"></div>
    <div class="card" id="mistakeDomBox">
      <div class="cardhead"><span class="ch-t">Where your mistakes are</span><span class="ch-s">by exam domain</span></div>
      <div id="mistakeDoms"></div>
    </div>
    <div class="card" id="mistakeSecBox">
      <div class="cardhead"><span class="ch-t">Study these before you start</span><span class="ch-s">most mistakes first</span></div>
      <div id="mistakeSecs"></div>
    </div>
    <div class="mkacts" id="mistakeActs">
      <button class="btn wide" id="mistakeStart">Start the mistakes exam ▸</button>
      <button class="btn ghost sm" id="mistakeCsv">⬇ These questions (CSV)</button>
    </div>
    <div class="rdempty hidden" id="mistakeEmpty">
      <div class="rdempty-ic">🎯</div>
      <b>Nothing to practise</b>
      <span>Questions you answer wrong in an exam land here, ready to sit again.</span>
    </div>
  </div>
  <div id="paperScreen" class="screen hidden">""")
sub("""const SCREENS=['redoScreen',""","""const SCREENS=['mistakeScreen','redoScreen',""")
sub("""  const family={stuReadScreen:'stuPickScreen', simRevScreen:'paperScreen',
                simDoneScreen:'paperScreen'};""","""  const family={stuReadScreen:'stuPickScreen', simRevScreen:'paperScreen',
                simDoneScreen:'paperScreen', mistakeScreen:'redoScreen'};""")
sub("""$('redoCsvAll').onclick=()=>histCsvAll();""","""$('redoCsvAll').onclick=()=>histCsvAll();
$('redoMkGo').onclick=()=>openMistakes();
$('mistakeBack').onclick=()=>{ renderRedoScreen(); go('redoScreen'); syncNav(); };
$('mistakeStart').onclick=()=>mistakeAsk($('mistakeStart'));
$('mistakeCsv').onclick=()=>mistakeCsv();""")

sub(""".rdtools{display:flex;justify-content:flex-end;margin:2px 0 8px}""",""".rdtools{display:flex;justify-content:flex-end;margin:2px 0 8px}
/* the mistakes exam: its card on the Redo page, and its screen */
.mkentry{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  border-color:color-mix(in srgb, var(--gold) 38%, var(--line));background:color-mix(in srgb, var(--gold) 6%, var(--panel))}
.mkentry.hidden{display:none}
.mkentry-in{display:flex;align-items:center;gap:11px;flex:1;min-width:180px}
.mkic{font-size:24px;flex:none}
.mkentry-t{display:flex;flex-direction:column;gap:2px;min-width:0}
.mkentry-t b{font-size:14px}
.mkentry-t span{font-size:11.5px;color:var(--dim)}
#mistakeScreen .card{margin-top:10px}
#mistakeScreen .card.hidden,#mistakeScreen .statstrip.hidden,.mkacts.hidden{display:none}
.mkrow.first .bsnm{color:var(--gold)}
.mkmeta{display:flex;align-items:center;justify-content:space-between;gap:10px}
.mkstudy{flex:none;font-size:11.5px;font-weight:650;min-height:32px;padding:5px 11px;border-radius:9px;
  background:transparent;border:1px solid var(--line2);color:var(--cyan)}
.mkstudy:hover{border-color:var(--cyan)}
.mkacts{display:flex;flex-direction:column;align-items:center;gap:8px;margin:14px auto 4px;max-width:var(--colw)}
.mkacts .btn.wide{width:100%}""")

sub("""    histCsvLines, histCsvName, histCsv, histCsvAll, HIST_CSV_HEAD,""",
"""    histCsvLines, histCsvName, histCsv, histCsvAll, HIST_CSV_HEAD,
    examLabel, mistakeSet, mistakeStats, renderMistakes, openMistakes, startMistakes, mistakeAsk, mistakeCsv, fmtMins,""")

PAGE.write_text(s, encoding="utf-8"); print("mistakes exam: set, stats screen, timed exam, kind carried everywhere")
