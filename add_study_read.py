#!/usr/bin/env python3
"""A read-aloud button on every paragraph of a Study chapter — tables left out.

Asked for: a read button in the study sections, for every paragraph, not for tables.

Each paragraph, "Must know" and "Exam trap" callout, note and list in a Study chapter gets a
small 🔊 button. It reads that block — the text as it is on screen, without the icons — through
the same engine and voice settings as the question's Read. Tapping it again (⏹) stops;
tapping another paragraph moves the reading there; leaving the chapter stops it. Tables, the
flow diagrams, decision trees, split columns and code are not given one.

The speech engine has one current reader now (ttsOwner: the question, the explanation, or a
paragraph), so each button shows Stop only for what it started, and the rule that stops the
question's reading on the exams that taper it never touches a paragraph.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

# ---- one current reader
sub("""let exTts=false;            // what is being read is the explanation, not the question""",
"""let exTts=false;            // what is being read is the explanation, not the question
let ttsOwner='q';           // who started the reading: 'q' the question, 'ex' the explanation, 'para' a Study paragraph
let paraOn=null;            // the paragraph being read""")
sub("""  exTts=!!(opts&&opts.ex);""","""  exTts=!!(opts&&opts.ex);
  ttsOwner=(opts&&opts.owner)||(exTts?'ex':'q');""")
sub("""function renderTtsBtn(){
  if(!ttsOn) exTts=false;
  renderExReadBtn();""","""function renderTtsBtn(){
  if(!ttsOn){ exTts=false; ttsOwner='q'; paraOn=null; }
  renderExReadBtn(); renderParaBtns();""")
sub("""  const on=ttsOn&&exTts;
  b.classList.toggle('on',on);
  b.textContent=on?'\\u23f9 Stop':'\\u{1f50a} Read';""","""  const on=ttsOn&&exTts&&ttsOwner==='ex';
  b.classList.toggle('on',on);
  b.textContent=on?'\\u23f9 Stop':'\\u{1f50a} Read';""")

# ---- the paragraphs
sub("""function exReadToggle(){""","""// ---------- reading a Study paragraph ----------
const PARA_READ=new Set(['p','key','trap','note','list','steps']);   // not tables, diagrams or code
function paraText(el){
  const c=el.cloneNode(true);
  c.querySelectorAll('.parread,.ic').forEach(x=>x.remove());
  return c.textContent.replace(/\\s*[\\u2014\\u2013]\\s*/g,', ').replace(/[\\u2b50\\u26a0\\u270e\\u2192\\u2191]/g,'')
    .replace(/\\s+/g,' ').trim();
}
function paraRead(btn){
  const el=btn.closest('.rdpara'); if(!el) return;
  if(ttsOn&&ttsOwner==='para'&&paraOn===el){ ttsStop(); renderTtsBtn(); return; }
  const text=paraText(el); if(!text) return;
  ensureAudio&&ensureAudio();
  paraOn=el;
  ttsSpeak(text,{ex:true,owner:'para'});
  paraOn=el;                           // ttsSpeak's own repaint must not lose which one it is
  renderParaBtns();
}
function renderParaBtns(){
  document.querySelectorAll('#stuBody .rdpara').forEach(el=>{
    const on=ttsOn&&ttsOwner==='para'&&paraOn===el;
    el.classList.toggle('reading',on);
    const b=el.querySelector('.parread'); if(!b) return;
    b.textContent=on?'\\u23f9':'\\u{1f50a}';
    b.setAttribute('aria-label',on?'Stop reading':'Read this paragraph aloud');
    b.classList.toggle('on',on);
  });
}
// the chapter's blocks, each readable one with its own button
function studyBlocksHTML(arr){
  return (arr||[]).map(b=>{
    const html=lbHTML(b);
    if(!html||!PARA_READ.has(b.t)||!ttsOk()) return html;
    return '<div class="rdpara">'+html+'<button type="button" class="parread" aria-label="Read this paragraph aloud">\\u{1f50a}</button></div>';
  }).join('');
}
function exReadToggle(){""")
sub("""  $('stuBody').innerHTML=c.topics.map((t,k)=>
    '<section class="stutopic" id="stuT'+k+'"><h2>'+esc(t.nm)+'</h2>'+blocksHTML(t.blocks)+'</section>'
  ).join('');""","""  if(ttsOn&&ttsOwner==='para') ttsStop();       // a new chapter: the old paragraph stops
  $('stuBody').innerHTML=c.topics.map((t,k)=>
    '<section class="stutopic" id="stuT'+k+'"><h2>'+esc(t.nm)+'</h2>'+studyBlocksHTML(t.blocks)+'</section>'
  ).join('');
  $('stuBody').querySelectorAll('.parread').forEach(b=>{ b.onclick=()=>paraRead(b); });""")
# leaving the chapter stops it
sub("""  SCREENS.forEach(s=>$(s).classList.toggle('hidden',s!==id)); route=id;""",
"""  if(route==='stuReadScreen'&&id!=='stuReadScreen'&&typeof ttsOwner!=='undefined'&&ttsOn&&ttsOwner==='para') ttsStop();
  SCREENS.forEach(s=>$(s).classList.toggle('hidden',s!==id)); route=id;""")
sub(""".stutopic{scroll-margin-top:86px;padding-top:6px}""",""".stutopic{scroll-margin-top:86px;padding-top:6px}
/* a read-aloud button on each paragraph: in the gutter, out of the text's way */
.rdpara{position:relative;padding-right:40px;border-radius:10px;transition:background .2s}
.rdpara.reading{background:color-mix(in srgb, var(--cyan) 7%, transparent)}
.parread{position:absolute;top:2px;right:0;width:34px;height:34px;border-radius:9px;display:grid;place-items:center;
  font-size:14px;background:transparent;border:1px solid var(--line);color:var(--dim);opacity:.75}
.parread:hover,.parread.on{opacity:1;border-color:var(--cyan);color:var(--cyan)}
.parread.on{background:color-mix(in srgb, var(--cyan) 12%, transparent)}""")
sub("""    qStory, hiQual, renderStory, exReadText, exReadToggle, get exTts(){return exTts;}, get ttsOn(){return ttsOn;},""",
"""    qStory, hiQual, renderStory, exReadText, exReadToggle, get exTts(){return exTts;}, get ttsOn(){return ttsOn;},
    paraRead, paraText, studyBlocksHTML, get ttsOwner(){return ttsOwner;},""")
PAGE.write_text(s, encoding="utf-8"); print("study paragraphs can be read aloud")
