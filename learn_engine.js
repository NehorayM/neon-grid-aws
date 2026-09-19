// ================= LEARN A SUBJECT =================
// A subject is taught in parts. Each part is a written module with tables, comparisons and
// callouts, followed by a few authored questions on *that part only*. Below the pass mark the
// part is read again and re-tested; above it, the next part unlocks. After the last part comes
// the full written summary of the subject, and then a ten-question exam drawn from authored
// questions tagged to the parts just studied — nothing off-topic can appear in it.
const LEARN=(()=>{ try{ return JSON.parse($('learndata').textContent).subjects||{}; }catch(e){ return {}; } })();
function learnData(sec){ return LEARN[String(sec)]||null; }
const LEARN_SECS=Object.keys(LEARN).map(Number).sort((a,b)=>a-b);
const LSIM_MIN=15;            // minutes for the ten-question exam
const LSIM_PASS=70;           // percent
const LPASS=0.75;             // fraction of a part's check questions needed to move on

// ---------- content blocks ----------
function lbList(items,tag){ return '<'+tag+'>'+items.map(i=>'<li>'+mdInline(i)+'</li>').join('')+'</'+tag+'>'; }
function lbCap(b){ return b.cap?'<p class="lb-cap">'+mdInline(b.cap)+'</p>':''; }
function lbHTML(b){
  switch(b.t){
    case 'h':     return '<h3>'+mdInline(b.x)+'</h3>';
    case 'p':     return '<p>'+mdInline(b.x)+'</p>';
    case 'list':  return lbList(b.x,'ul');
    case 'steps': return lbList(b.x,'ol');
    case 'table': return '<div class="mdxtable"><table'+(b.head.length>2?' class="wide"':'')+'><thead><tr>'+
      b.head.map(h=>'<th>'+mdInline(h)+'</th>').join('')+'</tr></thead><tbody>'+
      b.rows.map(r=>'<tr>'+r.map(c=>'<td>'+mdInline(c)+'</td>').join('')+'</tr>').join('')+
      '</tbody></table></div>'+lbCap(b);
    // the arrow lives inside the node it points at, so a wrapped row never starts with an
    // orphaned arrow hanging off the end of the line above
    case 'flow':  return '<div class="lb-flow">'+b.x.map(n=>
      '<span class="n">'+mdInline(n)+'</span>').join('')+'</div>'+lbCap(b);
    case 'split': return '<div class="lb-split">'+b.cols.map(c=>
      '<div class="c"><h5>'+mdInline(c.nm)+'</h5>'+lbList(c.items,'ul')+'</div>').join('')+'</div>'+lbCap(b);
    case 'key':   return '<div class="lb-call key"><span class="ic">⭐</span><span><strong>Must know — </strong>'+mdInline(b.x)+'</span></div>';
    case 'trap':  return '<div class="lb-call trap"><span class="ic">⚠</span><span><strong>Exam trap — </strong>'+mdInline(b.x)+'</span></div>';
    case 'note':  return '<div class="lb-call note"><span class="ic">✎</span><span>'+mdInline(b.x)+'</span></div>';
    case 'code':  return '<pre class="lb-code">'+esc(b.x)+'</pre>'+lbCap(b);
    case 'dtree': return '<div class="lb-tree">'+b.x.map(r=>
      '<div class="r"><span class="q">'+mdInline(r[0])+'</span><span class="v">'+mdInline(r[1])+'</span></div>').join('')+'</div>'+lbCap(b);
    default:      return '';
  }
}
function blocksHTML(arr){ return (arr||[]).map(lbHTML).join(''); }
function blocksChars(arr){ return (arr||[]).reduce((n,b)=>n+lbHTML(b).length,0); }

// ---------- run state ----------
// L is null whenever no subject is open. Everything about the run lives in it so that one
// localStorage write per transition is enough to survive a refresh.
let L=null, lrnTimer=null, lrnGate=0, lrnGateTimer=null, lrnQuitArm=0;
const LRN_KEY='academy_learn';

