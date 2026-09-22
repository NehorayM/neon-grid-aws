#!/usr/bin/env python3
"""Make the app report its own read-aloud latency.

Four probe runs now say the speech API answers in 300-800ms on this machine,
with the ChromeOS "local" voices the only thing that never speaks. What is still
unknown is what the *app* does when Read is pressed, and asking for that as a
separate test has not worked.

So the app measures itself. Open it with ?ttsdebug=1 and every press of Read
toasts the time from the tap to the first sound, plus how it got there. Nothing
to run, nothing to copy between pages — press the button and read the number.

Without the flag it stays quiet, with one exception: if the first sound takes
more than three seconds it says so once, because that is worth knowing about
whether or not anybody is debugging.

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


sub("""function ttsSend(text,seq,plain){
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
}""",
"""const TTS_DEBUG=typeof location!=='undefined'&&/[?&]ttsdebug=1/.test(location.search);
let ttsAskedAt=0, ttsSlowSaid=false;
// The app times itself, so the only thing anyone has to do to report a delay is press Read.
function ttsReport(how){
  const ms=ttsAskedAt?Date.now()-ttsAskedAt:0;
  ttsAskedAt=0;
  if(TTS_DEBUG) toast('\\u25b6 '+ms+'ms \\u00b7 '+how+' \\u00b7 warm: '+ttsWarmState);
  else if(ms>3000&&!ttsSlowSaid){
    ttsSlowSaid=true;
    toast('\\u23f3 The voice took '+(ms/1000).toFixed(1)+'s to start');
  }
}
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
    if(k===0) u.onstart=()=>{
      started=true;
      ttsReport((plain?'plain retry':chunks.length+' chunk'+(chunks.length===1?'':'s'))+
                (voice?' \\u00b7 '+voice.name:' \\u00b7 default voice'));
      if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); }
    };
    if(k===chunks.length-1) u.onend=done;
    u.onerror=done;
    ss.speak(u);
  });
  return ()=>started||ss.speaking;
}""")

sub("""    ss.cancel();
    try{ if(ss.paused) ss.resume(); }catch(e){}
    ttsOn=true; renderTtsBtn();""",
"""    ss.cancel();
    try{ if(ss.paused) ss.resume(); }catch(e){}
    ttsAskedAt=Date.now();
    ttsOn=true; renderTtsBtn();""")

sub("""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend,""",
"""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend, TTS_DEBUG,
    get ttsAskedAt(){return ttsAskedAt;},""")

PAGE.write_text(s, encoding="utf-8")
print("the app times its own reading now · page %.2f MB" % (len(s) / 1e6))
