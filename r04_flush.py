#!/usr/bin/env python3
"""Round 4: an answer given just before the page closed was lost.

saveProfile() waits 250 ms before writing, so a burst of changes becomes one write. Nothing
flushed that wait when the page went away. Measured: an answer is not in storage right
after it is given, only 250 ms later — so answering and then refreshing, closing the tab,
or switching apps on a phone (which can kill the tab without another event) dropped it.
Everything else about the clock survives a refresh now; this was the last gap.

The pending write is now flushed on `pagehide`, and when the page is hidden, which on a
phone is the last reliable moment before the tab can be discarded.

And every write failure was swallowed. A private window, or storage blocked by the browser,
throws on every setItem, and the app carried on as if progress were being kept. The shim
now reports whether the write landed, and the first failure says so once.

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

sub("""  set: async (key, value) => {
    try { localStorage.setItem(key, value); } catch(e){}
  }""",
"""  // Reports whether the write landed. The body runs synchronously when called, so a caller
  // that needs the write to happen NOW (a page being closed) gets it without awaiting.
  set: async (key, value) => {
    try { localStorage.setItem(key, value); return true; } catch(e){ return false; }
  }""")

sub("""let saveTimer=null;
function saveProfile(){
  P.at=Date.now();                // which side of a two-device merge is the newer one
  if(saveTimer) clearTimeout(saveTimer);
  saveTimer=setTimeout(async()=>{
    try{ await window.storage.set('academy_profile',JSON.stringify(P),false); }catch(e){}
    if(typeof cloudTouch==='function') cloudTouch();
  },250);
}""",
"""let saveTimer=null, saveWarned=false;
function writeProfile(){
  let p;
  try{ p=window.storage.set('academy_profile',JSON.stringify(P),false); }catch(e){ p=Promise.resolve(false); }
  // A private window or blocked storage throws on every write, and this used to carry on as
  // if progress were being kept. Say so, once.
  Promise.resolve(p).then(ok=>{
    if(ok===false&&!saveWarned){
      saveWarned=true;
      if(typeof toast==='function')
        toast('\\u26a0 This browser is not saving your progress \\u2014 a private window, or storage is blocked');
    }
  });
}
function saveProfile(){
  P.at=Date.now();                // which side of a two-device merge is the newer one
  if(saveTimer) clearTimeout(saveTimer);
  saveTimer=setTimeout(()=>{
    saveTimer=null;
    writeProfile();
    if(typeof cloudTouch==='function') cloudTouch();
  },250);
}
// The 250 ms wait turns a burst of changes into one write, but nothing flushed it when the
// page went away: answer, then refresh or switch apps, and that answer was gone.
function flushProfile(){
  if(!saveTimer) return;
  clearTimeout(saveTimer); saveTimer=null;
  writeProfile();
}
if(typeof window!=='undefined') window.addEventListener('pagehide',flushProfile);
if(typeof document!=='undefined')
  document.addEventListener('visibilitychange',()=>{ if(document.hidden) flushProfile(); });""")

# expose for the harness
sub("    isPractice, brkOpen, brkElapsed,", "    isPractice, brkOpen, brkElapsed, saveProfile, flushProfile,")

PAGE.write_text(s, encoding="utf-8")
print("pending save flushed on close; failed writes reported")
