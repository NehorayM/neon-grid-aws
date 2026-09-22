#!/usr/bin/env python3
"""Two six-minute breaks per paper, and nothing else stops the clock.

Leaving the question screen mid-paper used to keep the clock running, so a look
at Study cost you exam time. Now leaving is a decision: a paper allows exactly
two breaks of exactly six minutes, and the clock is frozen for the whole of one.

  * trying to leave with a break in hand opens a sheet saying what it costs and
    how many are left. Confirming freezes both clocks and starts the six minutes.
  * both clocks stop dead for the break: the question's deadline and the paper's
    budget are each pushed out by the full six minutes when it ends, so nothing
    is spent while you are away.
  * a break is six minutes, not five and not seven. Coming back early is not a
    way to keep one in hand — the paper stays locked until the six minutes are up
    and then hands you straight back to the question you were on.
  * with both breaks spent, leaving is refused and the clock keeps running. That
    is the point of having two.

A banner counts the break down from wherever you are, so it is never a mystery
how long is left or that a paper is waiting.

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


# ------------------------------------------------------------------- markup
sub("""  <div id="studyModal" class="hidden">""",
"""  <!-- exam break -->
  <div id="brkAsk" class="hidden">
    <div class="sheet">
      <h3>☕ Take a break?</h3>
      <p class="sub" id="brkAskSub"></p>
      <div class="brkfacts">
        <div class="brkfact"><b id="brkAskLen">6:00</b><span>each break</span></div>
        <div class="brkfact"><b id="brkAskLeft">2</b><span>left on this paper</span></div>
      </div>
      <p class="sub" id="brkAskNote" style="margin-top:10px"></p>
      <button class="btn wide" id="brkAskGo" style="margin-top:12px">☕ Start the break</button>
      <button class="btn ghost sm" id="brkAskNo" style="width:100%;margin-top:8px">Stay on the question</button>
    </div>
  </div>
  <div id="brkBar" class="hidden">
    <span class="bem">☕</span>
    <span class="btxt">Break — the paper is paused</span>
    <span class="bclock" id="brkClock">6:00</span>
  </div>

  <div id="studyModal" class="hidden">""")

# ------------------------------------------------------------------ styling
sub("""#studyModal{position:absolute;inset:0;z-index:70;""",
"""#brkAsk{position:absolute;inset:0;z-index:72;display:flex;flex-direction:column;
  justify-content:flex-end;background:rgba(6,9,13,.72)}
#brkAsk.hidden{display:none}
.brkfacts{display:flex;gap:10px;margin-top:12px}
.brkfact{flex:1;text-align:center;padding:12px 8px;border-radius:12px;
  background:var(--surface);border:1px solid var(--line)}
.brkfact b{display:block;font-family:var(--mono);font-size:20px;font-weight:700;color:var(--cyan)}
.brkfact span{display:block;font-size:10.5px;color:var(--dim);margin-top:3px;letter-spacing:.3px}
#brkBar{position:fixed;left:10px;right:10px;bottom:74px;z-index:60;display:flex;align-items:center;
  gap:10px;padding:11px 14px;border-radius:13px;
  background:color-mix(in srgb, var(--cyan) 14%, var(--bg2));
  border:1px solid color-mix(in srgb, var(--cyan) 45%, var(--line));
  box-shadow:0 8px 26px rgba(0,0,0,.42)}
#brkBar.hidden{display:none}
#brkBar .bem{font-size:17px;flex:none}
#brkBar .btxt{flex:1;min-width:0;font-size:12.5px;color:var(--txt)}
#brkBar .bclock{font-family:var(--mono);font-size:17px;font-weight:700;color:var(--cyan);
  font-variant-numeric:tabular-nums}
#studyModal{position:absolute;inset:0;z-index:70;""")

