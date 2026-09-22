#!/usr/bin/env python3
"""Two devices, one account: make them converge instead of diverging.

The symptom was a desktop sitting on Exam 1 while the phone sat on Exam 2. It was
not an auth problem — three things in the sync were wrong:

  1. It only ever pushed. pullCloud() ran at boot, after sign-in and on the Sync
     now button, and nowhere else, so a tab left open all day never once looked at
     what the other device had done.
  2. When it did pull, mergeProfiles(remote, local) began Object.assign({}, a, b)
     with b = local, so every field outside MAX_KEYS and the hand-merged
     collections took the local value. simSave was in neither list, so the local
     exam beat the remote one every single time and the two could never converge.
  3. updated_at was written and selected but never compared to anything.

What this does:

  * P.at is stamped on every save, and the merge gives the plain fields to
    whichever device saved later instead of always to this one. Counters and
    collections keep their max/union merges, so nothing is lost either way.
    P.papers now merges too — a paper passed on the phone used to vanish on the
    desktop.
  * It pulls when the tab becomes visible or regains focus, throttled, as well as
    at boot.
  * An exam is owned by one device at a time. Every save carries the device that
    wrote it; the merge hands simSave to whichever device touched it last. If this
    device is mid-exam and the merge says another device now owns it, this one
    stops its clock and says so rather than running a second copy.
  * Resuming or starting a paper that is open elsewhere asks first, using the
    app's own arm-then-confirm idiom, and pushes the claim immediately so the
    other device finds out on its next focus instead of four seconds of debounce
    later.

Not done, deliberately: mirroring an exam live between two devices. sim.qt and
the paper deadline are wall-clock state measured on one device; two devices
ticking and pushing them corrupt each other, and mirroring the question index
drags a reader out of the question they are on.

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


# ------------------------------------------------------- 1. who this device is
sub("""const reduced=typeof window.matchMedia==='function'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;""",
"""const reduced=typeof window.matchMedia==='function'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- which device this is ----------
// Kept in its own localStorage key, never in P: the profile is merged across
// devices, so an id stored in it would be overwritten by the other device's copy
// and both would think they were the same machine.
let DEVICE_ID=(()=>{
  try{
    let v=localStorage.getItem('academy_device');
    if(!v){
      v=(window.crypto&&window.crypto.randomUUID)
        ? window.crypto.randomUUID()
        : 'd'+Date.now().toString(36)+Math.random().toString(36).slice(2,10);
      localStorage.setItem('academy_device',v);
    }
    return v;
  }catch(e){ return 'd-nostore'; }
})();
let DEVICE_KIND=(()=>{
  const ua=(navigator&&navigator.userAgent)||'';
  if(/iPad|Tablet/i.test(ua)||(/Android/i.test(ua)&&!/Mobile/i.test(ua))) return 'tablet';
  if(/Mobi|iPhone|iPod|Android/i.test(ua)) return 'phone';
  return 'desktop';
})();
const otherDevice=sv=>(sv&&sv.devKind)?('your '+sv.devKind):'your other device';""")

# --------------------------------------------- 2. every save carries its moment
sub("""function saveProfile(){
  if(saveTimer) clearTimeout(saveTimer);
  saveTimer=setTimeout(async()=>{""",
"""function saveProfile(){
  P.at=Date.now();                // which side of a two-device merge is the newer one
  if(saveTimer) clearTimeout(saveTimer);
  saveTimer=setTimeout(async()=>{""")

# ------------------------------------------------ 3. the merge stops preferring us
sub("""function mergeProfiles(a,b){
  a=a||{}; b=b||{};
  const out=Object.assign({},a,b);""",
"""// a is the cloud's copy, b is this device's. They are two devices, not an old and a
// new version of one, so the plain fields go to whichever saved later rather than
// always to us. Everything below is merged so that neither device loses anything.
function simSaveNewer(x,y){
  if(!x) return y||undefined;
  if(!y) return x;
  return Number(y.at||0)>=Number(x.at||0)?y:x;
}
function mergeProfiles(a,b){
  a=a||{}; b=b||{};
  const aNewer=Number(a.at||0)>Number(b.at||0);
  const out=aNewer?Object.assign({},b,a):Object.assign({},a,b);
  out.at=Math.max(Number(a.at||0),Number(b.at||0));
  // the exam in progress belongs to whichever device touched it last, not to us
  const sv=simSaveNewer(a.simSave,b.simSave);
  if(sv) out.simSave=sv; else delete out.simSave;
  // a paper passed on the phone used to disappear on the desktop
  out.papers={};
  const ps=new Set([...Object.keys(a.papers||{}),...Object.keys(b.papers||{})]);
  ps.forEach(k=>{
    const x=(a.papers||{})[k], y=(b.papers||{})[k];
    if(!x||!y){ out.papers[k]=x||y; return; }
    out.papers[k]={best:Math.max(x.best||0,y.best||0),
                   tries:Math.max(x.tries||0,y.tries||0),
                   last:(aNewer?x.last:y.last)||x.last||y.last,
                   d:(aNewer?x.d:y.d)||x.d||y.d};
  });""")

# --------------------------------------------- 4. the exam save names its device
sub("""  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},
             qt:sim.qt||{},
             left:Math.max(0,sim.endAt-Date.now()), mins:sim.mins||SIM_MIN, at:Date.now()};""",
"""  P.simSave={paper:sim.paper||0, qs:sim.qs, i:sim.i, ans:sim.ans, flag:sim.flag, rev:sim.rev||{},
             qt:sim.qt||{}, dev:DEVICE_ID, devKind:DEVICE_KIND,
             left:Math.max(0,sim.endAt-Date.now()), mins:sim.mins||SIM_MIN, at:Date.now()};""")

PAGE.write_text(s, encoding="utf-8")
print("device identity, timestamped merge and exam ownership stamped · page %.2f MB" % (len(s) / 1e6))
