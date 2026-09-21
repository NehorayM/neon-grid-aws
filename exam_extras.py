#!/usr/bin/env python3
"""Four changes to the exam experience, plus taking the price tags off.

  1. A paper you leave is kept. Question, answers, flags and the remaining time
     are saved, and the Practice Exams screen offers to resume it. The clock
     stops while you are away rather than running down in the background.
  2. The question can be read aloud (Web Speech), with an auto-read toggle that
     is remembered.
  3. Exams 1 to 5 show a briefing above each question: the services it turns on,
     the ones it name-drops as distractors, and how the exam phrases the ask.
  4. Nothing costs coins any more. Coins still accumulate as a score, but no
     study feature, lifeline, upgrade, theme or mini-game is behind a price.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import sys

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:100])
    s = s.replace(old, new, count)


# ============================================================ 1. styles
sub("/* ---------- study mode ---------- */",
"""/* ---------- exam briefing, resume and read-aloud ---------- */
.exbrief{border:1px solid var(--line);background:var(--surface);border-radius:12px;
  margin-bottom:12px;overflow:hidden}
.exbrief > summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:9px;
  padding:12px 14px;font-size:12.5px;font-weight:650;color:var(--txt)}
.exbrief > summary::-webkit-details-marker{display:none}
.exbrief > summary .chev{margin-left:auto;color:var(--dim);font-size:11px;transition:.15s}
.exbrief[open] > summary .chev{transform:rotate(90deg)}
.exbrief .bb{padding:0 14px 14px}
.exbrief .lbl{font-family:var(--mono);font-size:9.5px;letter-spacing:.8px;text-transform:uppercase;
  color:var(--dim);margin:10px 0 6px}
.exbrief .lbl:first-child{margin-top:0}
.exbrief .tip{font-size:12px;line-height:1.5;color:var(--txt);opacity:.9;margin-bottom:5px}
.exbrief .tip.warn{color:var(--gold)}
.exresume{position:relative;display:flex;align-items:center;gap:13px;width:100%;
  padding:15px 16px;border-radius:12px;background:var(--surface2);border:1px solid var(--line2);
  text-align:left;margin-bottom:14px;overflow:hidden}
.exresume::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--gold)}
.exresume .rem{font-size:20px;flex:none}
.exresume .rnm{font-size:13.5px;font-weight:650}
.exresume .rds{font-size:11.5px;color:var(--dim);margin-top:3px}
.simbtn.tts.on{border-color:var(--cyan);color:var(--cyan)}

/* ---------- study mode ---------- */""")


# ================================================= 2. markup: briefing slot
sub("""      <div class="qcard">
        <div class="qtext" id="qText"></div>""",
    """      <details class="exbrief hidden" id="exBrief"><summary><span>\U0001f4d8</span>
        <span id="exBriefTitle">Before you answer</span><span class="chev">\u203a</span></summary>
        <div class="bb" id="exBriefBody"></div></details>
      <div class="qcard">
        <div class="qtext" id="qText"></div>""")

# a read-aloud button next to the flag, inside the exam bar
sub("""        <button class="simbtn" id="simFlag">⚑ Flag</button>""",
    """        <button class="simbtn" id="simFlag">⚑ Flag</button>
        <button class="simbtn tts" id="simTts" title="Read the question aloud">\U0001f50a Read</button>""")


# =========================================== 3. engine: resume, TTS, briefing
sub("""function paperRec(n){ return (P.papers||{})[n]||null; }""",
r"""function paperRec(n){ return (P.papers||{})[n]||null; }

// ---------- a paper you walk away from is kept ----------
// The clock is stored as time remaining, not as a deadline: an exam you come back
// to tomorrow resumes where it stopped instead of having expired overnight.
function simPersist(){
  if(!sim||!sim.running) return;
  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag,
             left:Math.max(0,sim.endAt-Date.now()), mins:sim.mins||SIM_MIN, at:Date.now()};
  saveProfile();
}
function simClearSave(){ if(P.simSave){ delete P.simSave; saveProfile(); } }
function simSaved(){
  const sv=P.simSave;
  if(!sv||!sv.qs||!sv.qs.length||sv.left<=0) return null;
  if(sv.qs.some(i=>!QS[i])) return null;          // the bank changed under it
  return sv;
}
function simResume(){
  const sv=simSaved(); if(!sv){ toast('Nothing to resume'); return; }
  ensureAudio(); exitStudyMode();
  reviewMode=false; markMode=false; mock=null;
  sim={qs:sv.qs, i:Math.min(sv.i||0,sv.qs.length-1), ans:sv.ans||{}, flag:sv.flag||{},
       running:true, paper:sv.paper||0, mins:sv.mins,
       startAt:Date.now()-((sv.mins*60000)-sv.left), endAt:Date.now()+sv.left};
  renderClock(); simLoad();
}
function simAnsweredIn(sv){ return Object.keys(sv.ans||{}).filter(k=>(sv.ans[k]||[]).length).length; }

