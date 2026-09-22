#!/usr/bin/env python3
"""Part three: make a claim stick, and notice a takeover without waiting for focus.

Two problems with parts one and two, both found while testing the handover:

  1. The merge picked the exam by `at`, which simPersist refreshes on every
     question. So the desktop, still mid-exam and pushing every few seconds,
     would win the paper straight back off a phone that had just taken it over,
     and the two would ping-pong. A claim now carries its own `claimAt`, stamped
     only when a device deliberately starts, resumes or takes over a paper —
     never by a routine save — and that is what the merge compares first. Routine
     saves can no longer overturn somebody's claim.

  2. Pulling only on focus is the right default for the app in general, but it is
     wrong for exactly the case this was reported for: both devices awake and in
     the foreground, so neither ever fires a focus event. While an exam is
     actually running, this checks every 30 seconds whether it is still ours.
     That is two requests a minute, during an exam only.

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


# ------------------------------------------------------ 1. a claim that sticks
sub("""function simSaveNewer(x,y){
  if(!x) return y||undefined;
  if(!y) return x;
  return Number(y.at||0)>=Number(x.at||0)?y:x;
}""",
"""// claimAt is stamped only when a device deliberately takes a paper on — starting it,
// resuming it, taking it over. `at` moves on every ordinary save, so comparing that
// alone let a device that was merely still running win a paper back off the device
// that had just claimed it, and the two ping-ponged.
function simSaveNewer(x,y){
  if(!x) return y||undefined;
  if(!y) return x;
  const cx=Number(x.claimAt||0), cy=Number(y.claimAt||0);
  if(cx!==cy) return cy>cx?y:x;
  return Number(y.at||0)>=Number(x.at||0)?y:x;
}""")

sub("""             qt:sim.qt||{}, dev:DEVICE_ID, devKind:DEVICE_KIND,""",
"""             qt:sim.qt||{}, dev:sim.dev||DEVICE_ID, devKind:sim.devKind||DEVICE_KIND,
             claimAt:sim.claimAt||0,""")

sub("""function simClaim(){
  if(!sim) return;
  simPersist();""",
"""function simClaim(){
  if(!sim) return;
  sim.dev=DEVICE_ID; sim.devKind=DEVICE_KIND; sim.claimAt=Date.now();
  simPersist();""")

# resuming carries the claim it is resuming, until simClaim overwrites it
sub("""       rev:sv.rev||{}, qt:sv.qt||{}, running:true, paper:sv.paper||0, mins:sv.mins,""",
"""       rev:sv.rev||{}, qt:sv.qt||{}, running:true, paper:sv.paper||0, mins:sv.mins,
       dev:sv.dev||DEVICE_ID, devKind:sv.devKind||DEVICE_KIND, claimAt:sv.claimAt||0,""")

# resuming on the device that already owned it still refreshes the claim, so a stale
# claim from the other device cannot outrank an exam actually being worked on here
sub("""  renderClock(); simLoad();
}
function simAnsweredIn(sv){""",
"""  renderClock(); simLoad(); simClaim();
}
function simAnsweredIn(sv){""")

# ------------------------------------- 2. notice a takeover without a focus event
sub("""// every local save schedules a debounced push, so normal play keeps the cloud current
function cloudTouch(){""",
"""// Focus is the right trigger for the app in general, but not for the case this was
// reported for: two devices awake at once, neither of which ever loses focus. While an
// exam is genuinely running, check every 30 seconds whether it is still ours.
let ownIv=null;
function simWatchOwner(){
  if(ownIv){ clearInterval(ownIv); ownIv=null; }
  if(TEST) return;                     // the tests call simOwnerCheck() directly
  ownIv=setInterval(()=>{
    if(typeof sim==='undefined'||!sim||!sim.running){ clearInterval(ownIv); ownIv=null; return; }
    if(!sb||!sbUser||syncing||pulling) return;
    if(typeof document!=='undefined'&&document.hidden) return;
    syncOnFocus();
  },30000);
}

// every local save schedules a debounced push, so normal play keeps the cloud current
function cloudTouch(){""")

sub("""  sim.dev=DEVICE_ID; sim.devKind=DEVICE_KIND; sim.claimAt=Date.now();
  simPersist();""",
"""  sim.dev=DEVICE_ID; sim.devKind=DEVICE_KIND; sim.claimAt=Date.now();
  simPersist();
  if(typeof simWatchOwner==='function') simWatchOwner();""")

sub("""    SUPA, CLOUD_ON, mergeProfiles, renderAuth, authCreds, syncNow, cloudTouch, loadSupabase,""",
"""    simWatchOwner,
    SUPA, CLOUD_ON, mergeProfiles, renderAuth, authCreds, syncNow, cloudTouch, loadSupabase,""")

PAGE.write_text(s, encoding="utf-8")
print("claims stick and an exam watches for a takeover · page %.2f MB" % (len(s) / 1e6))