# --------------------------------------------------------------- the engine
ENGINE = """
// ---------- two six-minute breaks per paper ----------
// Leaving the question screen used to cost exam time, so a glance at Study was expensive.
// A paper now allows exactly two breaks of exactly six minutes, and both clocks stop for one.
const BREAK_MAX=2, BREAK_SECS=360;
const brkLeft=()=>sim?Math.max(0,BREAK_MAX-(sim.brkUsed||0)):0;
const brkOn=()=>!!(sim&&sim.brkUntil&&sim.brkUntil>Date.now());
const brkRemain=()=>brkOn()?Math.max(0,Math.ceil((sim.brkUntil-Date.now())/1000)):0;

function brkStart(){
  if(!sim||!sim.running||brkOn()||!brkLeft()) return false;
  sim.brkUsed=(sim.brkUsed||0)+1;
  sim.brkUntil=Date.now()+BREAK_SECS*1000;
  simQStop();                       // the question's own countdown stops dead
  ttsStop();
  simPersist();
  renderBrk();
  toast('\\u2615 Break started \\u2014 6 minutes, the paper is paused');
  return true;
}
// Both clocks are deadlines, so a break is paid for by pushing them out by its full length.
function brkEnd(quiet){
  if(!sim||!sim.brkUntil) return;
  const over=BREAK_SECS*1000;
  sim.brkUntil=0;
  if(sim.running){
    if(sim.endAt) sim.endAt+=over;                 // the paper's budget
    if(sim.qEndAt) sim.qEndAt+=over;               // and this question's
  }
  simPersist();
  renderBrk();
  if(!quiet) toast('\\u23f0 Break over \\u2014 back to the paper');
  if(sim&&sim.running){ simLoad(); }
}
function brkTick(){
  if(!sim||!sim.brkUntil) return;
  if(brkRemain()<=0){ brkEnd(false); return; }
  renderBrk();
}
function renderBrk(){
  const bar=$('brkBar'); if(!bar) return;
  if(!brkOn()){ bar.classList.add('hidden'); return; }
  bar.classList.remove('hidden');
  $('brkClock').textContent=fmtClock(brkRemain()*1000);
}

// Asking. This is the one place in the app with a real yes/no sheet, because it costs one of
// only two breaks and freezes a running exam — an arm-then-confirm button is too easy to trip.
let brkPending=null;
function brkAsk(go2){
  if(!sim||!sim.running) return false;
  if(brkOn()) return false;
  if(!brkLeft()){
    toast('\\u23f1 No breaks left \\u2014 the clock keeps running');
    return false;
  }
  brkPending=go2||null;
  $('brkAskSub').textContent='Leaving the paper pauses it. This is one of your '+
    BREAK_MAX+' breaks, and it runs for the full six minutes \\u2014 the paper waits and comes '+
    'back to this question when it ends.';
  $('brkAskLen').textContent=fmtClock(BREAK_SECS*1000);
  $('brkAskLeft').textContent=brkLeft();
  $('brkAskNote').textContent=brkLeft()===1
    ? 'This is your last one. After it, leaving the paper is not offered and the clock keeps running.'
    : 'You have '+plural(brkLeft(),'break')+' on this paper.';
  $('brkAsk').classList.remove('hidden');
  return true;
}
function brkAskClose(){ $('brkAsk').classList.add('hidden'); brkPending=null; }
"""

sub("""// ================= READING VOICE =================""",
    ENGINE + """
// ================= READING VOICE =================""")

# --------------------------------------------- leaving the paper goes through it
sub("""const _go=go;
go=function(id){
  if(id!=='quizScreen') stopQTimer();        // leaving the quiz freezes the countdown
  _go(id);
  if(id==='quizScreen') resumeQTimer();      // coming back continues from where it stopped
  syncNav();
};""",
"""const _go=go;
// Screens that are still part of the paper — moving between them is not leaving it.
const IN_PAPER={quizScreen:1,simRevScreen:1,simDoneScreen:1};
go=function(id){
  // Walking out of a running paper is either a break or refused. A break in progress lets you
  // move freely, which is the whole point of it.
  if(typeof sim!=='undefined'&&sim&&sim.running&&!IN_PAPER[id]&&!brkOn()
     &&route==='quizScreen'&&typeof brkAsk==='function'){
    if(brkAsk(()=>{ _go(id); syncNav(); })) return;
    if(!brkLeft()) return;                   // no breaks left: the paper keeps you
  }
  if(id!=='quizScreen') stopQTimer();        // leaving the quiz freezes the countdown
  _go(id);
  if(id==='quizScreen') resumeQTimer();      // coming back continues from where it stopped
  syncNav();
};""")