function learnSave(){
  if(!L) return;
  try{
    localStorage.setItem(LRN_KEY,JSON.stringify({
      v:1, sec:L.sec, phase:L.phase, mi:L.mi, startedAt:L.startedAt, spent:L.spent,
      mods:L.mods, sim:L.sim?{qs:L.sim.qs,i:L.sim.i,ans:L.sim.ans,left:Math.max(0,L.sim.endAt-Date.now())}:null,
      savedAt:Date.now()}));
  }catch(e){}
}
function learnClear(){ try{ localStorage.removeItem(LRN_KEY); }catch(e){} }
function learnStored(){
  try{
    const raw=localStorage.getItem(LRN_KEY); if(!raw) return null;
    const s=JSON.parse(raw);
    if(!s||s.v!==1||!learnData(s.sec)) return null;
    if(Date.now()-(s.savedAt||0)>1000*60*60*24*7) return null;   // a week is long enough
    return s;
  }catch(e){ return null; }
}
function learnResume(){
  const s=learnStored(); if(!s) return false;
  const d=learnData(s.sec); if(!d) return false;
  ensureAudio(); exitStudyMode(); reviewMode=false; markMode=false; mock=null; sim=null;
  L={sec:s.sec, phase:s.phase||'read', mi:Math.min(s.mi||0,d.modules.length), startedAt:Date.now()-(s.spent&&s.spent.total||0),
     spent:s.spent||{total:0}, mods:s.mods||{}, quiz:null, sim:null, stage:Date.now()};
  if(s.sim&&s.phase==='sim'){
    L.sim={qs:s.sim.qs, i:s.sim.i||0, ans:s.sim.ans||{}, endAt:Date.now()+(s.sim.left||LSIM_MIN*60000)};
  }
  learnClock();
  toast('▶ Back to '+(SHORT[s.sec]||d.nm));
  if(L.phase==='sim'&&L.sim) learnSimPaint(); else learnMap();
  return true;
}

// ---------- clocks ----------
function learnStopClock(){
  if(lrnTimer){ clearInterval(lrnTimer); lrnTimer=null; }
  if(lrnGateTimer){ clearInterval(lrnGateTimer); lrnGateTimer=null; }
}
function learnClock(){
  learnStopClock();
  lrnTimer=setInterval(learnTick,1000);
}
function learnTotal(){ return L?Date.now()-L.startedAt:0; }
function learnTick(){
  if(!L){ learnStopClock(); return; }
  const tot=fmtMS(learnTotal()), stage=fmtMS(Date.now()-L.stage);
  const set=(id,txt,over)=>{ const e=$(id); if(e){ e.textContent=txt; e.classList.toggle('over',!!over); } };
  if(route==='learnMapScreen') set('lrnMapClock','⏱ '+tot);
  if(route==='learnReadScreen'){
    const m=learnModule(); set('lrnReadClock',stage+' / '+(m?m.min:8)+':00', m&&Date.now()-L.stage>m.min*60000);
  }
  if(route==='learnQuizScreen') set('lrnQuizClock',stage);
  if(route==='learnRecapScreen') set('lrnRecapClock',stage);
  if(route==='learnSimScreen'&&L.sim){
    const left=L.sim.endAt-Date.now();
    set('lrnSimClock',fmtMS(Math.max(0,left)),left<120000);
    if(left<=0) learnSimSubmit(true);
  }
}

// ---------- picker ----------
function learnRecord(sec){ return (P.courses||{})[sec]||null; }
function learnModsDone(sec){ const r=learnRecord(sec); return (r&&r.mods)||[]; }
function renderLearnPick(){
  const btn=$('lrnResume'), s=learnStored();
  if(s&&learnData(s.sec)){
    const d=learnData(s.sec);
    btn.classList.remove('hidden');
    btn.innerHTML='▶ Continue '+esc(SHORT[s.sec]||d.nm)+
      ' <span style="opacity:.7">· part '+Math.min((s.mi||0)+1,d.modules.length)+' of '+d.modules.length+'</span>';
    btn.onclick=()=>{ if(!learnResume()) toast('That subject has expired'); };
  } else btn.classList.add('hidden');

  const list=$('lrnPickList'); list.innerHTML='';
  if(!LEARN_SECS.length){
    list.innerHTML='<div class="exempty">No subject has been authored yet. '+
      'Run <code>python3 build_learn.py</code> to inject them.</div>';
    return;
  }
  LEARN_SECS.forEach(sec=>{
    const d=learnData(sec), rec=learnRecord(sec), done=learnModsDone(sec).length;
    const mins=d.modules.reduce((a,m)=>a+m.min,0)+LSIM_MIN+8;
    const b=document.createElement('button'); b.className='crsrow';
    b.innerHTML='<span class="cem">'+(rec&&rec.best>=LSIM_PASS?'🎓':secEm(sec))+'</span>'+
      '<span style="flex:1;min-width:0"><span class="cnm">'+esc(SHORT[sec]||d.nm)+'</span>'+
      '<span class="cmeta">'+d.modules.length+' parts · '+mins+' min · '+
      d.modules.reduce((a,m)=>a+m.checks.length,0)+' check questions · 10-question exam'+
      (done?' · '+done+'/'+d.modules.length+' parts passed':'')+
      (rec?' · best '+rec.best+'%':'')+'</span></span>'+
      (rec?'<span class="cdone">✓ '+rec.runs+'</span>':'');
    b.onclick=()=>startLearn(sec);
    list.appendChild(b);
  });
}