// ---------- read the question aloud ----------
const ttsOk=()=>typeof window!=='undefined'&&'speechSynthesis' in window;
function ttsStop(){ try{ if(ttsOk()) window.speechSynthesis.cancel(); }catch(e){} }
function ttsText(q,i,total){
  return 'Question '+(i+1)+' of '+total+'. '+q.q+' '+
    q.o.map(o=>'Option '+o[0]+'. '+o[1]+'.').join(' ');
}
function ttsSpeak(text){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return false; }
  try{
    window.speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(text);
    u.rate=P.ttsRate||1; u.lang='en-US';
    const v=(window.speechSynthesis.getVoices()||[]).find(x=>/^en/i.test(x.lang));
    if(v) u.voice=v;
    window.speechSynthesis.speak(u);
    // a browser with no voices installed accepts speak() and stays silent, so say so
    // rather than leaving the reader wondering whether the tap registered
    if(!TEST) setTimeout(()=>{
      try{
        const ss=window.speechSynthesis;
        if(!ss.speaking&&!ss.pending&&!(ss.getVoices()||[]).length)
          toast('No speech voices are installed in this browser');
      }catch(e){}
    },400);
    return true;
  }catch(e){ return false; }
}
function simSpeak(){
  if(!sim) return false;
  const q=QS[sim.qs[sim.i]];
  return ttsSpeak(ttsText(q,sim.i,sim.qs.length));
}
function ttsToggle(){
  // one tap reads this question; a second tap turns auto-read on for the rest
  if(!ttsOk()){ toast('This browser cannot read aloud'); return; }
  if(P.ttsAuto){ P.ttsAuto=0; ttsStop(); toast('\U0001f507 Auto-read off'); }
  else if(window.speechSynthesis.speaking){ P.ttsAuto=1; toast('🔊 Auto-read on'); }
  else { simSpeak(); }
  saveProfile(); renderTtsBtn();
}
function renderTtsBtn(){
  const b=$('simTts'); if(!b) return;
  b.classList.toggle('on',!!P.ttsAuto);
  b.textContent=P.ttsAuto?'🔊 Auto':'🔊 Read';
}

