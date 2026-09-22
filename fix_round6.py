#!/usr/bin/env python3
"""Three from the sixth audit. Two of its fifteen findings were the audit's fault.

  * **fmtClock renders nonsense for anything but a sane millisecond count.**
    fmtClock(-1000) is "-1:-1", NaN is "NaN:NaN", Infinity is
    "Infinity:NaN:NaN". Most callers clamp, but not all: P.playMs and sessMs
    come from a merged profile and nothing stops a negative one, and a single
    guard in the formatter is cheaper than auditing every caller forever.

  * **Day keys do not sort.** dayKey() built "2026-1-5", so as strings
    "2026-1-5" > "2026-1-12" — January the fifth sorts after January the
    twelfth. Nothing orders them today (every use is `!==`), so this is a trap
    rather than a live bug, and exactly the kind that bites whoever first writes
    `logs.sort()`. The key is zero-padded now, and sameDay() compares loosely so
    dates already written in the old shape still match and nobody's daily
    counter resets.

  * **badgeProgress can report more than its goal.** It returns the raw pair, so
    a best streak of 12 against a goal of 5 renders "12/5". The bar is clamped
    but the text was not.

Not fixed, because the audit was wrong:
  * "two right answers do not push the review further out" — srSchedule measures
    in questions answered, not time, and the test never moved P.answered.
  * the badge findings at 1e6 are unreachable values; the clamp is still worth
    having for the reachable ones.

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


# ------------------------------------------------------------- fmtClock guards
sub("""function fmtClock(ms){
  const s=Math.floor(ms/1000), h=Math.floor(s/3600), m=Math.floor(s%3600/60), ss=s%60;""",
"""function fmtClock(ms){
  // Called with a merged profile's counters among other things, and "-1:-1" or "NaN:NaN" on
  // screen is worse than a wrong number — one guard here beats auditing every caller forever.
  ms=Number(ms);
  if(!isFinite(ms)||ms<0) ms=0;
  const s=Math.floor(ms/1000), h=Math.floor(s/3600), m=Math.floor(s%3600/60), ss=s%60;""")

# ------------------------------------------------------- day keys that sort
sub("""function dayKey(){ const d=new Date(); return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate(); }""",
"""// Zero-padded so the keys sort. They used to read "2026-1-5", which as a string is AFTER
// "2026-1-12". Nothing orders them today — every use is an equality check — but it is exactly
// the trap that bites whoever first writes logs.sort().
const pad2=n=>String(n).padStart(2,'0');
function dayKey(){ const d=new Date(); return d.getFullYear()+'-'+pad2(d.getMonth()+1)+'-'+pad2(d.getDate()); }
// Dates written before the padding still have to match today, or every daily counter and quest
// set resets once for no reason.
const dayNorm=k=>String(k||'').split('-').map((p,i)=>i?pad2(Number(p)):p).join('-');
const sameDay=(a,b)=>dayNorm(a)===dayNorm(b);""")

sub("""function today(){ const d=new Date(); return d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate(); }""",
"""function today(){ const d=new Date();
  return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }""")

sub("""  if(P.day.date!==today()) P.day={date:today(),n:0,claimed:false};""",
"""  if(!sameDay(P.day.date,today())) P.day={date:today(),n:0,claimed:false};""")

sub("""  if(!P.quests||P.quests.date!==dayKey()){""",
"""  if(!P.quests||!sameDay(P.quests.date,dayKey())){""")

sub("""  if(!P.rHist.length||P.rHist[P.rHist.length-1].d!==k) P.rHist.push({d:k,p:r.pct});""",
"""  if(!P.rHist.length||!sameDay(P.rHist[P.rHist.length-1].d,k)) P.rHist.push({d:k,p:r.pct});""")

# --------------------------------------------- badge progress cannot beat its goal
sub("""    codex25:[(P.known||[]).length,25],marks10:[(P.marks||[]).length,10],frugal:[P.coins,250]};
  return m[b.id]||null;""",
"""    codex25:[(P.known||[]).length,25],marks10:[(P.marks||[]).length,10],frugal:[P.coins,250]};
  const p=m[b.id];
  if(!p) return null;
  // a best streak of 12 against a goal of 5 used to render "12/5"
  const goal=Number(p[1])||0, cur=Number(p[0]);
  return [Math.max(0,Math.min(goal,isFinite(cur)?cur:0)),goal];""")

sub("""    fmtClock, dayKey, srSchedule, exportProfile, csvRows, badgeProgress, dailyState, BADGES,""",
"""    fmtClock, dayKey, sameDay, dayNorm, srSchedule, exportProfile, csvRows, badgeProgress,
    dailyState, BADGES,""")

PAGE.write_text(s, encoding="utf-8")
print("round six applied · page %.2f MB" % (len(s) / 1e6))