// ---------- lifecycle ----------
function startLearn(sec){
  ensureAudio();
  const d=learnData(sec);
  if(!d){ toast('That subject has not been authored yet'); return; }
  exitStudyMode(); reviewMode=false; markMode=false; mock=null; sim=null;
  P.lastLearn=sec;
  L={sec, phase:'read', mi:0, startedAt:Date.now(), spent:{total:0}, mods:{}, quiz:null, sim:null, stage:Date.now()};
  learnClock(); learnSave(); learnMap();
}
function learnModule(i){
  if(!L) return null;
  const d=learnData(L.sec); if(!d) return null;
  return d.modules[i===undefined?L.mi:i]||null;
}
function learnStages(){ const d=learnData(L.sec); return d.modules.length+2; }
function learnStageIndex(){
  if(!L) return 0;
  if(L.phase==='recap') return learnStages()-2;
  if(L.phase==='sim')   return learnStages()-1;
  return L.mi;
}
function learnRail(id){
  const el=$(id); if(!el||!L) return;
  const n=learnStages(), at=learnStageIndex();
  el.innerHTML='';
  for(let i=0;i<n;i++){
    const t=document.createElement('i');
    if(i<at) t.className='on'; else if(i===at) t.className='now';
    el.appendChild(t);
  }
}
function learnPassedCount(){ return Object.values(L.mods).filter(m=>m.passed).length; }

function learnMap(){
  if(!L) return;
  const d=learnData(L.sec);
  learnRail('lrnRail');
  $('lrnMapSubject').textContent=(SHORT[L.sec]||d.nm).slice(0,26);
  $('lrnMapDone').textContent=learnPassedCount()+' / '+d.modules.length+' parts';
  $('lrnMapTitle').textContent=d.nm;
  $('lrnMapSub').textContent='Work down the parts in order. Each one ends with a few questions on '+
    'that part; pass them and the next part opens. After the last part: the full summary, then a '+
    'ten-question exam on this subject only.';
  const list=$('lrnMapList'); list.innerHTML='';
  d.modules.forEach((m,i)=>{
    const st=L.mods[m.id]||{}, done=!!st.passed, now=(i===L.mi&&L.phase!=='recap'&&L.phase!=='sim');
    const row=document.createElement('button');
    row.className='lrnmod'+(done?' done':'')+(now?' now':'')+(i>L.mi?' lock':'');
    const meta=[m.min+' min', m.checks.length+' questions'];
    if(st.attempts) meta.push(st.best+'/'+m.checks.length+' best · '+st.attempts+(st.attempts>1?' attempts':' attempt'));
    row.innerHTML='<span class="st">'+(done?'✓':(i>L.mi?'🔒':i+1))+'</span>'+
      '<span class="bd"><span class="nm">'+esc(m.nm)+'</span>'+
      '<span class="go">'+esc(m.goal)+'</span>'+
      '<span class="mt">'+esc(meta.join(' · '))+'</span></span>';
    row.onclick=()=>{ if(i>L.mi){ toast('Finish part '+(L.mi+1)+' first'); return; } L.mi=i; L.phase='read'; learnReadModule(); };
    list.appendChild(row);
  });
  const allDone=learnPassedCount()>=d.modules.length;
  [['📚 Full summary of the subject','Everything above in one place, plus the decision tables and traps','recap'],
   ['🧪 Ten-question exam','Authored for these parts — nothing from outside this subject','sim']].forEach(([nm,sub,ph])=>{
    const row=document.createElement('div');
    row.className='lrnmod fin'+(allDone?'':' lock')+(L.phase===ph?' now':'');
    row.innerHTML='<span class="st">'+(allDone?'▸':'🔒')+'</span><span class="bd">'+
      '<span class="nm">'+esc(nm)+'</span><span class="go">'+esc(sub)+'</span></span>';
    list.appendChild(row);
  });
  const goBtn=$('lrnMapGo');
  goBtn.textContent=L.phase==='sim'?'Resume the exam ▸':
                 L.phase==='recap'?'Read the full summary ▸':
                 (L.mods[d.modules[L.mi]&&d.modules[L.mi].id]||{}).attempts?'Read part '+(L.mi+1)+' again ▸':
                 (L.mi?'Continue with part '+(L.mi+1)+' ▸':'Start part 1 ▸');
  learnSave();
  go('learnMapScreen');
}
function learnContinue(){
  if(!L) return;
  if(L.phase==='sim'){ if(L.sim) learnSimPaint(); else learnSim(); return; }
  if(L.phase==='recap'){ learnRecap(); return; }
  if(L.phase==='quiz'&&L.quiz){ learnQuizPaint(); return; }
  learnReadModule();
}