// ---------- the first five papers come with a briefing ----------
const BRIEF_PAPERS=5;
function renderExamBrief(qi){
  const box=$('exBrief');
  if(!box) return;
  if(!sim||!sim.paper||sim.paper>BRIEF_PAPERS){ box.classList.add('hidden'); return; }
  const b=buildBriefing(qi);
  box.classList.remove('hidden');
  box.open=P.briefOpen!==0;
  $('exBriefTitle').textContent='Before you answer — '+b.sector;
  const body=$('exBriefBody'); body.innerHTML='';
  const label=t=>{ const d=document.createElement('div'); d.className='lbl'; d.textContent=t;
    body.appendChild(d); };
  const card=(term,def,cls)=>{ const d=document.createElement('div');
    d.className='concept'+(cls?' '+cls:'');
    d.innerHTML='<b>'+esc(term.toUpperCase())+'</b><span>'+esc(def)+'</span>';
    body.appendChild(d); };
  // a briefing longer than the question defeats the point; cap it
  if(b.concepts.length){ label('What this question turns on');
    b.concepts.slice(0,4).forEach(k=>card(k,CODEX[k])); }
  else { label('How to read this one');
    card('scenario','No single service decides it. Read the requirement twice, then drop every option that adds operational overhead without meeting it.'); }
  if(b.distractors.length){ label('Also named — know the difference');
    b.distractors.slice(0,3).forEach(k=>card(k,CODEX[k],'alt')); }
  if(b.tips.length){ label('How the exam phrases it');
    b.tips.forEach(t=>{ const d=document.createElement('div'); d.className='tip';
      d.textContent='\U0001f4a1 '+t; body.appendChild(d); }); }
  if(b.multi){ const d=document.createElement('div'); d.className='tip warn';
    d.textContent='⚠ More than one answer is required here.'; body.appendChild(d); }
}""")

# --- hook the three into the exam lifecycle -------------------------------
sub("""  $('simFlag').textContent=sim.flag[sim.i]?'\U0001f6a9 Flagged':'⚑ Flag';
  $('simFlag').classList.toggle('on',!!sim.flag[sim.i]);
  $('simPrev').disabled=sim.i===0;""",
"""  $('simFlag').textContent=sim.flag[sim.i]?'\U0001f6a9 Flagged':'⚑ Flag';
  $('simFlag').classList.toggle('on',!!sim.flag[sim.i]);
  renderExamBrief(qi);
  renderTtsBtn();
  ttsStop();
  if(P.ttsAuto) simSpeak();
  simPersist();
  $('simPrev').disabled=sim.i===0;""")

sub("""  sim.ans[sim.i]=[...cur];
  chosen.clear(); cur.forEach(l=>chosen.add(l));""",
    """  sim.ans[sim.i]=[...cur];
  simPersist();
  chosen.clear(); cur.forEach(l=>chosen.add(l));""")

sub("""  sim.flag[sim.i]=!sim.flag[sim.i];
  $('simFlag').textContent=""",
    """  sim.flag[sim.i]=!sim.flag[sim.i];
  simPersist();
  $('simFlag').textContent=""")

sub("""  sim.running=false;
  const paper=sim.paper||0;""",
    """  sim.running=false;
  ttsStop(); simClearSave();
  const paper=sim.paper||0;""")

sub("""function simAbandon(){
  if(!sim) return;
  sim=null; renderClock();""",
"""function simAbandon(){
  if(!sim) return;
  simPersist();                 // keep it: the Practice Exams screen offers it back
  ttsStop();
  sim=null; renderClock();""")

# the briefing and the read button belong to exams only
sub("""  $('hintBtn').style.display='';
  $('lifeFifty').disabled=!diff().lifelines;""",
    """  $('hintBtn').style.display='';
  $('exBrief').classList.add('hidden');
  ttsStop();
  $('lifeFifty').disabled=!diff().lifelines;""")

# --- the resume card on the Practice Exams screen --------------------------
sub("""    <div class="statstrip" id="paperStats" style="margin-bottom:14px"></div>""",
    """    <button class="exresume hidden" id="exResume"></button>
    <div class="statstrip" id="paperStats" style="margin-bottom:14px"></div>""")

sub("""  $('paperStats').innerHTML=
    '<div class="stat"><b>'+done+' / '+PAPER_COUNT+'</b><span>Attempted</span></div>'+""",
"""  const sv=simSaved(), rbtn=$('exResume');
  if(sv&&rbtn){
    rbtn.classList.remove('hidden');
    rbtn.innerHTML='<span class="rem">⏸</span><span style="flex:1;min-width:0">'+
      '<div class="rnm">Resume '+(sv.paper?'Exam '+sv.paper:'the mock exam')+'</div>'+
      '<div class="rds">Question '+((sv.i||0)+1)+' of '+sv.qs.length+' · '+
      simAnsweredIn(sv)+' answered · '+fmtClock(sv.left)+' left</div></span>'+
      '<span class="buy">Resume</span>';
    rbtn.onclick=simResume;
  } else if(rbtn) rbtn.classList.add('hidden');
  $('paperStats').innerHTML=
    '<div class="stat"><b>'+done+' / '+PAPER_COUNT+'</b><span>Attempted</span></div>'+""")

# starting a fresh paper replaces any saved one
sub("""  const qs=paperQs(n);
  sim={qs,i:0,ans:{},flag:{},running:true,paper:n,mins:PAPER_MIN,""",
    """  const qs=paperQs(n);
  simClearSave();
  sim={qs,i:0,ans:{},flag:{},running:true,paper:n,mins:PAPER_MIN,""")

sub("""$('simCsv').onclick=exportLastExam;""",
    """$('simCsv').onclick=exportLastExam;
$('simTts').onclick=ttsToggle;
$('exBrief').ontoggle=()=>{ P.briefOpen=$('exBrief').open?1:0; saveProfile(); };""")


# =============================================== 4. everything is free now
sub("const STUDY_COST=15;", "const STUDY_COST=0;        // study cards are free")
sub("""    if(P.coins<STUDY_COST){ toast('Need '+STUDY_COST+' coins (or buy Codex Access)'); return; }
    addCoins(-STUDY_COST);""", "")
sub("function unlockCost(){ return Math.max(15,(chargeNeed()-(P.charge||0))*25); }",
    "function unlockCost(){ return 0; }        // unlocking a reward round is free")
sub("""  if(P.coins<cost){ toast('Need '+cost+' coins'); return; }
  addCoins(-cost); P.charge=chargeNeed(); saveProfile();""",
    """  P.charge=chargeNeed(); saveProfile();""")
sub("""  else { btn.textContent='Unlock '+unlockCost()+'\U0001fa99'; btn.disabled=P.coins<unlockCost(); }""",
    """  else { btn.textContent='Unlock now'; btn.disabled=false; }""")
sub("""  if(P.coins<30){ toast('Need 30 coins'); return; }""", "")
sub("""  addCoins(-30); $('lifeFifty').disabled=true; sfx.coin();""",
    """  $('lifeFifty').disabled=true; sfx.tap();""")
sub("""  if(P.coins<20){ toast('Need 20 coins'); return; }
  addCoins(-20); P.seen[curQ]=1; saveProfile(); nextQuestion();""",
    """  P.seen[curQ]=1; saveProfile(); nextQuestion();""")
sub("""  const cost=P.upgrades.autoFifty?10:30;
  if(answeredThis||curQ<0||!QS[curQ]) return;
  if(P.coins<cost){ toast('Need '+cost+' coins'); return; }""",
    """  if(answeredThis||curQ<0||!QS[curQ]) return;""")
sub("""  addCoins(-cost); $('lifeFifty').disabled=true; sfx.coin();
};""", """  $('lifeFifty').disabled=true; sfx.tap();
};""")
sub("""  if(P.coins<it.cost) return;
  addCoins(-it.cost);""", "")
sub("""    const b=document.createElement('button'); b.className='buy'; b.textContent=it.cost+' \U0001fa99';
    b.disabled=P.coins<it.cost; b.onclick=()=>buyCons(it);""",
    """    const b=document.createElement('button'); b.className='buy'; b.textContent='Take';
    b.onclick=()=>buyCons(it);""")
sub("""      const b=document.createElement('button'); b.className='buy'; b.textContent=it.cost+' \U0001fa99';
      b.disabled=P.coins<it.cost;
      b.onclick=()=>{ if(P.coins<it.cost) return; addCoins(-it.cost); P.upgrades[it.id]=1;""",
    """      const b=document.createElement('button'); b.className='buy'; b.textContent='Unlock';
      b.onclick=()=>{ P.upgrades[it.id]=1;""")
sub("""    b.textContent=PICK_COST+' \U0001fa99'; b.disabled=P.coins<PICK_COST;
    b.onclick=()=>{ if(P.coins<PICK_COST) return; addCoins(-PICK_COST); saveProfile(); launchGame(g.id); };""",
    """    b.textContent='Play'; b.disabled=false;
    b.onclick=()=>{ saveProfile(); launchGame(g.id); };""")
sub("""  if(P.coins<t.cost){ toast('Need '+t.cost+' coins'); return; }
  addCoins(-t.cost);""", "")
sub("""    else { b.textContent=t.cost+' \U0001fa99'; b.disabled=P.coins<t.cost; }""",
    """    else { b.textContent='Use'; b.disabled=false; }""")
sub("""      <p class="sub">Spend coins earned from questions and mini-games.</p>""",
    """      <p class="sub">Everything here is free — coins are just your score now. Take what helps.</p>""")

# the test surface
sub("""    PAPER_LEN, PAPER_MIN, PAPER_COUNT, paperQs, startPaper, renderPapers, paperRec,""",
    """    PAPER_LEN, PAPER_MIN, PAPER_COUNT, paperQs, startPaper, renderPapers, paperRec,
    simPersist, simClearSave, simSaved, simResume, ttsOk, ttsStop, ttsText, ttsSpeak,
    simSpeak, ttsToggle, renderTtsBtn, renderExamBrief, BRIEF_PAPERS, buildBriefing,""")

sub("""function themeOwned(t){
  if(t.free) return true;
  if(t.earn) return !!t.earn();
  return (P.themes||[]).indexOf(t.id)>=0;
}""",
    """function themeOwned(t){
  // nothing is sold any more: a theme is either earned by playing, or simply yours
  if(t.earn) return !!t.earn();
  return true;
}""")

sub("""  $('lifeFifty').style.display=''; $('lifeSkip').style.display='';
  $('hintBtn').style.display='';
  go('homeScreen'); renderHome();
}""",
    """  $('lifeFifty').style.display=''; $('lifeSkip').style.display='';
  $('hintBtn').style.display='';
  // land where the saved run is offered back, not on the home screen
  if(paper){ renderPapers(); go('paperScreen'); }
  else { go('homeScreen'); renderHome(); }
  syncNav();
}""")
sub("""  simPersist();                 // keep it: the Practice Exams screen offers it back""",
    """  const paper=sim.paper||0;\n  simPersist();                 // keep it: the Practice Exams screen offers it back""")

PAGE.write_text(s, encoding="utf-8")
print("exam extras applied · page %.2f MB" % (len(s) / 1e6))
sys.exit(0)
