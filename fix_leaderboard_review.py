#!/usr/bin/env python3
"""Weekly leaderboard: what the four-lens review confirmed (10 of 17 findings, 5 distinct).

  1. The week turned over on Saturday. weekKey() (the weekly challenge's) counts fractional days
     from Jan 1, so the key moved at the start of Saturday (01:00 in summer time), and the
     week around New Year split in three — while the card said "resets on Sunday". The board
     now keys a week by the date of its Sunday, from whole calendar days: '2026-09-20'. It
     cannot drift with the time of day, DST or the year. Keys in the old form are dropped (a
     count restarts once), and the SQL takes only the new form.
  2. The cached board was nobody's in particular: sign out and sign someone else in within a
     minute on one device, and they saw the first person's board with that person's rank
     marked as theirs. The cache is now held for one user id, cleared on sign-out and on any
     change of user, and a response that lands for a user who is no longer signed in is dropped.
  3. After answering, your count was new and your rank old: the board could be fetched between
     your answers and their upload, then cached for a minute. It refetches after every
     successful upload, and a cached board that is behind your own count is treated as stale.
     A count the board has not seen yet gets a row of its own instead of vanishing.
  4. Signed in, every page load first said "Sign in": the card was drawn before the session was
     read. Until the session is known it says Loading, and it redraws as soon as it is.
  5. A device with its date far ahead could take the week with it — a newer week always won, on
     every device, until that date came. A week more than seven days ahead of this device's
     clock is not a week.

Run once, after add_leaderboard.py; index.html is the source of truth afterwards.
"""
import pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent
PAGE = ROOT / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

# ---- 1 + 5. the board's own week, by its Sunday; nothing far ahead of now
sub("""const wkNum=k=>{ const m=/^(\\d{4})-w(\\d{1,2})$/.exec(String(k||'')); return m?Number(m[1])*100+Number(m[2]):0; };
function wkState(){
  const k=weekKey();
  const cur=(P.wk&&typeof P.wk==='object')?P.wk:null;
  // a week newer than this device's clock (another device, another timezone) is kept, not reset
  if(!cur||!cur.key||wkNum(cur.key)<wkNum(k)) P.wk={key:k,dev:{}};""",
"""// The board's week is named by the date of its Sunday, from whole calendar days. weekKey() —
// the weekly challenge's — counts fractions of days from Jan 1, so it turned over at the start
// of Saturday and split the week around New Year into three.
function lbWeek(d){
  d=d||new Date();
  const sun=new Date(d.getFullYear(),d.getMonth(),d.getDate()-d.getDay());
  return sun.getFullYear()+'-'+pad2(sun.getMonth()+1)+'-'+pad2(sun.getDate());
}
// a week key as a day number, for ordering; 0 for anything that is not one (the old '2026-w39')
const wkNum=k=>{ const m=/^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(String(k||'')); return m?Math.round(Date.UTC(+m[1],+m[2]-1,+m[3])/86400000):0; };
// a week more than a week ahead of this clock is a wrong date somewhere, not a newer week
const wkSane=k=>{ const n=wkNum(k); return n>0&&n<=wkNum(lbWeek())+7; };
function wkState(){
  const k=lbWeek();
  const cur=(P.wk&&typeof P.wk==='object')?P.wk:null;
  // one week ahead (another device, another timezone) is kept; an older, malformed or far-future
  // week starts this one from nothing
  if(!cur||!wkSane(cur.key)||wkNum(cur.key)<wkNum(k)) P.wk={key:k,dev:{}};""")
sub("""function wkCorrect(){
  const w=wkState();
  if(w.key!==weekKey()) return 0;""","""function wkCorrect(){
  const w=wkState();
  if(w.key!==lbWeek()) return 0;""")
sub("""  const ok=o=>o&&typeof o==='object'&&!Array.isArray(o)&&wkNum(o.key)?o:null;""",
"""  const ok=o=>o&&typeof o==='object'&&!Array.isArray(o)&&wkSane(o.key)?o:null;""")

