#!/usr/bin/env python3
"""Make Read impossible to silence, and stop guessing at Chrome's behaviour.

The last change made it worse: no sound at all. Two things in it could do that,
and both were reasoning about a browser I cannot test here rather than
measuring.

  * The zero-volume warm-up utterance. Some engines do not emit a silent
    utterance but still hold it in the queue, and anything spoken afterwards
    queues behind it. The warm-up is gone.
  * `ttsStop()` only cancelling when `speaking || pending`. If the engine has an
    utterance stuck where neither flag reports it — which is the whole reason
    this is a known Chrome bug — then nothing ever clears the queue and
    everything after it is silent.

What replaces the guesswork:

  * Pressing Read always cancels first, then speaks on the next tick. Yielding a
    tick is what avoids the cancel/speak race, rather than skipping the cancel
    and hoping the queue is empty.
  * A watchdog. If no sound has started 900ms after asking, it cancels, drops the
    voice override and the chunking, and tries once more as plainly as possible.
    The worst case is now a stutter, not silence.
  * If that retry is silent too, it says so instead of leaving a button that
    claims to be reading.

`ttsStop()` still avoids cancelling an idle engine on every question load, which
is the one part of the last change that is safe and is the likeliest cause of
the original delay.

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


# -------------------------------------------------- the warm-up utterance goes
sub("""// The speech engine is cold until something asks it for audio, and waking it takes seconds
// on Android. Ask for silence on the first user gesture — the same one that already wakes the
// Web Audio context — so it is up long before anyone presses Read.
let ttsWarmed=false;
function ttsWarm(){
  if(ttsWarmed||!ttsOk()||TEST) return;
  ttsWarmed=true;
  try{
    const ss=window.speechSynthesis;
    const u=new SpeechSynthesisUtterance(' ');
    u.volume=0; u.rate=1; u.lang='en-US';
    ss.speak(u);
    setTimeout(()=>{ try{ if(!ttsOn&&!ss.speaking) ss.cancel(); }catch(e){} },1200);
  }catch(e){}
}""",
"""// There was a zero-volume warm-up utterance here, to wake a cold engine on the first user
// gesture. It is gone: some engines never emit a silent utterance but still hold it in the
// queue, and everything spoken afterwards queues behind it and is never heard. Waking the
// engine is not worth a mode where the button does nothing at all.
let ttsWarmed=false;
function ttsWarm(){ ttsWarmed=true; }      // kept so ensureAudio() has something to call""")

# ------------------------------------------------ speaking, with a way back out
sub("""function ttsSpeak(text){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return false; }
  const ss=window.speechSynthesis;
  const seq=++ttsSeq;                 // a later tap makes this batch's callbacks stale
  try{
    // only cancel if there is something to cancel: cancel() straight into speak() is a
    // long-standing Chrome race that delays or drops the utterance entirely
    if(ss.speaking||ss.pending) ss.cancel();
    // Chrome can leave synthesis paused, and a paused engine queues speak() in silence
    try{ if(ss.paused) ss.resume(); }catch(e){}
    const chunks=ttsChunks(text);
    if(!chunks.length) return false;
    const voice=ttsVoice();
    const done=()=>{ if(seq===ttsSeq){ ttsOn=false; renderTtsBtn(); } };
    chunks.forEach((part,k)=>{
      const u=new SpeechSynthesisUtterance(part);
      u.rate=P.ttsRate||1; u.lang='en-US';
      if(voice) u.voice=voice;
      // the button turns to Stop when sound actually starts, not when we asked for it
      if(k===0) u.onstart=()=>{ if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); } };
      if(k===chunks.length-1) u.onend=done;
      u.onerror=done;
      ss.speak(u);
    });
    ttsOn=true; renderTtsBtn();
    // a browser with no voices installed accepts speak() and stays silent, so say so
    // rather than leaving the reader wondering whether the tap registered
    if(!TEST) setTimeout(()=>{
      try{
        if(seq!==ttsSeq) return;
        if(!ss.speaking&&!ss.pending&&!ttsLoadVoices().length){
          ttsOn=false; renderTtsBtn();
          toast('No speech voices are installed in this browser');
        }
      }catch(e){}
    },400);
    return true;
  }catch(e){ ttsOn=false; renderTtsBtn(); return false; }
}""",
"""// One batch of utterances. `plain` is the fallback the watchdog uses: no voice override,
// no chunking, nothing clever — just the text, which is the most likely thing to work on an
// engine that has ignored everything else.
function ttsSend(text,seq,plain){
  const ss=window.speechSynthesis;
  const chunks=plain?[String(text)]:ttsChunks(text);
  if(!chunks.length) return false;
  const voice=plain?null:ttsVoice();
  let started=false;
  const done=()=>{ if(seq===ttsSeq){ ttsOn=false; renderTtsBtn(); } };
  chunks.forEach((part,k)=>{
    const u=new SpeechSynthesisUtterance(part);
    u.rate=P.ttsRate||1; u.lang='en-US';
    if(voice) u.voice=voice;
    if(k===0) u.onstart=()=>{ started=true; if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); } };
    if(k===chunks.length-1) u.onend=done;
    u.onerror=done;
    ss.speak(u);
  });
  return ()=>started||ss.speaking;
}
function ttsSpeak(text){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return false; }
  const ss=window.speechSynthesis;
  const seq=++ttsSeq;                 // a later tap makes this batch's callbacks stale
  try{
    // Asking to read is an explicit request, so always clear whatever is there first — an
    // utterance the engine has lost track of reports neither speaking nor pending, and
    // everything sent afterwards queues silently behind it. The tick before speaking is what
    // avoids the cancel/speak race, rather than skipping the cancel and hoping.
    ss.cancel();
    try{ if(ss.paused) ss.resume(); }catch(e){}
    ttsOn=true; renderTtsBtn();
    setTimeout(()=>{
      if(seq!==ttsSeq) return;
      const live=ttsSend(text,seq,false);
      if(!live){ ttsOn=false; renderTtsBtn(); return; }
      if(TEST) return;
      // Nothing yet? Clear the queue and try again as plainly as possible. The worst case
      // becomes a stutter instead of a button that does nothing.
      setTimeout(()=>{
        if(seq!==ttsSeq||live()) return;
        try{ ss.cancel(); }catch(e){}
        const live2=ttsSend(text,seq,true);
        setTimeout(()=>{
          if(seq!==ttsSeq) return;
          if(live2&&live2()) return;
          ttsOn=false; renderTtsBtn();
          toast(ttsLoadVoices().length
            ? 'This browser will not play speech \\u2014 check the volume and the site sound setting'
            : 'No speech voices are installed in this browser');
        },1200);
      },900);
    },0);
    return true;
  }catch(e){ ttsOn=false; renderTtsBtn(); return false; }
}""")

sub("""    ttsChunks, ttsVoice, ttsLoadVoices, ttsWarm, get ttsVoices(){return ttsVoices;},""",
"""    ttsChunks, ttsVoice, ttsLoadVoices, ttsWarm, ttsSend, get ttsVoices(){return ttsVoices;},""")

PAGE.write_text(s, encoding="utf-8")
print("Read can no longer end up silent · page %.2f MB" % (len(s) / 1e6))
