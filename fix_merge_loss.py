#!/usr/bin/env python3
"""Signing in on a fresh browser wiped the account's history. Fix the merge.

Found testing in logged-in mode. mergeProfiles() let whichever profile saved LATER win every
plain field — and a fresh guest profile is always later, having just been created. Its empty
collections replaced the account's: the exam score history (simLog), the exam log, the
readiness history, the spaced-repetition schedule, study records, the known list, the login
streak — then the merged result was pushed to the cloud. The account read "sims: 11" with an
empty history.

  1. Collections are combined, never replaced: histories are united (duplicates dropped,
     newest first, same caps as the writers), the review schedule keeps each question's later
     due point, study records keep the better of each, the login streak keeps the later login,
     inventory keeps a non-empty side over an empty one. An empty list can no longer wipe a full
     one — and a device that still has the full data restores it the next time it syncs.
  2. A sign-in on a device takes the cloud's plain fields (settings), not a blank guest's
     defaults. After that, the later save wins, as before.
  3. "Reset all progress" carries a time, so a signed-in sync drops the copies saved before it
     instead of uniting their history back in.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old,new):
    global s
    assert s.count(old)==1, old[:80]; s=s.replace(old,new)

sub("""function mergeProfiles(a,b){
  a=a||{}; b=b||{};
  const aNewer=Number(a.at||0)>Number(b.at||0);
  const out=aNewer?Object.assign({},b,a):Object.assign({},a,b);
  out.at=Math.max(Number(a.at||0),Number(b.at||0));""",
"""function mergeProfiles(a,b,opts){
  a=a||{}; b=b||{}; opts=opts||{};
  // The first sync of an account on this device takes the cloud's settings: a fresh guest
  // profile is always the "later" save, and letting it win handed its defaults to the account.
  const aNewer=opts.cloudFirst?true:Number(a.at||0)>Number(b.at||0);
  const out=aNewer?Object.assign({},b,a):Object.assign({},a,b);
  out.at=Math.max(Number(a.at||0),Number(b.at||0));
  // ---- collections are combined, never replaced ----
  // Taking them from the later save let a fresh browser's EMPTY lists wipe the account's
  // history, review schedule and streak on sign-in. An empty side can no longer win.
  const newer=aNewer?a:b, older=aNewer?b:a;
  const uniteLog=(k,cap,desc)=>{
    const seen=new Set(), all=[];
    [...(Array.isArray(newer[k])?newer[k]:[]),...(Array.isArray(older[k])?older[k]:[])].forEach(e=>{
      if(!e||typeof e!=='object') return;
      const key=JSON.stringify(e); if(seen.has(key)) return; seen.add(key); all.push(e); });
    all.sort((x,y)=>{ const c=String(x.d||'').localeCompare(String(y.d||'')); return desc?-c:c; });
    out[k]=desc?all.slice(0,cap):all.slice(-cap);
  };
  uniteLog('simLog',12,true);
  uniteLog('examLog',20,true);
  { // readiness history: one point per day, ascending
    const byDay={};
    [...(Array.isArray(older.rHist)?older.rHist:[]),...(Array.isArray(newer.rHist)?newer.rHist:[])]
      .forEach(r=>{ if(r&&r.d) byDay[r.d]=r; });
    out.rHist=Object.values(byDay).sort((x,y)=>String(x.d).localeCompare(String(y.d))).slice(-30);
  }
  out.known=[...new Set([...(a.known||[]),...(b.known||[])])];
  { // spaced repetition: every scheduled question from either side, the later due point wins
    const sr=Object.assign({},older.sr||{});
    Object.entries(newer.sr||{}).forEach(([k,v])=>{ const o=sr[k];
      sr[k]=(!o||(Number(v&&v.due)||0)>=(Number(o.due)||0))?v:o; });
    out.sr=sr;
  }
  { // study chapters: read on either device, the better score
    const st={};
    new Set([...Object.keys(a.study||{}),...Object.keys(b.study||{})]).forEach(k=>{
      const x=(a.study||{})[k], y=(b.study||{})[k];
      if(!x||!y){ st[k]=x||y; return; }
      st[k]=Object.assign({},x,y,{read:(x.read||y.read)?1:0, best:Math.max(x.best||0,y.best||0),
                                  at:(String(x.at||'')>String(y.at||''))?x.at:y.at});
    });
    out.study=st;
  }
  { // the login streak belongs to the later login, not the later save
    const x=a.login||{}, y=b.login||{};
    const lx=Number(x.last)||0, ly=Number(y.last)||0;
    out.login=(lx!==ly)?(lx>ly?x:y):((Number(x.streak)||0)>=(Number(y.streak)||0)?x:y);
  }
  { // inventory counts go down as items are used, so the later save is right — unless it is empty
    const ni=newer.inv||{}, oi=older.inv||{};
    out.inv=Object.keys(ni).length?ni:oi;
  }
  if(!newer.lastPaper&&older.lastPaper) out.lastPaper=older.lastPaper;""")

# the first sync of an account on this device
sub("""    if(remote&&remote.profile&&Object.keys(remote.profile).length){
      const merged=mergeProfiles(remote.profile,P);""",
"""    if(remote&&remote.profile&&Object.keys(remote.profile).length){
      const seenKey='academy_cloud_seen_'+sbUser.id;
      let first=false; try{ first=!localStorage.getItem(seenKey); }catch(e){}
      const merged=mergeProfiles(remote.profile,P,{cloudFirst:first});
      try{ localStorage.setItem(seenKey,'1'); }catch(e){}""")
PAGE.write_text(s, encoding="utf-8"); print("merge combines collections")

# ---- second pass: "first sync" is a sign-in on this device, not a missing local flag ----
# A flag in localStorage would also be missing on every device that was signed in before this
# change, and those would then take the cloud's settings over their own.
s = PAGE.read_text(encoding="utf-8")
sub("""    const remote=await pullCloud();
    if(remote&&remote.username) myName=remote.username;
    if(remote&&remote.profile&&Object.keys(remote.profile).length){
      const seenKey='academy_cloud_seen_'+sbUser.id;
      let first=false; try{ first=!localStorage.getItem(seenKey); }catch(e){}
      const merged=mergeProfiles(remote.profile,P,{cloudFirst:first});
      try{ localStorage.setItem(seenKey,'1'); }catch(e){}""",
"""    const remote=await pullCloud();
    const cloudFirst=freshSignIn; freshSignIn=false;
    if(remote&&remote.username) myName=remote.username;
    if(remote&&remote.profile&&Object.keys(remote.profile).length){
      const merged=mergeProfiles(remote.profile,P,{cloudFirst});""")
sub("""async function syncNow(silent){""",
"""// Set by a sign-in on this device: its first merge takes the account's settings from the cloud.
let freshSignIn=false;
async function syncNow(silent){""")
sub("""  authMsg('Signed in. Merging your progress…','busy');
  await syncNow(false);""",
"""  authMsg('Signed in. Merging your progress…','busy');
  freshSignIn=true;
  await syncNow(false);""")
# dates written before zero-padding sort wrongly as plain strings
sub("""    all.sort((x,y)=>{ const c=String(x.d||'').localeCompare(String(y.d||'')); return desc?-c:c; });""",
"""    all.sort((x,y)=>{ const c=dayNorm(x.d).localeCompare(dayNorm(y.d)); return desc?-c:c; });""")
sub("""      .forEach(r=>{ if(r&&r.d) byDay[r.d]=r; });
    out.rHist=Object.values(byDay).sort((x,y)=>String(x.d).localeCompare(String(y.d))).slice(-30);""",
"""      .forEach(r=>{ if(r&&r.d) byDay[dayNorm(r.d)]=r; });
    out.rHist=Object.values(byDay).sort((x,y)=>dayNorm(x.d).localeCompare(dayNorm(y.d))).slice(-30);""")
sub("""                                  at:(String(x.at||'')>String(y.at||''))?x.at:y.at});""",
"""                                  at:(dayNorm(x.at)>dayNorm(y.at))?x.at:y.at});""")
PAGE.write_text(s, encoding="utf-8"); print("fresh sign-in flag, padded date sort")

# ---- third pass: the mock log is a history too ----
s = PAGE.read_text(encoding="utf-8")
sub("""  uniteLog('examLog',20,true);
""","""  uniteLog('examLog',20,true);
  uniteLog('mockLog',15,true);
""")
PAGE.write_text(s, encoding="utf-8"); print("mock log united")

# ---- fourth pass: a reset is not undone by the next sync ----
# With collections united, "Reset all progress" while signed in would come straight back from
# the cloud copy. The reset now carries a time, and a copy saved before it is dropped, not merged.
s = PAGE.read_text(encoding="utf-8")
sub("""function mergeProfiles(a,b,opts){
  a=a||{}; b=b||{}; opts=opts||{};""",
"""function mergeProfiles(a,b,opts){
  a=a||{}; b=b||{}; opts=opts||{};
  // "Reset all progress": a copy saved before the reset (on any device) is dropped, not merged —
  // uniting it back in would undo the reset on the next sync. Settings survive; progress does not.
  const ra=Number(a.resetAt)||0, rb=Number(b.resetAt)||0, reset=Math.max(ra,rb);
  const stale=p=>reset>0&&(Number(p.resetAt)||0)<reset&&Number(p.at||0)<reset;
  if(stale(a)!==stale(b)){
    const keep=stale(a)?b:a, drop=stale(a)?a:b, out=Object.assign({},keep);
    Object.keys(drop).forEach(k=>{ if(k in out) return; const v=drop[k];
      out[k]=Array.isArray(v)?[]:(v&&typeof v==='object')?{}:(typeof v==='number')?0:v; });
    return out;
  }""")
sub("""    diff:'easy',charge:0,bossesBeaten:0,gamesSinceBoss:0,inv:{},marks:[],known:[]});""",
"""    diff:'easy',charge:0,bossesBeaten:0,gamesSinceBoss:0,inv:{},marks:[],known:[],
    resetAt:Date.now()});            // so a signed-in sync drops the old copies instead of uniting them back""")
PAGE.write_text(s, encoding="utf-8"); print("reset survives a sync")