// ---------- reading a part ----------
function learnGateFor(chars,repeat){
  if(TEST) return 0;
  const base=Math.max(12,Math.min(70,Math.round(chars/1000*11)));
  return repeat?Math.round(base/3):base;
}
function learnReadModule(){
  if(!L) return;
  const d=learnData(L.sec), m=learnModule(); if(!m) return;
  const st=L.mods[m.id]||{};
  L.phase='read'; L.stage=Date.now();
  learnRail('lrnReadRail');
  $('lrnReadStep').textContent='PART '+(L.mi+1)+' OF '+d.modules.length;
  $('lrnReadSubject').textContent=(SHORT[L.sec]||d.nm).slice(0,22);
  $('lrnReadTitle').textContent=m.nm;
  $('lrnReadGoal').innerHTML='<b>After this</b><span>'+esc(m.goal)+'</span>';
  const redo=$('lrnReadRedo');
  if(st.missed&&st.missed.length){
    redo.classList.remove('hidden');
    redo.innerHTML='<b>Read it again — these are what you missed</b><ul>'+
      st.missed.map(t=>'<li>'+esc(t)+'</li>').join('')+'</ul>';
  } else redo.classList.add('hidden');
  $('lrnReadBody').innerHTML=blocksHTML(m.blocks);
  $('lrnReadClock').textContent='0:00 / '+m.min+':00';
  $('lrnReadClock').classList.remove('over');
  learnArmGate('lrnReadGo',learnGateFor(blocksChars(m.blocks),!!st.attempts),
               'Ready — take the questions ▸',()=>learnQuiz());
  learnSave();
  go('learnReadScreen');
  const sc=$('learnReadScreen'); if(sc) sc.scrollTop=0;
}
function learnArmGate(btnId,secs,label,then){
  const btn=$(btnId);
  if(lrnGateTimer){ clearInterval(lrnGateTimer); lrnGateTimer=null; }
  lrnGate=secs;
  btn.dataset.ready=''; btn.dataset.label=label;
  btn.onclick=()=>{
    if(btn.disabled||!btn.dataset.ready) return;
    btn.disabled=true;                       // consumed: a double tap must not skip a stage
    if(lrnGateTimer){ clearInterval(lrnGateTimer); lrnGateTimer=null; }
    then();
  };
  if(secs<=0){ btn.disabled=false; btn.dataset.ready='1'; btn.textContent=label; return; }
  btn.disabled=true; btn.textContent='Read… '+secs;
  lrnGateTimer=setInterval(()=>{
    lrnGate--;
    if(lrnGate<=0){
      clearInterval(lrnGateTimer); lrnGateTimer=null;
      btn.disabled=false; btn.dataset.ready='1'; btn.textContent=label; sfx.tap();
    } else btn.textContent='Read… '+lrnGate;
  },1000);
}

