#!/usr/bin/env python3
"""Exam Redo: its own tab, its own screen, and its own table in the database.

The list of exams lived on the Exam screen and travelled inside the profile. It now has:

  - A tab in the bottom bar, "Redo", and a screen for it: a summary (exams kept, best, average,
    passed), the score of each recent exam as a small chart against the 720 line, and a card per
    exam — its score, right/total, date, how often it has been redone, a bar against the pass
    mark, and Redo (or Continue, if a redo of it is open).
  - Its own database table, exam_history: one row per exam (supabase_exam_history.sql). Every
    change to an exam — submitting it, an edit in a redo, finishing it later — upserts that one
    row within a second and a half. Every sync pulls the table and keeps the newer copy of each
    exam, and opening the tab pulls it too, so the other device's changes show up. The profile
    still carries a copy, so nothing is lost if the table has not been created yet; the screen
    says which of the two it is syncing through.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new,count=1):
    global s
    n=s.count(old); assert n>=count, "NOT FOUND (%d): %s"%(n,old[:90]); s=s.replace(old,new,count)

# ---- the tab --------------------------------------------------------------------------------
sub("""    <button class="navbtn" id="navExam"><span class="ic">🎓</span>Exam</button>""",
"""    <button class="navbtn" id="navExam"><span class="ic">🎓</span>Exam</button>
    <button class="navbtn" id="navRedo"><span class="ic">✎</span>Redo</button>""")
sub("""const NAVS=[['navHome','homeScreen'],['navPlay','stuPickScreen'],['navExam','paperScreen'],""",
    """const NAVS=[['navHome','homeScreen'],['navPlay','stuPickScreen'],['navExam','paperScreen'],['navRedo','redoScreen'],""")
sub("""$('navExam').onclick=()=>{ if(L) learnLeave(true);
  renderPapers(); go('paperScreen'); syncNav(); };""",
"""$('navExam').onclick=()=>{ if(L) learnLeave(true);
  renderPapers(); go('paperScreen'); syncNav(); };
$('navRedo').onclick=()=>{ if(L) learnLeave(true);
  renderRedoScreen(); go('redoScreen'); syncNav();
  histCloudPull().then(ch=>{ if(route==='redoScreen') renderRedoScreen(); }); };""")
sub("""const SCREENS=['homeScreen',""", """const SCREENS=['redoScreen','homeScreen',""")
sub(""".navbtn .ic{font-size:19px;line-height:1}""",
    """.navbtn .ic{font-size:19px;line-height:1}
@media (max-width:360px){ .navbtn{font-size:8.5px;padding:7px 0 5px} .navbtn .ic{font-size:17px} }""")

# ---- the screen ---------------------------------------------------------------------------------
sub("""  <div id="paperScreen" class="screen hidden">""",
"""  <div id="redoScreen" class="screen hidden">
    <div style="text-align:center;margin-bottom:12px">
      <h2 class="head">✎ Exam Redo</h2>
      <p class="sub">Every exam you have submitted, kept with every answer. Redo any of them with no timer — change answers and watch the score move.</p>
      <div class="rdsync" id="redoSync"></div>
    </div>
    <div class="statstrip" id="redoStats"></div>
    <div class="card rdchart hidden" id="redoChartBox">
      <div class="rdcharthead"><span>Recent scores</span><span class="rdpass">720 to pass</span></div>
      <div class="rdchart-in" id="redoChart"></div>
    </div>
    <div class="list" id="redoList"></div>
    <div class="rdempty hidden" id="redoEmpty">
      <div class="rdempty-ic">📝</div>
      <b>No exams here yet</b>
      <span>Submit an exam from the Exam tab and it appears here, ready to redo.</span>
      <button class="btn" id="redoGoExam" style="margin-top:12px">Go to exams ›</button>
    </div>
  </div>
  <div id="paperScreen" class="screen hidden">""")

sub(""".histrow .ds{white-space:normal}""",
""".histrow .ds{white-space:normal}
/* ---- Exam Redo ---- */
.rdsync{display:inline-flex;align-items:center;gap:6px;margin-top:8px;padding:4px 10px;border-radius:99px;
  font-size:10.5px;font-family:var(--mono);color:var(--dim);border:1px solid var(--line);background:var(--surface)}
.rdsync.ok{color:var(--lime);border-color:color-mix(in srgb, var(--lime) 35%, var(--line))}
.rdsync.warn{color:var(--gold);border-color:color-mix(in srgb, var(--gold) 35%, var(--line))}
.rdchart{padding:12px 12px 8px;margin-bottom:14px}
.rdcharthead{display:flex;justify-content:space-between;font-size:10px;font-family:var(--mono);
  color:var(--dim);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}
.rdpass{color:var(--gold)}
.rdchart-in{position:relative;height:84px;display:flex;align-items:flex-end;gap:5px}
.rdchart-in .pl{position:absolute;left:0;right:0;border-top:1px dashed color-mix(in srgb, var(--gold) 70%, transparent);pointer-events:none}
.rdchart-in .b{flex:1;min-width:0;border-radius:4px 4px 0 0;position:relative;
  background:linear-gradient(180deg,var(--red),color-mix(in srgb, var(--red) 40%, transparent))}
.rdchart-in .b.pass{background:linear-gradient(180deg,var(--lime),color-mix(in srgb, var(--lime) 40%, transparent))}
.rdcard{display:flex;gap:12px;align-items:center;padding:12px;border-radius:15px;
  background:var(--surface);border:1px solid var(--line);margin-bottom:10px}
.rdcard.pass{border-color:color-mix(in srgb, var(--lime) 30%, var(--line))}
.rdscore{flex:none;width:62px;text-align:center}
.rdscore b{display:block;font-family:var(--mono);font-size:21px;font-weight:700;color:var(--red);line-height:1.1}
.rdcard.pass .rdscore b{color:var(--lime)}
.rdscore span{font-size:9.5px;color:var(--dim);font-family:var(--mono)}
.rdbody{flex:1;min-width:0}
.rdbody .nm{font-weight:650;font-size:13.5px}
.rdbody .ds{font-size:11px;color:var(--dim);margin-top:2px;white-space:normal}
.rdbar{position:relative;height:6px;border-radius:3px;background:rgba(255,255,255,.07);margin-top:7px;overflow:hidden}
.rdbar i{display:block;height:100%;border-radius:3px;background:var(--red)}
.rdcard.pass .rdbar i{background:var(--lime)}
.rdbar::after{content:'';position:absolute;top:0;bottom:0;left:69%;width:2px;background:var(--gold)}
.rdcard .buy{flex:none}
.rdempty{display:flex;flex-direction:column;align-items:center;text-align:center;gap:4px;padding:34px 18px;
  color:var(--dim);font-size:12.5px}
.rdempty.hidden{display:none}
.rdempty-ic{font-size:34px;margin-bottom:4px}
.rdempty b{color:var(--txt);font-size:14px}""")

# ---- render ------------------------------------------------------------------------------------------
sub("""function renderHist(){""",
"""function renderRedoScreen(){
  const L=$('redoList'); if(!L) return;
  histPrune();
  const h=P.examHist||{};
  const ks=Object.keys(h).filter(k=>h[k].qs.every(i=>!!QS[i]))
    .sort((a,b)=>(Number(h[b].d0)||0)-(Number(h[a].d0)||0));
  // sync status: which way this list reaches the other device
  const st=$('redoSync');
  if(st){
    st.className='rdsync';
    if(!(typeof sbUser!=='undefined'&&sbUser)){ st.textContent='\\u25cb Saved on this device \\u2014 sign in to sync'; }
    else if(histTable==='missing'){ st.classList.add('warn'); st.textContent='\\u25d0 Syncing inside your profile \\u2014 run supabase_exam_history.sql for its own table'; }
    else { st.classList.add('ok'); st.textContent='\\u25cf Synced to your account'+(histLastSync?' \\u00b7 '+new Date(histLastSync).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}):''); }
  }
  $('redoEmpty').classList.toggle('hidden',!!ks.length);
  const scs=ks.map(k=>Number(h[k].sc)||100);
  const passN=scs.filter(x=>x>=SAA_PASS).length;
  $('redoStats').innerHTML=ks.length?
    '<div class="stat"><b>'+ks.length+'</b><span>exams kept</span></div>'+
    '<div class="stat"><b>'+Math.max(...scs)+'</b><span>best</span></div>'+
    '<div class="stat"><b>'+Math.round(scs.reduce((a,b)=>a+b,0)/scs.length)+'</b><span>average</span></div>'+
    '<div class="stat"><b>'+passN+'</b><span>passed</span></div>':'';
  // the last twelve, oldest first, against the pass line
  const cb=$('redoChartBox'), ch=$('redoChart');
  cb.classList.toggle('hidden',ks.length<2);
  if(ks.length>=2){
    const last=ks.slice(0,12).reverse();
    const y=v=>Math.max(4,Math.round((v-100)/900*100));
    ch.innerHTML='<div class="pl" style="bottom:'+y(SAA_PASS)+'%"></div>'+last.map(k=>{
      const v=Number(h[k].sc)||100;
      return '<div class="b'+(v>=SAA_PASS?' pass':'')+'" style="height:'+y(v)+'%" title="'+
        (h[k].paper?'Exam '+(Number(h[k].paper)|0):'Mock')+': '+v+'"></div>'; }).join('');
  }
  L.innerHTML='';
  const open=simSaved();
  ks.forEach(k=>{
    const r=h[k], v=Number(r.sc)||100, pass=v>=SAA_PASS;
    const live=!!(open&&open.mode==='redo'&&open.hid===k);
    const card=document.createElement('div'); card.className='rdcard'+(pass?' pass':'');
    card.innerHTML='<div class="rdscore"><b></b><span>/ 1000</span></div>'+
      '<div class="rdbody"><div class="nm"></div><div class="ds"></div><div class="rdbar"><i></i></div></div>';
    card.querySelector('.rdscore b').textContent=v;
    card.querySelector('.nm').textContent=(r.paper?'Exam '+(Number(r.paper)|0):'Mock exam')+(pass?' \\u00b7 pass':'');
    card.querySelector('.ds').textContent=(Number(r.c)|0)+'/'+(Number(r.n)|0)+' right \\u00b7 '+(r.d||'')+
      (r.mode==='practice'?' \\u00b7 practice':'')+(r.redos?' \\u00b7 redone '+plural(Number(r.redos)|0,'time'):'');
    card.querySelector('.rdbar i').style.width=pctW(Math.round((v-100)/900*100));
    const b=document.createElement('button'); b.className='buy';
    b.textContent=live?'\\u25b6 Continue':'\\u25b6 Redo';
    b.setAttribute('aria-label',(live?'Continue the redo of ':'Redo ')+card.querySelector('.nm').textContent+', '+v+' out of 1000');
    b.onclick=()=>live?(simSaved()&&simResume()):histOpen(k,b);
    card.appendChild(b); L.appendChild(card);
  });
}
function renderHist(){""")
sub("""$('simCsv').onclick=exportLastExam;""",
"""$('simCsv').onclick=exportLastExam;
$('redoGoExam').onclick=()=>{ renderPapers(); go('paperScreen'); syncNav(); };""")

# The exam list keeps a pointer rather than a second copy of the list
sub("""    <div id="histBox" class="hidden">
      <div class="sechead">Exam history</div>
      <p class="sub" style="margin:-4px 0 8px">Every exam you have submitted. Redo any of them with no timer — change answers and watch the score move.</p>
      <div class="list" id="histList"></div>
    </div>""",
"""    <div id="histBox" class="hidden">
      <div class="sechead">Exam history</div>
      <button class="exresume" id="histGoRedo">✎ Your submitted exams are in the Redo tab ›</button>
      <div class="list hidden" id="histList"></div>
    </div>""")
sub("""$('redoGoExam').onclick=""", """$('histGoRedo').onclick=()=>{ renderRedoScreen(); go('redoScreen'); syncNav(); };
$('redoGoExam').onclick=""")
# the redo closes onto the Redo screen
sub("""  sim=null; saveProfile(); renderClock();
  renderPapers(); go('paperScreen');
  toast('\\u2714 '+(e.paper?'Exam '+e.paper:'Mock exam')+' saved""",
"""  sim=null; saveProfile(); renderClock();
  renderRedoScreen(); go('redoScreen'); syncNav();
  toast('\\u2714 '+(e.paper?'Exam '+e.paper:'Mock exam')+' saved""")

# ---- the table --------------------------------------------------------------------------------------
sub("""// ---------- exam history ----------""",
"""// ---------- exam history in its own table (supabase_exam_history.sql) ----------
// One row per exam, upserted within a second and a half of any change to it. Without the table
// (it has not been created yet) the profile copy still syncs, and the Redo screen says so.
let histTable='unknown', histLastSync=0, histTimer=null;
const histDirty=new Set();
function histMissing(e){
  const m=String(e&&e.message||'');
  return !!e&&(e.code==='42P01'||e.code==='PGRST205'||(/exam_history/.test(m)&&/does not exist|schema cache|could not find/i.test(m)));
}
function histCloudQueue(hid){
  if(!hid) return;
  histDirty.add(hid);
  if(histTimer) clearTimeout(histTimer);
  histTimer=setTimeout(histCloudPush,1500);
}
async function histCloudPush(){
  histTimer=null;
  if(typeof sb==='undefined'||!sb||!sbUser||histTable==='missing'||!histDirty.size) return;
  const rows=[...histDirty].map(h=>(P.examHist||{})[h]).filter(e=>e&&e.hid)
    .map(e=>({user_id:sbUser.id, hid:String(e.hid), exam:e}));
  histDirty.clear();
  if(!rows.length) return;
  try{
    const {error}=await sb.from('exam_history').upsert(rows);
    if(error){ if(histMissing(error)) histTable='missing'; else rows.forEach(r=>histDirty.add(r.hid)); }
    else { histTable='ok'; histLastSync=Date.now(); }
  }catch(e){ rows.forEach(r=>histDirty.add(r.hid)); }
  if(route==='redoScreen') renderRedoScreen();
}
async function histCloudPull(){
  if(typeof sb==='undefined'||!sb||!sbUser||histTable==='missing') return false;
  let data=null;
  try{
    const r=await sb.from('exam_history').select('hid,exam');
    if(r.error){ if(histMissing(r.error)) histTable='missing'; return false; }
    data=r.data||[];
  }catch(e){ return false; }
  histTable='ok';
  P.examHist=P.examHist||{};
  const seen={}; let changed=false;
  data.forEach(row=>{
    const e=row.exam; if(!e||!Array.isArray(e.qs)) return;
    seen[row.hid]=Number(e.at)||0;
    const mine=P.examHist[row.hid];
    if(!mine||(Number(e.at)||0)>(Number(mine.at)||0)){ P.examHist[row.hid]=e; changed=true; }
  });
  // anything this device has that the table lacks, or has older, goes up
  Object.keys(P.examHist).forEach(h=>{ if(!(h in seen)||(Number(P.examHist[h].at)||0)>seen[h]) histDirty.add(h); });
  if(changed){ normaliseProfile(P); histPrune(); saveProfile(); }
  histLastSync=Date.now();
  if(histDirty.size) histCloudPush();
  return changed;
}
// ---------- exam history ----------""")
sub("""  if(sim.mode==='redo') sim.redoCounted=1;
  histPrune();""" if "sim.redoCounted=1" in s else """    redos:prev.redos||0}, sc);
  histPrune();""",
"""    redos:prev.redos||0}, sc);
  histPrune();
  histCloudQueue(hid);""")
# a redo starting also counts, and goes up
sub("""    r.redos=(Number(r.redos)||0)+1; r.at=Date.now();""",
    """    r.redos=(Number(r.redos)||0)+1; r.at=Date.now(); histCloudQueue(hid);""")
# every sync pulls the table too
sub("""      // did the merge just hand our exam to the other device?
      if(simOwnerCheck()) { syncing=false; renderAuth(); return; }""",
"""      // did the merge just hand our exam to the other device?
      if(simOwnerCheck()) { syncing=false; renderAuth(); return; }
      await histCloudPull();
      if(route==='redoScreen') renderRedoScreen();""")

sub("    isPractice, brkOpen, brkElapsed,",
    "    isPractice, brkOpen, brkElapsed, renderRedoScreen, histCloudPull, histCloudPush, histCloudQueue, get histTable(){return histTable;}, set histTable(v){histTable=v;},")
PAGE.write_text(s, encoding="utf-8"); print("redo tab and table in")