# ---- 2. the cache belongs to one user
sub("""let lbCache=null, lbAt=0, lbBusy=false, lbState='';
async function lbFetch(force){
  if(typeof sb==='undefined'||!sb||!sbUser){ lbState='guest'; lbCache=null; return; }
  if(lbBusy||(!force&&Date.now()-lbAt<60000&&lbCache)) return;
  lbBusy=true;
  try{
    const {data,error}=await sb.rpc('leaderboard_week',{wk:weekKey(),lim:10});
    if(error){""","""let lbCache=null, lbAt=0, lbBusy=null, lbState='', lbUid=null, lbMine=0;
// Until the session has been read, a signed-in user is not a guest: the card says Loading.
let lbAuthKnown=false;       // CLOUD_ON is declared further down: read it at render time, not here
function lbReset(){ lbCache=null; lbAt=0; lbState=''; lbUid=null; }
async function lbFetch(force){
  if(typeof sb==='undefined'||!sb||!sbUser){ lbState='guest'; lbCache=null; lbUid=null; return; }
  const uid=sbUser.id;
  // a board fetched for someone else (a sign-out and sign-in on this device) is not this one's
  if(lbUid!==uid){ lbCache=null; lbAt=0; lbUid=uid; }
  // you have answered more since this board was fetched: it is behind, fetch it again (only
  // then — while an upload is pending the server's count lags, and that is not a reason to
  // ask on every render)
  if(lbCache&&wkCorrect()>lbMine) lbAt=0;
  if(lbBusy===uid||(!force&&Date.now()-lbAt<60000&&lbCache)) return;
  lbBusy=uid;
  try{
    const {data,error}=await sb.rpc('leaderboard_week',{wk:lbWeek(),lim:10});
    if(!sbUser||sbUser.id!==uid) return;           // signed out, or someone else, meanwhile
    if(error){""")
sub("""  finally{ lbBusy=false; }
  if(route==='homeScreen') renderLeaderboard();
}""","""  finally{ if(lbBusy===uid) lbBusy=null; }
  if(route==='homeScreen') renderLeaderboard();
}
// after an upload the board can show it: fetch again rather than wait out the minute
function lbAfterPush(){ lbAt=0; if(route==='homeScreen') lbFetch(true); }
// the session changed hands (or was read at last): what the card shows is no longer right
function lbAuthChanged(){
  lbAuthKnown=true;
  const uid=(typeof sbUser!=='undefined'&&sbUser)?sbUser.id:null;
  if(uid!==lbUid) lbReset();
  if(route==='homeScreen') renderLeaderboard(true);
}""")
sub("""  if(!(typeof sbUser!=='undefined'&&sbUser)){
    note.textContent='Sign in to see where you stand this week — and to be on the board.';""",
"""  if(!(typeof sbUser!=='undefined'&&sbUser)){
    if(!lbAuthKnown&&CLOUD_ON){ note.textContent='Loading\\u2026'; return; }
    note.textContent='Sign in to see where you stand this week — and to be on the board.';""")