// ---------- check questions on the part just read ----------
function lrnShuffle(n){
  const a=[...Array(n).keys()];
  for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; }
  return a;
}
function learnBuildQuiz(src){
  return lrnShuffle(src.length).map(qi=>{
    const q=src[qi], order=lrnShuffle(q.o.length);
    return {src:qi, order, picked:[], answered:false, ok:false};
  });
}
function learnQuiz(){
  const m=learnModule(); if(!m) return;
  L.phase='quiz'; L.stage=Date.now();
  L.quiz={mid:m.id, items:learnBuildQuiz(m.checks), i:0, correct:0, missed:[]};
  learnSave(); learnQuizPaint();
}
function learnQuizNeed(n){ return Math.ceil(n*LPASS); }
function learnQuizQ(){
  const m=learnData(L.sec).modules.find(x=>x.id===L.quiz.mid);
  return m.checks[L.quiz.items[L.quiz.i].src];
}
function learnQuizPaint(){
  if(!L||!L.quiz) return;
  const d=learnData(L.sec), m=d.modules.find(x=>x.id===L.quiz.mid), Q=L.quiz;
  const it=Q.items[Q.i], q=m.checks[it.src];
  $('lrnQuizTag').textContent='CHECK · PART '+(d.modules.indexOf(m)+1);
  $('lrnQuizTitle').textContent=m.nm.slice(0,28);
  $('lrnQuizCount').textContent=(Q.i+1)+' / '+Q.items.length;
  $('lrnQuizNeed').textContent='need '+learnQuizNeed(Q.items.length)+' right';
  $('lrnQuizProg').style.width=Math.round(Q.i/Q.items.length*100)+'%';
  $('lrnQuizQ').textContent=q.q;
  $('lrnQuizResult').classList.add('hidden');
  $('lrnQuizLive').classList.remove('hidden');
  const multi=q.a.length>1;
  const box=$('lrnQuizOpts'); box.innerHTML='';
  it.order.forEach((oi,shown)=>{
    const o=q.o[oi], btn=document.createElement('button');
    btn.className='opt'; btn.dataset.oi=String(oi);
    btn.innerHTML='<span class="ltr">'+String.fromCharCode(65+shown)+'</span><span>'+esc(o.t)+'</span>';
    btn.onclick=()=>learnQuizPick(oi);
    box.appendChild(btn);
  });
  $('lrnQuizFeed').classList.add('hidden');
  const sub=$('lrnQuizSubmit');
  sub.disabled=true; sub.textContent=multi?'Check my answer (pick '+q.a.length+')':'Check my answer';
  sub.onclick=()=>learnQuizSubmit();
  go('learnQuizScreen');
  const sc=$('learnQuizScreen'); if(sc) sc.scrollTop=0;
}
function learnQuizPick(oi){
  const Q=L&&L.quiz; if(!Q) return;
  const it=Q.items[Q.i]; if(it.answered) return;
  const q=learnQuizQ(), multi=q.a.length>1;
  if(multi){
    const at=it.picked.indexOf(oi);
    if(at>=0) it.picked.splice(at,1);
    else if(it.picked.length<q.a.length) it.picked.push(oi);
  } else it.picked=[oi];
  [...$('lrnQuizOpts').children].forEach(b=>b.classList.toggle('sel',it.picked.includes(Number(b.dataset.oi))));
  $('lrnQuizSubmit').disabled=multi?it.picked.length!==q.a.length:!it.picked.length;
  sfx.tap();
}
function learnQuizSubmit(){
  const Q=L&&L.quiz; if(!Q) return;
  const it=Q.items[Q.i]; if(it.answered||!it.picked.length) return;
  const q=learnQuizQ();
  const ok=it.picked.length===q.a.length&&q.a.every(a=>it.picked.includes(a));
  it.answered=true; it.ok=ok;
  if(ok){ Q.correct++; sfx.right(); } else { sfx.wrong(); buzz(40); Q.missed.push(q.q); }
  [...$('lrnQuizOpts').children].forEach(b=>{
    const oi=Number(b.dataset.oi);
    b.classList.remove('sel');
    if(q.a.includes(oi)) b.classList.add('ok');
    else if(it.picked.includes(oi)) b.classList.add('no');
    else b.classList.add('dim');
    b.onclick=null;
  });
  const correctText=q.a.map(a=>q.o[a].t).join('  ·  ');
  const feed=$('lrnQuizFeed');
  feed.className='lrnfeed '+(ok?'ok':'no');
  feed.innerHTML='<b>'+(ok?'✓ That is right':'✗ Not quite')+'</b>'+esc(q.x)+
    (ok?'':'<span class="ans"><b style="display:inline;color:var(--lime)">Correct: </b>'+esc(correctText)+'</span>');
  const sub=$('lrnQuizSubmit');
  sub.disabled=false;
  sub.textContent=(Q.i+1<Q.items.length)?'Next question ▸':'See how you did ▸';
  sub.onclick=()=>{
    if(Q.i+1<Q.items.length){ Q.i++; learnSave(); learnQuizPaint(); }
    else learnQuizResult();
  };
  learnSave();
}
function learnQuizResult(){
  const Q=L.quiz, d=learnData(L.sec), m=d.modules.find(x=>x.id===Q.mid);
  const need=learnQuizNeed(Q.items.length), passed=Q.correct>=need;
  const pct=Math.round(Q.correct/Q.items.length*100);
  const st=L.mods[m.id]||{attempts:0,best:0};
  st.attempts++; st.best=Math.max(st.best,Q.correct); st.passed=st.passed||passed;
  st.missed=passed?[]:Q.missed.slice(0,4);
  L.mods[m.id]=st;
  L.spent[m.id]=(L.spent[m.id]||0)+(Date.now()-L.stage);

  let pay=null;
  if(passed&&!st.paid){
    st.paid=true;
    pay={coins:8+(st.attempts===1?7:0), xp:45+(st.attempts===1?25:0)};
    addCoins(pay.coins); addXP(pay.xp);
  }
  $('lrnQuizLive').classList.add('hidden');
  const box=$('lrnQuizResult');
  box.classList.remove('hidden');
  box.innerHTML='<div class="lrnscore"><div class="big" style="color:'+(passed?'var(--lime)':'var(--gold)')+'">'+
      Q.correct+' / '+Q.items.length+'</div>'+
      '<div class="lbl">'+(passed?'Part '+(d.modules.indexOf(m)+1)+' passed — '+pct+'%'
        :'You need '+need+' to move on — '+pct+'% this time')+'</div></div>'+
    '<div class="lrnpartbar">'+Q.items.map((it,i)=>
      '<span class="phasechip '+(it.ok?'lime':'red')+'">'+(i+1)+(it.ok?' ✓':' ✗')+'</span>').join('')+'</div>'+
    (pay?'<div class="lrnpartbar"><span class="phasechip gold">+'+pay.coins+' 🪙</span>'+
         '<span class="phasechip">+'+pay.xp+' XP</span></div>':'')+
    (passed?'':'<div class="lrnredo" style="margin-top:12px"><b>What to look for on the re-read</b><ul>'+
      Q.missed.map(t=>'<li>'+esc(t)+'</li>').join('')+'</ul></div>')+
    '<div class="crsfoot"><button class="btn wide" id="lrnQuizAfter" style="width:100%"></button>'+
    '<button class="minichip" id="lrnQuizMap" style="display:block;margin:2px auto 0">See all parts</button></div>';

  const last=L.mi>=d.modules.length-1;
  L.quiz=null;
  if(passed&&last) L.phase='recap';
  else { if(passed) L.mi++; L.phase='read'; }
  const after=$('lrnQuizAfter');
  after.textContent=!passed?'Read this part again ▸':(last?'Read the full summary ▸':'Next part ▸');
  after.onclick=()=>{ after.disabled=true; learnContinue(); };
  if(passed&&!last) toast('✅ Part '+(d.modules.indexOf(m)+1)+' done');
  $('lrnQuizMap').onclick=()=>learnMap();
  learnSave(); saveProfile();
}

