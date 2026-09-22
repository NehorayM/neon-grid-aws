#!/usr/bin/env python3
"""A profile missing a collection took a whole screen down.

renderBadges() and renderShop() were fixed one at a time; then the third audit
found renderBank() doing the same thing, and a sweep turned up nineteen profile
fields dereferenced somewhere without a guard — P.login at twenty-one sites,
P.secStats at twelve, P.highs at eight with no default anywhere.

Guarding a hundred read sites is the wrong fix. The profile is normalised once,
on the way in, so the rest of the file can assume the shape it was written
against. Three doors lead in and all three now go through it: loadProfile(),
the cloud merge, and importing a profile from a file.

Run once; index.html is the source of truth afterwards.
"""
import pathlib

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


sub("""let loaded=false;
async function loadProfile(){
  try{
    const r=await window.storage.get('academy_profile',false);
    if(r) Object.assign(P,JSON.parse(r.value));
  }catch(e){}""",
"""let loaded=false;

// A profile can arrive from four places: this browser's storage, the cloud merge, an
// imported file, or nowhere at all on a first run. Any of them can be missing a field the
// rest of the file dereferences without asking — that is how an empty profile used to take
// the Badges, Shop and Bank screens down with it. Normalise once, here, rather than
// guarding a hundred read sites.
const P_COLLECTIONS={
  obj:['seen','secStats','upgrades','highs','inv','sr','study','known','papers','courses',
       'login','day','rHist','quests','simSave'],
  arr:['wrong','badges','marks','examLog','mockLog','simLog']
};
const P_NUMBERS=['xp','coins','answered','correct','streak','bestStreak','gamesPlayed',
                 'charge','bossesBeaten','gamesSinceBoss','skill','playMs','mocks',
                 'mocksPassed','bestMock','sims','simsPassed','bestSim','nextChest'];
function normaliseProfile(p){
  p=p||P;
  P_COLLECTIONS.obj.forEach(k=>{ if(p[k]===null||typeof p[k]!=='object'||Array.isArray(p[k])) p[k]=p[k]&&typeof p[k]==='object'?p[k]:{}; });
  P_COLLECTIONS.arr.forEach(k=>{ if(!Array.isArray(p[k])) p[k]=[]; });
  P_NUMBERS.forEach(k=>{ const n=Number(p[k]); if(p[k]!==undefined&&!isFinite(n)) p[k]=0; });
  if(!p.highs||typeof p.highs!=='object') p.highs={};
  ['breaker','dash','firewall','signal','sort','orbit','boss','match','scenario','defend']
    .forEach(g=>{ if(typeof p.highs[g]!=='number'||!isFinite(p.highs[g])) p.highs[g]=0; });
  if(typeof p.diff!=='string') p.diff='easy';
  // simSave starts life absent, not as an empty object the resume code would try to read
  if(p.simSave&&!Array.isArray(p.simSave.qs)) delete p.simSave;
  return p;
}

async function loadProfile(){
  try{
    const r=await window.storage.get('academy_profile',false);
    if(r) Object.assign(P,JSON.parse(r.value));
  }catch(e){}
  normaliseProfile(P);""")

sub("""      const merged=mergeProfiles(remote.profile,P);     // local is the newer side of the merge
      Object.assign(P,merged);""",
"""      const merged=mergeProfiles(remote.profile,P);
      Object.assign(P,merged);
      normaliseProfile(P);        // the other device may be on an older shape""")

sub("""    syncQBar, leaveExam, pctW, chestProgress, timerClamp,""",
"""    syncQBar, leaveExam, pctW, chestProgress, normaliseProfile, timerClamp,""")

PAGE.write_text(s, encoding="utf-8")
print("profile normalised on the way in · page %.2f MB" % (len(s) / 1e6))
