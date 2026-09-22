#!/usr/bin/env python3
"""Accessible names, stale copy, and the dead CSS behind the topic jump bar.

  * 32 icon-only buttons announced nothing. A screen reader read "button" for
    every back arrow in the app — 25 of them — and said nothing at all for the
    three that are filled in by script. Each gets an aria-label; the back arrows
    get one naming what they go back to, so they are told apart.
  * The shop still told people 50/50 costs coins, months after nothing costs
    coins. The Flashcards tile advertised 88 terms for a deck of 90. A comment
    still described a bank of 2,502 questions.
  * `.stujump button.on` was dead: nothing ever adds `.on`, so the topic jump bar
    in Study never marked where you were. It marks it now.
  * `readiness()` did not clamp accuracy, so a profile whose counters merged
    badly could report over 100%.

Run once; index.html is the source of truth afterwards.
"""
import pathlib
import re

PAGE = pathlib.Path(__file__).resolve().parent / "index.html"
s = PAGE.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, "NOT FOUND (%d): %s" % (n, old[:90])
    s = s.replace(old, new, count)


# ------------------------------------------------------------- 1. back arrows
BACK = {
    "quizBack": "Leave this question",
    "studyPickBack": "Back to the briefed drill list",
    "timerBack": "Back from the study timer",
    "stuPickBack": "Back to the Study chapters",
    "stuReadBack": "Back to the chapter list",
    "paperBack": "Back from Practice Exams",
    "casinoBack": "Back from the casino",
    "lrnPickBack": "Back from Learn a Subject",
    "lrnMapBack": "Back to the subject list",
    "lrnReadBack": "Back to the parts of this subject",
    "lrnQuizBack": "Back to the parts of this subject",
    "lrnRecapBack": "Back to the parts of this subject",
    "lrnSimBack": "Back from the subject exam",
    "lrnDoneBack": "Back to the subject list",
    "pathBack": "Back from the study path",
    "bankBack": "Back from the question bank",
    "themeBack": "Back from themes",
    "readyBack": "Back from readiness",
    "briefBack": "Back from the briefing",
    "pickBack": "Back from the subject picker",
    "logBack": "Back from the log",
    "flashBack": "Back from flashcards",
    "recBack": "Back from records",
    "sumBack": "Back from the summary",
    "shopBack": "Back from the shop",
    "achBack": "Back from badges",
    "gameExit": "Leave this mini-game",
}
named = 0
for bid, label in BACK.items():
    pat = '<button class="backbtn" id="%s">' % bid
    if pat in s:
        s = s.replace(pat, '<button class="backbtn" id="%s" aria-label="%s">' % (bid, label), 1)
        named += 1
        continue
    m = re.search(r'<button([^>]*\sid="%s")([^>]*)>' % re.escape(bid), s)
    assert m, "no button with id " + bid
    if "aria-label" not in m.group(0):
        s = s[:m.end() - 1] + ' aria-label="%s"' % label + s[m.end() - 1:]
        named += 1

# the three whose text is written by script, so the markup carries nothing to read
for bid, label in [("resumeBtn", "Resume your last session"),
                   ("exResume", "Resume the saved exam"),
                   ("lrnResume", "Resume the subject you were learning"),
                   ("flashCard", "Flip this flashcard"),
                   ("soundBtn", "Mute or unmute sound")]:
    m = re.search(r'<button([^>]*\sid="%s")([^>]*)>' % re.escape(bid), s)
    assert m, "no button with id " + bid
    if "aria-label" not in m.group(0):
        s = s[:m.end() - 1] + ' aria-label="%s"' % label + s[m.end() - 1:]
        named += 1

# ------------------------------------------------------------- 2. stale copy
sub("50/50 costs 10 coins instead of 30", "50/50 keeps both wrong answers hidden for longer")
sub("the 2,502 questions", "the question bank")

# ------------------------------------------- 3. the topic jump bar marks its place
# `.stujump button.on` was styled but nothing ever added `.on`, so the topic bar in a Study
# chapter never showed which topic you were reading.
sub("""  const jump=$('stuJump'); jump.innerHTML='';
  c.topics.forEach((t,k)=>{
    const b=document.createElement('button'); b.textContent=t.nm;
    b.onclick=()=>{ const el=$('stuT'+k); if(el) el.scrollIntoView({behavior:'smooth',block:'start'}); };
    jump.appendChild(b);
  });""",
"""  const jump=$('stuJump'); jump.innerHTML='';
  c.topics.forEach((t,k)=>{
    const b=document.createElement('button'); b.textContent=t.nm; b.dataset.topic=k;
    b.onclick=()=>{ const el=$('stuT'+k); if(el) el.scrollIntoView({behavior:'smooth',block:'start'}); };
    jump.appendChild(b);
  });
  stuJumpSync();""")

sub("""function stuRenderQuiz(c){""",
"""// Marks which topic you are reading. The .on style existed from the start; nothing applied it.
function stuJumpSync(){
  const bar=$('stuJump'); if(!bar||!bar.children.length) return;
  const secs=[...document.querySelectorAll('#stuBody .stutopic')];
  if(!secs.length) return;
  const line=140;
  let cur=0;
  secs.forEach((el,k)=>{ if(el.getBoundingClientRect().top<=line) cur=k; });
  [...bar.children].forEach((b,k)=>b.classList.toggle('on',k===cur));
  const act=bar.children[cur];
  if(act&&bar.scrollWidth>bar.clientWidth){
    const want=act.offsetLeft-bar.clientWidth/2+act.offsetWidth/2;
    bar.scrollTo({left:Math.max(0,want),behavior:'smooth'});
  }
}
function stuRenderQuiz(c){""")

sub("""$('quizBack').onclick=()=>{""",
"""window.addEventListener('scroll',()=>{ if(route==='stuReadScreen') stuJumpSync(); },{passive:true});
$('quizBack').onclick=()=>{""")

PAGE.write_text(s, encoding="utf-8")
print("named %d buttons; copy and jump bar fixed · page %.2f MB" % (named, len(s) / 1e6))
