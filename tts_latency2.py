#!/usr/bin/env python3
"""Second attempt at the Read delay. The first one did not fix it.

What the first pass missed:

  1. ttsStop() still called cancel() unconditionally — and simLoad() calls
     ttsStop() on every single question load. So cancel() has always just been
     fired at an idle engine by the time you press Read. Guarding the cancel
     inside ttsSpeak() was pointless while the other caller kept doing it. In
     Chrome, cancel() on an idle engine is exactly what leaves the next speak()
     sitting there.

  2. The engine is cold. Android's Google TTS and Chrome's speech service both
     take seconds to wake the first time they are asked for anything, and the
     app never asks until you press the button. It now speaks a zero-volume
     utterance on the first user gesture — the same gesture that already wakes
     the Web Audio context — so the engine is up before anybody wants it.

  3. If the voice list is still empty when you press, ttsVoice() returns null,
     nothing is set on the utterance, and the engine falls back to its own
     default — which on Chrome is usually the network voice this was supposed to
     avoid. It now waits for voiceschanged, briefly, rather than giving up.

  4. Chrome can leave synthesis paused, in which case speak() queues silently.
     resume() is now called before speaking.

tts_probe.html measures each of these on the actual device, because this needs
confirming rather than assuming again.

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


# ------------------------------------------- 1. stop cancelling an idle engine
sub("""function ttsStop(){
  ttsOn=false; ttsSeq++;              // anything still queued from before is now stale
  try{ if(ttsOk()) window.speechSynthesis.cancel(); }catch(e){}
  renderTtsBtn();
}""",
"""function ttsStop(){
  ttsOn=false; ttsSeq++;              // anything still queued from before is now stale
  try{
    // Only cancel something that is actually running. simLoad() calls ttsStop() on every
    // question load, so this used to fire cancel() at an idle engine constantly — and a
    // cancel with nothing to cancel is what leaves Chrome's next speak() sitting there.
    const ss=window.speechSynthesis;
    if(ttsOk()&&(ss.speaking||ss.pending)) ss.cancel();
  }catch(e){}
  renderTtsBtn();
}

// The speech engine is cold until something asks it for audio, and waking it takes seconds
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
}""")

# ------------------------------------------------- 2. warm it on the first gesture
sub("""function ensureAudio(){ if(!AC){ try{ AC=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ return; } }
  if(AC&&AC.state==='suspended') AC.resume(); }""",
"""function ensureAudio(){ if(!AC){ try{ AC=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ AC=null; } }
  if(AC&&AC.state==='suspended') AC.resume();
  if(typeof ttsWarm==='function') ttsWarm(); }""")

# ---------------------------------------- 3. do not give up on an empty voice list
sub("""if(typeof window!=='undefined'&&'speechSynthesis' in window){
  ttsLoadVoices();
  try{ window.speechSynthesis.addEventListener('voiceschanged',ttsLoadVoices); }
  catch(e){ try{ window.speechSynthesis.onvoiceschanged=ttsLoadVoices; }catch(e2){} }
}""",
"""if(typeof window!=='undefined'&&'speechSynthesis' in window){
  ttsLoadVoices();
  const onVoices=()=>{ ttsLoadVoices(); if(typeof renderTtsBtn==='function') renderTtsBtn(); };
  try{ window.speechSynthesis.addEventListener('voiceschanged',onVoices); }
  catch(e){ try{ window.speechSynthesis.onvoiceschanged=onVoices; }catch(e2){} }
  // some builds only fill the list after it has been asked for a few times
  let tries=0;
  const poll=setInterval(()=>{ if(ttsLoadVoices().length||++tries>10) clearInterval(poll); },300);
}""")

# ------------------------------------- 4. resume a paused engine before speaking
sub("""    // only cancel if there is something to cancel: cancel() straight into speak() is a
    // long-standing Chrome race that delays or drops the utterance entirely
    if(ss.speaking||ss.pending) ss.cancel();""",
"""    // only cancel if there is something to cancel: cancel() straight into speak() is a
    // long-standing Chrome race that delays or drops the utterance entirely
    if(ss.speaking||ss.pending) ss.cancel();
    // Chrome can leave synthesis paused, and a paused engine queues speak() in silence
    try{ if(ss.paused) ss.resume(); }catch(e){}""")

sub("""    ttsChunks, ttsVoice, ttsLoadVoices, get ttsVoices(){return ttsVoices;},""",
"""    ttsChunks, ttsVoice, ttsLoadVoices, ttsWarm, get ttsVoices(){return ttsVoices;},
    get ttsWarmed(){return ttsWarmed;},""")

PAGE.write_text(s, encoding="utf-8")
print("second pass at the Read delay applied · page %.2f MB" % (len(s) / 1e6))