sub("""  if(!lbCache){ note.textContent=lbState==='error'?'Could not load the leaderboard — it will try again.':'Loading\\u2026'; return; }""",
"""  if(!lbCache||lbUid!==sbUser.id){ note.textContent=lbState==='error'?'Could not load the leaderboard — it will try again.':'Loading\\u2026'; return; }""")
sub("""    } else if(data&&data.ok){ lbState='ok'; lbCache=data; lbAt=Date.now(); }""",
"""    } else if(data&&data.ok){ lbState='ok'; lbCache=data; lbAt=Date.now(); lbMine=wkCorrect(); }""")
# ---- 3. a count the board has not seen yet still gets its row
sub("""    d.querySelector('.lbrk').textContent=rk===1?'\\u{1f947}':rk===2?'\\u{1f948}':rk===3?'\\u{1f949}':'#'+rk;""",
"""    d.querySelector('.lbrk').textContent=!rk?'\\u2014':rk===1?'\\u{1f947}':rk===2?'\\u{1f948}':rk===3?'\\u{1f949}':'#'+rk;""")
sub("""  if(!meShown&&lbCache.me) add({rank:lbCache.me.rank,name:(typeof myName!=='undefined'&&myName)||'you',c:lbCache.me.c,me:true},true);""",
"""  if(!meShown&&lbCache.me) add({rank:lbCache.me.rank,name:(typeof myName!=='undefined'&&myName)||'you',c:lbCache.me.c,me:true},true);
  else if(!meShown&&mine>0) add({rank:0,name:(typeof myName!=='undefined'&&myName)||'you',c:mine,me:true},true);""")
sub("""  else note.textContent=plural(Number(lbCache.players)||rows.length,'player')+' this week \\u00b7 resets on Sunday';""",
"""  else note.textContent=plural(Number(lbCache.players)||rows.length,'player')+' this week \\u00b7 a new week starts on Sunday';""")

# the hooks: after an upload, on sign-in/out, when the session is first known
sub("""    const ok=await pushCloud();
    if(!silent) authMsg(ok?'Progress synced.':'Could not sync — kept locally.',ok?'ok':'bad');""",
"""    const ok=await pushCloud();
    if(ok&&typeof lbAfterPush==='function') lbAfterPush();
    if(!silent) authMsg(ok?'Progress synced.':'Could not sync — kept locally.',ok?'ok':'bad');""")
sub("""  const client=await loadSupabase(); if(!client) return;
  const {data}=await client.auth.getSession();
  if(data&&data.session){
    sbUser=data.session.user;
    myName=(sbUser.user_metadata&&sbUser.user_metadata.username)||null;
    await syncNow(true); refreshTop();
  }
  client.auth.onAuthStateChange((_e,session)=>{
    sbUser=session?session.user:null; renderAuth();""","""  const client=await loadSupabase(); if(!client){ lbAuthChanged(); return; }
  const {data}=await client.auth.getSession();
  if(data&&data.session){
    sbUser=data.session.user;
    myName=(sbUser.user_metadata&&sbUser.user_metadata.username)||null;
    lbAuthChanged();
    await syncNow(true); refreshTop();
  } else lbAuthChanged();
  client.auth.onAuthStateChange((_e,session)=>{
    const before=sbUser?sbUser.id:null;
    sbUser=session?session.user:null; renderAuth();
    if((sbUser?sbUser.id:null)!==before) lbAuthChanged();""")
sub("""  sbUser=null; lastSync=0; myName=null;
  authMsg('Signed out. Your progress stays on this device.','ok');""",
"""  sbUser=null; lastSync=0; myName=null;
  lbAuthChanged();
  authMsg('Signed out. Your progress stays on this device.','ok');""")
sub("""    wkState, wkBump, wkCorrect, wkMerge, wkNum, weekKey,""",
"""    wkState, wkBump, wkCorrect, wkMerge, wkNum, weekKey, lbWeek, wkSane, lbReset, lbAuthChanged, lbAfterPush,
    get lbUid(){return lbUid;}, set lbAuthKnown(v){ lbAuthKnown=v; },""")
PAGE.write_text(s, encoding="utf-8")

# ---- the SQL takes the Sunday-date key
sq = (ROOT / "supabase_leaderboard.sql")
t = sq.read_text(encoding="utf-8")
old = """  if wk is null or wk !~ '^[0-9]{4}-w[0-9]{1,2}$' then"""
assert t.count(old) == 1
t = t.replace(old, """  -- the week is named by the date of its Sunday: '2026-09-20'
  if wk is null or wk !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' then""")
sq.write_text(t, encoding="utf-8")
print("leaderboard review fixes: Sunday week, per-user cache, refetch after upload, loading state, sane dates")
