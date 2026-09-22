#!/usr/bin/env python3
"""The validation and robustness findings: numbers nobody sanity-checked.

  * The custom timer took whatever was typed. 0/0/0 started a countdown that ran
    until the heat death of the session (it lands ~1.9 years out because endAt is
    now + 0 and everything downstream reads a negative remainder); 999999 rounds
    printed "16666:39:00 · round 1/999999". Work, rest and rounds are now clamped
    to something a person could actually sit through, and a timer of no length is
    refused rather than started.
  * A past exam date read "0 days to go · 900 questions/day" — the pace divided by
    a clamped 1 day and hit its own ceiling. A date in the past now says so.
    A date centuries out read "355118 days to go"; it is capped at two years.
  * paperQs(0) returned indices from -65, and paperQs(-1) from -130. Both are
    reachable from the test surface and from any future caller that forgets the
    argument is 1-based. It now refuses anything outside 1..PAPER_COUNT.
  * renderBadges() and renderShop() threw outright on a profile with no `badges`
    or `upgrades` — every other reader in the file guards with `||[]`. A profile
    merged from an older device, or one that lost a field, took the Badges and
    Shop screens down with it.

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


# ---------------------------------------------------------------- the timer
sub("""function startTimer(cfg){
  ensureAudio();
  timer={mode:cfg.mode,phase:'work',work:cfg.work,rest:cfg.rest||0,
         rounds:cfg.rounds||1,round:1,paused:false,done:false,label:cfg.nm||'Timer',
         endAt:Date.now()+cfg.work*60000};""",
"""// Nothing checked these. 0/0/0 started a countdown with no end, and 999999 rounds
// printed "16666:39:00 · round 1/999999" in a pill built for four characters.
const TIMER_MAX={work:240, rest:120, rounds:99};
function timerClamp(cfg){
  const num=(v,lo,hi)=>{
    const n=Math.floor(Number(v));
    return isFinite(n)?Math.min(hi,Math.max(lo,n)):lo;
  };
  return {mode:cfg.mode, nm:cfg.nm,
          work:num(cfg.work,0,TIMER_MAX.work),
          rest:num(cfg.rest,0,TIMER_MAX.rest),
          rounds:num(cfg.rounds,1,TIMER_MAX.rounds)};
}
function startTimer(raw){
  ensureAudio();
  const cfg=timerClamp(raw||{});
  if(cfg.work<1){ toast('A timer needs at least one minute of work'); return false; }
  timer={mode:cfg.mode,phase:'work',work:cfg.work,rest:cfg.rest||0,
         rounds:cfg.rounds||1,round:1,paused:false,done:false,label:cfg.nm||'Timer',
         endAt:Date.now()+cfg.work*60000};""")

sub("""  sfx.rank();
  go('homeScreen'); renderHome();
}
function saveTimerPref(cfg){""",
"""  sfx.rank();
  go('homeScreen'); renderHome();
  return true;
}
function saveTimerPref(cfg){""")

# ------------------------------------------------------------- the exam date
sub("""function examDaysLeft(){
  if(!P.examDate) return null;
  const now=new Date(); now.setHours(0,0,0,0);
  const d=new Date(P.examDate); d.setHours(0,0,0,0);
  return Math.max(0,Math.round((d-now)/86400000));
}""",
"""// A date in the past used to clamp to 0, which the pace then divided by a floor of 1 day
// and reported as "0 days to go · 900 questions/day". A date centuries out read 355,118 days.
const EXAM_MAX_DAYS=730;
function examDaysLeft(){
  if(!P.examDate) return null;
  const now=new Date(); now.setHours(0,0,0,0);
  const d=new Date(P.examDate);
  if(isNaN(d.getTime())) return null;
  d.setHours(0,0,0,0);
  const days=Math.round((d-now)/86400000);
  if(days<0) return -1;                     // in the past, and the caller should say so
  return Math.min(EXAM_MAX_DAYS,days);
}""")

sub("""function dailyPace(){
  const left=examDaysLeft();
  const remaining=Math.max(0,QS.length-Object.keys(P.seen||{}).length);
  if(left===null) return {perDay:20,remaining,days:null};
  const days=Math.max(1,left);
  return {perDay:Math.ceil(Math.min(remaining,900)/days),remaining,days:left};
}""",
"""function dailyPace(){
  const left=examDaysLeft();
  const remaining=Math.max(0,QS.length-Object.keys(P.seen||{}).length);
  if(left===null||left<0) return {perDay:20,remaining,days:left};
  const days=Math.max(1,left);
  return {perDay:Math.ceil(Math.min(remaining,900)/days),remaining,days:left};
}
// one sentence for the countdown, so the three places that print it agree
function examDaysLabel(days,pace){
  if(days===null) return 'Set your exam date for a daily target';
  if(days<0) return 'Your exam date has passed — set a new one';
  if(days===0) return 'Exam day. Go and pass it.';
  return days+' day'+(days===1?'':'s')+' to go · '+pace.perDay+' questions/day';
}""")

sub("""  if(dEl) dEl.textContent=days===null?'Set your exam date for a daily target'
    :(days+' day'+(days===1?'':'s')+' to go · '+pace.perDay+' questions/day');""",
"""  if(dEl) dEl.textContent=examDaysLabel(days,pace);""")

sub("""  $('readyDays2').textContent=d===null?('Pick your exam date below · '+pace.remaining+' questions unseen')
    :(d+' days left · '+pace.perDay+' questions/day to cover the bank');""",
"""  $('readyDays2').textContent=d===null?('Pick your exam date below · '+pace.remaining+' questions unseen')
    :d<0?'Your exam date has passed — pick a new one below'
    :d===0?('Exam day · '+pace.remaining+' questions still unseen')
    :(d+' day'+(d===1?'':'s')+' left · '+pace.perDay+' questions/day to cover the bank');""")

sub("""  toast(iso?('🎯 Exam set — '+examDaysLeft()+' days to go'):'Exam date cleared');""",
"""  const dl=examDaysLeft();
  toast(!iso?'Exam date cleared'
        :dl<0?'🎯 That date has already passed'
        :dl===0?'🎯 Exam set — that is today'
        :('🎯 Exam set — '+dl+' day'+(dl===1?'':'s')+' to go'));""")

# ------------------------------------------------------------- paper bounds
sub("""function paperQs(n){                       // n is 1-based
  const from=(n-1)*PAPER_LEN;
  return Array.from({length:Math.min(PAPER_LEN,QS.length-from)},(_,k)=>from+k);
}""",
"""function paperQs(n){                       // n is 1-based
  // paperQs(0) used to hand back indices from -65 and paperQs(-1) from -130, which then
  // looked up QS[-65] and got undefined all the way down the call chain
  n=Math.floor(Number(n));
  if(!isFinite(n)||n<1||n>PAPER_COUNT) return [];
  const from=(n-1)*PAPER_LEN;
  return Array.from({length:Math.min(PAPER_LEN,QS.length-from)},(_,k)=>from+k);
}""")

# ------------------------------------- a profile missing a field is not a crash
sub("""function renderBadges(){
  $('achCount').textContent=P.badges.length+' of '+BADGES.length+' unlocked';""",
"""function renderBadges(){
  // every other reader in this file guards with ||[]; these two did not, and a profile
  // merged from a device that had never earned one took the whole screen down
  P.badges=P.badges||[];
  $('achCount').textContent=P.badges.length+' of '+BADGES.length+' unlocked';""")

sub("""function renderShop(){
  const L=$('shopList'); L.innerHTML='';""",
"""function renderShop(){
  P.upgrades=P.upgrades||{}; P.inv=P.inv||{};
  const L=$('shopList'); L.innerHTML='';""")

sub("""    syncQBar, leaveExam,""",
"""    syncQBar, leaveExam, timerClamp, TIMER_MAX, examDaysLabel, EXAM_MAX_DAYS,""")

PAGE.write_text(s, encoding="utf-8")
print("validation fixes applied · page %.2f MB" % (len(s) / 1e6))