// ---------- the full written summary ----------
function learnRecapHTML(){
  const d=learnData(L.sec), out=[];
  out.push('<div class="lb-call note"><span class="ic">✎</span><span>Everything from the '+
    d.modules.length+' parts you just worked through, in one place. Read it end to end — the exam '+
    'right after it is built from these parts.</span></div>');
  out.push(blocksHTML(d.recap));
  out.push('<h3>Part by part, in one line each</h3>');
  out.push('<div class="mdxtable"><table><thead><tr><th>Part</th><th>What it gave you</th></tr></thead><tbody>'+
    d.modules.map((m,i)=>'<tr><td><b>'+(i+1)+'. '+esc(m.nm)+'</b></td><td>'+esc(m.goal)+'</td></tr>').join('')+
    '</tbody></table></div>');
  if(typeof blueprintHTML==='function'){
    out.push('<details class="fullwrite"><summary>The reference material for this subject — services, decision matrix, trade-offs</summary>'+
             '<div class="mdx">'+blueprintHTML(L.sec)+'</div></details>');
    out.push('<details class="fullwrite"><summary>Traps, hard limits and the long write-up from the study guide</summary>'+
             '<div class="mdx">'+deepDiveHTML(L.sec)+'</div></details>');
  }
  return out.join('');
}
function learnRecap(){
  if(!L) return;
  const d=learnData(L.sec);
  L.phase='recap'; L.stage=Date.now();
  learnRail('lrnRecapRail');
  $('lrnRecapSubject').textContent=(SHORT[L.sec]||d.nm).slice(0,22);
  $('lrnRecapTitle').textContent='Full summary — '+d.nm;
  $('lrnRecapSub').textContent='All '+d.modules.length+' parts passed in '+fmtMS(learnTotal())+
    '. Next: ten exam questions, '+LSIM_MIN+' minutes, on this subject only.';
  $('lrnRecapBody').innerHTML=learnRecapHTML();
  $('lrnRecapClock').textContent='0:00';
  learnArmGate('lrnRecapGo',TEST?0:45,'Start the ten-question exam ▸',()=>learnSim());
  learnSave();
  go('learnRecapScreen');
  const sc=$('learnRecapScreen'); if(sc) sc.scrollTop=0;
}

