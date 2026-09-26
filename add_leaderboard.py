#!/usr/bin/env python3
"""A weekly leaderboard on the home page: every player, by correct answers this week.

Asked for (in Hebrew): on the home page, a top leaderboard of all users by how many questions
they answered correctly this week.

  - The count. Nothing counted correct answers by week — the weekly challenge counts every
    answer, right or wrong. P.wk = {key: weekKey(), dev: {deviceId: n}} counts correct answers
    wherever P.correct does (the question screens, and an exam's right answers when it is
    submitted). Per device, because two devices in one week must add up: a single number
    would have let the later save's total replace the other device's, and the merge takes each
    device's larger count. A new week (the app's own week, Sunday to Saturday, as the weekly
    challenge) starts from nothing; an older week from another device never replaces a newer.
  - The board. Profiles are private, so a server function (supabase_leaderboard.sql) reads them
    with the owner's rights and returns only rank, username and count. The card shows the top
    ten, marks you, and adds your own row when you are below the ten. Your own count is shown
    from this device the moment you answer, not when the next sync lands.
  - Signed out it says what signing in gets you; without the SQL installed it says what to run.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

# ---------------------------------------------------------------- the count
sub("""// ================= WEEKLY CHALLENGE =================""","""// ================= CORRECT ANSWERS THIS WEEK =================
// Counted per device and summed: a phone and a desktop in the same week add up, and the merge
// keeps each device's larger count instead of one device's total over the other's.
const wkNum=k=>{ const m=/^(\\d{4})-w(\\d{1,2})$/.exec(String(k||'')); return m?Number(m[1])*100+Number(m[2]):0; };
function wkState(){
  const k=weekKey();
  const cur=(P.wk&&typeof P.wk==='object')?P.wk:null;
  // a week newer than this device's clock (another device, another timezone) is kept, not reset
  if(!cur||!cur.key||wkNum(cur.key)<wkNum(k)) P.wk={key:k,dev:{}};
  if(!P.wk.dev||typeof P.wk.dev!=='object'||Array.isArray(P.wk.dev)) P.wk.dev={};
  return P.wk;
}
function wkBump(n){
  n=Math.floor(Number(n)||0); if(n<=0) return;
  const w=wkState(); w.dev[DEVICE_ID]=(Number(w.dev[DEVICE_ID])||0)+n;
}
function wkCorrect(){
  const w=wkState();
  if(w.key!==weekKey()) return 0;
  return Object.values(w.dev).reduce((a,v)=>a+(Number(v)>0?Math.floor(Number(v)):0),0);
}
// the newer week wins outright; the same week keeps every device, each at its larger count
function wkMerge(x,y){
  const ok=o=>o&&typeof o==='object'&&!Array.isArray(o)&&wkNum(o.key)?o:null;
  x=ok(x); y=ok(y);
  if(!x||!y) return x||y||undefined;
  if(x.key!==y.key) return wkNum(x.key)>wkNum(y.key)?x:y;
  const dev={};
  [x.dev,y.dev].forEach(d=>Object.entries(d&&typeof d==='object'?d:{}).forEach(([k,v])=>{
    const n=Number(v)>0?Math.floor(Number(v)):0; dev[k]=Math.max(dev[k]||0,n); }));
  return {key:x.key,dev};
}

// ================= WEEKLY LEADERBOARD =================
let lbCache=null, lbAt=0, lbBusy=false, lbState='';
async function lbFetch(force){
  if(typeof sb==='undefined'||!sb||!sbUser){ lbState='guest'; lbCache=null; return; }
  if(lbBusy||(!force&&Date.now()-lbAt<60000&&lbCache)) return;
  lbBusy=true;
  try{
    const {data,error}=await sb.rpc('leaderboard_week',{wk:weekKey(),lim:10});
    if(error){
      lbState=/could not find the function|schema cache|does not exist/i.test(error.message||'')?'missing':'error';
      lbCache=null;
    } else if(data&&data.ok){ lbState='ok'; lbCache=data; lbAt=Date.now(); }
    else { lbState='error'; lbCache=null; }
  }catch(e){ lbState='error'; }
  finally{ lbBusy=false; }
  if(route==='homeScreen') renderLeaderboard();
}
function renderLeaderboard(fetchToo){
  const L=$('lbList'), note=$('lbNote'); if(!L||!note) return;
  const mine=wkCorrect();
  $('lbSub').textContent='correct answers \\u00b7 you: '+mine;
  L.innerHTML=''; note.textContent='';
  $('lbSignIn').classList.add('hidden');
  if(fetchToo) lbFetch(false);
  if(!(typeof sbUser!=='undefined'&&sbUser)){
    note.textContent='Sign in to see where you stand this week — and to be on the board.';
    $('lbSignIn').classList.remove('hidden');
    return;
  }
  if(lbState==='missing'){ note.textContent='The leaderboard is not installed yet — run supabase_leaderboard.sql in the Supabase SQL editor.'; return; }
  if(!lbCache){ note.textContent=lbState==='error'?'Could not load the leaderboard — it will try again.':'Loading\\u2026'; return; }
  const rows=(lbCache.top||[]).slice();
  // your own number is this device's, straight away — the board catches up on the next sync
  let meShown=false;
  const add=(r,gap)=>{
    const d=document.createElement('div');
    d.className='lbrow'+(r.me?' me':'')+(gap?' gap':'');
    const rk=Number(r.rank)||0;
    d.innerHTML='<span class="lbrk"></span><span class="lbnm"></span><span class="lbc"></span>';
    d.querySelector('.lbrk').textContent=rk===1?'\\u{1f947}':rk===2?'\\u{1f948}':rk===3?'\\u{1f949}':'#'+rk;
    d.querySelector('.lbnm').textContent=(r.name||'player')+(r.me?' (you)':'');
    d.querySelector('.lbc').textContent=r.me?Math.max(Number(r.c)||0,mine):(Number(r.c)||0);
    L.appendChild(d);
  };
  rows.forEach(r=>{ if(r.me) meShown=true; add(r,false); });
  if(!meShown&&lbCache.me) add({rank:lbCache.me.rank,name:'you',c:lbCache.me.c,me:true},true);
  if(!rows.length) note.textContent=mine?'Your answers are on their way to the board.':'Nobody has a correct answer yet this week — be the first.';
  else note.textContent=plural(Number(lbCache.players)||rows.length,'player')+' this week \\u00b7 resets on Sunday';
}

