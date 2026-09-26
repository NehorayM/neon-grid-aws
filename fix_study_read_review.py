#!/usr/bin/env python3
"""Study read-aloud: what the review confirmed (2 of 2).

  1. The retry forgot who was reading. When the first attempt does not start (a chosen voice
     that fails, the case the watchdog exists for), the first batch's onerror ran done() — the
     seq still matched — which set ttsOn false and reset the owner to the question's and the
     paragraph to none. The plain retry then started as the question's reading: the paragraph's
     ⏹ could not stop it (it restarted it), leaving the chapter no longer stopped it, and on an
     exam question where reading is tapered away it could be cut off. Now each batch carries
     who started it (ttsOwn) and a batch number: a cancelled batch's callbacks are stale, and
     the batch that does start restores its owner. The retry is its own function, ttsRetry.
  2. Lists ran together. lbList emits <li> with nothing between them, so a list was read as
     "…Availability Zones.Tolerates losing two copies…" — no pause, and some voices say "dot".
     Each item now ends in a sentence break before the text is read.

Run once, after add_study_read.py; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

# ---- 1. a batch carries its owner; a cancelled batch is stale
sub("""let paraOn=null;            // the paragraph being read""",
"""let paraOn=null;            // the paragraph being read
let ttsBatch=0, ttsOwn=null; // which batch of utterances is current, and who asked for this reading""")
sub("""  let started=false;
  const done=()=>{ if(seq===ttsSeq){ ttsOn=false; renderTtsBtn(); } };""",
"""  let started=false;
  // A retry cancels this batch, and a cancelled utterance still fires onerror: without its own
  // number it counted as current, ended the reading and lost who had asked for it.
  const batch=++ttsBatch, own=ttsOwn;
  const cur=()=>seq===ttsSeq&&batch===ttsBatch;
  const done=()=>{ if(cur()){ ttsOn=false; renderTtsBtn(); } };""")
sub("""    if(k===0) u.onstart=()=>{ started=true; if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); } };""",
"""    if(k===0) u.onstart=()=>{ started=true;
      if(cur()){ if(own){ exTts=own.ex; ttsOwner=own.owner; paraOn=own.para; } ttsOn=true; renderTtsBtn(); } };""")
sub("""  ttsOwner=(opts&&opts.owner)||(exTts?'ex':'q');""","""  ttsOwner=(opts&&opts.owner)||(exTts?'ex':'q');
  if(ttsOwner!=='para') paraOn=null;
  ttsOwn={ex:exTts, owner:ttsOwner, para:paraOn};   // restored by whichever batch starts""")
sub("""        if(seq!==ttsSeq||live()) return;
        try{ ss.cancel(); }catch(e){}
        const live2=ttsSend(text,seq,true);""","""        if(seq!==ttsSeq||live()) return;
        const live2=ttsRetry(text,seq);""")
sub("""function simSpeak(){""","""// the watchdog's second try: clear the queue, send the text as plainly as possible
function ttsRetry(text,seq){
  try{ window.speechSynthesis.cancel(); }catch(e){}
  return ttsSend(text,seq,true);
}
function simSpeak(){""")

# ---- 2. a list is read item by item
sub("""  c.querySelectorAll('.parread,.ic').forEach(x=>x.remove());""",
"""  c.querySelectorAll('.parread,.ic').forEach(x=>x.remove());
  // list items sit edge to edge in the markup: end each one as a sentence, or they run together
  c.querySelectorAll('li').forEach(li=>{ const t=li.textContent.trim(); li.textContent=t+(/[.!?:;]$/.test(t)?' ':'. '); });""")

sub("""    paraRead, paraText, studyBlocksHTML, get ttsOwner(){return ttsOwner;},""",
"""    paraRead, paraText, studyBlocksHTML, get ttsOwner(){return ttsOwner;},
    ttsRetry, get ttsSeq(){return ttsSeq;}, get paraOn(){return paraOn;},""")
PAGE.write_text(s, encoding="utf-8"); print("read-aloud: a retry keeps its owner; lists read item by item")