// ---------- the ten-question exam ----------
function learnSim(){
  const d=learnData(L.sec);
  L.phase='sim'; L.stage=Date.now();
  L.sim={qs:lrnShuffle(d.final.length).map(qi=>({src:qi,order:lrnShuffle(d.final[qi].o.length)})),
         i:0, ans:{}, endAt:Date.now()+LSIM_MIN*60000};
  learnSave(); learnSimPaint();
}
function learnSimPaint(){
  if(!L||!L.sim) return;
  const d=learnData(L.sec), S=L.sim, it=S.qs[S.i], q=d.final[it.src];
  const m=d.modules.find(x=>x.id===q.m);
  $('lrnSimCount').textContent=(S.i+1)+' / '+S.qs.length;
  $('lrnSimPart').textContent=m?'part '+(d.modules.indexOf(m)+1):'';
  $('lrnSimQ').textContent=q.q;
  const picked=S.ans[S.i]||[];
  const box=$('lrnSimOpts'); box.innerHTML='';
  it.order.forEach((oi,shown)=>{
    const btn=document.createElement('button');
    btn.className='opt'+(picked.includes(oi)?' sel':'');
    btn.dataset.oi=String(oi);
    btn.innerHTML='<span class="ltr">'+String.fromCharCode(65+shown)+'</span><span>'+esc(q.o[oi].t)+'</span>';
    btn.onclick=()=>learnSimPick(oi);
    box.appendChild(btn);
  });
  const strip=$('lrnSimStrip'); strip.innerHTML='';
  S.qs.forEach((_,i)=>{
    const b=document.createElement('button');
    b.className='lrndot'+(i===S.i?' now':'')+((S.ans[i]||[]).length?' done':'');
    b.textContent=i+1; b.onclick=()=>{ S.i=i; learnSimPaint(); };
    strip.appendChild(b);
  });
  $('lrnSimPrev').disabled=S.i===0;
  $('lrnSimNext').textContent=S.i===S.qs.length-1?'First question ›':'Next ›';
  const n=Object.values(S.ans).filter(a=>a&&a.length).length;
  $('lrnSimSubmit').textContent='Submit exam'+(n<S.qs.length?' ('+n+'/'+S.qs.length+' answered)':'');
  go('learnSimScreen');
  learnTick();
}
function learnSimPick(oi){
  const S=L&&L.sim; if(!S) return;
  const q=learnData(L.sec).final[S.qs[S.i].src];
  const cur=S.ans[S.i]||[];
  if(q.a.length>1){
    const at=cur.indexOf(oi);
    if(at>=0) cur.splice(at,1); else if(cur.length<q.a.length) cur.push(oi);
    S.ans[S.i]=cur;
  } else S.ans[S.i]=[oi];
  sfx.tap(); learnSave(); learnSimPaint();
}
function learnSimGo(d){
  const S=L&&L.sim; if(!S) return;
  S.i=(S.i+d+S.qs.length)%S.qs.length;
  learnSimPaint();
}
function learnSimSubmit(auto){
  const S=L&&L.sim; if(!S||S.done) return;
  const n=Object.values(S.ans).filter(a=>a&&a.length).length;
  if(!auto&&n<S.qs.length&&!S.warned){
    S.warned=true;
    toast(S.qs.length-n+' unanswered — tap submit again to finish anyway');
    return;
  }
  S.done=true;
  L.spent.sim=(L.spent.sim||0)+(Date.now()-L.stage);
  if(auto) toast('⏰ Time — the exam was submitted for you');
  learnFinish();
}

// ---------- result ----------
function learnReviewCard(q,picked,n){
  const bits=[];
  bits.push('<div class="rcq"><b style="color:var(--dim);font-family:var(--mono);font-size:11px">Q'+n+'  </b>'+esc(q.q)+'</div>');
  q.o.forEach((o,oi)=>{
    const right=q.a.includes(oi), chose=picked.includes(oi);
    const pillar=pillarFor(o.t);
    bits.push('<div class="rcopt '+(right?'good':(chose?'bad':''))+'">'+
      '<span class="exl">'+String.fromCharCode(65+oi)+'</span><span>'+
      (right?'<b>'+esc(o.t)+'</b>':esc(o.t))+
      (chose?'<span class="rcpick">you picked this</span>':'')+
      (o.w?'<span class="rcwhy">'+(right?'✔ ':'✘ ')+esc(o.w)+'</span>':'')+
      (!right&&pillar?'<span class="rcpillar">'+esc(pillar)+'</span>':'')+
      '</span></div>');
  });
  bits.push('<div class="exfoot">'+esc(q.x)+'</div>');
  return '<div class="rcard">'+bits.join('')+'</div>';
}
function learnFinish(){
  const d=learnData(L.sec), S=L.sim;
  let correct=0;
  const rows=[];
  S.qs.forEach((it,i)=>{
    const q=d.final[it.src], picked=S.ans[i]||[];
    const ok=picked.length===q.a.length&&q.a.every(a=>picked.includes(a));
    if(ok) correct++;
    rows.push({q,picked,ok});
  });
  const pct=Math.round(correct/S.qs.length*100), passed=pct>=LSIM_PASS;
  const mins=Math.max(1,Math.round(learnTotal()/60000));
  const firstTry=d.modules.every(m=>(L.mods[m.id]||{}).attempts===1);

  P.courses=P.courses||{};
  const prev=P.courses[L.sec];
  const modIds=d.modules.filter(m=>(L.mods[m.id]||{}).passed).map(m=>m.id);
  P.courses[L.sec]={runs:(prev?prev.runs:0)+1, best:Math.max(prev?prev.best:0,pct), last:pct,
                    mins:Math.max(prev?prev.mins:0,mins), at:dayKey(),
                    mods:[...new Set([...(prev&&prev.mods||[]),...modIds])]};
  let coins=Math.round(pct*0.7)+(passed?60:0)+(firstTry?25:0);
  let xp=Math.round(pct*3)+(passed?260:0)+(firstTry?70:0);
  if(!prev){ coins+=80; xp+=140; } else { coins=Math.round(coins*0.6); xp=Math.round(xp*0.6); }
  coins=Math.min(coins,300); xp=Math.min(xp,1100);
  addCoins(coins); addXP(xp);

  $('lrnDoneScore').textContent=pct+'%';
  $('lrnDoneScore').style.color=passed?'var(--lime)':'var(--gold)';
  $('lrnDoneVerdict').textContent=(passed?'SUBJECT PASSED — ':'SUBJECT COMPLETE — ')+(SHORT[L.sec]||d.nm);
  $('lrnDoneHeb').innerHTML=hebHTML(passed?'learn':'fail');
  $('lrnDoneMeta').textContent=mins+' min · exam '+correct+'/'+S.qs.length+' · '+
    d.modules.length+' parts · +'+coins+' 🪙 · +'+xp+' XP';
  $('lrnDoneBreak').innerHTML=d.modules.map((m,i)=>{
    const st=L.mods[m.id]||{};
    return '<div class="minirow"><span class="ch-t" style="font-size:12px">'+(i+1)+'. '+esc(m.nm)+'</span>'+
      '<span class="ch-s">'+(st.best||0)+'/'+m.checks.length+
      (st.attempts>1?' · '+st.attempts+' attempts':'')+'</span></div>';
  }).join('')+
    '<div class="minirow"><span class="ch-t" style="font-size:12px">🧪 Exam</span>'+
    '<span class="ch-s">'+correct+'/'+S.qs.length+' · '+pct+'%</span></div>'+
    '<div class="minirow"><span class="ch-t" style="font-size:12px">⏱ Total</span>'+
    '<span class="ch-s">'+fmtMS(learnTotal())+'</span></div>';
  $('lrnDoneReview').innerHTML=rows.map((r,i)=>learnReviewCard(r.q,r.picked,i+1)).join('');

  const sec=L.sec;
  $('lrnDoneNext').onclick=()=>{
    const at=LEARN_SECS.indexOf(sec);
    startLearn(LEARN_SECS[(at+1)%LEARN_SECS.length]);
  };
  $('lrnDonePractice').onclick=()=>{ L=null; startSession(sec); };
  $('lrnDoneHome').onclick=()=>{ L=null; go('homeScreen'); renderHome(); };
  $('lrnDoneBack').onclick=()=>{ L=null; renderLearnPick(); go('learnPickScreen'); };

  learnStopClock(); learnClear(); L=null;
  saveProfile(); checkBadges(); logReadiness(); renderReadiness(); renderHome();
  if(passed) celebrate(); else sfx.end();
  go('learnDoneScreen');
}

