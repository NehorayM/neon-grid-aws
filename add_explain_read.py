#!/usr/bin/env python3
"""A Read button on the explanation.

Asked for: a read button for the explanations that reads the text aloud. "What happened in
this question" gets a 🔊 Read / ⏹ Stop button that reads the verdict, then the situation, what
they asked for, why the answer is right and why your pick is not — the block, in order.

It reads through the same engine as the question's Read (voice, speed, pitch, the watchdog
that retries a silent engine), but it is not that button: on the exams that taper the
question's Read away, renderTtsBtn stopped any speech on a question where reading is off —
which would have cut the explanation off the moment it started. The explanation's reading is
flagged (exTts) and the question button neither stops it nor lights up for it. Moving to the
next question stops it, as it stops the question's reading.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)

# the explanation's reading is its own
sub("""let ttsOn=false;""","""let ttsOn=false;
let exTts=false;            // what is being read is the explanation, not the question""")
sub("""function ttsSpeak(text){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return false; }""",
"""function ttsSpeak(text,opts){
  if(!ttsOk()) { toast('This browser cannot read aloud'); return false; }
  exTts=!!(opts&&opts.ex);""")
sub("""function renderTtsBtn(){
  const b=$('simTts'); if(!b) return;
  const allowed=!sim||readAllowed(sim.paper,sim.i);
  b.classList.toggle('hidden',!allowed);
  if(!allowed&&ttsOn) ttsStop();
  b.classList.toggle('on',ttsOn);
  b.textContent=ttsOn?'⏹ Stop':'🔊 Read';
  b.title=ttsOn?'Stop reading':'Read the question aloud';
}""","""function renderTtsBtn(){
  if(!ttsOn) exTts=false;
  renderExReadBtn();
  const b=$('simTts'); if(!b) return;
  const allowed=!sim||readAllowed(sim.paper,sim.i);
  // the question's reading only: the explanation's is allowed on every question, and the
  // question button neither stops it nor shows Stop for it
  const mine=ttsOn&&!exTts;
  b.classList.toggle('hidden',!allowed);
  if(!allowed&&mine) ttsStop();
  b.classList.toggle('on',mine);
  b.textContent=mine?'⏹ Stop':'🔊 Read';
  b.title=mine?'Stop reading':'Read the question aloud';
}
// ---------- reading the explanation ----------
function renderExReadBtn(){
  const b=document.querySelector('#explain .exread'); if(!b) return;
  const on=ttsOn&&exTts;
  b.classList.toggle('on',on);
  b.textContent=on?'\\u23f9 Stop':'\\u{1f50a} Read';
  b.setAttribute('aria-label',on?'Stop reading the explanation':'Read the explanation aloud');
}
// what the block says, in reading order: the verdict, then each row as "heading. text."
function exReadText(){
  const box=$('explain'); if(!box) return '';
  const parts=[];
  const head=box.querySelector('.exhead');
  if(head){ const h=head.cloneNode(true); h.querySelectorAll('.tag').forEach(x=>x.remove()); parts.push(h.textContent.trim().replace(/([^.!?])$/,'$1.')); }
  box.querySelectorAll('.exstory .exsrow').forEach(r=>{
    const k=(r.querySelector('.exsk')||{}).textContent||'';
    const v=[...r.querySelectorAll('.exsask')].map(x=>x.textContent.trim()).join(' ')||((r.querySelector('.exsv')||{}).textContent||'');
    parts.push(k.trim()+'. '+v.trim());
  });
  return parts.join(' ').replace(/\\s*[\\u2014\\u2013]\\s*/g,', ').replace(/[\\u2705\\u274c\\u23f1\\u2191\\u2192]/g,'').replace(/\\s+/g,' ').trim();
}
function exReadToggle(){
  if(ttsOn&&exTts){ ttsStop(); renderTtsBtn(); return; }
  const text=exReadText(); if(!text) return;
  ensureAudio&&ensureAudio();
  ttsSpeak(text,{ex:true});
  renderExReadBtn();
}""")

# the button, in the block's header
sub("""  return '<div class="exstory"><div class="exstoryh">\\u{1f50e} What happened in this question</div>'+""",
"""  return '<div class="exstory"><div class="exstoryh"><span>\\u{1f50e} What happened in this question</span>'+
    (ttsOk()?'<button type="button" class="exread" aria-label="Read the explanation aloud">\\u{1f50a} Read</button>':'')+'</div>'+""")
sub("""  box.innerHTML=bits.join('');""","""  box.innerHTML=bits.join('');
  { const rb=box.querySelector('.exread'); if(rb){ rb.onclick=exReadToggle; renderExReadBtn(); } }""")
sub(""".exstoryh{font-size:12.5px;font-weight:650;color:var(--dim);margin-bottom:6px}""",
""".exstoryh{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:12.5px;font-weight:650;color:var(--dim);margin-bottom:6px}
.exread{flex:none;font-size:12px;font-weight:650;min-height:34px;padding:6px 12px;border-radius:9px;
  border:1px solid color-mix(in srgb, var(--cyan) 40%, transparent);background:color-mix(in srgb, var(--cyan) 10%, transparent);color:var(--cyan)}
.exread.on{border-color:var(--gold);color:var(--gold);background:color-mix(in srgb, var(--gold) 12%, transparent)}""")

sub("""    qStory, hiQual, renderStory,""","""    qStory, hiQual, renderStory, exReadText, exReadToggle, get exTts(){return exTts;}, get ttsOn(){return ttsOn;},""")
PAGE.write_text(s, encoding="utf-8"); print("explanation has a Read button")
