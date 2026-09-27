#!/usr/bin/env python3
"""Casino: a tournament mode — you and seven bots, knockout, questions from the exams.

Asked for: a casino mode with tournaments against bots that play like people; duels of
questions; bots right about two times in three; two minutes a question; each player answers five
questions and whoever gets more right wins and goes through; eight players, round after round
until it is won; the winner takes the pot; questions from the exams.

The rules and the money are on the server (supabase_tournament.sql): the questions, the answer
key, the clock, the bots' answers and the payout. The page shows what it is told:

  - Lobby: rules, the exam the questions come from, the buy-in (10–250 chips) and the pot it
    makes (eight buy-ins), how many of today's five starts are left, and Resume when one is open.
  - The match: the duel's board — both players, a dot per question for each, the score — the
    round (quarter-final, semi-final, final; sudden death after five), a two-minute clock, the
    question with where it comes from. The bot "answers" at the moment the server chose for it, so
    it can be seen to answer before you, or to still be thinking. Your answer comes back with the
    right one, the bot's result and why.
  - Between rounds and at the end: the bracket, every match and score, your path marked; the next
    opponent, or the pot won, or who knocked you out and who won it.

A tournament survives leaving the casino and a reload: the lobby asks the server for the open
one and picks it up, and the server's clock is the one that counts.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

# ---------------------------------------------------------------- tab + panel
sub("""        <button class="castab" id="casTabDuel">⚔️ Duel</button>""",
"""        <button class="castab" id="casTabDuel">⚔️ Duel</button>
        <button class="castab" id="casTabTour">🏆 Tourney</button>""")
sub("""      <!-- duel -->
      <div class="card hidden" id="casDuel">""","""      <!-- tournament -->
      <div class="card hidden" id="casTour">
        <div id="tourLobby">
          <div class="duelhero"><span class="ic">🏆</span>
            <div><div class="ch-t">Tournament</div>
              <div class="ch-s">You and seven bots · knockout · the winner takes the pot</div></div></div>
          <div class="duelrules"><span><b>8</b> players</span><span><b>3</b> rounds</span><span><b>5</b> questions a match</span>
            <span><b>2 min</b> each</span><span>bots are right about <b>2 in 3</b></span></div>
          <div class="divider"></div>
          <div class="minirow"><span class="ch-t" style="font-size:12px">Questions from</span><span class="ch-s" id="tourExamNote"></span></div>
          <select class="authin" id="tourExam" aria-label="Which practice exam the tournament's questions come from"></select>
          <div class="minirow"><span class="ch-t" style="font-size:12px">Buy-in</span><span class="ch-s" id="tourPotNote"></span></div>
          <div class="betrow" id="tourBuyins"></div>
          <div class="duelbtns">
            <button class="btn wide hidden" id="tourResume">▶ Back to your tournament</button>
            <button class="btn wide" id="tourStart">Start a tournament ▸</button>
          </div>
          <div class="duelrec" id="tourLeftNote"></div>
          <div class="authnote" id="tourMsg"></div>
        </div>
        <div id="tourPlay" class="hidden">
          <div class="tourround" id="tourRound">Quarter-final</div>
          <div class="duelboard">
            <div class="dside me" id="tourMeSide"><span class="dav" id="tourMeAv">Y</span>
              <span class="dname" id="tourMe">you</span><span class="dpips" id="tourMePips"></span></div>
            <div class="dscore"><span id="tourScore">0 — 0</span><small id="tourPot"></small></div>
            <div class="dside them" id="tourThemSide"><span class="dav" id="tourThemAv">?</span>
              <span class="dname" id="tourThem">them</span><span class="dpips" id="tourThemPips"></span></div>
          </div>
          <div class="rouhead" style="margin:6px 0 10px">
            <span class="tag" id="tourQn">Q1</span>
            <div class="roubar"><i id="tourBarFill"></i></div>
            <span class="roucount" id="tourCount">2:00</span>
          </div>
          <div class="duellast hidden" id="tourLast" aria-live="polite"></div>
          <div class="qcard" style="margin-bottom:10px"><div class="duelsrc" id="tourSrc"></div><div class="qtext" id="tourQ"></div></div>
          <div class="opts" id="tourOpts"></div>
          <div class="ch-note" id="tourStatus" style="text-align:center;min-height:20px;margin-top:8px" aria-live="polite"></div>
          <button class="btn wide hidden" id="tourLock" style="margin-top:10px">Lock in</button>
          <button class="btn ghost sm duelleave" id="tourLeave">Leave the tournament</button>
        </div>
        <div id="tourBracket" class="hidden" style="text-align:center">
          <div class="duelresult" id="tourResult">—</div>
          <div class="duelpay" id="tourPay"></div>
          <p class="ch-note" id="tourReason"></p>
          <div class="tourbr" id="tourBr"></div>
          <div class="duelrecap" id="tourRecap"></div>
          <div class="duelacts">
            <button class="btn hidden" id="tourNext">Next round ▸</button>
            <button class="btn ghost" id="tourAgain">Back to the lobby</button>
          </div>
        </div>
      </div>

      <!-- duel -->
      <div class="card hidden" id="casDuel">""")

sub("""function casTab(which){
  [['casTabRoul','casRoul'],['casTabBj','casBj'],['casTabDuel','casDuel']].forEach(([t,p])=>{""",
"""function casTab(which){
  [['casTabRoul','casRoul'],['casTabBj','casBj'],['casTabDuel','casDuel'],['casTabTour','casTour']].forEach(([t,p])=>{""")
sub("""  if(which!=='Duel'&&typeof duelStop==='function'&&!duelId) duelStop();
}""","""  if(which!=='Duel'&&typeof duelStop==='function'&&!duelId) duelStop();
  if(which==='Tour'&&typeof tourLoad==='function') tourLoad(); else if(typeof tourStop==='function') tourStop();
}""")
sub("""  if(id!=='casinoScreen'&&typeof rouStop==='function'){ rouStop(); if(typeof duelStop==='function') duelStop(); }""",
"""  if(id!=='casinoScreen'&&typeof rouStop==='function'){ rouStop(); if(typeof duelStop==='function') duelStop(); if(typeof tourStop==='function') tourStop(); }""")

# ---------------------------------------------------------------- the client
sub("""// ---------- the practice bot: the same rules, played in this page, no chips ----------""",
r"""// ---------- tournament: you and seven bots, three knockout rounds (supabase_tournament.sql) ----------
// The server holds everything that decides chips: the questions, the answer key, the clock, the
// bots' answers and the payout. This draws what it is told and keeps a local clock in step.
let tourBuyin=25, tourExam=0, tourView=null, tourTick=null, tourPicked=new Set(), tourLeftToday=null;
let tourBase=0, tourBaseLeft=0, tourKey='', tourMissingSQL=false;
try{ const n=Number(localStorage.getItem('academy_tour_exam')); if(n>=0&&n<=PAPER_COUNT) tourExam=Math.floor(n)||0; }catch(e){}
const TOUR_ROUND=['Quarter-final','Semi-final','Final'];
function tourMsg(t,kind){ const e=$('tourMsg'); if(!e) return; e.textContent=t||''; e.className='authnote'+(kind?' '+kind:''); }
function tourShow(which){ ['tourLobby','tourPlay','tourBracket'].forEach(id=>$(id).classList.toggle('hidden',id!=='tour'+which)); }
function tourStop(){ if(tourTick){ clearInterval(tourTick); tourTick=null; } }
const tourName=(v,seat)=>{ const p=(v&&v.players)||[]; return String(p[seat]||(seat===0?'you':'player')); };
function tourMissing(){
  tourMissingSQL=true; tourShow('Lobby'); renderTourLobby();
  tourMsg('Tournaments are not installed on your database yet — run supabase_tournament.sql in the Supabase SQL editor.','bad');
}
function renderTourLobby(){
  const sel=$('tourExam');
  const opts=['<option value="0">Any exam — all '+QS.length.toLocaleString()+' questions</option>'];
  for(let n=1;n<=PAPER_COUNT;n++) opts.push('<option value="'+n+'">Exam '+n+'</option>');
  sel.innerHTML=opts.join(''); sel.value=String(tourExam);
  $('tourExamNote').textContent=tourExam?plural(paperQs(tourExam).length,'question')+' to draw from':'';
  renderBetRow('tourBuyins',tourBuyin,v=>{ tourBuyin=v; renderTourLobby(); });
  $('tourPotNote').textContent='pot '+(tourBuyin*8).toLocaleString()+' chips to the winner';
  const open=!!(tourView&&tourView.status==='active');
  $('tourResume').classList.toggle('hidden',!open);
  $('tourStart').classList.toggle('hidden',open);
  $('tourStart').textContent='Start a tournament — '+tourBuyin+' chips ▸';
  $('tourLeftNote').textContent=tourLeftToday==null?'':(tourLeftToday?plural(tourLeftToday,'tournament')+' left today':'No tournaments left today — back tomorrow');
}
async function tourLoad(){
  tourStop();
  if(!(typeof sbUser!=='undefined'&&sbUser)){ tourShow('Lobby'); renderTourLobby(); return; }
  const r=await casRpc('tourney_current',{},tourMsg,{missingOk:true});
  if(r==='missing'){ tourMissing(); return; }
  if(!r||!r.ok){ tourShow('Lobby'); renderTourLobby(); return; }
  tourMissingSQL=false; tourMsg('');           // a message from an earlier failure is not about now
  tourLeftToday=typeof r.left==='number'?r.left:null;
  if(r.t){ tourPaint(r.t); } else { tourView=null; tourShow('Lobby'); renderTourLobby(); }
}
async function tourStart(){
  if(casChips<tourBuyin){ tourMsg('Not enough chips for that buy-in.','bad'); return; }
  tourMsg('Seating the players…','busy');
  const r=await casRpc('tourney_start',{buyin:tourBuyin,exam:tourExam},tourMsg,{missingOk:true});
  if(r==='missing'){ tourMissing(); return; }
  if(!r){ return; }
  if(!r.ok){ tourMsg(r.reason||'Could not start','bad'); return; }
  tourMsg('');
  if(typeof tourLeftToday==='number'&&!r.resumed) tourLeftToday=Math.max(0,tourLeftToday-1);
  tourPaint(r.t);
  try{ $('casTour').scrollIntoView({block:'start',behavior:reduced?'auto':'smooth'}); }catch(e){}
}
// a dot per question: yours from your answers, theirs from the bot's (known once you answered)
function tourPips(el,v,side){
  const n=Math.max(5,v.n||5), log=v.log||[];
  el.innerHTML=Array.from({length:n},(_,i)=>{
    const e=log[i];
    if(e){ const ok=side==='you'?e.ok:e.bot; return '<i class="'+(ok?'ok':'no')+'"></i>'; }
    return '<i'+(i===v.i&&v.phase==='play'?' class="now"':'')+'></i>';
  }).join('');
}
function tourPaint(v){
  if(!v) return;
  tourView=v; tourStop();
  if(v.status==='active'&&v.phase==='play'){ tourShow('Play'); tourPaintPlay(v); return; }
  tourShow('Bracket'); tourPaintBracket(v);
}
function tourPaintPlay(v){
  const opp=tourName(v,v.opp), me=tourName(v,0);
  $('tourRound').textContent=(TOUR_ROUND[(v.round||1)-1]||'Round '+v.round)+' · vs '+opp;
  $('tourMe').textContent=me; $('tourThem').textContent=opp;
  $('tourMeAv').textContent=String(me).charAt(0).toUpperCase();
  $('tourThemAv').textContent=String(opp).charAt(0).toUpperCase();
  $('tourScore').textContent=(v.you||0)+' — '+(v.them||0);
  $('tourPot').textContent='POT '+Number(v.pot||0).toLocaleString();
  tourPips($('tourMePips'),v,'you'); tourPips($('tourThemPips'),v,'them');
  $('tourQn').textContent=(v.i>=5?'Sudden death · ':'')+'Q'+(v.i+1)+' of '+Math.max(5,v.n);
  // the question
  const q=QS[v.question];
  const key=v.id+':'+v.round+':'+v.i;
  if(key!==tourKey){
    tourKey=key; tourPicked.clear();
    if(!q){ $('tourQ').textContent='Question unavailable on this build.'; $('tourOpts').innerHTML=''; }
    else{
      $('tourSrc').textContent=duelWhere(v.question)+(q.a.length>1?' · choose '+q.a.length:'');
      $('tourQ').textContent=q.q;
      const need=q.a.length, box=$('tourOpts'); box.innerHTML='';
      q.o.forEach(([ltr,txt])=>{
        const b=document.createElement('button'); b.className='opt'; b.dataset.ltr=ltr;
        b.innerHTML='<span class="ltr">'+ltr+'</span><span>'+esc(txt)+'</span>';
        b.onclick=()=>{
          if(tourPicked.has(ltr)) tourPicked.delete(ltr);
          else { if(need===1) tourPicked.clear(); if(tourPicked.size>=need){ pickFull(need,b); return; } tourPicked.add(ltr); }
          [...box.children].forEach(el=>el.classList.toggle('sel',tourPicked.has(el.dataset.ltr)));
          $('tourLock').classList.toggle('hidden',tourPicked.size!==need);
        };
        box.appendChild(b);
      });
      $('tourLock').textContent=need>1?'Lock in '+plural(need,'answer'):'Lock in';
    }
    $('tourLock').classList.add('hidden');
  }
  tourPaintLast(v);
  // the clock: the server's time left, counted down here; the bot answers at the moment it chose
  tourBase=Date.now(); tourBaseLeft=Number(v.secondsLeft)||0;
  tourClock();
  tourTick=setInterval(tourClock,500);
  if(!$('tourLeave').dataset.armed) $('tourLeave').textContent='Leave the tournament';
}
function tourElapsedLeft(){ return Math.max(0,tourBaseLeft-Math.floor((Date.now()-tourBase)/1000)); }
function tourClock(){
  const v=tourView; if(!v||v.phase!=='play') { tourStop(); return; }
  const left=tourElapsedLeft(), total=Number(v.secondsTotal)||120;
  $('tourCount').textContent=Math.floor(left/60)+':'+String(left%60).padStart(2,'0');
  $('tourBarFill').style.width=pctW(left/total*100);
  $('tourCount').classList.toggle('closing',left<=15);
  $('tourBarFill').parentElement.classList.toggle('closing',left<=15);
  const opp=tourName(v,v.opp), answered=(total-left)>=(Number(v.oppAt)||9999);
  $('tourThemSide').classList.toggle('answered',answered);
  $('tourStatus').textContent=answered?'⚠ '+opp+' has answered — your move.':opp+' is thinking…';
  if(left<=0){ tourStop(); tourSync(); }            // out of time: the server marks it and moves on
}
async function tourSync(){
  if(!tourView) return;
  const r=await casRpc('tourney_state',{tid:tourView.id},tourMsg);
  if(r&&r.ok&&r.t) tourPaint(r.t);
}
async function tourLockIn(){
  if(!tourView||!tourPicked.size) return;
  $('tourLock').classList.add('hidden');
  const r=await casRpc('tourney_answer',{tid:tourView.id,picks:[...tourPicked]},tourMsg);
  if(r&&r.ok&&r.t){
    const before=(tourView.log||[]).length;
    tourPaint(r.t);
    const e=(r.t.log||[])[before]||(r.t.status!=='active'||r.t.phase!=='play'?null:null);
    if(e){ if(e.ok) sfx.coin&&sfx.coin(); else sfx.nope&&sfx.nope(); }
  }
}
// the question just answered: the right answer, both results, and why
function tourPaintLast(v){
  const box=$('tourLast'), log=v.log||[], e=log[log.length-1];
  if(!e){ box.classList.add('hidden'); box.dataset.key=''; return; }
  const key=v.id+':'+v.round+':'+log.length; if(box.dataset.key===key) return; box.dataset.key=key;
  const q=QS[e.q]; if(!q){ box.classList.add('hidden'); return; }
  const ans=(e.ans||q.a).slice().sort(), txt=ans.map(l=>{ const o=q.o.find(x=>x[0]===l); return o?o[1]:''; }).join(' / ');
  const mark=ok=>ok?'✓':'✗', opp=tourName(v,v.opp), why=duelWhy(q);
  box.className='duellast '+(e.ok?'ok':'no');
  box.innerHTML='<div class="dlh"><span>Q'+log.length+': '+ans.join(' + ')+'</span><span class="who">you '+
    (e.pick?esc([].concat(e.pick).join('+')):'—')+' '+mark(e.ok)+(e.late?' (time)':'')+' · '+esc(opp)+' '+mark(e.bot)+'</span></div>'+
    '<div class="dim" style="margin-top:3px">'+esc(txt.length>150?txt.slice(0,150)+'…':txt)+'</div>'+
    (why?'<details><summary>Why</summary><div style="margin-top:4px">'+esc(why)+'</div></details>':'');
}
function tourPaintBracket(v){
  const res=v.results||[], mine=res.filter(r=>r.you), last=mine[mine.length-1];
  const nm=seat=>tourName(v,seat);
  const R=$('tourResult'), pay=$('tourPay');
  if(v.status==='won'){
    R.className='duelresult win'; R.textContent='CHAMPION';
    pay.className='duelpay win'; pay.textContent='+'+plural(Number(v.payout)||0,'chip')+' — the pot is yours';
    $('tourReason').textContent='Three matches, three wins'+(last?' · final '+last.sa+'–'+last.sb+' against '+nm(last.b):'');
    if(!tourPaintBracket._shown||tourPaintBracket._shown!==v.id){ tourPaintBracket._shown=v.id; sfx.rank&&sfx.rank(); celebrate(); }
  } else if(v.status==='lost'){
    const champ=(v.alive||[])[0];
    R.className='duelresult lose'; R.textContent='KNOCKED OUT';
    pay.className='duelpay lose'; pay.textContent='In the '+(TOUR_ROUND[((last&&last.round)||1)-1]||'round').toLowerCase()+(last&&last.left?' — you left':'');
    $('tourReason').textContent=(last?(last.left?'':nm(last.b)+' won '+last.sb+'–'+last.sa+' · '):'')+(champ!=null?nm(champ)+' won the tournament':'');
  } else {
    R.className='duelresult win'; R.textContent='THROUGH';
    pay.className='duelpay win'; pay.textContent='On to the '+(TOUR_ROUND[(v.round||2)-1]||'next round').toLowerCase()+' — against '+nm(v.opp);
    $('tourReason').textContent=last?'You beat '+nm(last.b)+' '+last.sa+'–'+last.sb:'';
  }
  // the bracket: every match by round, your path marked
  const box=$('tourBr');
  box.innerHTML=[1,2,3].map(rd=>{
    const ms=res.filter(r=>Number(r.round)===rd);
    return '<div class="tbcol"><div class="tbh">'+TOUR_ROUND[rd-1]+'</div>'+(ms.length?ms.map(m=>{
      const aw=Number(m.w)===Number(m.a);
      const row=(seat,sc,won)=>'<div class="tbp'+(won?' w':'')+(Number(seat)===0?' me':'')+'"><span>'+esc(nm(seat))+'</span><b>'+sc+'</b></div>';
      return '<div class="tbm'+(m.you?' you':'')+'">'+row(m.a,m.sa,aw)+row(m.b,m.sb,!aw)+'</div>';
    }).join(''):'<div class="tbm tbwait">…</div>')+'</div>';
  }).join('');
  // the last match you played, question by question
  const log=v.log||[];
  $('tourRecap').innerHTML=log.length?log.map((e,i)=>{
    const q=QS[e.q]; if(!q) return '';
    const ans=(e.ans||q.a).slice().sort();
    return '<details class="drq"><summary><span class="n">Q'+(i+1)+'</span><span class="s">'+esc(q.q)+'</span>'+
      '<span class="m">you '+(e.ok?'✓':'✗')+' · '+esc(tourName(v,last?last.b:v.opp).slice(0,8))+' '+(e.bot?'✓':'✗')+'</span></summary>'+
      '<div class="body"><div class="duelsrc">'+duelWhere(e.q)+'</div><div class="q">'+esc(q.q)+'</div>'+
      q.o.map(([l,t])=>'<div class="exrow '+(ans.includes(l)?'good':'')+'" style="margin-bottom:4px"><span class="exl">'+l+'</span><span>'+esc(t)+'</span></div>').join('')+
      '</div></details>';
  }).join(''):'';
  $('tourNext').classList.toggle('hidden',!(v.status==='active'&&v.phase==='between'));
  $('tourNext').textContent='Start the '+(TOUR_ROUND[(v.round||2)-1]||'next round').toLowerCase()+' ▸';
  $('tourAgain').textContent=v.status==='active'?'Back to the lobby':'Play another';
}
async function tourNext(){
  if(!tourView) return;
  const r=await casRpc('tourney_next',{tid:tourView.id},tourMsg);
  if(r&&r.ok&&r.t){ tourPaint(r.t); try{ $('casTour').scrollIntoView({block:'start',behavior:reduced?'auto':'smooth'}); }catch(e){} }
}
async function tourQuit(){
  if(!tourView) return;
  tourStop();
  const r=await casRpc('tourney_leave',{tid:tourView.id},tourMsg);
  if(r&&r.ok&&r.t) tourPaint(r.t);
}
$('tourStart').onclick=()=>tourStart();
$('tourResume').onclick=()=>{ if(tourView) tourPaint(tourView); };
$('tourLock').onclick=()=>tourLockIn();
$('tourNext').onclick=()=>tourNext();
$('tourAgain').onclick=()=>{ if(tourView&&tourView.status!=='active') tourView=null; tourShow('Lobby'); renderTourLobby(); };
$('tourLeave').onclick=()=>armed($('tourLeave'),'Tap again to leave — you lose your buy-in',()=>tourQuit());
$('tourExam').onchange=()=>{ tourExam=Number($('tourExam').value)||0;
  try{ localStorage.setItem('academy_tour_exam',String(tourExam)); }catch(e){} renderTourLobby(); };
$('casTabTour').onclick=()=>casTab('Tour');
renderTourLobby();

// ---------- the practice bot: the same rules, played in this page, no chips ----------""")

sub("""function rpcFile(fn){
  if(fn.indexOf('duel')===0) return 'supabase_duel.sql, then supabase_duel_v2.sql,';""",
"""function rpcFile(fn){
  if(fn.indexOf('tourney')===0) return 'supabase_tournament.sql';
  if(fn.indexOf('duel')===0) return 'supabase_duel.sql, then supabase_duel_v2.sql,';""")
sub("""const CAS_POLLS=new Set(['roulette_table','duel_state','casino_state','bj_current']);""",
"""const CAS_POLLS=new Set(['roulette_table','duel_state','casino_state','bj_current','tourney_current']);""")

sub(""".duelacts{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:12px}""",
""".duelacts{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:12px}
/* the tournament */
.tourround{text-align:center;font-family:var(--mono);font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--gold);margin-bottom:8px}
.tourbr{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:14px 0 6px;text-align:left}
.tbcol{display:flex;flex-direction:column;justify-content:space-around;gap:6px;min-width:0}
.tbh{font-family:var(--mono);font-size:9.5px;letter-spacing:.5px;text-transform:uppercase;color:var(--dim);text-align:center}
.tbm{border:1px solid var(--line);border-radius:8px;background:rgba(255,255,255,.03);overflow:hidden}
.tbm.you{border-color:color-mix(in srgb, var(--cyan) 55%, transparent)}
.tbm.tbwait{padding:10px;text-align:center;color:var(--dim)}
.tbp{display:flex;justify-content:space-between;gap:6px;padding:4px 7px;font-size:11px;color:var(--dim)}
.tbp span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tbp b{font-family:var(--mono);font-weight:650}
.tbp.w{color:var(--txt);font-weight:650}
.tbp.w b{color:var(--gold)}
.tbp.me span{color:var(--cyan)}
.tbp+.tbp{border-top:1px solid var(--line)}""")

sub("""    duelFind, duelRefresh,""","""    tourLoad, tourPaint, tourStart, tourLockIn, tourNext, tourQuit, tourSync, renderTourLobby, tourStop,
    get tourView(){return tourView;}, set tourBuyin(v){ tourBuyin=v; }, get tourPicked(){return tourPicked;},
    duelFind, duelRefresh,""")
PAGE.write_text(s, encoding="utf-8"); print("casino tournament: lobby, match board, bracket")