# the break counts down wherever you are
sub("""  if(typeof sim!=='undefined'&&sim&&sim.running&&!TEST){
    if(!simQIv&&simQLeft>0&&route==='quizScreen') simQStart();
    else if(typeof simQSync==='function') simQSync();
  }""",
"""  if(typeof brkTick==='function') brkTick();
  if(typeof sim!=='undefined'&&sim&&sim.running&&!brkOn()&&!TEST){
    if(!simQIv&&simQLeft>0&&route==='quizScreen') simQStart();
    else if(typeof simQSync==='function') simQSync();
  }""")

# nothing counts down during a break
sub("""function simQSync(){
  if(!sim||!sim.running){ simQStop(); return; }
  if(!sim.qEndAt) return;""",
"""function simQSync(){
  if(!sim||!sim.running){ simQStop(); return; }
  if(brkOn()) return;                                           // the paper is paused
  if(!sim.qEndAt) return;""")

sub("""  if(sim&&sim.running&&simTimeLeft()<=0){ toast('⏳ Time expired — submitting'); simSubmit(true); }""",
"""  if(brkOn()) return;                       // a paused paper cannot expire
  if(sim&&sim.running&&simTimeLeft()<=0){ toast('⏳ Time expired — submitting'); simSubmit(true); }""")

# the break belongs to the run, so it survives leaving and resuming
sub("""             qt:sim.qt||{}, dev:sim.dev||DEVICE_ID, devKind:sim.devKind||DEVICE_KIND,""",
"""             qt:sim.qt||{}, brkUsed:sim.brkUsed||0, brkUntil:sim.brkUntil||0,
             dev:sim.dev||DEVICE_ID, devKind:sim.devKind||DEVICE_KIND,""")

sub("""       rev:sv.rev||{}, qt:sv.qt||{}, running:true, paper:sv.paper||0, mins:sv.mins,""",
"""       rev:sv.rev||{}, qt:sv.qt||{}, brkUsed:sv.brkUsed||0, brkUntil:sv.brkUntil||0,
       running:true, paper:sv.paper||0, mins:sv.mins,""")

# and it goes when the paper does
sub("""  simPersist();                 // keep it: the Practice Exams screen offers it back
  simQStop(); ttsStop(); hideExplain();
  { const stb=$('simTotal'); if(stb) stb.classList.add('hidden'); }""",
"""  simPersist();                 // keep it: the Practice Exams screen offers it back
  simQStop(); ttsStop(); hideExplain();
  { const stb=$('simTotal'); if(stb) stb.classList.add('hidden'); }
  { const bb=$('brkBar'); if(bb) bb.classList.add('hidden'); }
  brkAskClose();""")

sub("""$('navBadges').onclick=()=>{ renderBadges(); go('achScreen'); syncNav(); };""",
"""$('navBadges').onclick=()=>{ renderBadges(); go('achScreen'); syncNav(); };
$('brkAskGo').onclick=()=>{
  const after=brkPending;
  $('brkAsk').classList.add('hidden'); brkPending=null;
  if(brkStart()&&after) after();
};
$('brkAskNo').onclick=()=>brkAskClose();
$('brkAsk').onclick=e=>{ if(e.target&&e.target.id==='brkAsk') brkAskClose(); };""")

sub("""    simTotalLeft, simTotalFull, simQsLeft, renderSimTotal, simQSync, simAway, simBack,""",
"""    BREAK_MAX, BREAK_SECS, brkLeft, brkOn, brkRemain, brkStart, brkEnd, brkTick, brkAsk,
    brkAskClose, renderBrk, get brkPending(){return brkPending;},
    simTotalLeft, simTotalFull, simQsLeft, renderSimTotal, simQSync, simAway, simBack,""")

PAGE.write_text(s, encoding="utf-8")
print("breaks wired · page %.2f MB" % (len(s) / 1e6))
