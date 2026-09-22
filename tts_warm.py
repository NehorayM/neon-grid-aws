#!/usr/bin/env python3
"""The five seconds is a cold engine. Wake it before anyone asks.

Second probe run, fresh page load, same ChromeOS machine:

    1. short text, default voice              4591 ms   <- first utterance
    2. short text, right after cancel()        425 ms
    3. LONG text in one go                     438 ms
    4. short text again                        331 ms

The first utterance after a page load costs four and a half seconds. Every one
after it costs a third of a second. That is the reported delay, and it is the
engine starting up, not anything about the text or the cancel.

The first run of the probe could not show this, because by the time it reached
the warm-up line the engine had already been woken by the six lines above it.

So the warm-up comes back — it was the right idea, removed for the wrong reason.
What actually caused the silence was line 5 of the first run: the eight ChromeOS
voices that report localService:true and never speak, which the old ttsVoice()
preferred. That is already gone.

This warm-up is the careful version:

  * a real one-syllable word at volume 0, not a space — an engine that skips
    whitespace could hold it in the queue forever
  * onend and onerror attached, so the queue is known to have drained
  * no cancel afterwards. The previous one cancelled 1200ms later to tidy up,
    which is the one thing that can cut off whatever came next
  * fired from ensureAudio(), i.e. the first time the user touches anything,
    which is minutes before anyone reaches an exam and presses Read

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


sub("""// There was a zero-volume warm-up utterance here, to wake a cold engine on the first user
// gesture. It is gone: some engines never emit a silent utterance but still hold it in the
// queue, and everything spoken afterwards queues behind it and is never heard. Waking the
// engine is not worth a mode where the button does nothing at all.
let ttsWarmed=false;
function ttsWarm(){ ttsWarmed=true; }      // kept so ensureAudio() has something to call""",
"""// Measured: the first utterance after a page load takes 4591ms on a cold engine, and every
// one after it takes about 350ms. That is the whole delay. So the engine is woken the first
// time the user touches anything — minutes before they reach an exam and press Read.
//
// A real word rather than a space: an engine that skips whitespace could keep it in the
// queue forever and everything after it would be silent. And no tidy-up cancel afterwards,
// which is the one thing that could cut off whatever the user asks for next.
let ttsWarmed=false, ttsWarmState='not started';
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
}""")

sub("""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend,
    get ttsVoices(){return ttsVoices;},""",
"""    ttsChunks, ttsVoice, ttsVoicesEn, ttsLoadVoices, ttsWarm, ttsSend,
    get ttsVoices(){return ttsVoices;}, get ttsWarmState(){return ttsWarmState;},
    get ttsWarmed(){return ttsWarmed;},""")

PAGE.write_text(s, encoding="utf-8")
print("warm-up restored, without the tidy-up cancel · page %.2f MB" % (len(s) / 1e6))
