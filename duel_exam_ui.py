#!/usr/bin/env python3
"""Casino duel: fix the stacked panels, play on the practice exams, and make it a game.

Reported with two screenshots: on Roulette, the Question duel panel sat underneath it.

  1. #casDuel was the one casino panel without `hidden` in the markup, so until a tab was
     tapped Roulette and Duel were both on screen. The countdown also said 30s on a 75s clock.
  2. Questions from the exams: pick "Any exam" or Exam 1-19. Each question is labelled with
     where it lives ("Exam 7 · Q23"). Matching is on the server (supabase_duel_v2.sql); a
     database still on v1 keeps working on any exam, and the lobby says what to run.
  3. After every question: its answer, what you and they picked, and why — from the server's
     history, so nothing is revealed while a question is still open.
  4. A board instead of a form: avatars, a pip per question for each side, the pot, a result
     screen that recaps all five with the answers, and a rematch.
  5. A free practice duel against a bot, played entirely in the page with no chips — most of
     the time nobody else is online to play.
  6. A duel survives leaving the casino and reloading the page: it resumes instead of the
     clock running out unseen.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

# ---------------------------------------------------------------- CSS
sub("""#duelOpts .opt{padding:12px 13px;font-size:13px}
""", """#duelOpts .opt{padding:12px 13px;font-size:13px}
#duelOpts .opt.locked{cursor:default}
/* lobby */
.duelhero{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.duelhero .ic{flex:none;width:44px;height:44px;border-radius:13px;display:grid;place-items:center;font-size:21px;
  background:linear-gradient(135deg,color-mix(in srgb, var(--cyan) 22%, transparent),color-mix(in srgb, var(--mag) 22%, transparent));
  border:1px solid var(--line2)}
.duelhero .ch-t{font-size:15px}
.duelrules{display:flex;flex-wrap:wrap;gap:6px}
.duelrules span{font-size:11.5px;padding:5px 9px;border-radius:8px;background:var(--surface);border:1px solid var(--line);color:#d3d9e2}
.duelrules b{color:var(--gold);font-weight:650}
#duelExam{width:100%;margin-bottom:12px}
.duelbtns{display:flex;flex-direction:column;gap:8px;margin-top:12px}
.duelrec{font-size:11.5px;color:var(--dim);text-align:center;min-height:16px;margin-top:6px}
/* looking for someone */
.duelradar{width:58px;height:58px;margin:8px auto 10px;border-radius:50%;position:relative;display:grid;place-items:center;
  font-size:22px;border:2px solid color-mix(in srgb, var(--cyan) 40%, transparent)}
.duelradar::after{content:"";position:absolute;inset:-2px;border-radius:50%;border:2px solid var(--cyan);animation:radar 1.6s ease-out infinite}
@keyframes radar{from{transform:scale(1);opacity:.8}to{transform:scale(1.7);opacity:0}}
/* the board */
.duelboard{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;margin-bottom:8px}
.dside{display:flex;flex-direction:column;align-items:center;gap:5px;min-width:0}
.dav{width:42px;height:42px;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:17px;
  border:2px solid var(--line2);background:var(--surface);transition:box-shadow .2s}
.dside.me .dav{border-color:var(--cyan);color:var(--cyan)}
.dside.them .dav{border-color:var(--mag);color:var(--mag)}
.dside.answered .dav{box-shadow:0 0 0 4px color-mix(in srgb, var(--lime) 35%, transparent)}
.dside.them.answered .dav{animation:pillPop .4s ease}
.dname{font-size:12px;font-weight:650;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dpips{display:flex;gap:4px}
.dpips i{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.12)}
.dpips i.ok{background:var(--lime)} .dpips i.no{background:var(--red)} .dpips i.skip{background:var(--dim)}
.dpips i.now{background:transparent;box-shadow:inset 0 0 0 2px var(--gold)}
.dscore{font-family:var(--mono);font-size:22px;font-weight:700;color:var(--gold);text-align:center;line-height:1}
.dscore small{display:block;font-size:10px;font-weight:600;color:var(--dim);letter-spacing:.5px;margin-top:5px;white-space:nowrap}
.duelsrc{font-family:var(--mono);font-size:10.5px;color:var(--dim);letter-spacing:.4px;margin-bottom:7px}
.duellast{border-radius:11px;padding:9px 11px;margin-bottom:10px;font-size:12.5px;line-height:1.5;
  border:1px solid var(--line);background:var(--surface);animation:fadeUp .3s ease}
.duellast.ok{border-color:color-mix(in srgb, var(--lime) 45%, transparent)}
.duellast.no{border-color:color-mix(in srgb, var(--red) 45%, transparent)}
.duellast .dlh{display:flex;gap:6px 10px;align-items:baseline;flex-wrap:wrap;font-weight:650}
.duellast .who{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--dim)}
.duellast details{margin-top:4px}
.duellast summary,.drq .why summary{cursor:pointer;color:var(--cyan);font-size:12px;min-height:24px;display:flex;align-items:center}
.duelleave{display:block;margin:12px auto 0}
/* result */
#duelDone .duelresult{animation:vIn .35s ease}
.duelpay{font-family:var(--mono);font-size:15px;font-weight:650;margin-top:6px}
.duelpay.win{color:var(--lime)} .duelpay.lose{color:var(--red)} .duelpay.draw{color:var(--gold)}
.duelrecap{display:flex;flex-direction:column;gap:6px;margin:12px 0 4px;text-align:left}
.drq{border:1px solid var(--line);border-radius:10px;background:rgba(255,255,255,.03)}
.drq>summary{display:flex;gap:8px;align-items:center;padding:10px;cursor:pointer;font-size:12.3px;list-style:none;min-height:44px}
.drq>summary::-webkit-details-marker{display:none}
.drq .n{font-family:var(--mono);font-size:10.5px;color:var(--dim);flex:none}
.drq .s{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#d3d9e2}
.drq .m{flex:none;font-family:var(--mono);font-size:11px;white-space:nowrap}
.drq .body{padding:0 10px 10px;font-size:12.3px;line-height:1.55}
.drq .body .q{color:#d3d9e2;margin-bottom:6px}
.duelacts{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:12px}
""")

# ---------------------------------------------------------------- markup
old_start = """      <!-- duel -->
      <div class="card" id="casDuel">"""
old_end = """          <button class="btn" id="duelAgain" style="margin-top:8px">Play again</button>
        </div>
      </div>
"""
i = s.index(old_start); j = s.index(old_end, i) + len(old_end)
s = s[:i] + """      <!-- duel -->
      <div class="card hidden" id="casDuel">
        <!-- lobby -->
        <div id="duelLobby">
          <div class="duelhero"><span class="ic">⚔️</span>
            <div><div class="ch-t">Question duel</div>
              <div class="ch-s">Practice-exam questions, head to head</div></div></div>
          <div class="duelrules"><span><b>5</b> questions</span><span><b>75 s</b> each</span>
            <span>Wrong while they're right — <b>the pot is theirs</b></span></div>
          <div class="divider"></div>
          <div class="minirow"><span class="ch-t" style="font-size:12px">Questions from</span>
            <span class="ch-s" id="duelExamNote"></span></div>
          <select class="authin" id="duelExam" aria-label="Which practice exam the questions come from"></select>
          <div class="minirow"><span class="ch-t" style="font-size:12px">Stake</span>
            <span class="ch-s">the winner takes both</span></div>
          <div class="betrow" id="duelStakes"></div>
          <div class="duelbtns">
            <button class="btn wide" id="duelFind">Find an opponent ▸</button>
            <button class="btn ghost wide" id="duelBot">🤖 Practise against the bot — free</button>
          </div>
          <div class="duelrec" id="duelBotRec"></div>
          <div class="authnote" id="duelMsg"></div>
        </div>

        <!-- waiting for someone to sit down -->
        <div id="duelWait" class="hidden" style="text-align:center;padding:6px 0">
          <div class="duelradar">⚔️</div>
          <div class="ch-t" id="duelWaitMe">Looking for an opponent…</div>
          <p class="ch-note" id="duelWaitNote">Your seat is open. Anyone who picks the same stake sits down with you.</p>
          <div class="duelacts">
            <button class="btn ghost sm" id="duelCancel">Cancel and refund</button>
            <button class="btn ghost sm" id="duelWaitBot">🤖 Play the bot instead</button>
          </div>
        </div>

        <!-- live duel -->
        <div id="duelPlay" class="hidden">
          <div class="duelboard">
            <div class="dside me" id="duelMeSide"><span class="dav" id="duelMeAv">Y</span>
              <span class="dname" id="duelMe">you</span><span class="dpips" id="duelMePips"></span></div>
            <div class="dscore"><span id="duelScore">0 — 0</span><small id="duelPot"></small></div>
            <div class="dside them" id="duelThemSide"><span class="dav" id="duelThemAv">?</span>
              <span class="dname" id="duelThem">them</span><span class="dpips" id="duelThemPips"></span></div>
          </div>
          <div class="rouhead" style="margin:6px 0 10px">
            <span class="tag" id="duelQn">Q1</span>
            <div class="roubar"><i id="duelBarFill"></i></div>
            <span class="roucount" id="duelCount">75s</span>
          </div>
          <div class="duellast hidden" id="duelLast" aria-live="polite"></div>
          <div class="qcard" style="margin-bottom:10px"><div class="duelsrc" id="duelSrc"></div><div class="qtext" id="duelQ"></div></div>
          <div class="opts" id="duelOpts"></div>
          <div class="ch-note" id="duelStatus" style="text-align:center;min-height:20px;margin-top:8px" aria-live="polite"></div>
          <button class="btn wide hidden" id="duelLock" style="margin-top:10px">Lock in</button>
          <button class="btn ghost sm duelleave" id="duelLeave">Leave the duel</button>
        </div>

        <!-- result -->
        <div id="duelDone" class="hidden" style="text-align:center;padding:6px 0">
          <div class="duelresult" id="duelResult">—</div>
          <div class="duelpay" id="duelPay"></div>
          <p class="ch-note" id="duelReason"></p>
          <div class="duelrecap" id="duelRecap"></div>
          <div class="duelacts">
            <button class="btn" id="duelAgain">Rematch ▸</button>
            <button class="btn ghost" id="duelToLobby">Back to the lobby</button>
          </div>
        </div>
      </div>
""" + s[j:]

# ---------------------------------------------------------------- JS
js_start = "// ---------- duel: two players, same questions, server holds the answer key ----------"
js_end = "renderBetRow('duelStakes',duelStake,v=>{duelStake=v;});\n"
i = s.index(js_start); j = s.index(js_end, i) + len(js_end)
s = s[:i] + r"""// ---------- duel: two players, same questions, server holds the answer key ----------
// The client renders the question from its own bank by index, but never decides who was
// right: only the server has the answers, so "answer wrong and the pot is theirs" is
// something it can actually enforce. Once a question is over the server hands back its
// answer and both picks (duel.hist), which is what the reveal and the recap are drawn from.
let duelStake=50, duelId=null, duelPoll=null, duelPicked=new Set(), duelTick=null;
// the server publishes both the countdown and its total, so this never drifts from it
let duelLeft=75, duelTotal=75;
let duelExam=0;              // 0 = any exam, else a practice exam 1..PAPER_COUNT
let duelV1=false;            // the database has not had supabase_duel_v2.sql: no exam choice
let duelLastView=null;       // for the rematch and the recap
try{ const n=Number(localStorage.getItem('academy_duel_exam')); if(n>=0&&n<=PAPER_COUNT) duelExam=Math.floor(n)||0; }catch(e){}

// where a bank question lives among the practice exams
const duelWhere=qi=>'Exam '+(Math.floor(qi/PAPER_LEN)+1)+' · Q'+(qi%PAPER_LEN+1);

function duelMsg(t,kind){ const e=$('duelMsg'); if(!e) return; e.textContent=t||''; e.className='authnote'+(kind?' '+kind:''); }
function duelShow(which){
  ['duelLobby','duelWait','duelPlay','duelDone'].forEach(id=>
    $(id).classList.toggle('hidden',id!=='duel'+which));
}
function duelStop(){
  if(duelPoll){ clearInterval(duelPoll); duelPoll=null; }
  if(duelTick){ clearInterval(duelTick); duelTick=null; }
}
function renderDuelLobby(){
  const sel=$('duelExam'); if(!sel) return;
  const opts=['<option value="0">Any exam — all '+QS.length.toLocaleString()+' questions</option>'];
  for(let n=1;n<=PAPER_COUNT;n++){
    const p=(P.papers||{})[n];
    opts.push('<option value="'+n+'">Exam '+n+(p&&p.best?' — your best '+p.best+'%':'')+'</option>');
  }
  sel.innerHTML=opts.join('');
  sel.value=String(duelExam);
  $('duelExamNote').textContent=duelExam?plural(paperQs(duelExam).length,'question')+' to draw from':'';
  const w=P.botW||0, l=P.botL||0, d=P.botD||0;
  $('duelBotRec').textContent=(w+l+d)?('Against the bot: '+w+' won · '+l+' lost'+(d?' · '+d+' drawn':'')):'';
}
// A pip per question for one side: right, wrong, skipped, the one in play, still to come.
function duelPips(el,v,side){
  const n=v.count||5, h=v.hist||[];
  el.innerHTML=Array.from({length:n},(_,i)=>{
    const e=h[i];
    if(e){ const ok=e[side+'Ok']; return '<i class="'+(ok===true?'ok':ok===false?'no':'skip')+'"></i>'; }
    return '<i'+(i===v.turn&&v.status==='active'?' class="now"':'')+'></i>';
  }).join('');
}
const duelLtrs=a=>(Array.isArray(a)&&a.length)?a.slice().sort().join(' + '):'—';
function duelWhy(q){
  if(q.x) return q.x;
  try{
    const e=buildExplain(q,q.a,true);
    const line=q.a.map(l=>e.why.byLetter[l]).filter(Boolean)[0];
    if(line) return line;
  }catch(err){}
  return '';
}
// the question that just finished: its answer, both picks, and a folded "why"
function renderDuelLast(v){
  const box=$('duelLast'), h=v.hist||[], e=h[h.length-1];
  if(!e||v.status!=='active'){ box.classList.add('hidden'); return; }
  const q=QS[e.q]; if(!q){ box.classList.add('hidden'); return; }
  const key=v.id+':'+h.length;
  if(box.dataset.key===key) return;              // already showing this one
  box.dataset.key=key;
  const ans=(e.answer||q.a).slice().sort();
  const txt=ans.map(l=>{ const o=q.o.find(x=>x[0]===l); return o?o[1]:''; }).join(' / ');
  const mark=ok=>ok===true?'✓':ok===false?'✗':'—';
  box.className='duellast '+(e.youOk?'ok':'no');
  const why=duelWhy(q);
  box.innerHTML='<div class="dlh"><span>Q'+h.length+': '+ans.join(' + ')+'</span>'+
    '<span class="who">you '+duelLtrs(e.you)+' '+mark(e.youOk)+' · '+esc(v.them.name||'them')+' '+duelLtrs(e.them)+' '+mark(e.themOk)+'</span></div>'+
    '<div class="dim" style="margin-top:3px">'+esc(txt.length>150?txt.slice(0,150)+'…':txt)+'</div>'+
    (why?'<details><summary>Why</summary><div style="margin-top:4px">'+esc(why)+'</div></details>':'');
  if(e.youOk) sfx.coin&&sfx.coin(); else if(e.youOk===false) sfx.nope&&sfx.nope();
}
function renderDuelQuestion(d){
  const qi=d.question;
  const q=QS[qi];
  if(!q){ $('duelQ').textContent='Question unavailable on this build.'; $('duelOpts').innerHTML=''; $('duelSrc').textContent=''; return; }
  $('duelQn').textContent='Q'+(d.turn+1)+' of '+(d.count||5);
  $('duelSrc').textContent=duelWhere(qi)+(q.a.length>1?' · choose '+q.a.length:'');
  // the same question repainted every poll must not rebuild the options under a finger
  const key=d.id+':'+d.turn+':'+(d.you.answered?1:0);
  const box=$('duelOpts');
  if(box.dataset.key!==key){
    box.dataset.key=key;
    $('duelQ').textContent=q.q;
    const need=q.a.length;
    box.innerHTML='';
    q.o.forEach(([ltr,txt])=>{
      const b=document.createElement('button');
      b.className='opt'+(duelPicked.has(ltr)?' sel':'')+(d.you.answered?' locked':''); b.dataset.ltr=ltr;
      b.innerHTML='<span class="ltr">'+ltr+'</span><span>'+esc(txt)+'</span>';
      b.onclick=()=>{
        if(d.you.answered) return;
        if(duelPicked.has(ltr)) duelPicked.delete(ltr);
        else {
          if(need===1) duelPicked.clear();
          if(duelPicked.size>=need){ pickFull(need,b); return; }
          duelPicked.add(ltr);
        }
        [...box.children].forEach(el=>el.classList.toggle('sel',duelPicked.has(el.dataset.ltr)));
        $('duelLock').classList.toggle('hidden',duelPicked.size!==need);
      };
      box.appendChild(b);
    });
    $('duelLock').textContent=need>1?('Lock in '+plural(need,'answer')+''):'Lock in';
  }
  $('duelLock').classList.toggle('hidden',duelPicked.size!==q.a.length||d.you.answered);
}
function paintDuel(d){
  if(!d) return;
  duelLastView=d;
  if(d.status==='waiting'){
    duelShow('Wait');
    $('duelWaitMe').textContent='Looking for an opponent…';
    $('duelWaitNote').textContent='Your seat is open at '+plural(d.stake,'chip')+
      (d.exam?' on Exam '+d.exam:'')+'. Anyone who picks the same stake sits down with you.';
    return;
  }
  if(d.status==='active'){
    duelShow('Play');
    const me=d.you.name||'you', them=d.them.name||'opponent';
    $('duelMe').textContent=me; $('duelThem').textContent=them;
    $('duelMeAv').textContent=d.bot?'🙂':String(me).charAt(0).toUpperCase();
    $('duelThemAv').textContent=d.bot?'🤖':String(them).charAt(0).toUpperCase();
    $('duelMeSide').classList.toggle('answered',!!d.you.answered);
    $('duelThemSide').classList.toggle('answered',!!d.them.answered);
    $('duelScore').textContent=d.you.score+' — '+d.them.score;
    $('duelPot').textContent=d.bot?'PRACTICE':'POT '+(d.stake*2);
    duelPips($('duelMePips'),d,'you'); duelPips($('duelThemPips'),d,'them');
    // key on the duel as well as the turn: a new duel also starts at turn 0
    const mark=d.id+':'+d.turn;
    if(mark!==paintDuel._mark){ duelPicked.clear(); paintDuel._mark=mark; }
    renderDuelLast(d);
    renderDuelQuestion(d);
    if(typeof d.secondsTotal==='number'&&d.secondsTotal>0) duelTotal=d.secondsTotal;
    if(typeof d.secondsLeft==='number'){ duelLeft=d.secondsLeft; duelPaintClock(); }
    $('duelStatus').textContent = d.you.answered
      ? (d.them.answered?'Both in — scoring…':'Locked in. Waiting for '+them+'…')
      : (d.them.answered?'⚠ '+them+' has answered — your move.':'Pick your answer.');
    // the leave button confirms by relabelling itself; a repaint must not undo that mid-tap
    if(!$('duelLeave').dataset.armed) $('duelLeave').textContent='Leave the duel';
    return;
  }
  if(d.status==='done'){
    duelShow('Done');
    duelStop();
    const won=d.youWon, draw=!d.winner;
    $('duelResult').className='duelresult '+(draw?'draw':won?'win':'lose');
    $('duelResult').textContent=draw?'DRAW':won?'YOU WIN':'YOU LOSE';
    const pay=$('duelPay');
    pay.className='duelpay '+(draw?'draw':won?'win':'lose');
    pay.textContent=d.bot?(draw?'Level with the bot':won?'You beat the bot':'The bot wins this one')
                         :(draw?'Stakes returned':won?'+'+plural(d.stake,'chip'):'−'+plural(d.stake,'chip'));
    $('duelReason').textContent=(d.reason||'')+' · '+d.you.score+'–'+d.them.score;
    renderDuelRecap(d);
    $('duelAgain').textContent=d.bot?'Play the bot again ▸':'Rematch — '+plural(d.stake,'chip')+' ▸';
    if(won){ sfx.rank&&sfx.rank(); celebrate(); } else if(!draw) sfx.wrong();
    duelId=null;
    if(!d.bot) casRefresh();
  }
}
// all five, with the answer and both picks; tap one for the question and why
function renderDuelRecap(d){
  const box=$('duelRecap'), h=d.hist||[];
  if(!h.length){ box.innerHTML=''; return; }
  const mark=ok=>ok===true?'<span style="color:var(--lime)">✓</span>':ok===false?'<span style="color:var(--red)">✗</span>':'<span class="dim">—</span>';
  box.innerHTML=h.map((e,i)=>{
    const q=QS[e.q]; if(!q) return '';
    const ans=(e.answer||q.a).slice().sort();
    const why=duelWhy(q);
    return '<details class="drq"><summary><span class="n">Q'+(i+1)+'</span><span class="s">'+esc(q.q)+'</span>'+
      '<span class="m">'+mark(e.youOk)+' '+mark(e.themOk)+'</span></summary><div class="body">'+
      '<div class="duelsrc">'+duelWhere(e.q)+'</div><div class="q">'+esc(q.q)+'</div>'+
      q.o.map(([l,t])=>'<div class="exrow '+(ans.includes(l)?'good':'')+'" style="margin-bottom:4px"><span class="exl">'+l+'</span><span>'+esc(t)+'</span></div>').join('')+
      '<div class="dim" style="margin-top:6px">You picked '+duelLtrs(e.you)+' · '+esc(d.them.name||'them')+' picked '+duelLtrs(e.them)+'</div>'+
      (why?'<div style="margin-top:6px"><b>Why</b> '+esc(why)+'</div>':'')+
      '</div></details>';
  }).join('');
}
function duelPaintClock(){
  $('duelCount').textContent=duelLeft+'s';
  $('duelBarFill').style.width=pctW((duelLeft/duelTotal)*100);
  $('duelCount').classList.toggle('closing',duelLeft<=10);
  $('duelBarFill').parentElement.classList.toggle('closing',duelLeft<=10);
}
async function duelRefresh(){
  if(!duelId) return;
  if(bot&&duelId===bot.id){ botTick(); return; }
  const r=await casRpc('duel_state',{duel:duelId},duelMsg);
  if(!r||!r.ok) return;
  paintDuel(r.duel);
}
function duelRun(){
  duelStop();
  const isBot=bot&&duelId===bot.id;
  duelPoll=setInterval(duelRefresh,isBot?500:1500);
  duelTick=setInterval(()=>{
    if(isBot) return;                               // the bot's clock is repainted by botTick
    if(duelLeft>0){ duelLeft--; duelPaintClock(); }
  },1000);
}
async function duelFind(){
  if(bot&&bot.status==='active') botAbandon();
  if(casChips<duelStake){ duelMsg('Not enough chips for that stake.','bad'); return; }
  duelMsg('Looking for an opponent…','busy');
  let r=null;
  if(!duelV1){
    r=await casRpc('duel_find',{stake:duelStake,exam:duelExam},duelMsg,{missingOk:true});
    if(r==='missing'){ duelV1=true; r=null; }
  }
  if(duelV1) r=await casRpc('duel_find',{stake:duelStake},duelMsg);
  if(!r){ if(/Looking/.test($('duelMsg').textContent)) duelMsg('Could not start a duel — see above.','bad'); return; }
  if(!r.ok){ duelMsg(r.reason,'bad'); return; }
  duelMsg(duelV1&&duelExam?'Playing on any exam — choosing one needs supabase_duel_v2.sql in the Supabase SQL editor.':'',duelV1&&duelExam?'bad':'');
  duelId=r.duel.id;
  paintDuel._mark=null; duelPicked.clear();
  paintDuel(r.duel);
  duelRun();
}
async function duelLockIn(){
  if(!duelId||!duelPicked.size) return;
  if(bot&&duelId===bot.id){ botPlayerAnswer([...duelPicked]); return; }
  const r=await casRpc('duel_answer',{duel:duelId,picks:[...duelPicked]},duelMsg);
  if(r&&r.ok){ paintDuel(r.duel); $('duelLock').classList.add('hidden'); }
}
async function duelQuit(){
  if(!duelId) return;
  if(bot&&duelId===bot.id){ botFinish('them','you left'); return; }
  const id=duelId;
  duelStop();
  // a poll still in flight holds casBusy, and casRpc would drop the leave without a word
  for(let i=0;i<30&&casBusy;i++) await new Promise(r=>setTimeout(r,100));
  await casRpc('duel_leave',{duel:id},duelMsg);
  // a live duel ends in a result, with its recap; an empty seat just goes back to the lobby
  const r=await casRpc('duel_state',{duel:id},duelMsg);
  if(r&&r.ok&&r.duel&&r.duel.status==='done'){ paintDuel(r.duel); return; }
  duelId=null; duelShow('Lobby'); renderDuelLobby(); casRefresh();
}
// A duel outlives the screen: leaving the casino stopped the polling and a reload lost the
// id, so the clock ran out unseen and the stake went with it. Pick it back up.
async function duelResume(){
  if(duelId){ duelRun(); duelRefresh(); return; }
  if(!sb||!sbUser) return;
  try{
    const {data}=await sb.from('duels').select('id,status')
      .or('a.eq.'+sbUser.id+',b.eq.'+sbUser.id).in('status',['waiting','active'])
      .order('created_at',{ascending:false}).limit(1);
    const row=data&&data[0];
    if(!row||duelId) return;
    duelId=row.id; paintDuel._mark=null; duelPicked.clear();
    casTab('Duel');
    await duelRefresh(); duelRun();
  }catch(e){}
}

// ---------- the practice bot: the same rules, played in this page, no chips ----------
// Most of the time nobody else is online. The bot plays by the server's rules — five
// questions, 75 seconds, wrong-while-right ends it — but it is only practice, so nothing is
// staked and nothing goes to the server.
const BOT_NAME='Byte', BOT_SKILL=0.62, DUEL_SECS=75;
let bot=null;
function botStart(){
  duelStop();
  const pool=duelExam?paperQs(duelExam):QS.map((_,i)=>i);
  const qs=[]; const left=pool.slice();
  while(qs.length<5&&left.length) qs.push(left.splice(Math.floor(Math.random()*left.length),1)[0]);
  bot={id:'bot-'+Date.now(), qs, turn:0, exam:duelExam, status:'active', winner:null, reason:'',
       you:{score:0,pick:null,ok:null}, them:{score:0,pick:null,ok:null}, hist:[],
       start:Date.now(), botAt:botDelay()};
  duelId=bot.id; paintDuel._mark=null; duelPicked.clear(); duelMsg('');
  casTab('Duel');
  paintDuel(botView()); duelRun();
}
const botDelay=()=>6000+Math.random()*30000;       // it reads, too
function botPick(q){
  if(Math.random()<BOT_SKILL) return q.a.slice();
  const wrong=q.o.map(o=>o[0]).filter(l=>!q.a.includes(l));
  const pick=q.a.slice(1);                            // a multi-answer miss keeps some of it
  while(pick.length<q.a.length&&wrong.length) pick.push(wrong.splice(Math.floor(Math.random()*wrong.length),1)[0]);
  return pick;
}
const botSame=(a,b)=>a.length===b.length&&a.every(x=>b.includes(x));
function botView(){
  const b=bot, now=Date.now();
  return {id:b.id, bot:true, status:b.status, stake:0, turn:b.turn, exam:b.exam, count:b.qs.length,
    question:b.status==='active'?b.qs[b.turn]:null,
    you:{name:myName||'you', score:b.you.score, answered:b.you.pick!==null},
    them:{name:BOT_NAME, score:b.them.score, answered:b.them.pick!==null},
    hist:b.hist.slice(), secondsTotal:DUEL_SECS,
    secondsLeft:b.status==='active'?Math.max(0,DUEL_SECS-Math.floor((now-b.start)/1000)):null,
    winner:b.winner, reason:b.reason, youWon:b.winner==='you'};
}
function botLog(){
  const b=bot; if(b.hist.length>b.turn) return;
  const q=QS[b.qs[b.turn]];
  b.hist.push({q:b.qs[b.turn], answer:q.a.slice(), you:b.you.pick, them:b.them.pick, youOk:b.you.ok, themOk:b.them.ok});
}
function botFinish(win,why){
  const b=bot; if(!b||b.status!=='active') return;
  botLog();
  b.status='done'; b.winner=win; b.reason=why;
  if(win==='you') P.botW=(P.botW||0)+1; else if(win==='them') P.botL=(P.botL||0)+1; else P.botD=(P.botD||0)+1;
  saveProfile();
  paintDuel(botView());
}
function botNext(){
  const b=bot;
  botLog();
  if(b.turn+1>=b.qs.length){
    if(b.you.score>b.them.score) botFinish('you','higher score');
    else if(b.them.score>b.you.score) botFinish('them','higher score');
    else botFinish(null,'draw');
    return;
  }
  b.turn++; b.you={score:b.you.score,pick:null,ok:null}; b.them={score:b.them.score,pick:null,ok:null};
  b.start=Date.now(); b.botAt=botDelay();
  paintDuel(botView());
}
// the server's rule: one right and one wrong ends it there; otherwise the next question
function botResolve(){
  const b=bot;
  if(b.you.pick===null||b.them.pick===null) return;
  if(b.you.ok&&!b.them.ok) botFinish('you','the bot answered wrong');
  else if(b.them.ok&&!b.you.ok) botFinish('them','you answered wrong');
  else botNext();
}
function botPlayerAnswer(picks){
  const b=bot; if(!b||b.status!=='active'||b.you.pick!==null) return;
  const q=QS[b.qs[b.turn]];
  b.you.pick=picks.slice(); b.you.ok=botSame(picks,q.a);
  if(b.you.ok) b.you.score++;
  // an answer in hand hurries the bot along: nobody waits half a minute on it
  if(b.them.pick===null) b.botAt=Math.min(b.botAt,Date.now()-b.start+1200+Math.random()*2500);
  paintDuel(botView());
  botResolve();
}
function botTick(){
  const b=bot; if(!b||b.status!=='active') return;
  const el=Date.now()-b.start;
  if(b.them.pick===null&&el>=b.botAt){
    const q=QS[b.qs[b.turn]];
    b.them.pick=botPick(q); b.them.ok=botSame(b.them.pick,q.a);
    if(b.them.ok) b.them.score++;
    botResolve();
    if(b.status!=='active') return;
  }
  if(el>=DUEL_SECS*1000){
    if(b.you.pick===null&&b.them.pick!==null){ botFinish('them','you ran out of time'); return; }
    if(b.you.pick===null&&b.them.pick===null){ botNext(); return; }
  }
  paintDuel(botView());
}
function botAbandon(){ if(bot&&bot.status==='active'){ bot.status='done'; } if(bot&&duelId===bot.id){ duelId=null; duelStop(); } }

$('duelFind').onclick=()=>duelFind();
$('duelBot').onclick=()=>botStart();
$('duelWaitBot').onclick=async()=>{ await duelQuit(); botStart(); };
$('duelLock').onclick=()=>duelLockIn();
$('duelCancel').onclick=()=>duelQuit();
$('duelLeave').onclick=()=>{
  const isBot=bot&&duelId===bot.id;
  armed($('duelLeave'),isBot?'Tap again to leave — the bot takes it':'Tap again to leave — you lose '+plural((duelLastView&&duelLastView.stake)||0,'chip'),()=>duelQuit());
};
$('duelAgain').onclick=()=>{
  const was=duelLastView;
  if(was&&was.bot){ botStart(); return; }
  duelShow('Lobby'); renderDuelLobby(); duelFind();
};
$('duelToLobby').onclick=()=>{ duelShow('Lobby'); duelMsg(''); renderDuelLobby(); };
$('duelExam').onchange=()=>{
  duelExam=Number($('duelExam').value)||0;
  try{ localStorage.setItem('academy_duel_exam',String(duelExam)); }catch(e){}
  renderDuelLobby();
};
renderBetRow('duelStakes',duelStake,v=>{duelStake=v;});
renderDuelLobby();
""" + s[j:]

# ---------------------------------------------------------------- casRpc: let a caller handle "not installed"
sub("""async function casRpc(fn,args,say){
  const tell=say||casMsg;""",
"""async function casRpc(fn,args,say,opts){
  const tell=say||casMsg;""")
sub("""      if(/could not find the function|schema cache|does not exist/i.test(error.message||''))
        tell(""",
"""      if(/could not find the function|schema cache|does not exist/i.test(error.message||'')){
        if(opts&&opts.missingOk) return 'missing';
        tell(""")
sub("""run '+rpcFile(fn)+' in the Supabase SQL editor.','bad');
      else tell(humanError(error),'bad');""",
"""run '+rpcFile(fn)+' in the Supabase SQL editor.','bad');
      }
      else tell(humanError(error),'bad');""")
sub("""  if(fn.indexOf('duel')===0) return 'supabase_duel.sql';""",
"""  if(fn.indexOf('duel')===0) return 'supabase_duel.sql, then supabase_duel_v2.sql,';""")

# ---------------------------------------------------------------- entering the casino picks a duel back up
sub("""  if(sbUser&&!$('casRoul').classList.contains('hidden')) rouStart();
};""",
"""  if(sbUser&&!$('casRoul').classList.contains('hidden')) rouStart();
  renderDuelLobby();
  if(duelId||sbUser) duelResume();
};""")

# bot record merges like the other counters, and survives a malformed profile
sub("""                'bestMock','reviewCleared','studyOpened','skill','sims','simsPassed','bestSim'];""",
"""                'bestMock','reviewCleared','studyOpened','skill','sims','simsPassed','bestSim',
                'botW','botL','botD'];""")
sub("""                 'exams','examsPassed','reviewCleared','studyOpened','dailyStreak'];""",
"""                 'exams','examsPassed','reviewCleared','studyOpened','dailyStreak','botW','botL','botD'];""")

# test surface
sub("""    duelFind, duelRefresh, duelLockIn, duelQuit, paintDuel, duelShow,""",
"""    duelFind, duelRefresh, duelLockIn, duelQuit, paintDuel, duelShow, duelWhere, renderDuelLobby,
    botStart, botTick, botPlayerAnswer, get bot(){return bot;}, get duelExam(){return duelExam;},
    set duelExam(v){ duelExam=v; }, get duelLastView(){return duelLastView;}, duelResume,""")

PAGE.write_text(s, encoding="utf-8"); print("duel: exams, reveal, board, bot, resume")

# ---- second pass: the "why" is the question's own write-up; the board scrolls into view ----
s = PAGE.read_text(encoding="utf-8")
sub("""function duelWhy(q){
  if(q.x) return q.x;
  try{
    const e=buildExplain(q,q.a,true);
    const line=q.a.map(l=>e.why.byLetter[l]).filter(Boolean)[0];
    if(line) return line;
  }catch(err){}
  return '';
}""","""// The write-up covers every option, which is the point after a duel question: why the answer
// wins AND why the one you picked does not. The per-letter split is often empty for the
// right answer, so it is only the fallback.
function duelWhy(q){
  if(q.w) return q.w;
  if(q.x) return q.x;
  try{
    const e=buildExplain(q,q.a,true);
    const line=q.a.map(l=>e.why.byLetter[l]).filter(Boolean)[0];
    if(line) return line;
  }catch(err){}
  return '';
}
// the lobby sits below the chips card, so the board that replaces it can open off screen
function duelIntoView(){
  try{ $('casDuel').scrollIntoView({block:'start',behavior:reduced?'auto':'smooth'}); }catch(e){}
}""")
sub("""#duelOpts .opt.locked{cursor:default}
""","""#duelOpts .opt.locked{cursor:default}
#casDuel{scroll-margin-top:calc(var(--topH, 64px) + 10px)}
""")
sub("""  casTab('Duel');
  paintDuel(botView()); duelRun();
}""","""  casTab('Duel');
  paintDuel(botView()); duelRun(); duelIntoView();
}""")
sub("""  paintDuel._mark=null; duelPicked.clear();
  paintDuel(r.duel);
  duelRun();
}""","""  paintDuel._mark=null; duelPicked.clear();
  paintDuel(r.duel);
  duelRun(); duelIntoView();
}""")
PAGE.write_text(s, encoding="utf-8"); print("why from the write-up; board scrolls into view")

# ---- third pass: the recap says whose mark is whose ----
s = PAGE.read_text(encoding="utf-8")
sub("""      '<span class="m">'+mark(e.youOk)+' '+mark(e.themOk)+'</span></summary><div class="body">'+""",
"""      '<span class="m">you '+mark(e.youOk)+' · '+esc(them)+' '+mark(e.themOk)+'</span></summary><div class="body">'+""")
sub("""  const mark=ok=>ok===true?'<span style="color:var(--lime)">✓</span>':ok===false?'<span style="color:var(--red)">✗</span>':'<span class="dim">—</span>';
  box.innerHTML=h.map((e,i)=>{""",
"""  const mark=ok=>ok===true?'<span style="color:var(--lime)">✓</span>':ok===false?'<span style="color:var(--red)">✗</span>':'<span class="dim">—</span>';
  const nm=String(d.them.name||'them'), them=nm.length>8?nm.slice(0,7)+'…':nm;
  box.innerHTML=h.map((e,i)=>{""")
PAGE.write_text(s, encoding="utf-8"); print("recap marks labelled")

# ---- fourth pass: the "Why" toggle is a real tap target at 320px ----
s = PAGE.read_text(encoding="utf-8")
sub(""".duellast summary,.drq .why summary{cursor:pointer;color:var(--cyan);font-size:12px;min-height:24px;display:flex;align-items:center}""",
""".duellast summary{cursor:pointer;color:var(--cyan);font-size:12px;min-height:34px;display:flex;align-items:center}""")
PAGE.write_text(s, encoding="utf-8"); print("why toggle 34px")

# ---- fifth pass: a roulette spin with nothing to land on stops ----
# Found testing signed in: the wheel said "No more bets — spinning…" round after round. The
# server never had a result for a round nobody bet on (fixed in supabase_duel_v2.sql); until
# that runs, and whenever a result is slow, the wheel gives up after a few seconds.
s = PAGE.read_text(encoding="utf-8")
sub("""    rouSpinningFor=null;
  }
}
async function rouRefresh(){""","""    rouSpinningFor=null;
  }
  // no result to land on: stop spinning and wait for the next round rather than spin forever
  if(rouPhase==='spinning'&&rouSpinningFor&&Date.now()-rouSpinningFor>7000){
    rouSpinningFor=null; rouSetPhase('betting');
    $('rouPocket').textContent='—';
    $('rouResult').textContent='Waiting for the table…';
  }
}
async function rouRefresh(){""")
sub("""    paintRouTable, rouSetPhase, get rouPhase(){return rouPhase;},""",
"""    paintRouTable, rouSetPhase, get rouPhase(){return rouPhase;}, set rouSpinningFor(v){ rouSpinningFor=v; },""")
PAGE.write_text(s, encoding="utf-8"); print("roulette spin gives up")