// ================= WEEKLY CHALLENGE =================""")

sub("""  if(ok){
    P.correct++; st.c++; P.streak++;""","""  if(ok){
    P.correct++; st.c++; P.streak++; wkBump(1);""")
sub("""  if(cont){ P.correct+=gain; }
  else { P.answered+=len; P.correct+=correct; checkChest(); renderChest(); }""",
"""  if(cont){ P.correct+=gain; wkBump(gain); }
  else { P.answered+=len; P.correct+=correct; wkBump(correct); checkChest(); renderChest(); }""")

# the merge keeps both devices' counts
sub("""  out.upgrades=Object.assign({},a.upgrades||{},b.upgrades||{});""",
"""  out.upgrades=Object.assign({},a.upgrades||{},b.upgrades||{});
  { const w=wkMerge(a.wk,b.wk); if(w) out.wk=w; else delete out.wk; }""")

# ---------------------------------------------------------------- the card
sub("""    <div class="sechead">Next goals</div>""","""    <div class="sechead">This week</div>
    <div class="card accent-cyan" id="lbCard">
      <div class="cardhead"><span class="ch-t">🏆 Top this week</span><span class="ch-s" id="lbSub">correct answers</span></div>
      <div class="lblist" id="lbList"></div>
      <div class="ch-note" id="lbNote"></div>
      <button class="btn ghost sm hidden" id="lbSignIn" style="margin-top:8px">Sign in ›</button>
    </div>

    <div class="sechead">Next goals</div>""")
sub("""function renderHome(){
  if(typeof renderGoals==='function'){ renderGoals(); renderWeek(); renderTomorrow(); }""",
"""function renderHome(){
  if(typeof renderGoals==='function'){ renderGoals(); renderWeek(); renderTomorrow(); }
  if(typeof renderLeaderboard==='function') renderLeaderboard(true);""")
sub("""$('redoMkGo').onclick=()=>openMistakes();""","""$('redoMkGo').onclick=()=>openMistakes();
$('lbSignIn').onclick=()=>{ renderAuth(); go('authScreen'); };""")
sub(""".rdtools{display:flex;justify-content:flex-end;margin:2px 0 8px}""",""".rdtools{display:flex;justify-content:flex-end;margin:2px 0 8px}
/* the weekly leaderboard */
.lblist{display:flex;flex-direction:column;gap:4px;margin-top:4px}
.lbrow{display:grid;grid-template-columns:38px 1fr auto;align-items:center;gap:8px;padding:7px 10px;border-radius:10px;
  background:rgba(255,255,255,.03);border:1px solid var(--line);font-size:13px}
.lbrow.me{border-color:color-mix(in srgb, var(--cyan) 50%, transparent);background:color-mix(in srgb, var(--cyan) 9%, transparent)}
.lbrow.gap{margin-top:8px}
.lbrk{font-family:var(--mono);font-size:12.5px;font-weight:650;text-align:center;color:var(--dim)}
.lbnm{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}
.lbc{font-family:var(--mono);font-weight:700;color:var(--gold)}
#lbSignIn.hidden{display:none}""")

sub("""    examLabel, mistakeSet, mistakeStats, histViewsRefresh,""",
"""    examLabel, mistakeSet, mistakeStats, histViewsRefresh,
    wkState, wkBump, wkCorrect, wkMerge, wkNum, weekKey, lbFetch, renderLeaderboard, get lbState(){return lbState;},""")
PAGE.write_text(s, encoding="utf-8"); print("weekly leaderboard: per-device weekly count, merge, server board, home card")

# ---- second pass: your own row carries your name, not "you (you)" ----
s = PAGE.read_text(encoding="utf-8")
sub("""    d.querySelector('.lbnm').textContent=(r.name||'player')+(r.me?' (you)':'');""",
"""    d.querySelector('.lbnm').textContent=r.me?((r.name&&r.name!=='you'?r.name:'You')+(r.name&&r.name!=='you'?' (you)':'')):(r.name||'player');""")
sub("""  if(!meShown&&lbCache.me) add({rank:lbCache.me.rank,name:'you',c:lbCache.me.c,me:true},true);""",
"""  if(!meShown&&lbCache.me) add({rank:lbCache.me.rank,name:(typeof myName!=='undefined'&&myName)||'you',c:lbCache.me.c,me:true},true);""")
PAGE.write_text(s, encoding="utf-8"); print("your row carries your name")
