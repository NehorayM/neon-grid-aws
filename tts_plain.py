#!/usr/bin/env python3
"""Make Read a plain on/off button, and stop it reading out the options.

It had two behaviours stacked on one button: one tap read the question, a
second tap while it was still talking armed auto-read for the rest of the
paper. Nobody can discover that, and auto-read then talks over you every time
you move. Now it is what it says: tap to read, tap again to stop.

It also read every option aloud after the stem. The options are on the screen
and a reader following along does not need them spoken, so the reading is the
question's position and its stem, and stops there.

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


# ------------------------------------------------------- 1. the stem, not the options
sub("""function ttsText(q,i,total){
  return 'Question '+(i+1)+' of '+total+'. '+q.q+' '+
    q.o.map(o=>'Option '+o[0]+'. '+o[1]+'.').join(' ');
}""",
"""function ttsText(q,i,total){
  // the stem only — the options are on the screen in front of whoever is listening
  return 'Question '+(i+1)+' of '+total+'. '+q.q;
}""")

# --------------------------------------------- 2. the button knows when it is talking
sub("""function ttsStop(){ try{ if(ttsOk()) window.speechSynthesis.cancel(); }catch(e){} }""",
"""// speechSynthesis.speaking lags behind cancel() in some browsers, so the button
// follows our own flag and the utterance's own end event instead
let ttsOn=false;
function ttsStop(){
  ttsOn=false;
  try{ if(ttsOk()) window.speechSynthesis.cancel(); }catch(e){}
  renderTtsBtn();
}""")

sub("""    const u=new SpeechSynthesisUtterance(text);
    u.rate=P.ttsRate||1; u.lang='en-US';""",
"""    const u=new SpeechSynthesisUtterance(text);
    u.rate=P.ttsRate||1; u.lang='en-US';
    u.onend=u.onerror=()=>{ ttsOn=false; renderTtsBtn(); };""")

sub("""    window.speechSynthesis.speak(u);
    // a browser with no voices installed accepts speak() and stays silent, so say so""",
"""    window.speechSynthesis.speak(u);
    ttsOn=true; renderTtsBtn();
    // a browser with no voices installed accepts speak() and stays silent, so say so""")

sub("""        if(!ss.speaking&&!ss.pending&&!(ss.getVoices()||[]).length)
          toast('No speech voices are installed in this browser');""",
"""        if(!ss.speaking&&!ss.pending&&!(ss.getVoices()||[]).length){
          ttsOn=false; renderTtsBtn();
          toast('No speech voices are installed in this browser');
        }""")

# --------------------------------------------------------- 3. read / stop, nothing else
sub("""function ttsToggle(){
  // one tap reads this question; a second tap turns auto-read on for the rest
  if(!ttsOk()){ toast('This browser cannot read aloud'); return; }
  if(P.ttsAuto){ P.ttsAuto=0; ttsStop(); toast('\\u{1f507} Auto-read off'); }
  else if(window.speechSynthesis.speaking){ P.ttsAuto=1; toast('\U0001f50a Auto-read on'); }
  else { simSpeak(); }
  saveProfile(); renderTtsBtn();
}
function renderTtsBtn(){
  const b=$('simTts'); if(!b) return;
  b.classList.toggle('on',!!P.ttsAuto);
  b.textContent=P.ttsAuto?'\U0001f50a Auto':'\U0001f50a Read';
}""".replace("\\u{1f507}", "\U0001f507"),
"""function ttsToggle(){
  // read, or stop reading. That is the whole button.
  if(!ttsOk()){ toast('This browser cannot read aloud'); return; }
  if(ttsOn) ttsStop();
  else simSpeak();
  renderTtsBtn();
}
function renderTtsBtn(){
  const b=$('simTts'); if(!b) return;
  b.classList.toggle('on',ttsOn);
  b.textContent=ttsOn?'⏹ Stop':'\U0001f50a Read';
  b.title=ttsOn?'Stop reading':'Read the question aloud';
}""")

# --------------------------------------------- 4. nothing reads itself any more
sub("""  renderTtsBtn();""", """  renderTtsBtn();""")   # keep the call, drop the auto-speak below it
sub("""  ttsStop();
  if(P.ttsAuto) simSpeak();""",
"""  ttsStop();""")

PAGE.write_text(s, encoding="utf-8")
print("Read is a plain toggle now · page %.2f MB" % (len(s) / 1e6))
