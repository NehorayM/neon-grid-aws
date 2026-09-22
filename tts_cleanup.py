#!/usr/bin/env python3
"""Take the diagnostics back out now that the read-aloud delay is fixed.

Removed:
  * tts_probe.html, the standalone latency probe
  * the ?ttsdebug=1 readout and everything only it used — TTS_DEBUG, ttsReport(),
    ttsAskedAt, ttsSlowSaid, and the ttsWarmState string the toast printed

Kept, because these are the fix rather than the instrumentation:
  * ttsWarm() waking the engine on the first touch (the 4.6s cold start)
  * ttsVoice() returning null, so nothing picks one of the ChromeOS voices that
    report localService:true and never speak
  * the 900ms watchdog and its plain retry
  * the sentence-sized chunking

Both diagnostics are in git history if this ever comes back: tts_probe.html at
10bd287, the in-app readout at 81803b3.

Run once; index.html is the source of truth afterwards.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# ------------------------------------------------------- the debug readout
sub("""const TTS_DEBUG=typeof location!=='undefined'&&/[?&]ttsdebug=1/.test(location.search);
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
function ttsSend(text,seq,plain){""",
"""function ttsSend(text,seq,plain){""")

sub("""    if(k===0) u.onstart=()=>{
      started=true;
      ttsReport((plain?'plain retry':chunks.length+' chunk'+(chunks.length===1?'':'s'))+
                (voice?' \\u00b7 '+voice.name:' \\u00b7 default voice'));
      if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); }
    };""",
"""    if(k===0) u.onstart=()=>{ started=true; if(seq===ttsSeq){ ttsOn=true; renderTtsBtn(); } };""")

sub("""    ss.cancel();
    try{ if(ss.paused) ss.resume(); }catch(e){}
    ttsAskedAt=Date.now();
    ttsOn=true; renderTtsBtn();""",
"""    ss.cancel();
    try{ if(ss.paused) ss.resume(); }catch(e){}
    ttsOn=true; renderTtsBtn();""")

# --------------------------------- the warm-up no longer narrates what it did
sub("""let ttsWarmed=false, ttsWarmState='not started';
function ttsWarm(){
  if(ttsWarmed||!ttsOk()||TEST) return;
  ttsWarmed=true; ttsWarmState='waking';
  try{
    const u=new SpeechSynthesisUtterance('ok');
    u.volume=0; u.rate=1; u.lang='en-US';
    const t0=Date.now();
    u.onstart=()=>{ ttsWarmState='awake after '+(Date.now()-t0)+'ms'; };
    u.onend=()=>{ if(ttsWarmState==='waking') ttsWarmState='ended without starting'; };
    u.onerror=e=>{ ttsWarmState='failed: '+((e&&e.error)||'error'); };
    window.speechSynthesis.speak(u);
  }catch(e){ ttsWarmState='threw'; }
}""",
"""let ttsWarmed=false;
function ttsWarm(){
  if(ttsWarmed||!ttsOk()||TEST) return;
  ttsWarmed=true;
  try{
    const u=new SpeechSynthesisUtterance('ok');
    u.volume=0; u.rate=1; u.lang='en-US';
    u.onend=u.onerror=()=>{};        // attached so the queue is known to drain
    window.speechSynthesis.speak(u);
  }catch(e){}
}""")

sub("""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend, TTS_DEBUG,
    get ttsAskedAt(){return ttsAskedAt;},
    get ttsVoices(){return ttsVoices;}, get ttsWarmState(){return ttsWarmState;},
    get ttsWarmed(){return ttsWarmed;},""",
"""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend,
    get ttsVoices(){return ttsVoices;}, get ttsWarmed(){return ttsWarmed;},""")

assert "ttsdebug" not in s and "ttsReport" not in s and "ttsWarmState" not in s
assert "ttsAskedAt" not in s and "TTS_DEBUG" not in s

PAGE.write_text(s, encoding="utf-8")
(HERE / "tts_probe.html").unlink(missing_ok=True)
print("probe deleted, debug readout removed · page %.2f MB" % (len(s) / 1e6))
