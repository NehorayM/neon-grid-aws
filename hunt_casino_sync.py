#!/usr/bin/env python3
"""Bug hunt, 2026-09-24: casino taps that vanished, and loose ends in the redo sync.

  1. casRpc dropped any call made while another was in flight, silently. The duel polls every
     1.5 s, the roulette table every 2.5 s (0.8 s while spinning), so "Lock in", a roulette bet,
     Hit or Stand pressed during a poll did nothing — near the end of a duel question that loses
     the duel. Proven with a slow fake server: a duel_answer sent 50 ms into a duel_state poll
     never left the page. Polls still skip when something is in flight; actions now wait for it.
  2. Coming back to the casino with a duel running (a bot game, or one remembered in memory)
     resumed it without showing the Duel tab, so it played on unseen behind Roulette.
  3. Redo: "Continue" on a redo already open on this device resumed it without asking the
     account for the other device's answers. It now pulls, and the open redo takes them in.
  4. Exam history uploads that failed (network) were kept but never retried until the next
     sync happened to come along. They now retry after 15 s.
  5. The "finish the questions you did not reach" button had no label until it was shown.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

# 1. actions wait for an in-flight poll instead of vanishing
sub("""async function casRpc(fn,args,say,opts){
  const tell=say||casMsg;
  if(!sb||!sbUser){ tell('Sign in to play.','bad'); return null; }
  if(casBusy) return null;""","""// The background polls: when something is already in flight they skip a beat. Everything else
// is something the player pressed, and dropping it (as every call used to be) lost bets and the
// "Lock in" that decides a duel.
const CAS_POLLS=new Set(['roulette_table','duel_state','casino_state','bj_current']);
async function casRpc(fn,args,say,opts){
  const tell=say||casMsg;
  if(!sb||!sbUser){ tell('Sign in to play.','bad'); return null; }
  if(casBusy&&CAS_POLLS.has(fn)) return null;
  for(let i=0;i<50&&casBusy;i++) await new Promise(r=>setTimeout(r,100));
  if(casBusy){ tell('The table is slow to answer — try again.','bad'); return null; }""")

# 2. a running duel is shown when you come back
sub("""async function duelResume(){
  if(duelId){ duelRun(); duelRefresh(); return; }""","""async function duelResume(){
  if(duelId){ casTab('Duel'); duelRun(); duelRefresh(); return; }""")

# 3. Continue on an open redo asks the account first
sub("""    b.onclick=()=>live?(simSaved()&&simResume()):histOpen(k,b);""",
"""    // resuming here still asks the account: the other device may have gone on with it
    b.onclick=()=>live?(simSaved()&&simResume(),histCloudPull()):histOpen(k,b);""")

# 4. failed uploads retry
sub("""    const r=await sb.from('exam_history').select('hid,exam').in('hid',want.map(String));
    if(r.error){ if(histMissing(r.error)){ histTable='missing'; return; } want.forEach(h=>histDirty.add(h)); return; }
    (r.data||[]).forEach(row=>{ if(row.exam) cloud[row.hid]=row.exam; });
  }catch(e){ want.forEach(h=>histDirty.add(h)); return; }""","""    const r=await sb.from('exam_history').select('hid,exam').in('hid',want.map(String));
    if(r.error){ if(histMissing(r.error)){ histTable='missing'; return; } want.forEach(h=>histDirty.add(h)); histRetry(); return; }
    (r.data||[]).forEach(row=>{ if(row.exam) cloud[row.hid]=row.exam; });
  }catch(e){ want.forEach(h=>histDirty.add(h)); histRetry(); return; }""")
sub("""    if(error){ if(histMissing(error)) histTable='missing'; else rows.forEach(r=>histDirty.add(r.hid)); }
    else { histTable='ok'; histLastSync=Date.now(); }
  }catch(e){ rows.forEach(r=>histDirty.add(r.hid)); }""","""    if(error){ if(histMissing(error)) histTable='missing'; else { rows.forEach(r=>histDirty.add(r.hid)); histRetry(); } }
    else { histTable='ok'; histLastSync=Date.now(); }
  }catch(e){ rows.forEach(r=>histDirty.add(r.hid)); histRetry(); }""")
sub("""function histCloudQueue(hid){""","""// a failed upload (offline, a dropped connection) is kept and tried again, not left for luck
function histRetry(){
  if(histTimer) return;
  histTimer=setTimeout(histCloudPush,15000);
}
function histCloudQueue(hid){""")

# 5. a label before it is shown
sub("""<button class="btn wide hidden" id="simCont" style="margin:14px auto 0;max-width:420px"></button>""",
"""<button class="btn wide hidden" id="simCont" style="margin:14px auto 0;max-width:420px">↩ Finish the questions you did not reach</button>""")

PAGE.write_text(s, encoding="utf-8"); print("casino actions wait; duel shown on return; redo continue pulls; uploads retry")