// ---------- leaving ----------
function learnLeave(silent){
  if(!L) return;
  learnSave(); learnStopClock(); L=null;
  if(!silent) toast('Saved — pick the subject again to carry on');
}
function learnQuit(){
  if(L&&Date.now()-lrnQuitArm>3000&&learnPassedCount()>0){
    lrnQuitArm=Date.now();
    toast('Tap again to leave — your progress is saved');
    return;
  }
  learnLeave(true);
  go('homeScreen'); renderHome();
}

// ---------- wiring ----------
$('courseOpen').onclick=()=>{ renderLearnPick(); go('learnPickScreen'); };
$('lrnPickBack').onclick=()=>{ go('homeScreen'); renderHome(); };
$('lrnMapBack').onclick=()=>{ learnSave(); renderLearnPick(); go('learnPickScreen'); };
$('lrnMapGo').onclick=()=>learnContinue();
$('lrnMapQuit').onclick=()=>learnQuit();
$('lrnReadBack').onclick=()=>{ if(L) learnMap(); else { go('homeScreen'); renderHome(); } };
$('lrnQuizBack').onclick=()=>{ if(L){ L.quiz=null; L.phase='read'; learnMap(); } else { go('homeScreen'); renderHome(); } };
$('lrnRecapBack').onclick=()=>{ if(L) learnMap(); else { go('homeScreen'); renderHome(); } };
$('lrnSimBack').onclick=()=>{ toast('Finish or submit the exam — the clock is running'); };
$('lrnSimPrev').onclick=()=>learnSimGo(-1);
$('lrnSimNext').onclick=()=>learnSimGo(1);
$('lrnSimSubmit').onclick=()=>learnSimSubmit(false);

const LEARN_T={
  LEARN, learnData, get L(){return L;}, startLearn, learnResume, learnStored, learnMap,
  learnReadModule, learnQuiz, learnQuizPick, learnQuizSubmit, learnQuizPaint, learnQuizResult,
  learnQuizNeed, learnRecap, learnSim, learnSimPick, learnSimGo, learnSimSubmit, learnFinish,
  learnContinue, learnLeave, learnQuit, renderLearnPick, lbHTML, blocksHTML, learnReviewCard,
  LSIM_MIN, LSIM_PASS, LPASS, LEARN_SECS, get gate(){return lrnGate;},
  clickGate(id){ const b=$(id); if(b&&b.dataset.ready) b.onclick(); return !!(b&&b.dataset.ready); },
  forceGate(id){ const b=$(id); if(!b) return false;
    if(lrnGateTimer){ clearInterval(lrnGateTimer); lrnGateTimer=null; }
    lrnGate=0; b.disabled=false; b.dataset.ready='1'; b.textContent=b.dataset.label||'Continue'; return true; }
};
