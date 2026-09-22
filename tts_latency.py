#!/usr/bin/env python3
"""Make Read start speaking at once instead of after several seconds.

Three things were stacking up between the tap and the first sound:

  1. The voice was picked with `getVoices().find(v => /^en/.test(v.lang))` — the
     FIRST English voice in the list. On Chrome that is usually one of the Google
     network voices, which fetches its audio from a server before it says
     anything. A local voice starts immediately. That was most of the wait.

  2. The whole stem went in as one utterance. The median exam question is 411
     characters and 85% are over 300, and the engine prepares the whole utterance
     before emitting a sound — with a network voice, that means fetching all of
     it. Split into sentence-sized pieces the first one is short, so speech
     starts almost at once and the rest queues behind it.

  3. cancel() was called before every speak(), even with nothing speaking. The
     cancel/speak race is a long-standing Chrome bug that delays or swallows the
     utterance. It now only cancels when something is actually speaking.

Also: the voice list is fetched once at boot and refreshed on voiceschanged
rather than being asked for at the moment of the tap (getVoices() is populated
asynchronously and the first call often returns an empty list), and the button
waits for onstart, so "Stop" means it really is speaking.

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


sub("""function ttsStop(){
  ttsOn=false;
  try{ if(ttsOk()) window.speechSynthesis.cancel(); }catch(e){}
  renderTtsBtn();
}""",
"""let ttsSeq=0;
function ttsStop(){
  ttsOn=false; ttsSeq++;              // anything still queued from before is now stale
  try{ if(ttsOk()) window.speechSynthesis.cancel(); }catch(e){}
  renderTtsBtn();
}

// getVoices() is filled in asynchronously and the first call usually returns nothing,
// so the list is warmed at boot and refreshed rather than asked for at the tap.
let ttsVoices=[];
function ttsLoadVoices(){
  try{ ttsVoices=window.speechSynthesis.getVoices()||[]; }catch(e){ ttsVoices=[]; }
  return ttsVoices;
}
function ttsVoice(){
  const list=(ttsVoices&&ttsVoices.length)?ttsVoices:ttsLoadVoices();
  const en=list.filter(v=>/^en/i.test(v.lang||''));
  // A local voice speaks the moment it is asked. A network one fetches its audio from a
  // server first, which is where the several-second wait before any sound came from —
  // and on Chrome a Google network voice is usually first in the list.
  return en.find(v=>v.localService)||en.find(v=>/^en[-_]US/i.test(v.lang))||en[0]||null;
}
if(typeof window!=='undefined'&&'speechSynthesis' in window){
  ttsLoadVoices();
  try{ window.speechSynthesis.addEventListener('voiceschanged',ttsLoadVoices); }
  catch(e){ try{ window.speechSynthesis.onvoiceschanged=ttsLoadVoices; }catch(e2){} }
}

// The engine prepares a whole utterance before it makes a sound, and the median question
// here is 411 characters. Cut into sentence-sized pieces the first one is short, so it
// starts speaking straight away and the rest queue behind it.
function ttsChunks(text,max){
  max=max||160;
  const out=[]; let buf='';
  String(text||'').split(/(?<=[.!?;:])\\s+/).forEach(part=>{
    let p=part.trim();
    while(p.length>max){                       // one clause longer than a whole chunk
      let cut=p.lastIndexOf(', ',max);
      if(cut<max*0.4) cut=p.lastIndexOf(' ',max);
      if(cut<=0) cut=max;
      out.push(p.slice(0,cut).trim()); p=p.slice(cut).trim();
    }
    if(!p) return;
    if(!buf) buf=p;
    else if((buf+' '+p).length<=max) buf=buf+' '+p;
    else { out.push(buf); buf=p; }
  });
  if(buf) out.push(buf);
  return out.filter(Boolean);
}""")

sub("""function ttsSpeak(text){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return false; }
  try{
    window.speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(text);
    u.rate=P.ttsRate||1; u.lang='en-US';
    u.onend=u.onerror=()=>{ ttsOn=false; renderTtsBtn(); };
    const v=(window.speechSynthesis.getVoices()||[]).find(x=>/^en/i.test(x.lang));
    if(v) u.voice=v;
    window.speechSynthesis.speak(u);
    ttsOn=true; renderTtsBtn();
    // a browser with no voices installed accepts speak() and stays silent, so say so
    // rather than leaving the reader wondering whether the tap registered
    if(!TEST) setTimeout(()=>{
      try{
        const ss=window.speechSynthesis;
        if(!ss.speaking&&!ss.pending&&!(ss.getVoices()||[]).length){
          ttsOn=false; renderTtsBtn();
          toast('No speech voices are installed in this browser');
        }
      }catch(e){}
    },400);
    return true;
  }catch(e){ return false; }
}""",
"""function ttsSpeak(text){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return false; }
  const ss=window.speechSynthesis;
  const seq=++ttsSeq;                 // a later tap makes this batch's callbacks stale
  try{
    // only cancel if there is something to cancel: cancel() straight into speak() is a
    // long-standing Chrome race that delays or drops the utterance entirely
    if(ss.speaking||ss.pending) ss.cancel();
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
}""")

sub("""    simSpeak, ttsToggle, renderTtsBtn, renderExamBrief, BRIEF_PAPERS, buildBriefing,""",
"""    ttsChunks, ttsVoice, ttsLoadVoices, get ttsVoices(){return ttsVoices;},
    simSpeak, ttsToggle, renderTtsBtn, renderExamBrief, BRIEF_PAPERS, buildBriefing,""")

PAGE.write_text(s, encoding="utf-8")
print("Read starts at once now · page %.2f MB" % (len(s) / 1e6))
