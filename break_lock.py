#!/usr/bin/env python3
"""A break has to keep you out of the paper, or it looks like a broken clock.

Reported as "the timer isn't working". Reproduced: start a paper, take a break,
then walk back in through Exam -> Resume. You land on the question screen with
both clocks frozen — correctly, the paper is paused — and sit looking at a dead
1:30 for up to six minutes. From the outside that is indistinguishable from a
broken timer, and it was my design that allowed it.

The break is six minutes exactly, so the answer is not to resume early on
re-entry. It is that during those six minutes the paper is not somewhere you can
be. Going back is refused with the time remaining, the banner says the paper
comes back on its own, and when the six minutes are up it takes you there.

  * go() refuses any in-paper screen while a break is running
  * the resume row and the top-bar clock say "on a break" rather than showing a
    countdown that is not counting
  * the banner reads "Paper resumes in 4:12" instead of just sitting there

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


# ------------------------------------------- the paper is not a place during a break
sub("""go=function(id){
  // Walking out of a running paper is either a break or refused. A break in progress lets you
  // move freely, which is the whole point of it.
  if(typeof sim!=='undefined'&&sim&&sim.running&&!IN_PAPER[id]&&!brkOn()
     &&route==='quizScreen'&&typeof brkAsk==='function'){
    if(brkAsk(()=>{ _go(id); syncNav(); })) return;
    if(!brkLeft()) return;                   // no breaks left: the paper keeps you
  }""",
"""go=function(id){
  // A break freezes both clocks, so being inside the paper during one means looking at a dead
  // countdown — which is exactly what "the timer isn't working" turned out to be. For those six
  // minutes the paper is not somewhere you can be, and it takes you back itself when they end.
  if(typeof brkOn==='function'&&brkOn()&&IN_PAPER[id]){
    toast('☕ Break — the paper comes back in '+fmtClock(brkRemain()*1000));
    return;
  }
  // Walking out of a running paper is either a break or refused. A break in progress lets you
  // move freely, which is the whole point of it.
  if(typeof sim!=='undefined'&&sim&&sim.running&&!IN_PAPER[id]&&!brkOn()
     &&route==='quizScreen'&&typeof brkAsk==='function'){
    if(brkAsk(()=>{ _go(id); syncNav(); })) return;
    if(!brkLeft()) return;                   // no breaks left: the paper keeps you
  }""")

# ----------------------------------------------------- the banner explains itself
sub("""  bar.classList.remove('hidden');
  $('brkClock').textContent=fmtClock(brkRemain()*1000);""",
"""  bar.classList.remove('hidden');
  const txt=bar.querySelector('.btxt');
  if(txt) txt.textContent='Paper paused — it comes back on its own';
  $('brkClock').textContent=fmtClock(brkRemain()*1000);""")

# ------------------------------- the resume row does not offer a paper you cannot enter
sub("""    const mine=simOwns(sv);
    rbtn.classList.remove('hidden');
    rbtn.dataset.armed='';""",
"""    const mine=simOwns(sv);
    const paused=(typeof brkOn==='function')&&brkOn();
    rbtn.classList.remove('hidden');
    rbtn.dataset.armed='';""")

sub("""      '<span class="buy">'+(mine?'Resume':'Take over')+'</span>';
    rbtn.onclick=()=>simResumeHere(sv);""",
"""      '<span class="buy">'+(paused?fmtClock(brkRemain()*1000):mine?'Resume':'Take over')+'</span>';
    rbtn.onclick=()=>{
      if(paused){ toast('☕ Break — the paper comes back in '+fmtClock(brkRemain()*1000)); return; }
      simResumeHere(sv);
    };""")

sub("""    const savedHere=sv&&(sv.paper||0)===n;""",
"""    const onBreak=(typeof brkOn==='function')&&brkOn();
    const savedHere=sv&&(sv.paper||0)===n;""")

sub("""    b.onclick=()=>{
      const open=simSaved();
      if(savedHere){ simResumeHere(open||sv); return; }""",
"""    b.onclick=()=>{
      const open=simSaved();
      if(onBreak){ toast('☕ Break — the paper comes back in '+fmtClock(brkRemain()*1000)); return; }
      if(savedHere){ simResumeHere(open||sv); return; }""")

# --------------------------------- the top clock says paused rather than showing a dead number
sub("""    // the question's own 90 seconds is what governs now, so that is what the clock shows;
    // the paper's remaining budget is on the review screen, where it is actually useful
    const left=simQLeft*1000;
    el.textContent='⏳ '+fmtClock(left);
    el.classList.toggle('warn',simQLeft<=30);
    el.classList.toggle('crit',simQLeft<=10);""",
"""    // A frozen countdown reads as a broken one, so during a break the clock says so and
    // counts the break down instead of sitting on a number that is not moving.
    if(typeof brkOn==='function'&&brkOn()){
      el.textContent='☕ '+fmtClock(brkRemain()*1000);
      el.classList.remove('warn','crit');
      const sb=$('clockSub'); if(sb) sb.textContent='break · paper paused';
      return;
    }
    // the question's own 90 seconds is what governs now, so that is what the clock shows;
    // the paper's remaining budget is on the review screen, where it is actually useful
    const left=simQLeft*1000;
    el.textContent='⏳ '+fmtClock(left);
    el.classList.toggle('warn',simQLeft<=30);
    el.classList.toggle('crit',simQLeft<=10);""")

# ------------------------- when the break ends, brkEnd's simLoad() has to be allowed through
sub("""  if(sim&&sim.running){ simLoad(); }
}
function brkTick(){""",
"""  if(sim&&sim.running){ simLoad(); }        // brkUntil is already 0, so go() lets this through
}
function brkTick(){""")

PAGE.write_text(s, encoding="utf-8")
print("a break now keeps you out of the paper · page %.2f MB" % (len(s) / 1e6))
