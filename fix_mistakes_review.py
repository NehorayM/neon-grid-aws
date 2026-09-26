#!/usr/bin/env python3
"""Mistakes exam: what the four-lens review confirmed (16 of 19 findings, 7 distinct defects).

  1. Answers were dated by their exam's last edit. `at` is the version stamp of a whole kept
     exam, and a redo — even Save with nothing changed — sets it to now, so every untouched
     answer in an old exam became "the latest" and a real mistake could vanish (or a fixed one
     come back). histWrite now keeps `aat`: when each answer was given, carried over unchanged
     answers, now for changed ones. mistakeSet orders by that, falling back to the sitting time
     (d0), never to `at`.
  2. A mistakes exam scored as a full simulation: three questions right was a PASS that bumped
     sims/simsPassed/bestSim/exams/examsPassed, the exam quest, badges and the +90/+200 pass
     bonus. Those are for real exams. It still pays per right answer, and still feeds the study
     stats, spaced repetition and history — that is what it is for. The Redo page's best /
     average / passed and its chart leave mistakes exams out too.
  3. "From N exams" counted labels: three mock exams, or two sittings of Exam 4, were one exam.
     Sources are counted by entry now, and the CSV names a sitting with its date.
  4. Quit put a paused mistakes exam on Home, where nothing offers it back — and Home's Random
     mock exam cleared it for good (runDone) with no warning; that was already true of a paused
     mock. Quit now goes back to the mistakes screen, which offers Resume; starting a new one
     asks first. The random mock now puts an open exam on hold, as the mistakes exam does,
     instead of deleting it.
  5. armed() on the Start button left "Put … on hold and start?" on it after the picker was
     dismissed, and took its full width with the `wide` class. The label is rebuilt before the
     picker opens and the width no longer depends on that class.
  6. A cloud pull refreshed the Redo page but not the mistakes screen in front of you.
  7. Two labels still went by paper alone: the question header said EXAM SIM, and a kept
     mistakes exam's CSV was named skyforge-mock-….

Run once, after add_mistakes_exam.py; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

# ---- 1. when each answer was given
sub("""  const sc=histScoreOf(sim.qs,sim.ans||{});
  P.examHist[hid]=Object.assign({}, prev, {hid, paper:sim.paper||0, kind:sim.kind||prev.kind||'', qs:sim.qs.slice(),""",
"""  const sc=histScoreOf(sim.qs,sim.ans||{});
  // When each answer was given. `at` versions the whole entry and a redo moves it for every
  // answer in it, so it cannot say which of two exams answered a question last.
  const now=Date.now(), pa=prev.ans||{}, paat=prev.aat||{}, aat={};
  Object.keys(sim.ans||{}).forEach(i=>{
    const a=sim.ans[i]; if(!Array.isArray(a)||!a.length) return;
    const same=JSON.stringify(a)===JSON.stringify(pa[i]||null);
    aat[i]=same?(Number(paat[i])||Number(prev.d0)||now):now;
  });
  P.examHist[hid]=Object.assign({}, prev, {hid, paper:sim.paper||0, kind:sim.kind||prev.kind||'', aat, qs:sim.qs.slice(),""")
sub("""function mistakeSet(){
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
}""","""function mistakeSet(){
  const h=P.examHist||{}, last={}, src={}, names={}, everWrong=new Set();
  Object.keys(h).forEach(key=>{
    const e=h[key];
    if(!e||!Array.isArray(e.qs)) return;
    const id=e.hid||key, base=Number(e.d0)||Number(e.at)||0;
    // a sitting, told apart from another of the same exam by its date
    names[id]=examLabel(e)+(e.d?' ('+e.d+')':'');
    e.qs.forEach((qi,i)=>{
      const q=QS[qi]; if(!q) return;
      const a=(e.ans||{})[i]; if(!Array.isArray(a)||!a.length) return;
      const ok=a.length===q.a.length&&q.a.every(l=>a.includes(l));
      // when THIS answer was given — not when its exam was last saved (a redo re-saves them all)
      const t=Number((e.aat||{})[i])||base;
      if(!ok){ everWrong.add(qi); (src[qi]=src[qi]||new Set()).add(id); }
      if(!last[qi]||t>=last[qi].t) last[qi]={ok,t};
    });
  });
  const qs=[...everWrong].filter(qi=>last[qi]&&!last[qi].ok).sort((a,b)=>a-b);
  const ids=new Set(); qs.forEach(qi=>src[qi].forEach(x=>ids.add(x)));
  const from={}; qs.forEach(qi=>{ from[qi]=new Set([...src[qi]].map(x=>names[x])); });
  return {qs, fixed:everWrong.size-qs.length, exams:[...ids].map(x=>names[x]), from};
}""")

# ---- 2. a mistakes exam is not a full simulation
sub("""  const newPass=passed&&!(cont&&base.passed);""",
"""  // a mistakes exam is practice on questions already seen: its PASS is not an exam passed
  const real=kind!=='mistakes';
  const newPass=real&&passed&&!(cont&&base.passed);""")
sub("""  if(!cont){ P.sims=(P.sims||0)+1; }
  if(newPass) P.simsPassed=(P.simsPassed||0)+1;
  P.bestSim=Math.max(P.bestSim||0,pct);
  P.simLog=(P.simLog||[]);
  P.simLog.unshift({d:dayKey(),p:pct,sc:S.scaled,pass:passed?1:0,mins,pr:isPractice()?1:0,ct:cont?1:0,""",
"""  if(!cont&&real){ P.sims=(P.sims||0)+1; }
  if(newPass) P.simsPassed=(P.simsPassed||0)+1;
  if(real) P.bestSim=Math.max(P.bestSim||0,pct);
  P.simLog=(P.simLog||[]);
  P.simLog.unshift({d:dayKey(),p:pct,sc:S.scaled,pass:passed?1:0,mins,pr:isPractice()?1:0,ct:cont?1:0,k:real?'':'m',""")
sub("""  if(!cont) P.exams=(P.exams||0)+1;
  if(newPass) P.examsPassed=(P.examsPassed||0)+1;
  logExam(correct,len,passed);""","""  if(!cont&&real) P.exams=(P.exams||0)+1;
  if(newPass) P.examsPassed=(P.examsPassed||0)+1;
  if(real) logExam(correct,len,passed);""")
sub("""  const scs=ks.map(k=>Number(h[k].sc)||100);""",
"""  // the numbers are about exams: a mistakes exam re-sits questions already seen, so it is listed
  // but not counted in the best, the average or the passes
  const real=ks.filter(k=>h[k].kind!=='mistakes');
  const scs=(real.length?real:ks).map(k=>Number(h[k].sc)||100);""")
sub("""  const passN=scs.filter(x=>x>=SAA_PASS).length;""",
"""  const passN=real.map(k=>Number(h[k].sc)||100).filter(x=>x>=SAA_PASS).length;""")
sub("""    const last=ks.slice(0,12).reverse();""","""    const last=(real.length>=2?real:ks).slice(0,12).reverse();""")

# ---- 4. Quit returns to the mistakes screen, which offers Resume; the random mock holds, not deletes
sub("""function simAbandon(){
  if(!sim) return;
  const paper=sim.paper||0;""","""function simAbandon(){
  if(!sim) return;
  const paper=sim.paper||0, wasMistakes=sim.kind==='mistakes';""")
sub("""  if(paper){ renderPapers(); go('paperScreen'); }
  else { go('homeScreen'); renderHome(); }
  syncNav();
}""","""  if(wasMistakes){ openMistakes(); return; }
  if(paper){ renderPapers(); go('paperScreen'); }
  else { go('homeScreen'); renderHome(); }
  syncNav();
}""")
sub("""  const budget=simBudget(qs.length);
  simClearSave();
  sim={qs,i:0,ans:{},flag:{},rev:{},running:true,rid:newRid(),
       paper:0,mins:budget,qt:{},""","""  const budget=simBudget(qs.length);
  // An exam that was open is put on hold in Running exams, not deleted — clearing the save
  // marked it done everywhere, and a paused paper went with no warning.
  if(sim&&sim.running) simAbandon();
  if(P.simSave) runRecord(P.simSave);
  sim={qs,i:0,ans:{},flag:{},rev:{},running:true,rid:newRid(),
       paper:0,mins:budget,qt:{},""")
sub("""  saveProfile();
  renderClock();          // switch to the exam countdown immediately, not on the next tick
  simLoad();
}""","""  saveProfile();
  renderClock();          // switch to the exam countdown immediately, not on the next tick
  simLoad(); simClaim(); simPersist();
}""")
sub("""$('simOpen').onclick=()=>modeAsk('the mock exam',m=>startSim(m));""",
"""$('simOpen').onclick=()=>{
  const open=simSaved(), b=$('simOpen');
  const ask=()=>modeAsk('the mock exam',m=>startSim(m));
  if(open&&!b.dataset.armed){
    b.dataset.armed='1';
    const was=b.innerHTML;
    b.innerHTML='<span class="ic">\\u23f8</span><b>Put '+esc(examLabel(open,1))+' on hold?</b><span>Tap again to start a mock</span>';
    setTimeout(()=>{ if(b.dataset.armed){ b.dataset.armed=''; b.innerHTML=was; } },4000);
    b._was=was; return;
  }
  if(b.dataset.armed){ b.dataset.armed=''; if(b._was) b.innerHTML=b._was; }
  ask();
};""")
# the mistakes screen offers back the one that is open
sub("""    <div class="mkacts" id="mistakeActs">
      <button class="btn wide" id="mistakeStart">Start the mistakes exam ▸</button>""",
"""    <div class="mkacts" id="mistakeActs">
      <button class="btn wide hidden" id="mistakeResume">▶ Resume</button>
      <button class="btn wide" id="mistakeStart">Start the mistakes exam ▸</button>""")
sub("""  $('mistakeStart').textContent='Start the mistakes exam \\u2014 '+n+' questions \\u00b7 '+fmtMins(mins)+' \\u25b8';
  return ms;""","""  // one already under way comes first; a new one is the second choice
  const open=simSaved(), mine=!!(open&&open.kind==='mistakes');
  const rb=$('mistakeResume');
  rb.classList.toggle('hidden',!mine);
  if(mine) rb.textContent='\\u25b6 Resume the mistakes exam \\u2014 question '+((Number(open.i)||0)+1)+' of '+open.qs.length;
  const sbtn=$('mistakeStart');
  sbtn.dataset.armed='';
  sbtn.classList.toggle('ghost',mine);
  sbtn.textContent=(mine?'Start a new one \\u2014 ':'Start the mistakes exam \\u2014 ')+n+' questions \\u00b7 '+fmtMins(mins)+' \\u25b8';
  return ms;""")
sub("""$('mistakeStart').onclick=()=>mistakeAsk($('mistakeStart'));""",
"""$('mistakeStart').onclick=()=>mistakeAsk($('mistakeStart'));
$('mistakeResume').onclick=()=>{ const sv=simSaved(); if(sv) simResumeHere(sv); };""")

# ---- 5. the Start button's confirm does not stick, nor cost it its width
sub("""  const ask=()=>modeAsk('the mistakes exam',m=>startMistakes(m),""",
"""  const ask=()=>{ renderMistakes(); modeAsk('the mistakes exam',m=>startMistakes(m),""")
sub("""    'What changes is whether you can stop.');
  const open=simSaved();
  if(open&&btn){ armed(btn,'Put '+examLabel(open,1)+' on hold and start?',ask); return; }
  ask();""","""    'What changes is whether you can stop.'); };
  const open=simSaved();
  if(open&&btn){ armed(btn,'Put '+examLabel(open,1)+' on hold and start a new one?',ask); return; }
  ask();""")
sub(""".mkacts .btn.wide{width:100%}""",""".mkacts .btn.wide,#mistakeStart,#mistakeResume{width:100%}
#mistakeResume.hidden{display:none}""")

# ---- 6. a pull refreshes the mistakes screen as well as the Redo page
sub("""  if(!rows.length){ histTable='ok'; histLastSync=Date.now(); if(route==='redoScreen') renderRedoScreen(); return; }""",
"""  if(!rows.length){ histTable='ok'; histLastSync=Date.now(); histViewsRefresh(); return; }""")
sub("""  }catch(e){ rows.forEach(r=>histDirty.add(r.hid)); histRetry(); }
  if(route==='redoScreen') renderRedoScreen();
}""","""  }catch(e){ rows.forEach(r=>histDirty.add(r.hid)); histRetry(); }
  histViewsRefresh();
}
// the screens drawn from the kept exams, whichever is in front
function histViewsRefresh(){
  if(route==='redoScreen') renderRedoScreen();
  else if(route==='mistakeScreen') renderMistakes();
}""")
sub("""  histCloudPull().then(ch=>{ if(route==='redoScreen') renderRedoScreen(); }); };""",
"""  histCloudPull().then(ch=>histViewsRefresh()); };""")
sub("""      if(route==='redoScreen') renderRedoScreen();""","""      histViewsRefresh();""")

# ---- 7. the last two labels built from paper alone
sub("""  $('qSector').textContent=(sim.paper?('EXAM '+sim.paper):'EXAM SIM')+""",
"""  $('qSector').textContent=(sim.kind==='mistakes'?'MISTAKES EXAM':sim.paper?('EXAM '+sim.paper):'EXAM SIM')+""")
sub("""  return 'skyforge-'+(r.paper?'exam-'+(Number(r.paper)|0):'mock')+'-'+(Number(r.sc)||100)+'-'+""",
"""  return 'skyforge-'+(r.kind==='mistakes'?'mistakes':r.paper?'exam-'+(Number(r.paper)|0):'mock')+'-'+(Number(r.sc)||100)+'-'+""")

sub("""    examLabel, mistakeSet, mistakeStats,""","""    examLabel, mistakeSet, mistakeStats, histViewsRefresh,""")
PAGE.write_text(s, encoding="utf-8"); print("review fixes: answer times, not a full sim, exams by entry, resume, button, refresh, labels")

# ---- second pass: a REDO of a kept mistakes exam is a redo, not the mistakes exam in progress
s = PAGE.read_text(encoding="utf-8")
sub("""  const paper=sim.paper||0, wasMistakes=sim.kind==='mistakes';""",
"""  const paper=sim.paper||0, wasMistakes=sim.kind==='mistakes'&&sim.mode!=='redo';""")
sub("""  const open=simSaved(), mine=!!(open&&open.kind==='mistakes');""",
"""  const open=simSaved(), mine=!!(open&&open.kind==='mistakes'&&open.mode!=='redo');""")
PAGE.write_text(s, encoding="utf-8"); print("a redo of a mistakes exam stays a redo")
